"""
pytest configuration and shared fixtures for the test suite.
"""

from unittest.mock import Mock

import pytest

# Import simple fixtures
from mcp_rag_playground.tests.fixtures import embedding_fixtures, vector_client_fixtures
from mcp_rag_playground.vectordb.embedding_service import EmbeddingService
from mcp_rag_playground.vectordb.vector_db_interface import VectorDBInterface



def pytest_configure(config):
    """Configure pytest with custom markers."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )
    config.addinivalue_line(
        "markers", "milvus: mark test as requiring Milvus connection"
    )
    config.addinivalue_line(
        "markers", "metadata: mark test as testing metadata functionality"
    )
    config.addinivalue_line(
        "markers", "embedding: mark test as requiring embedding models"
    )
    config.addinivalue_line(
        "markers", "requires_milvus: mark test as requiring Milvus connection"
    )
    config.addinivalue_line(
        "markers", "requires_embedding: mark test as requiring embedding models"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names and content."""
    for item in items:
        # Add embedding marker to tests that use real embedding models
        if "embedding_service" in item.nodeid or "SentenceTransformer" in str(item.function):
            item.add_marker(pytest.mark.embedding)

        # Add milvus marker to tests that use real Milvus
        if "milvus_client" in item.nodeid or "MilvusVectorDB" in str(item.function):
            item.add_marker(pytest.mark.milvus)

        # Add integration marker to integration test files
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)



# Legacy configuration fixtures removed - using simple fixtures instead


# Old complex mock fixtures removed - using simple ones below


# Configuration-based test data fixtures removed - using simple fixtures instead


# Skip markers removed - tests handle their own dependencies


# Cleanup fixtures removed - TestHelpers module not found



# Performance and sample fixtures removed - using simple fixtures instead


# Conditional and parameterized fixtures removed - using simple fixtures instead


# Simple embedding fixtures
@pytest.fixture
def embedding_single_texts():
    """Get single test texts for embedding tests."""
    return embedding_fixtures.get_single_test_texts()


@pytest.fixture
def embedding_batch_texts():
    """Get batch test texts for embedding tests."""
    return embedding_fixtures.get_batch_test_texts()


@pytest.fixture
def embedding_multilingual_texts():
    """Get multilingual texts for embedding tests."""
    return embedding_fixtures.get_multilingual_texts()


@pytest.fixture
def embedding_edge_case_texts():
    """Get edge case texts for embedding tests."""
    return embedding_fixtures.get_edge_case_texts()


@pytest.fixture
def embedding_similarity_pair():
    """Get high similarity text pair for testing."""
    return embedding_fixtures.get_high_similarity_pair()


@pytest.fixture
def embedding_model_configs():
    """Get embedding model configurations."""
    return embedding_fixtures.get_model_configs()


# Vector client fixtures (moved from test files)
@pytest.fixture
def mock_vector_db():
    """Create mock vector database for unit tests."""
    return vector_client_fixtures.create_mock_vector_db()


@pytest.fixture
def mock_embedding_service():
    """Create mock embedding service for unit tests."""
    return vector_client_fixtures.create_mock_embedding_service()


@pytest.fixture
def mock_document_processor():
    """Create mock document processor for unit tests."""
    return vector_client_fixtures.create_mock_document_processor()


@pytest.fixture
def sample_documents():
    """Get sample documents for testing."""
    return vector_client_fixtures.get_sample_documents()


@pytest.fixture
def sample_embeddings():
    """Get sample embeddings for testing."""
    return vector_client_fixtures.get_sample_embeddings()


@pytest.fixture
def search_results():
    """Get sample search results for testing."""
    return vector_client_fixtures.create_search_results()


# Integration test fixtures (moved from test files)
@pytest.fixture
def test_data_dir():
    """Get path to test data directory."""
    from pathlib import Path
    return Path(__file__).parent / "test_data"


@pytest.fixture
def test_files(test_data_dir):
    """Get paths to test data files."""
    return {
        "txt": str(test_data_dir / "test_document.txt"),
        "md": str(test_data_dir / "test_document.md"),
        "py": str(test_data_dir / "test_module.py")
    }


@pytest.fixture
def test_collection_name():
    """Generate unique test collection name."""
    return vector_client_fixtures.generate_unique_collection_name()


# Milvus-specific fixtures (moved from test files)
@pytest.fixture
def milvus_config_basic():
    """Create basic Milvus configuration for testing."""
    from mcp_rag_playground.config.milvus_config import MilvusConfig
    return MilvusConfig(
        host="localhost",
        port=19530,
        collection_name="test_collection",
        index_type="IVF_FLAT",
        metric_type="COSINE"
    )


@pytest.fixture
def milvus_client_basic(milvus_config_basic):
    """Create MilvusVectorDB client for testing."""
    from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
    return MilvusVectorDB(config=milvus_config_basic)


# RAG API fixtures (moved from test files)
@pytest.fixture
def rag_api_basic(test_collection_name):
    """Create RagAPI with real components for integration testing."""
    from mcp_rag_playground.rag.rag_api import RagAPI
    from mcp_rag_playground.vectordb.vector_client import VectorClient
    from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
    from mcp_rag_playground.vectordb.embedding_service import SentenceTransformerEmbedding
    from mcp_rag_playground.vectordb.processor.document_processor import DocumentProcessor
    from mcp_rag_playground.config.milvus_config import MilvusConfig
    
    # Create real components
    milvus_config = MilvusConfig(
        host="localhost",
        port=19530,
        collection_name=test_collection_name,
        index_type="IVF_FLAT",
        metric_type="COSINE"
    )
    vector_db = MilvusVectorDB(config=milvus_config)
    embedding_service = SentenceTransformerEmbedding(model_name="all-MiniLM-L6-v2")
    document_processor = DocumentProcessor()
    
    # Create vector client
    vector_client = VectorClient(
        vector_db=vector_db,
        embedding_service=embedding_service,
        document_processor=document_processor,
        collection_name=test_collection_name
    )
    
    # Create RAG API
    return RagAPI(vector_client=vector_client, collection_name=test_collection_name)