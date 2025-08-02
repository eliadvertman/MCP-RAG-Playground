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
  - `tests/` - Test suite with dedicated test data
    - `test_vector_client.py` - Comprehensive test script for vector client
    - `test_milvus_config.py` - Test script for Milvus configuration
    - `test_data/` - Dedicated test data files
      - `test_document.md` - Markdown test content
      - `test_document.txt` - Plain text test content
      - `test_module.py` - Python module test content
      - `test_config.json` - Test configuration parameters
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

## Usage Examples

### Basic Vector Client Usage

#### Using Dependency Injection (Recommended)

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
- **SOLID-compliant vector database client** with abstract interfaces
- **Enhanced search accuracy** with score filtering and query preprocessing
- **Generic document processor** supporting 15+ file types with optimized chunking
- **Milvus vector database integration** with configuration management
- **Embedding service abstraction** (sentence-transformers + mock for testing)
- **Dependency injection container** with comprehensive debugging support
- **Environment-aware configuration** (test, dev, prod)
- **Comprehensive test suite** for validation
- **Docker Compose setup** for local Milvus deployment

### Recent Enhancements (Latest)

- **Search Accuracy Improvements**:
  - Score threshold filtering (`min_score` parameter) to filter low-quality results
  - Query preprocessing with abbreviation expansion (db→database, ai→artificial intelligence)
  - Optimized chunking strategy (800 chars with 200 char overlap)
  - Enhanced test coverage for search quality validation

- **Dependency Injection Debugging**:
  - Comprehensive logging for service registration and instantiation
  - Instance lifecycle tracking (creation, caching, reuse)
  - Dependency resolution visibility with detailed debug output

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
5. Every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Make sure to not create large Python files. Follow SOLID principles to break big components to smaller ones.
8. Once finished, add the new files to git staging
9. Finally, add a review section to the todo.md file with a summary of the changes you made and any other relevant information.