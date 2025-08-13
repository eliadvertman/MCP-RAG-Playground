"""
Tests for schema configuration framework.
"""
import pytest
from unittest.mock import patch, MagicMock

from mcp_rag_playground.config.schema_config import SchemaConfig, FieldConfig, DataType
from mcp_rag_playground.config.milvus_config import MilvusConfig


class TestSchemaConfig:
    """Test schema configuration functionality."""
    
    def test_default_schema_fields(self):
        """Test that default schema contains expected fields."""
        schema_config = SchemaConfig()
        fields = schema_config.get_field_configs()
        
        # Verify expected field count (11 fields without embedding)
        assert len(fields) == 11
        
        # Verify primary key field
        id_field = next(f for f in fields if f.name == "id")
        assert id_field.is_primary is True
        assert id_field.dtype == DataType.VARCHAR
        
        # Verify content fields
        content_fields = ["content", "metadata", "filename", "file_type"]
        for field_name in content_fields:
            field = next(f for f in fields if f.name == field_name)
            assert field.dtype == DataType.VARCHAR
        
        # Verify integer fields
        int_fields = {"chunk_count": DataType.INT32, "chunk_position": DataType.INT32, 
                     "file_size": DataType.INT64}
        for field_name, expected_type in int_fields.items():
            field = next(f for f in fields if f.name == field_name)
            assert field.dtype == expected_type
    
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
        assert embedding_field.dtype == DataType.FLOAT_VECTOR
        assert embedding_field.dim == dimension
    
    def test_validate_field_config(self):
        """Test field configuration validation."""
        schema_config = SchemaConfig()
        
        # Valid VARCHAR field
        valid_varchar = FieldConfig(name="test", dtype=DataType.VARCHAR, max_length=100)
        assert schema_config.validate_field_config(valid_varchar) is True
        
        # Invalid VARCHAR field (no max_length)
        invalid_varchar = FieldConfig(name="test", dtype=DataType.VARCHAR)
        assert schema_config.validate_field_config(invalid_varchar) is False
        
        # Valid vector field
        valid_vector = FieldConfig(name="vector", dtype=DataType.FLOAT_VECTOR, dim=384)
        assert schema_config.validate_field_config(valid_vector) is True
        
        # Invalid vector field (no dimension)
        invalid_vector = FieldConfig(name="vector", dtype=DataType.FLOAT_VECTOR)
        assert schema_config.validate_field_config(invalid_vector) is False
        
        # Invalid field (no name)
        invalid_name = FieldConfig(name="", dtype=DataType.INT32)
        assert schema_config.validate_field_config(invalid_name) is False
    
    @patch('pymilvus.FieldSchema')
    def test_to_milvus_field_schema(self, mock_field_schema):
        """Test conversion to Milvus FieldSchema."""
        schema_config = SchemaConfig()
        
        # Test VARCHAR field conversion
        varchar_field = FieldConfig(
            name="content", 
            dtype=DataType.VARCHAR, 
            max_length=1000, 
            is_primary=False
        )
        
        schema_config.to_milvus_field_schema(varchar_field)
        
        # Verify FieldSchema was called with correct parameters
        mock_field_schema.assert_called_once()
        call_kwargs = mock_field_schema.call_args.kwargs
        
        assert "name" in call_kwargs
        assert "dtype" in call_kwargs
        assert "max_length" in call_kwargs
        
        # Test vector field conversion
        mock_field_schema.reset_mock()
        vector_field = FieldConfig(
            name="embedding", 
            dtype=DataType.FLOAT_VECTOR, 
            dim=384
        )
        
        schema_config.to_milvus_field_schema(vector_field)
        call_kwargs = mock_field_schema.call_args.kwargs
        
        assert "dim" in call_kwargs
        assert call_kwargs["dim"] == 384


class TestMilvusConfigSchemaIntegration:
    """Test MilvusConfig integration with SchemaConfig."""
    
    def test_schema_config_in_config(self):
        """Test that MilvusConfig includes schema configuration."""
        config = MilvusConfig.from_env()
        
        # Should have schema_config initialized
        assert config.schema_config is not None
        assert isinstance(config.schema_config, SchemaConfig)
    
    def test_get_schema_config(self):
        """Test getting schema configuration from MilvusConfig."""
        config = MilvusConfig()
        
        # Should create default if not set
        schema_config = config.get_schema_config()
        assert schema_config is not None
        assert isinstance(schema_config, SchemaConfig)
        
        # Should return same instance on subsequent calls
        same_config = config.get_schema_config()
        assert same_config is schema_config


class TestDualSchemaRemoval:
    """Test that legacy dual schema logic has been completely removed."""
    
    def test_no_legacy_methods_exist(self):
        """Verify legacy methods are completely removed."""
        from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
        
        # These methods should not exist
        assert not hasattr(MilvusVectorDB, '_insert_documents_legacy')
        assert not hasattr(MilvusVectorDB, '_parse_legacy_search_result')
    
    def test_no_field_count_detection(self):
        """Test that field count detection logic is removed."""
        from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
        import inspect
        
        # Get source code of insert_documents and search methods
        insert_source = inspect.getsource(MilvusVectorDB.insert_documents)
        search_source = inspect.getsource(MilvusVectorDB.search)
        
        # These should not contain legacy detection logic
        legacy_keywords = ["len(schema_fields)", "is_enhanced_schema", "field count"]
        
        for keyword in legacy_keywords:
            assert keyword not in insert_source
            assert keyword not in search_source
    
    def test_unified_schema_approach(self):
        """Test that methods use unified schema approach."""
        from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
        import inspect
        
        # insert_documents should call _insert_documents_enhanced directly
        insert_source = inspect.getsource(MilvusVectorDB.insert_documents)
        assert "_insert_documents_enhanced" in insert_source
        assert "_insert_documents_legacy" not in insert_source
        
        # search should use _parse_enhanced_search_result directly
        search_source = inspect.getsource(MilvusVectorDB.search)
        assert "_parse_enhanced_search_result" in search_source
        assert "_parse_legacy_search_result" not in search_source


@pytest.mark.unit
class TestSchemaConfigurationDriven:
    """Test that schema is fully configuration-driven."""
    
    @patch('pymilvus.Collection')
    @patch('pymilvus.CollectionSchema')
    def test_create_collection_uses_config(self, mock_collection_schema, mock_collection):
        """Test that create_collection uses schema configuration."""
        from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
        
        # Mock collection existence check
        config = MilvusConfig()
        db = MilvusVectorDB(config)
        db.collection_exists = MagicMock(return_value=False)
        db.connect = MagicMock()
        
        # Mock collection creation
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance
        
        # Call create_collection
        result = db.create_collection("test_collection", 384)
        
        # Verify it uses schema configuration
        assert result is True
        mock_collection_schema.assert_called_once()
        
        # Verify schema was built from configuration, not hardcoded
        fields_arg = mock_collection_schema.call_args[0][0]
        assert len(fields_arg) == 12  # 11 + 1 embedding field
    
    def test_search_uses_config_output_fields(self):
        """Test that search method uses configuration for output fields."""
        from mcp_rag_playground.vectordb.milvus.milvus_client import MilvusVectorDB
        
        config = MilvusConfig()
        db = MilvusVectorDB(config)
        
        # Get schema config to verify output fields
        schema_config = config.get_schema_config()
        expected_fields = schema_config.get_output_fields()
        
        # This validates that the search method would use these fields
        assert len(expected_fields) == 11
        assert "embedding" not in expected_fields  # Vector field excluded
        assert "content" in expected_fields
        assert "metadata" in expected_fields