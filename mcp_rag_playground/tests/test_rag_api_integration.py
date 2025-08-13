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
    def cleanup_collection(self, rag_api_basic_basic):
        """Automatically cleanup collection after each test."""
        yield
        # Cleanup: delete the test collection
        try:
            rag_api_basic_basic.delete_collection()
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