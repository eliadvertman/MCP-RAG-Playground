"""
Dependency injection container using dependency-injector library.
Defaults to production configuration.
"""

from dependency_injector import containers, providers
from typing import Optional

from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
from mcp_rag_playground.vectordb.embedding_service import SentenceTransformerEmbedding
from mcp_rag_playground.vectordb.processor.document_processor import DocumentProcessor
from mcp_rag_playground.vectordb.vector_client import VectorClient
from mcp_rag_playground.rag.rag_api import RagAPI
from mcp_rag_playground.config.milvus_config import MilvusConfig


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
