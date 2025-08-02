"""
Tests for the MCP Server functionality.
"""

import shutil

from mcp_rag_playground import create_mock_rag_mcp_server
from mcp_rag_playground.tests.test_utils import create_test_files


def test_mcp_server_creation():
    """Test MCP server creation and initialization."""
    print("\n" + "=" * 60)
    print("TESTING MCP SERVER CREATION")
    print("=" * 60)
    
    try:
        # Test creating MCP server
        mcp_server = create_mock_rag_mcp_server("test_mcp_collection")
        print("✓ MCP server created successfully")
        
        # Test getting the FastMCP instance
        fastmcp_instance = mcp_server.get_server()
        print("✓ FastMCP instance retrieved")
        
        # Test attributes
        assert mcp_server.rag_api is not None
        assert mcp_server.mcp is not None
        print("✓ MCP server attributes validated")
        
    except Exception as e:
        print(f"✗ MCP server creation failed: {e}")
        return False
    
    return True


def test_mcp_add_document_tool():
    """Test the add_document_from_file MCP tool."""
    print("\n" + "=" * 60)
    print("TESTING MCP ADD DOCUMENT TOOL")
    print("=" * 60)
    
    try:
        # Create MCP server
        mcp_server = create_mock_rag_mcp_server("test_mcp_add_doc")
        
        # Get test files
        test_files, temp_dir = create_test_files()
        test_file = list(test_files.values())[0]  # Get first test file
        
        try:
            # Test the tool function directly (simulating MCP call)
            # Note: In actual MCP usage, this would be called through the protocol
            
            # Access the tool function through the server's mcp instance
            # For testing, we'll simulate the tool call
            result = mcp_server.mcp._tools["add_document_from_file"].func(test_file)
            
            print(f"📄 Add document result: {result}")
            
            # Validate result
            assert isinstance(result, dict)
            assert "success" in result
            assert "file_path" in result
            print("✓ Add document tool executed successfully")
            
        finally:
            # Cleanup temp files
            shutil.rmtree(temp_dir)
            print("🧹 Cleaned up test files")
            
    except Exception as e:
        print(f"✗ MCP add document tool test failed: {e}")
        return False
    
    return True


def test_mcp_search_tool():
    """Test the search_knowledge_base MCP tool."""
    print("\n" + "=" * 60)
    print("TESTING MCP SEARCH TOOL")
    print("=" * 60)
    
    try:
        # Create MCP server
        mcp_server = create_mock_rag_mcp_server("test_mcp_search")
        
        # Add some test content first
        test_files, temp_dir = create_test_files()
        test_file = list(test_files.values())[0]
        
        try:
            # Add a document first
            add_result = mcp_server.mcp._tools["add_document_from_file"].func(test_file)
            print(f"📄 Added test document: {add_result.get('success', False)}")
            
            # Test search tool
            search_result = mcp_server.mcp._tools["search_knowledge_base"].func(
                "Python programming", 5, 0.0
            )
            
            print(f"🔍 Search result: {search_result}")
            
            # Validate search result
            assert isinstance(search_result, dict)
            assert "success" in search_result
            assert "results" in search_result
            assert "query" in search_result
            print("✓ Search tool executed successfully")
            
            # Test empty query
            empty_search = mcp_server.mcp._tools["search_knowledge_base"].func("", 5, 0.0)
            assert not empty_search["success"]
            print("✓ Empty query handling validated")
        
        finally:
            # Cleanup temp files
            shutil.rmtree(temp_dir)
            print("🧹 Cleaned up test files")
            
    except Exception as e:
        print(f"✗ MCP search tool test failed: {e}")
        return False
    
    return True


def test_mcp_collection_info_tool():
    """Test the get_collection_info MCP tool."""
    print("\n" + "=" * 60)
    print("TESTING MCP COLLECTION INFO TOOL")
    print("=" * 60)
    
    try:
        # Create MCP server
        mcp_server = create_mock_rag_mcp_server("test_mcp_info")
        
        # Test collection info tool
        info_result = mcp_server.mcp._tools["get_collection_info"].func()
        
        print(f"📊 Collection info result: {info_result}")
        
        # Validate result
        assert isinstance(info_result, dict)
        assert "success" in info_result
        assert "collection_name" in info_result
        print("✓ Collection info tool executed successfully")
        
    except Exception as e:
        print(f"✗ MCP collection info tool test failed: {e}")
        return False
    
    return True


def test_mcp_add_content_tool():
    """Test the add_document_from_content MCP tool."""
    print("\n" + "=" * 60)
    print("TESTING MCP ADD CONTENT TOOL")
    print("=" * 60)
    
    try:
        # Create MCP server
        mcp_server = create_mock_rag_mcp_server("test_mcp_content")
        
        # Test content
        test_content = "This is a test document about Python programming and machine learning."
        test_metadata = {"source": "test", "topic": "programming"}
        
        # Test the add content tool
        result = mcp_server.mcp._tools["add_document_from_content"].func(
            test_content, test_metadata
        )
        
        print(f"📝 Add content result: {result}")
        
        # Validate result
        assert isinstance(result, dict)
        assert "success" in result
        assert "content_length" in result
        assert result["content_length"] == len(test_content)
        print("✓ Add content tool executed successfully")
        
    except Exception as e:
        print(f"✗ MCP add content tool test failed: {e}")
        return False
    
    return True


def main():
    """Run all MCP server tests."""
    print("🧪 MCP SERVER TESTS")
    print("=" * 60)
    
    tests = [
        test_mcp_server_creation,
        test_mcp_add_document_tool,
        test_mcp_search_tool,
        test_mcp_collection_info_tool,
        test_mcp_add_content_tool
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED")
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
        print("🎉 All MCP server tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    main()