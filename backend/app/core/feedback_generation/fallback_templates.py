"""Deterministic fallback feedback templates when LLM is unavailable."""
from __future__ import annotations
from app.models.domain_schemas import PoseEvaluation, AttemptComparison


def generate_fallback_feedback(
    evaluation: PoseEvaluation,
    comparison: AttemptComparison | None = None,
) -> str:
    """
    Generate feedback purely from deterministic evaluation data.
    Used when the LLM is unavailable or fails.
    ALWAYS produces useful output — never returns empty or useless text.
    Written in a warm, descriptive tone to feel like a real instructor.
    """
    lines = []

    # Layer 1: Pose identification
    pose_label = f"**{evaluation.pose_name}**"
    if evaluation.sanskrit_name:
        pose_label += f" ({evaluation.sanskrit_name})"
    lines.append(pose_label)
    lines.append(f"Score: {evaluation.overall_score:.0f}/100 — {_label_text(evaluation.correctness_label)}")

    # Layer 2: What's going well — descriptive and pose-specific
    lines.append("\n**What You're Doing Well:**")
    pose = evaluation.pose_name
    if evaluation.correctness_label == "correct":
        lines.append(
            f"Wonderful work on your {pose}! Your overall alignment is looking "
            f"strong and well-balanced. The fact that you're holding this shape with "
            f"this level of precision shows real progress in your practice — keep "
            f"building on this solid foundation."
        )
    elif evaluation.correctness_label == "needs_adjustment":
        lines.append(
            f"You've established a solid foundation in {pose} — the basic shape "
            f"and intention of the pose are clearly there. That takes body awareness "
            f"and effort, so give yourself credit. With a few targeted adjustments, "
            f"you can refine this pose even further."
        )
    elif evaluation.correctness_label == "incorrect":
        lines.append(
            f"You're showing courage by working on {pose} — that's genuinely the "
            f"hardest part. Every practitioner starts from where you are right now. "
            f"Let's focus on building the key alignment points one step at a time."
        )
    else:
        lines.append(
            f"You're practicing {pose}, and that commitment to showing up on the "
            f"mat is what matters most. Let's work through some guidance to help "
            f"you deepen your expression of this pose."
        )

    # Layer 3: Issues / Corrections — descriptive with WHY and HOW
    if evaluation.issues:
        lines.append("\n**Suggestions for Improvement:**")
        for issue in evaluation.issues[:5]:
            severity_icon = {"major": "🔴", "moderate": "🟡", "minor": "🟢"}.get(issue.severity, "⚪")
            body_label = issue.body_part.replace('_', ' ')

            # Build a richer correction based on severity
            if issue.severity == "major":
                lines.append(
                    f"{severity_icon} **{issue.instruction_key}** "
                    f"Your {body_label} needs significant attention here — this is one of "
                    f"the key alignment points that defines {pose}. Focus on making this "
                    f"adjustment first, as it will improve your overall stability and the "
                    f"effectiveness of the pose. Take a breath, and on your next exhale, "
                    f"gently work toward the correction."
                )
            elif issue.severity == "moderate":
                lines.append(
                    f"{severity_icon} **{issue.instruction_key}** "
                    f"Your {body_label} is close but could use some refinement. "
                    f"This adjustment will help you access the full benefits of the pose "
                    f"and improve your balance. Try to bring awareness to this area — "
                    f"breathe into it and make small, mindful adjustments."
                )
            else:
                lines.append(
                    f"{severity_icon} **{issue.instruction_key}** "
                    f"A small tweak to your {body_label} will polish your form here. "
                    f"It's a subtle adjustment, but these details are what separate good "
                    f"form from great form. Stay aware of this area as you hold the pose."
                )
    else:
        lines.append("\n**Suggestions for Improvement:**")
        lines.append(
            "No specific misalignments were detected — that's excellent! To continue "
            "refining your practice, focus on maintaining steady, rhythmic breathing "
            "throughout the hold. Keep your core gently engaged and bring awareness "
            "to how your weight distributes through your body. These subtle refinements "
            "deepen the pose from the inside out."
        )

    # Safety
    if evaluation.safety_flags:
        lines.append(f"\n**Safety:** {evaluation.safety_flags[0]}")

    # Layer 4: Historical comparison
    if comparison and comparison.historical_context_available and comparison.previous_attempt_exists:
        lines.append("\n**Progress:**")
        delta = comparison.current_vs_previous_delta or 0
        if delta > 5:
            lines.append(
                f"✅ You've improved by {delta:.0f} points since your last attempt — "
                f"that's real, measurable progress! Your practice is paying off."
            )
        elif delta > -5:
            lines.append(
                "➡️ Your score is consistent with your last attempt. Consistency is a "
                "sign of solid muscle memory developing — keep at it."
            )
        else:
            lines.append(
                f"⬇️ Your score dipped by {abs(delta):.0f} points from last time. "
                f"Don't worry — this is completely normal. Some days our bodies "
                f"respond differently. Focus on the adjustments below and you'll bounce back."
            )

        if comparison.improved_areas:
            areas = ', '.join(comparison.improved_areas[:3])
            lines.append(f"Areas that improved: {areas} — great work on these!")
        if comparison.declined_areas:
            areas = ', '.join(comparison.declined_areas[:3])
            lines.append(f"Areas to focus on: {areas}")

    elif comparison and not comparison.previous_attempt_exists:
        lines.append(
            "\nThis is your first recorded attempt for this pose — a perfect starting point "
            "to track your growth from here."
        )

    # Layer 5: Key focus — descriptive with encouragement
    lines.append("\n**Key Focus:**")
    if evaluation.issues:
        top_issue = evaluation.issues[0]
        body_label = top_issue.body_part.replace('_', ' ')
        lines.append(
            f"{top_issue.instruction_key} This is the single most impactful adjustment "
            f"you can make right now. In your next practice, bring your attention to your "
            f"{body_label} early in the pose and make it your anchor point. "
            f"Small, consistent improvements here will transform your {pose} over time. "
            f"You're doing great — keep showing up! 🧘"
        )
    else:
        lines.append(
            "Your alignment is looking excellent! Challenge yourself to hold the pose "
            "for a few extra breaths, focusing on steady inhales and exhales. "
            "Consistency and breath awareness are what take a good practice to a great one. "
            "You're doing wonderfully — trust the process! 🧘"
        )

    return "\n".join(lines)


def _label_text(label: str) -> str:
    return {
        "correct": "Well Done ✅",
        "needs_adjustment": "Needs Adjustment 🟡",
        "incorrect": "Needs Correction 🔴",
        "not_reliably_evaluable": "Basic Assessment ⚠️",
    }.get(label, label)
