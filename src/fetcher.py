"""
arXiv Paper Fetcher Module

Handles querying the arXiv API (Atom feed), parsing responses,
and returning structured paper metadata.
"""

import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree as ET

import feedparser
import requests


@dataclass
class ArxivPaper:
    """Represents a single arXiv paper with extracted metadata."""
    
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: datetime
    updated: datetime
    pdf_url: str
    arxiv_url: str
    primary_category: str
    
    def __post_init__(self):
        """Clean up fields after initialization."""
        # Clean title - remove newlines and extra spaces
        self.title = ' '.join(self.title.split())
        # Clean abstract - normalize whitespace
        self.abstract = ' '.join(self.abstract.split())


class ArxivFetcher:
    """
    Client for fetching papers from arXiv using the Atom feed API.
    
    Uses the arXiv API query interface:
    http://export.arxiv.org/api/query?search_query=...&start=...&max_results=...
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    DEFAULT_DELAY = 3.0  # Seconds between requests (arXiv rate limiting)
    
    def __init__(self, delay: float = DEFAULT_DELAY):
        """
        Initialize the fetcher.
        
        Args:
            delay: Seconds to wait between API requests
        """
        self.delay = delay
        self._last_request_time: Optional[float] = None
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()
    
    def _build_query(
        self, 
        queries: List[str], 
        categories: List[str],
        lookback_days: Optional[int] = None
    ) -> str:
        """
        Build the arXiv search query string.
        
        Args:
            queries: List of keyword search terms
            categories: List of arXiv categories (e.g., 'cs.LG')
            lookback_days: Only return papers from last N days
            
        Returns:
            URL-encoded query string
        """
        query_parts = []
        
        # Add keyword queries with OR
        if queries:
            keyword_query = ' OR '.join(f'"{q}"' for q in queries)
            query_parts.append(f"({keyword_query})")
        
        # Add category constraints with OR
        if categories:
            cat_query = ' OR '.join(f'cat:{cat}' for cat in categories)
            query_parts.append(f"({cat_query})")
        
        # Combine with AND
        full_query = ' AND '.join(query_parts)
        
        # Add date filter if specified
        if lookback_days:
            # arXiv uses submittedDate field
            # Format: [YYYYMMDD TO YYYYMMDD]
            end_date = datetime.now()
            start_date = end_date.replace(day=end_date.day - lookback_days)
            # Ensure valid date
            while start_date.day < 1:
                start_date = start_date.replace(month=start_date.month - 1)
                # Add days from previous month
                if start_date.month == 0:
                    start_date = start_date.replace(year=start_date.year - 1, month=12)
            
            date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')}* TO {end_date.strftime('%Y%m%d')}235959]"
            full_query = f"({full_query}) AND {date_query}"
        
        return urllib.parse.quote(full_query, safe='():[]*"')
    
    def fetch_papers(
        self,
        queries: List[str],
        categories: List[str],
        max_results: int = 20,
        lookback_days: Optional[int] = None
    ) -> List[ArxivPaper]:
        """
        Fetch papers from arXiv matching the given criteria.
        
        Args:
            queries: List of keyword search terms
            categories: List of arXiv category codes
            max_results: Maximum number of results to return
            lookback_days: Only return papers from last N days
            
        Returns:
            List of ArxivPaper objects
        """
        self._rate_limit()
        
        query_str = self._build_query(queries, categories, lookback_days)
        url = f"{self.BASE_URL}?search_query={query_str}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ArxivFetchError(f"Failed to fetch from arXiv: {e}") from e
        
        return self._parse_feed(response.content)
    
    def _parse_feed(self, feed_content: bytes) -> List[ArxivPaper]:
        """
        Parse the Atom feed response into ArxivPaper objects.
        
        Args:
            feed_content: Raw XML feed content
            
        Returns:
            List of parsed ArxivPaper objects
        """
        feed = feedparser.parse(feed_content)
        papers = []
        
        for entry in feed.entries:
            try:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)
            except Exception as e:
                # Log error but continue processing other entries
                print(f"Warning: Failed to parse entry: {e}")
                continue
        
        return papers
    
    def _parse_entry(self, entry) -> Optional[ArxivPaper]:
        """
        Parse a single feed entry into an ArxivPaper.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            ArxivPaper or None if parsing fails
        """
        # Extract arXiv ID from the ID field (format: http://arxiv.org/abs/xxxx.xxxxx)
        arxiv_id = entry.id.split('/')[-1]
        # Remove version suffix if present (e.g., v1, v2)
        arxiv_id = arxiv_id.split('v')[0]
        
        # Get authors - handle both dict-like and attribute access
        authors = []
        if hasattr(entry, 'authors'):
            for author in entry.authors:
                if isinstance(author, dict):
                    authors.append(author.get('name', ''))
                else:
                    authors.append(getattr(author, 'name', ''))
        
        # Get categories
        categories = []
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if isinstance(tag, dict):
                    categories.append(tag.get('term', ''))
                else:
                    categories.append(getattr(tag, 'term', ''))
        
        primary_category = ''
        if hasattr(entry, 'arxiv_primary_category'):
            pc = entry.arxiv_primary_category
            if isinstance(pc, dict):
                primary_category = pc.get('term', '')
            else:
                primary_category = getattr(pc, 'term', '')
        
        # Parse dates - handle both dict-like and attribute access
        published_str = entry.get('published', '') if hasattr(entry, 'get') else getattr(entry, 'published', '')
        updated_str = entry.get('updated', '') if hasattr(entry, 'get') else getattr(entry, 'updated', '')
        published = self._parse_date(published_str)
        updated = self._parse_date(updated_str)
        
        # Get URLs
        arxiv_url = entry.id
        pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"
        
        # Get abstract and title - handle both dict-like and attribute access
        abstract = entry.get('summary', '') if hasattr(entry, 'get') else getattr(entry, 'summary', '')
        title = entry.get('title', '') if hasattr(entry, 'get') else getattr(entry, 'title', '')
        
        return ArxivPaper(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            categories=categories,
            published=published,
            updated=updated,
            pdf_url=pdf_url,
            arxiv_url=arxiv_url,
            primary_category=primary_category
        )
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse an ISO format date string.
        
        Args:
            date_str: ISO format date string
            
        Returns:
            datetime object
        """
        if not date_str:
            return datetime.now()
        
        # Handle various ISO formats
        try:
            # Try with microseconds
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try without timezone
                return datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                # Fallback to current time
                return datetime.now()


class ArxivFetchError(Exception):
    """Exception raised when arXiv fetching fails."""
    pass


def fetch_for_topic(
    fetcher: ArxivFetcher,
    topic_name: str,
    queries: List[str],
    categories: List[str],
    max_results: int = 20,
    lookback_days: Optional[int] = None
) -> List[ArxivPaper]:
    """
    Convenience function to fetch papers for a specific topic.
    
    Args:
        fetcher: ArxivFetcher instance
        topic_name: Name of the topic (for logging)
        queries: List of keyword queries
        categories: List of arXiv categories
        max_results: Maximum results to fetch
        lookback_days: Only fetch papers from last N days
        
    Returns:
        List of ArxivPaper objects
    """
    print(f"Fetching papers for topic: {topic_name}")
    print(f"  Queries: {queries}")
    print(f"  Categories: {categories}")
    
    papers = fetcher.fetch_papers(
        queries=queries,
        categories=categories,
        max_results=max_results,
        lookback_days=lookback_days
    )
    
    print(f"  Found {len(papers)} papers")
    return papers
