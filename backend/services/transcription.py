"""
VoiceTrace AI — Transcription Service
MODE = "api"  → Groq Whisper API (whisper-large-v3), no GPU, ~1–3 s latency
MODE = "local" → stub for future WhisperX local fallback

Pipeline: upload audio file → POST to Groq → return {text, segments, language}
"""
from __future__ import annotations

import os
import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import GROQ_API_KEY, GROQ_WHISPER_MODEL, MODEL_MODE

# Groq audio transcription endpoint
_GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=60.0, pool=5.0)

# Supported audio MIME types accepted by Groq Whisper
_MIME_MAP: dict[str, str] = {
    ".mp3":  "audio/mpeg",
    ".mp4":  "audio/mp4",
    ".mpeg": "audio/mpeg",
    ".mpga": "audio/mpeg",
    ".m4a":  "audio/mp4",
    ".wav":  "audio/wav",
    ".webm": "audio/webm",
    ".ogg":  "audio/ogg",
    ".flac": "audio/flac",
}

_groq_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    before_sleep=lambda rs: logger.warning(
        f"Groq Whisper retry {rs.attempt_number}: {rs.outcome.exception()}"
    ),
)


class TranscriptionService:
    """
    Unified transcription interface.
    In api mode: delegates to Groq Whisper.
    In local mode: raises NotImplementedError (plug in WhisperX here).
    """

    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe audio at `audio_path`.

        Returns:
            {
                "text":     str,           # full transcript
                "segments": list[dict],    # [{start, end, text}, ...]
                "language": str
            }
        """
        if MODEL_MODE == "api":
            return self._transcribe_groq(audio_path)
        else:
            raise NotImplementedError(
                "Local transcription mode is not enabled. "
                "Set MODEL_MODE=api or install WhisperX."
            )

    @_groq_retry
    def _transcribe_groq(self, audio_path: str) -> dict:
        """Send audio to Groq Whisper API and parse the response."""
        ext = os.path.splitext(audio_path)[1].lower()
        mime = _MIME_MAP.get(ext, "audio/mpeg")

        logger.info(
            f"Transcribing via Groq Whisper | model={GROQ_WHISPER_MODEL} "
            f"file={os.path.basename(audio_path)} mime={mime}"
        )

        with open(audio_path, "rb") as audio_file:
            with httpx.Client(timeout=_TIMEOUT) as client:
                response = client.post(
                    _GROQ_AUDIO_URL,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    data={
                        "model":            GROQ_WHISPER_MODEL,
                        "response_format":  "verbose_json",  # includes segments + language
                        # Remove language param to enable auto-detection
                        "temperature":      "0",
                    },
                    files={"file": (os.path.basename(audio_path), audio_file, mime)},
                )

        if response.status_code != 200:
            raise RuntimeError(
                f"Groq Whisper API error {response.status_code}: {response.text[:300]}"
            )

        payload = response.json()

        full_text: str = payload.get("text", "").strip()
        language: str  = payload.get("language", "unknown")

        # verbose_json returns segments; fall back to single-segment if missing
        raw_segments: list[dict] = payload.get("segments", [])
        segments = [
            {
                "start": seg.get("start", 0.0),
                "end":   seg.get("end",   0.0),
                "text":  seg.get("text",  "").strip(),
            }
            for seg in raw_segments
        ] or [{"start": 0.0, "end": 0.0, "text": full_text}]

        # Detect if it's Hinglish (code-mixed Hindi-English)
        detected_language = self._detect_language_type(full_text, language)

        logger.info(
            f"Groq Whisper done — {len(segments)} segments, "
            f"detected_lang={detected_language}, chars={len(full_text)}"
        )

        return {
            "text":     full_text,
            "segments": segments,
            "language": detected_language,
        }

    def _detect_language_type(self, text: str, whisper_lang: str) -> str:
        """
        Detect if text is Hindi, English, or Hinglish (code-mixed).
        
        Args:
            text: Transcribed text
            whisper_lang: Language detected by Whisper (e.g., 'hi', 'en')
        
        Returns:
            'hindi', 'english', 'hinglish', or 'other'
        """
        if not text:
            return "unknown"
        
        # Count Hindi (Devanagari) and English (Latin) characters
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        total_alpha = hindi_chars + english_chars
        
        if total_alpha == 0:
            return whisper_lang if whisper_lang in ('hi', 'en') else "unknown"
        
        hindi_ratio = hindi_chars / total_alpha
        english_ratio = english_chars / total_alpha
        
        # Hinglish: significant mix of both scripts
        if hindi_ratio > 0.2 and english_ratio > 0.2:
            return "hinglish"
        elif hindi_ratio > 0.5:
            return "hindi"
        elif english_ratio > 0.5:
            return "english"
        elif whisper_lang == "hi":
            return "hindi"
        elif whisper_lang == "en":
            return "english"
        else:
            return "hinglish"  # Default for Indian context


# Module-level singleton
transcription_service = TranscriptionService()
