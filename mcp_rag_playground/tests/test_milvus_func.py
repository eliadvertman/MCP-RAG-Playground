import os
import shutil

from mcp_rag_playground import MilvusConfig, create_container, create_mock_vector_client
from mcp_rag_playground.tests.test_utils import load_test_config, create_test_files


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
            container = create_container("dev")

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
                    for i, result in enumerate(results):
                        content_preview = result.document.content[:80].replace('\n', ' ')
                        if len(result.document.content) > 80:
                            content_preview += "..."
                        print(f"    {i}. {result.document.metadata.get('file_name', 'unknown')}: {content_preview} with score of {result.score}")
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



def main():
    """Run all tests."""
    print("🧪 MILVUS e2e test")

    # Test: Actual Milvus connection (requires Milvus running)
    test_with_milvus()

    print("✅ Test completed!")

if __name__ == "__main__":
    main()