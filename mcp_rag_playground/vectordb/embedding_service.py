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