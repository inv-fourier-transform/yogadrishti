"""Tests for alignment, symmetry, and postural check functions."""
import pytest
from app.models.domain_schemas import Landmark, LandmarkSet
from app.core.pose_evaluation.alignment import (
    shoulder_level_diff, hip_level_diff, shoulder_hip_alignment,
    spine_alignment_angle, stance_width,
    arm_symmetry, leg_symmetry,
    body_centerline_x, forward_lean,
)


def _lm(x: float, y: float, z: float = 0.0) -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=1.0, name="")


def _make_landmarks(overrides: dict[int, Landmark] = None) -> LandmarkSet:
    defaults = [_lm(0.0, 0.0) for _ in range(33)]
    if overrides:
        for idx, lm in overrides.items():
            defaults[idx] = lm
    return LandmarkSet(landmarks=tuple(defaults), overall_visibility=1.0)


# Landmark indices
LS, RS = 11, 12      # shoulders
LE, RE = 13, 14      # elbows
LW, RW = 15, 16      # wrists
LH, RH = 23, 24      # hips
LK, RK = 25, 26      # knees
LA, RA = 27, 28      # ankles


class TestShoulderLevelDiff:
    def test_level_shoulders(self):
        lm = _make_landmarks({LS: _lm(0.3, 0.4), RS: _lm(0.7, 0.4)})
        assert shoulder_level_diff(lm) == pytest.approx(0.0)

    def test_uneven_shoulders(self):
        lm = _make_landmarks({LS: _lm(0.3, 0.4), RS: _lm(0.7, 0.5)})
        assert shoulder_level_diff(lm) == pytest.approx(0.1)


class TestHipLevelDiff:
    def test_level_hips(self):
        lm = _make_landmarks({LH: _lm(0.4, 0.6), RH: _lm(0.6, 0.6)})
        assert hip_level_diff(lm) == pytest.approx(0.0)

    def test_tilted_hips(self):
        lm = _make_landmarks({LH: _lm(0.4, 0.6), RH: _lm(0.6, 0.65)})
        assert hip_level_diff(lm) == pytest.approx(0.05)


class TestShoulderHipAlignment:
    def test_aligned(self):
        lm = _make_landmarks({
            LS: _lm(0.4, 0.3), RS: _lm(0.6, 0.3),
            LH: _lm(0.4, 0.6), RH: _lm(0.6, 0.6),
        })
        assert shoulder_hip_alignment(lm) == pytest.approx(0.0)

    def test_shifted(self):
        lm = _make_landmarks({
            LS: _lm(0.3, 0.3), RS: _lm(0.5, 0.3),  # mid = 0.4
            LH: _lm(0.4, 0.6), RH: _lm(0.6, 0.6),  # mid = 0.5
        })
        assert shoulder_hip_alignment(lm) == pytest.approx(0.1)


class TestSpineAlignmentAngle:
    def test_vertical_spine(self):
        """Shoulders directly above hips → angle close to 0."""
        lm = _make_landmarks({
            LS: _lm(0.45, 0.3), RS: _lm(0.55, 0.3),
            LH: _lm(0.45, 0.6), RH: _lm(0.55, 0.6),
        })
        angle = spine_alignment_angle(lm)
        assert angle < 2.0  # Nearly vertical

    def test_leaning_spine(self):
        """Shoulders shifted horizontally → angle > 0."""
        lm = _make_landmarks({
            LS: _lm(0.55, 0.3), RS: _lm(0.65, 0.3),  # mid = 0.6
            LH: _lm(0.45, 0.6), RH: _lm(0.55, 0.6),  # mid = 0.5
        })
        angle = spine_alignment_angle(lm)
        assert angle > 5.0


class TestStanceWidth:
    def test_wide_stance(self):
        lm = _make_landmarks({LA: _lm(0.2, 1.0), RA: _lm(0.8, 1.0)})
        assert stance_width(lm) == pytest.approx(0.6)

    def test_narrow_stance(self):
        lm = _make_landmarks({LA: _lm(0.45, 1.0), RA: _lm(0.55, 1.0)})
        assert stance_width(lm) == pytest.approx(0.1)

    def test_together(self):
        lm = _make_landmarks({LA: _lm(0.5, 1.0), RA: _lm(0.5, 1.0)})
        assert stance_width(lm) == pytest.approx(0.0)


class TestArmSymmetry:
    def test_symmetric_arms(self):
        lm = _make_landmarks({
            LS: _lm(0.4, 0.3), RS: _lm(0.6, 0.3),
            LW: _lm(0.2, 0.3), RW: _lm(0.8, 0.3),
        })
        assert arm_symmetry(lm) < 0.01

    def test_asymmetric_arms(self):
        lm = _make_landmarks({
            LS: _lm(0.4, 0.3), RS: _lm(0.6, 0.3),
            LW: _lm(0.1, 0.3), RW: _lm(0.65, 0.3),  # Right arm is shorter
        })
        assert arm_symmetry(lm) > 0.1


class TestLegSymmetry:
    def test_symmetric_legs(self):
        lm = _make_landmarks({
            LH: _lm(0.4, 0.6), RH: _lm(0.6, 0.6),
            LA: _lm(0.4, 1.0), RA: _lm(0.6, 1.0),
        })
        assert leg_symmetry(lm) < 0.01

    def test_asymmetric_legs(self):
        lm = _make_landmarks({
            LH: _lm(0.4, 0.6), RH: _lm(0.6, 0.6),
            LA: _lm(0.4, 1.0), RA: _lm(0.6, 0.7),  # Right leg shorter
        })
        assert leg_symmetry(lm) > 0.1


class TestBodyCenterline:
    def test_centered(self):
        lm = _make_landmarks({
            LS: _lm(0.4, 0.3), RS: _lm(0.6, 0.3),
            LH: _lm(0.4, 0.6), RH: _lm(0.6, 0.6),
        })
        assert body_centerline_x(lm) == pytest.approx(0.5)


class TestForwardLean:
    def test_no_lean(self):
        lm = _make_landmarks({
            LS: _lm(0.4, 0.3, 0.0), RS: _lm(0.6, 0.3, 0.0),
            LH: _lm(0.4, 0.6, 0.0), RH: _lm(0.6, 0.6, 0.0),
        })
        assert forward_lean(lm) == pytest.approx(0.0)

    def test_forward_lean(self):
        lm = _make_landmarks({
            LS: _lm(0.4, 0.3, -0.2), RS: _lm(0.6, 0.3, -0.2),
            LH: _lm(0.4, 0.6, 0.0), RH: _lm(0.6, 0.6, 0.0),
        })
        assert forward_lean(lm) < 0  # Negative = forward
