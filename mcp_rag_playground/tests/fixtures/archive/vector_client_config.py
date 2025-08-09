"""
Configuration classes for VectorClient test fixtures.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from mcp_rag_playground.vectordb.vector_db_interface import Document, SearchResult


@dataclass
class MockConfig:
    """Configuration for mock objects."""
    default_dimension: int = 384
    default_embedding_value: float = 0.1
    default_collection_exists: bool = False
    default_create_collection: bool = True
    default_insert_success: bool = True
    default_test_connection: bool = True


@dataclass
class QueryTestScenario:
    """Configuration for a query test scenario."""
    query_text: str
    expected_preprocessing: str
    description: str
    min_score: float = 0.0
    limit: int = 5
    expected_results: int = 0  # Number of expected results


@dataclass
class UploadTestScenario:
    """Configuration for an upload test scenario."""
    file_path: str
    expected_success: bool
    expected_documents: int
    description: str
    mock_documents: Optional[List[Document]] = None


@dataclass
class VectorClientMockConfig:
    """Configuration for VectorClient mock objects."""
    
    # Mock behavior configuration
    mock_config: MockConfig = field(default_factory=MockConfig)
    
    # Default mock return values
    default_embeddings: List[List[float]] = field(default_factory=lambda: [
        [0.1] * 384,  # First embedding
        [0.2] * 384,  # Second embedding
        [0.3] * 384   # Third embedding
    ])
    
    # Mock documents for document processor
    mock_documents: List[Document] = field(default_factory=lambda: [
        Document(
            content="Test content from file",
            metadata={"source": "test.txt", "type": "text"}
        ),
        Document(
            content="Second document content", 
            metadata={"source": "test.txt", "chunk": 2}
        )
    ])
    
    # Mock search results
    mock_search_results: List[SearchResult] = field(default_factory=lambda: [
        SearchResult(
            document=Document(
                content="High relevance result",
                metadata={"source": "doc1.txt", "score_rank": 1}
            ),
            score=0.95,
            distance=0.05
        ),
        SearchResult(
            document=Document(
                content="Medium relevance result", 
                metadata={"source": "doc2.txt", "score_rank": 2}
            ),
            score=0.75,
            distance=0.25
        ),
        SearchResult(
            document=Document(
                content="Low relevance result",
                metadata={"source": "doc3.txt", "score_rank": 3}  
            ),
            score=0.45,
            distance=0.55
        )
    ])
    
    def get_mock_embedding(self, text: str = None) -> List[float]:
        """Get a mock embedding for given text."""
        return self.default_embeddings[0]
    
    def get_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get mock embeddings for multiple texts."""
        return self.default_embeddings[:len(texts)]
    
    def get_filtered_search_results(self, min_score: float) -> List[SearchResult]:
        """Get search results filtered by minimum score."""
        return [result for result in self.mock_search_results if result.score >= min_score]


@dataclass
class VectorClientQueryConfig:
    """Configuration for query testing scenarios."""
    
    # Query preprocessing test cases
    preprocessing_tests: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("Hello World", "hello world"),
        ("  Extra   Spaces  ", "extra spaces"),
        ("Special!@#$%Characters", "special characters"),
        ("db query", "db database query"),
        ("AI and ML", "ai artificial intelligence and ml machine learning"),
        ("API development", "api application programming interface development"),
        ("UI/UX design", "ui user interface ux user experience design"),
    ])
    
    # Query test scenarios
    query_scenarios: List[QueryTestScenario] = field(default_factory=lambda: [
        QueryTestScenario(
            query_text="test query",
            expected_preprocessing="test query",
            description="Simple query without preprocessing",
            limit=5,
            expected_results=3
        ),
        QueryTestScenario(
            query_text="vector db search",
            expected_preprocessing="vector db database search",
            description="Query with abbreviation expansion",
            limit=10,
            expected_results=3
        ),
        QueryTestScenario(
            query_text="AI ML models",
            expected_preprocessing="ai artificial intelligence ml machine learning models",
            description="Multiple abbreviation expansion",
            limit=5,
            expected_results=2
        ),
        QueryTestScenario(
            query_text="",
            expected_preprocessing="",
            description="Empty query test",
            limit=5,
            expected_results=0
        ),
        QueryTestScenario(
            query_text="   \n\t   ",
            expected_preprocessing="",
            description="Whitespace-only query test",
            limit=5,
            expected_results=0
        )
    ])
    
    # Score filtering tests
    score_filter_tests: List[Tuple[float, int]] = field(default_factory=lambda: [
        (0.0, 3),   # No filtering - all results
        (0.5, 2),   # Medium filtering - high and medium results
        (0.8, 1),   # High filtering - only high result
        (0.99, 0)   # Very high filtering - no results
    ])


@dataclass
class VectorClientTestScenarios:
    """Configuration for various test scenarios."""
    
    # Upload test scenarios
    upload_scenarios: List[UploadTestScenario] = field(default_factory=lambda: [
        UploadTestScenario(
            file_path="test.txt",
            expected_success=True,
            expected_documents=1,
            description="Successful single document upload"
        ),
        UploadTestScenario(
            file_path="multi_chunk.md",
            expected_success=True,
            expected_documents=2,
            description="Multi-document file upload",
            mock_documents=[
                Document(content="First chunk", metadata={"source": "multi_chunk.md", "chunk": 1}),
                Document(content="Second chunk", metadata={"source": "multi_chunk.md", "chunk": 2})
            ]
        ),
        UploadTestScenario(
            file_path="empty_file.txt",
            expected_success=False,
            expected_documents=0,
            description="Empty file upload failure"
        ),
        UploadTestScenario(
            file_path="problematic_file.txt",
            expected_success=False,
            expected_documents=0,
            description="File processing error scenario"
        )
    ])
    
    # Error test scenarios
    error_scenarios: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "name": "collection_creation_failure",
            "description": "Collection creation fails",
            "mock_setup": {
                "collection_exists": False,
                "create_collection": False
            },
            "expected_error": "Failed to create collection"
        },
        {
            "name": "document_processor_error",
            "description": "Document processor raises exception",
            "mock_setup": {
                "processor_exception": Exception("File processing error")
            },
            "expected_result": False
        },
        {
            "name": "embedding_service_error",
            "description": "Embedding service raises exception", 
            "mock_setup": {
                "embedding_exception": Exception("Embedding error")
            },
            "expected_result": []
        },
        {
            "name": "vector_db_connection_error",
            "description": "Vector database connection fails",
            "mock_setup": {
                "test_connection": False
            },
            "expected_result": False
        }
    ])
    
    # Collection management scenarios
    collection_scenarios: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "name": "successful_deletion",
            "description": "Collection deleted successfully",
            "mock_setup": {
                "delete_collection": True
            },
            "expected_result": True,
            "expected_initialized": False
        },
        {
            "name": "failed_deletion",
            "description": "Collection deletion fails",
            "mock_setup": {
                "delete_collection": False
            },
            "expected_result": False
        },
        {
            "name": "get_collection_info_success",
            "description": "Get collection info successfully",
            "mock_setup": {
                "collection_info": {"name": "test", "num_entities": 100}
            },
            "expected_result": {"name": "test", "num_entities": 100}
        },
        {
            "name": "get_collection_info_error",
            "description": "Get collection info fails",
            "mock_setup": {
                "info_exception": Exception("Database error")
            },
            "expected_result": {}
        }
    ])


@dataclass
class VectorClientConfig:
    """Main configuration class for VectorClient tests."""
    
    # Mock configuration
    mock_config: VectorClientMockConfig = field(default_factory=VectorClientMockConfig)
    
    # Query configuration
    query_config: VectorClientQueryConfig = field(default_factory=VectorClientQueryConfig)
    
    # Test scenarios
    test_scenarios: VectorClientTestScenarios = field(default_factory=VectorClientTestScenarios)
    
    # Default collection name
    default_collection_name: str = "test_collection"
    
    def get_query_scenario(self, scenario_name: str) -> Optional[QueryTestScenario]:
        """Get a specific query test scenario."""
        for scenario in self.query_config.query_scenarios:
            if scenario_name in scenario.description.lower():
                return scenario
        return None
    
    def get_upload_scenario(self, scenario_name: str) -> Optional[UploadTestScenario]:
        """Get a specific upload test scenario."""
        for scenario in self.test_scenarios.upload_scenarios:
            if scenario_name in scenario.description.lower():
                return scenario
        return None
    
    def get_error_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific error test scenario."""
        for scenario in self.test_scenarios.error_scenarios:
            if scenario["name"] == scenario_name:
                return scenario
        return None


# Default configuration instance
DEFAULT_VECTOR_CLIENT_CONFIG = VectorClientConfig()