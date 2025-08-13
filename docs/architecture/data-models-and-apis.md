# Data Models and APIs

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
