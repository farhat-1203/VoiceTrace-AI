"""
Node: Final decision / response generation + output guardrail

Pipeline position: LAST node before END
  1. Generate response via Groq LLM
  2. Run output guardrail — filter/block if response is unsafe
  3. Return final state
"""
from loguru import logger
from models import PipelineState
from services.groq_llm import generate_response
from services.guardrail import classify as guardrail_classify


def decision_node(state: PipelineState) -> PipelineState:
    """Generate the final AI response and apply an output guardrail before returning."""
    logger.info("─── NODE: decision_node ───")

    transcript = state.get("sanitized_transcript", state.get("transcript", ""))
    extracted  = state.get("extracted_data", {})
    memories   = state.get("retrieved_memories", [])

    if not transcript:
        state["final_response"] = "No transcript was generated from the audio."
        return state

    # ── Stage 1: Generate response via Groq LLM ───────────────────────
    try:
        response = generate_response(
            transcript=transcript,
            extracted_data=extracted,
            past_memories=memories,
        )
        logger.info(f"LLM response generated ({len(response)} chars)")
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        state["final_response"] = f"Error generating response: {str(e)}"
        return state

    # ── Stage 2: Output guardrail ─────────────────────────────────────
    # Validate the AI-generated response before sending it to the user.
    # This catches hallucinated harmful content or prompt-injection echoes.
    try:
        guard = guardrail_classify(response, role="output")
        if not guard["is_safe"]:
            logger.warning(
                f"Output guardrail BLOCKED response | "
                f"reason={guard['reason']} action={guard['action']}"
            )
            # Replace unsafe response with a safe fallback message
            state["final_response"] = (
                "I was unable to generate a safe response for this input. "
                "Please try rephrasing or contact support."
            )
            # Mark the overall result as unsafe so the API can signal this
            state["is_safe"] = False
            state["safety_response"] = (
                f"Output blocked — {guard['reason']} (action: {guard['action']})"
            )
            return state
        else:
            logger.info("Output guardrail: PASSED ✓")
    except Exception as e:
        # Non-fatal: if guardrail fails, log and proceed (fail-open on output)
        logger.error(f"Output guardrail check failed (non-fatal): {e}")

    state["final_response"] = response
    return state
