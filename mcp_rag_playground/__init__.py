"""
MCP RAG Playground - Vector database client with RAG capabilities.

This package provides a production-ready RAG (Retrieval-Augmented Generation) system
built on top of Milvus vector database with clean SOLID architecture patterns.

Core Components:
- VectorClient: Main client for vector database operations
- RagAPI: High-level RAG interface for document ingestion and search
- MilvusVectorDB: Milvus vector database implementation
- SentenceTransformerEmbedding: Text embedding service
- rag_server: FastMCP server module (conditional, based on MCP availability)

The package gracefully handles optional MCP dependencies - if MCP server components
are not available, core vector database functionality remains fully operational.
"""

from .vectordb.vector_client import VectorClient
from .vectordb.milvus.milvus_client import MilvusVectorDB
from .vectordb.embedding_service import SentenceTransformerEmbedding
from .config.milvus_config import MilvusConfig
from .vectordb.vector_db_interface import Document, SearchResult
from .rag.rag_api import RagAPI

# MCP Server imports (conditional)
# Gracefully handle missing MCP dependencies - core functionality remains available
try:
    from .mcp import rag_server
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    rag_server = None



# Build __all__ list dynamically based on what's available
__all__ = [
    # Core classes
    'VectorClient',
    'MilvusVectorDB', 
    'SentenceTransformerEmbedding',
    'Document',
    'SearchResult',
    'MilvusConfig',
    'RagAPI',
    

]

# Add MCP Server module if available
if _MCP_AVAILABLE:
    __all__.append('rag_server')