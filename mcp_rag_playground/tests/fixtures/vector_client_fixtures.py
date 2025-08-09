"""
Simple vector client test fixtures.
Provides mock objects and test data for vector client tests.
"""

import time
import uuid
from typing import List, Dict, Any
from unittest.mock import Mock

from mcp_rag_playground.vectordb.vector_db_interface import VectorDBInterface, Document, SearchResult
from mcp_rag_playground.vectordb.embedding_service import EmbeddingService
from mcp_rag_playground.vectordb.processor.document_processor import DocumentProcessor


def create_mock_vector_db() -> Mock:
    """Create a mock vector database for testing."""
    mock_db = Mock(spec=VectorDBInterface)
    mock_db.collection_exists.return_value = False
    mock_db.create_collection.return_value = True
    mock_db.insert_documents.return_value = True
    mock_db.search.return_value = []
    mock_db.get_collection_info.return_value = {"name": "test", "num_entities": 0}
    mock_db.delete_collection.return_value = True
    mock_db.test_connection.return_value = True
    return mock_db


def create_mock_embedding_service() -> Mock:
    """Create a mock embedding service for testing."""
    mock_service = Mock(spec=EmbeddingService)
    mock_service.get_dimension.return_value = 384
    mock_service.embed_text.return_value = [0.1] * 384
    mock_service.embed_texts.return_value = [[0.1] * 384, [0.2] * 384]
    return mock_service


def create_mock_document_processor() -> Mock:
    """Create a mock document processor for testing."""
    mock_processor = Mock(spec=DocumentProcessor)
    mock_processor.process_file.return_value = [
        Document(content="Test content", metadata={"source": "test.txt"})
    ]
    return mock_processor


def get_sample_documents() -> List[Document]:
    """Get sample documents for testing."""
    return [
        Document(
            content="First test document about machine learning and AI.",
            metadata={"source": "doc1.txt", "category": "ai"}
        ),
        Document(
            content="Second test document about vector databases and search.",
            metadata={"source": "doc2.txt", "category": "database"}
        ),
        Document(
            content="Third test document about natural language processing.",
            metadata={"source": "doc3.txt", "category": "nlp"}
        )
    ]


def get_sample_embeddings(count: int = 3) -> List[List[float]]:
    """Get sample embeddings for testing."""
    import random
    random.seed(42)  # Ensure reproducible results
    
    embeddings = []
    for i in range(count):
        # Generate normalized random embeddings
        embedding = [random.uniform(-1, 1) for _ in range(384)]
        # Normalize to unit vector
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x/norm for x in embedding]
        embeddings.append(embedding)
    
    return embeddings


def create_search_results() -> List[SearchResult]:
    """Create sample search results for testing."""
    documents = get_sample_documents()
    return [
        SearchResult(
            document=documents[0],
            score=0.95,
            distance=0.05
        ),
        SearchResult(
            document=documents[1], 
            score=0.85,
            distance=0.15
        ),
        SearchResult(
            document=documents[2],
            score=0.75,
            distance=0.25
        )
    ]


def get_query_test_cases() -> List[Dict[str, Any]]:
    """Get test cases for query functionality."""
    return [
        {
            "query": "machine learning AI",
            "expected_preprocessing": ["machine learning", "artificial intelligence", "ai", "ml"],
            "limit": 5,
            "min_score": 0.7
        },
        {
            "query": "vector db search",
            "expected_preprocessing": ["vector", "database", "db", "search"],
            "limit": 10,
            "min_score": 0.5
        },
        {
            "query": "nlp natural language",
            "expected_preprocessing": ["natural language processing", "nlp"],
            "limit": 3,
            "min_score": 0.8
        }
    ]


def get_upload_test_scenarios() -> List[Dict[str, Any]]:
    """Get test scenarios for upload functionality."""
    return [
        {
            "scenario": "successful_upload",
            "file_path": "test_document.txt",
            "processed_docs": get_sample_documents()[:1],
            "expected_result": True
        },
        {
            "scenario": "no_documents_extracted",
            "file_path": "empty_file.txt",
            "processed_docs": [],
            "expected_result": False
        },
        {
            "scenario": "multiple_documents",
            "file_path": "multi_doc.txt",
            "processed_docs": get_sample_documents(),
            "expected_result": True
        }
    ]


def get_performance_test_config() -> Dict[str, Any]:
    """Get performance testing configuration."""
    return {
        "upload_timeout": 30.0,  # seconds
        "query_timeout": 5.0,    # seconds
        "batch_sizes": [1, 5, 10, 25],
        "stress_test_documents": 100
    }


def generate_unique_collection_name() -> str:
    """Generate a unique collection name for testing."""
    return f"test_collection_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def get_collection_info_samples() -> List[Dict[str, Any]]:
    """Get sample collection information."""
    return [
        {
            "name": "test_collection",
            "num_entities": 0,
            "schema": {"fields": ["id", "content", "metadata", "embedding"]}
        },
        {
            "name": "populated_collection",
            "num_entities": 100,
            "schema": {"fields": ["id", "content", "metadata", "embedding"]},
            "index_info": {"type": "IVF_FLAT", "metric": "COSINE"}
        }
    ]


def create_mock_with_search_results(search_results: List[SearchResult] = None) -> Mock:
    """Create a mock vector database that returns specific search results."""
    mock_db = create_mock_vector_db()
    if search_results is None:
        search_results = create_search_results()
    mock_db.search.return_value = search_results
    mock_db.collection_exists.return_value = True
    return mock_db


def create_mock_with_failures() -> Mock:
    """Create a mock vector database that simulates failures."""
    mock_db = create_mock_vector_db()
    mock_db.create_collection.return_value = False
    mock_db.insert_documents.return_value = False
    mock_db.test_connection.return_value = False
    return mock_db


def get_preprocessing_test_cases() -> List[tuple]:
    """Get test cases for query preprocessing."""
    return [
        ("vector db", "vector database db"),
        ("ai ml", "artificial intelligence ai machine learning ml"),
        ("nlp processing", "natural language processing nlp processing"),
        ("api rest", "application programming interface api representational state transfer rest"),
        ("simple query", "simple query")  # No expansion expected
    ]