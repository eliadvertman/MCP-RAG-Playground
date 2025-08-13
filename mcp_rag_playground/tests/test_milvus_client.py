"""
Test suite for Milvus vector database client.
Uses real Milvus database connection (no mocks) for integration testing.
"""

import time
import uuid

import pytest

from mcp_rag_playground.config.milvus_config import MilvusConfig
from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
from mcp_rag_playground.vectordb.vector_db_interface import Document, SearchResult


class TestMilvusVectorDB:
    """Test suite for MilvusVectorDB using real Milvus connection."""

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_connection_management(self, milvus_client_basic):
        """Test connection and disconnection operations."""
        # Test connection
        assert not milvus_client_basic._connected
        milvus_client_basic.connect()
        assert milvus_client_basic._connected
        
        # Test double connection (should not fail)
        milvus_client_basic.connect()
        assert milvus_client_basic._connected
        
        # Test disconnection
        milvus_client_basic.disconnect()
        assert not milvus_client_basic._connected
        
        # Test double disconnection (should not fail)
        milvus_client_basic.disconnect()
        assert not milvus_client_basic._connected


    @pytest.mark.milvus
    @pytest.mark.integration
    def test_collection_creation_and_existence(self, milvus_client_basic, test_collection_name):
        """Test collection creation and existence checking."""
        try:
            # Collection should not exist initially
            assert not milvus_client_basic.collection_exists(test_collection_name)
            
            # Create collection
            result = milvus_client_basic.create_collection(test_collection_name, dimension=384)
            assert result is True
            
            # Collection should now exist
            assert milvus_client_basic.collection_exists(test_collection_name)
            
            # Creating existing collection should return True (idempotent)
            result = milvus_client_basic.create_collection(test_collection_name, dimension=384)
            assert result is True
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_collection_deletion(self, milvus_client_basic, test_collection_name):
        """Test collection deletion."""
        # Create collection first
        milvus_client_basic.create_collection(test_collection_name, dimension=384)
        assert milvus_client_basic.collection_exists(test_collection_name)
        
        # Delete collection
        result = milvus_client_basic.delete_collection(test_collection_name)
        assert result is True
        
        # Collection should no longer exist
        assert not milvus_client_basic.collection_exists(test_collection_name)
        
        # Deleting non-existent collection should not fail
        result = milvus_client_basic.delete_collection(test_collection_name)
        assert result is True

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_document_insertion(self, milvus_client_basic, test_collection_name, 
                              sample_documents, sample_embeddings):
        """Test inserting documents into collection."""
        try:
            # Create collection
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            
            # Insert documents
            result = milvus_client_basic.insert_documents(
                test_collection_name, 
                sample_documents, 
                sample_embeddings
            )
            assert result is True
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_document_insertion_nonexistent_collection(self, milvus_client_basic, 
                                                     sample_documents, sample_embeddings):
        """Test inserting documents into non-existent collection."""
        nonexistent_collection = f"nonexistent_{uuid.uuid4().hex[:8]}"
        
        # Should raise ValueError for non-existent collection
        with pytest.raises(ValueError, match=f"Collection {nonexistent_collection} does not exist"):
            milvus_client_basic.insert_documents(
                nonexistent_collection,
                sample_documents,
                sample_embeddings
            )

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_document_search(self, milvus_client_basic, test_collection_name,
                           sample_documents, sample_embeddings):
        """Test searching for documents."""
        try:
            # Create collection and insert documents
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            milvus_client_basic.insert_documents(
                test_collection_name,
                sample_documents,
                sample_embeddings
            )
            
            # Wait for index to be built (Milvus may need time)
            time.sleep(2)
            
            # Search using first embedding as query
            query_embedding = sample_embeddings[0]
            results = milvus_client_basic.search(
                test_collection_name,
                query_embedding,
                limit=3
            )
            
            # Verify search results
            assert isinstance(results, list)
            assert len(results) <= 3
            
            if results:  # If results are returned
                for result in results:
                    assert isinstance(result, SearchResult)
                    assert isinstance(result.document, Document)
                    assert isinstance(result.score, float)
                    assert isinstance(result.distance, float)
                    assert result.document.content
                    assert isinstance(result.document.metadata, dict)
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration 
    def test_search_nonexistent_collection(self, milvus_client_basic, sample_embeddings):
        """Test searching in non-existent collection."""
        nonexistent_collection = f"nonexistent_{uuid.uuid4().hex[:8]}"
        
        # Should raise ValueError for non-existent collection
        with pytest.raises(ValueError, match=f"Collection {nonexistent_collection} does not exist"):
            milvus_client_basic.search(
                nonexistent_collection,
                sample_embeddings[0],
                limit=5
            )

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_get_collection_info(self, milvus_client_basic, test_collection_name):
        """Test getting collection information."""
        try:
            # Non-existent collection should return empty dict
            info = milvus_client_basic.get_collection_info("nonexistent_collection")
            assert info == {}
            
            # Create collection
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            
            # Get collection info
            info = milvus_client_basic.get_collection_info(test_collection_name)
            assert isinstance(info, dict)
            assert "name" in info
            assert "schema" in info
            assert "num_entities" in info
            assert info["name"] == test_collection_name
            
            # Verify schema information
            schema = info["schema"]
            assert "fields" in schema
            fields = schema["fields"]
            assert len(fields) >= 4  # id, content, metadata, embedding
            
            field_names = [field["name"] for field in fields]
            assert "id" in field_names
            assert "content" in field_names
            assert "metadata" in field_names
            assert "embedding" in field_names
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_context_manager(self, milvus_client_basic):
        """Test context manager functionality."""
        # Test successful context manager usage
        with milvus_client_basic as client:
            assert client._connected
            assert client is milvus_client_basic
        
        # Should be disconnected after exiting context
        assert not milvus_client_basic._connected

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_document_with_ids_insertion(self, milvus_client_basic, test_collection_name, sample_embeddings):
        """Test inserting documents with explicit IDs."""
        try:
            # Create documents with explicit IDs
            documents = [
                Document(
                    id="doc_1",
                    content="First document with explicit ID.",
                    metadata={"source": "test", "doc_num": 1}
                ),
                Document(
                    id="doc_2", 
                    content="Second document with explicit ID.",
                    metadata={"source": "test", "doc_num": 2}
                ),
            ]
            
            # Create collection and insert
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            result = milvus_client_basic.insert_documents(
                test_collection_name,
                documents,
                sample_embeddings[:2]
            )
            assert result is True
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_complex_metadata_handling(self, milvus_client_basic, test_collection_name, sample_embeddings):
        """Test handling of complex metadata structures."""
        try:
            # Create documents with complex metadata
            documents = [
                Document(
                    content="Document with complex metadata.",
                    metadata={
                        "source": "test_file.txt",
                        "author": "Test Author",
                        "tags": ["ai", "ml", "vector_db"],
                        "score": 0.95,
                        "nested": {
                            "category": "technical",
                            "subcategory": "database"
                        }
                    }
                ),
            ]
            
            # Create collection and insert
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            result = milvus_client_basic.insert_documents(
                test_collection_name,
                documents,
                sample_embeddings[:1]
            )
            assert result is True
            
            # Wait for indexing
            time.sleep(2)
            
            # Search and verify metadata preservation
            results = milvus_client_basic.search(
                test_collection_name,
                sample_embeddings[0],
                limit=1
            )
            
            if results:
                retrieved_metadata = results[0].document.metadata
                assert retrieved_metadata["source"] == "test_file.txt"
                assert retrieved_metadata["author"] == "Test Author"
                assert retrieved_metadata["tags"] == ["ai", "ml", "vector_db"]
                assert retrieved_metadata["score"] == 0.95
                assert retrieved_metadata["nested"]["category"] == "technical"
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_large_batch_insertion(self, milvus_client_basic, test_collection_name):
        """Test inserting a larger batch of documents."""
        try:
            import numpy as np
            np.random.seed(42)
            
            # Create larger set of documents
            num_docs = 50
            documents = [
                Document(
                    content=f"Test document number {i} with unique content.",
                    metadata={"doc_id": i, "batch": "large_test"}
                )
                for i in range(num_docs)
            ]
            
            embeddings = [np.random.rand(384).tolist() for _ in range(num_docs)]
            
            # Create collection and insert
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            result = milvus_client_basic.insert_documents(
                test_collection_name,
                documents,
                embeddings
            )
            assert result is True
            
            # Verify collection info shows correct count
            time.sleep(2)  # Wait for indexing
            info = milvus_client_basic.get_collection_info(test_collection_name)
            assert info["num_entities"] == num_docs
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_search_limit_parameter(self, milvus_client_basic, test_collection_name,
                                  sample_documents, sample_embeddings):
        """Test search limit parameter."""
        try:
            # Create collection and insert documents
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            milvus_client_basic.insert_documents(
                test_collection_name,
                sample_documents,
                sample_embeddings
            )
            
            time.sleep(2)  # Wait for indexing
            
            # Test different limit values
            for limit in [1, 2, 3, 5]:
                results = milvus_client_basic.search(
                    test_collection_name,
                    sample_embeddings[0],
                    limit=limit
                )
                
                # Results should not exceed limit or number of documents
                expected_max = min(limit, len(sample_documents))
                assert len(results) <= expected_max
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_error_handling(self, milvus_config):
        """Test error handling with invalid configuration."""
        # Test with invalid host
        invalid_config = MilvusConfig(
            host="invalid_host_that_does_not_exist",
            port=19530
        )
        
        invalid_client = MilvusVectorDB(config=invalid_config)
        
        # Connection test should fail
        result = invalid_client.test_connection()
        assert result is False
        
        # Operations should handle errors gracefully
        result = invalid_client.create_collection("test", 384)
        assert result is False

    @pytest.mark.milvus
    @pytest.mark.integration
    @pytest.mark.parametrize("limit", [1, 2, 3, 5])
    def test_search_with_various_limits(self, milvus_client_basic, test_collection_name,
                                       sample_documents, sample_embeddings, limit):
        """Test search with various limit parameters using parametrized fixture."""
        try:
            # Create collection and insert documents
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            milvus_client_basic.insert_documents(
                test_collection_name,
                sample_documents,
                sample_embeddings
            )
            
            time.sleep(2)  # Wait for indexing
            
            # Search with parametrized limit
            results = milvus_client_basic.search(
                test_collection_name,
                sample_embeddings[0],
                limit=limit
            )
            
            # Results should not exceed limit or number of documents
            expected_max = min(limit, len(sample_documents))
            assert len(results) <= expected_max
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_large_batch_with_fixture_provider(self, milvus_client_basic, test_collection_name):
        """Test large batch insertion using fixture provider."""
        from mcp_rag_playground.tests.fixtures import milvus_fixtures
        from mcp_rag_playground.vectordb.vector_db_interface import Document
        
        try:
            # Get large document set from fixture provider
            test_docs = milvus_fixtures.get_large_document_set(50)
            documents = [
                Document(content=doc.content, metadata=doc.metadata)
                for doc in test_docs
            ]
            embeddings = milvus_fixtures.get_sample_embeddings(50)
            
            # Create collection and insert
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            result = milvus_client_basic.insert_documents(
                test_collection_name,
                documents,
                embeddings
            )
            assert result is True
            
            # Verify collection info shows correct count
            time.sleep(2)  # Wait for indexing
            info = milvus_client_basic.get_collection_info(test_collection_name)
            assert info["num_entities"] == 50
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_remove_documents_success(self, milvus_client_basic, test_collection_name):
        """Test successful document removal with real Milvus."""
        try:
            # Create and insert test documents
            documents = [
                Document(
                    id="doc_to_remove_1",
                    content="First document to remove.",
                    metadata={"source": "test_removal", "doc_num": 1}
                ),
                Document(
                    id="doc_to_remove_2", 
                    content="Second document to remove.",
                    metadata={"source": "test_removal", "doc_num": 2}
                ),
                Document(
                    id="doc_to_keep",
                    content="Document that should remain.",
                    metadata={"source": "test_removal", "doc_num": 3}
                )
            ]
            
            import numpy as np
            np.random.seed(42)
            embeddings = [np.random.rand(384).tolist() for _ in range(3)]
            
            # Create collection and insert documents
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            result = milvus_client_basic.insert_documents(test_collection_name, documents, embeddings)
            assert result is True
            
            time.sleep(2)  # Wait for indexing
            
            # Verify all documents are inserted
            info = milvus_client_basic.get_collection_info(test_collection_name)
            assert info["num_entities"] == 3
            
            # Remove two documents
            result = milvus_client_basic.remove_documents(test_collection_name, ["doc_to_remove_1", "doc_to_remove_2"])
            assert result is True
            
            time.sleep(1)  # Wait for removal to complete
            
            # Verify documents were removed
            info = milvus_client_basic.get_collection_info(test_collection_name)
            assert info["num_entities"] == 1
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_remove_documents_empty_list(self, milvus_client_basic, test_collection_name):
        """Test remove documents with empty list."""
        try:
            # Create collection
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            
            # Remove empty list should succeed
            result = milvus_client_basic.remove_documents(test_collection_name, [])
            assert result is True
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_remove_documents_nonexistent_collection(self, milvus_client_basic):
        """Test remove documents from non-existent collection."""
        # Try to remove from non-existent collection
        result = milvus_client_basic.remove_documents("nonexistent_collection", ["doc1"])
        assert result is False

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_get_document_by_id_success(self, milvus_client_basic, test_collection_name):
        """Test successful document retrieval by ID with real Milvus."""
        try:
            # Create test document with enhanced metadata
            original_document = Document(
                id="retrievable_doc",
                content="Document content for retrieval test.",
                metadata={"source": "test_retrieval", "importance": "high"},
                filename="test_file.txt",
                file_type=".txt", 
                file_size=100,
                chunk_count=1,
                chunk_position=0,
                embedding_status="completed"
            )
            
            import numpy as np
            np.random.seed(42)
            embedding = [np.random.rand(384).tolist()]
            
            # Create collection and insert document
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            result = milvus_client_basic.insert_documents(test_collection_name, [original_document], embedding)
            assert result is True
            
            time.sleep(2)  # Wait for indexing
            
            # Retrieve document by ID
            retrieved_document = milvus_client_basic.get_document_by_id(test_collection_name, "retrievable_doc")
            
            # Verify document retrieval
            assert retrieved_document is not None
            assert retrieved_document.id == "retrievable_doc"
            assert retrieved_document.content == "Document content for retrieval test."
            assert retrieved_document.metadata["source"] == "test_retrieval"
            assert retrieved_document.metadata["importance"] == "high"
            assert retrieved_document.filename == "test_file.txt"
            assert retrieved_document.file_type == ".txt"
            assert retrieved_document.file_size == 100
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_get_document_by_id_not_found(self, milvus_client_basic, test_collection_name):
        """Test get document by ID when document not found."""
        try:
            # Create collection without any documents
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            
            # Try to retrieve non-existent document
            retrieved_document = milvus_client_basic.get_document_by_id(test_collection_name, "nonexistent_doc")
            assert retrieved_document is None
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_get_document_by_id_nonexistent_collection(self, milvus_client_basic):
        """Test get document by ID from non-existent collection."""
        # Try to retrieve from non-existent collection
        result = milvus_client_basic.get_document_by_id("nonexistent_collection", "doc1")
        assert result is None

    @pytest.mark.milvus
    @pytest.mark.integration
    def test_document_lifecycle(self, milvus_client_basic, test_collection_name):
        """Test complete document lifecycle: insert, retrieve, remove."""
        try:
            # Create test document
            test_document = Document(
                id="lifecycle_doc",
                content="Document for lifecycle testing.",
                metadata={"test": "lifecycle"},
                filename="lifecycle.txt",
                file_type=".txt"
            )
            
            import numpy as np
            np.random.seed(42)
            embedding = [np.random.rand(384).tolist()]
            
            # Step 1: Create collection and insert document
            milvus_client_basic.create_collection(test_collection_name, dimension=384)
            insert_result = milvus_client_basic.insert_documents(test_collection_name, [test_document], embedding)
            assert insert_result is True
            
            time.sleep(2)  # Wait for indexing
            
            # Step 2: Retrieve document and verify
            retrieved = milvus_client_basic.get_document_by_id(test_collection_name, "lifecycle_doc")
            assert retrieved is not None
            assert retrieved.id == "lifecycle_doc"
            assert retrieved.content == "Document for lifecycle testing."
            
            # Step 3: Remove document
            remove_result = milvus_client_basic.remove_documents(test_collection_name, ["lifecycle_doc"])
            assert remove_result is True
            
            time.sleep(1)  # Wait for removal
            
            # Step 4: Verify document is gone
            retrieved_after_removal = milvus_client_basic.get_document_by_id(test_collection_name, "lifecycle_doc")
            assert retrieved_after_removal is None
            
            # Verify collection is empty
            info = milvus_client_basic.get_collection_info(test_collection_name)
            assert info["num_entities"] == 0
            
        finally:
            # Cleanup
            milvus_client_basic.delete_collection(test_collection_name)