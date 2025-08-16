"""
Enhanced data models for question-answering interface.

This module provides data structures specific to enhanced Q&A functionality,
including enriched search results with source attribution and structured Q&A responses.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any

from mcp_rag_playground.vectordb.vector_db_interface import Document, SearchResult


@dataclass
class EnhancedSearchResult:
    """Enhanced search result with additional context and citation information."""
    
    document: Document
    score: float
    context: str
    citation: str
    relevance_explanation: str
    distance: float = 0.0
    
    def __post_init__(self):
        """Validate score range and citation format."""
        if not 0 <= self.score <= 1:
            raise ValueError("Score must be between 0 and 1")
        
        if not self.citation:
            self.citation = self._generate_citation()
        
        if not self.relevance_explanation:
            self.relevance_explanation = f"Relevance score: {self.score:.3f}"
    
    def _generate_citation(self) -> str:
        """Generate a formatted citation for this search result."""
        filename = self.document.filename or "Unknown Document"
        file_type = self.document.file_type or ""
        timestamp = ""
        
        if self.document.ingestion_timestamp:
            if isinstance(self.document.ingestion_timestamp, datetime):
                timestamp = self.document.ingestion_timestamp.strftime("%Y-%m-%d")
            elif isinstance(self.document.ingestion_timestamp, str):
                # Try to extract date part from ISO string
                timestamp = self.document.ingestion_timestamp.split('T')[0]
        
        citation_parts = [filename]
        if file_type:
            citation_parts.append(f"({file_type})")
        if timestamp:
            citation_parts.append(f"- {timestamp}")
        
        return " ".join(citation_parts)
    
    @classmethod
    def from_search_result(cls, search_result: SearchResult, context: str = None, 
                          relevance_explanation: str = None) -> 'EnhancedSearchResult':
        """Create an EnhancedSearchResult from a basic SearchResult."""
        if context is None:
            # Use first 200 characters of content as context
            context = search_result.document.content[:200]
            if len(search_result.document.content) > 200:
                context += "..."
        
        return cls(
            document=search_result.document,
            score=search_result.score,
            distance=getattr(search_result, 'distance', 0.0),
            context=context,
            citation="",  # Will be auto-generated in __post_init__
            relevance_explanation=relevance_explanation or ""
        )


@dataclass
class QAResponse:
    """Structured response for question-answering queries."""
    
    question: str
    answer: str
    sources: List[EnhancedSearchResult]
    confidence_score: float
    processing_time: float
    suggestions: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate response data."""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        
        if self.processing_time < 0:
            raise ValueError("Processing time must be non-negative")
        
        if not self.metadata:
            self.metadata = {}
        
        # Add automatic metadata
        self.metadata.update({
            "sources_count": len(self.sources),
            "max_source_score": max((s.score for s in self.sources), default=0.0),
            "avg_source_score": sum(s.score for s in self.sources) / len(self.sources) if self.sources else 0.0,
            "response_generated_at": datetime.now().isoformat()
        })
    
    def get_formatted_sources(self) -> str:
        """Get a formatted string of all sources with citations."""
        if not self.sources:
            return "No sources found."
        
        formatted = []
        for i, source in enumerate(self.sources, 1):
            formatted.append(f"{i}. {source.citation} (Score: {source.score:.3f})")
        
        return "\n".join(formatted)
    
    def get_source_attribution(self) -> str:
        """Get a formatted source attribution for the answer."""
        if not self.sources:
            return ""
        
        if len(self.sources) == 1:
            return f"Source: {self.sources[0].citation}"
        else:
            return f"Sources: {', '.join(s.citation for s in self.sources[:3])}"
            

class CitationFormatter:
    """Utility class for formatting citations from document metadata."""
    
    @staticmethod
    def format_basic_citation(document: Document) -> str:
        """Format a basic citation from document metadata."""
        filename = document.filename or "Unknown Document"
        file_type = document.file_type or ""
        
        citation_parts = [filename]
        if file_type:
            citation_parts.append(f"({file_type})")
        
        return " ".join(citation_parts)
    
    @staticmethod
    def format_detailed_citation(document: Document) -> str:
        """Format a detailed citation with timestamps and chunk information."""
        basic = CitationFormatter.format_basic_citation(document)
        
        details = []
        
        # Add timestamp
        if document.ingestion_timestamp:
            if isinstance(document.ingestion_timestamp, datetime):
                timestamp = document.ingestion_timestamp.strftime("%Y-%m-%d %H:%M")
            elif isinstance(document.ingestion_timestamp, str):
                timestamp = document.ingestion_timestamp.split('T')[0]
            else:
                timestamp = str(document.ingestion_timestamp)
            details.append(f"Added: {timestamp}")
        
        # Add chunk information
        if document.chunk_position is not None and document.chunk_count is not None:
            details.append(f"Chunk {document.chunk_position + 1}/{document.chunk_count}")
        
        # Add file size
        if document.file_size is not None:
            if document.file_size > 1024 * 1024:
                size_str = f"{document.file_size / (1024 * 1024):.1f}MB"
            elif document.file_size > 1024:
                size_str = f"{document.file_size / 1024:.1f}KB"
            else:
                size_str = f"{document.file_size}B"
            details.append(f"Size: {size_str}")
        
        if details:
            return f"{basic} [{', '.join(details)}]"
        else:
            return basic
    
    @staticmethod
    def format_apa_style(document: Document) -> str:
        """Format citation in APA-like style."""
        filename = document.filename or "Unknown Document"
        
        # Remove file extension for title
        title = filename
        if '.' in title:
            title = title.rsplit('.', 1)[0]
        
        year = "n.d."
        if document.ingestion_timestamp:
            if isinstance(document.ingestion_timestamp, datetime):
                year = document.ingestion_timestamp.strftime("%Y")
            elif isinstance(document.ingestion_timestamp, str):
                year = document.ingestion_timestamp.split('-')[0] if '-' in document.ingestion_timestamp else "n.d."
        
        return f"{title}. ({year}). {filename}"

#TODO move from model to a dedicated file
class QueryProcessor:
    """Utility class for processing and analyzing natural language queries."""
    
    @staticmethod
    def expand_abbreviations(query: str) -> str:
        """Expand common abbreviations in queries."""
        #TODO - move to static parameter
        abbreviations = {
            "db": "database",
            "ai": "artificial intelligence",
            "ml": "machine learning",
            "api": "application programming interface",
            "ui": "user interface",
            "ux": "user experience",
            "cpu": "central processing unit",
            "gpu": "graphics processing unit",
            "ram": "random access memory",
            "os": "operating system",
            "js": "javascript",
            "py": "python",
            "css": "cascading style sheets",
            "html": "hypertext markup language",
            "http": "hypertext transfer protocol",
            "https": "hypertext transfer protocol secure",
            "url": "uniform resource locator",
            "json": "javascript object notation",
            "xml": "extensible markup language",
            "sql": "structured query language"
        }
        
        words = query.lower().split()
        expanded_words = []
        
        for word in words:
            # Remove punctuation for matching
            clean_word = word.strip('.,!?;:')
            if clean_word in abbreviations:
                expanded_words.append(abbreviations[clean_word])
            else:
                expanded_words.append(word)
        
        return " ".join(expanded_words)
    
    @staticmethod
    def detect_question_type(query: str) -> str:
        """Detect the type of question being asked."""
        query_lower = query.lower().strip()
        
        if query_lower.startswith(("what", "who", "where", "when", "which")):
            return "factual"
        elif query_lower.startswith(("how", "why")):
            return "procedural"
        elif query_lower.startswith(("is", "are", "can", "could", "will", "would", "should", "does", "do")):
            return "boolean"
        elif "?" in query:
            return "general_question"
        else:
            return "keyword_search"
    
    @staticmethod
    def extract_keywords(query: str) -> List[str]:
        """Extract key terms from a query."""
        # Simple keyword extraction - remove common stop words
        #TODO - move to static parameter
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
            "to", "was", "will", "with", "the", "this", "these", "those",
            "i", "you", "we", "they", "me", "us", "them", "my", "your", "our"
        }
        
        words = query.lower().split()
        keywords = [word.strip('.,!?;:') for word in words 
                   if word.strip('.,!?;:') not in stop_words and len(word) > 2]
        
        return keywords