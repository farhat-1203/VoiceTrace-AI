"""
VoiceTrace AI — SQLite Short-Term Memory Service
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from loguru import logger

from config import SQLITE_DB_PATH


class SQLiteMemoryService:
    """Manages short-term conversational memory via SQLite."""

    _instance: SQLiteMemoryService | None = None

    def __new__(cls) -> SQLiteMemoryService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        """Create the short-term memory table if it doesn't exist."""
        logger.info(f"Initializing SQLite database at {SQLITE_DB_PATH}")
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                transcript TEXT NOT NULL,
                extracted_data TEXT,
                final_response TEXT,
                is_important BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()
        logger.info("SQLite short-term memory table ready")

    def store(
        self,
        session_id: str,
        transcript: str,
        extracted_data: dict | None = None,
        final_response: str = "",
        is_important: bool = False,
    ) -> int:
        """Store a conversation record in short-term memory."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO short_term_memory
                (session_id, transcript, extracted_data, final_response, is_important, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                transcript,
                json.dumps(extracted_data or {}),
                final_response,
                is_important,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        logger.info(f"Stored short-term memory record #{row_id} for session {session_id}")
        return row_id

    def get_recent(self, limit: int = 10) -> list[dict]:
        """Retrieve the most recent short-term memories."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM short_term_memory
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_by_session(self, session_id: str) -> list[dict]:
        """Retrieve all entries for a given session."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM short_term_memory WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows


# Module-level singleton
sqlite_service = SQLiteMemoryService()
