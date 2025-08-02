from typing import Optional

from mcp_rag_playground.config.milvus_config import MilvusConfig


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
