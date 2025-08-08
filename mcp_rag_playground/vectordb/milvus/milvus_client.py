"""
Milvus implementation of the vector database interface.
"""

import uuid
import json
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
        """Create a new collection in Milvus."""
        try:
            from pymilvus import Collection, FieldSchema, CollectionSchema, DataType
            
            self.connect()
            
            if self.collection_exists(collection_name):
                return True
            
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=65535, is_primary=True),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension)
            ]
            
            schema = CollectionSchema(fields, description=f"Collection for {collection_name}")
            collection = Collection(collection_name, schema)
            
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            
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
            
            ids = []
            contents = []
            metadata_list = []
            
            for doc, embedding in zip(documents, embeddings):
                doc_id = doc.id or str(uuid.uuid4())
                ids.append(doc_id)
                contents.append(doc.content)
                metadata_list.append(json.dumps(doc.metadata))
            
            entities = [ids, contents, metadata_list, embeddings]
            collection.insert(entities)
            collection.flush()
            
            return True
            
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
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=["content", "metadata"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    metadata = json.loads(hit.entity.get("metadata"))
                    document = Document(
                        content=hit.entity.get("content"),
                        metadata=metadata,
                        id=hit.id
                    )
                    
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