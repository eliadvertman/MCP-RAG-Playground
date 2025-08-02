#!/usr/bin/env python3
"""
Test script for Milvus configuration.
"""

from mcp_rag_playground.config.milvus_config import MilvusConfig, test_connection


def main():
    """Test the Milvus configuration setup."""
    print("Testing Milvus Configuration...")
    print("-" * 40)
    
    # Test default configuration
    config = MilvusConfig.from_env()
    print(f"Default config: {config.host}:{config.port}")
    
    # Test connection parameters
    params = config.to_connection_params()
    print(f"Connection params: {params}")
    
    # Test connection (requires Milvus to be running)
    print("\nTesting connection...")
    if test_connection(config):
        print("✓ Connection successful!")
    else:
        print("✗ Connection failed (ensure Milvus is running)")
    
    print("\nConfiguration test completed.")


if __name__ == "__main__":
    main()