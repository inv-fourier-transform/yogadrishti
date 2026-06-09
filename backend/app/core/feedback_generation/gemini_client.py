"""Google Gemini API client for grounded yoga feedback generation.

Uses the new `google-genai` SDK (replaces deprecated `google-generativeai`).
Includes a timeout to prevent hanging during demo recordings.
Supports model fallback when primary model is overloaded.
"""
from __future__ import annotations
import asyncio
from app.config import get_settings
from app.utils.logging import logger
from app.utils.exceptions import LLMError

SETTINGS = get_settings()

# Timeout for Gemini API call (seconds)
_API_TIMEOUT = 25

# System instruction for grounded yoga feedback
_SYSTEM_INSTRUCTION = (
    "You are a warm, experienced yoga instructor providing detailed, personalized "
    "feedback — like a trusted teacher speaking directly to a student after observing "
    "their pose. Your tone is encouraging, knowledgeable, and conversational.\n\n"
    "VOICE & STYLE:\n"
    "- Speak naturally, as a caring instructor would in person — not like a checklist.\n"
    "- Use plain language a beginner would understand, but include proper yoga "
    "terminology where it adds clarity.\n"
    "- Be descriptive: explain WHAT to correct, WHY it matters for the pose's "
    "benefits and safety, and HOW to physically make the adjustment.\n"
    "- Include body awareness cues (e.g., 'feel the energy drawing upward from your "
    "sit bones', 'imagine pressing the floor away').\n"
    "- Weave in breath coordination where relevant (e.g., 'exhale as you fold deeper', "
    "'breathe into the stretch').\n"
    "- Celebrate genuine effort — be specific about what looks good, not just generic praise.\n\n"
    "GROUNDING RULES:\n"
    "- You MUST only reference facts present in the structured data provided.\n"
    "- Do NOT invent issues, angles, or corrections not in the data.\n"
    "- For alignment guidance, reference authoritative yoga instruction sources "
    "(tummee.com, yogapoint.com).\n"
    "- Always prioritize the Sanskrit name for looking up correct alignment cues; "
    "fall back to the English name if needed.\n"
    "- IMPORTANT: Always provide complete, useful feedback with ALL requested sections.\n"
    "- Never produce empty or overly brief responses.\n"
    "- Do NOT use markdown headings (#). Use **bold** for section headers."
)


def _call_gemini(prompt: str, model: str) -> str:
    """Synchronous Gemini call (run in thread to avoid blocking event loop)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=SETTINGS.gemini_api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            temperature=0.5,
            max_output_tokens=1536,
            top_p=0.9,
        ),
    )

    # Handle responses that include thought parts (thinking models)
    text = ""
    if hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text += part.text
    if not text:
        text = response.text or ""

    return text


def _call_with_fallback(prompt: str) -> str:
    """Try primary model, fall back to secondary on failure."""
    models = [SETTINGS.gemini_model]
    if SETTINGS.gemini_fallback_model and SETTINGS.gemini_fallback_model != SETTINGS.gemini_model:
        models.append(SETTINGS.gemini_fallback_model)

    last_error = None
    for model in models:
        try:
            logger.info(f"Calling Gemini model: {model}")
            text = _call_gemini(prompt, model)
            if text and len(text.strip()) >= 30:
                return text
            logger.warning(f"Model {model} returned insufficient text ({len(text or '')} chars)")
        except Exception as e:
            last_error = e
            logger.warning(f"Model {model} failed: {e}, trying next...")
            continue

    raise last_error or LLMError("All Gemini models failed")


async def generate_feedback(prompt: str) -> str:
    """
    Call Gemini API with a timeout to prevent hanging.
    Returns the generated text or raises LLMError.
    """
    if not SETTINGS.gemini_api_key:
        raise LLMError("Gemini API key not configured. Set GEMINI_API_KEY in .env")

    try:
        # Run synchronous API call on a thread with timeout
        text = await asyncio.wait_for(
            asyncio.to_thread(_call_with_fallback, prompt),
            timeout=_API_TIMEOUT,
        )

        if not text or len(text.strip()) < 30:
            raise LLMError(f"Gemini returned insufficient feedback ({len(text or '')} chars)")

        return text.strip()

    except asyncio.TimeoutError:
        logger.error(f"Gemini API timed out after {_API_TIMEOUT}s — using fallback")
        raise LLMError(f"Gemini API timed out after {_API_TIMEOUT} seconds")
    except LLMError:
        raise
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise LLMError(f"Failed to generate feedback: {str(e)}")

