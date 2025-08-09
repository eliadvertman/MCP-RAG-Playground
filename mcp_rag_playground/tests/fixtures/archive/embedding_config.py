"""
Configuration classes for embedding service test fixtures.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path


@dataclass
class ModelConfig:
    """Configuration for a specific embedding model."""
    name: str
    expected_dimension: int
    download_timeout: float = 300.0  # seconds
    description: str = ""


@dataclass
class SimilarityTestCase:
    """Configuration for a similarity test case."""
    text1: str
    text2: str
    expected_similarity: str  # "high", "medium", "low"
    description: str = ""


@dataclass
class PerformanceThreshold:
    """Performance thresholds for timing tests."""
    single_embed_max_time: float = 5.0
    batch_embed_max_time: float = 10.0
    model_load_max_time: float = 30.0
    large_text_max_time: float = 15.0


@dataclass
class EmbeddingTestTexts:
    """Collection of test texts for embedding service tests."""
    
    # Single text examples
    single_texts: List[str] = field(default_factory=lambda: [
        "This is a test sentence for embedding.",
        "Vector databases enable semantic search capabilities.",
        "Machine learning models process data efficiently.",
        "Python programming language is versatile and powerful.",
        "Natural language processing enables computers to understand text.",
        "",  # Empty string test
        "   \n\t   ",  # Whitespace only test
        "!@#$%^&*()",  # Special characters test
    ])
    
    # Batch text examples
    batch_texts: List[List[str]] = field(default_factory=lambda: [
        [
            "First test sentence.", 
            "Second test sentence with different content.", 
            "Third sentence about vector databases."
        ],
        [
            "Short.", 
            "Medium length sentence with more words.", 
            "A very long sentence that contains multiple concepts and ideas to test the embedding model's capability to handle longer text inputs effectively."
        ],
        [
            "Python programming",
            "JavaScript development", 
            "TypeScript applications",
            "Go backend services",
            "Rust system programming"
        ]
    ])
    
    # Multilingual examples
    multilingual_texts: List[str] = field(default_factory=lambda: [
        "Hello world in English.",
        "Hola mundo en español.",
        "Bonjour le monde en français.", 
        "Hallo Welt auf Deutsch.",
        "Ciao mondo in italiano.",
        "こんにちは世界 in Japanese.",
        "Привет мир in Russian."
    ])
    
    # Performance test texts
    performance_texts: Dict[str, str] = field(default_factory=lambda: {
        "single": "Performance test for single embedding generation with sufficient content.",
        "large": "This is a very long text for performance testing. " * 100,
        "stability": "Testing numerical stability of embeddings with identical input."
    })


@dataclass 
class EmbeddingSimilarityTests:
    """Configuration for similarity test cases."""
    
    test_cases: List[SimilarityTestCase] = field(default_factory=lambda: [
        SimilarityTestCase(
            text1="The cat sits on the mat.",
            text2="A cat is sitting on a mat.",
            expected_similarity="high",
            description="Paraphrase similarity test"
        ),
        SimilarityTestCase(
            text1="The cat sits on the mat.",
            text2="Python programming and software development.",
            expected_similarity="low", 
            description="Unrelated content similarity test"
        ),
        SimilarityTestCase(
            text1="Machine learning and artificial intelligence",
            text2="AI and ML technologies",
            expected_similarity="high",
            description="Semantic equivalence test"
        ),
        SimilarityTestCase(
            text1="Database management systems",
            text2="Vector databases and embeddings",
            expected_similarity="medium",
            description="Related domain concepts"
        )
    ])
    
    # Similarity thresholds
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "high": 0.5,      # Above this is high similarity
        "medium": 0.3,    # Between medium and high
        "low": 0.3        # Below this is low similarity
    })


@dataclass
class EmbeddingPerformanceConfig:
    """Configuration for performance testing."""
    
    thresholds: PerformanceThreshold = field(default_factory=PerformanceThreshold)
    
    # Batch size configurations
    batch_sizes: List[int] = field(default_factory=lambda: [1, 5, 10, 25, 50])
    
    # Repetition configs for stability testing
    stability_repetitions: int = 5
    numerical_tolerance: float = 1e-10
    
    # Large text configuration  
    large_text_multiplier: int = 100
    large_text_base: str = "This is a very long text for performance testing. "


@dataclass
class EmbeddingServiceConfig:
    """Main configuration class for embedding service tests."""
    
    # Available models for testing
    models: Dict[str, ModelConfig] = field(default_factory=lambda: {
        "default": ModelConfig(
            name="all-MiniLM-L6-v2",
            expected_dimension=384,
            download_timeout=300.0,
            description="Default lightweight model for testing"
        ),
        "alternative": ModelConfig(
            name="all-mpnet-base-v2", 
            expected_dimension=768,
            download_timeout=600.0,
            description="Higher quality alternative model"
        ),
        "small": ModelConfig(
            name="paraphrase-albert-small-v2",
            expected_dimension=768,
            download_timeout=300.0,
            description="Compact model for quick testing"
        )
    })
    
    # Test text collections
    texts: EmbeddingTestTexts = field(default_factory=EmbeddingTestTexts)
    
    # Similarity test configurations
    similarity_tests: EmbeddingSimilarityTests = field(default_factory=EmbeddingSimilarityTests)
    
    # Performance test configurations
    performance: EmbeddingPerformanceConfig = field(default_factory=EmbeddingPerformanceConfig)
    
    def get_default_model(self) -> ModelConfig:
        """Get the default model configuration."""
        return self.models["default"]
    
    def get_model(self, model_key: str) -> ModelConfig:
        """Get a specific model configuration."""
        return self.models.get(model_key, self.get_default_model())
    
    def get_single_test_texts(self) -> List[str]:
        """Get single text examples for testing."""
        return self.texts.single_texts
    
    def get_batch_test_texts(self, batch_index: int = 0) -> List[str]:
        """Get batch text examples for testing."""
        if batch_index < len(self.texts.batch_texts):
            return self.texts.batch_texts[batch_index]
        return self.texts.batch_texts[0]
    
    def get_similarity_test_case(self, case_index: int = 0) -> SimilarityTestCase:
        """Get a specific similarity test case."""
        if case_index < len(self.similarity_tests.test_cases):
            return self.similarity_tests.test_cases[case_index]
        return self.similarity_tests.test_cases[0]
    
    def get_performance_text(self, text_type: str = "single") -> str:
        """Get performance test text."""
        return self.texts.performance_texts.get(text_type, self.texts.performance_texts["single"])


# Default configuration instance
DEFAULT_EMBEDDING_CONFIG = EmbeddingServiceConfig()