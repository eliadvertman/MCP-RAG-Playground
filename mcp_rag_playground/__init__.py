"""
MCP RAG Playground - Vector database client with RAG capabilities.
"""

from .vectordb.vector_client import VectorClient
from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
from mcp_rag_playground.vectordb.embedding_service import SentenceTransformerEmbedding, MockEmbeddingService
from mcp_rag_playground.config.milvus_config import MilvusConfig
from .vectordb.vector_db_interface import Document, SearchResult
from mcp_rag_playground.rag.rag_api import RagAPI

# Dependency injection imports
from .container import (
    Container,
    ConfigProvider,
    MilvusConfigProvider,
    create_vector_client,
    create_container,
    create_mock_vector_client,
    create_test_container,
    create_dev_container,
    create_prod_container,
    create_rag_api,
    create_mock_rag_api
)

__all__ = [
    # Core classes
    'VectorClient',
    'MilvusVectorDB', 
    'SentenceTransformerEmbedding',
    'MockEmbeddingService',
    'Document',
    'SearchResult',
    'MilvusConfig',
    'RagAPI',
    
    # Dependency injection
    'Container',
    'ConfigProvider',
    'MilvusConfigProvider',
    'create_vector_client',
    'create_container',
    'create_mock_vector_client',
    'create_test_container',
    'create_dev_container',
    'create_prod_container',
    'create_rag_api',
    'create_mock_rag_api'
]