"""
VoiceTrace AI — LangGraph Pipeline Orchestrator

Builds the full processing graph:
  transcribe → guardrail → sanitize → extract → memory_analysis
    → [conditional: important?]
        → yes: long_term_memory → retrieval → decision
        → no:  retrieval → decision
"""
from __future__ import annotations

from loguru import logger
from langgraph.graph import StateGraph, END

from models import PipelineState
from nodes import (
    transcribe_node,
    guardrail_node,
    sanitize_node,
    extract_node,
    memory_analysis_node,
    memory_router_node,
    long_term_memory_node,
    retrieval_node,
    decision_node,
)


def _safety_gate(state: PipelineState) -> str:
    """After guardrail: continue if safe, end if unsafe."""
    if state.get("is_safe", True):
        return "sanitize_node"
    else:
        logger.warning("Pipeline halted — content is UNSAFE")
        return END


def _memory_route(state: PipelineState) -> str:
    """After memory analysis: route based on importance."""
    return memory_router_node(state)


def build_pipeline() -> StateGraph:
    """
    Construct and compile the LangGraph pipeline.

    Returns a compiled graph ready for .invoke() or .ainvoke().
    """
    logger.info("Building LangGraph pipeline...")

    graph = StateGraph(PipelineState)

    # ── Register nodes ────────────────────────────────────────────────
    graph.add_node("transcribe_node", transcribe_node)
    graph.add_node("guardrail_node", guardrail_node)
    graph.add_node("sanitize_node", sanitize_node)
    graph.add_node("extract_node", extract_node)
    graph.add_node("memory_analysis_node", memory_analysis_node)
    graph.add_node("long_term_memory_node", long_term_memory_node)
    graph.add_node("retrieval_node", retrieval_node)
    graph.add_node("decision_node", decision_node)

    # ── Define edges ──────────────────────────────────────────────────

    # Entry point
    graph.set_entry_point("transcribe_node")

    # transcribe → guardrail
    graph.add_edge("transcribe_node", "guardrail_node")

    # guardrail → conditional (safe/unsafe)
    graph.add_conditional_edges(
        "guardrail_node",
        _safety_gate,
        {
            "sanitize_node": "sanitize_node",
            END: END,
        },
    )

    # sanitize → extract
    graph.add_edge("sanitize_node", "extract_node")

    # extract → memory_analysis
    graph.add_edge("extract_node", "memory_analysis_node")

    # memory_analysis → conditional (important/not)
    graph.add_conditional_edges(
        "memory_analysis_node",
        _memory_route,
        {
            "long_term_memory_node": "long_term_memory_node",
            "retrieval_node": "retrieval_node",
        },
    )

    # long_term_memory → retrieval
    graph.add_edge("long_term_memory_node", "retrieval_node")

    # retrieval → decision
    graph.add_edge("retrieval_node", "decision_node")

    # decision → END
    graph.add_edge("decision_node", END)

    compiled = graph.compile()
    logger.info("LangGraph pipeline compiled successfully")
    return compiled


# Pre-build the pipeline at module load
pipeline = build_pipeline()
