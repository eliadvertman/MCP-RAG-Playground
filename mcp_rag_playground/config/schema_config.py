"""
Schema configuration for vector database collections.
"""
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class DataType(Enum):
    """Supported data types for schema fields."""
    VARCHAR = "VARCHAR"
    INT32 = "INT32"
    INT64 = "INT64"
    FLOAT_VECTOR = "FLOAT_VECTOR"


@dataclass
class FieldConfig:
    """Configuration for a single field in the schema."""
    name: str
    dtype: DataType
    max_length: int = None
    is_primary: bool = False
    dim: int = None  # For vector fields


class SchemaConfig:
    """Configuration for vector database schema."""
    
    def __init__(self):
        self._fields = self._get_default_fields()
    
    def _get_default_fields(self) -> List[FieldConfig]:
        """Get the default enhanced schema fields configuration."""
        return [
            FieldConfig(name="id", dtype=DataType.VARCHAR, max_length=65535, is_primary=True),
            FieldConfig(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldConfig(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
            # Enhanced metadata fields for efficient querying
            FieldConfig(name="filename", dtype=DataType.VARCHAR, max_length=1024),
            FieldConfig(name="file_type", dtype=DataType.VARCHAR, max_length=50),
            FieldConfig(name="ingestion_timestamp", dtype=DataType.VARCHAR, max_length=100),
            FieldConfig(name="chunk_count", dtype=DataType.INT32),
            FieldConfig(name="file_size", dtype=DataType.INT64),
            FieldConfig(name="chunk_position", dtype=DataType.INT32),
            FieldConfig(name="vector_id", dtype=DataType.VARCHAR, max_length=100),
            FieldConfig(name="embedding_status", dtype=DataType.VARCHAR, max_length=50),
        ]
    
    def get_field_configs(self) -> List[FieldConfig]:
        """Get all field configurations."""
        return self._fields.copy()
    
    def get_field_names(self) -> List[str]:
        """Get all field names."""
        return [field.name for field in self._fields]
    
    def get_output_fields(self) -> List[str]:
        """Get field names for search output (excludes embedding vector)."""
        return [field.name for field in self._fields if field.dtype != DataType.FLOAT_VECTOR]
    
    def add_embedding_field(self, dimension: int) -> List[FieldConfig]:
        """Add the embedding vector field with specified dimension."""
        fields = self.get_field_configs()
        fields.append(FieldConfig(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension))
        return fields
    
    def validate_field_config(self, field: FieldConfig) -> bool:
        """Validate a field configuration."""
        if not field.name:
            return False
        if field.dtype == DataType.VARCHAR and not field.max_length:
            return False
        if field.dtype == DataType.FLOAT_VECTOR and not field.dim:
            return False
        return True
    
    def to_milvus_field_schema(self, field: FieldConfig):
        """Convert FieldConfig to Milvus FieldSchema."""
        from pymilvus import FieldSchema, DataType as MilvusDataType
        
        # Map our DataType enum to Milvus DataType
        dtype_mapping = {
            DataType.VARCHAR: MilvusDataType.VARCHAR,
            DataType.INT32: MilvusDataType.INT32,
            DataType.INT64: MilvusDataType.INT64,
            DataType.FLOAT_VECTOR: MilvusDataType.FLOAT_VECTOR,
        }
        
        milvus_dtype = dtype_mapping[field.dtype]
        
        # Build field parameters
        kwargs = {
            "name": field.name,
            "dtype": milvus_dtype,
        }
        
        if field.is_primary:
            kwargs["is_primary"] = True
        
        if field.max_length:
            kwargs["max_length"] = field.max_length
        
        if field.dim:
            kwargs["dim"] = field.dim
        
        return FieldSchema(**kwargs)