"""
Test module for verifying import chain functionality.

This module tests that all imports in __init__.py work correctly without ImportError
and that the conditional MCP import behavior works as expected.
"""

import pytest
import sys


class TestImportChain:
    """Test the main package import chain."""

    def test_main_package_import(self):
        """Test that main package can be imported without errors."""
        # This should succeed without ImportError
        import mcp_rag_playground
        
        # Verify basic components are available
        assert hasattr(mcp_rag_playground, 'VectorClient')
        assert hasattr(mcp_rag_playground, 'RagAPI')
        assert hasattr(mcp_rag_playground, 'MilvusVectorDB')

    def test_all_exports_importable(self):
        """Test that all items in __all__ can be imported."""
        import mcp_rag_playground
        
        # Get the __all__ list
        all_exports = mcp_rag_playground.__all__
        assert len(all_exports) > 0, "No exports found in __all__"
        
        # Verify each export can be accessed
        for export_name in all_exports:
            assert hasattr(mcp_rag_playground, export_name), f"Export '{export_name}' not available"
            
            # Verify the attribute is not None (except for conditional imports)
            attr = getattr(mcp_rag_playground, export_name)
            if export_name != 'rag_server':  # rag_server might be None if MCP unavailable
                assert attr is not None, f"Export '{export_name}' is None"

    def test_core_components_available(self):
        """Test that core components are always available."""
        from mcp_rag_playground import (
            VectorClient,
            RagAPI, 
            MilvusVectorDB,
            SentenceTransformerEmbedding,
            Document,
            SearchResult,
            MilvusConfig
        )
        
        # Verify these are actual classes/types, not None
        assert VectorClient is not None
        assert RagAPI is not None
        assert MilvusVectorDB is not None
        assert SentenceTransformerEmbedding is not None
        assert Document is not None
        assert SearchResult is not None
        assert MilvusConfig is not None

    def test_mcp_conditional_import(self):
        """Test MCP conditional import behavior."""
        import mcp_rag_playground
        
        # Check if MCP is available
        mcp_available = mcp_rag_playground._MCP_AVAILABLE
        
        if mcp_available:
            # If MCP is available, rag_server should be in __all__ and accessible
            assert 'rag_server' in mcp_rag_playground.__all__
            assert hasattr(mcp_rag_playground, 'rag_server')
            rag_server = mcp_rag_playground.rag_server
            assert rag_server is not None
            
            # Verify rag_server module has expected attributes
            assert hasattr(rag_server, 'mcp')  # FastMCP instance
            assert hasattr(rag_server, 'container')  # DI container
        else:
            # If MCP is not available, rag_server might not be in __all__
            # or might be None
            if hasattr(mcp_rag_playground, 'rag_server'):
                assert mcp_rag_playground.rag_server is None

    def test_fresh_installation_import(self):
        """Test import behavior simulating fresh installation."""
        # This simulates what happens when someone does:
        # python -c "import mcp_rag_playground"
        
        try:
            import mcp_rag_playground
            # Should not raise ImportError
            success = True
        except ImportError as e:
            success = False
            pytest.fail(f"Fresh installation import failed: {e}")
        
        assert success, "Fresh installation import should succeed"

    def test_mcp_module_structure(self):
        """Test MCP module structure and exports."""
        try:
            from mcp_rag_playground.mcp import rag_server
            
            # If import succeeds, verify module structure
            assert hasattr(rag_server, 'mcp'), "rag_server should have 'mcp' attribute"
            assert hasattr(rag_server, 'container'), "rag_server should have 'container' attribute"
            
            # Verify MCP server tools are available
            mcp_instance = rag_server.mcp
            # Note: FastMCP tools aren't easily introspectable, but we can check it's a FastMCP
            assert str(type(mcp_instance)).find('FastMCP') != -1, "Should be FastMCP instance"
            
        except ImportError:
            # If MCP dependencies not available, this is expected
            pytest.skip("MCP dependencies not available")

    def test_backward_compatibility_imports(self):
        """Test that existing import patterns still work."""
        # Test individual component imports
        from mcp_rag_playground import VectorClient
        from mcp_rag_playground import RagAPI
        from mcp_rag_playground.vectordb.vector_client import VectorClient as VCDirect
        from mcp_rag_playground.rag.rag_api import RagAPI as RAGDirect
        
        # Verify these are the same classes
        assert VectorClient is VCDirect
        assert RagAPI is RAGDirect
        
        # Test container import (common existing pattern)
        from mcp_rag_playground.container.container import Container
        assert Container is not None


class TestImportErrorHandling:
    """Test import error handling and graceful degradation."""

    def test_missing_optional_dependencies(self):
        """Test behavior when optional dependencies are missing."""
        # This is harder to test directly since we'd need to mock missing dependencies
        # But we can verify the conditional import pattern works
        
        import mcp_rag_playground
        
        # The import should succeed even if some conditional imports fail
        assert mcp_rag_playground is not None
        assert hasattr(mcp_rag_playground, '_MCP_AVAILABLE')
        
        # _MCP_AVAILABLE should be a boolean
        assert isinstance(mcp_rag_playground._MCP_AVAILABLE, bool)

    def test_import_path_consistency(self):
        """Test that relative and absolute imports return the same objects."""
        import mcp_rag_playground
        from mcp_rag_playground.vectordb.vector_client import VectorClient as DirectVectorClient
        from mcp_rag_playground.rag.rag_api import RagAPI as DirectRagAPI
        
        # Verify package exports match direct imports
        assert mcp_rag_playground.VectorClient is DirectVectorClient, "Package export should match direct import"
        assert mcp_rag_playground.RagAPI is DirectRagAPI, "Package export should match direct import"
        
        # Test that we can import the same module multiple ways without issues
        from mcp_rag_playground import VectorClient as ExportedVC
        assert ExportedVC is DirectVectorClient, "All import methods should return same object"