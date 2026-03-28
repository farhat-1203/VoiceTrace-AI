"""
VoiceTrace AI — Embedding Service (API mode)
Uses qdrant-client's built-in FastEmbed (BAAI/bge-small-en-v1.5).

Why FastEmbed instead of sentence-transformers?
  • Ships with qdrant-client — zero extra install
  • ONNX runtime, ~40 MB model, runs on CPU with no torch required
  • 384-dim output — small Qdrant collection, fast retrieval
  • Quantized INT8 — ~3ms per embed on CPU

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
        logger.info("FastEmbed model loaded ✓")

    def embed(self, text: str) -> list[float]:
        """
        Generate a query embedding vector.
        FastEmbed handles the E5 prefix internally for supported models.
        """
        self._load()
        vectors = list(self._model.embed([text]))
        vector: np.ndarray = vectors[0]
        return vector.tolist()

    def embed_passage(self, text: str) -> list[float]:
        """
        Generate a passage (storage) embedding vector.
        For bge-small, query and passage embeddings use the same model.
        """
        return self.embed(text)

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIM


# Module-level singleton
embedding_service = EmbeddingService()
