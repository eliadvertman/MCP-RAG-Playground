# Integration Points and External Dependencies

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
