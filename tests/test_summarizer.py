"""
Tests for the summarizer module.
"""

import unittest

from src.summarizer import (
    HeuristicSummarizer,
    TitleBasedSummarizer,
    HybridSummarizer,
    LLMSummarizer,
    summarize_paper,
    batch_summarize_papers
)


class MockPaper:
    """Mock paper for testing."""
    def __init__(self, title, abstract):
        self.title = title
        self.abstract = abstract


class TestHeuristicSummarizer(unittest.TestCase):
    """Test the HeuristicSummarizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.summarizer = HeuristicSummarizer()
    
    def test_summarize_simple(self):
        """Test basic summarization."""
        title = "Test Paper"
        abstract = "This is the first sentence. This is the second sentence."
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertEqual(summary, "This is the first sentence.")
    
    def test_summarize_empty_abstract(self):
        """Test handling of empty abstract."""
        title = "Test Paper"
        abstract = ""
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertEqual(summary, "No abstract available.")
    
    def test_summarize_whitespace_only(self):
        """Test handling of whitespace-only abstract."""
        title = "Test Paper"
        abstract = "   \n\t   "
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertEqual(summary, "No abstract available.")
    
    def test_summarize_long_abstract(self):
        """Test truncation of long abstract."""
        title = "Test Paper"
        abstract = "This is a very long sentence that goes on and on and on without ending and continues to grow with many words and never seems to stop adding more content making it exceed the maximum length significantly"
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertLess(len(summary), 250)  # Should be truncated
        # Since there's no period, it will be truncated and get ...
        self.assertTrue(summary.endswith('...'))
    
    def test_summarize_with_abbreviations(self):
        """Test handling of abbreviations like e.g. and i.e."""
        title = "Test Paper"
        abstract = "This paper uses e.g. machine learning and i.e. neural networks. The second sentence starts here."
        
        summary = self.summarizer.summarize(title, abstract)
        
        # Should not break at e.g. or i.e.
        self.assertIn("e.g.", summary)
        self.assertIn("i.e.", summary)
        self.assertNotIn("The second sentence", summary)
    
    def test_clean_abstract_html(self):
        """Test removal of HTML tags."""
        title = "Test Paper"
        abstract = "<p>This is <b>bold</b> text.</p>"
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertNotIn("<p>", summary)
        self.assertNotIn("</p>", summary)
        self.assertNotIn("<b>", summary)
        self.assertIn("bold", summary)
    
    def test_clean_abstract_prefix(self):
        """Test removal of 'Abstract:' prefix."""
        title = "Test Paper"
        abstract = "Abstract: This is the actual abstract."
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertNotIn("Abstract:", summary)
        self.assertIn("This is the actual abstract", summary)
    
    def test_ensure_ending_with_punctuation(self):
        """Test that summary ends with proper punctuation."""
        title = "Test Paper"
        abstract = "This sentence is cut off mid"
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertTrue(summary.endswith('...'))


class TestTitleBasedSummarizer(unittest.TestCase):
    """Test the TitleBasedSummarizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.summarizer = TitleBasedSummarizer()
    
    def test_summarize_with_title(self):
        """Test basic title-based summarization."""
        title = "Amazing Paper on AI"
        abstract = "Some abstract here"
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertIn("Amazing Paper on AI", summary)
    
    def test_summarize_empty_title(self):
        """Test handling of empty title."""
        title = ""
        abstract = "Some abstract"
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertEqual(summary, "No title available.")


class TestHybridSummarizer(unittest.TestCase):
    """Test the HybridSummarizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.summarizer = HybridSummarizer()
    
    def test_uses_heuristic_when_abstract_good(self):
        """Test that heuristic is used when abstract is available."""
        title = "The Title"
        abstract = "This is a good abstract with enough content. More details here."
        
        summary = self.summarizer.summarize(title, abstract)
        
        # Should use abstract content, not just title
        self.assertIn("abstract", summary.lower())
    
    def test_falls_back_to_title_when_abstract_short(self):
        """Test fallback to title when abstract is too short."""
        title = "Important Paper Title"
        abstract = "Too short"
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertIn("Important Paper Title", summary)
    
    def test_falls_back_to_title_when_abstract_empty(self):
        """Test fallback to title when abstract is empty."""
        title = "Important Paper Title"
        abstract = ""
        
        summary = self.summarizer.summarize(title, abstract)
        
        self.assertIn("Important Paper Title", summary)


class TestConvenienceFunctions(unittest.TestCase):
    """Test the convenience functions."""
    
    def test_summarize_paper_default(self):
        """Test summarize_paper with default summarizer."""
        title = "Test Title"
        abstract = "This is a test abstract. More content here."
        
        summary = summarize_paper(title, abstract)
        
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
    
    def test_summarize_paper_custom(self):
        """Test summarize_paper with custom summarizer."""
        title = "Test Title"
        abstract = "Test abstract"
        custom = TitleBasedSummarizer()
        
        summary = summarize_paper(title, abstract, custom)
        
        self.assertIn("Test Title", summary)
    
    def test_batch_summarize(self):
        """Test batch summarization."""
        papers = [
            MockPaper("Paper 1", "Abstract one. More details."),
            MockPaper("Paper 2", "Abstract two. More details."),
            MockPaper("Paper 3", "Abstract three. More details."),
        ]
        
        summaries = batch_summarize_papers(papers)
        
        self.assertEqual(len(summaries), 3)
        for summary in summaries:
            self.assertIsInstance(summary, str)
            self.assertGreater(len(summary), 0)


class TestLLMSummarizer(unittest.TestCase):
    """Test the LLM summarizer placeholder."""
    
    def test_raises_not_implemented(self):
        """Test that LLMSummarizer raises NotImplementedError."""
        summarizer = LLMSummarizer()
        
        with self.assertRaises(NotImplementedError):
            summarizer.summarize("Title", "Abstract")


class TestRealAbstracts(unittest.TestCase):
    """Test with realistic arXiv-style abstracts."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.summarizer = HeuristicSummarizer()
    
    def test_gnn_abstract(self):
        """Test with a GNN-style abstract."""
        abstract = (
            "Graph Neural Networks (GNNs) have emerged as a powerful tool for learning on graph-structured data. "
            "However, existing approaches struggle with scalability on large graphs. "
            "In this work, we propose a novel sampling-based approach that significantly reduces computational cost."
        )
        
        summary = self.summarizer.summarize("Title", abstract)
        
        # Should extract first sentence
        self.assertIn("Graph Neural Networks", summary)
        self.assertNotIn("In this work", summary)  # Should stop at first sentence
    
    def test_dp_abstract_with_latex(self):
        """Test with abstract containing LaTeX notation."""
        abstract = (
            "Differential privacy (DP) provides rigorous privacy guarantees for machine learning models. "
            "We analyze the privacy-utility tradeoff in DP-SGD, showing that $(\\epsilon, \\delta)$-DP "
            "can be improved using adaptive clipping strategies."
        )
        
        summary = self.summarizer.summarize("Title", abstract)
        
        self.assertIn("Differential privacy", summary)
        # LaTeX might be kept or cleaned depending on implementation
    
    def test_multi_sentence_abstract(self):
        """Test with a multi-sentence academic abstract."""
        abstract = (
            "Recommender systems are essential for personalized content delivery in modern platforms. "
            "Collaborative filtering remains a dominant approach, but faces cold-start challenges. "
            "We propose a hybrid method combining collaborative and content-based filtering. "
            "Experimental results on benchmark datasets demonstrate 15% improvement in NDCG@10."
        )
        
        summary = self.summarizer.summarize("Title", abstract)
        
        # Should only have first sentence
        self.assertIn("Recommender systems", summary)
        self.assertNotIn("cold-start", summary)
        self.assertNotIn("We propose", summary)


if __name__ == '__main__':
    unittest.main()
