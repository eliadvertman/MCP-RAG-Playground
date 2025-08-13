"""
MCP Server wrapper for RAG API functionality.

This module provides a Model Context Protocol (MCP) server that wraps the RagAPI,
making RAG operations available as MCP tools for integration with LLM applications.
"""

import os
import platform
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, Any, Optional, AsyncIterator, List

from mcp.server.fastmcp import FastMCP, Context

from mcp_rag_playground import RagAPI
from mcp_rag_playground.config.logging_config import get_logger
from mcp_rag_playground.container.container import Container

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


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    rag_api: RagAPI

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage application lifecycle with DI container."""
    logger.info("Initializing RAG server with DI container")
    # Get RAG API from production container
    rag_api = container.rag_api()
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
    
    try:
        yield AppContext(rag_api=rag_api)
    finally:
        logger.info("RAG server shutdown complete")

container : Container = Container()
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
        ctx.info(f"MCP Tool: add_document_from_file called with: {file_path}")
        # Normalize the file path for cross-platform compatibility
        normalized_path = _normalize_file_path(file_path)

        if not os.path.exists(normalized_path):
            error_msg = f"File not found: {file_path} (checked: {normalized_path})"
            ctx.error(error_msg)
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
        rag_api : RagAPI = ctx.request_context.lifespan_context.rag_api
        upload_result = rag_api.add_document(normalized_path)
        end_time = time.time()
        processing_time = end_time - start_time

        # Extract success from the enhanced result
        success = upload_result.get("success", False)
        
        result = {
            "success": success,
            "file_path": file_path,
            "normalized_path": normalized_path,
            "filename": os.path.basename(normalized_path),
            "file_size": file_size,
            "processing_time_seconds": round(processing_time, 2)
        }
        
        # Merge enhanced metadata from RagAPI
        if isinstance(upload_result, dict):
            result.update({
                key: value for key, value in upload_result.items() 
                if key not in result and key != "file_path"  # Don't override our normalized path
            })

        if success:
            result["message"] = f"Successfully processed {os.path.basename(normalized_path)} ({file_size:,} bytes) in {processing_time:.1f}s"
            ctx.info(f"Successfully processed file: {normalized_path} in {processing_time:.1f}s")
        else:
            result["message"] = f"Failed to process {os.path.basename(normalized_path)}"
            if upload_result.get("error"):
                result["error"] = upload_result["error"]
            ctx.error(f"Failed to process file: {normalized_path}")
        return result

    except Exception as e:
        ctx.error(f"Exception in add_document_from_file: {e}")
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
            rag_api : RagAPI = ctx.request_context.lifespan_context.rag_api
            upload_result = rag_api.add_document(temp_file_path)
            success = upload_result.get("success", False) if isinstance(upload_result, dict) else upload_result

            result = {
                "success": success,
                "content_length": len(content),
                "metadata": metadata or {},
                "message": "Successfully added content" if success else "Failed to add content"
            }
            
            # Add enhanced metadata if available
            if isinstance(upload_result, dict) and success:
                result.update({
                    key: value for key, value in upload_result.items() 
                    if key not in ["success", "file_path"]  # Skip temp file path
                })
                
            return result
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
        rag_api : RagAPI = ctx.request_context.lifespan_context.rag_api
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

@mcp.tool()
def get_document_metadata(ctx: Context, document_id: str) -> Dict[str, Any]:
    """
    Retrieve comprehensive metadata for a specific document by its ID.
    
    This tool provides detailed information about a document in the knowledge base,
    including both document-level and chunk-level metadata. Perfect for tracking
    document ingestion history, analyzing knowledge base composition, and
    troubleshooting document-related issues.
    
    Returned metadata includes:
    - Basic info: filename, file type, content length
    - Ingestion tracking: timestamp, processing status
    - Chunking details: chunk position, total chunks, file size
    - Vector info: embedding status, vector ID, similarity scores
    - Content preview: truncated document content
    
    Use cases:
    - Document management and administration
    - Debugging ingestion issues
    - Quality assurance and content validation
    - Knowledge base analytics and reporting
    - Troubleshooting search relevance issues
    
    Args:
        document_id: Unique identifier of the document to retrieve metadata for
        
    Returns:
        Document metadata dictionary containing:
        - success: Boolean indicating if the document was found
        - document_id: The requested document ID
        - metadata: Complete document metadata including all tracking fields
        - content_preview: First 200 characters of document content
        - error: Error message if document not found or retrieval failed
    """
    try:
        logger.info(f"MCP Tool: get_document_metadata called for document: {document_id}")
        
        # Input validation
        if not document_id or not isinstance(document_id, str) or not document_id.strip():
            return {
                "success": False,
                "document_id": document_id,
                "error": "document_id must be a non-empty string"
            }
        
        document_id = document_id.strip()
        rag_api: RagAPI = ctx.request_context.lifespan_context.rag_api
        
        # Search for the specific document ID
        # Note: This is a simple implementation. For better performance,
        # consider adding a direct document retrieval method to VectorClient
        results = rag_api.query(document_id, limit=100)
        
        # Find the document with matching ID
        document = None
        for result in results:
            if result.get('document_id') == document_id:
                document = result
                break
        
        if not document:
            return {
                "success": False,
                "document_id": document_id,
                "error": f"Document with ID '{document_id}' not found"
            }
        
        # Extract metadata from the document
        content = document.get('content', '')
        metadata = {
            "document_id": document_id,
            "filename": document.get('filename'),
            "file_type": document.get('file_type'),
            "ingestion_timestamp": document.get('ingestion_timestamp'),
            "chunk_count": document.get('chunk_count'),
            "file_size": document.get('file_size'),
            "chunk_position": document.get('chunk_position'),
            "vector_id": document.get('vector_id'),
            "embedding_status": document.get('embedding_status'),
            "content_length": len(content),
        }
        
        return {
            "success": True,
            "document_id": document_id,
            "metadata": metadata,
            "content_preview": content[:200] + "..." if len(content) > 200 else content
        }
        
    except Exception as e:
        logger.error(f"Exception in get_document_metadata: {e}")
        return {
            "success": False,
            "document_id": document_id,
            "error": str(e)
        }


@mcp.tool()
def list_documents_with_metadata(ctx: Context, limit: int = 20, file_type_filter: str = None) -> Dict[str, Any]:
    """
    List all documents in the knowledge base with their metadata.
    
    This tool provides a comprehensive overview of all documents stored in the
    knowledge base, including their metadata. Essential for knowledge base
    administration, content auditing, and understanding the composition of
    your document collection.
    
    Features:
    - Complete document inventory with metadata
    - Optional file type filtering (e.g., ".py", ".md", ".txt")
    - Pagination support with configurable limits
    - Summary statistics about the knowledge base
    - Document grouping by file type and ingestion date
    
    Metadata included for each document:
    - File information: name, type, size, ingestion date
    - Processing details: chunk count, embedding status
    - Content summary: length, preview
    - Technical details: vector IDs, chunk positions
    
    Use cases:
    - Knowledge base inventory and auditing
    - Content management and organization
    - Identifying processing issues or gaps
    - Planning knowledge base maintenance
    - Generating reports on knowledge base composition
    - Finding documents for selective deletion or updates
    
    Args:
        limit: Maximum number of documents to return (1-100, default: 20)
        file_type_filter: Optional file extension filter (e.g., ".py", ".md")
                         Only documents with matching file types will be included
        
    Returns:
        Document listing dictionary containing:
        - success: Boolean indicating if the operation succeeded
        - total_found: Number of documents found (before limit applied)
        - returned_count: Number of documents in this response
        - limit: Applied result limit
        - file_type_filter: Applied file type filter (if any)
        - documents: Array of document metadata objects
        - summary: Statistics about file types, ingestion dates, etc.
        - error: Error message if the operation failed
    """
    try:
        logger.info(f"MCP Tool: list_documents_with_metadata called (limit: {limit}, filter: {file_type_filter})")
        
        # Input validation
        if limit < 1 or limit > 100:
            return {
                "success": False,
                "error": "limit must be between 1 and 100",
                "documents": []
            }
        
        if file_type_filter is not None and not isinstance(file_type_filter, str):
            return {
                "success": False,
                "error": "file_type_filter must be a string or None",
                "documents": []
            }
        
        rag_api: RagAPI = ctx.request_context.lifespan_context.rag_api
        
        # Use a broad search to get all documents
        # Note: This is not the most efficient approach for large collections
        # Consider implementing a dedicated "list all documents" method
        all_results = rag_api.query("*", limit=max(limit, 1000), min_score=0.0)
        
        # Filter by file type if specified
        if file_type_filter:
            filtered_results = [
                result for result in all_results 
                if result.get('file_type', '').lower() == file_type_filter.lower()
            ]
        else:
            filtered_results = all_results
        
        # Apply limit
        limited_results = filtered_results[:limit]
        
        # Build document metadata list
        documents = []
        file_types = {}
        ingestion_dates = {}
        
        for result in limited_results:
            content = result.get('content', '')
            doc_metadata = {
                "document_id": result.get('document_id'),
                "filename": result.get('filename'),
                "file_type": result.get('file_type'),
                "ingestion_timestamp": result.get('ingestion_timestamp'),
                "chunk_count": result.get('chunk_count'),
                "file_size": result.get('file_size'),
                "chunk_position": result.get('chunk_position'),
                "vector_id": result.get('vector_id'),
                "embedding_status": result.get('embedding_status'),
                "content_length": len(content),
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            }
            documents.append(doc_metadata)
            
            # Collect statistics
            ftype = result.get('file_type', 'unknown')
            file_types[ftype] = file_types.get(ftype, 0) + 1
            
            # Collect ingestion date (just date part)
            timestamp = result.get('ingestion_timestamp')
            if timestamp:
                date_part = timestamp.split('T')[0] if 'T' in timestamp else timestamp
                ingestion_dates[date_part] = ingestion_dates.get(date_part, 0) + 1
        
        # Generate summary
        summary = {
            "file_types": file_types,
            "ingestion_dates": ingestion_dates,
            "total_documents": len(filtered_results),
            "unique_files": len(set(d.get('filename') for d in documents if d.get('filename')))
        }
        
        return {
            "success": True,
            "total_found": len(all_results),
            "returned_count": len(documents),
            "limit": limit,
            "file_type_filter": file_type_filter,
            "documents": documents,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Exception in list_documents_with_metadata: {e}")
        return {
            "success": False,
            "error": str(e),
            "documents": []
        }


@mcp.tool()
def remove_document_from_knowledge_base(ctx: Context, document_id: str) -> Dict[str, Any]:
    """
    Remove a specific document from the knowledge base by its unique identifier.
    
    This tool permanently removes a single document and all its associated data
    (content, metadata, embeddings) from the knowledge base. The removal is
    immediate and cannot be undone.
    
    Safety features:
    - Validates document existence before attempting removal
    - Provides clear feedback about what was removed
    - Prevents removal of non-existent documents
    - Maintains data integrity during the removal process
    
    Use cases:
    - Remove outdated or incorrect information
    - Delete duplicate documents
    - Clean up test data
    - Remove sensitive information that should no longer be searchable
    - Maintain data hygiene in production knowledge bases
    
    Args:
        document_id: The unique identifier of the document to remove.
                    This ID is returned when documents are added or found in search results.
                    
    Returns:
        Removal result dictionary containing:
        - success: Boolean indicating if the removal succeeded
        - document_id: The ID of the document that was targeted
        - message: Human-readable confirmation or error message
        - error: Detailed error information if the operation failed
        
    Examples:
        remove_document_from_knowledge_base("doc_12345")
        remove_document_from_knowledge_base("uuid-generated-id")
    """
    try:
        logger.info(f"MCP Tool: remove_document_from_knowledge_base called for: {document_id}")
        
        # Input validation
        if not document_id or not isinstance(document_id, str) or not document_id.strip():
            return {
                "success": False,
                "document_id": document_id,
                "error": "document_id must be a non-empty string"
            }
        
        rag_api: RagAPI = ctx.request_context.lifespan_context.rag_api
        result = rag_api.remove_document(document_id.strip())
        
        if result.get("success"):
            ctx.info(f"Successfully removed document: {document_id}")
        else:
            ctx.error(f"Failed to remove document: {document_id} - {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Exception in remove_document_from_knowledge_base: {e}")
        return {
            "success": False,
            "document_id": document_id,
            "error": str(e)
        }


@mcp.tool()
def batch_add_documents_from_files(ctx: Context, file_paths: List[str]) -> Dict[str, Any]:
    """
    Add multiple documents to the knowledge base from a list of file paths.
    
    This tool processes multiple files in a single operation, providing efficient
    batch ingestion with comprehensive progress tracking and error handling.
    Each file is processed with the same quality and metadata tracking as
    individual file additions.
    
    Features:
    - Parallel-capable processing of multiple files
    - Individual file success/failure tracking
    - Comprehensive error reporting and recovery
    - Progress monitoring for large batch operations
    - Maintains all file type support (15+ formats)
    - Transaction-safe: partial failures don't corrupt the knowledge base
    
    Performance considerations:
    - Large files will take longer to process
    - Memory usage scales with the number and size of files
    - Consider breaking very large batches into smaller chunks
    - Network/disk I/O is the primary bottleneck
    
    Use cases:
    - Initial knowledge base population
    - Bulk import from file systems or archives
    - Migration from other documentation systems
    - Batch processing of daily/periodic content updates
    - Development environment setup with test data
    
    Args:
        file_paths: List of absolute or relative paths to files to add.
                   Each path must exist and point to a readable file.
                   Supports all file formats (.txt, .md, .py, .json, etc.)
                   
    Returns:
        Batch operation result dictionary containing:
        - success: Boolean indicating overall batch success (true only if all files succeeded)
        - total_files: Total number of files attempted
        - successful_files: Number of files successfully processed
        - failed_files: Number of files that failed to process
        - results: Array of individual file results with detailed metadata
        - message: Summary message describing the batch operation outcome
        - errors: Array of error messages for failed files (null if no errors)
        
    Examples:
        batch_add_documents_from_files(["/docs/manual.md", "/code/api.py"])
        batch_add_documents_from_files(["./config.json", "./README.txt"])
    """
    try:
        logger.info(f"MCP Tool: batch_add_documents_from_files called with {len(file_paths)} files")
        
        # Input validation
        if not file_paths or not isinstance(file_paths, list):
            return {
                "success": False,
                "error": "file_paths must be a non-empty list",
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0,
                "results": []
            }
        
        if len(file_paths) > 100:  # Reasonable batch limit
            return {
                "success": False,
                "error": "Batch size limited to 100 files per operation",
                "total_files": len(file_paths),
                "successful_files": 0,
                "failed_files": len(file_paths),
                "results": []
            }
        
        # Normalize file paths
        normalized_paths = []
        for file_path in file_paths:
            if not isinstance(file_path, str):
                return {
                    "success": False,
                    "error": f"All file paths must be strings, got: {type(file_path)}",
                    "total_files": len(file_paths),
                    "successful_files": 0,
                    "failed_files": len(file_paths),
                    "results": []
                }
            normalized_paths.append(_normalize_file_path(file_path))
        
        rag_api: RagAPI = ctx.request_context.lifespan_context.rag_api
        result = rag_api.batch_add_documents(normalized_paths)
        
        # Log results
        if result.get("success"):
            ctx.info(f"Batch add completed successfully: {result.get('successful_files', 0)} files processed")
        else:
            failed = result.get('failed_files', 0)
            successful = result.get('successful_files', 0)
            ctx.error(f"Batch add completed with errors: {successful} successful, {failed} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Exception in batch_add_documents_from_files: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_files": len(file_paths) if file_paths else 0,
            "successful_files": 0,
            "failed_files": len(file_paths) if file_paths else 0,
            "results": []
        }


@mcp.tool()
def batch_remove_documents_from_knowledge_base(ctx: Context, document_ids: List[str]) -> Dict[str, Any]:
    """
    Remove multiple documents from the knowledge base by their unique identifiers.
    
    This tool performs bulk removal of documents, providing efficient batch
    deletion with comprehensive tracking and safety features. Each document
    is validated before removal to prevent errors.
    
    Safety features:
    - Validates each document ID before attempting removal
    - Provides detailed feedback about what was and wasn't removed
    - Transaction-safe: failures don't affect successfully removed documents
    - Comprehensive error reporting for failed removals
    - Maintains data integrity throughout the batch operation
    
    Performance considerations:
    - Removal operations are generally fast (metadata deletion)
    - Network latency may affect large batches
    - Consider breaking very large batches (1000+) into smaller chunks
    - Failed removals don't block successful ones
    
    Use cases:
    - Clean up outdated documentation in bulk
    - Remove test data after development cycles
    - Delete duplicate or incorrect content
    - Periodic maintenance of the knowledge base
    - Migration cleanup when replacing content
    
    Args:
        document_ids: List of unique document identifiers to remove.
                     These IDs are returned when documents are added or found in search results.
                     Each ID must be a non-empty string.
                     
    Returns:
        Batch removal result dictionary containing:
        - success: Boolean indicating overall batch success (true only if all removals succeeded)
        - total_documents: Total number of documents targeted for removal
        - successful_removals: Number of documents successfully removed
        - failed_removals: Number of documents that failed to remove
        - results: Array of individual removal results with success/error details
        - message: Summary message describing the batch operation outcome
        - errors: Array of error messages for failed removals (null if no errors)
        
    Examples:
        batch_remove_documents_from_knowledge_base(["doc_123", "doc_456"])
        batch_remove_documents_from_knowledge_base(["uuid-generated-id"])
    """
    try:
        logger.info(f"MCP Tool: batch_remove_documents_from_knowledge_base called with {len(document_ids)} documents")
        
        # Input validation
        if not document_ids or not isinstance(document_ids, list):
            return {
                "success": False,
                "error": "document_ids must be a non-empty list",
                "total_documents": 0,
                "successful_removals": 0,
                "failed_removals": 0,
                "results": []
            }
        
        if len(document_ids) > 1000:  # Reasonable batch limit
            return {
                "success": False,
                "error": "Batch size limited to 1000 documents per operation",
                "total_documents": len(document_ids),
                "successful_removals": 0,
                "failed_removals": len(document_ids),
                "results": []
            }
        
        # Validate document IDs
        for doc_id in document_ids:
            if not isinstance(doc_id, str) or not doc_id.strip():
                return {
                    "success": False,
                    "error": f"All document IDs must be non-empty strings, got: {type(doc_id)}",
                    "total_documents": len(document_ids),
                    "successful_removals": 0,
                    "failed_removals": len(document_ids),
                    "results": []
                }
        
        rag_api: RagAPI = ctx.request_context.lifespan_context.rag_api
        result = rag_api.batch_remove_documents(document_ids)
        
        # Log results
        if result.get("success"):
            ctx.info(f"Batch removal completed successfully: {result.get('successful_removals', 0)} documents removed")
        else:
            failed = result.get('failed_removals', 0)
            successful = result.get('successful_removals', 0)
            ctx.error(f"Batch removal completed with errors: {successful} successful, {failed} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Exception in batch_remove_documents_from_knowledge_base: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_documents": len(document_ids) if document_ids else 0,
            "successful_removals": 0,
            "failed_removals": len(document_ids) if document_ids else 0,
            "results": []
        }


@mcp.tool()
def delete_collection(ctx: Context) -> Dict[str, Any]:
    """
    ⚠️  DESTRUCTIVE OPERATION: Permanently delete the entire knowledge base collection.

    🚨 CRITICAL WARNING: This operation is IRREVERSIBLE and will completely remove:
    - ALL documents and their content from the knowledge base
    - ALL metadata, embeddings, and search indices
    - ALL collection schema and configuration
    - The collection itself and its entire history

    This action CANNOT be undone. Once executed, all data is permanently lost.

    Safety recommendations:
    ⛔ ALWAYS backup your collection before deletion if data recovery might be needed
    ⛔ VERIFY you are targeting the correct collection using get_collection_info() first
    ⛔ DOUBLE-CHECK this is the intended operation in production environments
    ⛔ CONSIDER using this only in development, testing, or explicit cleanup scenarios
    ⛔ IMPLEMENT additional confirmation layers in production applications

    Legitimate use cases:
    - Clean slate: Starting fresh with new document sets
    - Development/testing: Resetting test environments between test runs
    - Data migration: Removing old collections after successful migration
    - Storage cleanup: Freeing resources when collections are genuinely no longer needed
    - Error recovery: Clearing corrupted collections that cannot be repaired

    Alternative approaches to consider:
    - Selective document removal (if such functionality exists)
    - Creating new collections instead of deleting existing ones
    - Archiving collections rather than deleting them
    - Using separate collections for different environments

    Post-deletion effects:
    - All search operations will fail until new documents are added
    - Collection info will show empty/uninitialized state
    - Any applications depending on this collection will lose access to data
    - Vector indices and embeddings will need to be rebuilt from scratch

    Args:
        ctx: MCP context for accessing the RAG API instance

    Returns:
        Deletion result dictionary containing:
        - success: Boolean indicating if the deletion succeeded
        - collection_name: Name of the deleted collection (for confirmation)
        - message: Confirmation message or failure details
        - error: Error message if the deletion failed

    Example response:
        {"success": true, "collection_name": "test_collection",
         "message": "Successfully deleted collection 'test_collection'"}
    """
    try:
        logger.warning("MCP Tool: delete_collection called - DESTRUCTIVE OPERATION")
        rag_api: RagAPI = ctx.request_context.lifespan_context.rag_api
        collection_name = rag_api.collection_name
        
        success = rag_api.delete_collection()

        result = {
            "success": success,
            "collection_name": collection_name,
            "message": f"Successfully deleted collection '{collection_name}'" if success
                      else f"Failed to delete collection '{collection_name}'"
        }
        
        if success:
            logger.warning(f"Collection '{collection_name}' has been permanently deleted")
        else:
            logger.error(f"Failed to delete collection '{collection_name}'")
            
        return result

    except Exception as e:
        logger.error(f"Exception in delete_collection: {e}")
        rag_api: RagAPI = ctx.request_context.lifespan_context.rag_api
        collection_name = getattr(rag_api, 'collection_name', 'unknown') if rag_api else 'unknown'
        
        return {
            "success": False,
            "error": str(e),
            "collection_name": collection_name
        }


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