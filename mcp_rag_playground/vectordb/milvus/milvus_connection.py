from typing import Optional

from mcp_rag_playground.config.logging_config import get_logger
from mcp_rag_playground.config.milvus_config import MilvusConfig

logger = get_logger(__name__)

class MilvusConnection:
    """Milvus connection manager."""

    def __init__(self, config: Optional[MilvusConfig] = None):
        logger.info(f"Initializing MilvusConnection with config: {config is not None}")
        self.config = config or MilvusConfig.from_env()
        logger.info(f"Using Milvus config - host: {self.config.host}, port: {self.config.port}")
        self._connection = None

    def connect(self) -> None:
        """Establish connection to Milvus."""
        logger.info(f'Connecting to MilvusDB at {self.config.host}:{self.config.port}')
        try:
            from pymilvus import connections

            connection_params = self.config.to_connection_params()
            logger.info(f"Connection parameters: {connection_params}")
            
            connections.connect(alias="default", **connection_params)
            self._connection = connections
            logger.info("Successfully connected to Milvus")
            # Note: Connection successful but avoiding stdout print to prevent MCP JSON interference

        except ImportError as e:
            logger.error("pymilvus library not found")
            raise ImportError("pymilvus is required. Install it with: pip install pymilvus")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            logger.debug(f"Connection attempt failed with params: {self.config.to_connection_params()}")
            raise ConnectionError(f"Failed to connect to Milvus: {e}")

    def disconnect(self) -> None:
        """Disconnect from Milvus."""
        if self._connection:
            logger.info(f'Disconnecting to MilvusDB')
            self._connection.disconnect(alias="default")
            self._connection = None
            # Note: Disconnection successful but avoiding stdout print to prevent MCP JSON interference

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
