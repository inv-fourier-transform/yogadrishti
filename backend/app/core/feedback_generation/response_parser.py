"""Response parser and validator for LLM feedback output."""


def parse_feedback_response(raw_text: str) -> str:
    """
    Parse and clean the LLM response text.
    Strips markdown formatting, excessive whitespace, etc.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # Remove leading/trailing markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    return text


def validate_feedback(feedback: str, pose_name: str) -> bool:
    """
    Basic validation that feedback is reasonable.
    Returns True if feedback passes validation.
    """
    if not feedback or len(feedback) < 20:
        return False

    # Check it's not just an error or refusal
    refusal_indicators = [
        "i cannot", "i can't", "i'm unable", "as an ai",
        "i don't have access", "no image provided",
    ]
    lower = feedback.lower()
    if any(indicator in lower for indicator in refusal_indicators):
        return False

    return True
