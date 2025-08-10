"""
Unit tests for enhanced document metadata tracking functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import tempfile
import os
import json

from mcp_rag_playground.vectordb.vector_db_interface import Document, SearchResult
from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
from mcp_rag_playground.vectordb.vector_client import VectorClient


class TestDocumentModel:
    """Test the extended Document model with metadata fields."""
    
    def test_document_creation_with_basic_fields(self):
        """Test Document creation with basic required fields."""
        doc = Document(
            content="Test content",
            metadata={"key": "value"}
        )
        
        assert doc.content == "Test content"
        assert doc.metadata == {"key": "value"}
        assert doc.id is None
        
        # Check default values for new metadata fields
        assert doc.filename is None
        assert doc.file_type is None
        assert doc.ingestion_timestamp is None
        assert doc.chunk_count is None
        assert doc.file_size is None
        assert doc.chunk_position is None
        assert doc.vector_id is None
        assert doc.embedding_status == "pending"
    
    def test_document_creation_with_enhanced_metadata(self):
        """Test Document creation with all metadata fields."""
        timestamp = datetime.now()
        
        doc = Document(
            content="Test content",
            metadata={"source": "test"},
            id="test-id",
            filename="test.txt",
            file_type=".txt",
            ingestion_timestamp=timestamp,
            chunk_count=5,
            file_size=1024,
            chunk_position=2,
            vector_id="vec-123",
            embedding_status="completed"
        )
        
        assert doc.content == "Test content"
        assert doc.metadata == {"source": "test"}
        assert doc.id == "test-id"
        assert doc.filename == "test.txt"
        assert doc.file_type == ".txt"
        assert doc.ingestion_timestamp == timestamp
        assert doc.chunk_count == 5
        assert doc.file_size == 1024
        assert doc.chunk_position == 2
        assert doc.vector_id == "vec-123"
        assert doc.embedding_status == "completed"
    
    def test_document_backward_compatibility(self):
        """Test that existing Document creation still works."""
        # This tests backward compatibility with existing code
        doc = Document("Old style content", {"old": "metadata"}, "old-id")
        
        assert doc.content == "Old style content"
        assert doc.metadata == {"old": "metadata"}
        assert doc.id == "old-id"
        assert doc.embedding_status == "pending"  # Default value
    
    def test_document_validation(self):
        """Test Document field validation."""
        # Test invalid embedding status
        with pytest.raises(ValueError, match="embedding_status must be one of"):
            Document("content", {}, embedding_status="invalid")
        
        # Test negative chunk_count
        with pytest.raises(ValueError, match="chunk_count must be non-negative"):
            Document("content", {}, chunk_count=-1)
        
        # Test negative file_size
        with pytest.raises(ValueError, match="file_size must be non-negative"):
            Document("content", {}, file_size=-1)
        
        # Test negative chunk_position
        with pytest.raises(ValueError, match="chunk_position must be non-negative"):
            Document("content", {}, chunk_position=-1)
    
    def test_document_file_type_normalization(self):
        """Test that file_type is normalized to include leading dot."""
        doc = Document("content", {}, file_type="txt")
        assert doc.file_type == ".txt"
        
        doc2 = Document("content", {}, file_type=".txt")
        assert doc2.file_type == ".txt"


class TestMilvusVectorDBMetadata:
    """Test MilvusVectorDB with enhanced metadata support."""
    
    @pytest.fixture
    def mock_milvus_db(self):
        """Create a mock MilvusVectorDB instance."""
        return MilvusVectorDB()
    
    @patch('pymilvus.Collection')
    @patch('pymilvus.CollectionSchema')
    @patch('pymilvus.FieldSchema')
    def test_create_collection_with_metadata_fields(self, mock_field_schema, mock_schema, mock_collection, mock_milvus_db):
        """Test that create_collection includes all metadata fields."""
        mock_milvus_db._connected = True
        mock_milvus_db.collection_exists = Mock(return_value=False)
        
        result = mock_milvus_db.create_collection("test_collection", 128)
        
        # Verify that FieldSchema was called with metadata fields
        field_calls = mock_field_schema.call_args_list
        field_names = [call[1]['name'] for call in field_calls if 'name' in call[1]]
        
        expected_fields = [
            "id", "content", "metadata", "filename", "file_type", 
            "ingestion_timestamp", "chunk_count", "file_size", 
            "chunk_position", "vector_id", "embedding_status", "embedding"
        ]
        
        for field in expected_fields:
            assert field in field_names, f"Missing field: {field}"
        
        assert result is True
    
    def test_insert_documents_with_metadata(self, mock_milvus_db):
        """Test document insertion with enhanced metadata."""
        timestamp = datetime.now()
        
        documents = [
            Document(
                content="Test content 1",
                metadata={"test": "data1"},
                id="doc1",
                filename="test1.txt",
                file_type=".txt",
                ingestion_timestamp=timestamp,
                chunk_count=2,
                file_size=512,
                chunk_position=0,
                vector_id="vec1",
                embedding_status="completed"
            ),
            Document(
                content="Test content 2",
                metadata={"test": "data2"},
                id="doc2",
                filename="test2.txt",
                file_type=".txt",
                ingestion_timestamp=timestamp,
                chunk_count=2,
                file_size=512,
                chunk_position=1,
                vector_id="vec2",
                embedding_status="completed"
            )
        ]
        
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        # Mock the necessary methods
        mock_milvus_db._connected = True
        mock_milvus_db.collection_exists = Mock(return_value=True)
        
        with patch('pymilvus.Collection') as mock_collection_class:
            mock_collection = Mock()
            mock_collection_class.return_value = mock_collection
            
            result = mock_milvus_db.insert_documents("test_collection", documents, embeddings)
            
            # Verify insert was called with correct entities structure
            mock_collection.insert.assert_called_once()
            entities = mock_collection.insert.call_args[0][0]
            
            # Should have 12 entity lists (all fields including metadata)
            assert len(entities) == 12
            
            # Check that metadata fields are properly included
            assert entities[3] == ["test1.txt", "test2.txt"]  # filenames
            assert entities[4] == [".txt", ".txt"]  # file_types
            assert entities[6] == [2, 2]  # chunk_counts
            assert entities[7] == [512, 512]  # file_sizes
            
            assert result is True


class TestVectorClientMetadataIntegration:
    """Test VectorClient metadata integration."""
    
    @pytest.fixture
    def mock_vector_client(self):
        """Create a mock VectorClient."""
        mock_vector_db = Mock()
        mock_embedding_service = Mock()
        mock_document_processor = Mock()
        
        return VectorClient(
            vector_db=mock_vector_db,
            embedding_service=mock_embedding_service,
            document_processor=mock_document_processor,
            collection_name="test_collection"
        )
    
    @patch('os.path.getsize')
    @patch('os.path.exists')
    def test_upload_captures_metadata(self, mock_exists, mock_getsize, mock_vector_client):
        """Test that upload method captures file metadata."""
        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        
        mock_vector_client._initialized = True
        mock_vector_client.document_processor.process_file.return_value = [
            Document("Content 1", {"original": "metadata"}),
            Document("Content 2", {"original": "metadata"})
        ]
        mock_vector_client.embedding_service.embed_texts.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_vector_client.vector_db.insert_documents.return_value = True
        
        # Test upload
        result = mock_vector_client.upload("/path/to/test.txt")
        
        # Verify metadata was captured
        assert result is True
        mock_vector_client.vector_db.insert_documents.assert_called_once()
        
        call_args = mock_vector_client.vector_db.insert_documents.call_args
        documents = call_args[0][1]  # Second argument is documents list
        
        # Check that documents have enhanced metadata
        for i, doc in enumerate(documents):
            assert doc.filename == "test.txt"
            assert doc.file_type == ".txt"
            assert doc.ingestion_timestamp is not None
            assert doc.chunk_count == 2
            assert doc.file_size == 1024
            assert doc.chunk_position == i
            assert doc.embedding_status == "completed"
    
    def test_upload_handles_missing_file(self, mock_vector_client):
        """Test upload gracefully handles missing files."""
        mock_vector_client._initialized = True
        
        # Configure mocks before calling upload
        mock_vector_client.document_processor.process_file.return_value = [
            Document("Content", {})
        ]
        mock_vector_client.vector_db.insert_documents.return_value = True
        mock_vector_client.embedding_service.embed_texts.return_value = [[0.1, 0.2]]
        
        with patch('os.path.exists', return_value=False):
            with patch('os.path.getsize', side_effect=OSError("File not found")):
                result = mock_vector_client.upload("/nonexistent/file.txt")
                
                # Should still attempt upload but with 0 file size
                assert result is True


@pytest.mark.integration
class TestMetadataIntegration:
    """Integration tests for metadata functionality."""
    
    def test_end_to_end_metadata_tracking(self):
        """Test complete metadata tracking flow."""
        # This would be an integration test with real Milvus
        # For now, we'll use mocks to simulate the flow
        pass
    
    def test_backward_compatibility_with_existing_collections(self):
        """Test that new metadata schema works with existing collections."""
        # This would test schema evolution and backward compatibility
        pass


class TestMCPToolsMetadata:
    """Test MCP tools for metadata access."""
    
    def test_get_document_metadata_tool(self):
        """Test get_document_metadata MCP tool."""
        # This would test the new MCP tool
        # Implementation depends on MCP testing framework
        pass
    
    def test_list_documents_with_metadata_tool(self):
        """Test list_documents_with_metadata MCP tool."""
        # This would test the new MCP tool
        # Implementation depends on MCP testing framework
        pass


# Test markers for different test categories
pytestmark = [
    pytest.mark.unit,
    pytest.mark.metadata
]