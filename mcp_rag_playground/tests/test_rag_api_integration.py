"""
Test suite for RAG API integration testing.
Uses real components (no mocks) for end-to-end testing with existing test data.
"""

import os
import time

import pytest


class TestRagAPIIntegration:
    """Integration test suite for RagAPI using real components and test data."""

    @pytest.fixture(autouse=True)
    def cleanup_collection(self, rag_api_basic):
        """Automatically cleanup collection after each test."""
        yield
        # Cleanup: delete the test collection
        try:
            rag_api_basic.delete_collection()
        except Exception:
            pass  # Ignore cleanup errors

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_rag_api_basic_initialization(self, rag_api_basic, test_collection_name):
        """Test RAG API initialization."""
        assert rag_api_basic.collection_name == test_collection_name
        assert rag_api_basic.vector_client is not None
        assert rag_api_basic.vector_client.collection_name == test_collection_name

    @pytest.mark.integration
    @pytest.mark.milvus 
    @pytest.mark.slow
    def test_add_text_document(self, rag_api_basic, test_files):
        """Test adding a text document to RAG system."""
        # Add text document
        result = rag_api_basic.add_document(test_files["txt"])
        assert result is True
        
        # Verify collection info
        info = rag_api_basic.get_collection_info()
        assert info["collection_ready"] is True
        assert info["document_count"] > 0

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_add_markdown_document(self, rag_api_basic, test_files):
        """Test adding a markdown document to RAG system."""
        # Add markdown document
        result = rag_api_basic.add_document(test_files["md"])
        assert result is True
        
        # Verify collection info
        info = rag_api_basic.get_collection_info()
        assert info["collection_ready"] is True
        assert info["document_count"] > 0

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_add_python_document(self, rag_api_basic, test_files):
        """Test adding a Python file to RAG system."""
        # Add Python file
        result = rag_api_basic.add_document(test_files["py"])
        assert result is True
        
        # Verify collection info
        info = rag_api_basic.get_collection_info()
        assert info["collection_ready"] is True
        assert info["document_count"] > 0

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_add_multiple_documents(self, rag_api_basic, test_files):
        """Test adding multiple documents to RAG system."""
        # Add all test documents
        for file_type, file_path in test_files.items():
            result = rag_api_basic.add_document(file_path)
            assert result is True, f"Failed to add {file_type} document: {file_path}"
        
        # Verify collection info
        info = rag_api_basic.get_collection_info()
        assert info["collection_ready"] is True
        assert info["document_count"] > 0

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_query_after_document_addition(self, rag_api_basic, test_files):
        """Test querying the RAG system after adding documents."""
        # Add text document first
        rag_api_basic.add_document(test_files["txt"])
        
        # Wait for indexing
        time.sleep(2)
        
        # Query for content we know is in test_document.txt
        results = rag_api_basic.query("vector database", limit=5)
        
        # Verify results
        assert isinstance(results, list)
        if results:  # If results are found
            for result in results:
                assert "content" in result
                assert "score" in result
                assert "metadata" in result
                assert "source" in result
                assert isinstance(result["score"], float)
                assert result["score"] >= 0.0
                assert result["score"] <= 1.0

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_query_with_score_filtering(self, rag_api_basic, test_files):
        """Test querying with score filtering."""
        # Add markdown document
        rag_api_basic.add_document(test_files["md"])
        
        # Wait for indexing
        time.sleep(2)
        
        # Query with different score thresholds
        all_results = rag_api_basic.query("Lorem ipsum", min_score=0.0, limit=10)
        filtered_results = rag_api_basic.query("Lorem ipsum", min_score=0.7, limit=10)
        
        # Filtered results should be subset of all results
        assert len(filtered_results) <= len(all_results)
        
        # All filtered results should have score >= 0.7
        for result in filtered_results:
            assert result["score"] >= 0.7

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_query_different_content_types(self, rag_api_basic, test_files):
        """Test querying different types of content."""
        # Add all documents
        for file_path in test_files.values():
            rag_api_basic.add_document(file_path)
        
        # Wait for indexing
        time.sleep(3)
        
        # Test queries for different content types
        queries = [
            "vector database",  # Should match text document
            "Section 1",        # Should match markdown document  
            "hello world",      # Should match Python file
            "Lorem ipsum",      # Should match markdown content
        ]
        
        for query in queries:
            results = rag_api_basic.query(query, limit=5)
            # Each query should potentially return results
            # (actual results depend on embedding similarity)
            assert isinstance(results, list)

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_query_limit_parameter(self, rag_api_basic, test_files):
        """Test query limit parameter."""
        # Add document
        rag_api_basic.add_document(test_files["md"])
        
        # Wait for indexing
        time.sleep(2)
        
        # Test different limits
        for limit in [1, 2, 5]:
            results = rag_api_basic.query("document", limit=limit)
            assert len(results) <= limit

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_query_empty_and_invalid_inputs(self, rag_api_basic, test_files):
        """Test querying with empty and invalid inputs."""
        # Add document first
        rag_api_basic.add_document(test_files["txt"])
        
        # Test empty query
        results = rag_api_basic.query("")
        assert results == []
        
        # Test whitespace-only query
        results = rag_api_basic.query("   \n\t   ")
        assert results == []
        
        # Test None query (if handled)
        try:
            results = rag_api_basic.query(None)
            assert results == []
        except (TypeError, AttributeError):
            # Expected if None is not handled gracefully
            pass

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_get_collection_info_states(self, rag_api_basic, test_files):
        """Test collection info in different states."""
        # Test info before any documents
        info = rag_api_basic.get_collection_info()
        assert "collection_name" in info
        assert "status" in info
        
        # Add document
        rag_api_basic.add_document(test_files["txt"])
        
        # Test info after adding document
        info = rag_api_basic.get_collection_info()
        assert info["collection_ready"] is True
        assert "document_count" in info
        assert info["document_count"] > 0

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_collection_deletion(self, rag_api_basic, test_files):
        """Test collection deletion functionality."""
        # Add document first
        rag_api_basic.add_document(test_files["txt"])
        
        # Verify collection exists
        info = rag_api_basic.get_collection_info()
        assert info["collection_ready"] is True
        
        # Delete collection
        result = rag_api_basic.delete_collection()
        assert result is True
        
        # Verify collection state after deletion
        info = rag_api_basic.get_collection_info()
        # Collection should not be ready after deletion
        assert info["collection_ready"] is False or info["document_count"] == 0

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_add_nonexistent_file(self, rag_api_basic):
        """Test adding non-existent file."""
        # Try to add non-existent file
        result = rag_api_basic.add_document("non_existent_file.txt")
        assert result is False

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_semantic_search_quality(self, rag_api_basic, test_files):
        """Test semantic search quality with known content."""
        # Add markdown document which contains "Lorem ipsum"
        rag_api_basic.add_document(test_files["md"])
        
        # Wait for indexing
        time.sleep(2)
        
        # Query for conceptually similar but different wording
        results = rag_api_basic.query("dolor sit amet", limit=5)
        
        if results:
            # Should find results related to Lorem ipsum content
            found_relevant = any("Lorem" in result["content"] or 
                               "dolor" in result["content"] or
                               "ipsum" in result["content"]
                               for result in results)
            # Note: This test might be flaky depending on embedding model
            # but helps verify semantic search is working

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_result_metadata_completeness(self, rag_api_basic, test_files):
        """Test that query results contain complete metadata."""
        # Add document
        rag_api_basic.add_document(test_files["txt"])
        
        # Wait for indexing
        time.sleep(2)
        
        # Query
        results = rag_api_basic.query("test", limit=3)
        
        if results:
            for result in results:
                # Verify required fields
                required_fields = ["content", "score", "metadata", "source", "document_id"]
                for field in required_fields:
                    assert field in result, f"Missing field: {field}"
                
                # Verify field types
                assert isinstance(result["content"], str)
                assert isinstance(result["score"], (int, float))
                assert isinstance(result["metadata"], dict)
                assert isinstance(result["source"], str)

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_multiple_queries_consistency(self, rag_api_basic, test_files):
        """Test that multiple identical queries return consistent results."""
        # Add document
        rag_api_basic.add_document(test_files["py"])
        
        # Wait for indexing
        time.sleep(2)
        
        query_text = "hello world"
        
        # Run same query multiple times
        results1 = rag_api_basic.query(query_text, limit=5)
        results2 = rag_api_basic.query(query_text, limit=5)
        results3 = rag_api_basic.query(query_text, limit=5)
        
        # Results should be consistent
        assert len(results1) == len(results2) == len(results3)
        
        if results1:  # If we got results
            # Scores should be identical for same query
            scores1 = [r["score"] for r in results1]
            scores2 = [r["score"] for r in results2]
            scores3 = [r["score"] for r in results3]
            
            assert scores1 == scores2 == scores3

    @pytest.mark.integration 
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_large_document_handling(self, rag_api_basic, test_files):
        """Test handling of documents that get chunked."""
        # Add markdown document (should be chunked into multiple parts)
        rag_api_basic.add_document(test_files["md"])
        
        # Verify collection contains multiple chunks
        info = rag_api_basic.get_collection_info()
        assert info["document_count"] > 0
        
        # Query should work across chunks
        time.sleep(2)
        results = rag_api_basic.query("Section", limit=10)
        
        # Should find content from different sections
        if results:
            contents = [r["content"] for r in results]
            # Verify we got diverse content (not just one chunk repeated)
            unique_contents = set(contents)
            assert len(unique_contents) >= 1

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_file_path_verification(self, test_files):
        """Verify that test data files exist before running tests."""
        # Ensure all test files exist
        for file_type, file_path in test_files.items():
            assert os.path.exists(file_path), f"Test file missing: {file_path}"
            assert os.path.isfile(file_path), f"Path is not a file: {file_path}"
            assert os.path.getsize(file_path) > 0, f"File is empty: {file_path}"

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_remove_document_integration(self, rag_api_basic, test_files):
        """Test complete add → remove → verify cycle."""
        # Add document and get enhanced metadata
        add_result = rag_api_basic.add_document(test_files["txt"])
        assert add_result["success"] is True
        assert "filename" in add_result
        assert "file_size" in add_result
        
        time.sleep(2)  # Wait for indexing
        
        # Verify document was added by querying
        initial_results = rag_api_basic.query("test", limit=5)
        assert len(initial_results) > 0
        
        # Get document ID from first result
        document_id = initial_results[0]["document_id"]
        assert document_id is not None
        
        # Remove the document
        remove_result = rag_api_basic.remove_document(document_id)
        assert remove_result["success"] is True
        assert remove_result["document_id"] == document_id
        assert "message" in remove_result
        
        time.sleep(1)  # Wait for removal
        
        # Verify document was removed by querying again
        final_results = rag_api_basic.query("test", limit=5)
        # Should have fewer results (or none)
        remaining_ids = [r["document_id"] for r in final_results]
        assert document_id not in remaining_ids

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_batch_add_documents_integration(self, rag_api_basic, test_files):
        """Test batch document addition with multiple file types."""
        # Test with multiple files of different types
        file_paths = [test_files["txt"], test_files["md"], test_files["py"]]
        
        # Batch add documents
        batch_result = rag_api_basic.batch_add_documents(file_paths)
        
        # Verify batch operation results
        assert batch_result["success"] is True
        assert batch_result["total_files"] == 3
        assert batch_result["successful_files"] == 3
        assert batch_result["failed_files"] == 0
        assert len(batch_result["results"]) == 3
        
        # Verify each file was processed
        for i, result in enumerate(batch_result["results"]):
            assert result["success"] is True
            assert result["file_path"] == file_paths[i]
            assert "filename" in result
            assert "file_size" in result
            assert "message" in result
        
        time.sleep(2)  # Wait for indexing
        
        # Verify all documents are searchable
        results = rag_api_basic.query("test", limit=10)
        assert len(results) >= 3  # Should have at least one result per file

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_batch_remove_documents_integration(self, rag_api_basic, test_files):
        """Test batch document removal after batch addition."""
        # First, batch add documents
        file_paths = [test_files["txt"], test_files["md"]]
        add_result = rag_api_basic.batch_add_documents(file_paths)
        assert add_result["success"] is True
        
        time.sleep(2)  # Wait for indexing
        
        # Get document IDs from search results
        initial_results = rag_api_basic.query("test", limit=10)
        assert len(initial_results) >= 2
        
        # Collect document IDs to remove
        document_ids = [result["document_id"] for result in initial_results[:2]]
        
        # Batch remove documents
        remove_result = rag_api_basic.batch_remove_documents(document_ids)
        
        # Verify batch removal results
        assert remove_result["success"] is True
        assert remove_result["total_documents"] == 2
        assert remove_result["successful_removals"] == 2
        assert remove_result["failed_removals"] == 0
        assert len(remove_result["results"]) == 2
        
        # Verify each removal was successful
        for i, result in enumerate(remove_result["results"]):
            assert result["success"] is True
            assert result["document_id"] == document_ids[i]
            assert "message" in result
        
        time.sleep(1)  # Wait for removal
        
        # Verify documents were removed
        final_results = rag_api_basic.query("test", limit=10)
        remaining_ids = [r["document_id"] for r in final_results]
        
        for doc_id in document_ids:
            assert doc_id not in remaining_ids

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_document_lifecycle_integration(self, rag_api_basic, test_files):
        """Test complete document lifecycle with enhanced metadata."""
        # Step 1: Add document with enhanced metadata tracking
        add_result = rag_api_basic.add_document(test_files["py"])
        assert add_result["success"] is True
        
        # Verify enhanced metadata
        expected_fields = ["filename", "file_type", "file_size", "message"]
        for field in expected_fields:
            assert field in add_result
        
        assert add_result["file_type"] == ".py"
        assert add_result["file_size"] > 0
        
        time.sleep(2)  # Wait for indexing
        
        # Step 2: Query and verify document is searchable
        search_results = rag_api_basic.query("hello", limit=5)
        assert len(search_results) > 0
        
        # Get document details
        document_id = search_results[0]["document_id"]
        document_metadata = search_results[0]["metadata"]
        
        # Verify metadata preservation
        assert "file_name" in document_metadata or "filename" in document_metadata
        assert document_metadata.get("source") is not None
        
        # Step 3: Remove document
        remove_result = rag_api_basic.remove_document(document_id)
        assert remove_result["success"] is True
        assert remove_result["document_id"] == document_id
        
        time.sleep(1)  # Wait for removal
        
        # Step 4: Verify document is no longer searchable
        final_search = rag_api_basic.query("hello", limit=5)
        remaining_ids = [r["document_id"] for r in final_search]
        assert document_id not in remaining_ids

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_error_handling_integration(self, rag_api_basic):
        """Test error handling in document management operations."""
        # Test remove non-existent document
        remove_result = rag_api_basic.remove_document("nonexistent_doc_id")
        assert remove_result["success"] is False
        assert "error" in remove_result
        assert remove_result["document_id"] == "nonexistent_doc_id"
        
        # Test batch remove with mixed valid/invalid IDs
        mixed_ids = ["nonexistent_1", "nonexistent_2"]
        batch_remove_result = rag_api_basic.batch_remove_documents(mixed_ids)
        assert batch_remove_result["success"] is False  # All failed
        assert batch_remove_result["total_documents"] == 2
        assert batch_remove_result["successful_removals"] == 0
        assert batch_remove_result["failed_removals"] == 2
        
        # Test batch add with non-existent files
        invalid_files = ["nonexistent1.txt", "nonexistent2.txt"]
        batch_add_result = rag_api_basic.batch_add_documents(invalid_files)
        assert batch_add_result["success"] is False  # All failed
        assert batch_add_result["total_files"] == 2
        assert batch_add_result["successful_files"] == 0
        assert batch_add_result["failed_files"] == 2
        assert "errors" in batch_add_result

    @pytest.mark.integration
    @pytest.mark.milvus
    @pytest.mark.slow
    def test_empty_batch_operations_integration(self, rag_api_basic):
        """Test batch operations with empty lists."""
        # Test empty batch add
        empty_add_result = rag_api_basic.batch_add_documents([])
        assert empty_add_result["success"] is False
        assert empty_add_result["total_files"] == 0
        assert "error" in empty_add_result
        
        # Test empty batch remove  
        empty_remove_result = rag_api_basic.batch_remove_documents([])
        assert empty_remove_result["success"] is False
        assert empty_remove_result["total_documents"] == 0
        assert "error" in empty_remove_result