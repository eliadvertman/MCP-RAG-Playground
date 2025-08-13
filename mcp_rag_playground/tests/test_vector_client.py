"""
Test suite for VectorClient.
Uses mocks for VectorDBInterface and EmbeddingService to test VectorClient logic in isolation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List

from mcp_rag_playground.vectordb.vector_client import VectorClient
from mcp_rag_playground.vectordb.vector_db_interface import Document, SearchResult, VectorDBInterface
from mcp_rag_playground.vectordb.embedding_service import EmbeddingService
from mcp_rag_playground.vectordb.processor.document_processor import DocumentProcessor


class TestVectorClient:
    """Test suite for VectorClient using mocks for dependencies."""

    @pytest.fixture
    def vector_client(self, mock_vector_db, mock_embedding_service, mock_document_processor):
        """Create VectorClient with mocked dependencies."""
        return VectorClient(
            vector_db=mock_vector_db,
            embedding_service=mock_embedding_service,
            document_processor=mock_document_processor,
            collection_name="test_collection"
        )

    @pytest.mark.unit
    def test_initialization(self, mock_vector_db, mock_embedding_service, mock_document_processor):
        """Test VectorClient initialization."""
        client = VectorClient(
            vector_db=mock_vector_db,
            embedding_service=mock_embedding_service,
            document_processor=mock_document_processor,
            collection_name="my_collection"
        )
        
        assert client.vector_db is mock_vector_db
        assert client.embedding_service is mock_embedding_service
        assert client.document_processor is mock_document_processor
        assert client.collection_name == "my_collection"
        assert not client._initialized

    @pytest.mark.unit
    def test_ensure_collection_exists_new_collection(self, vector_client, mock_vector_db, mock_embedding_service):
        """Test collection creation when collection doesn't exist."""
        # Setup mocks
        mock_vector_db.collection_exists.return_value = False
        mock_vector_db.create_collection.return_value = True
        mock_embedding_service.get_dimension.return_value = 384
        
        # Call method
        vector_client._ensure_collection_exists()
        
        # Verify calls
        mock_embedding_service.get_dimension.assert_called_once()
        mock_vector_db.collection_exists.assert_called_once_with("test_collection")
        mock_vector_db.create_collection.assert_called_once_with("test_collection", 384)
        assert vector_client._initialized

    @pytest.mark.unit
    def test_ensure_collection_exists_existing_collection(self, vector_client, mock_vector_db, mock_embedding_service):
        """Test when collection already exists."""
        # Setup mocks
        mock_vector_db.collection_exists.return_value = True
        mock_embedding_service.get_dimension.return_value = 384
        
        # Call method
        vector_client._ensure_collection_exists()
        
        # Verify calls
        mock_embedding_service.get_dimension.assert_called_once()
        mock_vector_db.collection_exists.assert_called_once_with("test_collection")
        mock_vector_db.create_collection.assert_not_called()
        assert vector_client._initialized

    @pytest.mark.unit
    def test_ensure_collection_exists_creation_failure(self, vector_client, mock_vector_db, mock_embedding_service):
        """Test error handling when collection creation fails."""
        # Setup mocks
        mock_vector_db.collection_exists.return_value = False
        mock_vector_db.create_collection.return_value = False
        mock_embedding_service.get_dimension.return_value = 384
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to create collection: test_collection"):
            vector_client._ensure_collection_exists()

    @pytest.mark.unit
    def test_upload_success(self, vector_client, mock_vector_db, mock_embedding_service, mock_document_processor):
        """Test successful file upload."""
        # Setup mocks
        documents = [Document(content="Test content", metadata={"source": "test.txt"})]
        mock_document_processor.process_file.return_value = documents
        mock_embedding_service.embed_texts.return_value = [[0.1] * 384]
        mock_vector_db.collection_exists.return_value = True
        mock_vector_db.insert_documents.return_value = True
        
        # Call upload
        result = vector_client.upload("test.txt")
        
        # Verify result and calls
        assert result is True
        mock_document_processor.process_file.assert_called_once_with("test.txt")
        mock_embedding_service.embed_texts.assert_called_once_with(["Test content"])
        mock_vector_db.insert_documents.assert_called_once_with(
            "test_collection", documents, [[0.1] * 384]
        )

    @pytest.mark.unit
    def test_upload_no_documents(self, vector_client, mock_document_processor):
        """Test upload when no documents are extracted."""
        # Setup mocks
        mock_document_processor.process_file.return_value = []
        
        # Call upload
        result = vector_client.upload("empty_file.txt")
        
        # Verify result
        assert result is False
        mock_document_processor.process_file.assert_called_once_with("empty_file.txt")

    @pytest.mark.unit
    def test_upload_exception_handling(self, vector_client, mock_document_processor):
        """Test upload exception handling."""
        # Setup mock to raise exception
        mock_document_processor.process_file.side_effect = Exception("File processing error")
        
        # Call upload
        result = vector_client.upload("problematic_file.txt")
        
        # Verify result
        assert result is False

    @pytest.mark.unit
    def test_query_preprocessing(self, vector_client):
        """Test query text preprocessing."""
        from mcp_rag_playground.tests.fixtures.vector_client_fixtures import get_preprocessing_test_cases
        test_cases = get_preprocessing_test_cases()
        
        for input_text, expected in test_cases:
            result = vector_client._preprocess_query(input_text)
            assert expected in result.lower()

    @pytest.mark.unit
    def test_query_success(self, vector_client, mock_vector_db, mock_embedding_service):
        """Test successful query operation."""
        # Setup mocks
        mock_vector_db.collection_exists.return_value = True
        mock_embedding_service.embed_text.return_value = [0.1] * 384
        
        search_result = SearchResult(
            document=Document(content="Result content", metadata={"source": "test"}),
            score=0.95,
            distance=0.05
        )
        mock_vector_db.search.return_value = [search_result]
        
        # Call query
        results = vector_client.query("test query", limit=5, min_score=0.8)
        
        # Verify results
        assert len(results) == 1
        assert results[0].document.content == "Result content"
        assert results[0].score == 0.95
        
        # Verify calls
        mock_embedding_service.embed_text.assert_called_once()
        mock_vector_db.search.assert_called_once_with(
            "test_collection", [0.1] * 384, 5
        )

    @pytest.mark.unit
    def test_query_score_filtering(self, vector_client, mock_vector_db, mock_embedding_service):
        """Test query results are filtered by minimum score."""
        # Setup mocks
        mock_vector_db.collection_exists.return_value = True
        mock_embedding_service.embed_text.return_value = [0.1] * 384
        
        search_results = [
            SearchResult(
                document=Document(content="High score", metadata={"source": "test1"}),
                score=0.95,
                distance=0.05
            ),
            SearchResult(
                document=Document(content="Medium score", metadata={"source": "test2"}),
                score=0.75,
                distance=0.25
            ),
            SearchResult(
                document=Document(content="Low score", metadata={"source": "test3"}),
                score=0.45,
                distance=0.55
            )
        ]
        mock_vector_db.search.return_value = search_results
        
        # Call query with min_score filter
        results = vector_client.query("test query", min_score=0.8)
        
        # Should only return high score result
        assert len(results) == 1
        assert results[0].document.content == "High score"
        assert results[0].score == 0.95

    @pytest.mark.unit
    def test_query_empty_string(self, vector_client, mock_vector_db, mock_embedding_service):
        """Test query with empty or whitespace-only string."""
        # Setup mocks
        mock_vector_db.collection_exists.return_value = True
        mock_embedding_service.embed_text.return_value = [0.1] * 384
        mock_vector_db.search.return_value = []
        
        # Test empty string
        results = vector_client.query("", limit=5)
        assert len(results) == 0
        
        # Test whitespace only
        results = vector_client.query("   \n\t   ", limit=5)
        assert len(results) == 0

    @pytest.mark.unit
    def test_query_exception_handling(self, vector_client, mock_embedding_service):
        """Test query exception handling."""
        # Setup mock to raise exception
        mock_embedding_service.embed_text.side_effect = Exception("Embedding error")
        
        # Call query
        results = vector_client.query("test query")
        
        # Should return empty list on error
        assert results == []

    @pytest.mark.unit
    def test_get_collection_info(self, vector_client, mock_vector_db):
        """Test getting collection information."""
        # Setup mock
        expected_info = {
            "name": "test_collection",
            "num_entities": 100,
            "schema": {"fields": []}
        }
        mock_vector_db.collection_exists.return_value = True
        mock_vector_db.get_collection_info.return_value = expected_info
        
        # Call method
        info = vector_client.get_collection_info()
        
        # Verify result
        assert info == expected_info
        mock_vector_db.get_collection_info.assert_called_once_with("test_collection")

    @pytest.mark.unit
    def test_get_collection_info_exception(self, vector_client, mock_vector_db):
        """Test get_collection_info exception handling."""
        # Setup mock to raise exception
        mock_vector_db.get_collection_info.side_effect = Exception("Database error")
        
        # Call method
        info = vector_client.get_collection_info()
        
        # Should return empty dict on error
        assert info == {}

    @pytest.mark.unit
    def test_delete_collection_success(self, vector_client, mock_vector_db):
        """Test successful collection deletion."""
        # Setup mock
        mock_vector_db.delete_collection.return_value = True
        
        # Call method
        result = vector_client.delete_collection()
        
        # Verify result
        assert result is True
        assert not vector_client._initialized
        mock_vector_db.delete_collection.assert_called_once_with("test_collection")

    @pytest.mark.unit
    def test_delete_collection_failure(self, vector_client, mock_vector_db):
        """Test collection deletion failure."""
        # Setup mock
        mock_vector_db.delete_collection.return_value = False
        
        # Call method
        result = vector_client.delete_collection()
        
        # Verify result
        assert result is False
        # _initialized should remain unchanged on failure

    @pytest.mark.unit
    def test_delete_collection_exception(self, vector_client, mock_vector_db):
        """Test delete_collection exception handling."""
        # Setup mock to raise exception
        mock_vector_db.delete_collection.side_effect = Exception("Database error")
        
        # Call method
        result = vector_client.delete_collection()
        
        # Should return False on error
        assert result is False

    @pytest.mark.unit
    def test_test_connection(self, vector_client, mock_vector_db):
        """Test connection testing."""
        # Test successful connection
        mock_vector_db.test_connection.return_value = True
        result = vector_client.test_connection()
        assert result is True
        
        # Test failed connection
        mock_vector_db.test_connection.return_value = False
        result = vector_client.test_connection()
        assert result is False

    @pytest.mark.unit
    def test_test_connection_exception(self, vector_client, mock_vector_db):
        """Test test_connection exception handling."""
        # Setup mock to raise exception
        mock_vector_db.test_connection.side_effect = Exception("Connection error")
        
        # Call method
        result = vector_client.test_connection()
        
        # Should return False on error
        assert result is False

    @pytest.mark.unit
    def test_collection_initialization_called_once(self, vector_client, mock_vector_db, mock_embedding_service):
        """Test that collection initialization is only called once."""
        # Setup mocks
        mock_vector_db.collection_exists.return_value = True
        mock_embedding_service.get_dimension.return_value = 384
        
        # Call multiple methods that trigger initialization
        vector_client.get_collection_info()
        vector_client.query("test", limit=1)
        vector_client.get_collection_info()
        
        # Verify initialization was called only once
        assert mock_embedding_service.get_dimension.call_count == 1
        assert mock_vector_db.collection_exists.call_count == 1

    @pytest.mark.unit
    def test_query_text_preprocessing_expansions(self, vector_client):
        """Test specific text preprocessing expansions."""
        # Test abbreviation expansions
        result = vector_client._preprocess_query("using db for ai ml")
        
        # Should contain both original and expanded terms
        assert "db" in result
        assert "database" in result
        assert "ai" in result
        assert "artificial intelligence" in result
        assert "ml" in result
        assert "machine learning" in result

    @pytest.mark.unit
    def test_upload_with_multiple_documents(self, vector_client, mock_vector_db, mock_embedding_service, mock_document_processor):
        """Test upload with multiple documents from file."""
        # Setup mocks
        documents = [
            Document(content="First document", metadata={"source": "test.txt", "chunk": 1}),
            Document(content="Second document", metadata={"source": "test.txt", "chunk": 2})
        ]
        mock_document_processor.process_file.return_value = documents
        mock_embedding_service.embed_texts.return_value = [[0.1] * 384, [0.2] * 384]
        mock_vector_db.collection_exists.return_value = True
        mock_vector_db.insert_documents.return_value = True
        
        # Call upload
        result = vector_client.upload("test.txt")
        
        # Verify result and calls
        assert result is True
        mock_embedding_service.embed_texts.assert_called_once_with(
            ["First document", "Second document"]
        )
        mock_vector_db.insert_documents.assert_called_once_with(
            "test_collection", documents, [[0.1] * 384, [0.2] * 384]
        )

    @pytest.mark.unit
    def test_remove_document_success(self, vector_client, mock_vector_db):
        """Test successful document removal."""
        # Setup mock
        mock_vector_db.collection_exists.return_value = True
        mock_vector_db.remove_documents.return_value = True
        
        # Call method
        result = vector_client.remove_document("test_doc_id")
        
        # Verify result and calls
        assert result is True
        mock_vector_db.remove_documents.assert_called_once_with("test_collection", ["test_doc_id"])

    @pytest.mark.unit
    def test_remove_document_empty_id(self, vector_client, mock_vector_db):
        """Test remove document with empty ID."""
        # Setup mock
        mock_vector_db.collection_exists.return_value = True
        
        # Call method with empty ID
        result = vector_client.remove_document("")
        
        # Should return False and not call vector DB
        assert result is False
        mock_vector_db.remove_documents.assert_not_called()
        
        # Test with None ID
        result = vector_client.remove_document(None)
        assert result is False

    @pytest.mark.unit
    def test_remove_document_exception_handling(self, vector_client, mock_vector_db):
        """Test remove document exception handling."""
        # Setup mock to raise exception
        mock_vector_db.collection_exists.return_value = True
        mock_vector_db.remove_documents.side_effect = Exception("Database error")
        
        # Call method
        result = vector_client.remove_document("test_doc_id")
        
        # Should return False on error
        assert result is False

    @pytest.mark.unit
    def test_get_document_by_id_success(self, vector_client, mock_vector_db):
        """Test successful document retrieval by ID."""
        # Setup mock
        expected_document = Document(
            content="Test content",
            metadata={"source": "test.txt"},
            id="test_doc_id"
        )
        mock_vector_db.collection_exists.return_value = True
        mock_vector_db.get_document_by_id.return_value = expected_document
        
        # Call method
        result = vector_client.get_document_by_id("test_doc_id")
        
        # Verify result and calls
        assert result == expected_document
        mock_vector_db.get_document_by_id.assert_called_once_with("test_collection", "test_doc_id")

    @pytest.mark.unit
    def test_get_document_by_id_not_found(self, vector_client, mock_vector_db):
        """Test get document by ID when document not found."""
        # Setup mock
        mock_vector_db.collection_exists.return_value = True
        mock_vector_db.get_document_by_id.return_value = None
        
        # Call method
        result = vector_client.get_document_by_id("nonexistent_doc_id")
        
        # Should return None
        assert result is None
        mock_vector_db.get_document_by_id.assert_called_once_with("test_collection", "nonexistent_doc_id")

    @pytest.mark.unit
    def test_get_document_by_id_empty_id(self, vector_client, mock_vector_db):
        """Test get document by ID with empty ID."""
        # Setup mock
        mock_vector_db.collection_exists.return_value = True
        
        # Call method with empty ID
        result = vector_client.get_document_by_id("")
        
        # Should return None and not call vector DB
        assert result is None
        mock_vector_db.get_document_by_id.assert_not_called()
        
        # Test with None ID
        result = vector_client.get_document_by_id(None)
        assert result is None

    @pytest.mark.unit
    def test_get_document_by_id_exception_handling(self, vector_client, mock_vector_db):
        """Test get document by ID exception handling."""
        # Setup mock to raise exception
        mock_vector_db.collection_exists.return_value = True
        mock_vector_db.get_document_by_id.side_effect = Exception("Database error")
        
        # Call method
        result = vector_client.get_document_by_id("test_doc_id")
        
        # Should return None on error
        assert result is None