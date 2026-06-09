"""MediaPipe Pose Landmarker wrapper for landmark extraction."""
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from app.models.domain_schemas import Landmark, LandmarkSet
from app.utils.logging import logger

# MediaPipe landmark names (33 landmarks)
LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear",
    "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_pinky", "right_pinky",
    "left_index", "right_index",
    "left_thumb", "right_thumb",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]

# Important indices
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28

_detector = None


def _get_detector():
    """Lazily initialize the MediaPipe Pose Landmarker."""
    global _detector
    if _detector is not None:
        return _detector

    try:
        import os
        model_path = os.path.join(os.path.dirname(__file__), 'pose_landmarker_lite.task')
        base_options = mp_python.BaseOptions(
            model_asset_path=model_path 
        )
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            num_poses=5,  # Detect up to 5 to check for multiple people
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        _detector = vision.PoseLandmarker.create_from_options(options)
        return _detector
    except Exception as e:
        logger.error(f"Failed to initialize MediaPipe PoseLandmarker: {e}")
        # Fallback: use legacy Pose solution
        return None


def extract_landmarks_legacy(image_rgb: np.ndarray) -> tuple[list[LandmarkSet], int]:
    """
    Fallback: Use mp.solutions.pose for landmark extraction.
    Returns (list_of_landmark_sets, person_count).
    Only detects one person with solutions API.
    """
    mp_pose = mp.solutions.pose
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.5,
    ) as pose:
        results = pose.process(image_rgb)

    if not results.pose_landmarks:
        return [], 0

    landmarks = []
    for i, lm in enumerate(results.pose_landmarks.landmark):
        name = LANDMARK_NAMES[i] if i < len(LANDMARK_NAMES) else f"landmark_{i}"
        landmarks.append(Landmark(
            x=lm.x, y=lm.y, z=lm.z,
            visibility=lm.visibility,
            name=name,
        ))

    visibilities = [lm.visibility for lm in landmarks]
    avg_vis = sum(visibilities) / len(visibilities) if visibilities else 0.0

    return [LandmarkSet(landmarks=tuple(landmarks), overall_visibility=avg_vis)], 1


def extract_landmarks(image_rgb: np.ndarray) -> tuple[list[LandmarkSet], int]:
    """
    Run MediaPipe pose landmark detection on an RGB image.
    Returns (list_of_landmark_sets, detected_person_count).
    Each LandmarkSet contains 33 landmarks.
    """
    detector = _get_detector()

    # Use legacy API as fallback
    if detector is None:
        return extract_landmarks_legacy(image_rgb)

    try:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        result = detector.detect(mp_image)

        if not result.pose_landmarks:
            return [], 0

        person_count = len(result.pose_landmarks)
        landmark_sets = []

        for person_landmarks in result.pose_landmarks:
            landmarks = []
            for i, lm in enumerate(person_landmarks):
                name = LANDMARK_NAMES[i] if i < len(LANDMARK_NAMES) else f"landmark_{i}"
                landmarks.append(Landmark(
                    x=lm.x, y=lm.y, z=lm.z,
                    visibility=lm.visibility,
                    name=name,
                ))

            visibilities = [lm.visibility for lm in landmarks]
            avg_vis = sum(visibilities) / len(visibilities) if visibilities else 0.0
            landmark_sets.append(LandmarkSet(
                landmarks=tuple(landmarks),
                overall_visibility=avg_vis,
            ))

        return landmark_sets, person_count

    except Exception as e:
        logger.error(f"PoseLandmarker detection error: {e}")
        return extract_landmarks_legacy(image_rgb)


def landmarks_to_feature_vector(landmark_set: LandmarkSet) -> list[float]:
    """Convert landmarks to a flat feature vector for ML classification.
    Format: [x0, y0, z0, vis0, x1, y1, z1, vis1, ...]
    Total: 33 * 4 = 132 features.
    """
    features = []
    for lm in landmark_set.landmarks:
        features.extend([lm.x, lm.y, lm.z, lm.visibility])
    return features
