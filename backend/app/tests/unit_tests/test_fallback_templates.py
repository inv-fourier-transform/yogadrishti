"""Tests for fallback feedback templates."""
import pytest
from app.models.domain_schemas import PoseEvaluation, PoseIssue, AttemptComparison
from app.core.feedback_generation.fallback_templates import generate_fallback_feedback, _label_text


def _make_eval(**kwargs) -> PoseEvaluation:
    defaults = dict(
        pose_name="Tree Pose",
        sanskrit_name="Vrksasana",
        pose_confidence=0.9,
        evaluation_status="evaluated",
        overall_score=85.0,
        correctness_label="correct",
    )
    defaults.update(kwargs)
    return PoseEvaluation(**defaults)


def _make_issue(part="left_knee", severity="minor") -> PoseIssue:
    return PoseIssue(
        body_part=part, measured_value=75.0,
        expected_min=80.0, expected_max=100.0,
        severity=severity, instruction_key=f"Adjust your {part}.",
        description=f"{part} is off.",
    )


class TestLabelText:
    def test_correct(self):
        assert "✅" in _label_text("correct")

    def test_needs_adjustment(self):
        assert "🟡" in _label_text("needs_adjustment")

    def test_incorrect(self):
        assert "🔴" in _label_text("incorrect")

    def test_unknown(self):
        assert _label_text("some_random") == "some_random"


class TestFallbackFeedback:
    def test_correct_pose(self):
        feedback = generate_fallback_feedback(_make_eval())
        assert "Great work" in feedback
        assert "Tree Pose" in feedback
        assert "Vrksasana" in feedback
        assert "85" in feedback

    def test_needs_adjustment(self):
        feedback = generate_fallback_feedback(
            _make_eval(correctness_label="needs_adjustment", overall_score=65.0)
        )
        assert "adjustments" in feedback.lower()

    def test_incorrect(self):
        feedback = generate_fallback_feedback(
            _make_eval(correctness_label="incorrect", overall_score=30.0)
        )
        assert "correction" in feedback.lower()

    def test_unreliable(self):
        feedback = generate_fallback_feedback(_make_eval(
            correctness_label="not_reliably_evaluable",
            reliability_reason="Too few landmarks visible.",
        ))
        assert "could not" in feedback.lower()
        assert "landmarks" in feedback.lower()

    def test_includes_issues(self):
        ev = _make_eval(correctness_label="needs_adjustment", overall_score=60.0)
        ev.issues = [_make_issue("left_knee", "major")]
        feedback = generate_fallback_feedback(ev)
        assert "🔴" in feedback
        assert "left_knee" in feedback

    def test_includes_safety_flags(self):
        ev = _make_eval()
        ev.safety_flags = ["If you feel unsteady, use a wall."]
        feedback = generate_fallback_feedback(ev)
        assert "Safety" in feedback
        assert "wall" in feedback

    def test_improvement_with_history(self):
        ev = _make_eval(overall_score=80.0)
        comp = AttemptComparison(
            historical_context_available=True,
            previous_attempt_exists=True,
            previous_score=70.0,
            current_vs_previous_delta=10.0,
            improved_areas=["left knee"],
        )
        feedback = generate_fallback_feedback(ev, comp)
        assert "Improved" in feedback
        assert "10" in feedback

    def test_decline_with_history(self):
        ev = _make_eval(overall_score=50.0, correctness_label="needs_adjustment")
        comp = AttemptComparison(
            historical_context_available=True,
            previous_attempt_exists=True,
            previous_score=70.0,
            current_vs_previous_delta=-20.0,
            declined_areas=["right shoulder"],
        )
        feedback = generate_fallback_feedback(ev, comp)
        assert "decreased" in feedback.lower()
        assert "right shoulder" in feedback

    def test_first_attempt(self):
        ev = _make_eval(overall_score=70.0)
        comp = AttemptComparison(
            historical_context_available=False,
            previous_attempt_exists=False,
        )
        feedback = generate_fallback_feedback(ev, comp)
        assert "first" in feedback.lower()

    def test_next_step_coaching(self):
        ev = _make_eval(correctness_label="needs_adjustment", overall_score=60.0)
        ev.issues = [_make_issue("left_knee")]
        feedback = generate_fallback_feedback(ev)
        assert "Next step" in feedback
