"""Tests for history comparison logic."""
import pytest
from app.models.domain_schemas import AttemptComparison
from app.core.feedback_generation.history_comparison import (
    compare_attempts, _compare_angles, _parse_summary, summarize_pose_progress,
)


class TestCompareAttempts:
    def test_no_history(self):
        """No previous or best attempt → first attempt."""
        result = compare_attempts(
            current_score=80.0,
            current_angles={"left_knee": 90.0},
            current_issues=[],
            previous_attempt=None,
            best_attempt=None,
        )
        assert not result.historical_context_available
        assert not result.previous_attempt_exists
        assert "first" in result.progress_summary.lower()

    def test_improvement(self):
        """Current score > previous → improvement."""
        result = compare_attempts(
            current_score=85.0,
            current_angles={"left_knee": 92.0},
            current_issues=[],
            previous_attempt={
                "overall_score": 70.0,
                "summary_json": '{"angles":{"left_knee":85.0}}',
            },
            best_attempt=None,
        )
        assert result.historical_context_available
        assert result.previous_attempt_exists
        assert result.current_vs_previous_delta == 15.0
        assert "improvement" in result.progress_summary.lower() or "improved" in result.progress_summary.lower()

    def test_decline(self):
        """Current score < previous → decline."""
        result = compare_attempts(
            current_score=55.0,
            current_angles={"left_knee": 70.0},
            current_issues=[],
            previous_attempt={
                "overall_score": 80.0,
                "summary_json": '{"angles":{"left_knee":90.0}}',
            },
            best_attempt=None,
        )
        assert result.current_vs_previous_delta == -25.0
        assert "decreased" in result.progress_summary.lower()

    def test_similar(self):
        """Current score within ±5 → similar."""
        result = compare_attempts(
            current_score=78.0,
            current_angles={"left_knee": 90.0},
            current_issues=[],
            previous_attempt={
                "overall_score": 75.0,
                "summary_json": '{"angles":{"left_knee":89.0}}',
            },
            best_attempt=None,
        )
        assert result.current_vs_previous_delta == 3.0
        assert "similar" in result.progress_summary.lower()

    def test_best_attempt_comparison(self):
        """Compares with best attempt."""
        result = compare_attempts(
            current_score=75.0,
            current_angles={},
            current_issues=[],
            previous_attempt=None,
            best_attempt={"overall_score": 90.0},
        )
        assert result.best_score == 90.0
        assert result.current_vs_best_delta == -15.0

    def test_both_previous_and_best(self):
        """Both previous and best attempt data."""
        result = compare_attempts(
            current_score=80.0,
            current_angles={"left_knee": 95.0},
            current_issues=[],
            previous_attempt={
                "overall_score": 72.0,
                "summary_json": '{"angles":{"left_knee":88.0}}',
            },
            best_attempt={"overall_score": 92.0},
        )
        assert result.previous_score == 72.0
        assert result.best_score == 92.0
        assert result.current_vs_previous_delta == 8.0
        assert result.current_vs_best_delta == -12.0


class TestCompareAngles:
    def test_no_overlap(self):
        improved, declined, unchanged = _compare_angles(
            {"left_knee": 90.0}, {"right_knee": 85.0}
        )
        assert improved == []
        assert declined == []
        assert unchanged == []

    def test_unchanged(self):
        improved, declined, unchanged = _compare_angles(
            {"left_knee": 90.0}, {"left_knee": 91.0}
        )
        assert "left knee" in unchanged

    def test_improved(self):
        improved, declined, unchanged = _compare_angles(
            {"left_knee": 95.0}, {"left_knee": 80.0}
        )
        assert "left knee" in improved

    def test_declined(self):
        improved, declined, unchanged = _compare_angles(
            {"left_knee": 75.0}, {"left_knee": 90.0}
        )
        assert "left knee" in declined


class TestParseSummary:
    def test_valid_json(self):
        result = _parse_summary('{"angles":{"a":1}}')
        assert result == {"angles": {"a": 1}}

    def test_dict_passthrough(self):
        result = _parse_summary({"key": "val"})
        assert result == {"key": "val"}

    def test_invalid_json(self):
        assert _parse_summary("not json") == {}

    def test_empty_string(self):
        assert _parse_summary("") == {}

    def test_none(self):
        assert _parse_summary(None) == {}


class TestSummarizePoseProgress:
    def test_no_history(self):
        comp = AttemptComparison(
            historical_context_available=False,
            progress_summary="First attempt.",
        )
        result = summarize_pose_progress(comp)
        assert "First attempt" in result

    def test_with_areas(self):
        comp = AttemptComparison(
            historical_context_available=True,
            progress_summary="Improved overall.",
            improved_areas=["left knee"],
            declined_areas=["right shoulder"],
        )
        result = summarize_pose_progress(comp)
        assert "Improved" in result
        assert "left knee" in result
        assert "right shoulder" in result
