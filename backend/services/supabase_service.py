"""
VoiceTrace AI — Supabase Service
Handles all database operations via the Supabase Python client.
Uses the service-role key so it bypasses RLS for backend writes.
"""
from __future__ import annotations

import json
from typing import Optional
from datetime import datetime

from loguru import logger
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY


class SupabaseService:
    """Central Supabase DB client. Singleton pattern."""

    _instance: SupabaseService | None = None
    _client: Client | None = None

    def __new__(cls) -> SupabaseService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        """Initialise the Supabase client using the service-role key."""
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            logger.error(
                "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not set! "
                "DB writes will fail."
            )
            return
        self._client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info(f"Supabase client initialised → {SUPABASE_URL}")

    # ─────────────────────────────────────────────────────────────────
    #  Auth helpers
    # ─────────────────────────────────────────────────────────────────

    def get_user_from_token(self, access_token: str) -> Optional[dict]:
        """
        Verify a Supabase access token (JWT) and return the user payload.
        Returns None if the token is invalid / expired.
        """
        try:
            response = self._client.auth.get_user(access_token)
            if response and response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {},
                }
            return None
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────
    #  Transcriptions CRUD
    # ─────────────────────────────────────────────────────────────────

    def store_transcription(
        self,
        user_id: str,
        transcript: str,
        *,
        audio_filename: str = "",
        audio_duration_secs: float = 0.0,
        audio_url: str | None = None,
        audio_storage_path: str | None = None,
        sanitized_transcript: str = "",
        is_safe: bool = True,
        safety_response: str = "",
        safety_flag: str = "safe",
        extracted_data: dict | None = None,
        is_important: bool = False,
        formatted_memory: str | None = None,
        retrieved_memories: list | None = None,
        final_response: str = "",
        detected_language: str = "unknown",
        error: str | None = None,
        processing_time_secs: float = 0.0,
    ) -> Optional[str]:
        """
        Insert a completed pipeline result into the `transcriptions` table.
        Returns the new row UUID, or None on failure.
        """
        if not self._client:
            logger.error("Supabase client not initialised; cannot store transcription.")
            return None

        row = {
            "user_id": user_id,
            "audio_filename": audio_filename,
            "audio_duration_secs": audio_duration_secs,
            "audio_url": audio_url,
            "audio_storage_path": audio_storage_path,
            "transcript": transcript,
            "sanitized_transcript": sanitized_transcript,
            "is_safe": is_safe,
            "safety_response": safety_response,
            "safety_flag": safety_flag,
            "extracted_data": extracted_data or {},
            "is_important": is_important,
            "formatted_memory": formatted_memory,
            "retrieved_memories": retrieved_memories or [],
            "final_response": final_response,
            "detected_language": detected_language,
            "error": error,
            "processing_time_secs": processing_time_secs,
        }

        try:
            result = self._client.table("transcriptions").insert(row).execute()
            inserted = result.data[0] if result.data else {}
            row_id = inserted.get("id")
            logger.info(f"Stored transcription {row_id} for user {user_id} (lang={detected_language})")
            return row_id
        except Exception as e:
            logger.error(f"Failed to store transcription: {e}")
            return None

    def get_transcriptions_by_user(
        self, user_id: str, limit: int = 20
    ) -> list[dict]:
        """Fetch the most recent transcriptions for a user."""
        if not self._client:
            return []
        try:
            result = (
                self._client.table("transcriptions")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to fetch transcriptions: {e}")
            return []

    def get_transcription_by_id(
        self, transcription_id: str, user_id: str
    ) -> Optional[dict]:
        """Fetch a single transcription by its UUID (scoped to user)."""
        if not self._client:
            return None
        try:
            result = (
                self._client.table("transcriptions")
                .select("*")
                .eq("id", transcription_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to fetch transcription {transcription_id}: {e}")
            return None

    def get_important_memories_by_user(
        self, user_id: str, limit: int = 10
    ) -> list[dict]:
        """Fetch important memories (for RAG context) for a user."""
        if not self._client:
            return []
        try:
            result = (
                self._client.table("transcriptions")
                .select("formatted_memory, extracted_data, created_at")
                .eq("user_id", user_id)
                .eq("is_important", True)
                .not_.is_("formatted_memory", "null")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to fetch important memories: {e}")
            return []

    def health_check(self) -> bool:
        """Returns True if Supabase is reachable."""
        try:
            self._client.table("transcriptions").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False


# Module-level singleton
supabase_service = SupabaseService()
