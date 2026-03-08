"""
Tests for the arXiv fetcher module.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.fetcher import ArxivFetcher, ArxivPaper, fetch_for_topic


class TestArxivPaper(unittest.TestCase):
    """Test the ArxivPaper dataclass."""
    
    def test_paper_creation(self):
        """Test creating an ArxivPaper instance."""
        paper = ArxivPaper(
            arxiv_id="2401.12345",
            title="Test Paper Title",
            authors=["John Doe", "Jane Smith"],
            abstract="This is a test abstract.",
            categories=["cs.LG", "cs.AI"],
            published=datetime(2024, 1, 15),
            updated=datetime(2024, 1, 15),
            pdf_url="http://arxiv.org/pdf/2401.12345.pdf",
            arxiv_url="http://arxiv.org/abs/2401.12345",
            primary_category="cs.LG"
        )
        
        self.assertEqual(paper.arxiv_id, "2401.12345")
        self.assertEqual(paper.title, "Test Paper Title")
        self.assertEqual(len(paper.authors), 2)
        self.assertEqual(paper.primary_category, "cs.LG")
    
    def test_title_cleanup(self):
        """Test that newlines and extra spaces are cleaned from title."""
        paper = ArxivPaper(
            arxiv_id="2401.12345",
            title="Test\nPaper\n  Title",
            authors=["Author"],
            abstract="Abstract",
            categories=["cs.LG"],
            published=datetime.now(),
            updated=datetime.now(),
            pdf_url="",
            arxiv_url="",
            primary_category="cs.LG"
        )
        
        self.assertEqual(paper.title, "Test Paper Title")
    
    def test_abstract_cleanup(self):
        """Test that abstract whitespace is normalized."""
        paper = ArxivPaper(
            arxiv_id="2401.12345",
            title="Title",
            authors=["Author"],
            abstract="This   is\na\n  test abstract",
            categories=["cs.LG"],
            published=datetime.now(),
            updated=datetime.now(),
            pdf_url="",
            arxiv_url="",
            primary_category="cs.LG"
        )
        
        self.assertEqual(paper.abstract, "This is a test abstract")


class TestArxivFetcher(unittest.TestCase):
    """Test the ArxivFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ArxivFetcher(delay=0)  # No delay for tests
    
    def test_build_query_simple(self):
        """Test building a simple query."""
        queries = ["graph neural networks"]
        categories = ["cs.LG"]
        
        query_str = self.fetcher._build_query(queries, categories)
        
        self.assertIn("graph", query_str.lower())
        self.assertIn("cs.LG", query_str)
    
    def test_build_query_multiple_keywords(self):
        """Test building query with multiple keywords."""
        queries = ["graph neural networks", "GNN"]
        categories = []
        
        query_str = self.fetcher._build_query(queries, categories)
        
        # Should contain OR between keywords
        self.assertIn("OR", query_str)
        self.assertIn("graph", query_str.lower())
        self.assertIn("GNN", query_str)
    
    def test_build_query_multiple_categories(self):
        """Test building query with multiple categories."""
        queries = []
        categories = ["cs.LG", "cs.AI"]
        
        query_str = self.fetcher._build_query(queries, categories)
        
        # Should contain OR between categories
        self.assertIn("OR", query_str)
        self.assertIn("cs.LG", query_str)
        self.assertIn("cs.AI", query_str)
        self.assertIn("cat:", query_str)
    
    def test_build_query_combined(self):
        """Test building query with both keywords and categories."""
        queries = ["differential privacy"]
        categories = ["cs.CR", "cs.LG"]
        
        query_str = self.fetcher._build_query(queries, categories)
        
        # Should contain AND between keyword and category parts
        self.assertIn("AND", query_str)
        self.assertIn("differential", query_str.lower())
        self.assertIn("cs.CR", query_str)
    
    @patch('src.fetcher.requests.get')
    def test_fetch_papers_success(self, mock_get):
        """Test successful paper fetching."""
        # Mock response with sample Atom feed
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
            <title>Search Results</title>
            <entry>
                <id>http://arxiv.org/abs/2401.12345</id>
                <title>Test Paper on Machine Learning</title>
                <summary>This is a test abstract about ML.</summary>
                <published>2024-01-15T12:00:00Z</published>
                <updated>2024-01-15T12:00:00Z</updated>
                <author><name>John Doe</name></author>
                <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
                <arxiv:primary_category term="cs.LG"/>
            </entry>
        </feed>'''
        mock_get.return_value = mock_response
        
        papers = self.fetcher.fetch_papers(
            queries=["machine learning"],
            categories=["cs.LG"],
            max_results=10
        )
        
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].arxiv_id, "2401.12345")
        self.assertEqual(papers[0].title, "Test Paper on Machine Learning")
        self.assertEqual(papers[0].primary_category, "cs.LG")
    
    @patch('src.fetcher.requests.get')
    def test_fetch_papers_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        from src.fetcher import ArxivFetchError
        import requests
        
        mock_get.side_effect = requests.RequestException("Connection error")
        
        with self.assertRaises(ArxivFetchError):
            self.fetcher.fetch_papers(
                queries=["test"],
                categories=["cs.LG"],
                max_results=10
            )
    
    def test_parse_entry_with_version(self):
        """Test parsing entry with version suffix in ID."""
        # Create a proper mock that behaves like feedparser entry
        class MockEntry:
            def __init__(self):
                self.id = "http://arxiv.org/abs/2401.12345v2"
                self.title = "Test Paper"
                self.summary = "Test abstract"
                self.published = "2024-01-15T12:00:00Z"
                self.updated = "2024-01-15T12:00:00Z"
                self.authors = [{'name': 'John Doe'}]
                self.tags = [{'term': 'cs.LG'}]
                self.arxiv_primary_category = {'term': 'cs.LG'}
            
            def get(self, key, default=''):
                return getattr(self, key, default)
        
        mock_entry = MockEntry()
        paper = self.fetcher._parse_entry(mock_entry)
        
        # Version suffix should be stripped
        self.assertEqual(paper.arxiv_id, "2401.12345")


class TestFetchForTopic(unittest.TestCase):
    """Test the fetch_for_topic convenience function."""
    
    @patch.object(ArxivFetcher, 'fetch_papers')
    def test_fetch_for_topic(self, mock_fetch):
        """Test fetching papers for a specific topic."""
        # Mock return value
        mock_papers = [
            ArxivPaper(
                arxiv_id="2401.12345",
                title="Test Paper",
                authors=["Author"],
                abstract="Abstract",
                categories=["cs.LG"],
                published=datetime.now(),
                updated=datetime.now(),
                pdf_url="",
                arxiv_url="",
                primary_category="cs.LG"
            )
        ]
        mock_fetch.return_value = mock_papers
        
        fetcher = ArxivFetcher(delay=0)
        papers = fetch_for_topic(
            fetcher=fetcher,
            topic_name="Test Topic",
            queries=["query1", "query2"],
            categories=["cs.LG"],
            max_results=10
        )
        
        self.assertEqual(len(papers), 1)
        mock_fetch.assert_called_once_with(
            queries=["query1", "query2"],
            categories=["cs.LG"],
            max_results=10,
            lookback_days=None
        )


class TestIntegrationRealFetch(unittest.TestCase):
    """
    Integration tests that make real arXiv API calls.
    These are skipped by default to avoid rate limiting.
    """
    
    @unittest.skip("Skipping real API call - run manually with: python -m pytest tests/test_fetcher.py::TestIntegrationRealFetch -v")
    def test_real_fetch_single_result(self):
        """Test fetching a single real result from arXiv."""
        fetcher = ArxivFetcher(delay=3)
        
        # Fetch a well-known paper
        papers = fetcher.fetch_papers(
            queries=["attention is all you need"],
            categories=["cs.CL"],
            max_results=1
        )
        
        self.assertGreaterEqual(len(papers), 0)
        if papers:
            paper = papers[0]
            self.assertTrue(len(paper.arxiv_id) > 0)
            self.assertTrue(len(paper.title) > 0)
            self.assertTrue(len(paper.authors) > 0)
            print(f"\nFetched paper: {paper.title} ({paper.arxiv_id})")


if __name__ == '__main__':
    unittest.main()
