# CLAUDE.md

## Project Overview
Python 3.9 MCP RAG playground with SOLID vector database client, RAG API, and MCP server integration.

## Key Structure
- `mcp_rag_playground/` - Main package
  - `vectordb/` - Vector DB abstractions + Milvus implementation
  - `rag/` - High-level RAG API (`rag_api.py`)
  - `mcp/` - MCP server (`rag_server.py` - module-level FastMCP)
  - `config/` - Milvus config + logging
  - `container/` - DI container (production-focused)
  - `tests/` - Pytest with fixtures, markers, coverage
- `vectordb/milvus/docker-compose.yml` - Local Milvus setup

## Current Implementation Status

### What Works
- **Core classes**: `VectorClient`, `RagAPI`, `MilvusVectorDB`, `SentenceTransformerEmbedding`
- **MCP Server**: Module-level FastMCP with 4 tools (add file/content, search, delete)  
- **DI Container**: Basic production container only
- **Testing**: Pytest fixtures, comprehensive markers

### Missing/Broken
- **No factory functions**: No `create_rag_api()`, `create_vector_client()` etc.
- **No examples directory**
- **Broken imports**: `RagMCPServer` imported but doesn't exist as class
- **Container exports**: No public factory functions exported

## Quick Usage (Current Reality)

### Direct Class Usage
```python
from mcp_rag_playground import RagAPI, VectorClient, MilvusVectorDB
from mcp_rag_playground.container.container import Container

# Manual instantiation
container = Container()
rag_api = container.rag_api()
vector_client = container.vector_client()
```

### MCP Server
```python
# Module is direct FastMCP, not a class
# Run: python -m mcp_rag_playground.mcp.rag_server
```

### Testing
```bash
pytest  # Uses pytest.ini config with coverage
pytest -m "not slow"  # Skip slow tests
```

## Commands
```bash
# Setup
pip install -e .
cd vectordb/milvus && docker-compose up -d

# Tests 
pytest mcp_rag_playground/tests/
pytest -m "unit" -v
```

## File Types Supported
15+ types: `.txt`, `.md`, `.py`, `.json`, `.js`, `.ts`, `.css`, `.html`, `.yml`, `.yaml`, `.log`

## Architecture
SOLID-compliant with dependency injection, abstract interfaces, 800-char chunking, score filtering.