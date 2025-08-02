#!/usr/bin/env python3
"""
Production MCP Server for RAG functionality.

This script creates a production-ready MCP server with real vector database
and embedding services for use with Claude Desktop or other MCP clients.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import mcp_rag_playground
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_rag_playground import create_rag_mcp_server
from mcp_rag_playground.config.logging_config import setup_mcp_logging

# Setup MCP-safe logging for production
setup_mcp_logging("prod", "INFO")

# Get configuration from environment variables
environment = os.getenv("MCP_ENVIRONMENT", "prod")
collection_name = os.getenv("MCP_COLLECTION_NAME", "claude_desktop_rag_collection")
server_name = os.getenv("MCP_SERVER_NAME", "Claude Desktop RAG Knowledge Base")

# Create MCP server for production use globally
try:
    rag_mcp_server = create_rag_mcp_server(
        environment=environment,
        collection_name=collection_name,
        server_name=server_name
    )
    
    # Expose the FastMCP instance globally with standard name expected by MCP CLI
    mcp = rag_mcp_server.get_server()
    
except Exception as e:
    # Only print errors to stderr to avoid interfering with MCP JSON
    import sys
    print(f"Failed to start production MCP server: {e}", file=sys.stderr)
    raise


def main():
    """Legacy main function for backwards compatibility."""
    return rag_mcp_server


# This is the entry point that MCP will use
if __name__ == "__main__":
    # When run directly (not via MCP), show information
    print("Starting Production RAG MCP Server...")
    print("Production RAG MCP Server initialized successfully!")
    print(f"   Environment: {environment}")
    print(f"   Collection: {collection_name}")
    print(f"   Server Name: {server_name}")
    print("   Tools:")
    print("     - add_document_from_file: Add documents from file paths")
    print("     - add_document_from_content: Add documents from raw content")
    print("     - search_knowledge_base: Search for relevant documents")
    print("     - get_collection_info: Get knowledge base statistics")
    print("     - delete_collection: Remove all documents (destructive)")
    print("   Resources:")
    print("     - rag://collection/info: Collection information")
    print("     - rag://search/{query}: Search results")
    print("   Prompts:")
    print("     - rag_search_prompt: Generate context-aware prompts for Q&A")
    print()
    print("Production server ready for Claude Desktop integration!")
    print("   Make sure Milvus vector database is running:")
    print("   cd vectordb/milvus && docker-compose up -d")
    print()
    print("Server is now running and ready for MCP client connections")
    print("   Integration: Configure Claude Desktop mcp_servers.json")
    print("   Testing: Use 'mcp inspector' to test server functionality")
    print("   Monitoring: Check logs for connection and operation status")