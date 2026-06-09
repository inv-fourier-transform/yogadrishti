"""Lightweight pose classifier using landmark features.

Uses a Deep Skeletal MLP (81.3% Accuracy) as the primary engine, 
falling back to XGBoost or a rule-matching heuristic.
"""
from __future__ import annotations
import os
import numpy as np
import joblib
from pathlib import Path
from app.config import get_settings
from app.models.domain_schemas import LandmarkSet
from app.core.pose_detection.mediapipe_runner import landmarks_to_feature_vector
from app.services.dataset.engineer_features import engineer_features
from app.core.pose_evaluation.pose_registry import get_pose_info, get_class82_to_key_map
from app.utils.logging import logger

SETTINGS = get_settings()

# --- Registry & State ---
_classifier = None
_label_encoder = None

# Neural Engine State
_mlp_model = None
_mlp_label_map = None
_mlp_pose_keys = None

# --- Model Loading Helpers ---

def _load_model():
    """Lazily load the legacy XGBoost classifier."""
    global _classifier, _label_encoder
    if _classifier is not None:
        return _classifier, _label_encoder

    model_path = Path(SETTINGS.pose_classifier_model_path)
    encoder_path = Path(SETTINGS.pose_label_encoder_path)

    if model_path.exists() and encoder_path.exists():
        try:
            _classifier = joblib.load(model_path)
            _label_encoder = joblib.load(encoder_path)
            logger.info("Loaded legacy XGBoost classifier.")
            return _classifier, _label_encoder
        except Exception as e:
            logger.error(f"Failed to load XGBoost: {e}")

    return None, None

def _load_mlp_model():
    """Lazily load the PyTorch Skeletal MLP model (81.3% Accuracy)."""
    global _mlp_model, _mlp_label_map, _mlp_pose_keys
    if _mlp_model is not None:
        return _mlp_model, _mlp_pose_keys
        
    model_path = Path("./models/pose_mlp.pth")
    label_map_path = Path("./models/mlp_label_map.joblib")
    
    if model_path.exists() and label_map_path.exists():
        try:
            import torch
            import torch.nn as nn
            
            # 1. Load label map and align with PoseRegistry
            _mlp_label_map = joblib.load(label_map_path)
            # Create array of pose keys matching index order (0..81)
            _mlp_pose_keys = ["" for _ in range(82)]
            class82_to_key = get_class82_to_key_map()
            
            # Map math ID to pose_key string
            for class_id, idx in _mlp_label_map.items():
                pose_key = class82_to_key.get(int(class_id), "unknown_pose")
                if idx < 82:
                    _mlp_pose_keys[idx] = pose_key
                
            # 2. Define Internal Architecture (Must exactly match training)
            class InternalYogaMLP(nn.Module):
                def __init__(self, input_dim=160, num_classes=82):
                    super().__init__()
                    self.network = nn.Sequential(
                        nn.Linear(input_dim, 1024),
                        nn.BatchNorm1d(1024),
                        nn.ReLU(),
                        nn.Dropout(0.3),
                        nn.Linear(1024, 512),
                        nn.BatchNorm1d(512),
                        nn.ReLU(),
                        nn.Dropout(0.3),
                        nn.Linear(512, 256),
                        nn.BatchNorm1d(256),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(256, num_classes)
                    )
                def forward(self, x):
                    return self.network(x)

            # 3. Initialize and load weights
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            _mlp_model = InternalYogaMLP(input_dim=160, num_classes=len(_mlp_label_map))
            _mlp_model.load_state_dict(torch.load(model_path, map_location=device))
            _mlp_model = _mlp_model.to(device).eval()
            
            logger.info("Deep Skeletal MLP integrated as primary engine.")
            return _mlp_model, _mlp_pose_keys
        except Exception as e:
            logger.error(f"Failed to load MLP model: {e}")
            
    return None, None

# --- Main Interface ---

def classify_pose(landmarks: LandmarkSet, image_rgb: np.ndarray = None) -> tuple[str, float, dict[str, float]]:
    """
    Classify the yoga pose using the deep skeletal MLP engine (Primary, 81.3% Acc).
    Falls back to legacy XGBoost or Heuristics if deep learning is unavailable.
    """
    # 0. Preparation: Engineer features for MLP/XGBoost
    raw_features = landmarks_to_feature_vector(landmarks)
    X_raw = np.array([raw_features])
    X_engineered = engineer_features(X_raw)

    # 1. PRIMARY: Deep Skeletal MLP (81.32% Accuracy)
    mlp_model, mlp_class_keys = _load_mlp_model()
    if mlp_model is not None:
        try:
            import torch
            device = next(mlp_model.parameters()).device
            feat_tensor = torch.FloatTensor(X_engineered).to(device)
            
            with torch.no_grad():
                output = mlp_model(feat_tensor)
                probas = torch.nn.functional.softmax(output[0], dim=0).cpu().numpy()
                
            predicted_idx = np.argmax(probas)
            confidence = float(probas[predicted_idx])
            predicted_label = mlp_class_keys[predicted_idx]
            
            # Extract top 3 for Gemini/LLM context
            top3_indices = np.argsort(probas)[-3:][::-1]
            top3 = {mlp_class_keys[idx]: float(probas[idx]) for idx in top3_indices}
            
            return predicted_label, confidence, top3
        except Exception as e:
            logger.warning(f"MLP inference failed, falling back to legacy: {e}")

    # 2. FALLBACK 1: Legacy XGBoost (81.04% Accuracy)
    model, encoder = _load_model()
    if model is not None and encoder is not None:
        try:
            probas = model.predict_proba(X_engineered)[0]
            predicted_idx = np.argmax(probas)
            confidence = float(probas[predicted_idx])
            pose_id = model.classes_[predicted_idx]
            
            class82_to_key = get_class82_to_key_map()
            predicted_label = class82_to_key.get(pose_id, "unknown_pose")
            
            top3_indices = np.argsort(probas)[-3:][::-1]
            top3 = {}
            for idx in top3_indices:
                p_id = model.classes_[idx]
                p_key = class82_to_key.get(p_id, "unknown_pose")
                top3[p_key] = float(probas[idx])
                
            return predicted_label, confidence, top3
        except Exception:
            pass

    # 3. FALLBACK 2: Geometry-based Heuristic
    return _heuristic_classify(landmarks)

# --- Heuristic Fallback Logic ---

def _score_pose_against_rules(angles: dict, landmarks: LandmarkSet, ruleset) -> float:
    """Score how well detected angles match a specific pose's rule set."""
    from app.core.pose_evaluation.alignment import (
        shoulder_level_diff, hip_level_diff, spine_alignment_angle, stance_width,
    )

    total_weight = 0.0
    weighted_score = 0.0

    for rule in ruleset.angle_rules:
        if rule.joint_name not in angles:
            total_weight += rule.weight
            weighted_score += 0.3 * rule.weight
            continue

        measured = angles[rule.joint_name].angle_degrees
        total_weight += rule.weight

        if rule.min_degrees <= measured <= rule.max_degrees:
            weighted_score += 1.0 * rule.weight
        else:
            deviation = min(abs(measured - rule.min_degrees), abs(measured - rule.max_degrees))
            score = max(0.0, 1.0 - deviation / 60.0)
            weighted_score += score * rule.weight

    for arule in ruleset.alignment_rules:
        check_type = arule.check_type
        max_dev = arule.max_deviation
        total_weight += arule.weight
        try:
            if check_type == "shoulder_level":
                val = shoulder_level_diff(landmarks)
            elif check_type == "hip_level":
                val = hip_level_diff(landmarks)
            elif check_type == "spine_vertical":
                val = spine_alignment_angle(landmarks) / 90.0
            elif check_type == "stance_width":
                val = max(0, max_dev - stance_width(landmarks))
            else:
                val = 0.0
            ascore = max(0.0, 1.0 - val / max_dev) if max_dev > 0 else 1.0
            weighted_score += ascore * arule.weight
        except Exception:
            weighted_score += 0.3 * arule.weight

    effective_weight = max(total_weight, 4.0)
    return weighted_score / effective_weight if effective_weight > 0 else 0.0

def _detect_body_orientation(landmarks: LandmarkSet) -> str:
    """Detect body orientation using Y-coordinates and spine angle."""
    from app.core.pose_evaluation.alignment import spine_alignment_angle
    lm = landmarks.landmarks
    shoulder_y = (lm[11].y + lm[12].y) / 2
    hip_y = (lm[23].y + lm[24].y) / 2
    ankle_y = (lm[27].y + lm[28].y) / 2

    shoulder_hip_gap = hip_y - shoulder_y
    hip_ankle_gap = ankle_y - hip_y
    spine_angle = spine_alignment_angle(landmarks)

    if ankle_y < shoulder_y - 0.05: return "inverted"
    if spine_angle > 35 or (abs(shoulder_hip_gap) < 0.10 and abs(hip_ankle_gap) < 0.10):
        return "prone_or_supine"
    if shoulder_hip_gap > 0.12 and hip_ankle_gap > 0.10 and spine_angle < 30: return "upright"
    if shoulder_hip_gap > 0.10 and hip_ankle_gap < 0.10: return "seated"
    return "unknown"

_POSE_ORIENTATION = {
    "tree_pose": "upright", "warrior_i": "upright", "warrior_ii": "upright",
    "warrior_iii": "upright", "chair_pose": "upright", "eagle_pose": "upright",
    "half_moon_pose": "upright", "extended_side_angle_pose": "upright",
    "reverse_warrior_pose": "upright", "triangle_pose": "upright",
    "standing_forward_bend_pose": "upright", "lord_of_dance_pose": "upright",
    "low_lunge_pose": "upright", "garland_pose": "upright",
    "standing_big_toe_hold_pose": "upright", "gate_pose": "upright",
    "intense_side_stretch_pose": "upright", "standing_split_pose": "upright",
    "wide_legged_forward_bend_pose": "upright", "noose_pose": "upright",
    "camel_pose": "upright",
    "plank_pose": "prone_or_supine", "cobra_pose": "prone_or_supine",
    "four_limbed_staff_pose": "prone_or_supine", "downward_dog": "prone_or_supine",
    "bridge_pose": "prone_or_supine", "corpse_pose": "prone_or_supine",
    "supported_headstand_pose": "inverted", "supported_shoulderstand_pose": "inverted",
    "seated_forward_bend_pose": "seated", "bound_angle_pose": "seated",
    "hero_pose": "seated", "staff_pose": "seated", "half_lord_fishes_pose": "seated",
}

def _heuristic_classify(landmarks: LandmarkSet) -> tuple[str, float, dict[str, float]]:
    """Rule-matching fallback."""
    from app.core.pose_evaluation.angles import compute_all_angles
    from app.core.pose_evaluation.pose_rules import POSE_RULES

    body_orientation = _detect_body_orientation(landmarks)
    angles = compute_all_angles(landmarks)
    angle_values = {name: ja for name, ja in angles.items()}

    pose_scores = {}
    for pose_key, ruleset in POSE_RULES.items():
        if not ruleset.angle_rules: continue
        score = _score_pose_against_rules(angle_values, landmarks, ruleset)
        expected_orient = _POSE_ORIENTATION.get(pose_key, "unknown")
        if body_orientation != expected_orient and body_orientation != "unknown":
            score *= 0.25
        pose_scores[pose_key] = score

    if not pose_scores: return "unknown_pose", 0.10, {"unknown_pose": 0.10}
    sorted_poses = sorted(pose_scores.items(), key=lambda x: x[1], reverse=True)
    best_key, best_raw = sorted_poses[0]
    confidence = min(0.95, round(0.3 + best_raw * 0.5, 2))
    
    top3 = {key: round(min(0.95, 0.2 + raw * 0.6), 2) for key, raw in sorted_poses[:3]}
    top3[best_key] = confidence
    return best_key, confidence, top3
