"""
VoiceTrace AI — Centralized Configuration

MODEL_MODE controls the inference backend:
  "api"   → Groq Whisper + Groq LLM (default, no GPU required)
  "local" → WhisperX + local models (future, requires GPU)
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Mode switch ───────────────────────────────────────────────────────
# "api" uses Groq for everything. "local" is a future GPU fallback.
MODEL_MODE: str = os.getenv("MODEL_MODE", "api")

# ── Groq ─────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# Transcription — Groq Whisper (api mode)
GROQ_WHISPER_MODEL: str = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")

# LLM models
GROQ_GUARD_MODEL: str  = os.getenv("GROQ_GUARD_MODEL",    "llama-3.1-8b-instant")
GROQ_FAST_MODEL: str   = os.getenv("GROQ_FAST_MODEL",     "llama-3.1-8b-instant")
GROQ_MEMORY_MODEL: str = os.getenv("GROQ_MEMORY_MODEL",   "llama-3.1-8b-instant")
GROQ_RESPONSE_MODEL: str = os.getenv("GROQ_RESPONSE_MODEL", "llama-3.3-70b-versatile")

# ── Qdrant ───────────────────────────────────────────────────────────
QDRANT_URL: str        = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY: str    = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION: str = "long_term_memory"

# Embedding model for multilingual support (Hindi/English/Hinglish)
# intfloat/multilingual-e5-small: 384 dims, supports 100+ languages
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
EMBEDDING_DIM: int   = 384   # multilingual-e5-small output size

# ── Supabase ─────────────────────────────────────────────────────────
SUPABASE_URL: str              = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ── Paths & Limits ───────────────────────────────────────────────────
UPLOAD_DIR: str               = os.path.join(os.path.dirname(__file__), "uploads")
MAX_AUDIO_DURATION_SECONDS: int = 180   # 3 minutes

# ── RAG ──────────────────────────────────────────────────────────────
RAG_TOP_K: int = 3
