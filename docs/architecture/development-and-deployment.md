# Development and Deployment

### Local Development Setup (Working Steps)

1. `pip install -e .` (required for MCP server module imports)
2. `cd vectordb/milvus && docker-compose up -d` (start Milvus)
3. Test connection: `python -c "from mcp_rag_playground.container.container import Container; c = Container(); c.rag_api().vector_client.test_connection()"`
4. Run MCP server: `python -m mcp_rag_playground.mcp.rag_server`

### Build and Deployment Process

- **Build**: No build step, pure Python package
- **Testing**: `pytest` with comprehensive markers and 80% coverage target
- **MCP Deployment**: Module-level server, not class-based
