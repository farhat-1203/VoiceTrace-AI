"""
Node: Extract structured business entities via Groq
"""
from loguru import logger
from models import PipelineState
from services.groq_llm import extract_entities


def extract_node(state: PipelineState) -> PipelineState:
    """Extract structured business data from the sanitized transcript."""
    logger.info("─── NODE: extract_node ───")

    transcript = state.get("sanitized_transcript", state.get("transcript", ""))
    if not transcript:
        logger.warning("No transcript to extract from")
        state["extracted_data"] = {}
        return state

    try:
        data = extract_entities(transcript)
        state["extracted_data"] = data
        logger.info(f"Extracted {len(data)} fields")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        state["extracted_data"] = {"error": str(e)}

    return state
