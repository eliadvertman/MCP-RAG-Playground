"""
Dependency injection container using dependency-injector library.
Defaults to production configuration.
"""

from dependency_injector import containers, providers
from typing import Optional

from ..vectordb.milvus.milvus_client import MilvusVectorDB
from ..vectordb.embedding_service import SentenceTransformerEmbedding, MockEmbeddingService
from ..vectordb.processor.document_processor import DocumentProcessor
from ..vectordb.vector_client import VectorClient
from ..rag.rag_api import RagAPI
from ..config.milvus_config import MilvusConfig


class Container(containers.DeclarativeContainer):
    """Production-focused dependency injection container."""
    
    # Milvus configuration
    milvus_config = providers.Singleton(
        MilvusConfig.from_env
    )
    
    # Vector database
    vector_db = providers.Singleton(
        MilvusVectorDB,
        config=milvus_config
    )
    
    # Production embedding service
    embedding_service = providers.Singleton(
        SentenceTransformerEmbedding,
        model_name="all-MiniLM-L6-v2"
    )
    
    # Document processor
    document_processor = providers.Singleton(
        DocumentProcessor,
        chunk_size=800,
        overlap=200
    )
    
    # Production vector client
    vector_client = providers.Singleton(
        VectorClient,
        vector_db=vector_db,
        embedding_service=embedding_service,
        document_processor=document_processor,
        collection_name=providers.Callable(lambda: "prod_kb_collection")
    )
    
    # Production RAG API
    rag_api = providers.Singleton(
        RagAPI,
        vector_client=vector_client,
        collection_name=providers.Callable(lambda: "prod_collection")
    )


# Default container instance
_container = Container()


def create_vector_client(collection_name: Optional[str] = None) -> VectorClient:
    """
    Create a configured VectorClient instance for production.
    
    Args:
        collection_name: Optional collection name override
        
    Returns:
        Configured VectorClient instance
    """
    if collection_name:
        # Create custom vector client with overridden collection name
        return VectorClient(
            vector_db=_container.vector_db(),
            embedding_service=_container.embedding_service(),
            document_processor=_container.document_processor(),
            collection_name=collection_name
        )
    else:
        return _container.vector_client()


def create_rag_api(collection_name: Optional[str] = None) -> RagAPI:
    """
    Create a configured RagAPI instance for production.
    
    Args:
        collection_name: Optional collection name override
        
    Returns:
        Configured RagAPI instance
    """
    if collection_name:
        # Create custom vector client first
        vector_client = create_vector_client(collection_name)
        return RagAPI(
            vector_client=vector_client,
            collection_name=collection_name
        )
    else:
        return _container.rag_api()



def create_prod_vector_client(collection_name: str = "prod_collection") -> VectorClient:
    """Create a VectorClient for production."""
    return create_vector_client(collection_name)


def create_prod_rag_api(collection_name: str = "prod_collection") -> RagAPI:
    """Create a RagAPI for production."""
    return create_rag_api(collection_name)