# High Level Architecture

### Technical Summary

**Current Reality**: Python 3.9+ MCP RAG system with SOLID-compliant vector database client, production DI container, and module-level FastMCP server. Missing factory functions and examples directory.

### Actual Tech Stack (from pyproject.toml)

| Category            | Technology              | Version | Notes                                    |
| ------------------- | ----------------------- | ------- | ---------------------------------------- |
| Runtime             | Python                  | >=3.12  | **CRITICAL**: pyproject.toml requires 3.12+, CLAUDE.md outdated |
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
