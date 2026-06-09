"""Tests for joint angle computation functions."""
import math
import pytest
from app.models.domain_schemas import Landmark, LandmarkSet
from app.core.pose_evaluation.angles import (
    _angle_3d, compute_angle, compute_all_angles,
    left_elbow_angle, right_elbow_angle,
    left_shoulder_angle, right_shoulder_angle,
    left_hip_angle, right_hip_angle,
    left_knee_angle, right_knee_angle,
    left_ankle_angle, right_ankle_angle,
)


def _lm(x: float, y: float, z: float = 0.0, vis: float = 1.0, name: str = "") -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=vis, name=name)


def _make_landmarks(overrides: dict[int, Landmark] = None) -> LandmarkSet:
    """Create a LandmarkSet with 33 default landmarks and optional overrides."""
    defaults = [_lm(0.0, 0.0) for _ in range(33)]
    if overrides:
        for idx, lm in overrides.items():
            defaults[idx] = lm
    return LandmarkSet(landmarks=tuple(defaults), overall_visibility=1.0)


# ── _angle_3d tests ──────────────────────────────────

class TestAngle3D:
    def test_right_angle(self):
        """Three points forming a 90° angle at b."""
        a = _lm(1, 0, 0)
        b = _lm(0, 0, 0)
        c = _lm(0, 1, 0)
        angle = _angle_3d(a, b, c)
        assert abs(angle - 90.0) < 0.1

    def test_straight_line(self):
        """Three colinear points → 180°."""
        a = _lm(-1, 0, 0)
        b = _lm(0, 0, 0)
        c = _lm(1, 0, 0)
        angle = _angle_3d(a, b, c)
        assert abs(angle - 180.0) < 0.1

    def test_acute_angle(self):
        """Points forming a 60° angle."""
        a = _lm(1, 0, 0)
        b = _lm(0, 0, 0)
        c = _lm(0.5, math.sqrt(3) / 2, 0)
        angle = _angle_3d(a, b, c)
        assert abs(angle - 60.0) < 0.1

    def test_obtuse_angle(self):
        """Points forming a 120° angle."""
        a = _lm(1, 0, 0)
        b = _lm(0, 0, 0)
        c = _lm(-0.5, math.sqrt(3) / 2, 0)
        angle = _angle_3d(a, b, c)
        assert abs(angle - 120.0) < 0.1

    def test_zero_length_returns_zero(self):
        """If two points coincide, angle should be 0."""
        a = _lm(0, 0, 0)
        b = _lm(0, 0, 0)
        c = _lm(1, 0, 0)
        assert _angle_3d(a, b, c) == 0.0

    def test_3d_angle(self):
        """Angle in 3D space."""
        a = _lm(1, 0, 0)
        b = _lm(0, 0, 0)
        c = _lm(0, 0, 1)
        angle = _angle_3d(a, b, c)
        assert abs(angle - 90.0) < 0.1


# ── compute_angle tests ─────────────────────────────

class TestComputeAngle:
    def test_basic(self):
        lm = _make_landmarks({
            11: _lm(1, 0),  # LEFT_SHOULDER
            13: _lm(0, 0),  # LEFT_ELBOW
            15: _lm(0, 1),  # LEFT_WRIST
        })
        angle = compute_angle(lm, 11, 13, 15)
        assert abs(angle - 90.0) < 0.1


# ── Named angle function tests ──────────────────────

class TestNamedAngleFunctions:
    def _make_pose(self) -> LandmarkSet:
        """Create landmarks that produce known angles for key joints."""
        return _make_landmarks({
            # Arms: elbows at 90 degrees
            11: _lm(0.3, 0.3),     # LEFT_SHOULDER
            12: _lm(0.7, 0.3),     # RIGHT_SHOULDER
            13: _lm(0.2, 0.5),     # LEFT_ELBOW
            14: _lm(0.8, 0.5),     # RIGHT_ELBOW
            15: _lm(0.3, 0.7),     # LEFT_WRIST
            16: _lm(0.7, 0.7),     # RIGHT_WRIST
            # Torso
            23: _lm(0.35, 0.6),    # LEFT_HIP
            24: _lm(0.65, 0.6),    # RIGHT_HIP
            # Legs
            25: _lm(0.35, 0.8),    # LEFT_KNEE
            26: _lm(0.65, 0.8),    # RIGHT_KNEE
            27: _lm(0.35, 1.0),    # LEFT_ANKLE
            28: _lm(0.65, 1.0),    # RIGHT_ANKLE
            31: _lm(0.40, 1.0),    # LEFT_FOOT_INDEX
            32: _lm(0.60, 1.0),    # RIGHT_FOOT_INDEX
        })

    def test_left_elbow_angle(self):
        ja = left_elbow_angle(self._make_pose())
        assert ja.joint_name == "left_elbow"
        assert isinstance(ja.angle_degrees, float)
        assert 0 <= ja.angle_degrees <= 180

    def test_right_elbow_angle(self):
        ja = right_elbow_angle(self._make_pose())
        assert ja.joint_name == "right_elbow"

    def test_left_shoulder_angle(self):
        ja = left_shoulder_angle(self._make_pose())
        assert ja.joint_name == "left_shoulder"

    def test_right_shoulder_angle(self):
        ja = right_shoulder_angle(self._make_pose())
        assert ja.joint_name == "right_shoulder"

    def test_left_hip_angle(self):
        ja = left_hip_angle(self._make_pose())
        assert ja.joint_name == "left_hip"

    def test_right_hip_angle(self):
        ja = right_hip_angle(self._make_pose())
        assert ja.joint_name == "right_hip"

    def test_left_knee_angle(self):
        ja = left_knee_angle(self._make_pose())
        assert ja.joint_name == "left_knee"
        assert ja.angle_degrees > 0

    def test_right_knee_angle(self):
        ja = right_knee_angle(self._make_pose())
        assert ja.joint_name == "right_knee"

    def test_left_ankle_angle(self):
        ja = left_ankle_angle(self._make_pose())
        assert ja.joint_name == "left_ankle"

    def test_right_ankle_angle(self):
        ja = right_ankle_angle(self._make_pose())
        assert ja.joint_name == "right_ankle"

    def test_straight_knee(self):
        """Hip, knee, ankle on a straight vertical line → ~180°."""
        lm = _make_landmarks({
            23: _lm(0.5, 0.3),    # LEFT_HIP
            25: _lm(0.5, 0.6),    # LEFT_KNEE
            27: _lm(0.5, 0.9),    # LEFT_ANKLE
        })
        ja = left_knee_angle(lm)
        assert abs(ja.angle_degrees - 180.0) < 0.1

    def test_bent_elbow_90(self):
        """Shoulder-elbow-wrist forming a right angle."""
        lm = _make_landmarks({
            11: _lm(0.5, 0.3),   # LEFT_SHOULDER
            13: _lm(0.5, 0.5),   # LEFT_ELBOW
            15: _lm(0.7, 0.5),   # LEFT_WRIST
        })
        ja = left_elbow_angle(lm)
        assert abs(ja.angle_degrees - 90.0) < 0.5


# ── compute_all_angles tests ────────────────────────

class TestComputeAllAngles:
    def test_returns_ten_angles(self):
        lm = _make_landmarks({
            11: _lm(0.3, 0.3), 12: _lm(0.7, 0.3),
            13: _lm(0.2, 0.5), 14: _lm(0.8, 0.5),
            15: _lm(0.3, 0.7), 16: _lm(0.7, 0.7),
            23: _lm(0.35, 0.6), 24: _lm(0.65, 0.6),
            25: _lm(0.35, 0.8), 26: _lm(0.65, 0.8),
            27: _lm(0.35, 1.0), 28: _lm(0.65, 1.0),
            31: _lm(0.40, 1.0), 32: _lm(0.60, 1.0),
        })
        angles = compute_all_angles(lm)
        assert len(angles) == 10
        expected_keys = {
            "left_elbow", "right_elbow",
            "left_shoulder", "right_shoulder",
            "left_hip", "right_hip",
            "left_knee", "right_knee",
            "left_ankle", "right_ankle",
        }
        assert set(angles.keys()) == expected_keys

    def test_all_angles_are_positive(self):
        lm = _make_landmarks({
            11: _lm(0.3, 0.3), 12: _lm(0.7, 0.3),
            13: _lm(0.2, 0.5), 14: _lm(0.8, 0.5),
            15: _lm(0.3, 0.7), 16: _lm(0.7, 0.7),
            23: _lm(0.35, 0.6), 24: _lm(0.65, 0.6),
            25: _lm(0.35, 0.8), 26: _lm(0.65, 0.8),
            27: _lm(0.35, 1.0), 28: _lm(0.65, 1.0),
            31: _lm(0.40, 1.0), 32: _lm(0.60, 1.0),
        })
        angles = compute_all_angles(lm)
        for name, ja in angles.items():
            assert ja.angle_degrees >= 0, f"{name} has negative angle"
            assert ja.angle_degrees <= 180, f"{name} exceeds 180°"
