"""
Node: Retrieve similar past memories from Qdrant (RAG)
"""
from loguru import logger
from models import PipelineState
from services.embedding import embedding_service
from services.qdrant_memory import qdrant_service


def retrieval_node(state: PipelineState) -> PipelineState:
    """Generate query embedding and retrieve top-k similar memories."""
    logger.info("─── NODE: retrieval_node ───")

    transcript = state.get("sanitized_transcript", state.get("transcript", ""))
    if not transcript:
        state["retrieved_memories"] = []
        return state

    try:
        # Use the transcript as the retrieval query
        query_embedding = embedding_service.embed(transcript)

        # Retrieve from Qdrant
        memories = qdrant_service.retrieve_similar(query_embedding)
        state["retrieved_memories"] = memories

        logger.info(f"Retrieved {len(memories)} past memories")
        for i, mem in enumerate(memories):
            logger.debug(
                f"  Memory {i+1} (score={mem['score']:.3f}): "
                f"{mem['formatted_memory'][:60]}..."
            )

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        state["retrieved_memories"] = []

    return state
