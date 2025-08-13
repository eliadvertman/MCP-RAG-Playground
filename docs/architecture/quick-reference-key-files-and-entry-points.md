# Quick Reference - Key Files and Entry Points

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

**Story 1.2 (Schema Evolution Framework)**: ✅ **READY FOR IMPLEMENTATION**
- `mcp_rag_playground/vectordb/milvus/milvus_client.py` - Remove dual schema logic
- `mcp_rag_playground/config/milvus_config.py` - Add schema configuration
- Status: Story approved, simplified for MVP (manual migration acceptable)

**Story 1.3 (Document Management Operations)**: ✅ **READY FOR IMPLEMENTATION**
- `mcp_rag_playground/rag/rag_api.py` - Enhanced add/remove with metadata
- `mcp_rag_playground/mcp/rag_server.py` - MCP tools enhancement
- New: Batch operations interface
- Status: Story drafted, comprehensive dev notes completed

**Story 1.4 (Smart Processing Pipeline)**: 🔄 **PLANNED**
- `mcp_rag_playground/vectordb/processor/document_processor.py` - Smart categorization
- `mcp_rag_playground/vectordb/embedding_service.py` - Duplicate detection
- New: `mcp_rag_playground/processing/` module

**Story 1.5 (Enhanced Q&A Interface)**: 🔄 **PLANNED**
- `mcp_rag_playground/rag/rag_api.py` - Natural language interface
- `mcp_rag_playground/mcp/rag_server.py` - Enhanced search tools
- New: Source attribution system

**Story 1.6 (Tracking Dashboard)**: 🔄 **PLANNED**
- New: `mcp_rag_playground/api/` module for REST endpoints
- New: Dashboard web interface (optional deployment)

**Story 1.7 (Integration & Export)**: 🔄 **PLANNED**
- New: `mcp_rag_playground/api/` module expansion
- New: Export functionality across multiple formats
