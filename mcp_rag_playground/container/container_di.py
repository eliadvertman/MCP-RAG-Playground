"""
New dependency injection container using dependency-injector library.
"""

from dependency_injector import containers, providers
from dependency_injector.providers import Configuration

from ..vectordb.milvus.milvus_client import MilvusVectorDB
from ..vectordb.embedding_service import SentenceTransformerEmbedding, MockEmbeddingService
from ..vectordb.processor.document_processor import DocumentProcessor
from ..vectordb.vector_client import VectorClient
from ..rag.rag_api import RagAPI
from ..config.milvus_config import MilvusConfig


class Container(containers.DeclarativeContainer):
    """Main dependency injection container using dependency-injector."""
    
    # Configuration
    config = providers.Configuration()
    
    # Milvus configuration
    milvus_config = providers.Singleton(
        MilvusConfig.from_env
    )
    
    # Vector database
    vector_db = providers.Singleton(
        MilvusVectorDB,
        config=milvus_config
    )
    
    # Embedding service - conditional based on environment
    embedding_service = providers.Singleton(
        SentenceTransformerEmbedding,
        model_name="all-MiniLM-L6-v2"
    )
    
    # Mock embedding service for testing
    mock_embedding_service = providers.Singleton(
        MockEmbeddingService,
        dimension=384
    )
    
    # Document processor
    document_processor = providers.Singleton(
        DocumentProcessor,
        chunk_size=800,
        overlap=200
    )
    
    # Vector client
    vector_client = providers.Singleton(
        VectorClient,
        vector_db=vector_db,
        embedding_service=embedding_service,
        document_processor=document_processor,
        collection_name=config.collection_name
    )
    
    # Vector client for testing (with mock embedding)
    test_vector_client = providers.Singleton(
        VectorClient,
        vector_db=vector_db,
        embedding_service=mock_embedding_service,
        document_processor=document_processor,
        collection_name=config.collection_name
    )
    
    # RAG API
    rag_api = providers.Singleton(
        RagAPI,
        vector_client=vector_client,
        collection_name=config.collection_name
    )
    
    # RAG API for testing
    test_rag_api = providers.Singleton(
        RagAPI,
        vector_client=test_vector_client,
        collection_name=config.collection_name
    )


def create_container(environment: str = "prod") -> Container:
    """
    Create and configure a dependency injection container.
    
    Args:
        environment: Either "prod" or "test"
        
    Returns:
        Configured Container instance
    """
    container = Container()
    
    # Configure collection name based on environment
    if environment == "test":
        container.config.collection_name.from_value("test_collection")
    else:  # prod
        container.config.collection_name.from_value("prod_collection")
    
    return container


def create_vector_client(environment: str = "prod", collection_name: str = None) -> VectorClient:
    """
    Create a configured VectorClient instance.
    
    Args:
        environment: Either "prod" or "test"
        collection_name: Optional collection name override
        
    Returns:
        Configured VectorClient instance
    """
    container = create_container(environment)
    
    if collection_name:
        container.config.collection_name.from_value(collection_name)
    
    if environment == "test":
        return container.test_vector_client()
    else:
        return container.vector_client()


def create_rag_api(environment: str = "prod", collection_name: str = None) -> RagAPI:
    """
    Create a configured RagAPI instance.
    
    Args:
        environment: Either "prod" or "test"  
        collection_name: Optional collection name override
        
    Returns:
        Configured RagAPI instance
    """
    container = create_container(environment)
    
    if collection_name:
        container.config.collection_name.from_value(collection_name)
    
    if environment == "test":
        return container.test_rag_api()
    else:
        return container.rag_api()


# Convenience functions
def create_test_vector_client(collection_name: str = "test_collection") -> VectorClient:
    """Create a VectorClient with mock services for testing."""
    return create_vector_client("test", collection_name)


def create_prod_vector_client(collection_name: str = "prod_collection") -> VectorClient:
    """Create a VectorClient for production."""
    return create_vector_client("prod", collection_name)


def create_test_rag_api(collection_name: str = "test_collection") -> RagAPI:
    """Create a RagAPI with mock services for testing."""
    return create_rag_api("test", collection_name)


def create_prod_rag_api(collection_name: str = "prod_collection") -> RagAPI:
    """Create a RagAPI for production."""
    return create_rag_api("prod", collection_name)