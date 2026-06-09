"""Tests for confidence and reliability gating."""
import pytest
import numpy as np
from app.models.domain_schemas import Landmark, LandmarkSet, PoseEvaluation
from app.core.pose_evaluation.confidence_gate import (
    check_landmark_visibility,
    check_image_quality,
    apply_reliability_gate,
)


def _lm(x=0.0, y=0.0, z=0.0, vis=1.0, name="") -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=vis, name=name)


def _make_landmarks(default_vis: float = 1.0, overrides: dict[int, float] = None) -> LandmarkSet:
    """Create 33 landmarks with default visibility, optionally overriding specific ones."""
    landmarks = [_lm(vis=default_vis, name=f"lm_{i}") for i in range(33)]
    if overrides:
        for idx, vis in overrides.items():
            landmarks[idx] = _lm(vis=vis, name=f"lm_{idx}")
    vises = [lm.visibility for lm in landmarks]
    return LandmarkSet(landmarks=tuple(landmarks), overall_visibility=sum(vises) / len(vises))


def _make_eval(**kwargs) -> PoseEvaluation:
    defaults = dict(
        pose_name="tree_pose",
        sanskrit_name="Vrksasana",
        pose_confidence=0.9,
        evaluation_status="evaluated",
        overall_score=85.0,
        correctness_label="correct",
    )
    defaults.update(kwargs)
    return PoseEvaluation(**defaults)


def _make_image(h: int = 640, w: int = 480) -> np.ndarray:
    """Create a non-blurry test image with noise."""
    rng = np.random.RandomState(42)
    return rng.randint(0, 256, (h, w, 3), dtype=np.uint8)


class TestCheckLandmarkVisibility:
    def test_all_visible(self):
        lm = _make_landmarks(default_vis=0.9)
        ratio, issues = check_landmark_visibility(lm, min_vis=0.5)
        assert ratio == pytest.approx(1.0)
        assert len(issues) == 0

    def test_all_hidden(self):
        lm = _make_landmarks(default_vis=0.1)
        ratio, issues = check_landmark_visibility(lm, min_vis=0.5)
        assert ratio == pytest.approx(0.0)
        assert len(issues) > 0

    def test_partial_visibility(self):
        # Half visible, half not
        overrides = {i: 0.1 for i in range(17)}
        lm = _make_landmarks(default_vis=0.9, overrides=overrides)
        ratio, issues = check_landmark_visibility(lm, min_vis=0.5)
        expected = (33 - 17) / 33
        assert ratio == pytest.approx(expected, abs=0.01)

    def test_essential_landmarks_hidden(self):
        # Hide core landmarks (shoulders and hips: indices 11, 12, 23, 24)
        overrides = {11: 0.1, 12: 0.1, 23: 0.1, 24: 0.1}
        lm = _make_landmarks(default_vis=0.9, overrides=overrides)
        ratio, issues = check_landmark_visibility(lm, min_vis=0.5)
        # Should flag essential landmarks as hidden
        assert any("not clearly visible" in issue for issue in issues)


class TestCheckImageQuality:
    def test_normal_image(self):
        img = _make_image(640, 480)
        issues = check_image_quality(img)
        # A random noise image has high-frequency content → not blurry
        low_res_issues = [i for i in issues if "resolution" in i.lower()]
        assert len(low_res_issues) == 0

    def test_too_small_image(self):
        img = _make_image(60, 60)
        issues = check_image_quality(img)
        assert any("resolution" in i.lower() for i in issues)

    def test_blurry_image(self):
        # Create a uniform image → Laplacian variance will be ~0
        img = np.ones((300, 300, 3), dtype=np.uint8) * 128
        issues = check_image_quality(img)
        assert any("blurry" in i.lower() for i in issues)


class TestApplyReliabilityGate:
    def test_reliable_evaluation_unchanged(self):
        """High-quality input should not change evaluation status."""
        evaluation = _make_eval()
        lm = _make_landmarks(default_vis=0.9)
        img = _make_image()
        result = apply_reliability_gate(evaluation, lm, img)
        assert result.evaluation_status == "evaluated"
        assert result.correctness_label == "correct"

    def test_low_visibility_downgrades(self):
        """Low landmark visibility should downgrade the evaluation."""
        evaluation = _make_eval()
        lm = _make_landmarks(default_vis=0.1)
        result = apply_reliability_gate(evaluation, lm)
        assert result.evaluation_status == "low_confidence"
        assert result.correctness_label == "not_reliably_evaluable"
        assert result.reliability_reason  # Should have a reason

    def test_low_pose_confidence_flags(self):
        """Low pose classification confidence should flag the result."""
        evaluation = _make_eval(pose_confidence=0.1)
        lm = _make_landmarks(default_vis=0.9)
        result = apply_reliability_gate(evaluation, lm)
        assert "confidence" in result.reliability_reason.lower()

    def test_no_image_still_works(self):
        """Should work without image (skip quality checks)."""
        evaluation = _make_eval()
        lm = _make_landmarks(default_vis=0.9)
        result = apply_reliability_gate(evaluation, lm, image=None)
        assert result.evaluation_status == "evaluated"
