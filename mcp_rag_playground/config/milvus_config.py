"""
Milvus vector database configuration and connection management.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class MilvusConfig:
    """Configuration class for Milvus connection."""
    
    host: str = "localhost"
    port: int = 19530
    user: str = ""
    password: str = ""
    secure: bool = False
    server_name: str = ""
    
    @classmethod
    def from_env(cls) -> "MilvusConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("MILVUS_HOST", "localhost"),
            port=int(os.getenv("MILVUS_PORT", "19530")),
            user=os.getenv("MILVUS_USER", ""),
            password=os.getenv("MILVUS_PASSWORD", ""),
            secure=os.getenv("MILVUS_SECURE", "false").lower() == "true",
            server_name=os.getenv("MILVUS_SERVER_NAME", "")
        )
    
    def to_connection_params(self) -> Dict[str, Any]:
        """Convert config to connection parameters."""
        params = {
            "host": self.host,
            "port": self.port
        }
        
        if self.user:
            params["user"] = self.user
            
        if self.password:
            params["password"] = self.password
            
        if self.secure:
            params["secure"] = self.secure
            
        if self.server_name:
            params["server_name"] = self.server_name
            
        return params



# Default configuration instance
default_config = MilvusConfig.from_env()


def get_connection(config: Optional[MilvusConfig] = None):
    """Get a Milvus connection instance."""
    from mcp_rag_playground.vectordb.milvus.milvus_connection import MilvusConnection
    return MilvusConnection(config or default_config)


def test_connection(config: Optional[MilvusConfig] = None) -> bool:
    """Test connection to Milvus."""
    try:
        from mcp_rag_playground.vectordb.milvus.milvus_connection import MilvusConnection
        with MilvusConnection(config or default_config) as conn:
            return conn.is_connected()
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

