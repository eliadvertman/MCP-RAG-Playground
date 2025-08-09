"""
Simple embedding service test fixtures.
Provides test data for embedding service tests without complex provider patterns.
"""

from typing import List, Dict, Tuple, Any


def get_single_test_texts() -> List[str]:
    """Get simple test texts for single embedding tests."""
    return [
        "This is a test sentence for embedding.",
        "Python programming language is versatile.",
        "Machine learning models require training data.",
        "Vector databases store high-dimensional data.",
        "Natural language processing enables text understanding."
    ]


def get_batch_test_texts() -> List[str]:
    """Get test texts for batch embedding tests."""
    return [
        "First document about artificial intelligence and machine learning.",
        "Second document discussing vector databases and semantic search.",
        "Third document covering natural language processing techniques.",
        "Fourth document explaining neural networks and deep learning.",
        "Fifth document about information retrieval and search systems."
    ]


def get_multilingual_texts() -> List[str]:
    """Get multilingual test texts."""
    return [
        "Hello world in English",
        "Bonjour le monde en français", 
        "Hola mundo en español",
        "Hallo Welt auf Deutsch",
        "こんにちは世界、日本語で"
    ]


def get_edge_case_texts() -> List[str]:
    """Get edge case test texts."""
    return [
        "",  # Empty string
        "   \n\t   ",  # Whitespace only
        "!@#$%^&*()",  # Special characters only
        "a",  # Single character
        "Very long text " * 100,  # Very long text (~1400 chars)
        "123 456 789",  # Numbers
        "UPPERCASE TEXT ONLY",  # All caps
        "mixed CaSe TeXt"  # Mixed case
    ]


def get_similarity_pairs() -> List[Tuple[str, str, float]]:
    """Get pairs of texts with expected similarity levels."""
    return [
        # High similarity pairs (threshold > 0.7)
        (
            "Machine learning algorithms process data to make predictions.",
            "Data processing algorithms in machine learning make predictions.",
            0.7
        ),
        (
            "Python is a programming language used for AI development.",
            "AI development often uses Python programming language.",
            0.7
        ),
        # Medium similarity pairs (threshold 0.4-0.7)
        (
            "Dogs are loyal pets that enjoy playing outside.",
            "Cats are independent animals that prefer indoor activities.",
            0.4
        ),
        # Low similarity pairs (threshold < 0.4)
        (
            "The weather is sunny and warm today.",
            "Database indexing improves query performance significantly.",
            0.1
        )
    ]


def get_model_configs() -> Dict[str, Dict[str, Any]]:
    """Get embedding model configurations for testing."""
    return {
        "default": {
            "name": "all-MiniLM-L6-v2",
            "dimension": 384,
            "description": "Default lightweight model for testing"
        },
        "alternative": {
            "name": "all-mpnet-base-v2", 
            "dimension": 768,
            "description": "Alternative higher-quality model"
        }
    }


def get_performance_test_config() -> Dict[str, Any]:
    """Get configuration for performance testing."""
    return {
        "batch_sizes": [1, 5, 10, 20],
        "max_embedding_time": 10.0,  # seconds
        "max_batch_time": 30.0,  # seconds
        "stability_repetitions": 3,
        "stability_tolerance": 1e-6
    }


def get_mock_embeddings(count: int = 1, dimension: int = 384) -> List[List[float]]:
    """Generate mock embeddings for testing."""
    import random
    random.seed(42)  # Ensure reproducible results
    
    embeddings = []
    for i in range(count):
        # Generate normalized random embeddings
        embedding = [random.uniform(-1, 1) for _ in range(dimension)]
        # Normalize to unit vector
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x/norm for x in embedding]
        embeddings.append(embedding)
    
    return embeddings


def get_high_similarity_pair() -> Tuple[str, str, float]:
    """Get a pair of texts with high expected similarity."""
    pairs = get_similarity_pairs()
    # Return the first high similarity pair
    return pairs[0]


def get_low_similarity_pair() -> Tuple[str, str, float]:
    """Get a pair of texts with low expected similarity.""" 
    pairs = get_similarity_pairs()
    # Return the last low similarity pair
    return pairs[-1]


def get_stability_test_config() -> Dict[str, Any]:
    """Get configuration for numerical stability testing."""
    return {
        "test_text": "This text will be embedded multiple times to test stability.",
        "repetitions": 5,
        "tolerance": 1e-6
    }