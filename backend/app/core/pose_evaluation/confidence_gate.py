"""Confidence and reliability gating before feedback generation.

IMPORTANT: The MLP classifier distributes probability across 82 classes.
Random chance = 1.2%, so a 15% confidence IS statistically significant.
Only truly degraded inputs (missing landmarks, blurry images) should
downgrade evaluation reliability — NOT classifier confidence.
"""
from app.models.domain_schemas import LandmarkSet, PoseEvaluation
from app.services.image_processing.decode import is_blurry
from app.core.pose_detection.landmarks_schema import ESSENTIAL_LANDMARKS
from app.config import get_settings
import numpy as np

SETTINGS = get_settings()


def check_landmark_visibility(landmarks: LandmarkSet, min_vis: float = None) -> tuple[float, list[str]]:
    """
    Check overall landmark visibility.
    Returns (visibility_ratio, list_of_issues).
    """
    min_vis = min_vis or SETTINGS.min_landmark_visibility
    issues = []
    total = len(landmarks.landmarks)
    visible = sum(1 for lm in landmarks.landmarks if lm.visibility >= min_vis)
    ratio = visible / total if total > 0 else 0.0

    # Check essential landmarks specifically
    essential_hidden = []
    for idx in ESSENTIAL_LANDMARKS:
        if idx < total and landmarks.get(idx).visibility < min_vis:
            essential_hidden.append(landmarks.get(idx).name)

    if essential_hidden:
        issues.append(
            f"Key body parts not clearly visible: {', '.join(essential_hidden[:5])}. "
            "Try positioning so your full body is visible to the camera."
        )

    if ratio < 0.4:
        issues.append(
            "Too many body landmarks are not visible. Ensure your full body is in the frame "
            "with adequate lighting."
        )

    return ratio, issues


def check_image_quality(image: np.ndarray) -> list[str]:
    """Check image quality issues. Returns list of issues found."""
    issues = []
    h, w = image.shape[:2]

    if h < 120 or w < 120:
        issues.append(
            "Image resolution is very low. Please upload a higher resolution image."
        )

    if is_blurry(image, threshold=30.0):
        issues.append(
            "Image appears blurry. Please use a clearer photo for more accurate analysis."
        )

    return issues


def apply_reliability_gate(
    evaluation: PoseEvaluation,
    landmarks: LandmarkSet,
    image: np.ndarray = None,
) -> PoseEvaluation:
    """
    Apply reliability gating based on INPUT QUALITY only.

    Only image quality and landmark visibility degrade reliability.
    Classifier confidence is NOT a reliability issue — the MLP distributes
    probability across 82 classes, making low raw confidence values normal
    and expected. A 15% confidence on 82 classes is 12x random chance.
    """
    reasons = []

    # Check landmark visibility
    vis_ratio, vis_issues = check_landmark_visibility(landmarks)
    evaluation.landmark_visibility_ratio = vis_ratio

    # Check image quality
    if image is not None:
        quality_issues = check_image_quality(image)
        reasons.extend(quality_issues)

    # Only flag visibility if truly terrible (< 30%)
    if vis_ratio < 0.3:
        reasons.extend(vis_issues)

    # If input quality is genuinely bad, downgrade
    if reasons:
        evaluation.evaluation_status = "low_confidence"
        evaluation.correctness_label = "not_reliably_evaluable"
        evaluation.reliability_reason = " | ".join(reasons)
    else:
        # Attach visibility info as non-blocking notes
        if vis_issues:
            evaluation.reliability_reason = " | ".join(vis_issues)

    return evaluation
