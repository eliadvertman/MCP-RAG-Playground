#!/usr/bin/env python3
"""
MCP Server Example for RAG functionality.

This script demonstrates how to create and run an MCP server that provides
RAG (Retrieval-Augmented Generation) capabilities through the Model Context Protocol.

Usage:
    # Run the server in development mode
    uv run mcp dev examples/mcp_server_example.py
    
    # Or with direct python
    python examples/mcp_server_example.py
"""

import sys
import os
from pathlib import Path

from mcp.server import FastMCP

# Add the parent directory to the path so we can import mcp_rag_playground
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_rag_playground import create_mock_rag_mcp_server
from mcp_rag_playground.config.logging_config import setup_mcp_logging

# Setup MCP-safe logging (only to stderr and files)
setup_mcp_logging("dev", "INFO")

# Create the MCP server globally so it can be discovered by MCP CLI
# Create the MCP server with mock services (good for development/demo)
# For production, use: create_rag_mcp_server("prod", "production_rag_collection")
rag_mcp_server = create_mock_rag_mcp_server(
    collection_name="demo_knowledge_base",
    server_name="RAG Knowledge Base Demo"
)

# Expose the FastMCP instance globally with standard name expected by MCP CLI
mcp = rag_mcp_server.get_server()


def main():
    """
    Legacy main function for backwards compatibility.
    The MCP server is now created globally for MCP CLI discovery.
    """
    return rag_mcp_server


# This is the entry point that MCP will use
if __name__ == "__main__":
    # When run directly (not via MCP), show information
    print("Starting RAG MCP Server...")
    print("RAG MCP Server initialized with the following capabilities:")
    print("   Tools:")
    print("     - add_document_from_file: Add documents from file paths")
    print("     - add_document_from_content: Add documents from raw content")
    print("     - search_knowledge_base: Search for relevant documents")
    print("     - get_collection_info: Get knowledge base statistics")
    print("     - delete_collection: Remove all documents (destructive)")
    print()
    print("   Resources:")
    print("     - rag://collection/info: Collection information")
    print("     - rag://search/{query}: Search results")
    print()
    print("   Prompts:")
    print("     - rag_search_prompt: Generate context-aware prompts for Q&A")
    print()
    print("Server ready for MCP connections!")
    print("   Use 'uv run mcp dev examples/mcp_server_example.py' to run in development mode")
    print("   Or integrate directly with Claude Desktop or other MCP clients")
    print()
    print("Example usage from an MCP client:")
    print("   - Tool: search_knowledge_base")
    print("     Args: {'query': 'Python programming', 'limit': 5}")
    print("   - Resource: rag://collection/info")
    print("   - Prompt: rag_search_prompt")
    print("     Args: {'query': 'What is machine learning?', 'context_type': 'comprehensive'}")