
import json
import os
import shutil
import tempfile
from pathlib import Path

def get_test_data_dir():
    """Get the path to the test data directory."""
    current_file = Path(__file__)
    test_data_dir = current_file.parent / "test_data"

    if not test_data_dir.exists():
        raise FileNotFoundError(f"Test data directory not found: {test_data_dir}")

    return test_data_dir


def get_test_file_paths():
    """Get paths to the static test data files."""
    test_data_dir = get_test_data_dir()

    test_files = {
        'markdown': test_data_dir / "test_document.md",
        'text': test_data_dir / "test_document.txt",
        'python': test_data_dir / "test_module.py"
    }

    # Verify all test files exist
    for file_type, file_path in test_files.items():
        if not file_path.exists():
            raise FileNotFoundError(f"Test {file_type} file not found: {file_path}")

    return test_files


def get_direct_test_files():
    """Get direct paths to test files (no copying needed for read-only tests)."""
    source_files = get_test_file_paths()
    return {file_type: str(path) for file_type, path in source_files.items()}


def load_test_config():
    """Load test configuration from test_config.json."""
    test_data_dir = get_test_data_dir()
    config_path = test_data_dir / "test_config.json"

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Return default configuration if file doesn't exist
        return {
            "test_queries": ["vector database", "Python programming", "hello world", "markdown document"],
            "milvus_test_queries": ["vector database", "Python class", "greeting message"],
            "embedding_dimension": 384,
            "chunk_size": 1000,
            "chunk_overlap": 100,
            "test_collection_names": {
                "mock": "test_collection_mock",
                "milvus": "test_collection_milvus"
            }
        }


def create_test_files():
    """Create temporary test files for testing by copying from test_data."""
    try:
        # Get source test files
        source_files = get_test_file_paths()

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Copy test files to temporary directory
        test_files = {}
        for file_type, source_path in source_files.items():
            dest_path = os.path.join(temp_dir, source_path.name)
            shutil.copy2(source_path, dest_path)
            test_files[file_type] = dest_path

        return test_files, temp_dir

    except Exception as e:
        raise RuntimeError(f"Failed to create test files: {e}")