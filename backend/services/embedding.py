"""
VoiceTrace AI — Embedding Service (SentenceTransformers)
"""
from __future__ import annotations

import torch
from loguru import logger
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, EMBEDDING_DIM


class EmbeddingService:
    """Singleton embedding service using multilingual-e5-large."""

    _instance: EmbeddingService | None = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> EmbeddingService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is not None:
            return

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading embedding model {EMBEDDING_MODEL} on {device}")
        self._model = SentenceTransformer(EMBEDDING_MODEL, device=device)
        logger.info("Embedding model loaded successfully")

    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.
        Prepends 'query: ' prefix as required by E5 models.
        """
        self._load_model()
        # E5 models expect 'query: ' or 'passage: ' prefix
        prefixed = f"query: {text}"
        vector = self._model.encode(prefixed, normalize_embeddings=True)
        return vector.tolist()

    def embed_passage(self, text: str) -> list[float]:
        """
        Generate an embedding for storage (passage).
        Prepends 'passage: ' prefix as required by E5 models.
        """
        self._load_model()
        prefixed = f"passage: {text}"
        vector = self._model.encode(prefixed, normalize_embeddings=True)
        return vector.tolist()

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIM


# Module-level singleton
embedding_service = EmbeddingService()
