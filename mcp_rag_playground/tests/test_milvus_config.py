#!/usr/bin/env python3
"""
Test script for the vector database client.
"""

import os
import shutil

from mcp_rag_playground.container import create_mock_vector_client, create_container
from mcp_rag_playground.tests.test_utils import load_test_config, create_test_files


def test_with_mock_embedding():
    """Test the vector client with mock embedding service."""
    print("=" * 60)
    print("TESTING WITH MOCK EMBEDDING SERVICE")
    print("=" * 60)
    
    # Load test configuration
    config = load_test_config()
    
    # Create test files
    test_files, temp_dir = create_test_files()
    
    try:
        # Create client using dependency injection container
        client = create_mock_vector_client(config["test_collection_names"]["mock"])
        
        # Get services for display information
        container = create_container("test")
        embedding_service = container.get("embedding_service")
        
        print(f"✓ Created vector client with mock embedding service")
        print(f"  - Embedding dimension: {embedding_service.get_dimension()}")
        
        # Test file upload
        for file_type, file_path in test_files.items():
            print(f"\n📁 Testing {file_type} file upload: {os.path.basename(file_path)}")
            
            try:
                success = client.upload(file_path)
                if success:
                    print(f"  ✓ Successfully uploaded {file_type} file")
                else:
                    print(f"  ✗ Failed to upload {file_type} file")
            except Exception as e:
                print(f"  ✗ Error uploading {file_type} file: {e}")
        
        # Test queries from configuration
        test_queries = config["test_queries"]
        
        print(f"\n🔍 Testing queries:")
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            try:
                # Test without score filtering
                all_results = client.query(query, limit=5, min_score=0.0)
                print(f"    All results: {len(all_results)}")
                
                # Test with score filtering
                filtered_results = client.query(query, limit=5, min_score=0.8)
                print(f"    High-quality results (score ≥ 0.8): {len(filtered_results)}")
                
                results = filtered_results if filtered_results else all_results[:3]
                
                for i, result in enumerate(results, 1):
                    content_preview = result.document.content[:100].replace('\n', ' ')
                    if len(result.document.content) > 100:
                        content_preview += "..."
                    
                    print(f"    {i}. Score: {result.score:.4f}")
                    print(f"       Content: {content_preview}")
                    print(f"       File: {result.document.metadata.get('file_name', 'unknown')}")
                
            except Exception as e:
                print(f"    ✗ Query failed: {e}")
        
        # Test collection info
        print(f"\n📊 Collection Information:")
        try:
            info = client.get_collection_info()
            if info:
                print(f"  - Name: {info.get('name', 'unknown')}")
                print(f"  - Documents: {info.get('num_entities', 'unknown')}")
            else:
                print("  No collection info available (may need Milvus running)")
        except Exception as e:
            print(f"  ✗ Error getting collection info: {e}")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary files")




def test_dependency_injection():
    """Test the dependency injection container functionality."""
    print("\n" + "=" * 60)
    print("TESTING DEPENDENCY INJECTION CONTAINER")
    print("=" * 60)
    
    try:
        # Test creating containers for different environments
        print("🏗️  Testing container creation for different environments:")
        
        test_container = create_container("test")
        print(f"  ✓ Test container created - Services: {len(test_container.list_services())}")
        print(f"    - Configs: {test_container.list_configs()}")
        
        dev_container = create_container("dev")
        print(f"  ✓ Dev container created - Services: {len(dev_container.list_services())}")
        
        # Test configuration differences
        print(f"\n⚙️  Testing environment-specific configurations:")
        test_embedding_config = test_container.get_config("embedding")
        dev_embedding_config = dev_container.get_config("embedding")
        
        print(f"  - Test embedding provider: {test_embedding_config['provider']}")
        print(f"  - Dev embedding provider: {dev_embedding_config['provider']}")
        
        # Test service resolution
        print(f"\n🔧 Testing service resolution:")
        embedding_service = test_container.get("embedding_service")
        print(f"  ✓ Embedding service resolved: {type(embedding_service).__name__}")
        
        vector_db = test_container.get("vector_db")
        print(f"  ✓ Vector DB resolved: {type(vector_db).__name__}")
        
        document_processor = test_container.get("document_processor")
        print(f"  ✓ Document processor resolved: {type(document_processor).__name__}")
        
        vector_client = test_container.get("vector_client")
        print(f"  ✓ Vector client resolved: {type(vector_client).__name__}")
        
        # Test singleton behavior
        print(f"\n🔄 Testing singleton behavior:")
        same_service = test_container.get("embedding_service")
        print(f"  ✓ Same instance returned: {same_service is embedding_service}")
        
        print(f"\n✅ Dependency injection container tests passed!")
        
    except Exception as e:
        print(f"✗ DI container test failed: {e}")


def main():
    """Run all tests."""
    print("🧪 VECTOR DATABASE CLIENT TESTS")
    print("=" * 60)
    
    # Test 1: Dependency injection container
    test_dependency_injection()

    # Test 2: Mock embedding service (always works)
    test_with_mock_embedding()


    print("\n" + "=" * 60)
    print("✅ Tests completed!")


if __name__ == "__main__":
    main()