"""
MCP (Model Context Protocol) integration for RAG functionality.

This module provides MCP server implementations that wrap the RAG API,
making document ingestion and semantic search available as MCP tools.
"""

from .rag_server import RagMCPServer

__all__ = [
    'RagMCPServer'
]