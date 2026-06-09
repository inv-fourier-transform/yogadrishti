"""Compare current pose attempt with previous/best attempts for personalized feedback."""
from __future__ import annotations
import json
from typing import Optional
from app.models.domain_schemas import AttemptComparison


def compare_attempts(
    current_score: float,
    current_angles: dict[str, float],
    current_issues: list[dict],
    previous_attempt: Optional[dict],
    best_attempt: Optional[dict],
) -> AttemptComparison:
    """
    Compare the current attempt against previous and best attempts.
    Returns structured comparison suitable for feedback generation.
    """
    if not previous_attempt and not best_attempt:
        return AttemptComparison(
            historical_context_available=False,
            previous_attempt_exists=False,
            progress_summary="This is the first recorded attempt for this pose.",
        )

    comparison = AttemptComparison(historical_context_available=True)

    # Compare with previous attempt
    if previous_attempt:
        comparison.previous_attempt_exists = True
        prev_score = previous_attempt.get("overall_score", 0)
        comparison.previous_score = prev_score
        comparison.current_vs_previous_delta = round(current_score - prev_score, 1)

        # Parse previous summary for angle comparison
        prev_summary = _parse_summary(previous_attempt.get("summary_json", "{}"))
        prev_angles = prev_summary.get("angles", {})

        improved, declined, unchanged = _compare_angles(current_angles, prev_angles)
        comparison.improved_areas = improved
        comparison.declined_areas = declined
        comparison.unchanged_areas = unchanged

        # Generate progress summary
        delta = comparison.current_vs_previous_delta
        if delta > 5:
            comparison.progress_summary = (
                f"Great improvement! Your score increased by {delta:.0f} points. "
                f"Areas that improved: {', '.join(improved[:3]) if improved else 'overall form'}."
            )
        elif delta > -5:
            comparison.progress_summary = (
                f"Your performance is similar to your last attempt. "
                f"Focus on: {', '.join(declined[:2]) if declined else 'maintaining your form'}."
            )
        else:
            comparison.progress_summary = (
                f"Your score decreased by {abs(delta):.0f} points compared to last time. "
                f"Areas that need attention: {', '.join(declined[:3]) if declined else 'overall alignment'}."
            )

    # Compare with best attempt
    if best_attempt:
        best_score = best_attempt.get("overall_score", 0)
        comparison.best_score = best_score
        comparison.current_vs_best_delta = round(current_score - best_score, 1)

    return comparison


def _compare_angles(current: dict[str, float], previous: dict[str, float]) -> tuple[list, list, list]:
    """Compare angle measurements between attempts."""
    improved = []
    declined = []
    unchanged = []

    for name, curr_val in current.items():
        if name in previous:
            prev_val = previous[name]
            diff = abs(curr_val - prev_val)
            if diff < 3:
                unchanged.append(name.replace("_", " "))
            elif curr_val > prev_val:  # Higher angle can be improvement or regression depending on context
                improved.append(name.replace("_", " "))
            else:
                declined.append(name.replace("_", " "))

    return improved[:5], declined[:5], unchanged[:5]


def _parse_summary(summary_str: str) -> dict:
    """Parse summary JSON safely."""
    try:
        if isinstance(summary_str, dict):
            return summary_str
        return json.loads(summary_str) if summary_str else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def summarize_pose_progress(comparison: AttemptComparison) -> str:
    """Generate a text summary of pose progress."""
    if not comparison.historical_context_available:
        return comparison.progress_summary

    lines = [comparison.progress_summary]

    if comparison.improved_areas:
        lines.append(f"Improved: {', '.join(comparison.improved_areas)}")
    if comparison.declined_areas:
        lines.append(f"Needs work: {', '.join(comparison.declined_areas)}")

    return " | ".join(lines)
