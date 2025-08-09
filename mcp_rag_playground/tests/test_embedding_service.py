"""
Test suite for embedding service implementations.
Uses real sentence-transformer models (no mocks) for comprehensive testing.
"""

import pytest
import numpy as np
from typing import List
from unittest.mock import patch

from mcp_rag_playground.vectordb.embedding_service import (
    EmbeddingService, 
    SentenceTransformerEmbedding
)


class TestSentenceTransformerEmbedding:
    """Test suite for SentenceTransformerEmbedding using real models."""

    @pytest.fixture
    def embedding_service(self, embedding_model_configs):
        """Create embedding service with default model."""
        model_config = embedding_model_configs["default"]
        return SentenceTransformerEmbedding(model_name=model_config["name"])
    
    @pytest.fixture
    def custom_embedding_service(self, embedding_model_configs):
        """Create embedding service with alternative model."""
        model_config = embedding_model_configs["alternative"]
        return SentenceTransformerEmbedding(model_name=model_config["name"])

    @pytest.mark.slow
    @pytest.mark.integration
    def test_model_loading_lazy_initialization(self, embedding_service):
        """Test that model is loaded lazily on first use."""
        # Model should not be loaded initially
        assert embedding_service._model is None
        assert embedding_service._dimension is None
        
        # First call should trigger model loading
        dimension = embedding_service.get_dimension()
        
        # Model should now be loaded
        assert embedding_service._model is not None
        assert embedding_service._dimension is not None
        assert dimension > 0

    @pytest.mark.slow
    @pytest.mark.integration
    def test_embed_text_single(self, embedding_service, embedding_single_texts):
        """Test embedding a single text."""
        text = embedding_single_texts[0]  # Use first test text
        
        embedding = embedding_service.embed_text(text)
        
        # Verify embedding properties
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        
        # Check dimension consistency
        expected_dimension = embedding_service.get_dimension()
        assert len(embedding) == expected_dimension

    @pytest.mark.slow
    @pytest.mark.integration
    def test_embed_texts_batch(self, embedding_service, embedding_batch_texts):
        """Test embedding multiple texts."""
        texts = embedding_batch_texts  # Use batch texts from fixture
        
        embeddings = embedding_service.embed_texts(texts)
        
        # Verify batch embeddings
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)
        
        # Check each embedding
        expected_dimension = embedding_service.get_dimension()
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == expected_dimension
            assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.slow
    @pytest.mark.integration
    def test_dimension_consistency(self, embedding_service):
        """Test that dimension is consistent across calls."""
        # Get dimension multiple times
        dim1 = embedding_service.get_dimension()
        dim2 = embedding_service.get_dimension()
        
        assert dim1 == dim2
        assert dim1 > 0
        
        # Verify embedding dimensions match
        text = "Test text for dimension verification."
        embedding = embedding_service.embed_text(text)
        assert len(embedding) == dim1

    @pytest.mark.slow
    @pytest.mark.integration
    def test_embedding_similarity(self, embedding_service, embedding_similarity_pair):
        """Test that similar texts have higher similarity."""
        # Get similarity pair and threshold from fixture
        text1, text2, threshold = embedding_similarity_pair
        
        # Get a dissimilar text
        from mcp_rag_playground.tests.fixtures.embedding_fixtures import get_low_similarity_pair
        low_text1, text3, _ = get_low_similarity_pair()
        
        emb1 = embedding_service.embed_text(text1)
        emb2 = embedding_service.embed_text(text2)
        emb3 = embedding_service.embed_text(text3)
        
        # Calculate cosine similarities
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            a_np = np.array(a)
            b_np = np.array(b)
            return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
        
        sim_12 = cosine_similarity(emb1, emb2)
        sim_13 = cosine_similarity(emb1, emb3)
        
        # Similar texts should have higher similarity
        assert sim_12 > sim_13
        
        # Use threshold from fixture
        assert sim_12 > threshold  # Should meet high similarity threshold

    @pytest.mark.slow
    @pytest.mark.integration
    def test_custom_model_name(self, custom_embedding_service):
        """Test embedding service with custom model name."""
        text = "Testing custom model embedding."
        
        embedding = custom_embedding_service.embed_text(text)
        dimension = custom_embedding_service.get_dimension()
        
        assert isinstance(embedding, list)
        assert len(embedding) == dimension
        assert dimension > 0

    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.parametrize("text_content,description", [
        ("", "empty string"),
        ("   \n\t   ", "whitespace only"), 
        ("!@#$%^&*()", "special characters")
    ])
    def test_edge_case_texts(self, embedding_service, text_content, description):
        """Test handling of edge case text inputs."""
        embedding = embedding_service.embed_text(text_content)
        assert isinstance(embedding, list)
        assert len(embedding) == embedding_service.get_dimension()

    @pytest.mark.slow
    @pytest.mark.integration
    def test_batch_vs_individual_consistency(self, embedding_service):
        """Test that batch and individual embeddings are consistent."""
        texts = ["First text.", "Second text.", "Third text."]
        
        # Get embeddings individually
        individual_embeddings = [embedding_service.embed_text(text) for text in texts]
        
        # Get embeddings in batch
        batch_embeddings = embedding_service.embed_texts(texts)
        
        # Compare embeddings (should be very close)
        assert len(individual_embeddings) == len(batch_embeddings)
        
        for individual, batch in zip(individual_embeddings, batch_embeddings):
            individual_np = np.array(individual)
            batch_np = np.array(batch)
            
            # Should be very close (allowing for small numerical differences)
            np.testing.assert_allclose(individual_np, batch_np, rtol=1e-5, atol=1e-6)

    @pytest.mark.unit
    def test_missing_sentence_transformers_import(self):
        """Test error handling when sentence-transformers is not available."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'sentence_transformers'")):
            embedding_service = SentenceTransformerEmbedding()
            
            with pytest.raises(ImportError, match="sentence-transformers is required"):
                embedding_service.embed_text("test")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_large_text_handling(self, embedding_service):
        """Test handling of large text inputs."""
        # Create a large text (longer than typical sentence)
        large_text = "This is a very long text. " * 100  # ~2700 characters
        
        embedding = embedding_service.embed_text(large_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedding_service.get_dimension()
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.slow
    @pytest.mark.integration
    def test_multiple_languages(self, embedding_service, embedding_multilingual_texts):
        """Test embedding texts in different languages."""
        texts = embedding_multilingual_texts  # Use multilingual texts from fixture
        
        embeddings = embedding_service.embed_texts(texts)
        
        assert len(embeddings) == len(texts)
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == embedding_service.get_dimension()

    @pytest.mark.slow
    @pytest.mark.integration
    def test_numerical_stability(self, embedding_service):
        """Test that embeddings are numerically stable."""
        from mcp_rag_playground.tests.fixtures.embedding_fixtures import get_stability_test_config
        stability_config = get_stability_test_config()
        text = stability_config["test_text"]
        repetitions = stability_config["repetitions"]
        
        # Get embedding multiple times
        embeddings = [embedding_service.embed_text(text) for _ in range(repetitions)]
        
        # All embeddings should be identical (within tolerance)
        tolerance = stability_config["tolerance"]
        for i in range(1, len(embeddings)):
            np.testing.assert_allclose(embeddings[0], embeddings[i], rtol=tolerance, atol=tolerance)

    @pytest.mark.slow
    @pytest.mark.integration
    def test_abstract_interface_compliance(self, embedding_service):
        """Test that SentenceTransformerEmbedding implements EmbeddingService interface."""
        assert isinstance(embedding_service, EmbeddingService)
        
        # Verify all required methods are implemented
        assert hasattr(embedding_service, 'embed_text')
        assert hasattr(embedding_service, 'embed_texts')
        assert hasattr(embedding_service, 'get_dimension')
        
        # Verify methods are callable
        assert callable(embedding_service.embed_text)
        assert callable(embedding_service.embed_texts)
        assert callable(embedding_service.get_dimension)
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.parametrize("text_type", ["single", "large", "stability"])
    def test_performance_texts(self, embedding_service, text_type, embedding_single_texts):
        """Test embedding performance with different text types."""
        from mcp_rag_playground.tests.fixtures.embedding_fixtures import get_stability_test_config
        
        if text_type == "single":
            text = embedding_single_texts[0]
        elif text_type == "large":
            text = "Long text " * 100  # Create long text
        else:  # stability
            stability_config = get_stability_test_config()
            text = stability_config["test_text"]
        
        # Test that we can embed the performance text
        embedding = embedding_service.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedding_service.get_dimension()
        assert all(isinstance(x, float) for x in embedding)