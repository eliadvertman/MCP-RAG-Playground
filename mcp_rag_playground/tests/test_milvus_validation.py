"""
Tests for MilvusVectorDB parameter validation and error handling.
"""
import pytest
from unittest.mock import Mock

from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
from mcp_rag_playground.vectordb.vector_db_interface import Document


class TestMilvusVectorDBValidation:
    """Test parameter validation and error handling in MilvusVectorDB."""
    
    @pytest.fixture
    def mock_milvus_db(self):
        """Create a mock MilvusVectorDB instance."""
        db = MilvusVectorDB()
        db._connected = True
        return db
    
    def test_create_collection_invalid_name(self, mock_milvus_db):
        """Test create_collection with invalid collection names."""
        # Empty string
        result = mock_milvus_db.create_collection("", 128)
        assert result is False
        
        # None
        result = mock_milvus_db.create_collection(None, 128)
        assert result is False
        
        # Non-string type
        result = mock_milvus_db.create_collection(123, 128)
        assert result is False
    
    def test_create_collection_invalid_dimension(self, mock_milvus_db):
        """Test create_collection with invalid dimensions."""
        # Zero dimension
        result = mock_milvus_db.create_collection("test", 0)
        assert result is False
        
        # Negative dimension
        result = mock_milvus_db.create_collection("test", -1)
        assert result is False
    
    def test_insert_documents_invalid_collection_name(self, mock_milvus_db):
        """Test insert_documents with invalid collection names."""
        docs = [Document("content", {})]
        embeddings = [[0.1, 0.2, 0.3]]
        
        # Empty string
        result = mock_milvus_db.insert_documents("", docs, embeddings)
        assert result is False
        
        # None
        result = mock_milvus_db.insert_documents(None, docs, embeddings)
        assert result is False
    
    def test_insert_documents_empty_documents_list(self, mock_milvus_db):
        """Test insert_documents with empty documents list."""
        # Empty documents should return True (no-op)
        result = mock_milvus_db.insert_documents("test", [], [])
        assert result is True
    
    def test_insert_documents_mismatched_lengths(self, mock_milvus_db):
        """Test insert_documents with mismatched document and embedding counts."""
        docs = [Document("content1", {}), Document("content2", {})]
        embeddings = [[0.1, 0.2, 0.3]]  # Only one embedding for two docs
        
        result = mock_milvus_db.insert_documents("test", docs, embeddings)
        assert result is False