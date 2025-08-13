"""
Milvus implementation of the vector database interface.
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from mcp_rag_playground.config.logging_config import get_logger
from mcp_rag_playground.config.milvus_config import MilvusConfig
from mcp_rag_playground.vectordb.milvus.milvus_connection import MilvusConnection
from mcp_rag_playground.vectordb.vector_db_interface import Document, SearchResult, VectorDBInterface

logger = get_logger(__name__)


class MilvusVectorDB(VectorDBInterface):
    """Milvus implementation of vector database interface."""
    
    def __init__(self, config: Optional[MilvusConfig] = None):
        self.connection = MilvusConnection(config)
        self.config = config or MilvusConfig.from_env()
        self._connected = False
    
    def connect(self):
        """Establish connection to Milvus."""
        if not self._connected:
            self.connection.connect()
            self._connected = True
    
    def disconnect(self):
        """Disconnect from Milvus."""
        if self._connected:
            self.connection.disconnect()
            self._connected = False
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection in Milvus using configuration-driven schema."""
        try:
            from pymilvus import Collection, CollectionSchema
            
            self.connect()
            
            if self.collection_exists(collection_name):
                return True
            
            # Get schema configuration
            schema_config = self.config.get_schema_config()
            
            # Build fields from configuration
            field_configs = schema_config.add_embedding_field(dimension)
            fields = []
            
            for field_config in field_configs:
                if not schema_config.validate_field_config(field_config):
                    logger.error(f"Invalid field configuration: {field_config}")
                    return False
                
                field_schema = schema_config.to_milvus_field_schema(field_config)
                fields.append(field_schema)
            
            schema = CollectionSchema(fields, description=f"Collection for {collection_name}")
            collection = Collection(collection_name, schema)
            
            # Create vector index
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            
            # Create indexes on frequently queried metadata fields for performance
            try:
                collection.create_index("filename", {"index_type": "TRIE"})
                collection.create_index("file_type", {"index_type": "TRIE"})
                logger.info(f"Created metadata indexes for collection: {collection_name}")
            except Exception as index_e:
                # Index creation is optional, don't fail if not supported
                logger.warning(f"Could not create metadata indexes: {index_e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False
    
    def insert_documents(self, collection_name: str, documents: List[Document], 
                        embeddings: List[List[float]]) -> bool:
        """Insert documents with their embeddings into the collection."""
        try:
            from pymilvus import Collection
            
            self.connect()
            
            if not self.collection_exists(collection_name):
                raise ValueError(f"Collection {collection_name} does not exist")
            
            collection = Collection(collection_name)
            
            # Use unified enhanced schema approach
            return self._insert_documents_enhanced(collection, documents, embeddings)
            
        except Exception as e:
            logger.error(f"Error inserting documents: {e}")
            return False
    
    def search(self, collection_name: str, query_embedding: List[float], 
               limit: int = 10) -> List[SearchResult]:
        """Search for similar documents using vector similarity."""
        try:
            from pymilvus import Collection
            
            self.connect()
            
            if not self.collection_exists(collection_name):
                raise ValueError(f"Collection {collection_name} does not exist")
            
            collection = Collection(collection_name)
            collection.load()
            
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            # Get output fields from schema configuration
            schema_config = self.config.get_schema_config()
            output_fields = schema_config.get_output_fields()
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=output_fields
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    # Use unified enhanced schema parsing
                    document = self._parse_enhanced_search_result(hit)
                    
                    search_results.append(SearchResult(
                        document=document,
                        score=hit.score,
                        distance=hit.distance
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from Milvus."""
        try:
            from pymilvus import utility
            
            self.connect()
            
            if self.collection_exists(collection_name):
                utility.drop_collection(collection_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        try:
            from pymilvus import utility
            
            self.connect()
            return utility.has_collection(collection_name)
            
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        try:
            from pymilvus import Collection
            
            self.connect()
            
            if not self.collection_exists(collection_name):
                return {}
            
            collection = Collection(collection_name)
            
            return {
                "name": collection_name,
                "description": collection.description,
                "num_entities": collection.num_entities,
                "schema": {
                    "fields": [
                        {
                            "name": field.name,
                            "type": str(field.dtype),
                            "params": field.params
                        }
                        for field in collection.schema.fields
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test the connection to Milvus."""
        try:
            from pymilvus import utility
            
            # Attempt to connect
            self.connect()
            
            # Test with a simple operation - list collections
            utility.list_collections()
            
            logger.info("Milvus connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Milvus connection test failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def _parse_datetime_field(self, datetime_str: str) -> Optional[datetime]:
        """
        Parse datetime string with robust error handling.
        
        Args:
            datetime_str: ISO format datetime string
            
        Returns:
            Parsed datetime or None if parsing fails
        """
        if not datetime_str or not isinstance(datetime_str, str):
            return None
        
        try:
            return datetime.fromisoformat(datetime_str)
        except ValueError:
            logger.warning(f"Failed to parse datetime string: {datetime_str}")
            return None
    
    def _insert_documents_enhanced(self, collection, documents: List[Document], embeddings: List[List[float]]) -> bool:
        """Insert documents using the enhanced schema with individual metadata fields."""
        ids = []
        contents = []
        metadata_list = []
        filenames = []
        file_types = []
        ingestion_timestamps = []
        chunk_counts = []
        file_sizes = []
        chunk_positions = []
        vector_ids = []
        embedding_statuses = []
        
        for doc, embedding in zip(documents, embeddings):
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)
            contents.append(doc.content)
            metadata_list.append(json.dumps(doc.metadata))
            
            # Add enhanced metadata fields
            filenames.append(doc.filename or "")
            file_types.append(doc.file_type or "")
            ingestion_timestamps.append(doc.ingestion_timestamp.isoformat() if doc.ingestion_timestamp else "")
            chunk_counts.append(doc.chunk_count or 0)
            file_sizes.append(doc.file_size or 0)
            chunk_positions.append(doc.chunk_position or 0)
            vector_ids.append(doc.vector_id or doc_id)  # Use doc_id as fallback
            embedding_statuses.append(doc.embedding_status or "pending")
        
        entities = [ids, contents, metadata_list, filenames, file_types, ingestion_timestamps, 
                   chunk_counts, file_sizes, chunk_positions, vector_ids, embedding_statuses, embeddings]
        collection.insert(entities)
        collection.flush()
        return True
    
    
    def _parse_enhanced_search_result(self, hit) -> Document:
        """Parse search result from enhanced schema."""
        metadata = json.loads(hit.entity.get("metadata"))
        
        # Parse ingestion timestamp with improved error handling
        ingestion_timestamp = self._parse_datetime_field(hit.entity.get("ingestion_timestamp"))
        
        return Document(
            content=hit.entity.get("content"),
            metadata=metadata,
            id=hit.id,
            filename=hit.entity.get("filename") or None,
            file_type=hit.entity.get("file_type") or None,
            ingestion_timestamp=ingestion_timestamp,
            chunk_count=hit.entity.get("chunk_count") or None,
            file_size=hit.entity.get("file_size") or None,
            chunk_position=hit.entity.get("chunk_position") or None,
            vector_id=hit.entity.get("vector_id") or None,
            embedding_status=hit.entity.get("embedding_status") or "pending"
        )
    
