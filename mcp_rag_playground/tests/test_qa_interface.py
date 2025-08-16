"""
Comprehensive unit tests for the QuestionAnsweringInterface.

This module tests the enhanced Q&A capabilities including natural language
processing, source attribution, and structured response generation.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from mcp_rag_playground.models.qa_models import (
    EnhancedSearchResult, QAResponse, CitationFormatter, QueryProcessor
)
from mcp_rag_playground.rag.qa_interface import QuestionAnsweringInterface
from mcp_rag_playground.vectordb.vector_client import VectorClient
from mcp_rag_playground.vectordb.vector_db_interface import Document, SearchResult


#TODO move to config
@pytest.fixture
def mock_vector_client():
    """Create a mock VectorClient for testing."""
    mock_client = Mock(spec=VectorClient)
    mock_client.collection_name = "test_collection"
    return mock_client

#TODO move to config
@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    docs = []
    
    # Document 1: Python tutorial
    doc1 = Document(
        content="Python is a high-level programming language. It is widely used for web development, data analysis, and artificial intelligence.",
        metadata={"source": "python_tutorial.md", "topic": "programming"},
        id="doc_1",
        filename="python_tutorial.md",
        file_type=".md",
        ingestion_timestamp=datetime(2024, 1, 15, 10, 30),
        chunk_count=5,
        file_size=1024,
        chunk_position=0,
        vector_id="vec_1",
        embedding_status="completed"
    )
    
    # Document 2: Machine learning basics
    doc2 = Document(
        content="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed. It uses algorithms to find patterns in data.",
        metadata={"source": "ml_basics.txt", "topic": "ai"},
        id="doc_2",
        filename="ml_basics.txt",
        file_type=".txt",
        ingestion_timestamp=datetime(2024, 1, 16, 14, 20),
        chunk_count=3,
        file_size=2048,
        chunk_position=1,
        vector_id="vec_2",
        embedding_status="completed"
    )
    
    # Document 3: Web development guide
    doc3 = Document(
        content="Web development involves creating websites and web applications. Frontend development focuses on user interfaces, while backend development handles server-side logic.",
        metadata={"source": "web_dev.py", "topic": "web"},
        id="doc_3",
        filename="web_dev.py",
        file_type=".py",
        ingestion_timestamp=datetime(2024, 1, 17, 9, 45),
        chunk_count=7,
        file_size=4096,
        chunk_position=2,
        vector_id="vec_3",
        embedding_status="completed"
    )
    
    docs.extend([doc1, doc2, doc3])
    return docs

#TODO move to config
@pytest.fixture
def sample_search_results(sample_documents):
    """Create sample search results for testing."""
    results = []
    scores = [0.95, 0.82, 0.67]
    
    for doc, score in zip(sample_documents, scores):
        result = SearchResult(
            document=doc,
            score=score,
            distance=1.0 - score
        )
        results.append(result)
    
    return results


@pytest.fixture
def qa_interface(mock_vector_client):
    """Create a QuestionAnsweringInterface instance for testing."""
    return QuestionAnsweringInterface(
        vector_client=mock_vector_client,
        collection_name="test_collection"
    )


class TestQuestionAnsweringInterface:
    """Test cases for QuestionAnsweringInterface."""
    
    def test_initialization(self, mock_vector_client):
        """Test Q&A interface initialization."""
        qa_interface = QuestionAnsweringInterface(
            vector_client=mock_vector_client,
            collection_name="test_collection"
        )
        
        assert qa_interface.vector_client == mock_vector_client
        assert qa_interface.collection_name == "test_collection"
        assert mock_vector_client.collection_name == "test_collection"
    
    def test_ask_question_basic(self, qa_interface, mock_vector_client, sample_search_results):
        """Test basic ask_question functionality."""
        # Setup mock
        mock_vector_client.query.return_value = sample_search_results
        
        # Ask a question
        result = qa_interface.ask_question("What is Python?")
        
        # Verify result structure
        assert isinstance(result, QAResponse)
        assert result.question == "What is Python?"
        assert len(result.sources) <= 5  # Default max_sources
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.processing_time > 0
        assert isinstance(result.answer, str)
        assert isinstance(result.suggestions, list)
        
        # Verify vector client was called
        mock_vector_client.query.assert_called_once()
    
    def test_ask_question_empty_input(self, qa_interface):
        """Test ask_question with empty input."""
        result = qa_interface.ask_question("")
        
        assert isinstance(result, QAResponse)
        assert result.question == ""
        assert result.confidence_score == 0.0
        assert len(result.sources) == 0
        assert "empty" in result.answer.lower() or "cannot" in result.answer.lower()
    
    def test_ask_question_no_results(self, qa_interface, mock_vector_client):
        """Test ask_question when no search results are found."""
        # Setup mock to return empty results
        mock_vector_client.query.return_value = []
        
        result = qa_interface.ask_question("What is quantum computing?")
        
        assert isinstance(result, QAResponse)
        assert result.confidence_score == 0.0
        assert len(result.sources) == 0
        assert "couldn't find" in result.answer.lower() or "no" in result.answer.lower()
        assert len(result.suggestions) > 0
    
    def test_ask_question_with_parameters(self, qa_interface, mock_vector_client, sample_search_results):
        """Test ask_question with custom parameters."""
        mock_vector_client.query.return_value = sample_search_results
        
        result = qa_interface.ask_question(
            question="How do I use Python?",
            max_sources=3,
            include_context=True,
            min_score=0.5,
            expand_query=False
        )
        
        assert isinstance(result, QAResponse)
        assert len(result.sources) <= 3
        assert result.metadata.get("min_score_used") == 0.5
        
        # Verify vector client was called with correct parameters
        mock_vector_client.query.assert_called_once()
        call_args = mock_vector_client.query.call_args
        assert call_args[1]["min_score"] == 0.5
        assert call_args[1]["limit"] >= 3  # Should be at least max_sources
    
    def test_enhance_search_results(self, qa_interface, sample_search_results):
        """Test enhancement of basic search results."""
        enhanced_results = qa_interface._enhance_search_results(
            sample_search_results, 
            "What is Python?", 
            include_context=True
        )
        
        assert len(enhanced_results) == len(sample_search_results)
        
        for enhanced in enhanced_results:
            assert isinstance(enhanced, EnhancedSearchResult)
            assert enhanced.context  # Should have context
            assert enhanced.citation  # Should have citation
            assert enhanced.relevance_explanation  # Should have relevance explanation
            assert 0.0 <= enhanced.score <= 1.0
    
    def test_extract_relevant_context(self, qa_interface):
        """Test context extraction functionality."""
        content = "Python is a programming language. It was created by Guido van Rossum. Python is used for web development, data science, and automation. The language emphasizes code readability."
        question = "What is Python used for?"
        
        context = qa_interface._extract_relevant_context(content, question, context_length=100)
        
        assert len(context) <= 103  # Allow for "..." addition
        assert "python" in context.lower()  # Should contain relevant terms
    
    def test_question_type_detection_and_processing(self, qa_interface, mock_vector_client, sample_search_results):
        """Test different question types are handled appropriately."""
        mock_vector_client.query.return_value = sample_search_results
        
        test_questions = [
            ("What is machine learning?", "factual"),
            ("How do I install Python?", "procedural"), 
            ("Can Python be used for web development?", "boolean"),
            ("Python programming concepts", "keyword_search")
        ]
        
        for question, expected_type in test_questions:
            result = qa_interface.ask_question(question)
            
            assert isinstance(result, QAResponse)
            assert result.metadata.get("question_type") == expected_type
            assert len(result.answer) > 0
    
    def test_confidence_score_calculation(self, qa_interface, mock_vector_client):
        """Test confidence score calculation based on source quality."""
        # High quality results
        high_quality_results = [
            SearchResult(
                document=Document(content="High quality content", metadata={}),
                score=0.95,
                distance=0.05
            )
        ]
        
        # Low quality results
        low_quality_results = [
            SearchResult(
                document=Document(content="Low quality content", metadata={}),
                score=0.3,
                distance=0.7
            )
        ]
        
        mock_vector_client.query.side_effect = [high_quality_results, low_quality_results]
        
        # Test high quality
        high_result = qa_interface.ask_question("High quality question")
        assert high_result.confidence_score > 0.8
        
        # Test low quality
        low_result = qa_interface.ask_question("Low quality question")
        assert low_result.confidence_score < 0.5
    
    def test_query_suggestions_generation(self, qa_interface, mock_vector_client):
        """Test query suggestion generation."""
        # Test with no results
        mock_vector_client.query.return_value = []
        result = qa_interface.ask_question("obscure question")
        
        assert len(result.suggestions) > 0
        assert any("specific" in suggestion.lower() for suggestion in result.suggestions)
        
        # Test with low quality results
        low_quality_results = [
            SearchResult(
                document=Document(content="Content", metadata={}, file_type=".py"),
                score=0.4,
                distance=0.6
            )
        ]
        mock_vector_client.query.return_value = low_quality_results
        result = qa_interface.ask_question("another question")
        
        assert len(result.suggestions) > 0
    
    def test_error_handling(self, qa_interface, mock_vector_client):
        """Test error handling in ask_question."""
        # Simulate vector client error
        mock_vector_client.query.side_effect = Exception("Database connection failed")
        
        result = qa_interface.ask_question("What is Python?")
        
        assert isinstance(result, QAResponse)
        assert result.confidence_score == 0.0
        assert len(result.sources) == 0
        assert "error" in result.answer.lower()
        assert "Database connection failed" in result.metadata.get("error", "")


class TestEnhancedSearchResult:
    """Test cases for EnhancedSearchResult model."""
    
    def test_enhanced_search_result_creation(self, sample_documents):
        """Test creation of EnhancedSearchResult."""
        doc = sample_documents[0]
        
        enhanced = EnhancedSearchResult(
            document=doc,
            score=0.85,
            context="Python is a programming language",
            citation="python_tutorial.md (.md) - 2024-01-15",
            relevance_explanation="High relevance match",
            distance=0.15
        )
        
        assert enhanced.document == doc
        assert enhanced.score == 0.85
        assert enhanced.context == "Python is a programming language"
        assert enhanced.citation == "python_tutorial.md (.md) - 2024-01-15"
        assert enhanced.relevance_explanation == "High relevance match"
    
    def test_enhanced_search_result_validation(self, sample_documents):
        """Test validation in EnhancedSearchResult."""
        doc = sample_documents[0]
        
        # Test invalid score
        with pytest.raises(ValueError, match="Score must be between 0 and 1"):
            EnhancedSearchResult(
                document=doc,
                score=1.5,  # Invalid score
                context="Test context",
                citation="",
                relevance_explanation=""
            )
    
    def test_enhanced_search_result_from_basic(self, sample_documents):
        """Test creation from basic SearchResult."""
        doc = sample_documents[0]
        basic_result = SearchResult(document=doc, score=0.8, distance=0.2)
        
        enhanced = EnhancedSearchResult.from_search_result(basic_result)
        
        assert enhanced.document == doc
        assert enhanced.score == 0.8
        assert enhanced.distance == 0.2
        assert len(enhanced.context) > 0
        assert len(enhanced.citation) > 0
    
    def test_citation_auto_generation(self, sample_documents):
        """Test automatic citation generation."""
        doc = sample_documents[0]
        
        enhanced = EnhancedSearchResult(
            document=doc,
            score=0.8,
            context="Test context",
            citation="",  # Empty citation should be auto-generated
            relevance_explanation=""
        )
        
        assert "python_tutorial.md" in enhanced.citation
        assert ".md" in enhanced.citation
        assert "2024-01-15" in enhanced.citation


class TestQAResponse:
    """Test cases for QAResponse model."""
    
    def test_qa_response_creation(self, sample_documents):
        """Test QAResponse creation and validation."""
        enhanced_sources = [
            EnhancedSearchResult(
                document=sample_documents[0],
                score=0.9,
                context="Test context",
                citation="test.md",
                relevance_explanation="High relevance"
            )
        ]
        
        response = QAResponse(
            question="What is Python?",
            answer="Python is a programming language.",
            sources=enhanced_sources,
            confidence_score=0.85,
            processing_time=0.5,
            suggestions=["Try more specific terms"],
            metadata={"custom": "value"}
        )
        
        assert response.question == "What is Python?"
        assert response.answer == "Python is a programming language."
        assert len(response.sources) == 1
        assert response.confidence_score == 0.85
        assert response.processing_time == 0.5
        assert len(response.suggestions) == 1
        
        # Check auto-generated metadata
        assert response.metadata["sources_count"] == 1
        assert response.metadata["max_source_score"] == 0.9
        assert response.metadata["avg_source_score"] == 0.9
        assert "response_generated_at" in response.metadata
    
    def test_qa_response_validation(self):
        """Test QAResponse validation."""
        # Test invalid confidence score
        with pytest.raises(ValueError, match="Confidence score must be between 0 and 1"):
            QAResponse(
                question="Test",
                answer="Test answer",
                sources=[],
                confidence_score=1.5,  # Invalid
                processing_time=0.1,
                suggestions=[],
                metadata={}
            )
        
        # Test invalid processing time
        with pytest.raises(ValueError, match="Processing time must be non-negative"):
            QAResponse(
                question="Test",
                answer="Test answer", 
                sources=[],
                confidence_score=0.5,
                processing_time=-0.1,  # Invalid
                suggestions=[],
                metadata={}
            )
    
    def test_formatted_sources(self, sample_documents):
        """Test formatted sources output."""
        sources = [
            EnhancedSearchResult(
                document=sample_documents[0],
                score=0.9,
                context="Context 1",
                citation="doc1.md",
                relevance_explanation="High"
            ),
            EnhancedSearchResult(
                document=sample_documents[1],
                score=0.8,
                context="Context 2", 
                citation="doc2.txt",
                relevance_explanation="Good"
            )
        ]
        
        response = QAResponse(
            question="Test",
            answer="Test answer",
            sources=sources,
            confidence_score=0.8,
            processing_time=0.1,
            suggestions=[],
            metadata={}
        )
        
        formatted = response.get_formatted_sources()
        assert "1. doc1.md (Score: 0.900)" in formatted
        assert "2. doc2.txt (Score: 0.800)" in formatted
    
    def test_source_attribution(self, sample_documents):
        """Test source attribution formatting."""
        # Single source
        single_source = [
            EnhancedSearchResult(
                document=sample_documents[0],
                score=0.9,
                context="Context",
                citation="single.md",
                relevance_explanation="High"
            )
        ]
        
        response = QAResponse(
            question="Test",
            answer="Test",
            sources=single_source,
            confidence_score=0.8,
            processing_time=0.1,
            suggestions=[],
            metadata={}
        )
        
        attribution = response.get_source_attribution()
        assert attribution == "Source: single.md"
        
        # Multiple sources
        multiple_sources = single_source + [
            EnhancedSearchResult(
                document=sample_documents[1],
                score=0.8,
                context="Context 2",
                citation="multi.txt", 
                relevance_explanation="Good"
            )
        ]
        
        response.sources = multiple_sources
        attribution = response.get_source_attribution()
        assert attribution.startswith("Sources: ")
        assert "single.md" in attribution
        assert "multi.txt" in attribution


class TestCitationFormatter:
    """Test cases for CitationFormatter utility."""
    
    def test_basic_citation_formatting(self, sample_documents):
        """Test basic citation formatting."""
        doc = sample_documents[0]
        citation = CitationFormatter.format_basic_citation(doc)
        
        assert "python_tutorial.md" in citation
        assert "(.md)" in citation
    
    def test_detailed_citation_formatting(self, sample_documents):
        """Test detailed citation formatting with metadata."""
        doc = sample_documents[0]
        citation = CitationFormatter.format_detailed_citation(doc)
        
        assert "python_tutorial.md" in citation
        assert "(.md)" in citation
        assert "2024-01-15" in citation
        assert "Chunk 1/5" in citation  # chunk_position=0, chunk_count=5
        assert "1.0KB" in citation or "1024B" in citation  # file_size=1024 (either format acceptable)
    
    def test_apa_style_citation(self, sample_documents):
        """Test APA-style citation formatting."""
        doc = sample_documents[0]
        citation = CitationFormatter.format_apa_style(doc)
        
        assert "python_tutorial" in citation  # Filename without extension
        assert "(2024)" in citation  # Year from timestamp
        assert "python_tutorial.md" in citation  # Full filename


class TestQueryProcessor:
    """Test cases for QueryProcessor utility."""
    
    def test_abbreviation_expansion(self):
        """Test query abbreviation expansion."""
        query = "What is ai and ml in db systems?"
        expanded = QueryProcessor.expand_abbreviations(query)
        
        assert "artificial intelligence" in expanded
        assert "machine learning" in expanded
        assert "database" in expanded
    
    def test_question_type_detection(self):
        """Test question type detection."""
        test_cases = [
            ("What is Python?", "factual"),
            ("How do I install packages?", "procedural"),
            ("Is Python good for AI?", "boolean"),
            ("Can you use Python for web dev?", "boolean"),
            ("Python programming", "keyword_search"),
            ("Why does Python use indentation?", "procedural")
        ]
        
        for question, expected_type in test_cases:
            detected_type = QueryProcessor.detect_question_type(question)
            assert detected_type == expected_type
    
    def test_keyword_extraction(self):
        """Test keyword extraction from queries."""
        query = "How do I use Python for machine learning and data analysis?"
        keywords = QueryProcessor.extract_keywords(query)
        
        assert "python" in keywords
        assert "machine" in keywords
        assert "learning" in keywords
        assert "data" in keywords
        assert "analysis" in keywords
        
        # Stop words should be removed
        assert "do" not in keywords
        assert "for" not in keywords
        assert "and" not in keywords


@pytest.mark.integration
class TestQAInterfaceIntegration:
    """Integration tests for Q&A interface with real components."""
    
    def test_full_qa_workflow(self, qa_interface, mock_vector_client, sample_search_results):
        """Test complete Q&A workflow from question to response."""
        mock_vector_client.query.return_value = sample_search_results
        
        # Test various question types
        questions = [
            "What is Python used for?",
            "How do I learn machine learning?", 
            "Can Python handle web development?",
            "programming languages comparison"
        ]
        
        for question in questions:
            result = qa_interface.ask_question(question)
            
            # Verify complete workflow
            assert isinstance(result, QAResponse)
            assert result.question == question
            assert len(result.answer) > 0
            assert isinstance(result.sources, list)
            assert 0.0 <= result.confidence_score <= 1.0
            assert result.processing_time > 0
            assert isinstance(result.suggestions, list)
            assert isinstance(result.metadata, dict)
            
            # Verify metadata completeness
            assert "question_type" in result.metadata
            assert "keywords" in result.metadata
            assert "sources_count" in result.metadata