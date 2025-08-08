"""
Abstract interface for vector database operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """Represents a document with content and metadata."""
    
    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None


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