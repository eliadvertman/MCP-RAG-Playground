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


class MilvusConnection:
    """Milvus connection manager."""
    
    def __init__(self, config: Optional[MilvusConfig] = None):
        self.config = config or MilvusConfig.from_env()
        self._connection = None
        
    def connect(self) -> None:
        """Establish connection to Milvus."""
        try:
            from pymilvus import connections
            
            connection_params = self.config.to_connection_params()
            connections.connect(alias="default", **connection_params)
            self._connection = connections
            print(f"Connected to Milvus at {self.config.host}:{self.config.port}")
            
        except ImportError:
            raise ImportError("pymilvus is required. Install it with: pip install pymilvus")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Milvus: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from Milvus."""
        if self._connection:
            self._connection.disconnect(alias="default")
            self._connection = None
            print("Disconnected from Milvus")
    
    def is_connected(self) -> bool:
        """Check if connected to Milvus."""
        try:
            from pymilvus import connections
            return connections.has_connection("default")
        except ImportError:
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Default configuration instance
default_config = MilvusConfig.from_env()


def get_connection(config: Optional[MilvusConfig] = None) -> MilvusConnection:
    """Get a Milvus connection instance."""
    return MilvusConnection(config or default_config)


def test_connection(config: Optional[MilvusConfig] = None) -> bool:
    """Test connection to Milvus."""
    try:
        with get_connection(config) as conn:
            return conn.is_connected()
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False