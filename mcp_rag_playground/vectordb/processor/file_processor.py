from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class FileProcessor(ABC):
    """Abstract base class for file-specific processors."""

    @abstractmethod
    def process(self, file_path: str) -> str:
        """Extract text content from the file."""
        pass

    @abstractmethod
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get file-specific metadata."""
        pass


class TextFileProcessor(FileProcessor):
    """Processor for plain text files."""

    def process(self, file_path: str) -> str:
        """Extract text content from plain text file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata for text files."""
        return {
            'file_type': 'text',
            'file_name': Path(file_path).name,
            'file_extension': Path(file_path).suffix.lower()
        }


class MarkdownFileProcessor(FileProcessor):
    """Processor for Markdown files."""

    def process(self, file_path: str) -> str:
        """Extract text content from Markdown file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata for Markdown files."""
        return {
            'file_type': 'markdown',
            'file_name': Path(file_path).name,
            'file_extension': Path(file_path).suffix.lower()
        }


class PythonFileProcessor(FileProcessor):
    """Processor for Python source files."""

    def process(self, file_path: str) -> str:
        """Extract text content from Python file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata for Python files."""
        return {
            'file_type': 'python',
            'file_name': Path(file_path).name,
            'file_extension': Path(file_path).suffix.lower(),
            'language': 'python'
        }


class JSONFileProcessor(FileProcessor):
    """Processor for JSON files."""

    def process(self, file_path: str) -> str:
        """Extract text content from JSON file."""
        import json

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return json.dumps(data, indent=2)

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata for JSON files."""
        return {
            'file_type': 'json',
            'file_name': Path(file_path).name,
            'file_extension': Path(file_path).suffix.lower(),
            'format': 'json'
        }