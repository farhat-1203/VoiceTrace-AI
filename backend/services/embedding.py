"""
VoiceTrace AI — Embedding Service (API mode)
Uses FastEmbed with multilingual-e5-small for Hindi/English/Hinglish support.

Model: intfloat/multilingual-e5-small
  • 384-dim output (same as bge-small)
  • Supports 100+ languages including Hindi
  • ONNX runtime, ~40 MB model, runs on CPU
  • Requires "query:" and "passage:" prefixes for optimal accuracy

Mode guard:
  "api"   → FastEmbed (CPU, no GPU needed)
  "local" → could swap to full SentenceTransformer if needed
"""
from __future__ import annotations

import numpy as np
from loguru import logger

from config import EMBEDDING_MODEL, EMBEDDING_DIM, MODEL_MODE


class EmbeddingService:
    """
    Singleton embedding service.
    Lazy-loads the FastEmbed model on first use so startup is instant.
    """

    _instance: EmbeddingService | None = None
    _model = None   # fastembed.TextEmbedding instance

    def __new__(cls) -> EmbeddingService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load(self) -> None:
        if self._model is not None:
            return

        logger.info(f"Loading FastEmbed model: {EMBEDDING_MODEL}")

        # fastembed is a transitive dep of qdrant-client[fastembed]
        # We import lazily so the service file can be imported even if the
        # optional extra isn't installed — only fails on first embed call.
        try:
            from fastembed import TextEmbedding  # type: ignore[import]
        except ImportError:
            raise ImportError(
                "fastembed is not installed. "
                "Run: pip install 'qdrant-client[fastembed]'"
            )

        self._model = TextEmbedding(model_name=EMBEDDING_MODEL)
        logger.info("FastEmbed model loaded ✓ (multilingual-e5-small with Hindi support)")

    def embed(self, text: str) -> list[float]:
        """
        Generate a query embedding vector.
        
        CRITICAL: multilingual-e5 models REQUIRE "query:" prefix for search queries.
        Without it, accuracy drops ~15%.
        
        Use this for:
        - Searching similar memories
        - VAPI queries
        - Vendor questions
        """
        self._load()
        
        # Add required prefix for multilingual-e5 models
        prefixed_text = f"query: {text}"
        
        vectors = list(self._model.embed([prefixed_text]))
        vector: np.ndarray = vectors[0]
        return vector.tolist()

    def embed_passage(self, text: str) -> list[float]:
        """
        Generate a passage (storage) embedding vector.
        
        CRITICAL: multilingual-e5 models REQUIRE "passage:" prefix for documents.
        Without it, accuracy drops ~15%.
        
        Use this for:
        - Storing ledger entries
        - Storing memories
        - Storing transcriptions
        """
        self._load()
        
        # Add required prefix for multilingual-e5 models
        prefixed_text = f"passage: {text}"
        
        vectors = list(self._model.embed([prefixed_text]))
        vector: np.ndarray = vectors[0]
        return vector.tolist()

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIM


# Module-level singleton
embedding_service = EmbeddingService()
