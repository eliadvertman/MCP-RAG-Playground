"""
Main vector database client with upload and query capabilities.
"""

from typing import List, Dict, Any
import re
from .vector_db_interface import VectorDBInterface, SearchResult
from .embedding_service import EmbeddingService
from mcp_rag_playground.vectordb.processor.document_processor import DocumentProcessor
from mcp_rag_playground.config.logging_config import get_logger

logger = get_logger(__name__)


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
        logger.info(f"VectorClient initialized with collection: {collection_name}")
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists, create if not."""
        if not self._initialized:
            dimension = self.embedding_service.get_dimension()
            logger.info(f"Ensuring collection exists: {self.collection_name} (dimension: {dimension})")
            
            if not self.vector_db.collection_exists(self.collection_name):
                logger.info(f"Creating new collection: {self.collection_name}")
                success = self.vector_db.create_collection(self.collection_name, dimension)
                if not success:
                    error_msg = f"Failed to create collection: {self.collection_name}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                logger.info(f"Successfully created collection: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
            
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
            logger.info(f"Starting upload of file: {file_path}")
            self._ensure_collection_exists()
            
            documents = self.document_processor.process_file(file_path)
            
            if not documents:
                logger.warning(f"No documents extracted from file: {file_path}")
                return False
            
            logger.info(f"Extracted {len(documents)} documents from {file_path}")
            texts = [doc.content for doc in documents]
            embeddings = self.embedding_service.embed_texts(texts)
            
            success = self.vector_db.insert_documents(
                self.collection_name, 
                documents, 
                embeddings
            )
            
            if success:
                logger.info(f"Successfully uploaded {len(documents)} documents from {file_path}")
            else:
                logger.error(f"Failed to upload file: {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return False
    
    
    def _preprocess_query(self, query_text: str) -> str:
        """Preprocess query text for better search results."""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query_text.strip())
        
        # Convert to lowercase for consistency
        query = query.lower()
        
        # Remove special characters that might interfere with search
        query = re.sub(r'[^\w\s\-\']', ' ', query)
        
        # Handle common abbreviations and expansions
        expansions = {
            'db': 'database',
            'ai': 'artificial intelligence',
            'ml': 'machine learning',
            'api': 'application programming interface',
            'ui': 'user interface',
            'ux': 'user experience'
        }
        
        words = query.split()
        expanded_words = []
        for word in words:
            if word in expansions:
                expanded_words.extend([word, expansions[word]])
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)

    def query(self, query_text: str, limit: int = 5, min_score: float = 0.0) -> List[SearchResult]:
        """
        Query the vector database for similar documents.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold (0.0-1.0)
            
        Returns:
            List[SearchResult]: List of search results filtered by score
        """
        try:
            logger.info(f"Starting query: '{query_text}' (limit: {limit}, min_score: {min_score})")
            self._ensure_collection_exists()
            
            # Preprocess query for better results
            processed_query = self._preprocess_query(query_text)
            logger.debug(f"Preprocessed query: '{processed_query}'")
            
            query_embedding = self.embedding_service.embed_text(processed_query)
            
            results = self.vector_db.search(
                self.collection_name,
                query_embedding,
                limit
            )
            
            # Filter results by minimum score threshold
            filtered_results = [result for result in results if result.score >= min_score]
            
            logger.info(f"Query completed: found {len(results)} results, {len(filtered_results)} after filtering")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error querying database: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        try:
            logger.debug(f"Getting collection info for: {self.collection_name}")
            self._ensure_collection_exists()
            info = self.vector_db.get_collection_info(self.collection_name)
            logger.debug(f"Collection info retrieved: {info}")
            return info
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def delete_collection(self) -> bool:
        """Delete the current collection."""
        try:
            logger.warning(f"Deleting collection: {self.collection_name}")
            success = self.vector_db.delete_collection(self.collection_name)
            if success:
                self._initialized = False
                logger.info(f"Successfully deleted collection: {self.collection_name}")
            else:
                logger.error(f"Failed to delete collection: {self.collection_name}")
            return success
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test the connection to the vector database."""
        try:
            logger.info("Testing vector database connection...")
            success = self.vector_db.test_connection()
            if success:
                logger.info("Vector database connection test successful")
            else:
                logger.error("Vector database connection test failed")
            return success
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return False