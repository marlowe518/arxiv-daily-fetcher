"""
Summary Generation Module

Generates concise one-sentence summaries of papers.
Supports both heuristic-based and extensible LLM-based approaches.
"""

import re
from abc import ABC, abstractmethod
from typing import Optional, Protocol


class Summarizer(ABC):
    """Abstract base class for paper summarizers."""
    
    @abstractmethod
    def summarize(self, title: str, abstract: str) -> str:
        """
        Generate a one-sentence summary.
        
        Args:
            title: Paper title
            abstract: Paper abstract
            
        Returns:
            One-sentence summary
        """
        pass
    
    def batch_summarize(self, papers: list) -> list:
        """
        Summarize multiple papers.
        
        Args:
            papers: List of paper objects with title and abstract attributes
            
        Returns:
            List of summaries (same order as input)
        """
        return [self.summarize(p.title, p.abstract) for p in papers]


class HeuristicSummarizer(Summarizer):
    """
    Heuristic-based summarizer using abstract truncation.
    
    Extracts the first sentence of the abstract, or a truncated
    portion if the first sentence is too long.
    """
    
    MAX_SUMMARY_LENGTH = 200
    MIN_SUMMARY_LENGTH = 50
    
    def __init__(self, max_length: int = MAX_SUMMARY_LENGTH):
        """
        Initialize the heuristic summarizer.
        
        Args:
            max_length: Maximum summary length in characters
        """
        self.max_length = max_length
    
    def summarize(self, title: str, abstract: str) -> str:
        """
        Generate a summary using heuristics on the abstract.
        
        Strategy:
        1. Try to extract the first sentence
        2. If too long, truncate at a word boundary
        3. Clean up common arXiv abstract artifacts
        
        Args:
            title: Paper title
            abstract: Paper abstract
            
        Returns:
            One-sentence summary
        """
        if not abstract or not abstract.strip():
            return "No abstract available."
        
        # Clean the abstract
        cleaned = self._clean_abstract(abstract)
        
        # Extract first sentence
        first_sentence = self._extract_first_sentence(cleaned)
        
        # Truncate if necessary
        summary = self._truncate_to_length(first_sentence, self.max_length)
        
        # Ensure it ends properly
        summary = self._ensure_proper_ending(summary)
        
        return summary
    
    def _clean_abstract(self, abstract: str) -> str:
        """
        Clean up common artifacts in arXiv abstracts.
        
        Args:
            abstract: Raw abstract text
            
        Returns:
            Cleaned abstract
        """
        # Remove HTML tags if any
        abstract = re.sub(r'<[^>]+>', '', abstract)
        
        # Normalize whitespace
        abstract = ' '.join(abstract.split())
        
        # Remove "Abstract:" or "Abstract -" prefix
        abstract = re.sub(r'^\s*[Aa]bstract\s*[:-]?\s*', '', abstract)
        
        return abstract.strip()
    
    def _extract_first_sentence(self, text: str) -> str:
        """
        Extract the first sentence from text.
        
        Handles common sentence ending patterns while
        being careful about abbreviations like "e.g." and "i.e."
        
        Args:
            text: Input text
            
        Returns:
            First sentence
        """
        # Common sentence endings (period, question mark, exclamation)
        # But be careful about common abbreviations
        abbreviations = ['e.g', 'i.e', 'et al', 'etc', 'vs', 'dr', 'mr', 'mrs', 'prof']
        
        # Replace abbreviations temporarily to avoid false sentence ends
        text_copy = text
        placeholders = {}
        for i, abbr in enumerate(abbreviations):
            # Match abbreviation followed by period (case insensitive)
            pattern = re.compile(r'\b' + abbr + r'\.', re.IGNORECASE)
            placeholder = f"«{i}»"
            text_copy = pattern.sub(placeholder, text_copy)
            placeholders[placeholder] = abbr + '.'
        
        # Find first sentence ending
        sentence_end = -1
        for i, char in enumerate(text_copy):
            if char in '.!?' and i > 10:  # Minimum sentence length
                sentence_end = i
                break
        
        if sentence_end > 0:
            first = text_copy[:sentence_end + 1]
        else:
            # No sentence ending found, use whole text
            first = text_copy
        
        # Restore abbreviations
        for placeholder, abbr in placeholders.items():
            first = first.replace(placeholder, abbr)
        
        return first.strip()
    
    def _truncate_to_length(self, text: str, max_length: int) -> str:
        """
        Truncate text to max_length at a word boundary.
        
        Args:
            text: Input text
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Find last space before max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > self.MIN_SUMMARY_LENGTH:
            return truncated[:last_space]
        else:
            return truncated
    
    def _ensure_proper_ending(self, text: str) -> str:
        """
        Ensure summary ends with proper punctuation.
        
        Args:
            text: Input text
            
        Returns:
            Text with proper ending
        """
        if not text:
            return text
        
        # Remove trailing spaces
        text = text.rstrip()
        
        # Add ellipsis if truncated
        if not text.endswith(('.', '!', '?')):
            text = text + '...'
        
        return text


class TitleBasedSummarizer(Summarizer):
    """
    Simple summarizer that uses the title with a prefix.
    
    Useful as a fallback when abstract is not available.
    """
    
    def summarize(self, title: str, abstract: str) -> str:
        """
        Generate a summary based on title.
        
        Args:
            title: Paper title
            abstract: Paper abstract (ignored)
            
        Returns:
            Title-based summary
        """
        if not title:
            return "No title available."
        
        return f"Paper titled: {title}"


class HybridSummarizer(Summarizer):
    """
    Hybrid summarizer that tries multiple strategies.
    
    Falls back to simpler methods if more complex ones fail.
    """
    
    def __init__(self, max_length: int = 200):
        """
        Initialize the hybrid summarizer.
        
        Args:
            max_length: Maximum summary length
        """
        self.heuristic = HeuristicSummarizer(max_length)
        self.title_based = TitleBasedSummarizer()
    
    def summarize(self, title: str, abstract: str) -> str:
        """
        Generate summary using best available method.
        
        Strategy:
        1. Try heuristic on abstract
        2. If abstract is too short/empty, use title-based
        
        Args:
            title: Paper title
            abstract: Paper abstract
            
        Returns:
            Best available summary
        """
        # Check if abstract is usable
        abstract_clean = abstract.strip() if abstract else ""
        
        if len(abstract_clean) < 50:
            return self.title_based.summarize(title, abstract)
        
        heuristic_summary = self.heuristic.summarize(title, abstract_clean)
        
        # If heuristic produced something useful, use it
        if len(heuristic_summary) > 20:
            return heuristic_summary
        
        # Otherwise fall back to title
        return self.title_based.summarize(title, abstract)


# Default summarizer instance
default_summarizer: Summarizer = HybridSummarizer()


def summarize_paper(title: str, abstract: str, summarizer: Optional[Summarizer] = None) -> str:
    """
    Convenience function to summarize a paper.
    
    Args:
        title: Paper title
        abstract: Paper abstract
        summarizer: Optional custom summarizer (uses default if None)
        
    Returns:
        One-sentence summary
    """
    if summarizer is None:
        summarizer = default_summarizer
    
    return summarizer.summarize(title, abstract)


def batch_summarize_papers(papers: list, summarizer: Optional[Summarizer] = None) -> list:
    """
    Summarize multiple papers.
    
    Args:
        papers: List of paper objects with title and abstract attributes
        summarizer: Optional custom summarizer
        
    Returns:
        List of summaries
    """
    if summarizer is None:
        summarizer = default_summarizer
    
    return summarizer.batch_summarize(papers)


# Extension point for LLM-based summarization
class LLMSummarizer(Summarizer):
    """
    Placeholder for LLM-based summarization.
    
    To implement:
    1. Subclass this and implement the summarize method
    2. Add API key handling
    3. Add prompt engineering
    4. Add error handling and fallback
    
    Example:
        class OpenAISummarizer(LLMSummarizer):
            def __init__(self, api_key):
                self.api_key = api_key
            
            def summarize(self, title, abstract):
                # Call OpenAI API
                # Return summary
                pass
    """
    
    def summarize(self, title: str, abstract: str) -> str:
        """
        Not implemented - subclass must override.
        
        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError(
            "LLMSummarizer is a placeholder. "
            "Subclass and implement summarize() with your LLM provider."
        )
