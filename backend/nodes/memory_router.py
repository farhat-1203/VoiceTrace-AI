"""
Node: Memory Router — conditional branching for memory storage
"""
from loguru import logger
from models import PipelineState


def memory_router_node(state: PipelineState) -> str:
    """
    Conditional router that returns the next node name based on importance.

    Returns:
        "long_term_memory_node" if important
        "retrieval_node" if not important (skip long-term storage)
    """
    logger.info("─── NODE: memory_router_node ───")

    is_important = state.get("is_important", False)

    if is_important:
        logger.info("→ Routing to LONG-TERM MEMORY storage")
        return "long_term_memory_node"
    else:
        logger.info("→ Routing to RETRIEVAL (skipping long-term storage)")
        return "retrieval_node"
