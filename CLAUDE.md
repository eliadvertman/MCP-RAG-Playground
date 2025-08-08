# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "mcp_rag_playground" set up as an IntelliJ IDEA project with a Python 3.9 virtual environment.

## Project Structure

- `venv/` - Python 3.9 virtual environment (activated via `venv/Scripts/activate` on Windows or `source venv/bin/activate` on Unix)
- `mcp_rag_playground/` - Main Python package containing project modules
  - `vector_client.py` - Main vector database client with upload() and query() methods
  - `vectordb/` - Vector database implementations and interfaces
    - `vector_db_interface.py` - Abstract interface for vector databases (SOLID compliance)
    - `milvus_client.py` - Milvus-specific implementation
    - `document_processor.py` - Generic document processing with multiple file type support
    - `embedding_service.py` - Embedding service abstractions (sentence-transformers, mock)
  - `config/` - Configuration management
    - `milvus_config.py` - Milvus connection configuration
    - `milvus_connection.py` - Milvus connection manager
  - `container/` - Dependency injection container
    - `container.py` - Main DI container implementation
    - `config.py` - Configuration provider interfaces
    - `providers.py` - Service provider implementations
    - `factory.py` - Convenience factory methods
  - `rag/` - High-level RAG API
    - `rag_api.py` - Main RAG API with simplified add_documents and query methods
    - `__init__.py` - RAG module exports
  - `mcp/` - MCP (Model Context Protocol) integration
    - `rag_server.py` - MCP server wrapping RAG API functionality
    - `__init__.py` - MCP module exports
  - `tests/` - Test suite with dedicated test data
    - `test_vector_client.py` - Comprehensive test script for vector client
    - `test_milvus_config.py` - Test script for Milvus configuration  
    - `test_milvus_func.py` - End-to-end Milvus functionality tests
    - `test_rag_api.py` - RAG API functionality tests
    - `test_mcp_server.py` - MCP server functionality tests
    - `test_utils.py` - Shared test utilities and helper functions
    - `test_data/` - Dedicated test data files
      - `test_document.md` - Markdown test content
      - `test_document.txt` - Plain text test content
      - `test_module.py` - Python module test content
      - `test_config.json` - Test configuration parameters
- `examples/` - Usage examples and demonstration scripts
  - `rag_usage_example.py` - Comprehensive RAG API usage examples
  - `mcp_server_example.py` - MCP server implementation and usage example
- `vectordb/milvus/` - Milvus vector database Docker setup
- `vectordb/milvus/docker-compose.yml` - Docker Compose configuration for running Milvus locally

## Development Environment

- **Python Version**: 3.9.13
- **Virtual Environment**: Located in `venv/` directory
- **IDE**: IntelliJ IDEA project setup
- **Vector Database**: Milvus (configured for Docker deployment)

## Dependencies

- `pymilvus>=2.4.0` - Python SDK for Milvus vector database
- `sentence-transformers>=2.2.0` - Embedding models for text vectorization
- `mcp[cli]>=1.2.0` - Model Context Protocol SDK for MCP server implementation

## Common Commands

To activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Unix/Linux/macOS
source venv/bin/activate
```

To install dependencies:
```bash
pip install -r requirements.txt

# For MCP server compatibility, install project in editable mode
pip install -e .
```

To start Milvus vector database:
```bash
cd vectordb/milvus
docker-compose up -d
```

To test Milvus configuration:
```bash
python test_milvus_config.py
```

To test the vector client:
```bash
python -m mcp_rag_playground.tests.test_vector_client
```

To test the RAG API:
```bash
python -m mcp_rag_playground.tests.test_rag_api
```

To run the RAG API example:
```bash
python examples/rag_usage_example.py
```

To run the MCP server in development mode:
```bash
uv run mcp dev examples/mcp_server_example.py
```

To run the MCP server in production mode:
```bash
python examples/mcp_server_production.py
```

To test the MCP server:
```bash
python -m mcp_rag_playground.tests.test_mcp_server
```

## MCP Server Deployment

**IMPORTANT**: Before running MCP commands, ensure the project is installed in editable mode:
```bash
pip install -e .
```

This is required for the MCP server to properly access project dependencies when using `uv run mcp install` or similar commands.

For comprehensive deployment instructions including Claude Desktop integration, see the **[MCP Deployment Guide](docs/MCP_DEPLOYMENT_GUIDE.md)**.

## Usage Examples

### RAG API Usage (Recommended for Most Use Cases)

#### Quick Start with RAG API

```python
from mcp_rag_playground import create_rag_api

# Create a RAG API instance
rag_api = create_rag_api("dev")

# Add documents from files
file_result = rag_api.add_documents(["doc1.txt", "doc2.md", "doc3.py"])
print(f"Uploaded {file_result['summary']['successful']} files")

# Add documents from raw content
content_result = rag_api.add_documents([
    {
        "content": "Python is a versatile programming language",
        "metadata": {"source": "programming_guide", "topic": "python"}
    },
    {
        "content": "Machine learning enables computers to learn from data",
        "metadata": {"source": "ml_intro", "topic": "ai"}
    }
])

# Query for relevant documents
results = rag_api.query("Python programming", limit=5, min_score=0.7)
for result in results:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content']}")
    print(f"Source: {result['source']}")
```

#### Mixed Input (Files + Content)

```python
# Add both files and content in a single call
mixed_documents = [
    "document.pdf",  # File path
    {
        "content": "Inline content about vector databases",
        "metadata": {"source": "inline", "type": "educational"}
    },
    "another_file.txt"  # Another file path
]

result = rag_api.add_documents(mixed_documents)
print(f"Success rate: {result['summary']['success_rate']:.1%}")
```

### Advanced Vector Client Usage

#### Using Dependency Injection (Lower Level)

```python
from mcp_rag_playground import create_vector_client

# Create a client for development environment
client = create_vector_client("dev")

# Upload a file
success = client.upload("path/to/document.txt")

# Query for similar content with score filtering
results = client.query("your search query", limit=5, min_score=0.75)
for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.document.content}")

# Query preprocessing handles abbreviations automatically
results = client.query("vector db search")  # Expands "db" to "database"
```

#### Manual Construction (Advanced)

```python
from mcp_rag_playground import VectorClient, MilvusVectorDB, SentenceTransformerEmbedding, DocumentProcessor

# Initialize components manually
embedding_service = SentenceTransformerEmbedding()
vector_db = MilvusVectorDB()
doc_processor = DocumentProcessor()
client = VectorClient(vector_db, embedding_service, doc_processor)

# Upload a file
success = client.upload("path/to/document.txt")
```

#### Environment-Specific Clients

```python
from mcp_rag_playground import create_test_container, create_prod_container

# Test environment (uses mock services)
test_client = create_test_container().get("vector_client")

# Production environment (uses real services)
prod_client = create_prod_container().get("vector_client")
```

### MCP Server Usage (Model Context Protocol Integration)

#### Creating an MCP Server

```python
from mcp_rag_playground import create_rag_mcp_server, create_mock_rag_mcp_server

# Create MCP server for development (uses mock services)
mcp_server = create_mock_rag_mcp_server("demo_knowledge_base")

# Create MCP server for production
mcp_server = create_rag_mcp_server("prod", "production_knowledge_base")

# Get the FastMCP instance for integration
fastmcp_instance = mcp_server.get_server()
```

#### MCP Tools Available

1. **add_document_from_file**: Add documents from file paths
2. **add_document_from_content**: Add documents from raw content  
3. **search_knowledge_base**: Search for relevant documents
4. **get_collection_info**: Get knowledge base statistics
5. **delete_collection**: Remove all documents (⚠️ destructive)

#### MCP Resources Available

1. **rag://collection/info**: Collection information
2. **rag://search/{query}**: Search results for a query

#### MCP Prompts Available

1. **rag_search_prompt**: Generate context-aware prompts for Q&A

#### Running the MCP Server

```bash
# Development mode with MCP inspector
uv run mcp dev examples/mcp_server_example.py

# Use with Claude Desktop (add to configuration)
# ~/.config/claude-desktop/mcp_servers.json:
{
  "mcpServers": {
    "rag-knowledge-base": {
      "command": "uv",
      "args": ["run", "mcp", "dev", "/path/to/examples/mcp_server_example.py"]
    }
  }
}
```

### Supported File Types

The DocumentProcessor supports multiple file types:
- `.txt` - Plain text files
- `.md`, `.markdown` - Markdown files  
- `.py` - Python source files
- `.json` - JSON files
- `.js`, `.ts` - JavaScript/TypeScript files
- `.css`, `.html`, `.xml` - Web files
- `.yml`, `.yaml`, `.toml`, `.ini` - Configuration files
- `.log` - Log files

## Current State

The project has been implemented with:
- **MCP Server integration** with Model Context Protocol support for LLM integration
- **High-level RAG API** with simplified document ingestion and querying interface
- **SOLID-compliant vector database client** with abstract interfaces
- **Enhanced search accuracy** with score filtering and query preprocessing
- **Generic document processor** supporting 15+ file types with optimized chunking
- **Milvus vector database integration** with configuration management
- **Embedding service abstraction** (sentence-transformers + mock for testing)
- **Dependency injection container** with comprehensive debugging support
- **Environment-aware configuration** (test, dev, prod)
- **Comprehensive test suite** for validation
- **Docker Compose setup** for local Milvus deployment
- **Examples and demonstrations** showing complete usage patterns

### Recent Enhancements (Latest)

- **Connection Testing and Server Reliability (Latest)**:
  - Added `test_connection()` method to `VectorDBInterface` abstract class for consistent connection testing across implementations
  - Implemented connection testing in `MilvusVectorDB` with proper error handling and logging
  - Added `MockVectorDB` class for testing and development environments
  - Enhanced `VectorClient` with connection testing capability that delegates to underlying vector database
  - **Critical MCP Server Enhancement**: Added connection testing during MCP server startup with fail-fast behavior
  - MCP server now terminates gracefully if vector database connection fails, preventing startup with broken connections
  - Improved server reliability and debugging with detailed connection status logging

- **MCP Server Bug Fixes**:
  - Fixed critical bug in MCP server where RAG API was accessed incorrectly as configuration instead of service
  - Updated MCP tools (`add_document_from_file`, `add_document_from_content`, `search_knowledge_base`) to properly access RAG API from dependency injection container
  - Enhanced logging in Milvus connection manager for better debugging of connection issues
  - Improved error handling and type hints in MCP server tools

- **MCP Server Integration**:
  - Complete `RagMCPServer` implementation wrapping RAG API functionality
  - 5 MCP tools: document addition (file/content), search, collection info, deletion
  - 2 MCP resources: collection info and search results access
  - 1 MCP prompt: context-aware RAG question answering
  - Factory functions `create_rag_mcp_server()` and `create_mock_rag_mcp_server()`
  - MCP server example and comprehensive test coverage
  - **Claude Desktop Configuration**: Updated deployment guide for proper virtual environment usage

- **High-Level RAG API**:
  - Simplified `RagAPI` class with user-friendly `add_documents` and `query` methods
  - Support for mixed document input (files, raw content, or both)
  - Enhanced result formatting with comprehensive metadata
  - Collection management operations (info, deletion)
  - Factory functions `create_rag_api()` and `create_mock_rag_api()` for easy setup

- **Examples and Documentation**:
  - Comprehensive usage examples in `examples/rag_usage_example.py`
  - MCP server example with development and production configurations
  - Step-by-step demonstrations of all RAG API and MCP features
  - Test coverage for RAG API and MCP server functionality
  - Updated documentation with new patterns and usage

- **Search Accuracy Improvements**:
  - Score threshold filtering (`min_score` parameter) to filter low-quality results
  - Query preprocessing with abbreviation expansion (db→database, ai→artificial intelligence)
  - Optimized chunking strategy (800 chars with 200 char overlap)
  - Enhanced test coverage for search quality validation

- **Dependency Injection Debugging**:
  - Comprehensive logging for service registration and instantiation
  - Instance lifecycle tracking (creation, caching, reuse)
  - Dependency resolution visibility with detailed debug output

- **Test Infrastructure Improvements**:
  - Modular test organization with extracted utility functions
  - Shared test helpers in `test_utils.py` for better code reuse
  - Dedicated end-to-end tests in `test_milvus_func.py`
  - Improved test maintainability and reduced code duplication

### Architecture Highlights

- **Single Responsibility**: Each class has a focused purpose
- **Open/Closed**: Easy to extend with new vector DBs or file processors
- **Liskov Substitution**: Implementations are interchangeable via interfaces
- **Interface Segregation**: Clean, minimal interfaces
- **Dependency Inversion**: Depends on abstractions, not concretions

## Workflow

1. First think through the problem, read the codebase for relevant files, and write a plan to tasks/todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Every step of the way just give me a high level explanation of what changes you made.
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Make sure to not create large Python files. Follow SOLID principles to break big components into smaller ones.
8. Once finished, add the generated files to git staging.
9. Finally, add a review section to the todo.md file with a summary of the changes you made and any other relevant information.