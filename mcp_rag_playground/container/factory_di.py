"""
Convenience factory methods using dependency-injector.
"""

from typing import Optional
from .container_di import (
    create_container,
    create_vector_client,
    create_rag_api,
    create_test_vector_client,
    create_prod_vector_client,
    create_test_rag_api,
    create_prod_rag_api
)
from ..vectordb.milvus.milvus_client import MilvusVectorDB
from ..vectordb.embedding_service import SentenceTransformerEmbedding, MockEmbeddingService
from ..vectordb.processor.document_processor import DocumentProcessor
from ..vectordb.vector_client import VectorClient
from ..rag.rag_api import RagAPI

# Try to import MCP components
try:
    from ..mcp.rag_server import RagMCPServer
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


def create_milvus_client(environment: str = "prod") -> MilvusVectorDB:
    """Create a configured MilvusVectorDB instance."""
    container = create_container(environment)
    return container.vector_db()


def create_embedding_service(environment: str = "prod") -> SentenceTransformerEmbedding:
    """Create a configured embedding service."""
    container = create_container(environment)
    if environment == "test":
        return container.mock_embedding_service()
    else:
        return container.embedding_service()


def create_document_processor(environment: str = "prod") -> DocumentProcessor:
    """Create a configured document processor."""
    container = create_container(environment)
    return container.document_processor()


# MCP Server functions (only if MCP is available)
if _MCP_AVAILABLE:
    def create_rag_mcp_server(
        environment: str = "prod", 
        collection_name: Optional[str] = None,
        server_name: str = "RAG Knowledge Base"
    ) -> RagMCPServer:
        """
        Create a RAG MCP Server with the specified environment configuration.
        
        Args:
            environment: Environment configuration ("test" or "prod")
            collection_name: Optional collection name override
            server_name: Name for the MCP server
            
        Returns:
            Configured RagMCPServer instance
        """
        rag_api = create_rag_api(environment, collection_name)
        return RagMCPServer(rag_api=rag_api, server_name=server_name)

    def create_mock_rag_mcp_server(
        collection_name: str = "test_collection",
        server_name: str = "Test RAG Knowledge Base"
    ) -> RagMCPServer:
        """
        Create a mock RAG MCP Server for testing and development.
        
        Args:
            collection_name: Name for the RAG collection
            server_name: Name for the MCP server
            
        Returns:
            RagMCPServer instance with mock services
        """
        return create_rag_mcp_server("test", collection_name, server_name)

else:
    def create_rag_mcp_server(*args, **kwargs):
        """MCP Server creation not available - MCP library not installed."""
        raise ImportError(
            "MCP library not found. Install with: pip install 'mcp[cli]>=1.2.0'"
        )
    
    def create_mock_rag_mcp_server(*args, **kwargs):
        """MCP Server creation not available - MCP library not installed."""
        raise ImportError(
            "MCP library not found. Install with: pip install 'mcp[cli]>=1.2.0'"
        )


# Re-export main functions for compatibility
__all__ = [
    "create_container",
    "create_vector_client", 
    "create_rag_api",
    "create_test_vector_client",
    "create_prod_vector_client",
    "create_test_rag_api", 
    "create_prod_rag_api",
    "create_milvus_client",
    "create_embedding_service",
    "create_document_processor",
    "create_rag_mcp_server",
    "create_mock_rag_mcp_server"
]