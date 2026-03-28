"""
VoiceTrace AI — Pydantic Models & LangGraph State
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ═══════════════════════════════════════════════════════════════════════
#  LangGraph Pipeline State
# ═══════════════════════════════════════════════════════════════════════

class PipelineState(TypedDict, total=False):
    """Shared state flowing through the LangGraph pipeline."""
    # Meta
    session_id: str
    audio_path: str
    timestamp: str

    # Transcription
    transcript: str
    segments: list[dict]

    # Safety
    is_safe: bool
    safety_response: str

    # Sanitised transcript
    sanitized_transcript: str

    # Extraction
    extracted_data: dict

    # Memory analysis
    is_important: bool
    formatted_memory: Optional[str]

    # Embedding
    embedding: list[float]

    # Retrieval
    retrieved_memories: list[dict]

    # Final response
    final_response: str

    # Error
    error: Optional[str]


# ═══════════════════════════════════════════════════════════════════════
#  API Request / Response Schemas
# ═══════════════════════════════════════════════════════════════════════

class ProcessResponse(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transcript: str = ""
    extracted_data: dict = Field(default_factory=dict)
    is_important: bool = False
    formatted_memory: Optional[str] = None
    retrieved_memories: list[dict] = Field(default_factory=list)
    final_response: str = ""
    safety_flag: str = "safe"
    error: Optional[str] = None
    processing_time_seconds: float = 0.0


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]
