"""
Test script for multilingual-e5-small embeddings
Verifies Hindi, English, and Hinglish support
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from services.embedding import embedding_service


def test_embedding_dimensions():
    """Test that embeddings have correct dimensions."""
    logger.info("=" * 60)
    logger.info("Test 1: Embedding Dimensions")
    logger.info("=" * 60)
    
    text = "Test text"
    embedding = embedding_service.embed(text)
    
    logger.info(f"Text: {text}")
    logger.info(f"Embedding dimension: {len(embedding)}")
    logger.info(f"Expected: 384")
    
    assert len(embedding) == 384, f"Expected 384 dimensions, got {len(embedding)}"
    logger.info("✓ PASSED\n")


def test_hindi_text():
    """Test Hindi text embedding."""
    logger.info("=" * 60)
    logger.info("Test 2: Hindi Text")
    logger.info("=" * 60)
    
    texts = [
        "आज मैंने 50 केले बेचे",
        "व्यापार अच्छा था",
        "मुझे 500 रुपये का मुनाफा हुआ",
    ]
    
    for text in texts:
        embedding = embedding_service.embed_passage(text)
        logger.info(f"Text: {text}")
        logger.info(f"Embedding dimension: {len(embedding)}")
        logger.info(f"First 5 values: {embedding[:5]}")
        assert len(embedding) == 384
        logger.info("✓ PASSED")
    
    logger.info("")


def test_hinglish_text():
    """Test Hinglish (code-mixed) text embedding."""
    logger.info("=" * 60)
    logger.info("Test 3: Hinglish (Code-Mixed) Text")
    logger.info("=" * 60)
    
    texts = [
        "Aaj maine 50 kele beche",
        "Business achha tha aaj",
        "Mujhe 500 rupaye ka profit hua",
        "Aaj dhanda bhut manda gya",
    ]
    
    for text in texts:
        embedding = embedding_service.embed_passage(text)
        logger.info(f"Text: {text}")
        logger.info(f"Embedding dimension: {len(embedding)}")
        logger.info(f"First 5 values: {embedding[:5]}")
        assert len(embedding) == 384
        logger.info("✓ PASSED")
    
    logger.info("")


def test_english_text():
    """Test English text embedding."""
    logger.info("=" * 60)
    logger.info("Test 4: English Text")
    logger.info("=" * 60)
    
    texts = [
        "Today I sold 50 bananas",
        "Business was good today",
        "I made 500 rupees profit",
    ]
    
    for text in texts:
        embedding = embedding_service.embed_passage(text)
        logger.info(f"Text: {text}")
        logger.info(f"Embedding dimension: {len(embedding)}")
        logger.info(f"First 5 values: {embedding[:5]}")
        assert len(embedding) == 384
        logger.info("✓ PASSED")
    
    logger.info("")


def test_query_vs_passage():
    """Test that query and passage embeddings are different."""
    logger.info("=" * 60)
    logger.info("Test 5: Query vs Passage Prefixes")
    logger.info("=" * 60)
    
    text = "Aaj maine kele beche"
    
    query_embedding = embedding_service.embed(text)
    passage_embedding = embedding_service.embed_passage(text)
    
    logger.info(f"Text: {text}")
    logger.info(f"Query embedding (first 5): {query_embedding[:5]}")
    logger.info(f"Passage embedding (first 5): {passage_embedding[:5]}")
    
    # They should be different due to different prefixes
    assert query_embedding != passage_embedding, "Query and passage embeddings should differ"
    logger.info("✓ PASSED - Embeddings are different (prefixes working)\n")


def test_semantic_similarity():
    """Test that semantically similar texts have similar embeddings."""
    logger.info("=" * 60)
    logger.info("Test 6: Semantic Similarity")
    logger.info("=" * 60)
    
    import numpy as np
    
    # Similar texts
    text1 = "Aaj maine 50 kele beche"
    text2 = "Maine aaj 50 bananas bechein"
    
    # Different text
    text3 = "Mujhe ek naya phone chahiye"
    
    emb1 = np.array(embedding_service.embed_passage(text1))
    emb2 = np.array(embedding_service.embed_passage(text2))
    emb3 = np.array(embedding_service.embed_passage(text3))
    
    # Cosine similarity
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_1_2 = cosine_similarity(emb1, emb2)
    sim_1_3 = cosine_similarity(emb1, emb3)
    
    logger.info(f"Text 1: {text1}")
    logger.info(f"Text 2: {text2}")
    logger.info(f"Text 3: {text3}")
    logger.info(f"Similarity (1-2): {sim_1_2:.4f}")
    logger.info(f"Similarity (1-3): {sim_1_3:.4f}")
    
    assert sim_1_2 > sim_1_3, "Similar texts should have higher similarity"
    logger.info("✓ PASSED - Semantic similarity working\n")


def run_all_tests():
    """Run all embedding tests."""
    logger.info("\n" + "=" * 60)
    logger.info("MULTILINGUAL-E5-SMALL EMBEDDING TESTS")
    logger.info("=" * 60 + "\n")
    
    try:
        test_embedding_dimensions()
        test_hindi_text()
        test_hinglish_text()
        test_english_text()
        test_query_vs_passage()
        test_semantic_similarity()
        
        logger.info("=" * 60)
        logger.info("ALL TESTS PASSED ✓")
        logger.info("=" * 60)
        logger.info("Multilingual embeddings are working correctly!")
        logger.info("Hindi, English, and Hinglish are all supported.")
        
    except Exception as e:
        logger.error(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
