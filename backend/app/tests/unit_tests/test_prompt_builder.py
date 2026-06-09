"""Tests for prompt builder — structured LLM prompt generation."""
import pytest
from app.models.domain_schemas import (
    PoseEvaluation, PoseIssue, FeedbackPayload,
    AttemptComparison, VideoAnalysisResult, FrameResult,
)
from app.core.feedback_generation.prompt_builder import build_feedback_prompt


def _make_eval(**kwargs) -> PoseEvaluation:
    defaults = dict(
        pose_name="Warrior II",
        sanskrit_name="Virabhadrasana II",
        pose_confidence=0.85,
        evaluation_status="evaluated",
        overall_score=72.0,
        correctness_label="needs_adjustment",
    )
    defaults.update(kwargs)
    return PoseEvaluation(**defaults)


def _make_issue(part="left_knee", severity="moderate") -> PoseIssue:
    return PoseIssue(
        body_part=part, measured_value=75.0,
        expected_min=80.0, expected_max=100.0,
        severity=severity,
        instruction_key=f"Adjust your {part}.",
        description=f"{part} is at 75° (expected 80°–100°).",
    )


class TestBuildFeedbackPrompt:
    def test_no_evaluation(self):
        payload = FeedbackPayload(pose_name="Tree Pose", evaluation=None)
        prompt = build_feedback_prompt(payload)
        assert "No evaluation data" in prompt

    def test_basic_prompt_structure(self):
        ev = _make_eval()
        payload = FeedbackPayload(pose_name=ev.pose_name, evaluation=ev)
        prompt = build_feedback_prompt(payload)
        assert "Warrior II" in prompt
        assert "Virabhadrasana II" in prompt
        assert "72" in prompt
        assert "needs_adjustment" in prompt
        assert "yoga instructor" in prompt.lower()

    def test_includes_issues(self):
        ev = _make_eval()
        ev.issues = [_make_issue("left_knee"), _make_issue("right_shoulder")]
        payload = FeedbackPayload(pose_name=ev.pose_name, evaluation=ev)
        prompt = build_feedback_prompt(payload)
        assert "left_knee" in prompt
        assert "right_shoulder" in prompt
        assert "severity" in prompt.lower()

    def test_includes_safety_notes(self):
        ev = _make_eval()
        ev.safety_flags = ["Keep front knee over ankle."]
        payload = FeedbackPayload(pose_name=ev.pose_name, evaluation=ev)
        prompt = build_feedback_prompt(payload)
        assert "Safety" in prompt
        assert "knee over ankle" in prompt

    def test_includes_reliability_warning(self):
        ev = _make_eval(reliability_reason="Low visibility in lower body.")
        payload = FeedbackPayload(pose_name=ev.pose_name, evaluation=ev)
        prompt = build_feedback_prompt(payload)
        assert "Reliability" in prompt
        assert "Low visibility" in prompt

    def test_includes_historical_comparison(self):
        ev = _make_eval()
        comp = AttemptComparison(
            historical_context_available=True,
            previous_attempt_exists=True,
            previous_score=65.0,
            current_vs_previous_delta=7.0,
            improved_areas=["left knee"],
            declined_areas=["right shoulder"],
            best_score=80.0,
            current_vs_best_delta=-8.0,
        )
        payload = FeedbackPayload(
            pose_name=ev.pose_name, evaluation=ev, comparison=comp,
        )
        prompt = build_feedback_prompt(payload)
        assert "Previous Score: 65.0" in prompt
        assert "+7.0" in prompt
        assert "left knee" in prompt
        assert "right shoulder" in prompt
        assert "80.0" in prompt

    def test_includes_video_analysis(self):
        ev = _make_eval()
        vr = VideoAnalysisResult(
            frame_count=100, analyzed_frame_count=10,
            consistency_score=78.0,
        )
        payload = FeedbackPayload(
            pose_name=ev.pose_name, evaluation=ev,
            is_video=True, video_result=vr,
        )
        prompt = build_feedback_prompt(payload)
        assert "Video Analysis" in prompt
        assert "10/100" in prompt
        assert "78" in prompt

    def test_output_instructions_present(self):
        ev = _make_eval()
        payload = FeedbackPayload(pose_name=ev.pose_name, evaluation=ev)
        prompt = build_feedback_prompt(payload)
        assert "THREE layers" in prompt or "three layers" in prompt.lower()
        assert "200 words" in prompt
        assert "Do NOT" in prompt
