"""
Node: Sanitize transcript (remove PII, clean up text)
"""
import re
from loguru import logger
from models import PipelineState


def sanitize_node(state: PipelineState) -> PipelineState:
    """Clean and sanitize the transcript — remove potential PII patterns."""
    logger.info("─── NODE: sanitize_node ───")

    transcript = state.get("transcript", "")
    if not transcript:
        state["sanitized_transcript"] = ""
        return state

    sanitized = transcript

    # Mask phone numbers (various formats)
    sanitized = re.sub(
        r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "[PHONE_REDACTED]",
        sanitized,
    )

    # Mask email addresses
    sanitized = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "[EMAIL_REDACTED]",
        sanitized,
    )

    # Mask credit card–like numbers
    sanitized = re.sub(
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "[CARD_REDACTED]",
        sanitized,
    )

    # Mask SSN-like patterns
    sanitized = re.sub(
        r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
        "[SSN_REDACTED]",
        sanitized,
    )

    # Clean up extra whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    state["sanitized_transcript"] = sanitized
    logger.info(f"Sanitized transcript ({len(sanitized)} chars)")
    return state
