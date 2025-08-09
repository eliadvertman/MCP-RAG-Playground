"""
Configuration classes for RAG API integration test fixtures.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class TestFileConfig:
    """Configuration for test data files."""
    file_type: str
    file_name: str
    description: str
    expected_chunks: int = 1
    expected_success: bool = True


@dataclass
class QueryTestCase:
    """Configuration for a query test case."""
    query: str
    description: str
    expected_min_results: int = 0
    expected_max_results: int = 10
    min_score_threshold: float = 0.0
    expected_content_keywords: List[str] = field(default_factory=list)


@dataclass
class RagApiTestScenarios:
    """Configuration for RAG API test scenarios."""
    
    # Test file configurations
    test_files: List[TestFileConfig] = field(default_factory=lambda: [
        TestFileConfig(
            file_type="txt",
            file_name="test_document.txt",
            description="Plain text document test",
            expected_chunks=1,
            expected_success=True
        ),
        TestFileConfig(
            file_type="md", 
            file_name="test_document.md",
            description="Markdown document test",
            expected_chunks=2,  # Multiple sections expected
            expected_success=True
        ),
        TestFileConfig(
            file_type="py",
            file_name="test_module.py", 
            description="Python source code test",
            expected_chunks=1,
            expected_success=True
        )
    ])
    
    # Document addition test scenarios
    document_scenarios: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "name": "single_document",
            "description": "Add single document to empty collection",
            "files": ["txt"],
            "expected_success": True,
            "expected_doc_count_min": 1
        },
        {
            "name": "multiple_documents",
            "description": "Add multiple documents of different types",
            "files": ["txt", "md", "py"],
            "expected_success": True,
            "expected_doc_count_min": 3
        },
        {
            "name": "duplicate_addition",
            "description": "Add same document multiple times",
            "files": ["txt", "txt"],
            "expected_success": True,
            "expected_doc_count_min": 2
        },
        {
            "name": "nonexistent_file",
            "description": "Attempt to add non-existent file",
            "files": ["nonexistent.txt"],
            "expected_success": False,
            "expected_doc_count_min": 0
        }
    ])
    
    # Query test scenarios
    query_scenarios: List[QueryTestCase] = field(default_factory=lambda: [
        QueryTestCase(
            query="vector database",
            description="Query matching text document content",
            expected_min_results=0,
            expected_max_results=5,
            expected_content_keywords=["vector", "database"]
        ),
        QueryTestCase(
            query="Section 1",
            description="Query matching markdown section",
            expected_min_results=0,
            expected_max_results=5,
            expected_content_keywords=["Section"]
        ),
        QueryTestCase(
            query="hello world",
            description="Query matching Python code content",
            expected_min_results=0,
            expected_max_results=5,
            expected_content_keywords=["hello"]
        ),
        QueryTestCase(
            query="Lorem ipsum",
            description="Query matching Lorem ipsum content",
            expected_min_results=0,
            expected_max_results=5,
            expected_content_keywords=["Lorem", "ipsum"]
        ),
        QueryTestCase(
            query="machine learning AI",
            description="Semantic similarity query",
            expected_min_results=0,
            expected_max_results=5,
            min_score_threshold=0.3
        )
    ])
    
    # Score filtering test cases  
    score_filtering_scenarios: List[Tuple[str, float, str]] = field(default_factory=lambda: [
        ("Lorem ipsum", 0.0, "No score filtering - all results"),
        ("Lorem ipsum", 0.5, "Medium score filtering"),
        ("Lorem ipsum", 0.7, "High score filtering"), 
        ("Lorem ipsum", 0.9, "Very high score filtering")
    ])


@dataclass
class RagApiQueryConfig:
    """Configuration for query testing."""
    
    # Default query parameters
    default_limit: int = 5
    test_limits: List[int] = field(default_factory=lambda: [1, 2, 5, 10])
    
    # Score thresholds for testing
    score_thresholds: List[float] = field(default_factory=lambda: [0.0, 0.3, 0.5, 0.7, 0.9])
    
    # Semantic search quality tests
    semantic_tests: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "query": "dolor sit amet",
            "expected_content": ["Lorem", "ipsum", "dolor"],
            "description": "Semantic similarity to Lorem ipsum content",
            "min_score": 0.1
        },
        {
            "query": "programming language",
            "expected_content": ["Python", "programming"],
            "description": "Programming-related semantic search",
            "min_score": 0.2
        },
        {
            "query": "search technology",
            "expected_content": ["vector", "database", "search"],
            "description": "Technology domain semantic search",
            "min_score": 0.2
        }
    ])
    
    # Edge case queries
    edge_case_queries: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "query": "",
            "description": "Empty query test",
            "expected_results": 0
        },
        {
            "query": "   \n\t   ",
            "description": "Whitespace-only query test", 
            "expected_results": 0
        },
        {
            "query": "!@#$%^&*()",
            "description": "Special characters query test",
            "expected_results": 0
        },
        {
            "query": "verylongquerywithnospacesoranymeaningfulcontenttotest",
            "description": "Very long nonsensical query",
            "expected_results": 0
        }
    ])


@dataclass
class RagApiPerformanceConfig:
    """Configuration for performance testing."""
    
    # Timing thresholds (seconds)
    document_addition_timeout: float = 30.0
    query_response_timeout: float = 5.0
    collection_info_timeout: float = 3.0
    collection_deletion_timeout: float = 10.0
    
    # Indexing wait times
    milvus_indexing_wait: float = 2.0
    large_batch_indexing_wait: float = 5.0
    
    # Performance test configurations
    consistency_test_repetitions: int = 3
    large_document_count: int = 100


@dataclass
class RagApiIntegrationConfig:
    """Main configuration class for RAG API integration tests."""
    
    # Test scenarios configuration
    scenarios: RagApiTestScenarios = field(default_factory=RagApiTestScenarios)
    
    # Query configuration
    query_config: RagApiQueryConfig = field(default_factory=RagApiQueryConfig)
    
    # Performance configuration  
    performance: RagApiPerformanceConfig = field(default_factory=RagApiPerformanceConfig)
    
    # Collection management
    test_collection_prefix: str = "rag_test"
    cleanup_timeout: float = 10.0
    
    # Expected result formats
    expected_result_fields: List[str] = field(default_factory=lambda: [
        "content", "score", "metadata", "source", "document_id"
    ])
    
    def get_test_file_path(self, file_type: str, test_data_dir: Path) -> str:
        """Get the full path to a test file."""
        file_config = next(
            (f for f in self.scenarios.test_files if f.file_type == file_type),
            None
        )
        if file_config:
            return str(test_data_dir / file_config.file_name)
        return ""
    
    def get_all_test_file_paths(self, test_data_dir: Path) -> Dict[str, str]:
        """Get all test file paths as a dictionary."""
        return {
            config.file_type: str(test_data_dir / config.file_name)
            for config in self.scenarios.test_files
        }
    
    def get_query_test_case(self, query_text: str) -> Optional[QueryTestCase]:
        """Get a specific query test case by query text."""
        for case in self.scenarios.query_scenarios:
            if case.query == query_text:
                return case
        return None
    
    def get_document_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific document scenario by name."""
        for scenario in self.scenarios.document_scenarios:
            if scenario["name"] == scenario_name:
                return scenario
        return None
    
    def get_semantic_test(self, query: str) -> Optional[Dict[str, Any]]:
        """Get a specific semantic test case."""
        for test in self.query_config.semantic_tests:
            if test["query"] == query:
                return test
        return None
    
    def should_test_pass_file_verification(self, test_data_dir: Path) -> bool:
        """Check if all required test files exist."""
        for file_config in self.scenarios.test_files:
            file_path = test_data_dir / file_config.file_name
            if not file_path.exists() or not file_path.is_file():
                return False
        return True


# Default configuration instance
DEFAULT_RAG_API_CONFIG = RagApiIntegrationConfig()