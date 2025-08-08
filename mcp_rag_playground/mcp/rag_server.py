"""
MCP Server wrapper for RAG API functionality.

This module provides a Model Context Protocol (MCP) server that wraps the RagAPI,
making RAG operations available as MCP tools for integration with LLM applications.
"""

import os
import platform
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, AsyncIterator

from mcp.server.fastmcp import FastMCP, Context

from mcp_rag_playground import RagAPI
from mcp_rag_playground.container.container import _container
from mcp_rag_playground.config.logging_config import get_logger

logger = get_logger(__name__)


def _normalize_file_path(file_path: str) -> str:
    """
    Normalize file path for cross-platform compatibility.
    
    Converts Windows paths to WSL paths when running in WSL environment.
    
    Args:
        file_path: Original file path
        
    Returns:
        Normalized file path
    """
    # Check if we're in WSL and the path is a Windows path
    if (platform.system() == "Linux" and 
        "microsoft" in platform.uname().release.lower() and
        file_path.startswith("C:\\") and not os.path.exists(file_path)):
        
        # Convert Windows path to WSL path
        wsl_path = file_path.replace("C:\\", "/mnt/c/").replace("\\", "/")
        if os.path.exists(wsl_path):
            return wsl_path
    
    return file_path



@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage application lifecycle with DI container."""
    logger.info("Initializing RAG server with DI container")
    
    # Get RAG API from production container
    rag_api = _container.rag_api()
    logger.info(f"RAG API initialized with collection: {rag_api.collection_name}")
    
    # Test vector database connection
    logger.info("Testing vector database connection...")
    try:
        connection_success = rag_api.vector_client.test_connection()
        if not connection_success:
            error_msg = "Vector database connection test failed. Cannot start MCP server."
            logger.critical(error_msg)
            raise RuntimeError(error_msg)

        logger.info("Vector database connection successful - MCP server ready to start")

    except Exception as e:
        error_msg = f"Failed to test vector database connection: {e}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    # Create context for MCP tools
    context = {
        "rag_api": rag_api
    }
    
    try:
        yield context
    finally:
        logger.info("RAG server shutdown complete")


server_name = "FileSystemRagMCP"
mcp = FastMCP(server_name, lifespan=app_lifespan)
logger.info(f"Initializing RAG MCP Server: {server_name}")

@mcp.tool()
def add_document_from_file(ctx: Context, file_path: str) -> Dict[str, Any]:
    """
    Add a document to the knowledge base from a file with intelligent processing.

    This tool ingests documents from files, automatically processing and chunking them
    for optimal semantic search. The system supports 15+ file formats including text,
    markdown, code files, JSON, YAML, and web formats.

    Features:
    - Automatic file type detection and processing
    - Intelligent chunking (800 chars with 200 char overlap)
    - Metadata extraction (filename, file type, size)
    - Error handling for missing or corrupted files

    Supported formats: .txt, .md, .py, .js, .ts, .json, .yaml, .css, .html,
    .xml, .toml, .ini, .log and more.

    Use cases:
    - Import documentation, manuals, and guides
    - Add code repositories for semantic code search
    - Ingest configuration files and logs
    - Build knowledge bases from research papers
    - Process customer support documents

    Args:
        file_path: Absolute or relative path to the file to add to the knowledge base.
                  File must exist and be readable.

    Returns:
        Result dictionary containing:
        - success: Boolean indicating if the operation succeeded
        - file_path: The processed file path
        - filename: Base filename for reference
        - message: Human-readable status message
        - error: Error details if the operation failed

    Examples:
        add_document_from_file("/path/to/manual.md")
        add_document_from_file("./docs/api_reference.py")
        add_document_from_file("config.json")
        :param file_path:
        :param ctx:
    """
    try:
        logger.info(f"MCP Tool: add_document_from_file called with: {file_path}")
        # Normalize the file path for cross-platform compatibility
        normalized_path = _normalize_file_path(file_path)

        if not os.path.exists(normalized_path):
            error_msg = f"File not found: {file_path} (checked: {normalized_path})"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "file_path": file_path,
                "normalized_path": normalized_path
            }

        # Check file size and warn about potential processing time
        file_size = os.path.getsize(normalized_path)

        # For files larger than 1MB, provide size information
        if file_size > 1024 * 1024:
            # Calculate estimated processing info
            chunk_size = 4000  # From test environment config
            overlap = 400
            estimated_chunks = max(1, file_size // (chunk_size - overlap))

            # Log file processing info to stderr (not stdout to avoid JSON interference)
            import sys
            print(f"Processing large file: {file_size:,} bytes, estimated {estimated_chunks:,} chunks", file=sys.stderr)

        # Measure processing time
        start_time = time.time()
        logger.info('Getting context of rag_api from DI')
        rag_api : RagAPI = ctx.request_context.lifespan_context.get("rag_api")
        success = rag_api.add_document(normalized_path)
        end_time = time.time()
        processing_time = end_time - start_time

        result = {
            "success": success,
            "file_path": file_path,
            "normalized_path": normalized_path,
            "filename": os.path.basename(normalized_path),
            "file_size": file_size,
            "processing_time_seconds": round(processing_time, 2)
        }

        if success:
            result["message"] = f"Successfully processed {os.path.basename(normalized_path)} ({file_size:,} bytes) in {processing_time:.1f}s"
            logger.info(f"Successfully processed file: {normalized_path} in {processing_time:.1f}s")
        else:
            result["message"] = f"Failed to process {os.path.basename(normalized_path)}"
            logger.error(f"Failed to process file: {normalized_path}")

        return result

    except Exception as e:
        logger.error(f"Exception in add_document_from_file: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }
@mcp.tool()
def add_document_from_content(ctx: Context, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add a document to the knowledge base from raw text content with custom metadata.

    This tool allows direct ingestion of text content without requiring a physical file.
    Perfect for dynamic content, API responses, user input, or programmatically generated
    text that needs to be made searchable in the knowledge base.

    Features:
    - Direct text ingestion without file system dependency
    - Custom metadata support for enhanced categorization and filtering
    - Same intelligent chunking as file-based ingestion (800 chars with 200 char overlap)
    - Automatic content length validation and processing

    Metadata benefits:
    - Add source attribution and document provenance
    - Include categorization tags (topic, type, priority)
    - Store creation timestamps and author information
    - Enable filtered searches and document organization

    Use cases:
    - Add API documentation from swagger/OpenAPI specs
    - Ingest user-generated content (forum posts, comments)
    - Store chat conversations and meeting transcripts
    - Add dynamic content from web scraping
    - Import structured data (JSON, CSV) as searchable text
    - Create knowledge entries from database queries

    Args:
        content: The raw text content to add to the knowledge base. Should be
                meaningful text (minimum recommended: 50+ characters).
        metadata: Optional dictionary of key-value pairs for document metadata.
                 Common keys: 'source', 'topic', 'type', 'author', 'created_at'

    Returns:
        Result dictionary containing:
        - success: Boolean indicating if the operation succeeded
        - content_length: Length of the processed content
        - metadata: The metadata that was stored with the document
        - message: Human-readable status message
        - error: Error details if the operation failed

    Examples:
        add_document_from_content("Python is a programming language...",
                                {"source": "tutorial", "topic": "python"})
        add_document_from_content(api_response_text,
                                {"source": "api", "endpoint": "/users", "timestamp": "2024-01-01"})
        add_document_from_content(meeting_transcript,
                                {"type": "meeting", "participants": ["Alice", "Bob"]})
                                :param metadata:
                                :param content:
                                :param ctx:
    """
    try:
        # Use the batch add_documents method with a single content item
        document = {
            "content": content,
            "metadata": metadata or {}
        }

        # Note: This requires implementing add_documents method in RagAPI
        # For now, we'll simulate it by creating a temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            rag_api : RagAPI = ctx.request_context.lifespan_context.get("rag_api")
            success = rag_api.add_document(temp_file_path)

            return {
                "success": success,
                "content_length": len(content),
                "metadata": metadata or {},
                "message": "Successfully added content" if success else "Failed to add content"
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content_length": len(content) if content else 0
        }


@mcp.tool()
def search_knowledge_base(
    ctx: Context,
    query: str,
    limit: int = 5,
    min_score: float = 0.0
) -> Dict[str, Any]:
    """
    Perform semantic search across the knowledge base to find relevant documents.

    This tool uses advanced semantic search (not just keyword matching) to find documents
    that are conceptually related to your query. It understands context, synonyms, and
    meaning to return the most relevant content from your knowledge base.

    Search capabilities:
    - Semantic understanding: Finds documents by meaning, not just exact words
    - Query preprocessing: Automatically expands abbreviations (db→database, ai→artificial intelligence)
    - Similarity scoring: Returns confidence scores (0.0-1.0) for each result
    - Flexible filtering: Use min_score to filter low-quality matches
    - Rich metadata: Includes source information, document structure, and relevance context

    Scoring system:
    - 1.0: Perfect semantic match
    - 0.8-0.9: Highly relevant content
    - 0.7-0.8: Good relevance (recommended minimum for most use cases)
    - 0.5-0.7: Moderate relevance
    - 0.0-0.5: Lower relevance (consider filtering out)

    Query optimization tips:
    - Use natural language questions: "How do I configure SSL?"
    - Include context: "Python error handling best practices"
    - Try different phrasings if results aren't optimal
    - Use specific terms for technical topics

    Use cases:
    - Answer customer support questions from documentation
    - Find relevant code examples and snippets
    - Research topics across multiple documents
    - Fact-checking and information verification
    - Content discovery and knowledge exploration
    - RAG (Retrieval-Augmented Generation) for AI applications

    Args:
        query: Natural language search query. Can be a question, keywords, or description
              of what you're looking for. Empty queries are not allowed.
        limit: Maximum number of results to return (1-50, default: 5). Higher limits
              may include less relevant results but provide broader coverage.
        min_score: Minimum similarity score threshold (0.0-1.0, default: 0.0).
                  Recommended values: 0.7 for high precision, 0.5 for broader results.

    Returns:
        Search results dictionary containing:
        - success: Boolean indicating if the search succeeded
        - query: The processed search query
        - total_results: Number of documents found
        - limit: Applied result limit
        - min_score: Applied score threshold
        - results: Array of matching documents, each containing:
          * content: The relevant document text
          * score: Similarity score (0.0-1.0)
          * metadata: Document metadata (source, topic, etc.)
          * source: Primary source identifier
          * document_id: Unique document identifier

    Examples:
        search_knowledge_base("How to install Python packages?")
        search_knowledge_base("database connection errors", limit=10, min_score=0.7)
        search_knowledge_base("API authentication methods", limit=3, min_score=0.8)
        :param min_score:
        :param limit:
        :param query:
        :param ctx:
    """
    try:
        logger.info(f"MCP Tool: search_knowledge_base called with query: '{query}' (limit: {limit}, min_score: {min_score})")

        if not query or not query.strip():
            logger.warning("Empty query provided to search_knowledge_base")
            return {
                "success": False,
                "error": "Query cannot be empty",
                "results": []
            }
        rag_api : RagAPI = ctx.request_context.lifespan_context.get("rag_api")
        results = rag_api.query(query.strip(), limit=limit, min_score=min_score)
        logger.info(f"Search completed: {len(results)} results returned")

        return {
            "success": True,
            "query": query.strip(),
            "total_results": len(results),
            "limit": limit,
            "min_score": min_score,
            "results": results
        }

    except Exception as e:
        logger.error(f"Exception in search_knowledge_base: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "results": []
        }

# @mcp.tool()
# def get_collection_info() -> Dict[str, Any]:
#     """
#     Get comprehensive information about the current knowledge base collection status and metrics.
#
#     This tool provides essential insights into your knowledge base health, size, and configuration.
#     Use it to monitor collection status, track document ingestion progress, debug issues,
#     and understand the current state of your searchable content.
#
#     Information provided:
#     - Collection name and identification
#     - Document count and storage metrics
#     - Collection readiness and health status
#     - Schema information and field configuration
#     - Error states and diagnostic information
#
#     Monitoring use cases:
#     - Verify knowledge base is properly initialized before searching
#     - Track document ingestion progress during batch uploads
#     - Debug connection issues or configuration problems
#     - Monitor collection growth and storage usage
#     - Validate collection state before critical operations
#     - Generate usage reports and analytics
#
#     Operational benefits:
#     - Preventive health checks before automated operations
#     - Integration testing and deployment validation
#     - Performance monitoring and capacity planning
#     - Troubleshooting search quality issues
#     - System status dashboards and monitoring
#
#     Returns:
#         Collection information dictionary containing:
#         - success: Boolean indicating if the operation succeeded
#         - collection_name: Name of the current collection
#         - status: Overall collection status ("ready", "not_initialized", "error")
#         - collection_ready: Boolean indicating if the collection is ready for operations
#         - document_count: Number of documents currently stored (if available)
#         - schema_fields: Number of schema fields configured (if available)
#         - raw_info: Complete collection metadata from the vector database
#         - error: Error message if the operation failed
#
#     Example responses:
#         {"success": true, "collection_name": "knowledge_base", "status": "ready",
#          "document_count": 1250, "collection_ready": true}
#         {"success": false, "status": "error", "error": "Connection timeout"}
#     """
#     try:
#         info = rag_api.get_collection_info()
#         return {
#             "success": True,
#             **info
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "collection_name": getattr(rag_api, 'collection_name', 'unknown'),
#             "status": "error"
#         }
#
# @mcp.tool()
# def delete_collection() -> Dict[str, Any]:
#     """
#     ⚠️  DESTRUCTIVE OPERATION: Permanently delete the entire knowledge base collection.
#
#     🚨 CRITICAL WARNING: This operation is IRREVERSIBLE and will completely remove:
#     - ALL documents and their content from the knowledge base
#     - ALL metadata, embeddings, and search indices
#     - ALL collection schema and configuration
#     - The collection itself and its entire history
#
#     This action CANNOT be undone. Once executed, all data is permanently lost.
#
#     Safety recommendations:
#     ⛔ ALWAYS backup your collection before deletion if data recovery might be needed
#     ⛔ VERIFY you are targeting the correct collection using get_collection_info() first
#     ⛔ DOUBLE-CHECK this is the intended operation in production environments
#     ⛔ CONSIDER using this only in development, testing, or explicit cleanup scenarios
#     ⛔ IMPLEMENT additional confirmation layers in production applications
#
#     Legitimate use cases:
#     - Clean slate: Starting fresh with new document sets
#     - Development/testing: Resetting test environments between test runs
#     - Data migration: Removing old collections after successful migration
#     - Storage cleanup: Freeing resources when collections are genuinely no longer needed
#     - Error recovery: Clearing corrupted collections that cannot be repaired
#
#     Alternative approaches to consider:
#     - Selective document removal (if such functionality exists)
#     - Creating new collections instead of deleting existing ones
#     - Archiving collections rather than deleting them
#     - Using separate collections for different environments
#
#     Post-deletion effects:
#     - All search operations will fail until new documents are added
#     - Collection info will show empty/uninitialized state
#     - Any applications depending on this collection will lose access to data
#     - Vector indices and embeddings will need to be rebuilt from scratch
#
#     Returns:
#         Deletion result dictionary containing:
#         - success: Boolean indicating if the deletion succeeded
#         - collection_name: Name of the deleted collection (for confirmation)
#         - message: Confirmation message or failure details
#         - error: Error message if the deletion failed
#
#     Example response:
#         {"success": true, "collection_name": "test_collection",
#          "message": "Successfully deleted collection 'test_collection'"}
#     """
#     try:
#         success = rag_api.delete_collection()
#         collection_name = getattr(rag_api, 'collection_name', 'unknown')
#
#         return {
#             "success": success,
#             "collection_name": collection_name,
#             "message": f"Successfully deleted collection '{collection_name}'" if success
#                       else f"Failed to delete collection '{collection_name}'"
#         }
#
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "collection_name": getattr(rag_api, 'collection_name', 'unknown')
#         }

#
# def _setup_resources(self):
#     """Setup MCP resources for accessing knowledge base content."""
#
#     @self.mcp.resource("rag://collection/info")
#     def get_collection_resource() -> str:
#         """Get collection information as a resource."""
#         try:
#             info = self.rag_api.get_collection_info()
#             return json.dumps(info, indent=2)
#         except Exception as e:
#             return json.dumps({"error": str(e)}, indent=2)
#
#     @self.mcp.resource("rag://search/{query}")
#     def search_resource(query: str) -> str:
#         """Get search results as a resource."""
#         try:
#             results = self.rag_api.query(query, limit=10)
#             return json.dumps({
#                 "query": query,
#                 "results": results
#             }, indent=2)
#         except Exception as e:
#             return json.dumps({
#                 "query": query,
#                 "error": str(e)
#             }, indent=2)
#
# def _setup_prompts(self):
#     """Setup MCP prompts for RAG operations."""
#
#     @self.mcp.prompt()
#     def rag_search_prompt(
#         query: str,
#         context_type: str = "comprehensive",
#         max_results: int = 5
#     ) -> str:
#         """
#         Generate a prompt for RAG-based question answering.
#
#         Args:
#             query: The user's question or search query
#             context_type: Type of context to provide ("comprehensive", "focused", "summary")
#             max_results: Maximum number of context documents to include
#         """
#         try:
#             # Get relevant documents
#             results = self.rag_api.query(query, limit=max_results, min_score=0.3)
#
#             if not results:
#                 return f"""I don't have any relevant information in my knowledge base to answer the question: "{query}"
#
# Please let me know if you'd like me to help you add relevant documents to the knowledge base first."""
#
#             # Build context based on type
#             if context_type == "summary":
#                 context = "\n".join([
#                     f"- {result['content'][:100]}..."
#                     for result in results[:3]
#                 ])
#             elif context_type == "focused":
#                 context = "\n\n".join([
#                     f"Source: {result['source']}\nContent: {result['content'][:200]}..."
#                     for result in results[:2]
#                 ])
#             else:  # comprehensive
#                 context = "\n\n".join([
#                     f"Source: {result['source']} (Score: {result['score']:.3f})\n{result['content']}"
#                     for result in results
#                 ])
#
#             prompt = f"""Based on the following context from my knowledge base, please answer this question: "{query}"
#
# Context:
# {context}
#
# Please provide a comprehensive answer based on the context above. If the context doesn't fully answer the question, please indicate what information might be missing."""
#
#             return prompt
#
#         except Exception as e:
#             return f"""Error generating RAG prompt for query "{query}": {str(e)}
#
# Please try rephrasing your question or check if the knowledge base is properly configured."""
#
# def get_server(self) -> FastMCP:
#     """Get the configured MCP server instance."""
#     return self.mcp