"""
Embedding service abstraction for generating text embeddings.
"""

from abc import ABC, abstractmethod
from typing import List, Union


class EmbeddingService(ABC):
    """Abstract interface for embedding services."""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        pass


class SentenceTransformerEmbedding(EmbeddingService):
    """Sentence Transformer implementation of embedding service."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = None
    
    def _load_model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError("sentence-transformers is required. Install it with: pip install sentence-transformers")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        self._load_model()
        embedding = self._model.encode(text)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        self._load_model()
        embeddings = self._model.encode(texts)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        self._load_model()
        return self._dimension


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service for testing purposes."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    def embed_text(self, text: str) -> List[float]:
        """Generate a mock embedding based on text hash."""
        import hashlib
        
        hash_object = hashlib.md5(text.encode())
        hash_hex = hash_object.hexdigest()
        
        embedding = []
        for i in range(0, len(hash_hex), 8):
            chunk = hash_hex[i:i+8]
            value = int(chunk, 16) / (16**8)
            embedding.append(value)
        
        while len(embedding) < self.dimension:
            embedding.extend(embedding[:min(len(embedding), self.dimension - len(embedding))])
        
        return embedding[:self.dimension]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for multiple texts."""
        return [self.embed_text(text) for text in texts]
    
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self.dimension


class MockVectorDB:
    """Mock vector database implementation for testing."""
    
    def __init__(self):
        self._collections: Dict[str, List[Dict]] = {}
        self._connected = True
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a mock collection."""
        self._collections[collection_name] = []
        return True
    
    def insert_documents(self, collection_name: str, documents: List, embeddings: List[List[float]]) -> bool:
        """Insert mock documents."""
        if collection_name not in self._collections:
            return False
        
        for doc, embedding in zip(documents, embeddings):
            self._collections[collection_name].append({
                'document': doc,
                'embedding': embedding
            })
        return True
    
    def search(self, collection_name: str, query_embedding: List[float], limit: int = 10) -> List:
        """Mock search returning empty results."""
        from .vector_db_interface import SearchResult, Document
        return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete mock collection."""
        if collection_name in self._collections:
            del self._collections[collection_name]
        return True
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if mock collection exists."""
        return collection_name in self._collections
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get mock collection info."""
        if collection_name not in self._collections:
            return {}
        return {
            "name": collection_name,
            "num_entities": len(self._collections[collection_name]),
            "description": "Mock collection"
        }
    
    def test_connection(self) -> bool:
        """Test mock connection - always returns True."""
        return True