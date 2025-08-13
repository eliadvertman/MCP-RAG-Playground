"""
Abstract interface for vector database operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Document:
    """Represents a document with content and metadata."""
    
    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None
    
    # Enhanced metadata fields for tracking
    filename: Optional[str] = None
    file_type: Optional[str] = None
    ingestion_timestamp: Optional[datetime] = None
    chunk_count: Optional[int] = None
    file_size: Optional[int] = None
    chunk_position: Optional[int] = None
    vector_id: Optional[str] = None
    embedding_status: str = "pending"
    
    def __post_init__(self):
        """Validate and normalize metadata fields after initialization."""
        # Validate embedding status
        valid_statuses = ["pending", "completed", "failed"]
        if self.embedding_status not in valid_statuses:
            raise ValueError(f"embedding_status must be one of {valid_statuses}")
        
        # Normalize file_type to include leading dot
        if self.file_type and not self.file_type.startswith('.'):
            self.file_type = '.' + self.file_type
        
        # Validate numeric fields
        if self.chunk_count is not None and self.chunk_count < 0:
            raise ValueError("chunk_count must be non-negative")
        
        if self.file_size is not None and self.file_size < 0:
            raise ValueError("file_size must be non-negative")
        
        if self.chunk_position is not None and self.chunk_position < 0:
            raise ValueError("chunk_position must be non-negative")


@dataclass
class SearchResult:
    """Represents a search result from vector database."""
    
    document: Document
    score: float
    distance: float


class VectorDBInterface(ABC):
    """Abstract interface for vector database operations."""
    
    @abstractmethod
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection in the vector database."""
        pass
    
    @abstractmethod
    def insert_documents(self, collection_name: str, documents: List[Document], 
                        embeddings: List[List[float]]) -> bool:
        """Insert documents with their embeddings into the collection."""
        pass
    
    @abstractmethod
    def search(self, collection_name: str, query_embedding: List[float], 
               limit: int = 10) -> List[SearchResult]:
        """Search for similar documents using vector similarity."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the vector database."""
        pass
    
    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass
    
    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test the connection to the vector database."""
        pass
    
    @abstractmethod
    def remove_documents(self, collection_name: str, document_ids: List[str]) -> bool:
        """Remove documents from the collection by their IDs."""
        pass
    
    @abstractmethod
    def get_document_by_id(self, collection_name: str, document_id: str) -> Optional[Document]:
        """Retrieve a specific document by its ID."""
        pass