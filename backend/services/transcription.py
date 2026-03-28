"""
VoiceTrace AI — WhisperX Transcription Service
"""
from __future__ import annotations

import gc
import torch
import whisperx
from loguru import logger

from config import (
    WHISPERX_MODEL,
    WHISPERX_DEVICE,
    WHISPERX_COMPUTE_TYPE,
)


class TranscriptionService:
    """Singleton wrapper around WhisperX for GPU-efficient transcription."""

    _instance: TranscriptionService | None = None
    _model = None

    def __new__(cls) -> TranscriptionService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        """Lazy-load the WhisperX model."""
        if self._model is not None:
            return

        device = WHISPERX_DEVICE
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA not available, falling back to CPU")
            device = "cpu"
            compute_type = "int8"
        else:
            compute_type = WHISPERX_COMPUTE_TYPE

        logger.info(
            f"Loading WhisperX model={WHISPERX_MODEL} "
            f"device={device} compute_type={compute_type}"
        )
        self._model = whisperx.load_model(
            WHISPERX_MODEL,
            device=device,
            compute_type=compute_type,
        )
        self._device = device
        logger.info("WhisperX model loaded successfully")

    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe an audio file and return aligned segments.

        Returns:
            dict with keys: "text", "segments", "language"
        """
        self._load_model()

        logger.info(f"Transcribing: {audio_path}")

        # Load audio
        audio = whisperx.load_audio(audio_path)

        # Transcribe
        result = self._model.transcribe(audio, batch_size=16)
        language = result.get("language", "en")

        # Align whisper output
        try:
            model_a, metadata = whisperx.load_align_model(
                language_code=language, device=self._device
            )
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self._device,
                return_char_alignments=False,
            )
            # Free alignment model
            del model_a
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as e:
            logger.warning(f"Alignment failed (non-fatal): {e}")

        full_text = " ".join(
            seg.get("text", "") for seg in result.get("segments", [])
        ).strip()

        segments = [
            {
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", ""),
            }
            for seg in result.get("segments", [])
        ]

        logger.info(f"Transcription complete — {len(segments)} segments, lang={language}")

        return {
            "text": full_text,
            "segments": segments,
            "language": language,
        }


# Module-level singleton
transcription_service = TranscriptionService()
