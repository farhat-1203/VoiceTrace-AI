"""
Node: Analyse memory importance via Groq
"""
from loguru import logger
from models import PipelineState
from services.groq_llm import analyze_memory_importance


def memory_analysis_node(state: PipelineState) -> PipelineState:
    """Determine if the current transcript contains important long-term insights."""
    logger.info("─── NODE: memory_analysis_node ───")

    transcript = state.get("sanitized_transcript", state.get("transcript", ""))
    extracted = state.get("extracted_data", {})

    if not transcript:
        state["is_important"] = False
        state["formatted_memory"] = None
        return state

    try:
        result = analyze_memory_importance(transcript, extracted)
        state["is_important"] = result.get("is_important", False)
        state["formatted_memory"] = result.get("formatted_memory")
        logger.info(
            f"Memory importance: {state['is_important']} | "
            f"Memory: {state['formatted_memory'][:80] if state['formatted_memory'] else 'N/A'}"
        )
    except Exception as e:
        logger.error(f"Memory analysis failed: {e}")
        state["is_important"] = False
        state["formatted_memory"] = None

    return state
