"""
MCP RAG Playground - Vector database client with RAG capabilities.
"""

from .vectordb.vector_client import VectorClient
from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
from mcp_rag_playground.vectordb.embedding_service import SentenceTransformerEmbedding, MockEmbeddingService
from mcp_rag_playground.config.milvus_config import MilvusConfig
from .vectordb.vector_db_interface import Document, SearchResult
from mcp_rag_playground.rag.rag_api import RagAPI

# MCP Server imports (conditional)
try:
    from .mcp import RagMCPServer
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    RagMCPServer = None

# Dependency injection imports (using new dependency-injector)
from .container import (
    create_vector_client,
    create_rag_api,
    create_test_vector_client,
    create_prod_vector_client,
    create_test_rag_api,
    create_prod_rag_api,
    create_milvus_client,
    create_embedding_service,
    create_test_embedding_service,
    create_document_processor,
    create_rag_mcp_server,
    create_mock_rag_mcp_server
)

# Build __all__ list dynamically based on what's available
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
    'create_vector_client',
    'create_rag_api',
    'create_test_vector_client',
    'create_prod_vector_client',
    'create_test_rag_api',
    'create_prod_rag_api',
    'create_milvus_client',
    'create_embedding_service',
    'create_test_embedding_service',
    'create_document_processor',
    'create_rag_mcp_server',
    'create_mock_rag_mcp_server'
]

# Add MCP Server class if available
if _MCP_AVAILABLE:
    __all__.append('RagMCPServer')