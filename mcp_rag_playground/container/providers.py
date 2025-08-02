"""
Service provider implementations for dependency injection.
"""

from typing import Any
from .config import ConfigProvider
from ..config.milvus_config import MilvusConfig


class MilvusConfigProvider(ConfigProvider):
    """Configuration provider for Milvus database settings."""
    
    def get_config_name(self) -> str:
        """Get the name of this configuration provider."""
        return "milvus"
    
    def get_config(self, environment: str = "default") -> MilvusConfig:
        """
        Get Milvus configuration for the specified environment.
        
        Args:
            environment: The environment name
            
        Returns:
            MilvusConfig instance
        """
        if environment == "test":
            # Test environment with local defaults
            return MilvusConfig(
                host="localhost",
                port=19530,
                user="",
                password="",
                secure=False,
                server_name=""
            )
        elif environment == "dev":
            # Development environment
            return MilvusConfig(
                host="localhost",
                port=19530,
                user="",
                password="",
                secure=False,
                server_name=""
            )
        elif environment == "prod":
            # Production environment - use environment variables
            return MilvusConfig.from_env()
        else:
            # Default environment - use environment variables with fallbacks
            return MilvusConfig.from_env()


class EmbeddingConfigProvider(ConfigProvider):
    """Configuration provider for embedding service settings."""
    
    def get_config_name(self) -> str:
        """Get the name of this configuration provider."""
        return "embedding"
    
    def get_config(self, environment: str = "default") -> dict:
        """
        Get embedding configuration for the specified environment.
        
        Args:
            environment: The environment name
            
        Returns:
            Configuration dictionary
        """
        if environment == "test":
            return {
                "provider": "mock",
                "dimension": 384,
                "model_name": "mock-model"
            }
        elif environment == "dev":
            return {
                "provider": "sentence_transformers",
                "dimension": 384,
                "model_name": "all-MiniLM-L6-v2"
            }
        elif environment == "prod":
            return {
                "provider": "sentence_transformers",
                "dimension": 384,
                "model_name": "all-MiniLM-L6-v2"
            }
        else:
            # Default to development settings
            return {
                "provider": "sentence_transformers",
                "dimension": 384,
                "model_name": "all-MiniLM-L6-v2"
            }


class DocumentProcessorConfigProvider(ConfigProvider):
    """Configuration provider for document processor settings."""
    
    def get_config_name(self) -> str:
        """Get the name of this configuration provider."""
        return "document_processor"
    
    def get_config(self, environment: str = "default") -> dict:
        """
        Get document processor configuration for the specified environment.
        
        Args:
            environment: The environment name
            
        Returns:
            Configuration dictionary
        """
        if environment == "test":
            return {
                "chunk_size": 500,  # Smaller chunks for testing
                "overlap": 50
            }
        elif environment == "dev":
            return {
                "chunk_size": 1000,
                "overlap": 100
            }
        elif environment == "prod":
            return {
                "chunk_size": 1500,  # Larger chunks for production
                "overlap": 150
            }
        else:
            # Default settings
            return {
                "chunk_size": 1000,
                "overlap": 100
            }


class VectorClientConfigProvider(ConfigProvider):
    """Configuration provider for vector client settings."""
    
    def get_config_name(self) -> str:
        """Get the name of this configuration provider."""
        return "vector_client"
    
    def get_config(self, environment: str = "default") -> dict:
        """
        Get vector client configuration for the specified environment.
        
        Args:
            environment: The environment name
            
        Returns:
            Configuration dictionary
        """
        if environment == "test":
            return {
                "default_collection": "test_collection",
                "query_limit": 5
            }
        elif environment == "dev":
            return {
                "default_collection": "dev_collection",
                "query_limit": 10
            }
        elif environment == "prod":
            return {
                "default_collection": "prod_collection",
                "query_limit": 20
            }
        else:
            # Default settings
            return {
                "default_collection": "default_collection",
                "query_limit": 10
            }