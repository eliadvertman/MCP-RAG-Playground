# MCP RAG Playground

A SOLID-compliant vector database client with RAG capabilities, featuring dependency injection and environment-aware configuration.

## Features

- **SOLID-compliant architecture** with abstract interfaces and dependency injection
- **Multiple vector database support** (currently Milvus, easily extensible)
- **Generic document processing** supporting 15+ file types
- **Environment-aware configuration** (test, dev, prod)
- **Comprehensive embedding service abstraction** (sentence-transformers + mock for testing)
- **Dependency injection container** for clean service management
- **Docker-based Milvus deployment** for local development

## Quick Start

### Using Dependency Injection (Recommended)

```python
from mcp_rag_playground import create_vector_client

# Create a client for development environment
client = create_vector_client("dev")

# Upload a file
success = client.upload("path/to/document.txt")

# Query for similar content
results = client.query("your search query", limit=5)
for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.document.content}")
```

### Environment-Specific Usage

```python
from mcp_rag_playground import create_test_container, create_prod_container

# Test environment (uses mock services)
test_client = create_test_container().get("vector_client")

# Production environment (uses real services)
prod_client = create_prod_container().get("vector_client")
```

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Start Milvus: `cd vectordb/milvus && docker-compose up -d`
4. Run tests: `python -m mcp_rag_playground.tests.test_vector_client`

## Supported File Types

- `.txt` - Plain text files
- `.md`, `.markdown` - Markdown files  
- `.py` - Python source files
- `.json` - JSON files
- `.js`, `.ts` - JavaScript/TypeScript files
- `.css`, `.html`, `.xml` - Web files
- `.yml`, `.yaml`, `.toml`, `.ini` - Configuration files
- `.log` - Log files

## Architecture

The project follows SOLID principles with:

- **Single Responsibility**: Each class has a focused purpose
- **Open/Closed**: Easy to extend with new vector DBs or file processors
- **Liskov Substitution**: Implementations are interchangeable via interfaces
- **Interface Segregation**: Clean, minimal interfaces
- **Dependency Inversion**: Depends on abstractions, not concretions

## MCP Integration Opportunities

This foundation supports future MCP (Model Context Protocol) integration:

- **File System Access**: Direct document ingestion from file system
- **Database Queries**: Real-time data retrieval and indexing
- **Web Search**: Knowledge base augmentation with current information
- **External APIs**: Integration with productivity tools and services