"""
Document processing utilities for file upload and text chunking.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from mcp_rag_playground.vectordb.processor.file_processor import FileProcessor, TextFileProcessor, \
    MarkdownFileProcessor, PythonFileProcessor, JSONFileProcessor
from mcp_rag_playground.vectordb.vector_db_interface import Document





class DocumentProcessor:
    """Handles document processing for vector database ingestion."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100, 
                 custom_processors: Optional[Dict[str, FileProcessor]] = None):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # Default file processors
        self.processors = {
            '.txt': TextFileProcessor(),
            '.md': MarkdownFileProcessor(),
            '.markdown': MarkdownFileProcessor(),
            '.py': PythonFileProcessor(),
            '.json': JSONFileProcessor(),
            '.js': TextFileProcessor(),
            '.ts': TextFileProcessor(),
            '.css': TextFileProcessor(),
            '.html': TextFileProcessor(),
            '.xml': TextFileProcessor(),
            '.yml': TextFileProcessor(),
            '.yaml': TextFileProcessor(),
            '.toml': TextFileProcessor(),
            '.ini': TextFileProcessor(),
            '.cfg': TextFileProcessor(),
            '.conf': TextFileProcessor(),
            '.log': TextFileProcessor(),
        }
        
        # Add custom processors if provided
        if custom_processors:
            self.processors.update(custom_processors)
    
    def register_processor(self, extension: str, processor: FileProcessor):
        """Register a custom processor for a file extension."""
        if not extension.startswith('.'):
            extension = '.' + extension
        self.processors[extension.lower()] = processor
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.processors.keys())
    
    def process_file(self, file_path: str) -> List[Document]:
        """Process a file and return chunked documents."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension not in self.processors:
            raise ValueError(f"Unsupported file type: {file_extension}. "
                           f"Supported types: {', '.join(self.processors.keys())}")
        
        processor = self.processors[file_extension]
        
        try:
            content = processor.process(file_path)
            metadata = processor.get_metadata(file_path)
            metadata['source'] = file_path
            
            return self._chunk_text(content, metadata)
        
        except Exception as e:
            raise RuntimeError(f"Error processing file {file_path}: {e}")
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Process raw text and return chunked documents."""
        base_metadata = metadata or {}
        return self._chunk_text(text, base_metadata)
    
    def _chunk_text(self, text: str, base_metadata: Dict[str, Any]) -> List[Document]:
        """Split text into overlapping chunks with smart boundary detection."""
        if not text.strip():
            return []
            
        if len(text) <= self.chunk_size:
            return [Document(
                content=text.strip(),
                metadata={**base_metadata, 'chunk_index': 0, 'total_chunks': 1}
            )]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        # Pre-process text to normalize whitespace
        text = self._normalize_text(text)
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                end = self._find_optimal_boundary(text, end)
            else:
                end = len(text)
            
            chunk_content = text[start:end].strip()
            
            if chunk_content and len(chunk_content) > 10:  # Skip very short chunks
                chunks.append(Document(
                    content=chunk_content,
                    metadata={
                        **base_metadata,
                        'chunk_index': chunk_index,
                        'start_char': start,
                        'end_char': end,
                        'chunk_length': len(chunk_content)
                    }
                ))
                chunk_index += 1
            
            # Calculate next start position with overlap
            next_start = end - self.overlap
            if next_start <= start:  # Prevent infinite loops
                next_start = start + max(1, self.chunk_size // 2)
            start = next_start
        
        # Add total chunk count to all chunks
        for chunk in chunks:
            chunk.metadata['total_chunks'] = len(chunks)
        
        return chunks
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by cleaning up whitespace."""
        import re
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def _find_optimal_boundary(self, text: str, position: int) -> int:
        """Find the optimal boundary for splitting text."""
        # Priority order for boundaries
        boundaries = [
            ('\n\n', 0),      # Paragraph breaks (highest priority)
            ('\n', 0),        # Line breaks
            ('. ', 2),        # Sentence endings
            ('! ', 2),        # Exclamation endings
            ('? ', 2),        # Question endings
            (', ', 1),        # Comma breaks
            (' ', 0),         # Word boundaries (lowest priority)
        ]
        
        # Search backwards from position for optimal boundary
        search_range = min(200, position)  # Don't search too far back
        
        for boundary_text, offset in boundaries:
            for i in range(position, max(0, position - search_range), -1):
                if text[i:i+len(boundary_text)] == boundary_text:
                    return i + len(boundary_text) + offset
        
        # If no good boundary found, return original position
        return position