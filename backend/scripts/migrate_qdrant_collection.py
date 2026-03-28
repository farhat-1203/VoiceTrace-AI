"""
Qdrant Collection Migration Script
Recreates the collection for multilingual-e5-small embeddings

IMPORTANT: This will DELETE all existing embeddings in Qdrant!
Only run this if you're switching from bge-small to multilingual-e5-small.

The vector spaces are incompatible even though dimensions are the same (384).
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_DIM


def migrate_collection():
    """
    Delete old collection and recreate with multilingual-e5-small config.
    """
    logger.info("=" * 60)
    logger.info("Qdrant Collection Migration")
    logger.info("=" * 60)
    logger.info(f"Collection: {QDRANT_COLLECTION}")
    logger.info(f"Embedding Model: intfloat/multilingual-e5-small")
    logger.info(f"Dimensions: {EMBEDDING_DIM}")
    logger.info("=" * 60)
    
    # Connect to Qdrant
    logger.info(f"Connecting to Qdrant at {QDRANT_URL}...")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )
    
    # Check if collection exists
    collections = [c.name for c in client.get_collections().collections]
    
    if QDRANT_COLLECTION in collections:
        logger.warning(f"⚠️  Collection '{QDRANT_COLLECTION}' exists and will be DELETED!")
        logger.warning("⚠️  All existing embeddings will be lost!")
        
        response = input("\nType 'DELETE' to confirm: ")
        if response != "DELETE":
            logger.info("Migration cancelled.")
            return
        
        logger.info(f"Deleting collection '{QDRANT_COLLECTION}'...")
        client.delete_collection(QDRANT_COLLECTION)
        logger.info("✓ Collection deleted")
    else:
        logger.info(f"Collection '{QDRANT_COLLECTION}' does not exist yet")
    
    # Create new collection
    logger.info(f"Creating collection '{QDRANT_COLLECTION}' with multilingual-e5-small config...")
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
    )
    logger.info("✓ Collection created successfully")
    
    # Verify
    collection_info = client.get_collection(QDRANT_COLLECTION)
    logger.info(f"✓ Collection verified: {collection_info.vectors_count} vectors")
    
    logger.info("=" * 60)
    logger.info("Migration complete!")
    logger.info("=" * 60)
    logger.info("Next steps:")
    logger.info("1. Restart your backend: docker-compose restart backend")
    logger.info("2. Process new audio to populate with multilingual embeddings")
    logger.info("3. Old memories will be re-indexed as vendors use the system")


if __name__ == "__main__":
    try:
        migrate_collection()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
