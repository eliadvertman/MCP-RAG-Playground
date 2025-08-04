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
    
    def add_document(self, file_path: str) -> bool:
        """
        Add a document to the RAG system from a file.
        
        Args:
            file_path: Path to the file to upload
                
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            logger.info(f"Adding document from file: {file_path}")
            result = self._add_file(file_path)
            success = result["success"]
            if success:
                logger.info(f"Successfully added document: {file_path}")
            else:
                logger.error(f"Failed to add document: {file_path}")
            return success
        except Exception as e:
            logger.error(f"Error adding document {file_path}: {e}")
            return False

    def _add_file(self, file_path: str) -> Dict[str, Any]:
        """Add a single file to the vector database."""
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "source": file_path
                }
            
            success = self.vector_client.upload(file_path)
            
            return {
                "success": success,
                "source": file_path,
                "type": "file",
                "size": os.path.getsize(file_path),
                "filename": os.path.basename(file_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": file_path,
                "type": "file"
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