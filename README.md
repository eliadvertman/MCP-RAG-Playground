# MCP RAG Playground

A SOLID-compliant vector database client with RAG capabilities and MCP server integration, featuring enhanced search accuracy, dependency injection and environment-aware configuration.

## Features

- **MCP Server integration** - Model Context Protocol support for seamless LLM integration
- **Enhanced Document Metadata Tracking** - Comprehensive tracking of document lifecycle (filename, type, ingestion timestamp, chunk count, file size, chunk position, vector ID, embedding status)
- **High-level RAG API** with simplified `add_documents` and `query` methods supporting mixed input types
- **SOLID-compliant architecture** with abstract interfaces and dependency injection  
- **Enhanced search accuracy** with score filtering and query preprocessing
- **Multiple vector database support** (currently Milvus, easily extensible)
- **Intelligent document processing** supporting 15+ file types with optimized chunking
- **Flexible document input** - support for files, raw content, or mixed input in single call
- **Environment-aware configuration** (test, dev, prod)
- **Comprehensive embedding service abstraction** (sentence-transformers + mock for testing)
- **Dependency injection container** with debugging support for clean service management
- **Docker-based Milvus deployment** for local development
- **Comprehensive test suite** with pytest fixtures and markers

## Quick Start

### Using RAG API (Recommended)

```python
from mcp_rag_playground import RagAPI
from mcp_rag_playground.container.container import Container

# Create a RAG API instance using dependency injection
container = Container()
rag_api = container.rag_api()

# Add documents from files
file_result = rag_api.add_documents(["doc1.txt", "doc2.md"])
print(f"Uploaded {file_result['summary']['successful']} files")

# Add documents from raw content
content_result = rag_api.add_documents([
    {
        "content": "Python is a versatile programming language",
        "metadata": {"source": "guide", "topic": "python"}
    }
])

# Mix files and content in single call
mixed_result = rag_api.add_documents([
    "document.pdf",  # File path
    {
        "content": "Vector databases enable semantic search",
        "metadata": {"source": "inline", "type": "educational"}
    }
])

# Query for relevant documents
results = rag_api.query("Python programming", limit=5, min_score=0.7)
for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Content: {result['content'][:100]}...")
    print(f"Source: {result['source']}")
```

### Using Vector Client (Lower Level)

```python
from mcp_rag_playground import VectorClient
from mcp_rag_playground.container.container import Container

# Create a vector client using dependency injection
container = Container()
client = container.vector_client()

# Upload a file
success = client.upload("path/to/document.txt")

# Query for similar content with quality filtering
results = client.query("your search query", limit=5, min_score=0.75)
for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.document.content}")
```

### Using MCP Server (LLM Integration)

The MCP server is implemented as a module-level FastMCP application:

**Run MCP Server:**
```bash
# Run the MCP server directly
python -m mcp_rag_playground.mcp.rag_server

# Or use with uv for development
uv run python -m mcp_rag_playground.mcp.rag_server
```

**Available MCP Tools:**
- `add_document_from_file(file_path)` - Add documents from file paths
- `add_document_from_content(content, metadata)` - Add documents from raw content
- `search_knowledge_base(query, limit, min_score)` - Search for relevant documents
- `get_document_metadata(document_id)` - Retrieve comprehensive metadata for a specific document
- `list_documents_with_metadata(limit, file_type_filter)` - List all documents with metadata and statistics
- `delete_collection()` - Remove all documents (⚠️ destructive)

**Claude Desktop Integration:**
```json
{
  "mcpServers": {
    "rag-kb": {
      "command": "/absolute/path/to/venv/Scripts/python.exe",
      "args": ["-m", "mcp_rag_playground.mcp.rag_server"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/project"
      }
    }
  }
}
```

### Manual Component Construction

```python
from mcp_rag_playground import (
    VectorClient, RagAPI, MilvusVectorDB, 
    SentenceTransformerEmbedding, MilvusConfig
)
from mcp_rag_playground.vectordb.processor.document_processor import DocumentProcessor

# Manual construction for custom configurations
config = MilvusConfig(host="localhost", port=19530, collection_name="my_collection")
vector_db = MilvusVectorDB(config=config)
embedding_service = SentenceTransformerEmbedding(model_name="all-MiniLM-L6-v2")
document_processor = DocumentProcessor(chunk_size=800, overlap=200)

# Create vector client
vector_client = VectorClient(
    vector_db=vector_db,
    embedding_service=embedding_service,
    document_processor=document_processor,
    collection_name="my_collection"
)

# Create RAG API
rag_api = RagAPI(vector_client=vector_client, collection_name="my_collection")
```

## Installation

1. Clone the repository
2. **Install project in editable mode (required for MCP server)**: `pip install -e .`
3. Start Milvus: `cd vectordb/milvus && docker-compose up -d`
4. Run tests: 
   - All tests: `pytest`
   - Unit tests only: `pytest -m "unit"`
   - Skip slow tests: `pytest -m "not slow"`
   - Specific test files: `pytest mcp_rag_playground/tests/test_vector_client.py`
5. Try the MCP server: `python -m mcp_rag_playground.mcp.rag_server`

## 🚀 MCP Server Deployment & Claude Desktop Integration

For detailed instructions on deploying the MCP server locally and integrating it with Claude Desktop, see our comprehensive **[MCP Deployment Guide](docs/MCP_DEPLOYMENT_GUIDE.md)**.

The guide covers:
- **Local deployment** with step-by-step setup
- **Claude Desktop integration** configuration
- **Production deployment** with real vector database
- **Troubleshooting** common issues
- **Advanced configuration** and optimization
- **Usage examples** and best practices

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

## Search Quality Features

### Score Filtering
Filter results by similarity score to ensure quality:
```python
# Only return highly relevant results (recommended: 0.7-0.8)
results = client.query("search term", min_score=0.75)
```

### Query Preprocessing
Automatic query enhancement for better results:
- **Abbreviation expansion**: `db` → `database`, `ai` → `artificial intelligence`
- **Normalization**: Whitespace cleanup and lowercasing
- **Special character handling**: Removes noise that interferes with search

### Optimized Chunking
- **Chunk size**: 800 characters (optimal for semantic coherence)
- **Overlap**: 200 characters (ensures context preservation)
- **Smart boundaries**: Splits at paragraphs, sentences, or word boundaries

## Testing

The project includes comprehensive testing with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_rag_playground

# Run specific test categories
pytest -m "unit"           # Unit tests only
pytest -m "integration"    # Integration tests
pytest -m "not slow"       # Skip slow tests
pytest -m "milvus"         # Tests requiring Milvus

# Run specific test files
pytest mcp_rag_playground/tests/test_vector_client.py
pytest mcp_rag_playground/tests/test_embedding_service.py
```

### Test Organization

- **Unit Tests**: Fast, isolated tests with mocks
- **Integration Tests**: Tests with real Milvus and embedding models  
- **Fixtures**: Organized in `mcp_rag_playground/tests/fixtures/`
- **Markers**: Comprehensive test categorization system
- **Coverage**: Target 80% minimum coverage