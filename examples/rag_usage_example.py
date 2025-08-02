#!/usr/bin/env python3
"""
RAG API Usage Example

This script demonstrates how to use the RAG API for document ingestion and semantic search.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import mcp_rag_playground
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_rag_playground import create_rag_api, create_mock_rag_api


def example_basic_usage():
    """Demonstrate basic RAG API usage."""
    print("=" * 60)
    print("🚀 BASIC RAG API USAGE EXAMPLE")
    print("=" * 60)
    
    # Create a RAG API instance (using mock services for demo)
    rag_api = create_mock_rag_api("demo_collection")
    print("✓ Created RAG API instance")
    
    # Example 1: Add documents from content
    print("\n📝 Adding documents from raw content...")
    
    documents = [
        {
            "content": "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, and artificial intelligence.",
            "metadata": {"source": "programming_guide", "topic": "python", "difficulty": "beginner"}
        },
        {
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every scenario.",
            "metadata": {"source": "ai_handbook", "topic": "machine_learning", "difficulty": "intermediate"}
        },
        {
            "content": "Vector databases are specialized databases designed to store, index, and query high-dimensional vector data efficiently. They enable semantic search and similarity matching.",
            "metadata": {"source": "database_guide", "topic": "vector_databases", "difficulty": "advanced"}
        },
        {
            "content": "RAG (Retrieval-Augmented Generation) is a technique that combines information retrieval with language generation to produce more accurate and contextual responses.",
            "metadata": {"source": "rag_paper", "topic": "rag", "difficulty": "advanced"}
        }
    ]
    
    # Add the documents
    result = rag_api.add_documents(documents)
    
    print(f"📊 Upload Results:")
    print(f"  - Total documents: {result['summary']['total']}")
    print(f"  - Successful: {result['summary']['successful']}")
    print(f"  - Failed: {result['summary']['failed']}")
    print(f"  - Success rate: {result['summary']['success_rate']:.1%}")
    
    if result['success']:
        print("✅ All documents added successfully!")
    else:
        print("⚠️ Some documents failed to upload")
        for res in result['results']:
            if not res['success']:
                print(f"  - Error: {res.get('error', 'Unknown error')}")
    
    return rag_api


def example_querying(rag_api):
    """Demonstrate querying functionality."""
    print("\n" + "=" * 60)
    print("🔍 QUERYING EXAMPLES")
    print("=" * 60)
    
    # Example queries
    queries = [
        "What is Python programming?",
        "How do vector databases work?",
        "Explain machine learning",
        "What is RAG technique?"
    ]
    
    for query in queries:
        print(f"\n❓ Query: '{query}'")
        
        # Basic query
        results = rag_api.query(query, limit=3)
        
        if results:
            print(f"📋 Found {len(results)} relevant results:")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. Score: {result['score']:.4f}")
                print(f"     Content: {result['content'][:100]}...")
                print(f"     Source: {result['source']}")
                print(f"     Topic: {result['metadata'].get('topic', 'unknown')}")
        else:
            print("❌ No results found")
    
    # Example with score filtering
    print(f"\n🔍 Query with score filtering (min_score=0.7):")
    high_quality_results = rag_api.query("programming language", limit=5, min_score=0.7)
    print(f"📋 Found {len(high_quality_results)} high-quality results")
    
    for result in high_quality_results:
        print(f"  - Score: {result['score']:.4f} | {result['content'][:60]}...")


def example_file_upload():
    """Demonstrate file upload functionality."""
    print("\n" + "=" * 60)
    print("📁 FILE UPLOAD EXAMPLE")
    print("=" * 60)
    
    # Create a new RAG API instance for file demo
    rag_api = create_mock_rag_api("file_demo_collection")
    
    # Try to find some actual files to upload (if they exist)
    possible_files = [
        "README.md",
        "mcp_rag_playground/tests/test_data/test_document.md",
        "mcp_rag_playground/tests/test_data/test_document.txt",
        "CLAUDE.md"
    ]
    
    existing_files = []
    for file_path in possible_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
    
    if existing_files:
        print(f"📂 Found {len(existing_files)} files to upload:")
        for file_path in existing_files:
            print(f"  - {file_path}")
        
        # Upload the files
        result = rag_api.add_documents(existing_files)
        
        print(f"\n📊 Upload Results:")
        print(f"  - Total files: {result['summary']['total']}")
        print(f"  - Successful: {result['summary']['successful']}")
        print(f"  - Failed: {result['summary']['failed']}")
        
        # Show individual results
        for res in result['results']:
            status = "✅" if res['success'] else "❌"
            filename = res.get('filename', res['source'])
            print(f"  {status} {filename}")
        
        # Test querying the uploaded files
        if result['summary']['successful'] > 0:
            print(f"\n🔍 Querying uploaded files:")
            file_results = rag_api.query("document", limit=3)
            print(f"📋 Found {len(file_results)} results from uploaded files")
            
            for result in file_results:
                filename = result['metadata'].get('file_name', 'unknown')
                print(f"  - {filename}: {result['content'][:80]}...")
    
    else:
        print("📂 No demo files found in current directory")
        print("💡 You can test file upload by providing actual file paths")


def example_mixed_input():
    """Demonstrate mixed file and content input."""
    print("\n" + "=" * 60)
    print("🔀 MIXED INPUT EXAMPLE")
    print("=" * 60)
    
    rag_api = create_mock_rag_api("mixed_demo_collection")
    
    # Create a mix of files and content
    mixed_documents = [
        # Raw content
        {
            "content": "This is inline content about Docker containers and containerization technology.",
            "metadata": {"source": "inline_demo", "type": "content"}
        },
        # More raw content
        {
            "content": "Kubernetes is an orchestration platform for managing containerized applications at scale.",
            "metadata": {"source": "k8s_guide", "type": "content"}
        }
    ]
    
    # Add a file if it exists
    if os.path.exists("README.md"):
        mixed_documents.append("README.md")
    
    print(f"📋 Adding {len(mixed_documents)} mixed documents:")
    for i, doc in enumerate(mixed_documents, 1):
        if isinstance(doc, str):
            print(f"  {i}. File: {doc}")
        else:
            print(f"  {i}. Content: {doc['content'][:50]}...")
    
    # Upload mixed documents
    result = rag_api.add_documents(mixed_documents)
    
    print(f"\n📊 Mixed Upload Results:")
    print(f"  - Success rate: {result['summary']['success_rate']:.1%}")
    
    for i, res in enumerate(result['results'], 1):
        doc_type = res.get('type', 'unknown')
        status = "✅" if res['success'] else "❌"
        source = res.get('filename', res.get('source', 'unknown'))
        print(f"  {i}. {status} {doc_type.title()}: {source}")


def example_collection_management():
    """Demonstrate collection management operations."""
    print("\n" + "=" * 60)
    print("🗂️ COLLECTION MANAGEMENT EXAMPLE")
    print("=" * 60)
    
    rag_api = create_mock_rag_api("mgmt_demo_collection")
    
    # Show initial collection info
    print("📊 Initial collection info:")
    info = rag_api.get_collection_info()
    print(f"  - Name: {info['collection_name']}")
    print(f"  - Status: {info['status']}")
    print(f"  - Ready: {info['collection_ready']}")
    print(f"  - Documents: {info.get('document_count', 0)}")
    
    # Add some test documents
    test_docs = [
        {"content": "Sample document 1", "metadata": {"id": 1}},
        {"content": "Sample document 2", "metadata": {"id": 2}}
    ]
    
    rag_api.add_documents(test_docs)
    
    # Show updated collection info
    print("\n📊 Collection info after adding documents:")
    info = rag_api.get_collection_info()
    print(f"  - Documents: {info.get('document_count', 0)}")
    print(f"  - Status: {info['status']}")
    
    # Demonstrate collection deletion
    print("\n🗑️ Deleting collection...")
    delete_success = rag_api.delete_collection()
    print(f"  Delete result: {'✅ Success' if delete_success else '❌ Failed'}")


def main():
    """Run all RAG API examples."""
    print("🎯 RAG API USAGE EXAMPLES")
    print("=" * 60)
    print("This script demonstrates the RAG API capabilities.")
    print("Using mock embedding service for demonstration purposes.")
    print()
    
    try:
        # Run examples
        rag_api = example_basic_usage()
        example_querying(rag_api)
        example_file_upload()
        example_mixed_input()
        example_collection_management()
        
        print("\n" + "=" * 60)
        print("🎉 All examples completed successfully!")
        print("=" * 60)
        print()
        print("📚 Next steps:")
        print("  1. Install sentence-transformers for real semantic embeddings:")
        print("     pip install sentence-transformers")
        print("  2. Start Milvus for production use:")
        print("     cd vectordb/milvus && docker-compose up -d")
        print("  3. Use create_rag_api('dev') for real embeddings")
        print("  4. Explore the full API documentation in CLAUDE.md")
        
    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()