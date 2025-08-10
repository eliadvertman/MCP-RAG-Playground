# MCP RAG Playground Brownfield Architecture Document

## Introduction

This document captures the CURRENT STATE of the MCP RAG Playground codebase, including technical debt, workarounds, and real-world patterns. It serves as a reference for AI agents working on the Enhanced Document Lifecycle Management enhancements.

### Document Scope

Focused on areas relevant to: **Enhanced Document Lifecycle Management** (document metadata tracking, smart processing pipelines, REST API layer, comprehensive dashboard, and integration capabilities)

### Change Log

| Date       | Version | Description                 | Author           |
| ---------- | ------- | --------------------------- | ---------------- |
| 2025-08-10 | 1.0     | Initial brownfield analysis | Winston Architect |

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

- **Main Entry**: `mcp_rag_playground/__init__.py` (conditional MCP imports)
- **Configuration**: `mcp_rag_playground/config/milvus_config.py`, no `.env.example` yet
- **Core Business Logic**: `mcp_rag_playground/rag/rag_api.py` (high-level), `mcp_rag_playground/vectordb/vector_client.py` (low-level)
- **MCP Server**: `mcp_rag_playground/mcp/rag_server.py` (module-level FastMCP)
- **Database Models**: Vector operations via `mcp_rag_playground/vectordb/milvus/milvus_client.py`
- **DI Container**: `mcp_rag_playground/container/container.py` (production-focused only)

### Enhancement Impact Areas (Per PRD Stories 1.1-1.6)

**Story 1.1 (Metadata Tracking Foundation)**:
- `mcp_rag_playground/vectordb/milvus/milvus_client.py` - Need metadata storage extension
- `mcp_rag_playground/vectordb/vector_db_interface.py` - Document model enhancement
- `mcp_rag_playground/vectordb/vector_client.py` - Metadata tracking integration

**Story 1.2 (Document Management Operations)**:
- `mcp_rag_playground/rag/rag_api.py` - Enhanced add/remove with metadata
- `mcp_rag_playground/mcp/rag_server.py` - MCP tools enhancement
- New: Batch operations interface

**Story 1.3 (Smart Processing Pipeline)**:
- `mcp_rag_playground/vectordb/processor/document_processor.py` - Smart categorization
- `mcp_rag_playground/vectordb/embedding_service.py` - Duplicate detection
- New: `mcp_rag_playground/processing/` module

**Story 1.4 (Enhanced Q&A Interface)**:
- `mcp_rag_playground/rag/rag_api.py` - Natural language interface
- `mcp_rag_playground/mcp/rag_server.py` - Enhanced search tools
- New: Source attribution system

**Story 1.5 (Tracking Dashboard)**:
- New: `mcp_rag_playground/api/` module for REST endpoints
- New: Dashboard web interface (optional deployment)

**Story 1.6 (Integration & Export)**:
- New: `mcp_rag_playground/api/` module expansion
- New: Export functionality across multiple formats

## High Level Architecture

### Technical Summary

**Current Reality**: Python 3.9+ MCP RAG system with SOLID-compliant vector database client, production DI container, and module-level FastMCP server. Missing factory functions and examples directory.

### Actual Tech Stack (from pyproject.toml)

| Category            | Technology              | Version | Notes                                    |
| ------------------- | ----------------------- | ------- | ---------------------------------------- |
| Runtime             | Python                  | >=3.12  | CLAUDE.md says 3.9, pyproject.toml 3.12 |
| DI Framework        | dependency-injector     | 4.48.1+ | Production-focused container only        |
| Vector Database     | Milvus via pymilvus     | 2.4.0+  | Docker-compose local setup               |
| Embeddings          | sentence-transformers   | 2.2.0+  | "all-MiniLM-L6-v2" model                |
| MCP Protocol        | mcp[cli]                | 1.12.4  | Module-level FastMCP server             |
| Configuration       | pydantic                | 2.11.7+ | Type-safe config objects                |
| Environment         | python-dotenv           | 1.1.1+  | For environment variable loading         |
| Testing             | pytest + pytest-cov    | 7.0.0+  | 80% coverage target, comprehensive marks |
| AI Models           | huggingface-hub[hf-xet] | 0.34.3+ | Model downloading and caching            |

### Repository Structure Reality Check

- **Type**: Single package monorepo
- **Package Manager**: pip/uv (uv.lock present)
- **Notable**: Missing `examples/` directory, factory functions exist only in container

## Source Tree and Module Organization

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
- **MCP Server** (`mcp/rag_server.py`): Module-level FastMCP with 4 tools, path normalization for WSL

## Technical Debt and Known Issues

### Critical Technical Debt

1. **Missing Factory Functions**: No `create_rag_api()`, `create_vector_client()` functions - only container-based instantiation
2. **Container Exports**: Production container not properly exported, manual instantiation required
3. **Broken Imports**: CLAUDE.md mentions `RagMCPServer` class that doesn't exist (it's module-level)
4. **No Examples Directory**: Missing practical usage examples for developers
5. **Python Version Mismatch**: CLAUDE.md says 3.9, pyproject.toml requires 3.12+

### Workarounds and Gotchas

- **MCP Server Architecture**: It's a module-level FastMCP app, not a class-based server
- **Path Normalization**: WSL path conversion logic in rag_server.py for cross-platform compatibility
- **Collection Naming**: Two collection names - vector_client uses "prod_kb_collection", rag_api uses "prod_collection"
- **Conditional MCP**: Graceful degradation when MCP dependencies unavailable

## Data Models and APIs

### Data Models

**Current Models** (see `vectordb/vector_db_interface.py`):
- **Document**: Content + metadata structure
- **SearchResult**: Document + similarity score
- **MilvusConfig**: Connection and collection configuration

### MCP API Specifications

**Available MCP Tools** (module-level in `mcp/rag_server.py`):
- `add_document_from_file(file_path)` - File ingestion with path normalization
- `add_document_from_content(content, metadata)` - Direct content ingestion
- `search_knowledge_base(query, limit, min_score)` - Semantic search with filtering
- `delete_collection()` - Destructive collection removal

## Extension Patterns and Architectural Conventions

### SOLID Principles Implementation

**Single Responsibility**: Each class focused - VectorClient (orchestration), MilvusVectorDB (storage), RagAPI (user interface)

**Open/Closed**: Abstract interfaces enable extension:
- `VectorDBInterface` - Add new vector databases
- `EmbeddingServiceInterface` - Add new embedding providers  
- `DocumentProcessor` - Extend file type support

**Liskov Substitution**: Implementations interchangeable via dependency injection

**Interface Segregation**: Clean, minimal interfaces prevent coupling

**Dependency Inversion**: All components depend on abstractions through DI container

### Extensibility Patterns for New Features

**1. Service Layer Extension Pattern**:
```python
# Existing pattern - extend through interfaces
class NewVectorDB(VectorDBInterface):
    def __init__(self, config): pass
    # Implement required methods

# Register in container
class Container(containers.DeclarativeContainer):
    new_vector_db = providers.Singleton(NewVectorDB, config=config)
```

**2. Processing Pipeline Extension Pattern**:
```python
# Extend document processing for smart features (Story 1.3)
class SmartDocumentProcessor(DocumentProcessor):
    def __init__(self, categorizer, duplicate_detector):
        super().__init__()
        self.categorizer = categorizer
        self.duplicate_detector = duplicate_detector
    
    def process(self, content: str) -> List[Document]:
        # Extend base processing with smart features
        docs = super().process(content)
        return self._apply_smart_processing(docs)
```

**3. API Layer Extension Pattern**:
```python
# Add REST API layer (Stories 1.5-1.6) without breaking MCP
class RestAPIServer:
    def __init__(self, rag_api: RagAPI):
        self.rag_api = rag_api  # Reuse existing business logic
        
    # Map REST endpoints to existing RagAPI methods
    def add_documents_endpoint(self): 
        return self.rag_api.add_documents()
```

**4. Metadata Extension Pattern**:
```python
# Extend Document model for metadata tracking (Story 1.1)
@dataclass
class EnhancedDocument(Document):
    ingestion_timestamp: datetime
    file_size: int
    chunk_count: int
    processing_status: str
    
    # Backward compatible with existing Document usage
```

### Container Extension Strategy

**Current Reality**: Single production container, no factory exports

**Extension Approach for New Features**:
```python
# Extend container without breaking existing code
class Container(containers.DeclarativeContainer):
    # Existing services remain unchanged
    rag_api = providers.Singleton(RagAPI, ...)
    
    # Add new services for enhancements
    metadata_tracker = providers.Singleton(MetadataTracker, ...)
    smart_processor = providers.Singleton(SmartProcessor, ...)
    rest_api_server = providers.Singleton(RestAPIServer, rag_api=rag_api)
```

## Integration Points and External Dependencies

### External Services

| Service       | Purpose            | Integration Type | Key Files                              |
| ------------- | ------------------ | ---------------- | -------------------------------------- |
| Milvus        | Vector Database    | pymilvus SDK     | `vectordb/milvus/milvus_client.py`     |
| HuggingFace   | Model Downloads    | huggingface-hub  | `vectordb/embedding_service.py`        |
| Docker/Milvus | Local Development  | docker-compose   | `vectordb/milvus/docker-compose.yml`   |

### Internal Integration Points

- **MCP Protocol**: FastMCP module-level server on default port
- **DI Container**: Production container with singleton services
- **File Processing**: 15+ file types through processor pipeline
- **Embedding Pipeline**: sentence-transformers with "all-MiniLM-L6-v2"

## Development and Deployment

### Local Development Setup (Working Steps)

1. `pip install -e .` (required for MCP server module imports)
2. `cd vectordb/milvus && docker-compose up -d` (start Milvus)
3. Test connection: `python -c "from mcp_rag_playground.container.container import Container; c = Container(); c.rag_api().vector_client.test_connection()"`
4. Run MCP server: `python -m mcp_rag_playground.mcp.rag_server`

### Build and Deployment Process

- **Build**: No build step, pure Python package
- **Testing**: `pytest` with comprehensive markers and 80% coverage target
- **MCP Deployment**: Module-level server, not class-based

## Testing Reality

### Current Test Coverage

- **Test Framework**: pytest with comprehensive markers system
- **Coverage Target**: 80% minimum (pytest-cov configuration)
- **Test Organization**: fixtures organized by concern, markers for different test types
- **Integration**: Real Milvus and embedding models for integration tests

### Test Markers System

```ini
slow: tests requiring external services (model downloads)
integration: tests with real components  
unit: isolated tests with mocks
milvus: tests requiring Milvus connection
embedding: tests using real embedding models
performance: performance benchmark tests
smoke: quick sanity checks
```

### Running Tests

```bash
pytest                    # All tests with coverage
pytest -m "unit"          # Fast unit tests only
pytest -m "not slow"      # Skip model downloads
pytest -m "integration"   # Full integration tests
```

## Enhancement PRD Impact Analysis

### Files That Will Need Modification

Based on Stories 1.1-1.6, these existing files will be enhanced:

**Story 1.1 (Metadata Foundation)**:
- `vectordb/vector_db_interface.py` - Extend Document model with metadata fields
- `vectordb/milvus/milvus_client.py` - Add metadata storage and querying
- `vectordb/vector_client.py` - Integrate metadata tracking in upload/query flows

**Story 1.2 (Document Management)**:
- `rag/rag_api.py` - Enhanced add_documents with metadata, batch operations
- `mcp/rag_server.py` - Update MCP tools with metadata support

**Story 1.3 (Smart Processing)**:
- `vectordb/processor/document_processor.py` - Add categorization and duplicate detection
- `vectordb/embedding_service.py` - Extend for similarity-based duplicate detection

**Story 1.4 (Enhanced Q&A)**:
- `rag/rag_api.py` - Natural language query interface improvements
- `mcp/rag_server.py` - Enhanced search tools with source attribution

### New Files/Modules Needed

**Story 1.3 (Smart Processing Pipeline)**:
- `mcp_rag_playground/processing/__init__.py` - Smart processing module
- `mcp_rag_playground/processing/categorizer.py` - Document categorization
- `mcp_rag_playground/processing/duplicate_detector.py` - Content deduplication

**Story 1.5 (Tracking Dashboard)**:
- `mcp_rag_playground/api/__init__.py` - REST API module  
- `mcp_rag_playground/api/rest_server.py` - FastAPI/Flask server
- `mcp_rag_playground/api/dashboard.py` - Web dashboard interface

**Story 1.6 (Integration & Export)**:
- `mcp_rag_playground/export/__init__.py` - Export functionality
- `mcp_rag_playground/export/formats.py` - Multiple format support (JSON, CSV, PDF)
- `mcp_rag_playground/api/bulk_operations.py` - Batch processing endpoints

### Integration Considerations

**Container Extension**: All new services must integrate with existing Container DI pattern

**MCP Compatibility**: New features exposed through additional MCP tools while maintaining existing 4 tools

**Performance**: Bulk operations and smart processing must not degrade existing vector search performance

**Backward Compatibility**: All existing RagAPI and VectorClient method signatures must remain unchanged

## Appendix - Useful Commands and Scripts

### Frequently Used Commands

```bash
# Development setup
pip install -e .                    # Install in editable mode
cd vectordb/milvus && docker-compose up -d  # Start Milvus

# Testing
pytest                              # All tests with coverage
pytest -m "unit" -v                 # Fast unit tests verbose
pytest -m "not slow"                # Skip model downloads
pytest mcp_rag_playground/tests/test_vector_client.py  # Specific test

# MCP Server
python -m mcp_rag_playground.mcp.rag_server  # Run MCP server
uv run python -m mcp_rag_playground.mcp.rag_server    # With uv

# Container usage (current reality)
python -c "from mcp_rag_playground.container.container import Container; c = Container(); api = c.rag_api()"
```

### Debugging and Troubleshooting

- **Logs**: Python logging via `config.logging_config.get_logger(__name__)`
- **MCP Server Debug**: Module runs directly, check imports and DI container setup
- **Vector DB Connection**: Use `vector_client.test_connection()` method
- **Path Issues**: WSL path normalization in MCP server for cross-platform compatibility

### Extension Development Patterns

```bash
# Adding new vector database
# 1. Implement VectorDBInterface
# 2. Add to Container as provider
# 3. Update tests with new fixtures

# Adding smart processing
# 1. Extend DocumentProcessor or create parallel pipeline
# 2. Register in Container with existing dependencies
# 3. Integrate with existing chunking workflow

# Adding REST API
# 1. Create api/ module with FastAPI/Flask
# 2. Inject existing RagAPI for business logic reuse
# 3. Deploy alongside MCP server without conflicts
```