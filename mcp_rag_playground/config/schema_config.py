"""
Schema configuration for Milvus vector database collections.
"""
from typing import List
from pymilvus import FieldSchema, DataType


class SchemaConfig:
    """Configuration for Milvus vector database schema."""
    
    # Schema field configuration constants
    MAX_CONTENT_LENGTH = 65535
    MAX_METADATA_LENGTH = 65535
    MAX_FILENAME_LENGTH = 1024
    MAX_FILE_TYPE_LENGTH = 50
    MAX_TIMESTAMP_LENGTH = 100
    MAX_VECTOR_ID_LENGTH = 100
    MAX_STATUS_LENGTH = 50
    
    def __init__(self):
        self._field_schemas = self._get_default_field_schemas()
    
    def _get_default_field_schemas(self) -> List[FieldSchema]:
        """Get the default enhanced schema field schemas."""
        return [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=self.MAX_CONTENT_LENGTH, is_primary=True),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=self.MAX_CONTENT_LENGTH),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=self.MAX_METADATA_LENGTH),
            # Enhanced metadata fields for efficient querying
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=self.MAX_FILENAME_LENGTH),
            FieldSchema(name="file_type", dtype=DataType.VARCHAR, max_length=self.MAX_FILE_TYPE_LENGTH),
            FieldSchema(name="ingestion_timestamp", dtype=DataType.VARCHAR, max_length=self.MAX_TIMESTAMP_LENGTH),
            FieldSchema(name="chunk_count", dtype=DataType.INT32),
            FieldSchema(name="file_size", dtype=DataType.INT64),
            FieldSchema(name="chunk_position", dtype=DataType.INT32),
            FieldSchema(name="vector_id", dtype=DataType.VARCHAR, max_length=self.MAX_VECTOR_ID_LENGTH),
            FieldSchema(name="embedding_status", dtype=DataType.VARCHAR, max_length=self.MAX_STATUS_LENGTH),
        ]
    
    def get_field_schemas(self) -> List[FieldSchema]:
        """Get all field schemas."""
        return self._field_schemas.copy()
    
    def get_field_names(self) -> List[str]:
        """Get all field names."""
        return [field.name for field in self._field_schemas]
    
    def get_output_fields(self) -> List[str]:
        """Get field names for search output (excludes embedding vector)."""
        return [field.name for field in self._field_schemas if field.dtype != DataType.FLOAT_VECTOR]
    
    def add_embedding_field(self, dimension: int) -> List[FieldSchema]:
        """Add the embedding vector field with specified dimension."""
        fields = self.get_field_schemas()
        fields.append(FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension))
        return fields