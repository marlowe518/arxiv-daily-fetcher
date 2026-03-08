"""
Tests for the pipeline orchestrator module.
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.config import Config, TopicConfig
from src.fetcher import ArxivPaper
from src.pipeline import (
    PipelineResult,
    ArxivPipeline,
    create_pipeline,
    run_pipeline
)


class MockPaper:
    """Mock paper for testing."""
    def __init__(self, arxiv_id, title, topic="Test"):
        self.arxiv_id = arxiv_id
        self.title = title
        self.abstract = f"Abstract for {title}"
        self.authors = ["Author 1", "Author 2"]
        self.categories = ["cs.LG"]
        self.published = datetime(2024, 1, 15)
        self.topic = topic


class TestPipelineResult(unittest.TestCase):
    """Test the PipelineResult class."""
    
    def test_initial_state(self):
        """Test initial state."""
        result = PipelineResult()
        
        self.assertEqual(result.new_papers_count, 0)
        self.assertEqual(result.duplicates_filtered, 0)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.papers_by_topic, {})
    
    def test_add_papers(self):
        """Test adding papers."""
        result = PipelineResult()
        
        mock_papers = [MockPaper("1", "Paper 1"), MockPaper("2", "Paper 2")]
        result.add_papers("Test Topic", mock_papers)
        
        self.assertEqual(result.new_papers_count, 2)
        self.assertEqual(len(result.papers_by_topic["Test Topic"]), 2)
    
    def test_add_error(self):
        """Test adding errors."""
        result = PipelineResult()
        
        result.add_error("Test error")
        
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Test error", result.errors)
    
    def test_summary(self):
        """Test summary generation."""
        result = PipelineResult()
        result.add_papers("Topic A", [MockPaper("1", "Paper 1")])
        result.add_papers("Topic B", [MockPaper("2", "Paper 2")])
        result.duplicates_filtered = 3
        
        summary = result.summary()
        
        self.assertIn("Topics processed: 2", summary)
        self.assertIn("New papers added: 2", summary)
        self.assertIn("Duplicates filtered: 3", summary)
        self.assertIn("Topic A: 1 papers", summary)


class TestArxivPipeline(unittest.TestCase):
    """Test the ArxivPipeline class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "state.json"
        self.output_file = Path(self.temp_dir) / "papers.md"
        
        self.config = Config(
            topics=[
                TopicConfig(
                    name="Test Topic",
                    queries=["test query"],
                    categories=["cs.LG"]
                )
            ],
            max_results_per_topic=10,
            lookback_days=7
        )
        
        # Create mock objects
        self.state_manager = MagicMock()
        self.markdown_writer = MagicMock()
        self.summarizer = MagicMock()
        self.fetcher = MagicMock()
        
        # Set up state_manager mock
        self.state_manager.has_seen.return_value = False
        
        # Set up summarizer mock
        self.summarizer.batch_summarize.return_value = ["Summary 1", "Summary 2"]
        
        self.pipeline = ArxivPipeline(
            config=self.config,
            state_manager=self.state_manager,
            markdown_writer=self.markdown_writer,
            summarizer=self.summarizer,
            fetcher=self.fetcher
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.pipeline.fetch_for_topic')
    def test_run_with_new_papers(self, mock_fetch_for_topic):
        """Test running pipeline with new papers."""
        # Mock fetch to return papers
        mock_papers = [
            MockPaper("2401.11111", "Paper 1"),
            MockPaper("2401.22222", "Paper 2")
        ]
        mock_fetch_for_topic.return_value = mock_papers
        
        # Run pipeline
        result = self.pipeline.run(dry_run=True)
        
        # Check results
        self.assertEqual(result.new_papers_count, 2)
        self.assertEqual(result.duplicates_filtered, 0)
        
        # Verify mocks called
        mock_fetch_for_topic.assert_called_once()
        self.summarizer.batch_summarize.assert_called_once()
        self.markdown_writer.insert_entries.assert_called_once()
    
    @patch('src.pipeline.fetch_for_topic')
    def test_run_with_duplicates(self, mock_fetch_for_topic):
        """Test running pipeline with duplicate papers."""
        # Set up state manager to mark one paper as seen
        def has_seen(arxiv_id):
            return arxiv_id == "2401.11111"
        
        self.state_manager.has_seen.side_effect = has_seen
        
        # Mock fetch to return papers
        mock_papers = [
            MockPaper("2401.11111", "Paper 1"),  # Duplicate
            MockPaper("2401.22222", "Paper 2")   # New
        ]
        mock_fetch_for_topic.return_value = mock_papers
        
        # Run pipeline
        result = self.pipeline.run(dry_run=True)
        
        # Check results
        self.assertEqual(result.new_papers_count, 1)
        self.assertEqual(result.duplicates_filtered, 1)
    
    @patch('src.pipeline.fetch_for_topic')
    def test_run_no_papers(self, mock_fetch_for_topic):
        """Test running pipeline with no papers."""
        mock_fetch_for_topic.return_value = []
        
        result = self.pipeline.run(dry_run=True)
        
        self.assertEqual(result.new_papers_count, 0)
        self.markdown_writer.insert_entries.assert_called_once()
    
    @patch('src.pipeline.fetch_for_topic')
    def test_run_with_error(self, mock_fetch_for_topic):
        """Test running pipeline with fetch error."""
        mock_fetch_for_topic.side_effect = Exception("Fetch failed")
        
        result = self.pipeline.run(dry_run=True)
        
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Fetch failed", result.errors[0])


class TestCreatePipeline(unittest.TestCase):
    """Test the create_pipeline factory function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a valid config file
        self.config_path = Path(self.temp_dir) / "config.yaml"
        self.config_path.write_text("""
topics:
  - name: Test
    queries: ["test"]
    categories: [cs.LG]
""")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_pipeline(self):
        """Test creating pipeline with defaults."""
        data_dir = Path(self.temp_dir) / "data"
        output_dir = Path(self.temp_dir) / "output"
        
        pipeline = create_pipeline(
            config_path=str(self.config_path),
            data_dir=str(data_dir),
            output_dir=str(output_dir)
        )
        
        self.assertIsInstance(pipeline, ArxivPipeline)
        self.assertEqual(len(pipeline.config.topics), 1)


if __name__ == '__main__':
    unittest.main()
