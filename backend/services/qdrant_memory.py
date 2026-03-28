"""
VoiceTrace AI — Qdrant Vector Memory Service
"""
from __future__ import annotations

import uuid
from datetime import datetime

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
)

from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION, EMBEDDING_DIM, RAG_TOP_K


class QdrantMemoryService:
    """Manages long-term memory storage and retrieval via Qdrant."""

    _instance: QdrantMemoryService | None = None
    _client: QdrantClient | None = None
    _initialized: bool = False

    def __new__(cls) -> QdrantMemoryService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_client(self):
        """Lazy-initialise the Qdrant client and collection."""
        if self._initialized:
            return

        logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
        self._client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        # Create collection if it doesn't exist
        collections = [c.name for c in self._client.get_collections().collections]
        if QDRANT_COLLECTION not in collections:
            logger.info(f"Creating Qdrant collection: {QDRANT_COLLECTION}")
            self._client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )
        else:
            logger.info(f"Qdrant collection '{QDRANT_COLLECTION}' already exists")

        self._initialized = True

    def store_memory(
        self,
        embedding: list[float],
        formatted_memory: str,
        session_id: str,
        extracted_data: dict | None = None,
    ) -> str:
        """Store an important memory in Qdrant."""
        self._ensure_client()

        point_id = str(uuid.uuid4())
        payload = {
            "formatted_memory": formatted_memory,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "extracted_data": extracted_data or {},
        }

        self._client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        logger.info(f"Stored memory {point_id} in Qdrant")
        return point_id

    def retrieve_similar(
        self,
        query_embedding: list[float],
        top_k: int = RAG_TOP_K,
    ) -> list[dict]:
        """Retrieve top-k similar memories from Qdrant."""
        self._ensure_client()

        results = self._client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=top_k,
        )

        memories = []
        for hit in results:
            memories.append(
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "formatted_memory": hit.payload.get("formatted_memory", ""),
                    "session_id": hit.payload.get("session_id", ""),
                    "timestamp": hit.payload.get("timestamp", ""),
                }
            )

        logger.info(f"Retrieved {len(memories)} similar memories from Qdrant")
        return memories

    def health_check(self) -> bool:
        """Check if Qdrant is reachable."""
        try:
            self._ensure_client()
            self._client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Module-level singleton
qdrant_service = QdrantMemoryService()
