# Technical Debt and Known Issues

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
