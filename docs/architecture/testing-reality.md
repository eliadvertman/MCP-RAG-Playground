# Testing Reality

### Current Test Coverage

- **Test Framework**: pytest with comprehensive markers system
- **Coverage Target**: 80% minimum (pytest-cov configuration)
- **Test Organization**: fixtures organized by concern, markers for different test types
- **Integration**: Real Milvus and embedding models for integration tests

### Test Markers System

**Current Markers** (from `pytest.ini`):
```ini
slow: tests requiring external services (model downloads)
integration: tests with real components  
unit: isolated tests with mocks
milvus: tests requiring Milvus connection
mock: tests using mock services
embedding: tests using real embedding models
performance: performance benchmark tests
smoke: quick sanity checks
```

**Test Files Structure**:
```text
mcp_rag_playground/tests/
├── conftest.py                    # Pytest configuration
├── fixtures/                     # Organized by concern
│   ├── embedding_fixtures.py     # Embedding test fixtures
│   └── vector_client_fixtures.py # Vector client fixtures
├── test_data/                    # Sample test files
│   ├── test_config.json         
│   ├── test_document.md         
│   ├── test_document.txt        
│   └── test_module.py           
├── test_document_metadata.py     # Story 1.1 metadata tests
├── test_embedding_service.py     # Embedding service tests
├── test_imports.py              # Import validation tests
├── test_milvus_client.py        # Milvus implementation tests
├── test_rag_api_integration.py  # RAG API integration tests
└── test_vector_client.py        # Vector client unit tests
```

### Running Tests

```bash