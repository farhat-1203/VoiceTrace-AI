"""
Node: Store important memory in Qdrant (long-term)
"""
from loguru import logger
from models import PipelineState
from services.embedding import embedding_service
from services.qdrant_memory import qdrant_service


def long_term_memory_node(state: PipelineState) -> PipelineState:
    """Generate embedding and store important memory in Qdrant."""
    logger.info("─── NODE: long_term_memory_node ───")

    formatted_memory = state.get("formatted_memory")
    if not formatted_memory:
        logger.warning("No formatted memory to store")
        return state

    try:
        # Generate embedding for the formatted memory
        embedding = embedding_service.embed_passage(formatted_memory)
        state["embedding"] = embedding

        # Store in Qdrant
        point_id = qdrant_service.store_memory(
            embedding=embedding,
            formatted_memory=formatted_memory,
            session_id=state.get("session_id", "unknown"),
            extracted_data=state.get("extracted_data"),
        )
        logger.info(f"Stored long-term memory: {point_id}")

    except Exception as e:
        logger.error(f"Long-term memory storage failed: {e}")
        state["embedding"] = []

    return state
