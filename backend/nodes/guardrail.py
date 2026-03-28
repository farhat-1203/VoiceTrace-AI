"""
Node: Content Safety Guardrail
Uses the dedicated GuardrailService (Groq LLM + strict JSON classification prompt).
Applied to the raw transcript before any further processing.
"""
from loguru import logger
from models import PipelineState
from services.guardrail import check_safety  # ← dedicated guardrail service


def guardrail_node(state: PipelineState) -> PipelineState:
    """Run LlamaGuard safety check on the transcript. Stops pipeline if unsafe."""
    logger.info("─── NODE: guardrail_node ───")

    transcript = state.get("transcript", "")
    if not transcript:
        logger.warning("Empty transcript, marking as safe (nothing to check)")
        state["is_safe"] = True
        state["safety_response"] = "safe — empty transcript"
        return state

    try:
        result = check_safety(transcript)
        state["is_safe"] = result["is_safe"]
        state["safety_response"] = result["response"]

        if not result["is_safe"]:
            logger.warning(f"UNSAFE content detected: {result['response']}")
            state["error"] = f"Content flagged as unsafe: {result['response']}"
        else:
            logger.info("Content passed safety check")

    except Exception as e:
        logger.error(f"Safety check failed: {e}")
        # Fail-safe: mark as safe to avoid blocking, but log the error
        state["is_safe"] = True
        state["safety_response"] = f"Safety check error (defaulting safe): {str(e)}"

    return state
