"""Build structured prompts for grounded Gemini feedback generation.

Design principles:
1. Sanskrit name is prioritized for pose identification (standardized)
2. Only structured evaluation data is provided — no ambiguous text
3. The LLM is instructed to reference tummee.com/yogapoint.com for alignment cues
4. Strict anti-hallucination rules are enforced
5. NEVER tell the LLM the data is "unreliable" — this causes it to give empty responses
"""
from __future__ import annotations
from app.models.domain_schemas import FeedbackPayload, AttemptComparison


def build_feedback_prompt(payload: FeedbackPayload) -> str:
    """
    Build a structured prompt for LLM feedback generation.
    The LLM receives ONLY structured evaluation results — it must NOT
    invent geometric facts or speculate about things not in the data.
    """
    parts = []

    evaluation = payload.evaluation
    if not evaluation:
        return "No evaluation data available. Unable to generate feedback."

    # ── Pose Identification (Sanskrit-first) ──
    parts.append("## Pose Identification")
    if evaluation.sanskrit_name:
        parts.append(f"Sanskrit Name: {evaluation.sanskrit_name}")
        parts.append(f"English Name: {evaluation.pose_name}")
        parts.append(
            f"Use the Sanskrit name '{evaluation.sanskrit_name}' as the primary reference "
            f"when describing correct alignment. If this does not match a known pose, "
            f"use the English name '{evaluation.pose_name}' instead."
        )
    else:
        parts.append(f"English Name: {evaluation.pose_name}")
        parts.append("No Sanskrit name available. Use the English name for alignment reference.")

    # ── Current Attempt Data ──
    parts.append(f"\n## Current Attempt")
    parts.append(f"Overall Score: {evaluation.overall_score}/100")
    parts.append(f"Assessment: {_label_to_text(evaluation.correctness_label)}")
    parts.append(f"Detection Confidence: {evaluation.pose_confidence:.0%}")

    # ── Issues Detected (the core data for corrections) ──
    if evaluation.issues:
        parts.append("\n### Alignment Issues Detected:")
        for issue in evaluation.issues[:6]:
            parts.append(
                f"- **{issue.body_part.replace('_', ' ').title()}**: {issue.description} "
                f"(severity: {issue.severity})"
            )
    else:
        parts.append("\n### Alignment Issues Detected: None")
        parts.append(
            "No specific misalignments were detected. Provide general alignment "
            "guidance for this pose based on correct form as described in authoritative "
            "yoga instruction sources (tummee.com, yogapoint.com)."
        )

    # ── Safety Notes ──
    if evaluation.safety_flags:
        parts.append(f"\n### Safety Notes: {'; '.join(evaluation.safety_flags)}")

    # ── Historical Comparison ──
    comparison = payload.comparison
    if comparison and comparison.historical_context_available:
        parts.append("\n## Historical Comparison")
        if comparison.previous_attempt_exists:
            parts.append(f"Previous Score: {comparison.previous_score}")
            parts.append(f"Score Change: {comparison.current_vs_previous_delta:+.1f}")
            if comparison.improved_areas:
                parts.append(f"Improved Areas: {', '.join(comparison.improved_areas)}")
            if comparison.declined_areas:
                parts.append(f"Areas Needing Work: {', '.join(comparison.declined_areas)}")
        if comparison.best_score is not None:
            parts.append(f"Personal Best Score: {comparison.best_score}")
            parts.append(f"Delta from Best: {comparison.current_vs_best_delta:+.1f}")

    # ── Video-specific ──
    if payload.is_video and payload.video_result:
        vr = payload.video_result
        parts.append(f"\n## Video Analysis")
        parts.append(f"Frames Analyzed: {vr.analyzed_frame_count}/{vr.frame_count}")
        parts.append(f"Consistency Score: {vr.consistency_score}/100")

    # ── Output Format (must match frontend rendering) ──
    # Build the label text for the score line
    label_text = _label_to_text(evaluation.correctness_label)
    label_icon = {
        "correct": "✅",
        "needs_adjustment": "🟡",
        "incorrect": "🔴",
        "not_reliably_evaluable": "⚠️",
    }.get(evaluation.correctness_label, "")

    # Build severity icons map for issues
    issue_bullets = ""
    if evaluation.issues:
        for issue in evaluation.issues[:5]:
            sev_icon = {"major": "🔴", "moderate": "🟡", "minor": "🟢"}.get(issue.severity, "⚪")
            issue_bullets += f"\n{sev_icon} (issue for {issue.body_part.replace('_', ' ')})"

    parts.append(
        "\n## Instructions for your response:\n"
        "You MUST produce your response in EXACTLY this format (keep the bold markers **). "
        "Do NOT skip or rearrange any section:\n\n"
        f"**{evaluation.pose_name}**"
        + (f" ({evaluation.sanskrit_name})" if evaluation.sanskrit_name else "")
        + "\n"
        f"Score: {evaluation.overall_score:.0f}/100 — "
        + (label_text + " " + label_icon)
        + "\n\n"
        "**What You're Doing Well:**\n"
        "(2-3 sentences acknowledging what the practitioner is doing correctly. "
        "Be specific — reference particular body parts or alignments that look good "
        "based on the data. If their score is high, celebrate the effort with genuine warmth. "
        "Mention how their current form relates to the ideal form of this pose as described "
        "by authoritative yoga instruction sources.)\n\n"
        "**Suggestions for Improvement:**\n"
        + (
            f"For EACH of the issues below, write a DESCRIPTIVE correction (2-3 sentences) "
            f"that includes:\n"
            f"  1. WHAT to adjust (the body part and direction)\n"
            f"  2. WHY it matters for this specific pose (e.g., deeper engagement, balance, safety)\n"
            f"  3. HOW to physically do it — include a body awareness cue or visualization "
            f"(e.g., 'imagine pressing the crown of your head toward the ceiling', "
            f"'feel your sit bones grounding into the mat')\n"
            f"Start each correction with the matching severity icon.\n"
            f"Issues:{issue_bullets}\n"
            f"Use the exact icon (🔴/🟡/🟢) at the start of each bullet line. "
            f"Where relevant, include a breathing tip within the correction."
            if evaluation.issues else
            "(Provide 2-3 descriptive alignment tips specific to THIS pose using ⚪ bullets. "
            "For each tip, explain what to do, why it matters, and include a body awareness cue.)"
        )
        + "\n\n"
        + (f"**Safety:** {evaluation.safety_flags[0]}\n\n" if evaluation.safety_flags else "")
        + "**Health Benefits:**\n"
        "(List 3-4 specific health benefits of THIS particular asana. "
        "Each benefit should be a single concise sentence starting with a '•' bullet. "
        "Cover physical, mental, and therapeutic benefits. Be specific to this pose — "
        "e.g., for Eagle Pose mention improved balance, shoulder flexibility, concentration, "
        "and strengthened calves. Do NOT use generic benefits that apply to all yoga.)\n\n"
        "**Key Focus:**\n"
        "(Write 2-3 sentences about the single most important thing to work on in their next practice. "
        "Explain why this matters for progressing in the pose and offer a practical micro-drill "
        "or mental cue they can try. End with genuine encouragement.)\n\n"
        "STRICT RULES:\n"
        "- You MUST include ALL sections above — do NOT omit any.\n"
        "- The first two lines (pose name + score) must appear EXACTLY as shown.\n"
        "- Address specific body parts and issues from the data when available.\n"
        "- When no issues are listed, provide GENERAL alignment guidance for this specific pose.\n"
        "- Do NOT refuse to give feedback — always provide helpful yoga instruction.\n"
        "- Do NOT mention history if no historical data is provided.\n"
        "- Do NOT claim numerical improvement unless the data shows it.\n"
        "- Keep response between 250-400 words.\n"
        "- Use second person ('you', 'your').\n"
        "- Be warm, descriptive, and genuinely helpful — like a real instructor.\n"
        "- Include at least one breathing or body awareness cue in your suggestions."
    )

    return "\n".join(parts)


def _label_to_text(label: str) -> str:
    """Convert internal label to human-readable text for the prompt."""
    return {
        "correct": "Well Done",
        "needs_adjustment": "Needs Adjustment",
        "incorrect": "Needs Correction",
        "not_reliably_evaluable": "Basic Assessment",
    }.get(label, "Basic Assessment")
