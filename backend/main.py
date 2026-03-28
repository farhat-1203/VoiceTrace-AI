"""
VoiceTrace AI — FastAPI Backend
"""
from __future__ import annotations

import os
import time
import uuid
import shutil
from datetime import datetime
from contextlib import asynccontextmanager

import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydub import AudioSegment

from config import UPLOAD_DIR, MAX_AUDIO_DURATION_SECONDS
from models import ProcessResponse, HealthResponse
from graph import pipeline
from services.qdrant_memory import qdrant_service
from services.sqlite_memory import sqlite_service


# ═══════════════════════════════════════════════════════════════════════
#  Lifecycle
# ═══════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    logger.info("🚀 VoiceTrace AI Backend starting up")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    yield
    logger.info("VoiceTrace AI Backend shutting down")


# ═══════════════════════════════════════════════════════════════════════
#  App
# ═══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="VoiceTrace AI",
    description="Voice-based AI Business Assistant — Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def _validate_audio_duration(path: str) -> float:
    """Check audio duration and return it in seconds."""
    try:
        audio = AudioSegment.from_file(path)
        duration_sec = len(audio) / 1000.0
        if duration_sec > MAX_AUDIO_DURATION_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Audio is {duration_sec:.1f}s — exceeds the "
                    f"{MAX_AUDIO_DURATION_SECONDS}s limit."
                ),
            )
        return duration_sec
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Could not validate audio duration: {e}")
        return 0.0


# ═══════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    qdrant_ok = qdrant_service.health_check()
    return HealthResponse(
        status="healthy" if qdrant_ok else "degraded",
        services={
            "backend": "running",
            "qdrant": "connected" if qdrant_ok else "disconnected",
            "sqlite": "connected",
        },
    )


@app.post("/process", response_model=ProcessResponse)
async def process_audio(file: UploadFile = File(...)):
    """
    Main endpoint: upload an audio file and process it through the
    full LangGraph pipeline.
    """
    start = time.time()
    session_id = str(uuid.uuid4())

    # ── Validate file type ────────────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {ext}. Use wav, mp3, m4a, ogg, flac, or webm.",
        )

    # ── Save uploaded file ────────────────────────────────────────────
    file_path = os.path.join(UPLOAD_DIR, f"{session_id}{ext}")
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    logger.info(f"Saved upload: {file_path} ({len(content)} bytes)")

    # ── Validate duration ─────────────────────────────────────────────
    duration = _validate_audio_duration(file_path)
    logger.info(f"Audio duration: {duration:.1f}s")

    # ── Run the LangGraph pipeline ────────────────────────────────────
    try:
        initial_state = {
            "session_id": session_id,
            "audio_path": file_path,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Invoking pipeline for session {session_id}")
        result = pipeline.invoke(initial_state)

        processing_time = time.time() - start
        logger.info(f"Pipeline complete in {processing_time:.2f}s")

        # Check if unsafe
        safety_flag = "safe"
        if not result.get("is_safe", True):
            safety_flag = "unsafe"

        return ProcessResponse(
            session_id=session_id,
            transcript=result.get("transcript", ""),
            extracted_data=result.get("extracted_data", {}),
            is_important=result.get("is_important", False),
            formatted_memory=result.get("formatted_memory"),
            retrieved_memories=result.get("retrieved_memories", []),
            final_response=result.get("final_response", ""),
            safety_flag=safety_flag,
            error=result.get("error"),
            processing_time_seconds=round(processing_time, 2),
        )

    except Exception as e:
        processing_time = time.time() - start
        logger.error(f"Pipeline error: {e}")
        return ProcessResponse(
            session_id=session_id,
            error=str(e),
            processing_time_seconds=round(processing_time, 2),
        )

    finally:
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except OSError:
            pass


@app.get("/memories/recent")
async def get_recent_memories(limit: int = 10):
    """Retrieve recent short-term memories from SQLite."""
    return sqlite_service.get_recent(limit=limit)


@app.get("/memories/session/{session_id}")
async def get_session_memories(session_id: str):
    """Retrieve all memories for a specific session."""
    return sqlite_service.get_by_session(session_id)


# ═══════════════════════════════════════════════════════════════════════
#  Run (dev)
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
