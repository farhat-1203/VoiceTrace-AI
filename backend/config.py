"""
VoiceTrace AI — Centralized Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


# ── Groq ─────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# Models
GROQ_GUARD_MODEL = "llama-guard-3-8b"
GROQ_FAST_MODEL = "llama-3.1-8b-instant"
GROQ_MEMORY_MODEL = "llama-3.1-8b-instant"
GROQ_RESPONSE_MODEL = "llama-3.1-8b-instant"

# ── Qdrant ───────────────────────────────────────────────────────────
QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION: str = "long_term_memory"

# ── WhisperX ─────────────────────────────────────────────────────────
WHISPERX_MODEL: str = os.getenv("WHISPERX_MODEL", "medium")
WHISPERX_DEVICE: str = os.getenv("WHISPERX_DEVICE", "cuda")
WHISPERX_COMPUTE_TYPE: str = os.getenv("WHISPERX_COMPUTE_TYPE", "float16")

# ── Embedding ────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
EMBEDDING_DIM: int = 1024

# ── Paths ────────────────────────────────────────────────────────────
UPLOAD_DIR: str = os.path.join(os.path.dirname(__file__), "uploads")
SQLITE_DB_PATH: str = os.path.join(os.path.dirname(__file__), "memory.db")

# ── Audio Limits ─────────────────────────────────────────────────────
MAX_AUDIO_DURATION_SECONDS: int = 180  # 3 minutes

# ── RAG ──────────────────────────────────────────────────────────────
RAG_TOP_K: int = 3
