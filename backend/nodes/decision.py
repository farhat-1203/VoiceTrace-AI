"""
Node: Final decision / response generation
"""
from loguru import logger
from models import PipelineState
from services.groq_llm import generate_response
from services.sqlite_memory import sqlite_service


def decision_node(state: PipelineState) -> PipelineState:
    """Generate the final AI response and store short-term memory."""
    logger.info("─── NODE: decision_node ───")

    transcript = state.get("sanitized_transcript", state.get("transcript", ""))
    extracted = state.get("extracted_data", {})
    memories = state.get("retrieved_memories", [])

    if not transcript:
        state["final_response"] = "No transcript was generated from the audio."
        return state

    try:
        # Generate response using Groq
        response = generate_response(
            transcript=transcript,
            extracted_data=extracted,
            past_memories=memories,
        )
        state["final_response"] = response
        logger.info(f"Generated final response ({len(response)} chars)")

    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        state["final_response"] = f"Error generating response: {str(e)}"

    # Always store in short-term memory (SQLite)
    try:
        sqlite_service.store(
            session_id=state.get("session_id", "unknown"),
            transcript=transcript,
            extracted_data=extracted,
            final_response=state.get("final_response", ""),
            is_important=state.get("is_important", False),
        )
        logger.info("Stored conversation in short-term memory")
    except Exception as e:
        logger.error(f"Short-term memory storage failed: {e}")

    return state
