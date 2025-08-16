"""
Enhanced Question-Answering Interface for RAG operations.

This module provides natural language question processing with enhanced context
analysis, source attribution, and structured response generation.
"""

import time
from typing import List

from mcp_rag_playground.config.logging_config import get_logger
from mcp_rag_playground.models.qa_models import (
    EnhancedSearchResult, QAResponse, QueryProcessor
)
from mcp_rag_playground.vectordb.vector_client import VectorClient
from mcp_rag_playground.vectordb.vector_db_interface import SearchResult

logger = get_logger(__name__)

class QuestionAnsweringInterface:
    """
    Enhanced question-answering interface with natural language processing.
    
    Provides sophisticated query processing, context-aware response generation,
    and comprehensive source attribution for RAG-based question answering.
    """
    
    def __init__(self, vector_client: VectorClient, collection_name: str = "rag_collection"):
        """
        Initialize the Q&A interface.
        
        Args:
            vector_client: Configured VectorClient instance
            collection_name: Name for the document collection
        """
        self.vector_client = vector_client
        self.collection_name = collection_name
        self.vector_client.collection_name = collection_name
        logger.info(f"QuestionAnsweringInterface initialized with collection: {collection_name}")
    
    def ask_question(self, 
                    question: str, 
                    max_sources: int = 5,
                    include_context: bool = True,
                    min_score: float = 0.3,
                    expand_query: bool = True) -> QAResponse:
        """
        Ask a natural language question and get an enhanced answer with sources.
        
        Args:
            question: The natural language question
            max_sources: Maximum number of source documents to include
            include_context: Whether to include context snippets in sources
            min_score: Minimum similarity score threshold
            expand_query: Whether to apply query expansion and preprocessing
            
        Returns:
            QAResponse with structured answer, sources, and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing question: '{question}' (max_sources: {max_sources})")
            
            if not question or not question.strip():
                logger.warning("Empty question provided")
                return self._create_error_response(
                    question, "Question cannot be empty", start_time
                )
            
            # Preprocess the query
            processed_query = self._preprocess_query(question) if expand_query else question.strip()
            question_type = QueryProcessor.detect_question_type(question)
            keywords = QueryProcessor.extract_keywords(question)
            
            logger.debug(f"Question type: {question_type}, Keywords: {keywords}")
            
            # Perform semantic search
            search_results = self.vector_client.query(
                processed_query,
                limit=max(max_sources * 2, 10),  # Get more results for better filtering
                min_score=min_score
            )
            
            if not search_results:
                logger.info(f"No relevant documents found for: '{question}'")
                return self._create_no_results_response(question, start_time)
            
            # Enhance search results with context and citations
            enhanced_sources = self._enhance_search_results(
                search_results[:max_sources], 
                question, 
                include_context
            )
            
            # Generate structured answer
            answer = self._generate_answer(question, enhanced_sources, question_type)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(enhanced_sources, question_type)
            
            # Generate query suggestions
            suggestions = self._generate_query_suggestions(question, enhanced_sources, keywords)
            
            processing_time = time.time() - start_time
            
            response = QAResponse(
                question=question,
                answer=answer,
                sources=enhanced_sources,
                confidence_score=confidence_score,
                processing_time=processing_time,
                suggestions=suggestions,
                metadata={
                    "processed_query": processed_query,
                    "question_type": question_type,
                    "keywords": keywords,
                    "original_results_count": len(search_results),
                    "min_score_used": min_score
                }
            )
            
            logger.info(f"Q&A completed in {processing_time:.2f}s with {len(enhanced_sources)} sources")
            return response
            
        except Exception as e:
            logger.error(f"Error processing question '{question}': {e}")
            return self._create_error_response(question, str(e), start_time)
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess and enhance the query for better search results."""
        # Basic cleaning
        processed = query.strip()
        
        # Expand abbreviations
        processed = QueryProcessor.expand_abbreviations(processed)
        
        # Add context for question types
        question_type = QueryProcessor.detect_question_type(query)
        if question_type == "procedural" and not any(word in processed.lower() for word in ["how", "step", "method", "process"]):
            processed = f"how to {processed}"
        
        logger.debug(f"Query preprocessing: '{query}' -> '{processed}'")
        return processed
    
    def _enhance_search_results(self, 
                               search_results: List[SearchResult], 
                               question: str,
                               include_context: bool) -> List[EnhancedSearchResult]:
        """Convert basic search results to enhanced results with context and citations."""
        enhanced_results = []
        
        for result in search_results:
            try:
                # Generate context snippet
                context = self._extract_relevant_context(result.document.content, question) if include_context else result.document.content[:200]
                
                # Generate relevance explanation
                relevance_explanation = self._explain_relevance(result, question)
                
                # Create enhanced result
                enhanced_result = EnhancedSearchResult(
                    document=result.document,
                    score=result.score,
                    distance=getattr(result, 'distance', 0.0),
                    context=context,
                    citation="",  # Will be auto-generated
                    relevance_explanation=relevance_explanation
                )
                
                enhanced_results.append(enhanced_result)
                
            except Exception as e:
                logger.warning(f"Error enhancing search result: {e}")
                # Fall back to basic enhancement
                enhanced_results.append(EnhancedSearchResult.from_search_result(result))
        
        return enhanced_results
    
    def _extract_relevant_context(self, content: str, question: str, context_length: int = 300) -> str:
        """Extract the most relevant portion of content based on the question."""
        question_keywords = set(QueryProcessor.extract_keywords(question.lower()))
        
        if not question_keywords:
            # Fallback to beginning of content
            return content[:context_length] + ("..." if len(content) > context_length else "")
        
        # Split content into sentences/chunks
        sentences = content.replace('\n', ' ').split('. ')
        
        # Score each sentence based on keyword overlap
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            sentence_words = set(sentence.lower().split())
            overlap = len(question_keywords.intersection(sentence_words))
            scored_sentences.append((overlap, i, sentence))
        
        # Sort by relevance score
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Select best sentences within context length
        selected_text = ""
        for score, _, sentence in scored_sentences:
            if score == 0:
                break
            if len(selected_text) + len(sentence) + 2 <= context_length:
                if selected_text:
                    selected_text += ". "
                selected_text += sentence
            else:
                break
        
        # If no relevant sentences found or too short, use beginning
        if not selected_text or len(selected_text) < 50:
            selected_text = content[:context_length]
        
        if len(content) > len(selected_text):
            selected_text += "..."
        
        return selected_text
    
    def _explain_relevance(self, result: SearchResult, question: str) -> str:
        """Generate an explanation for why this result is relevant to the question."""
        score = result.score
        
        if score >= 0.9:
            return f"Highly relevant match (score: {score:.3f}) - contains very similar content to your question"
        elif score >= 0.8:
            return f"Strong relevance (score: {score:.3f}) - closely related to your question"
        elif score >= 0.7:
            return f"Good relevance (score: {score:.3f}) - contains relevant information"
        elif score >= 0.5:
            return f"Moderate relevance (score: {score:.3f}) - partially related content"
        else:
            return f"Lower relevance (score: {score:.3f}) - may contain related concepts"
    
    def _generate_answer(self, 
                        question: str, 
                        sources: List[EnhancedSearchResult], 
                        question_type: str) -> str:
        """Generate a structured answer based on the sources and question type."""
        if not sources:
            return "I couldn't find relevant information to answer your question. Please try rephrasing your question or check if the relevant documents are in the knowledge base."
        
        # Create answer based on question type
        if question_type == "boolean":
            return self._generate_boolean_answer(question, sources)
        elif question_type == "factual":
            return self._generate_factual_answer(question, sources)
        elif question_type == "procedural":
            return self._generate_procedural_answer(question, sources)
        else:
            return self._generate_general_answer(question, sources)
    
    def _generate_boolean_answer(self, question: str, sources: List[EnhancedSearchResult]) -> str:
        """Generate a yes/no answer with supporting evidence."""
        primary_source = sources[0]
        confidence = "high" if primary_source.score >= 0.8 else "moderate" if primary_source.score >= 0.6 else "low"
        
        answer = f"Based on the available information (confidence: {confidence}), "
        answer += f"the answer relates to content from {primary_source.citation}. "
        answer += f"\n\nRelevant context: {primary_source.context}"
        
        if len(sources) > 1:
            answer += f"\n\nAdditional supporting information found in {len(sources) - 1} other source(s)."
        
        return answer
    
    def _generate_factual_answer(self, question: str, sources: List[EnhancedSearchResult]) -> str:
        """Generate a factual answer with source attribution."""
        primary_source = sources[0]
        
        answer = f"According to {primary_source.citation}:\n\n{primary_source.context}"
        
        if len(sources) > 1:
            answer += f"\n\nAdditional information from other sources:\n"
            for source in sources[1:3]:  # Include up to 2 more sources
                answer += f"• {source.citation}: {source.context[:100]}...\n"
        
        return answer
    
    def _generate_procedural_answer(self, question: str, sources: List[EnhancedSearchResult]) -> str:
        """Generate a step-by-step or procedural answer."""
        answer = f"Based on {sources[0].citation}, here's the relevant information:\n\n"
        answer += sources[0].context
        
        # Look for step-like content in other sources
        step_sources = [s for s in sources[1:] if any(keyword in s.context.lower() 
                       for keyword in ["step", "first", "then", "next", "finally", "1.", "2.", "3."])]
        
        if step_sources:
            answer += "\n\nAdditional procedural information:\n"
            for source in step_sources[:2]:
                answer += f"• From {source.citation}: {source.context[:150]}...\n"
        
        return answer
    
    def _generate_general_answer(self, question: str, sources: List[EnhancedSearchResult]) -> str:
        """Generate a general answer combining multiple sources."""
        answer = f"Based on the available information:\n\n"
        
        # Combine context from top sources
        combined_context = ""
        for i, source in enumerate(sources[:3]):
            combined_context += f"{source.context} "
            if i < len(sources) - 1:
                combined_context += "\n\n"
        
        answer += combined_context
        
        # Add source attribution
        if len(sources) == 1:
            answer += f"\n\nSource: {sources[0].citation}"
        else:
            answer += f"\n\nSources: {', '.join(s.citation for s in sources[:3])}"
            if len(sources) > 3:
                answer += f" and {len(sources) - 3} more"
        
        return answer
    
    def _calculate_confidence_score(self, sources: List[EnhancedSearchResult], question_type: str) -> float:
        """Calculate confidence score for the answer based on source quality."""
        if not sources:
            return 0.0
        
        # Base confidence on top source score
        base_confidence = sources[0].score
        
        # Adjust based on question type
        if question_type == "factual":
            # Factual questions need high precision
            base_confidence *= 0.9
        elif question_type == "boolean":
            # Boolean questions can be more confident with moderate scores
            base_confidence = min(base_confidence * 1.1, 1.0)
        
        # Boost confidence if multiple sources agree (similar scores)
        if len(sources) > 1:
            score_variance = sum((s.score - sources[0].score) ** 2 for s in sources) / len(sources)
            if score_variance < 0.01:  # Low variance means consensus
                base_confidence = min(base_confidence * 1.05, 1.0)
        
        # Penalize if only low-quality sources
        if sources[0].score < 0.5:
            base_confidence *= 0.8
        
        return round(base_confidence, 3)
    
    def _generate_query_suggestions(self, 
                                  question: str, 
                                  sources: List[EnhancedSearchResult],
                                  keywords: List[str]) -> List[str]:
        """Generate suggestions for query refinement or related questions."""
        suggestions = []
        
        # Suggest more specific queries if low confidence
        if not sources or sources[0].score < 0.6:
            suggestions.append("Try using more specific terms or keywords")
            if keywords:
                suggestions.append(f"Consider focusing on specific terms like: {', '.join(keywords[:3])}")
        
        # Suggest related topics based on source content
        if sources:
            # Extract potential related terms from source metadata
            file_types = set()
            for source in sources:
                if source.document.file_type:
                    file_types.add(source.document.file_type)
            
            if file_types:
                type_str = ', '.join(sorted(file_types))
                suggestions.append(f"Related documents available in: {type_str} files")
        
        # Question type specific suggestions
        question_type = QueryProcessor.detect_question_type(question)
        if question_type == "procedural":
            suggestions.append("For step-by-step instructions, try asking 'How to...' or 'What are the steps...'")
        elif question_type == "factual":
            suggestions.append("For definitions, try asking 'What is...' or 'Define...'")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _create_error_response(self, question: str, error_message: str, start_time: float) -> QAResponse:
        """Create an error response for failed question processing."""
        processing_time = time.time() - start_time
        return QAResponse(
            question=question,
            answer=f"I encountered an error while processing your question: {error_message}",
            sources=[],
            confidence_score=0.0,
            processing_time=processing_time,
            suggestions=["Please try rephrasing your question", "Check if the question contains valid text"],
            metadata={"error": error_message}
        )
    
    def _create_no_results_response(self, question: str, start_time: float) -> QAResponse:
        """Create a response when no relevant documents are found."""
        processing_time = time.time() - start_time
        return QAResponse(
            question=question,
            answer="I couldn't find any relevant information in the knowledge base to answer your question.",
            sources=[],
            confidence_score=0.0,
            processing_time=processing_time,
            suggestions=[
                "Try using different keywords or phrases",
                "Check if relevant documents have been added to the knowledge base",
                "Consider using more general terms if your question is very specific"
            ],
            metadata={"reason": "no_relevant_documents"}
        )