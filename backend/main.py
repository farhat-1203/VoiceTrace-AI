"""
VoiceTrace AI — FastAPI Backend
Central database: Supabase
Vector memory:   Qdrant Cloud
Auth:            Supabase Auth (JWT Bearer tokens)
Inference:       Groq API (Whisper + LLaMA3) — no local GPU required
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

import aiofiles
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from pydantic import BaseModel
from pydub import AudioSegment

from config import UPLOAD_DIR, MAX_AUDIO_DURATION_SECONDS
from models import ProcessResponse, HealthResponse
from graph import pipeline
from services.qdrant_memory import qdrant_service
from services.supabase_service import supabase_service
from services.transcription import transcription_service
from services.guardrail import classify as guardrail_classify
from services.groq_llm import extract_entities, generate_response

# Import routers
from routers import ledger, patterns, anomalies, suggestions, vapi, export as export_router


# ═══════════════════════════════════════════════════════════════════════
#  Auth
# ═══════════════════════════════════════════════════════════════════════

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Validate the Supabase access token from the Authorization header.
    Raises 401 if missing or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please log in via Supabase Auth.",
        )
    user = supabase_service.get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token. Please log in again.",
        )
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    """Like get_current_user but returns None instead of raising for unauthenticated requests."""
    if not credentials:
        return None
    return supabase_service.get_user_from_token(credentials.credentials)


# ═══════════════════════════════════════════════════════════════════════
#  Lifecycle
# ═══════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    description=(
        "Voice-based AI Business Assistant — API-driven backend "
        "(Groq Whisper + LLaMA3, no GPU required)"
    ),
    version="3.0.0",
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
#  Mount Routers
# ═══════════════════════════════════════════════════════════════════════

app.include_router(ledger.router)
app.include_router(patterns.router)
app.include_router(anomalies.router)
app.include_router(suggestions.router)
app.include_router(vapi.router)
app.include_router(export_router.router)


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
#  Routes — Health
# ═══════════════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    qdrant_ok = qdrant_service.health_check()
    supabase_ok = supabase_service.health_check()
    overall = "healthy" if (qdrant_ok and supabase_ok) else "degraded"
    return HealthResponse(
        status=overall,
        services={
            "backend": "running",
            "qdrant_cloud": "connected" if qdrant_ok else "disconnected",
            "supabase": "connected" if supabase_ok else "disconnected",
        },
    )


# ═══════════════════════════════════════════════════════════════════════
#  Routes — Process Audio  (requires auth)
# ═══════════════════════════════════════════════════════════════════════

@app.post("/process", response_model=ProcessResponse)
async def process_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Main endpoint: upload audio and run the full LangGraph pipeline.
    Requires a valid Supabase access token in the Authorization header.
    Results are saved to Supabase and linked to the authenticated user.
    """
    start = time.time()
    session_id = str(uuid.uuid4())
    user_id = current_user["id"]

    logger.info(f"Processing audio for user={user_id} session={session_id}")

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
    result = {}
    pipeline_error: Optional[str] = None
    transcription_id: Optional[str] = None
    
    try:
        initial_state = {
            "session_id": session_id,
            "user_id": user_id,
            "audio_path": file_path,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Invoking pipeline for session {session_id}")
        result = pipeline.invoke(initial_state)
        logger.info(f"Pipeline complete in {time.time() - start:.2f}s")

    except Exception as e:
        pipeline_error = str(e)
        logger.error(f"Pipeline error: {e}")

    processing_time = round(time.time() - start, 2)
    safety_flag = "safe" if result.get("is_safe", True) else "unsafe"

    # ── Persist to Supabase ───────────────────────────────────────────
    transcription_id = supabase_service.store_transcription(
        user_id=user_id,
        transcript=result.get("transcript", ""),
        audio_filename=file.filename or "",
        audio_duration_secs=duration,
        sanitized_transcript=result.get("sanitized_transcript", ""),
        is_safe=result.get("is_safe", True),
        safety_response=result.get("safety_response", ""),
        safety_flag=safety_flag,
        extracted_data=result.get("extracted_data", {}),
        is_important=result.get("is_important", False),
        formatted_memory=result.get("formatted_memory"),
        retrieved_memories=result.get("retrieved_memories", []),
        final_response=result.get("final_response", ""),
        detected_language=result.get("detected_language", "unknown"),
        error=pipeline_error,
        processing_time_secs=processing_time,
    )
    
    if transcription_id:
        logger.info(f"Transcription stored with ID: {transcription_id}")
        
        # ── Create ledger entry after transcription is saved ─────────
        try:
            from services.ledger_service import ledger_service
            from services.audio_storage_service import audio_storage_service
            
            # Upload audio to Supabase Storage (before deleting file)
            audio_url = None
            if os.path.exists(file_path):
                storage_path = audio_storage_service.upload_audio(
                    file_path=file_path,
                    user_id=user_id,
                    session_id=session_id,
                )
                if storage_path:
                    audio_url = audio_storage_service.get_presigned_url(
                        storage_path=storage_path,
                        expires_in=604800,  # 7 days
                    )
                    logger.info(f"Audio uploaded to Supabase Storage: {storage_path}")
            
            # Create ledger entry
            ledger_entry_id = ledger_service.create_entry_from_transcription(
                user_id=user_id,
                transcription_id=transcription_id,
                extracted_data=result.get("extracted_data", {}),
                audio_url=audio_url,
            )
            
            if ledger_entry_id:
                logger.info(f"Ledger entry created: {ledger_entry_id}")
                
                # Store audio segments
                segments = result.get("segments", [])
                if segments and audio_url:
                    audio_storage_service.store_audio_segments(
                        transcription_id=transcription_id,
                        segments=segments,
                        audio_url=audio_url,
                    )
                    logger.info(f"Stored {len(segments)} audio segments")
                    
        except Exception as e:
            logger.error(f"Ledger creation failed (non-fatal): {e}")
    
    # ── Clean up uploaded file ────────────────────────────────────────
    try:
        os.remove(file_path)
        logger.info(f"Cleaned up temp file: {file_path}")
    except OSError as e:
        logger.warning(f"Could not delete temp file: {e}")

    return ProcessResponse(
        session_id=session_id,
        transcript=result.get("transcript", ""),
        extracted_data=result.get("extracted_data", {}),
        is_important=result.get("is_important", False),
        formatted_memory=result.get("formatted_memory"),
        retrieved_memories=result.get("retrieved_memories", []),
        final_response=result.get("final_response", ""),
        safety_flag=safety_flag,
        error=pipeline_error,
        processing_time_seconds=processing_time,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Routes — Transcription History  (requires auth)
# ═══════════════════════════════════════════════════════════════════════

@app.get("/transcriptions")
async def get_my_transcriptions(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """Return the most recent transcriptions for the authenticated user."""
    return supabase_service.get_transcriptions_by_user(
        user_id=current_user["id"],
        limit=limit,
    )


@app.get("/transcriptions/{transcription_id}")
async def get_transcription(
    transcription_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return a single transcription by ID (must belong to the current user)."""
    row = supabase_service.get_transcription_by_id(
        transcription_id=transcription_id,
        user_id=current_user["id"],
    )
    if not row:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return row


@app.get("/memories")
async def get_my_memories(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """Return important memories for the authenticated user (used as RAG context)."""
    return supabase_service.get_important_memories_by_user(
        user_id=current_user["id"],
        limit=limit,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Routes — Auth Info
# ═══════════════════════════════════════════════════════════════════════

@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user.get("user_metadata", {}).get("full_name", ""),
        "avatar_url": current_user.get("user_metadata", {}).get("avatar_url", ""),
    }


# ═══════════════════════════════════════════════════════════════════════
#  Run (dev)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
#  Route — /transcribe  (standalone, no full pipeline)
# ═══════════════════════════════════════════════════════════════════════

class TranscribeResponse(BaseModel):
    session_id: str
    text: str
    language: str
    segments: list[dict]
    duration_seconds: float
    processing_time_seconds: float


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Standalone transcription endpoint.
    Upload audio → get back text + word-level segments.
    Does NOT run the full pipeline (no LLM, no memory).
    Requires a valid Supabase auth token.
    """
    start = time.time()
    session_id = str(uuid.uuid4())

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {ext}. Use wav, mp3, m4a, ogg, flac, or webm.",
        )

    file_path = os.path.join(UPLOAD_DIR, f"{session_id}{ext}")
    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        duration = _validate_audio_duration(file_path)
        result   = transcription_service.transcribe(file_path)
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass

    return TranscribeResponse(
        session_id=session_id,
        text=result["text"],
        language=result["language"],
        segments=result["segments"],
        duration_seconds=round(duration, 2),
        processing_time_seconds=round(time.time() - start, 2),
    )


# ═══════════════════════════════════════════════════════════════════════
#  Route — /analyze  (text-only structured insights)
# ═══════════════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    text: str
    include_response: bool = True       # also generate a natural-language summary


class AnalyzeResponse(BaseModel):
    session_id: str
    safety_status: str                  # "SAFE" | "UNSAFE"
    safety_reason: str
    extracted_data: dict
    response: Optional[str] = None
    processing_time_seconds: float


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(
    body: AnalyzeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze a plain-text transcript without audio upload.

    Flow:
      1. Input guardrail  — classify text as SAFE / UNSAFE
      2. Entity extraction — structured business data
      3. (opt) Response generation — natural-language summary + insights
      4. Output guardrail  — validate AI response before returning

    Useful for: re-analyzing existing transcripts, testing, or
    integrating with external STT providers.
    """
    start      = time.time()
    session_id = str(uuid.uuid4())
    text       = body.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="text field must not be empty")

    # ── Step 1: Input guardrail ───────────────────────────────────────
    guard_in = guardrail_classify(text, role="input")
    if not guard_in["is_safe"]:
        logger.warning(f"Analyze input blocked: {guard_in['reason']}")
        return AnalyzeResponse(
            session_id=session_id,
            safety_status="UNSAFE",
            safety_reason=guard_in["reason"],
            extracted_data={},
            response=None,
            processing_time_seconds=round(time.time() - start, 2),
        )

    # ── Step 2: Entity extraction ─────────────────────────────────────
    try:
        extracted = extract_entities(text)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        extracted = {"error": str(e)}

    # ── Step 3: Optional response generation ─────────────────────────
    final_response: Optional[str] = None
    if body.include_response:
        try:
            raw_response = generate_response(
                transcript=text,
                extracted_data=extracted,
                past_memories=[],
            )
            # Step 4: Output guardrail
            guard_out = guardrail_classify(raw_response, role="output")
            if guard_out["is_safe"]:
                final_response = raw_response
            else:
                logger.warning(f"Analyze output blocked: {guard_out['reason']}")
                final_response = (
                    "Response could not be generated safely. Please try again."
                )
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            final_response = f"Error: {str(e)}"

    return AnalyzeResponse(
        session_id=session_id,
        safety_status="SAFE",
        safety_reason=guard_in["reason"],
        extracted_data=extracted,
        response=final_response,
        processing_time_seconds=round(time.time() - start, 2),
    )


# ═══════════════════════════════════════════════════════════════════════
#  Run (dev)
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
