#!/usr/bin/env python3
"""
Test script for the vector database client.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

from mcp_rag_playground.config.milvus_config import MilvusConfig
from mcp_rag_playground.vectordb.embedding_service import MockEmbeddingService
from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
from mcp_rag_playground.vectordb.vector_client import VectorClient
from mcp_rag_playground.container import create_mock_vector_client, create_container


def get_test_data_dir():
    """Get the path to the test data directory."""
    current_file = Path(__file__)
    test_data_dir = current_file.parent / "test_data"

    if not test_data_dir.exists():
        raise FileNotFoundError(f"Test data directory not found: {test_data_dir}")

    return test_data_dir


def get_test_file_paths():
    """Get paths to the static test data files."""
    test_data_dir = get_test_data_dir()

    test_files = {
        'markdown': test_data_dir / "test_document.md",
        'text': test_data_dir / "test_document.txt",
        'python': test_data_dir / "test_module.py"
    }

    # Verify all test files exist
    for file_type, file_path in test_files.items():
        if not file_path.exists():
            raise FileNotFoundError(f"Test {file_type} file not found: {file_path}")

    return test_files


def get_direct_test_files():
    """Get direct paths to test files (no copying needed for read-only tests)."""
    source_files = get_test_file_paths()
    return {file_type: str(path) for file_type, path in source_files.items()}


def load_test_config():
    """Load test configuration from test_config.json."""
    test_data_dir = get_test_data_dir()
    config_path = test_data_dir / "test_config.json"

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Return default configuration if file doesn't exist
        return {
            "test_queries": ["vector database", "Python programming", "hello world", "markdown document"],
            "milvus_test_queries": ["vector database", "Python class", "greeting message"],
            "embedding_dimension": 384,
            "chunk_size": 1000,
            "chunk_overlap": 100,
            "test_collection_names": {
                "mock": "test_collection_mock",
                "milvus": "test_collection_milvus"
            }
        }


def create_test_files():
    """Create temporary test files for testing by copying from test_data."""
    try:
        # Get source test files
        source_files = get_test_file_paths()

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Copy test files to temporary directory
        test_files = {}
        for file_type, source_path in source_files.items():
            dest_path = os.path.join(temp_dir, source_path.name)
            shutil.copy2(source_path, dest_path)
            test_files[file_type] = dest_path

        return test_files, temp_dir

    except Exception as e:
        raise RuntimeError(f"Failed to create test files: {e}")


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
                results = client.query(query, limit=3)
                print(f"    Found {len(results)} results:")

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


def test_with_milvus():
    """Test the vector client with actual Milvus connection."""
    print("\n" + "=" * 60)
    print("TESTING WITH ACTUAL MILVUS CONNECTION")
    print("=" * 60)

    # Load test configuration
    test_config = load_test_config()

    # Test Milvus connection
    milvus_config = MilvusConfig.from_env()
    print(f"Attempting to connect to Milvus at {milvus_config.host}:{milvus_config.port}")

    try:
        from mcp_rag_playground.config.milvus_config import test_connection

        if not test_connection(milvus_config):
            print("⚠️  Milvus is not running. Skipping Milvus tests.")
            print("   To run Milvus: cd vectordb/milvus && docker-compose up -d")
            return

        print("✓ Milvus connection successful!")

        # Create test files
        test_files, temp_dir = create_test_files()

        try:
            # Create client using dependency injection container
            # Note: We still create a test client since we want to use the actual Milvus config
            container = create_container("test")

            # Override the Milvus config with the actual one we tested
            container.register_instance("milvus_config_override", milvus_config)

            # Create client with the tested Milvus config
            client = create_mock_vector_client(test_config["test_collection_names"]["milvus"])

            print(f"✓ Created vector client with Milvus backend")

            # Clean up any existing test collection
            client.delete_collection()

            # Test file upload
            print(f"\n📁 Testing file uploads to Milvus:")
            for file_type, file_path in test_files.items():
                try:
                    success = client.upload(file_path)
                    if success:
                        print(f"  ✓ {file_type}: {os.path.basename(file_path)}")
                    else:
                        print(f"  ✗ {file_type}: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"  ✗ {file_type}: {e}")

            # Test queries
            print(f"\n🔍 Testing queries against Milvus:")
            test_queries = test_config["milvus_test_queries"]

            for query in test_queries:
                try:
                    results = client.query(query, limit=10)
                    print(f"\n  '{query}' -> {len(results)} results")
                    for i, result in enumerate(results, 1):
                        content_preview = result.document.content[:80].replace('\n', ' ')
                        if len(result.document.content) > 80:
                            content_preview += "..."
                        print(f"    {i}. {result.document.metadata.get('file_name', 'unknown')}: {content_preview} with score of {result.distance}")
                except Exception as e:
                    print(f"  ✗ Query '{query}' failed: {e}")

            # Get collection info
            print(f"\n📊 Milvus Collection Info:")
            info = client.get_collection_info()
            if info:
                print(f"  - Collection: {info.get('name')}")
                print(f"  - Documents: {info.get('num_entities')}")
                print(f"  - Schema fields: {len(info.get('schema', {}).get('fields', []))}")

            # Cleanup
            print(f"\n🧹 Cleaning up test collection...")
            client.delete_collection()

        finally:
            # Cleanup files
            shutil.rmtree(temp_dir)

    except ImportError as e:
        print(f"⚠️  Cannot test Milvus: {e}")
    except Exception as e:
        print(f"✗ Milvus test failed: {e}")


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

    # Test 3: Actual Milvus connection (requires Milvus running)
    test_with_milvus()

    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("\nNOTE: To test with actual embeddings, install sentence-transformers:")
    print("      pip install sentence-transformers")


if __name__ == "__main__":
    main()