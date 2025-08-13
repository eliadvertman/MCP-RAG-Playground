"""
RAG API - High-level interface for Retrieval-Augmented Generation operations.

This module provides a simplified API for document ingestion and semantic search,
wrapping the underlying vector database client with user-friendly methods.
"""

from typing import List, Dict, Any, Union, Optional
import os
from pathlib import Path

from mcp_rag_playground.vectordb.vector_client import VectorClient
from mcp_rag_playground.vectordb.vector_db_interface import SearchResult
from mcp_rag_playground.config.logging_config import get_logger

logger = get_logger(__name__)


class RagAPI:
    """
    High-level RAG API for document ingestion and semantic search.
    
    Provides simplified methods for adding documents and querying for relevant content,
    abstracting away the complexity of the underlying vector database operations.
    """
    
    def __init__(self, vector_client: VectorClient, collection_name: str = "rag_collection"):
        """
        Initialize the RAG API.
        
        Args:
            vector_client: Configured VectorClient instance
            collection_name: Name for the document collection
        """
        self.vector_client = vector_client
        self.collection_name = collection_name
        # Update the vector client's collection name
        self.vector_client.collection_name = collection_name
        logger.info(f"RagAPI initialized with collection: {collection_name}")
    
    def add_document(self, file_path: str) -> Dict[str, Any]:
        """
        Add a document to the RAG system from a file.
        
        Args:
            file_path: Path to the file to upload
                
        Returns:
            Dict[str, Any]: Result dictionary containing:
                - success: Boolean indicating if upload was successful
                - file_path: The uploaded file path
                - filename: Base filename for reference
                - file_type: Detected file extension
                - file_size: Size of file in bytes
                - chunk_count: Number of chunks created
                - ingestion_timestamp: When the file was processed
                - message: Human-readable status message
                - error: Error details if upload failed
        """
        try:
            logger.info(f"Adding document from file: {file_path}")
            result = self._add_file(file_path)
            success = result["success"]
            if success:
                logger.info(f"Successfully added document: {file_path}")
            else:
                logger.error(f"Failed to add document: {file_path}")
            return result
        except Exception as e:
            logger.error(f"Error adding document {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def _add_file(self, file_path: str) -> Dict[str, Any]:
        """Add a single file to the vector database with enhanced metadata."""
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "file_path": file_path
                }
            
            # Gather metadata before upload
            filename = os.path.basename(file_path)
            file_type = os.path.splitext(filename)[1].lower()
            file_size = os.path.getsize(file_path)
            
            success = self.vector_client.upload(file_path)
            
            if success:
                # Get enhanced metadata from what was just uploaded
                return {
                    "success": True,
                    "file_path": file_path,
                    "filename": filename,
                    "file_type": file_type,
                    "file_size": file_size,
                    "message": f"Successfully processed {filename} ({file_size:,} bytes)"
                }
            else:
                return {
                    "success": False,
                    "file_path": file_path,
                    "filename": filename,
                    "message": f"Failed to process {filename}",
                    "error": "Upload failed"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    
    def query(self, question: str, limit: int = 5, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Query the RAG system for relevant documents.
        
        Args:
            question: The question or search query
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold (0.0-1.0)
            
        Returns:
            List of result dictionaries containing:
                - content: The document content
                - score: Similarity score (0.0-1.0)
                - metadata: Document metadata
                - source: Source information
                
        Examples:
            # Basic query
            results = api.query("What is machine learning?")
            
            # Query with filtering
            results = api.query("Python programming", limit=10, min_score=0.7)
            
            for result in results:
                # Example output format (for documentation only):
                # print(f"Score: {result['score']}")
                # print(f"Content: {result['content']}")
        """
        if not question or not question.strip():
            logger.warning("Empty query provided to RAG API")
            return []
        
        try:
            logger.info(f"RAG API query: '{question}' (limit: {limit}, min_score: {min_score})")
            # Use vector client's enhanced query method
            search_results: List[SearchResult] = self.vector_client.query(
                question.strip(), 
                limit=limit, 
                min_score=min_score
            )
            
            # Convert SearchResult objects to user-friendly dictionaries
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    "content": result.document.content,
                    "score": result.score,
                    "metadata": result.document.metadata.copy(),
                    "source": result.document.metadata.get("source", "unknown"),
                    "document_id": result.document.id
                }
                
                # Add additional context information
                if "file_name" in result.document.metadata:
                    formatted_result["filename"] = result.document.metadata["file_name"]
                
                if "chunk_index" in result.document.metadata:
                    formatted_result["chunk_info"] = {
                        "index": result.document.metadata["chunk_index"],
                        "total_chunks": result.document.metadata.get("total_chunks", 1)
                    }
                
                formatted_results.append(formatted_result)
            
            logger.info(f"RAG API query completed: {len(formatted_results)} results returned")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during RAG API query: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the current document collection.
        
        Returns:
            Dict containing collection statistics and metadata
        """
        try:
            logger.debug(f"Getting collection info for: {self.collection_name}")
            info = self.vector_client.get_collection_info()
            
            # Enhance with RAG-specific information
            enhanced_info = {
                "collection_name": self.collection_name,
                "status": "ready" if info else "not_initialized",
                "raw_info": info
            }
            
            if info:
                enhanced_info.update({
                    "document_count": info.get("num_entities", 0),
                    "schema_fields": len(info.get("schema", {}).get("fields", [])),
                    "collection_ready": True
                })
            else:
                enhanced_info.update({
                    "document_count": 0,
                    "collection_ready": False
                })
            
            return enhanced_info
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "collection_name": self.collection_name,
                "status": "error",
                "error": str(e),
                "collection_ready": False
            }
    
    def delete_collection(self) -> bool:
        """
        Delete the current document collection.
        
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            logger.warning(f"Deleting collection: {self.collection_name}")
            result = self.vector_client.delete_collection()
            if result:
                logger.info(f"Successfully deleted collection: {self.collection_name}")
            else:
                logger.error(f"Failed to delete collection: {self.collection_name}")
            return result
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def remove_document(self, document_id: str) -> Dict[str, Any]:
        """
        Remove a document from the RAG system.
        
        Args:
            document_id: Unique identifier of the document to remove
            
        Returns:
            Dict[str, Any]: Result dictionary containing:
                - success: Boolean indicating if removal was successful
                - document_id: The document ID that was targeted for removal
                - message: Human-readable status message
                - error: Error details if removal failed
        """
        try:
            logger.info(f"Removing document from RAG system: {document_id}")
            
            if not document_id or not document_id.strip():
                return {
                    "success": False,
                    "error": "Document ID cannot be empty",
                    "document_id": document_id
                }
            
            # Verify document exists before attempting removal
            document = self.vector_client.get_document_by_id(document_id.strip())
            if not document:
                return {
                    "success": False,
                    "error": f"Document with ID '{document_id}' not found",
                    "document_id": document_id
                }
            
            success = self.vector_client.remove_document(document_id.strip())
            
            if success:
                logger.info(f"Successfully removed document: {document_id}")
                return {
                    "success": True,
                    "document_id": document_id,
                    "message": f"Successfully removed document '{document_id}'"
                }
            else:
                logger.error(f"Failed to remove document: {document_id}")
                return {
                    "success": False,
                    "document_id": document_id,
                    "error": "Document removal failed"
                }
                
        except Exception as e:
            logger.error(f"Error removing document {document_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id
            }
    
    def batch_add_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Add multiple documents to the RAG system in a batch operation.
        
        Args:
            file_paths: List of file paths to upload
            
        Returns:
            Dict[str, Any]: Result dictionary containing:
                - success: Boolean indicating overall success
                - total_files: Number of files attempted
                - successful_files: Number of files successfully processed
                - failed_files: Number of files that failed
                - results: List of individual file results
                - message: Summary message
                - errors: List of error details for failed files
        """
        try:
            logger.info(f"Starting batch add operation for {len(file_paths)} files")
            
            if not file_paths:
                return {
                    "success": False,
                    "error": "No file paths provided",
                    "total_files": 0,
                    "successful_files": 0,
                    "failed_files": 0,
                    "results": []
                }
            
            results = []
            successful_count = 0
            failed_count = 0
            errors = []
            
            for file_path in file_paths:
                try:
                    result = self.add_document(file_path)
                    results.append(result)
                    
                    if result.get("success"):
                        successful_count += 1
                        logger.debug(f"Successfully added file: {file_path}")
                    else:
                        failed_count += 1
                        error_msg = f"Failed to add {file_path}: {result.get('error', 'Unknown error')}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Exception adding {file_path}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    results.append({
                        "success": False,
                        "file_path": file_path,
                        "error": str(e)
                    })
            
            overall_success = failed_count == 0
            
            logger.info(f"Batch add completed: {successful_count} successful, {failed_count} failed")
            
            return {
                "success": overall_success,
                "total_files": len(file_paths),
                "successful_files": successful_count,
                "failed_files": failed_count,
                "results": results,
                "message": f"Processed {len(file_paths)} files: {successful_count} successful, {failed_count} failed",
                "errors": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Error in batch add operation: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_files": len(file_paths) if file_paths else 0,
                "successful_files": 0,
                "failed_files": len(file_paths) if file_paths else 0,
                "results": []
            }
    
    def batch_remove_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """
        Remove multiple documents from the RAG system in a batch operation.
        
        Args:
            document_ids: List of document IDs to remove
            
        Returns:
            Dict[str, Any]: Result dictionary containing:
                - success: Boolean indicating overall success
                - total_documents: Number of documents attempted
                - successful_removals: Number of documents successfully removed
                - failed_removals: Number of documents that failed to remove
                - results: List of individual removal results
                - message: Summary message
                - errors: List of error details for failed removals
        """
        try:
            logger.info(f"Starting batch remove operation for {len(document_ids)} documents")
            
            if not document_ids:
                return {
                    "success": False,
                    "error": "No document IDs provided",
                    "total_documents": 0,
                    "successful_removals": 0,
                    "failed_removals": 0,
                    "results": []
                }
            
            results = []
            successful_count = 0
            failed_count = 0
            errors = []
            
            for document_id in document_ids:
                try:
                    result = self.remove_document(document_id)
                    results.append(result)
                    
                    if result.get("success"):
                        successful_count += 1
                        logger.debug(f"Successfully removed document: {document_id}")
                    else:
                        failed_count += 1
                        error_msg = f"Failed to remove {document_id}: {result.get('error', 'Unknown error')}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Exception removing {document_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    results.append({
                        "success": False,
                        "document_id": document_id,
                        "error": str(e)
                    })
            
            overall_success = failed_count == 0
            
            logger.info(f"Batch remove completed: {successful_count} successful, {failed_count} failed")
            
            return {
                "success": overall_success,
                "total_documents": len(document_ids),
                "successful_removals": successful_count,
                "failed_removals": failed_count,
                "results": results,
                "message": f"Processed {len(document_ids)} documents: {successful_count} successful, {failed_count} failed",
                "errors": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Error in batch remove operation: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_documents": len(document_ids) if document_ids else 0,
                "successful_removals": 0,
                "failed_removals": len(document_ids) if document_ids else 0,
                "results": []
            }