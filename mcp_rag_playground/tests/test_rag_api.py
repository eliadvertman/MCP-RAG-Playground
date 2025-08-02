"""
Tests for the RAG API functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path

from mcp_rag_playground import create_mock_rag_api, create_rag_api
from mcp_rag_playground.tests.test_utils import create_test_files, load_test_config


def test_rag_api_creation():
    """Test RAG API creation and initialization."""
    print("\n" + "=" * 60)
    print("TESTING RAG API CREATION")
    print("=" * 60)
    
    try:
        # Test creating RAG API
        rag_api = create_mock_rag_api("test_rag_creation")
        print("✓ RAG API created successfully")
        
        # Test collection info
        info = rag_api.get_collection_info()
        print(f"✓ Collection info: {info['collection_name']}")
        
        # Test attributes
        assert rag_api.collection_name == "test_rag_creation"
        assert rag_api.vector_client is not None
        print("✓ RAG API attributes validated")
        
    except Exception as e:
        print(f"✗ RAG API creation failed: {e}")
        return False
    
    return True


def test_add_documents_from_files():
    """Test adding documents from file paths."""
    print("\n" + "=" * 60)
    print("TESTING ADD_DOCUMENTS WITH FILES")
    print("=" * 60)
    
    try:
        # Create RAG API
        rag_api = create_mock_rag_api("test_files")
        
        # Get test files
        test_files, temp_dir = create_test_files()
        file_paths = list(test_files.values())
        
        print(f"📁 Adding {len(file_paths)} files to RAG API")
        
        try:
            # Add documents one by one
            successful_uploads = 0
            for file_path in file_paths:
                success = rag_api.add_document(file_path)
                if success:
                    successful_uploads += 1
                    print(f"✓ Successfully uploaded: {os.path.basename(file_path)}")
                else:
                    print(f"✗ Failed to upload: {os.path.basename(file_path)}")
            
            # Validate results
            assert successful_uploads > 0, "No files were uploaded successfully"
            print(f"✓ File upload successful: {successful_uploads} files")
            
            # Test collection info after adding documents
            info = rag_api.get_collection_info()
            print(f"✓ Collection now has {info.get('document_count', 0)} documents")
            
        finally:
            # Cleanup temp files
            shutil.rmtree(temp_dir)
            print("🧹 Cleaned up test files")
            
    except Exception as e:
        print(f"✗ File upload test failed: {e}")
        return False
    
    return True






def test_query_functionality():
    """Test RAG API query functionality."""
    print("\n" + "=" * 60)
    print("TESTING QUERY FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Create RAG API and add some content
        rag_api = create_mock_rag_api("test_query")
        
        # Add test files for querying (using existing test files from create_test_files)
        test_files, temp_dir_query = create_test_files()
        file_paths = list(test_files.values())
        
        successful_uploads = 0
        for file_path in file_paths:
            success = rag_api.add_document(file_path)
            if success:
                successful_uploads += 1
        
        # Cleanup temp files
        shutil.rmtree(temp_dir_query)
        
        assert successful_uploads > 0, "Failed to add test documents"
        print(f"✓ {successful_uploads} test documents added successfully")
        
        # Test basic query
        print("\n🔍 Testing basic query:")
        results = rag_api.query("Python programming")
        print(f"  Found {len(results)} results for 'Python programming'")
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"    {i}. Score: {result['score']:.4f}")
                print(f"       Content: {result['content'][:60]}...")
                print(f"       Source: {result.get('source', result['metadata'].get('source', 'unknown'))}")
        
        # Test query with filtering
        print("\n🔍 Testing query with score filtering:")
        filtered_results = rag_api.query("vector database", limit=10, min_score=0.5)
        print(f"  Found {len(filtered_results)} high-quality results for 'vector database'")
        
        # Test empty query
        print("\n🔍 Testing empty query:")
        empty_results = rag_api.query("")
        assert len(empty_results) == 0, "Empty query should return no results"
        print("  ✓ Empty query correctly returns no results")
        
        # Test query result structure
        if results:
            result = results[0]
            required_keys = ['content', 'score', 'metadata', 'source']
            for key in required_keys:
                assert key in result, f"Result missing required key: {key}"
            print("✓ Query result structure validated")
        
    except Exception as e:
        print(f"✗ Query test failed: {e}")
        return False
    
    return True




def test_collection_management():
    """Test collection management operations."""
    print("\n" + "=" * 60)
    print("TESTING COLLECTION MANAGEMENT")
    print("=" * 60)
    
    try:
        # Create RAG API
        rag_api = create_mock_rag_api("test_collection_mgmt")
        
        # Test initial collection info
        print("📊 Testing initial collection info:")
        info = rag_api.get_collection_info()
        print(f"  Collection: {info['collection_name']}")
        print(f"  Status: {info['status']}")
        print(f"  Ready: {info['collection_ready']}")
        
        # Add a test file
        test_files, temp_dir_mgmt = create_test_files()
        test_file = list(test_files.values())[0]  # Get first test file
        
        success = rag_api.add_document(test_file)
        assert success, "Failed to add test document"
        
        # Cleanup temp files
        shutil.rmtree(temp_dir_mgmt)
        
        # Test collection info after adding documents
        print("📊 Testing collection info after adding documents:")
        info = rag_api.get_collection_info()
        print(f"  Documents: {info.get('document_count', 0)}")
        print(f"  Status: {info['status']}")
        
        # Test collection deletion
        print("🗑️ Testing collection deletion:")
        delete_success = rag_api.delete_collection()
        print(f"  Delete result: {'✓' if delete_success else '✗'}")
        
    except Exception as e:
        print(f"✗ Collection management test failed: {e}")
        return False
    
    return True


def main():
    """Run all RAG API tests."""
    print("🧪 RAG API TESTS")
    print("=" * 60)
    
    tests = [
        test_rag_api_creation,
        test_add_documents_from_files,
        test_query_functionality,
        test_collection_management
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED1")
            else:
                failed += 1
                print("❌ FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All RAG API tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    main()