"""
Dependency injection container for MCP RAG Playground.
Uses dependency-injector library for clean, simple DI.
"""

# Import new dependency-injector based implementation
from .container import (
    Container,
    create_vector_client,
    create_rag_api,
    create_prod_vector_client,
    create_prod_rag_api
)


__all__ = [
    # Core container
    'Container',
    
    # Main factory functions
    'create_vector_client',
    'create_rag_api',
    
    # Environment-specific functions
    'create_prod_vector_client',
    'create_prod_rag_api',
]