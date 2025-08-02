"""
Main vector database client with upload and query capabilities.
"""

from typing import List, Dict, Any
from .vector_db_interface import VectorDBInterface, SearchResult
from .embedding_service import EmbeddingService
from mcp_rag_playground.vectordb.processor.document_processor import DocumentProcessor


class VectorClient:
    """Main client for vector database operations."""
    
    def __init__(self, 
                 vector_db: VectorDBInterface,
                 embedding_service: EmbeddingService,
                 document_processor : DocumentProcessor,
                 collection_name: str = "default_collection"
                ):
        self.vector_db = vector_db
        self.embedding_service = embedding_service
        self.collection_name = collection_name
        self.document_processor = document_processor
        self._initialized = False
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists, create if not."""
        if not self._initialized:
            dimension = self.embedding_service.get_dimension()
            
            if not self.vector_db.collection_exists(self.collection_name):
                success = self.vector_db.create_collection(self.collection_name, dimension)
                if not success:
                    raise RuntimeError(f"Failed to create collection: {self.collection_name}")
            
            self._initialized = True
    
    def upload(self, file_path: str) -> bool:
        """
        Upload a file to the vector database.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            self._ensure_collection_exists()
            
            documents = self.document_processor.process_file(file_path)
            
            if not documents:
                print(f"No documents extracted from file: {file_path}")
                return False
            
            texts = [doc.content for doc in documents]
            embeddings = self.embedding_service.embed_texts(texts)
            
            success = self.vector_db.insert_documents(
                self.collection_name, 
                documents, 
                embeddings
            )
            
            if success:
                print(f"Successfully uploaded {len(documents)} document chunks from {file_path}")
            else:
                print(f"Failed to upload file: {file_path}")
            
            return success
            
        except Exception as e:
            print(f"Error uploading file {file_path}: {e}")
            return False
    
    def query(self, query_text: str, limit: int = 5) -> List[SearchResult]:
        """
        Query the vector database for similar documents.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results to return
            
        Returns:
            List[SearchResult]: List of search results
        """
        try:
            self._ensure_collection_exists()
            
            query_embedding = self.embedding_service.embed_text(query_text)
            
            results = self.vector_db.search(
                self.collection_name,
                query_embedding,
                limit
            )
            
            return results
            
        except Exception as e:
            print(f"Error querying database: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        try:
            self._ensure_collection_exists()
            return self.vector_db.get_collection_info(self.collection_name)
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {}
    
    def delete_collection(self) -> bool:
        """Delete the current collection."""
        try:
            success = self.vector_db.delete_collection(self.collection_name)
            if success:
                self._initialized = False
                print(f"Successfully deleted collection: {self.collection_name}")
            return success
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False