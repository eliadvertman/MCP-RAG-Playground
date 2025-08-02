"""
Convenience factory methods for creating configured services.
"""

from typing import Optional
from .container import Container
from .providers import (
    MilvusConfigProvider, 
    EmbeddingConfigProvider, 
    DocumentProcessorConfigProvider,
    VectorClientConfigProvider
)
from ..vectordb.milvus.milvus_client import MilvusVectorDB
from ..vectordb.embedding_service import SentenceTransformerEmbedding, MockEmbeddingService
from ..vectordb.processor.document_processor import DocumentProcessor
from ..vectordb.vector_client import VectorClient


def create_container(environment: str = "default") -> Container:
    """
    Create and configure a dependency injection container.
    
    Args:
        environment: Environment name (test, dev, prod, default)
        
    Returns:
        Configured Container instance
    """
    container = Container(environment)
    
    # Register configuration providers
    container.register_config_provider(MilvusConfigProvider())
    container.register_config_provider(EmbeddingConfigProvider())
    container.register_config_provider(DocumentProcessorConfigProvider())
    container.register_config_provider(VectorClientConfigProvider())
    
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
    container = create_container(environment)
    
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


def create_mock_vector_client(collection_name: str = "test_collection") -> VectorClient:
    """
    Create a VectorClient with mock services for testing.
    
    Args:
        collection_name: Collection name for the client
        
    Returns:
        VectorClient with mock embedding service
    """
    return create_vector_client("test", collection_name)


# Convenience functions for specific services
def create_milvus_client(environment: str = "default") -> MilvusVectorDB:
    """Create a configured MilvusVectorDB instance."""
    container = create_container(environment)
    return container.get("vector_db")


def create_embedding_service(environment: str = "default") -> SentenceTransformerEmbedding:
    """Create a configured embedding service."""
    container = create_container(environment)
    return container.get("embedding_service")


def create_document_processor(environment: str = "default") -> DocumentProcessor:
    """Create a configured document processor."""
    container = create_container(environment)
    return container.get("document_processor")