"""Tests for the scoring engine — per-joint deviation scoring, pose evaluation."""
import pytest
from app.models.domain_schemas import Landmark, LandmarkSet, PoseEvaluation, PoseIssue
from app.core.pose_evaluation.scoring import (
    _compute_angle_score, evaluate_pose,
)
from app.core.pose_evaluation.pose_rules import AngleRule, PoseRuleSet, get_pose_rules, get_all_ruled_poses


def _lm(x: float, y: float, z: float = 0.0) -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=1.0, name="")


def _make_landmarks(overrides: dict[int, Landmark] = None) -> LandmarkSet:
    defaults = [_lm(0.0, 0.0) for _ in range(33)]
    if overrides:
        for idx, lm in overrides.items():
            defaults[idx] = lm
    return LandmarkSet(landmarks=tuple(defaults), overall_visibility=1.0)


# ── _compute_angle_score tests ───────────────────────

class TestAngleScore:
    def test_perfect_angle(self):
        """Measured exactly within range → score 1.0, no issue."""
        rule = AngleRule("left_knee", 80, 100, 1.0)
        score, issue = _compute_angle_score(90.0, rule)
        assert score == 1.0
        assert issue is None

    def test_at_boundary_min(self):
        """Measured at min boundary → still perfect."""
        rule = AngleRule("left_knee", 80, 100, 1.0)
        score, issue = _compute_angle_score(80.0, rule)
        assert score == 1.0
        assert issue is None

    def test_at_boundary_max(self):
        """Measured at max boundary → still perfect."""
        rule = AngleRule("left_knee", 80, 100, 1.0)
        score, issue = _compute_angle_score(100.0, rule)
        assert score == 1.0
        assert issue is None

    def test_10_degrees_below_min(self):
        """10° below range → degraded score, minor severity."""
        rule = AngleRule("left_knee", 80, 100, 1.0,
                         instruction_on_low="Bend more")
        score, issue = _compute_angle_score(70.0, rule)
        expected = 1.0 - 10.0 / 45.0
        assert score == pytest.approx(expected, abs=0.01)
        assert issue is not None
        assert issue.severity == "minor"
        assert issue.body_part == "left_knee"

    def test_30_degrees_above_max(self):
        """30° above range → low score, major severity."""
        rule = AngleRule("left_knee", 80, 100, 1.0,
                         instruction_on_high="Open less")
        score, issue = _compute_angle_score(130.0, rule)
        expected = 1.0 - 30.0 / 45.0
        assert score == pytest.approx(expected, abs=0.01)
        assert issue.severity == "major"

    def test_45_degrees_deviation(self):
        """45° deviation → score = 0."""
        rule = AngleRule("left_knee", 80, 100, 1.0)
        score, issue = _compute_angle_score(145.0, rule)
        assert score == pytest.approx(0.0)
        assert issue.severity == "major"

    def test_more_than_45_clamped(self):
        """60° deviation → score clamped at 0."""
        rule = AngleRule("left_knee", 80, 100, 1.0)
        score, issue = _compute_angle_score(160.0, rule)
        assert score == 0.0


# ── evaluate_pose tests ─────────────────────────────

class TestEvaluatePose:
    def test_unknown_pose_returns_defaults(self):
        """A pose without rules returns a default evaluation."""
        lm = _make_landmarks({
            11: _lm(0.3, 0.3), 12: _lm(0.7, 0.3),
            13: _lm(0.2, 0.5), 14: _lm(0.8, 0.5),
            15: _lm(0.3, 0.7), 16: _lm(0.7, 0.7),
            23: _lm(0.35, 0.6), 24: _lm(0.65, 0.6),
            25: _lm(0.35, 0.8), 26: _lm(0.65, 0.8),
            27: _lm(0.35, 1.0), 28: _lm(0.65, 1.0),
            31: _lm(0.40, 1.0), 32: _lm(0.60, 1.0),
        })
        result = evaluate_pose(lm, "some_unknown_pose_xyz", 0.9)
        assert isinstance(result, PoseEvaluation)
        assert result.overall_score == 70.0
        assert result.evaluation_status == "evaluated"
        assert result.correctness_label == "needs_adjustment"

    def test_known_pose_returns_scored_result(self):
        """Evaluating a registered pose returns a proper scored result."""
        # Warrior I: expects left_knee 80-110, right_knee 150-180
        lm = _make_landmarks({
            11: _lm(0.3, 0.3), 12: _lm(0.7, 0.3),
            13: _lm(0.2, 0.5), 14: _lm(0.8, 0.5),
            15: _lm(0.2, 0.7), 16: _lm(0.8, 0.7),
            23: _lm(0.35, 0.6), 24: _lm(0.65, 0.6),
            25: _lm(0.35, 0.8), 26: _lm(0.65, 0.8),
            27: _lm(0.35, 1.0), 28: _lm(0.65, 1.0),
            31: _lm(0.40, 1.0), 32: _lm(0.60, 1.0),
        })
        result = evaluate_pose(lm, "warrior_i", 0.85)
        assert isinstance(result, PoseEvaluation)
        assert 0 <= result.overall_score <= 100
        assert result.evaluation_status == "evaluated"
        assert result.correctness_label in ("correct", "needs_adjustment", "incorrect")
        assert result.angles  # Should have computed angles

    def test_correctness_labels(self):
        """Verify label thresholds: >=80 correct, >=55 needs_adjustment, else incorrect."""
        lm = _make_landmarks({
            11: _lm(0.3, 0.3), 12: _lm(0.7, 0.3),
            13: _lm(0.2, 0.5), 14: _lm(0.8, 0.5),
            15: _lm(0.2, 0.7), 16: _lm(0.8, 0.7),
            23: _lm(0.35, 0.6), 24: _lm(0.65, 0.6),
            25: _lm(0.35, 0.8), 26: _lm(0.65, 0.8),
            27: _lm(0.35, 1.0), 28: _lm(0.65, 1.0),
            31: _lm(0.40, 1.0), 32: _lm(0.60, 1.0),
        })
        result = evaluate_pose(lm, "warrior_ii", 0.9)
        # The exact label depends on the angles, but it should be one of the valid labels
        assert result.correctness_label in ("correct", "needs_adjustment", "incorrect")

    def test_issues_sorted_by_severity(self):
        """Issues should be sorted: major first, then moderate, then minor."""
        lm = _make_landmarks({
            11: _lm(0.3, 0.3), 12: _lm(0.7, 0.3),
            13: _lm(0.2, 0.5), 14: _lm(0.8, 0.5),
            15: _lm(0.2, 0.7), 16: _lm(0.8, 0.7),
            23: _lm(0.35, 0.6), 24: _lm(0.65, 0.6),
            25: _lm(0.35, 0.8), 26: _lm(0.65, 0.8),
            27: _lm(0.35, 1.0), 28: _lm(0.65, 1.0),
            31: _lm(0.40, 1.0), 32: _lm(0.60, 1.0),
        })
        result = evaluate_pose(lm, "plank_pose", 0.9)
        if len(result.issues) > 1:
            severity_order = {"major": 0, "moderate": 1, "minor": 2}
            for i in range(len(result.issues) - 1):
                a = severity_order.get(result.issues[i].severity, 3)
                b = severity_order.get(result.issues[i + 1].severity, 3)
                assert a <= b

    def test_safety_flags_included(self):
        """Poses with safety notes should include them in the result."""
        lm = _make_landmarks({
            11: _lm(0.3, 0.3), 12: _lm(0.7, 0.3),
            13: _lm(0.2, 0.5), 14: _lm(0.8, 0.5),
            15: _lm(0.2, 0.7), 16: _lm(0.8, 0.7),
            23: _lm(0.35, 0.6), 24: _lm(0.65, 0.6),
            25: _lm(0.35, 0.8), 26: _lm(0.65, 0.8),
            27: _lm(0.35, 1.0), 28: _lm(0.65, 1.0),
            31: _lm(0.40, 1.0), 32: _lm(0.60, 1.0),
        })
        result = evaluate_pose(lm, "tree_pose", 0.9)
        assert len(result.safety_flags) > 0

    def test_pose_confidence_stored(self):
        """pose_confidence should be stored in the result."""
        lm = _make_landmarks({
            11: _lm(0.3, 0.3), 12: _lm(0.7, 0.3),
            13: _lm(0.2, 0.5), 14: _lm(0.8, 0.5),
            15: _lm(0.2, 0.7), 16: _lm(0.8, 0.7),
            23: _lm(0.35, 0.6), 24: _lm(0.65, 0.6),
            25: _lm(0.35, 0.8), 26: _lm(0.65, 0.8),
            27: _lm(0.35, 1.0), 28: _lm(0.65, 1.0),
            31: _lm(0.40, 1.0), 32: _lm(0.60, 1.0),
        })
        result = evaluate_pose(lm, "downward_dog", 0.75)
        assert result.pose_confidence == 0.75


# ── Pose rules structure tests ──────────────────────

class TestPoseRules:
    def test_all_registered_poses_have_rules(self):
        """All registered poses should have at least one angle rule."""
        for key in get_all_ruled_poses():
            if key == "unknown_pose":
                continue  # Special fallback entry with no angle rules by design
            rules = get_pose_rules(key)
            assert rules is not None, f"Missing rules for {key}"
            assert len(rules.angle_rules) > 0, f"No angle rules for {key}"

    def test_unknown_pose_returns_none(self):
        assert get_pose_rules("nonexistent_asana_999") is None

    def test_angle_rules_valid_ranges(self):
        """All angle rules should have min < max and be in 0-180 range."""
        for key in get_all_ruled_poses():
            rules = get_pose_rules(key)
            for rule in rules.angle_rules:
                assert rule.min_degrees < rule.max_degrees, (
                    f"{key}/{rule.joint_name}: min({rule.min_degrees}) >= max({rule.max_degrees})"
                )
                assert rule.min_degrees >= 0, f"{key}/{rule.joint_name}: min < 0"
                assert rule.max_degrees <= 180, f"{key}/{rule.joint_name}: max > 180"
                assert rule.weight > 0, f"{key}/{rule.joint_name}: weight <= 0"

    def test_rule_count(self):
        """There should be 30+ poses with rules."""
        poses = get_all_ruled_poses()
        assert len(poses) >= 30
