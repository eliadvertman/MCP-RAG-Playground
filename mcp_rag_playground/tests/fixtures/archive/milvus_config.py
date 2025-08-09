"""
Configuration classes for Milvus client test fixtures.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from mcp_rag_playground.vectordb.vector_db_interface import Document


@dataclass
class MilvusConnectionConfig:
    """Configuration for Milvus connection settings."""
    host: str = "localhost"
    port: int = 19530
    timeout: float = 30.0
    
    # Collection settings
    index_type: str = "IVF_FLAT"
    metric_type: str = "COSINE"
    nlist: int = 128
    
    # Test database settings
    test_prefix: str = "test_"
    cleanup_timeout: float = 10.0


@dataclass
class DocumentFixture:
    """A single document fixture for testing."""
    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None
    
    def to_document(self) -> Document:
        """Convert to Document object."""
        return Document(
            content=self.content,
            metadata=self.metadata,
            id=self.id
        )


@dataclass
class MilvusDocumentFixtures:
    """Collection of document fixtures for Milvus testing."""
    
    # Basic document fixtures
    basic_documents: List[DocumentFixture] = field(default_factory=lambda: [
        DocumentFixture(
            content="Vector databases enable semantic search capabilities.",
            metadata={"source": "test1.txt", "type": "text", "category": "technology"}
        ),
        DocumentFixture(
            content="Machine learning models process data efficiently.", 
            metadata={"source": "test2.txt", "type": "text", "category": "ai"}
        ),
        DocumentFixture(
            content="Python programming language is versatile and powerful.",
            metadata={"source": "test3.py", "type": "code", "category": "programming"}
        )
    ])
    
    # Documents with explicit IDs
    id_documents: List[DocumentFixture] = field(default_factory=lambda: [
        DocumentFixture(
            id="doc_1",
            content="First document with explicit ID.",
            metadata={"source": "test", "doc_num": 1}
        ),
        DocumentFixture(
            id="doc_2",
            content="Second document with explicit ID.", 
            metadata={"source": "test", "doc_num": 2}
        )
    ])
    
    # Documents with complex metadata
    complex_metadata_documents: List[DocumentFixture] = field(default_factory=lambda: [
        DocumentFixture(
            content="Document with complex metadata structure.",
            metadata={
                "source": "test_file.txt",
                "author": "Test Author", 
                "tags": ["ai", "ml", "vector_db"],
                "score": 0.95,
                "nested": {
                    "category": "technical",
                    "subcategory": "database"
                },
                "created_at": "2024-01-01T00:00:00Z"
            }
        )
    ])
    
    def get_basic_documents(self) -> List[Document]:
        """Get basic document fixtures as Document objects."""
        return [doc.to_document() for doc in self.basic_documents]
    
    def get_documents_with_ids(self) -> List[Document]:
        """Get documents with explicit IDs."""
        return [doc.to_document() for doc in self.id_documents]
    
    def get_complex_metadata_documents(self) -> List[Document]:
        """Get documents with complex metadata."""
        return [doc.to_document() for doc in self.complex_metadata_documents]
    
    def create_large_document_set(self, count: int = 50) -> List[Document]:
        """Create a large set of documents for performance testing."""
        documents = []
        for i in range(count):
            doc = DocumentFixture(
                content=f"Test document number {i} with unique content about topic {i % 10}.",
                metadata={
                    "doc_id": i,
                    "batch": "large_test",
                    "topic": f"topic_{i % 10}",
                    "index": i
                }
            )
            documents.append(doc.to_document())
        return documents


@dataclass
class MilvusSearchConfig:
    """Configuration for search operations."""
    
    # Search parameters
    default_limit: int = 10
    test_limits: List[int] = field(default_factory=lambda: [1, 2, 5, 10, 20])
    
    # Search thresholds
    high_similarity_threshold: float = 0.8
    medium_similarity_threshold: float = 0.5
    low_similarity_threshold: float = 0.2
    
    # Query configurations
    test_queries: List[str] = field(default_factory=lambda: [
        "vector database search",
        "machine learning models",
        "python programming", 
        "artificial intelligence",
        "semantic search technology",
        "data processing efficiency"
    ])
    
    # Performance search configs
    search_timeout: float = 5.0
    large_result_limit: int = 100


@dataclass
class MilvusPerformanceConfig:
    """Configuration for performance testing."""
    
    # Operation timeouts (seconds)
    connection_timeout: float = 10.0
    collection_creation_timeout: float = 15.0
    insertion_timeout: float = 30.0
    search_timeout: float = 5.0
    deletion_timeout: float = 10.0
    
    # Batch operation configs
    small_batch_size: int = 10
    medium_batch_size: int = 50
    large_batch_size: int = 200
    
    # Performance thresholds
    max_insert_time_per_doc: float = 0.1  # seconds per document
    max_search_response_time: float = 2.0  # seconds
    max_collection_creation_time: float = 10.0  # seconds


@dataclass 
class MilvusTestConfig:
    """Main configuration class for Milvus client tests."""
    
    # Connection configuration
    connection: MilvusConnectionConfig = field(default_factory=MilvusConnectionConfig)
    
    # Document fixtures
    documents: MilvusDocumentFixtures = field(default_factory=MilvusDocumentFixtures)
    
    # Search configuration
    search: MilvusSearchConfig = field(default_factory=MilvusSearchConfig)
    
    # Performance configuration
    performance: MilvusPerformanceConfig = field(default_factory=MilvusPerformanceConfig)
    
    # Embedding configuration
    embedding_dimension: int = 384
    test_embedding_seed: int = 42  # For reproducible embeddings
    
    def create_test_embeddings(self, count: int) -> List[List[float]]:
        """Create reproducible test embeddings."""
        np.random.seed(self.test_embedding_seed)
        embeddings = []
        for _ in range(count):
            # Create normalized random embeddings
            embedding = np.random.rand(self.embedding_dimension).astype(float)
            embedding = embedding / np.linalg.norm(embedding)  # Normalize
            embeddings.append(embedding.tolist())
        return embeddings
    
    def get_test_collection_name(self, base_name: str = "test") -> str:
        """Generate a unique test collection name."""
        import time
        import uuid
        return f"{self.connection.test_prefix}{base_name}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    def get_milvus_config_dict(self, collection_name: str = None) -> Dict[str, Any]:
        """Get Milvus configuration as dictionary."""
        return {
            "host": self.connection.host,
            "port": self.connection.port, 
            "collection_name": collection_name or self.get_test_collection_name(),
            "index_type": self.connection.index_type,
            "metric_type": self.connection.metric_type
        }
    
    def create_sample_documents_with_embeddings(self, doc_type: str = "basic") -> tuple[List[Document], List[List[float]]]:
        """Create sample documents with corresponding embeddings."""
        if doc_type == "basic":
            documents = self.documents.get_basic_documents()
        elif doc_type == "ids":
            documents = self.documents.get_documents_with_ids()
        elif doc_type == "complex":
            documents = self.documents.get_complex_metadata_documents()
        else:
            documents = self.documents.get_basic_documents()
        
        embeddings = self.create_test_embeddings(len(documents))
        return documents, embeddings


# Default configuration instance
DEFAULT_MILVUS_CONFIG = MilvusTestConfig()