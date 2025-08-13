# Source Tree and Module Organization

### Project Structure (Actual)

```text
mcp_rag_playground/
├── mcp_rag_playground/           # Main package
│   ├── __init__.py              # Conditional MCP imports, no factory functions
│   ├── config/                  # Configuration classes
│   │   ├── logging_config.py    # Logger setup
│   │   └── milvus_config.py     # Milvus connection config
│   ├── container/               # Dependency injection
│   │   └── container.py         # Production-only DI container  
│   ├── mcp/                     # MCP Server integration
│   │   └── rag_server.py        # Module-level FastMCP with 4 tools
│   ├── rag/                     # High-level RAG interface
│   │   └── rag_api.py           # Main RAG API class
│   ├── vectordb/                # Vector database abstractions
│   │   ├── vector_client.py     # Main vector client
│   │   ├── vector_db_interface.py # Abstract interfaces
│   │   ├── embedding_service.py # SentenceTransformer embedding
│   │   ├── milvus/             # Milvus-specific implementation
│   │   │   ├── milvus_client.py # MilvusVectorDB implementation
│   │   │   └── milvus_connection.py # Connection utilities
│   │   └── processor/          # Document processing
│   │       ├── document_processor.py # Chunking (800 chars, 200 overlap)
│   │       └── file_processor.py     # 15+ file type support
│   └── tests/                   # Comprehensive test suite
│       ├── conftest.py          # Pytest configuration
│       ├── fixtures/            # Test fixtures organized by concern
│       ├── test_data/           # Sample files for testing
│       └── test_*.py            # Test files with markers
├── docs/                        # Documentation
│   ├── prd.md                   # Enhancement PRD (Stories 1.1-1.6)
│   └── [other docs]
├── vectordb/milvus/             # Infrastructure
│   └── docker-compose.yml       # Local Milvus setup
├── pyproject.toml               # Project configuration
├── pytest.ini                  # Test configuration with markers
└── CLAUDE.md                    # Project instructions for AI agents
```

### Key Modules and Their Purpose

- **RagAPI** (`rag/rag_api.py`): High-level RAG interface, thin wrapper over VectorClient
- **VectorClient** (`vectordb/vector_client.py`): Main orchestrator, uses DI pattern
- **MilvusVectorDB** (`vectordb/milvus/milvus_client.py`): Concrete Milvus implementation
- **Container** (`container/container.py`): Production DI container, no factory functions exported
- **MCP Server** (`mcp/rag_server.py`): Module-level FastMCP with **6 tools** (verified), path normalization for WSL
