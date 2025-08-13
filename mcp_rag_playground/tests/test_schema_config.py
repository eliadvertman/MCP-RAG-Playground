"""
Tests for schema configuration framework.
"""

from mcp_rag_playground.config.schema_config import SchemaConfig


class TestSchemaConfig:
    """Test schema configuration functionality."""
    
    def test_default_schema_fields(self):
        """Test that default schema contains expected fields."""
        schema_config = SchemaConfig()
        field_schemas = schema_config.get_field_schemas()
        
        # Verify expected field count (11 fields without embedding)
        assert len(field_schemas) == 11
        
        # Verify primary key field
        id_field = next(f for f in field_schemas if f.name == "id")
        assert id_field.is_primary is True
        
        # Verify field names
        field_names = [f.name for f in field_schemas]
        expected_names = [
            "id", "content", "metadata", "filename", "file_type", 
            "ingestion_timestamp", "chunk_count", "file_size", 
            "chunk_position", "vector_id", "embedding_status"
        ]
        assert field_names == expected_names
    
    def test_get_field_names(self):
        """Test getting field names."""
        schema_config = SchemaConfig()
        field_names = schema_config.get_field_names()
        
        expected_names = [
            "id", "content", "metadata", "filename", "file_type", 
            "ingestion_timestamp", "chunk_count", "file_size", 
            "chunk_position", "vector_id", "embedding_status"
        ]
        
        assert field_names == expected_names
    
    def test_get_output_fields(self):
        """Test getting output fields (excludes vector)."""
        schema_config = SchemaConfig()
        output_fields = schema_config.get_output_fields()
        
        # Should have all fields except embedding vector
        expected_count = 11  # 11 non-vector fields
        assert len(output_fields) == expected_count
        assert "embedding" not in output_fields
    
    def test_add_embedding_field(self):
        """Test adding embedding field with dimension."""
        schema_config = SchemaConfig()
        dimension = 384
        
        fields_with_embedding = schema_config.add_embedding_field(dimension)
        
        # Should have original fields plus embedding
        assert len(fields_with_embedding) == 12  # 11 + 1 embedding
        
        # Find embedding field
        embedding_field = next(f for f in fields_with_embedding if f.name == "embedding")
        assert embedding_field.dim == dimension
    
    def test_field_schemas_are_milvus_types(self):
        """Test that field schemas are actual Milvus FieldSchema objects."""
        from pymilvus import FieldSchema
        
        schema_config = SchemaConfig()
        field_schemas = schema_config.get_field_schemas()
        
        # All returned objects should be Milvus FieldSchema instances
        for field in field_schemas:
            assert isinstance(field, FieldSchema)
    
    def test_schema_constants_are_defined(self):
        """Test that schema configuration constants are properly defined."""
        assert hasattr(SchemaConfig, 'MAX_CONTENT_LENGTH')
        assert hasattr(SchemaConfig, 'MAX_METADATA_LENGTH') 
        assert hasattr(SchemaConfig, 'MAX_FILENAME_LENGTH')
        assert hasattr(SchemaConfig, 'MAX_FILE_TYPE_LENGTH')
        assert hasattr(SchemaConfig, 'MAX_TIMESTAMP_LENGTH')
        assert hasattr(SchemaConfig, 'MAX_VECTOR_ID_LENGTH')
        assert hasattr(SchemaConfig, 'MAX_STATUS_LENGTH')
        
        # Verify constants are reasonable values
        assert SchemaConfig.MAX_CONTENT_LENGTH > 0
        assert SchemaConfig.MAX_FILENAME_LENGTH > 0
        assert SchemaConfig.MAX_FILE_TYPE_LENGTH > 0
    
    def test_get_field_schemas_returns_copy(self):
        """Test that get_field_schemas returns a copy, not the original list."""
        schema_config = SchemaConfig()
        fields1 = schema_config.get_field_schemas()
        fields2 = schema_config.get_field_schemas()
        
        # Should be different list objects
        assert fields1 is not fields2
        # But contain the same field names
        assert [f.name for f in fields1] == [f.name for f in fields2]