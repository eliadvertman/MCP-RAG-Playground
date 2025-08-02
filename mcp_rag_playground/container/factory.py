"""
Convenience factory methods for creating configured services.
"""

from typing import Optional
from .container import Container
from .providers import (
    MilvusConfigProvider, 
    EmbeddingConfigProvider, 
    DocumentProcessorConfigProvider,
    VectorClientConfigProvider,
    RagAPIConfigProvider,
    MCPServerConfigProvider
)
from ..vectordb.milvus.milvus_client import MilvusVectorDB
from ..vectordb.embedding_service import SentenceTransformerEmbedding, MockEmbeddingService
from ..vectordb.processor.document_processor import DocumentProcessor
from ..vectordb.vector_client import VectorClient
from mcp_rag_playground.rag.rag_api import RagAPI

# Conditional import for MCP server (requires mcp library)
try:
    from ..mcp.rag_server import RagMCPServer
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    RagMCPServer = None


def create_container(environment: str = "default", debug: bool = True) -> Container:
    """
    Create and configure a dependency injection container.
    
    Args:
        environment: Environment name (test, dev, prod, default)
        debug: Enable debug logging (disable for MCP to avoid JSON interference)
        
    Returns:
        Configured Container instance
    """
    container = Container(environment, debug=debug)
    
    # Register configuration providers
    container.register_config_provider(MilvusConfigProvider())
    container.register_config_provider(EmbeddingConfigProvider())
    container.register_config_provider(DocumentProcessorConfigProvider())
    container.register_config_provider(VectorClientConfigProvider())
    container.register_config_provider(RagAPIConfigProvider())
    container.register_config_provider(MCPServerConfigProvider())
    
    # Register vector database service
    container.register_singleton("vector_db", lambda: MilvusVectorDB(
        container.get_config("milvus")
    ))
    
    # Register embedding service based on environment config
    def create_embedding_service():
        config = container.get_config("embedding")
        if config["provider"] == "mock":
            return MockEmbeddingService(dimension=config["dimension"])
        else:
            return SentenceTransformerEmbedding(model_name=config["model_name"])
    
    container.register_singleton("embedding_service", create_embedding_service)
    
    # Register document processor service
    def create_document_processor():
        config = container.get_config("document_processor")
        return DocumentProcessor(
            chunk_size=config["chunk_size"],
            overlap=config["overlap"]
        )
    
    container.register_singleton("document_processor", create_document_processor)
    
    # Register vector client service
    def create_vector_client_service():
        client_config = container.get_config("vector_client")
        return VectorClient(
            vector_db=container.get("vector_db"),
            embedding_service=container.get("embedding_service"),
            document_processor=container.get("document_processor"),
            collection_name=client_config["default_collection"]
        )
    
    container.register_singleton("vector_client", create_vector_client_service)
    
    # Register RAG API service
    def create_rag_api_service():
        rag_config = container.get_config("rag_api")
        return RagAPI(
            vector_client=container.get("vector_client"),
            collection_name=rag_config["default_collection"]
        )
    
    container.register_singleton("rag_api", create_rag_api_service)
    
    # Register MCP Server service (only if MCP library is available)
    if _MCP_AVAILABLE:
        def create_mcp_server_service():
            mcp_config = container.get_config("mcp_server")
            return RagMCPServer(
                rag_api=container.get("rag_api"),
                server_name=mcp_config["server_name"]
            )
        
        container.register_singleton("mcp_server", create_mcp_server_service)
    
    return container


def create_vector_client(environment: str = "default", 
                        collection_name: Optional[str] = None) -> VectorClient:
    """
    Create a configured VectorClient instance.
    
    Args:
        environment: Environment name (test, dev, prod, default)
        collection_name: Optional collection name override
        
    Returns:
        Configured VectorClient instance
    """
    container = create_container(environment, debug=False)
    
    if collection_name:
        # Create a custom client with overridden collection name
        return VectorClient(
            vector_db=container.get("vector_db"),
            embedding_service=container.get("embedding_service"),
            document_processor=container.get("document_processor"),
            collection_name=collection_name
        )
    else:
        # Use the default registered client
        return container.get("vector_client")


def create_test_container() -> Container:
    """Create a container configured for testing."""
    return create_container("test")


def create_dev_container() -> Container:
    """Create a container configured for development."""
    return create_container("dev")


def create_prod_container() -> Container:
    """Create a container configured for production."""
    return create_container("prod")


def create_rag_mcp_server(
    environment: str = "dev", 
    collection_name: Optional[str] = None,
    server_name: Optional[str] = None
):
    """
    Create a RAG MCP Server with the specified environment configuration.
    
    Args:
        environment: Environment configuration ("test", "dev", "prod")
        collection_name: Optional collection name override
        server_name: Optional server name override
        
    Returns:
        Configured RagMCPServer instance
        
    Raises:
        ImportError: If MCP library is not installed
    """
    if not _MCP_AVAILABLE:
        raise ImportError(
            "MCP library not found. Install with: pip install 'mcp[cli]>=1.2.0'"
        )
    
    container = create_container(environment, debug=False)
    
    if collection_name or server_name:
        # Create custom MCP server with overrides
        mcp_config = container.get_config("mcp_server")
        
        # Create RAG API with custom collection name if provided
        if collection_name:
            vector_client = container.get("vector_client")
            # Override the collection name in vector client
            vector_client.collection_name = collection_name
            
            rag_api = RagAPI(
                vector_client=vector_client,
                collection_name=collection_name
            )
        else:
            rag_api = container.get("rag_api")
        
        # Create MCP server with custom server name if provided
        final_server_name = server_name or mcp_config["server_name"]
        return RagMCPServer(rag_api=rag_api, server_name=final_server_name)
    else:
        # Use the default registered service
        return container.get("mcp_server")


def create_mock_rag_mcp_server(
    collection_name: str = "mock_mcp_rag_collection",
    server_name: str = "Mock RAG Knowledge Base"
):
    """
    Create a mock RAG MCP Server for testing and development.
    
    Args:
        collection_name: Name for the RAG collection
        server_name: Name for the MCP server
        
    Returns:
        Configured RagMCPServer instance with mock services
        
    Raises:
        ImportError: If MCP library is not installed
    """
    return create_rag_mcp_server("test", collection_name, server_name)


def create_mock_vector_client(collection_name: str = "test_collection") -> VectorClient:
    """
    Create a VectorClient with mock services for testing.
    
    Args:
        collection_name: Collection name for the client
        
    Returns:
        VectorClient with mock embedding service
    """
    return create_vector_client("dev", collection_name)


# Convenience functions for specific services
def create_rag_api(environment: str = "default", 
                   collection_name: Optional[str] = None) -> RagAPI:
    """
    Create a configured RagAPI instance.
    
    Args:
        environment: Environment name (test, dev, prod, default)
        collection_name: Optional custom collection name
        
    Returns:
        Configured RagAPI instance
    """
    container = create_container(environment, debug=False)
    rag_api = container.get("rag_api")
    
    # Override collection name if provided
    if collection_name:
        rag_api.collection_name = collection_name
        rag_api.vector_client.collection_name = collection_name
    
    return rag_api


def create_mock_rag_api(collection_name: str = "test_rag_collection") -> RagAPI:
    """
    Create a RagAPI with mock services for testing.
    
    Args:
        collection_name: Collection name for the RAG API
        
    Returns:
        RagAPI with mock embedding service
    """
    return create_rag_api("test", collection_name)


def create_milvus_client(environment: str = "default") -> MilvusVectorDB:
    """Create a configured MilvusVectorDB instance."""
    container = create_container(environment, debug=False)
    return container.get("vector_db")


def create_embedding_service(environment: str = "default") -> SentenceTransformerEmbedding:
    """Create a configured embedding service."""
    container = create_container(environment, debug=False)
    return container.get("embedding_service")


def create_document_processor(environment: str = "default") -> DocumentProcessor:
    """Create a configured document processor."""
    container = create_container(environment, debug=False)
    return container.get("document_processor")