"""
Tests for the state manager and deduplication module.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.state_manager import StateManager, PaperFilter, create_state_manager


class TestStateManager(unittest.TestCase):
    """Test the StateManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "test_state.json")
        self.manager = StateManager(self.state_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_has_seen_empty(self):
        """Test that unseen papers return False."""
        self.assertFalse(self.manager.has_seen("2401.12345"))
    
    def test_add_and_check(self):
        """Test adding a paper and checking if seen."""
        self.manager.add_paper(
            arxiv_id="2401.12345",
            title="Test Paper",
            authors=["Author 1"],
            published=datetime(2024, 1, 15),
            topic="Test Topic"
        )
        
        self.assertTrue(self.manager.has_seen("2401.12345"))
        self.assertFalse(self.manager.has_seen("2401.99999"))
    
    def test_save_and_load(self):
        """Test saving and loading state."""
        # Add papers
        self.manager.add_paper(
            arxiv_id="2401.12345",
            title="Test Paper 1",
            authors=["Author 1"],
            published=datetime(2024, 1, 15),
            topic="Topic A"
        )
        self.manager.add_paper(
            arxiv_id="2401.67890",
            title="Test Paper 2",
            authors=["Author 2"],
            published=datetime(2024, 1, 16),
            topic="Topic B"
        )
        
        # Save
        self.manager.save()
        
        # Verify file exists
        self.assertTrue(Path(self.state_file).exists())
        
        # Load in new manager
        new_manager = StateManager(self.state_file)
        
        self.assertTrue(new_manager.has_seen("2401.12345"))
        self.assertTrue(new_manager.has_seen("2401.67890"))
        self.assertEqual(len(new_manager.get_all_papers()), 2)
    
    def test_get_paper(self):
        """Test retrieving paper metadata."""
        self.manager.add_paper(
            arxiv_id="2401.12345",
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            published=datetime(2024, 1, 15),
            topic="Test Topic",
            categories=["cs.LG", "cs.AI"]
        )
        
        paper = self.manager.get_paper("2401.12345")
        
        self.assertIsNotNone(paper)
        self.assertEqual(paper['title'], "Test Paper")
        self.assertEqual(len(paper['authors']), 2)
        self.assertEqual(paper['topic'], "Test Topic")
        self.assertEqual(paper['categories'], ["cs.LG", "cs.AI"])
    
    def test_get_paper_not_found(self):
        """Test retrieving non-existent paper."""
        paper = self.manager.get_paper("nonexistent")
        self.assertIsNone(paper)
    
    def test_remove_paper(self):
        """Test removing a paper."""
        self.manager.add_paper(
            arxiv_id="2401.12345",
            title="Test Paper",
            authors=["Author"],
            published=datetime.now(),
            topic="Topic"
        )
        
        self.assertTrue(self.manager.has_seen("2401.12345"))
        
        removed = self.manager.remove_paper("2401.12345")
        
        self.assertTrue(removed)
        self.assertFalse(self.manager.has_seen("2401.12345"))
    
    def test_remove_paper_not_found(self):
        """Test removing non-existent paper."""
        removed = self.manager.remove_paper("nonexistent")
        self.assertFalse(removed)
    
    def test_clear(self):
        """Test clearing all papers."""
        self.manager.add_paper(
            arxiv_id="2401.12345",
            title="Test Paper",
            authors=["Author"],
            published=datetime.now(),
            topic="Topic"
        )
        
        self.assertEqual(len(self.manager.get_all_papers()), 1)
        
        self.manager.clear()
        
        self.assertEqual(len(self.manager.get_all_papers()), 0)
        self.assertFalse(self.manager.has_seen("2401.12345"))
    
    def test_get_stats(self):
        """Test getting statistics."""
        self.manager.add_paper(
            arxiv_id="2401.11111",
            title="Paper 1",
            authors=["A"],
            published=datetime.now(),
            topic="Topic A"
        )
        self.manager.add_paper(
            arxiv_id="2401.22222",
            title="Paper 2",
            authors=["B"],
            published=datetime.now(),
            topic="Topic A"
        )
        self.manager.add_paper(
            arxiv_id="2401.33333",
            title="Paper 3",
            authors=["C"],
            published=datetime.now(),
            topic="Topic B"
        )
        
        stats = self.manager.get_stats()
        
        self.assertEqual(stats['total_papers'], 3)
        self.assertEqual(stats['papers_by_topic']['Topic A'], 2)
        self.assertEqual(stats['papers_by_topic']['Topic B'], 1)
        self.assertIn('last_updated', stats)
    
    def test_add_papers_batch(self):
        """Test adding multiple papers at once."""
        papers = [
            {
                'arxiv_id': '2401.11111',
                'title': 'Paper 1',
                'authors': ['A'],
                'published': datetime.now(),
                'topic': 'Topic A'
            },
            {
                'arxiv_id': '2401.22222',
                'title': 'Paper 2',
                'authors': ['B'],
                'published': datetime.now(),
                'topic': 'Topic B'
            }
        ]
        
        self.manager.add_papers_batch(papers)
        
        self.assertEqual(len(self.manager.get_all_papers()), 2)
        self.assertTrue(self.manager.has_seen('2401.11111'))
        self.assertTrue(self.manager.has_seen('2401.22222'))
    
    def test_load_corrupted_file(self):
        """Test handling of corrupted state file."""
        # Write invalid JSON
        with open(self.state_file, 'w') as f:
            f.write("not valid json")
        
        # Should not raise exception
        manager = StateManager(self.state_file)
        self.assertEqual(len(manager.get_all_papers()), 0)
    
    def test_load_old_format_list(self):
        """Test loading state in old list format."""
        # Write old format (list of papers)
        old_data = [
            {
                'arxiv_id': '2401.12345',
                'title': 'Old Format Paper',
                'authors': ['Author'],
                'published': '2024-01-15T12:00:00',
                'topic': 'Topic'
            }
        ]
        with open(self.state_file, 'w') as f:
            json.dump(old_data, f)
        
        manager = StateManager(self.state_file)
        
        self.assertTrue(manager.has_seen('2401.12345'))
        paper = manager.get_paper('2401.12345')
        self.assertEqual(paper['title'], 'Old Format Paper')


class MockPaper:
    """Mock paper object for testing."""
    def __init__(self, arxiv_id, title):
        self.arxiv_id = arxiv_id
        self.title = title


class TestPaperFilter(unittest.TestCase):
    """Test the PaperFilter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "test_state.json")
        self.state_manager = StateManager(self.state_file)
        self.filter = PaperFilter(self.state_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_filter_new_papers_all_new(self):
        """Test filtering when all papers are new."""
        papers = [
            MockPaper("2401.11111", "Paper 1"),
            MockPaper("2401.22222", "Paper 2"),
        ]
        
        new_papers = self.filter.filter_new_papers(papers, "Test Topic")
        
        self.assertEqual(len(new_papers), 2)
    
    def test_filter_new_papers_some_seen(self):
        """Test filtering when some papers are already seen."""
        # Pre-mark one paper as seen
        self.state_manager.add_paper(
            arxiv_id="2401.11111",
            title="Existing Paper",
            authors=["A"],
            published=datetime.now(),
            topic="Existing Topic"
        )
        
        papers = [
            MockPaper("2401.11111", "Paper 1"),  # Already seen
            MockPaper("2401.22222", "Paper 2"),  # New
        ]
        
        new_papers = self.filter.filter_new_papers(papers, "Test Topic")
        
        self.assertEqual(len(new_papers), 1)
        self.assertEqual(new_papers[0].arxiv_id, "2401.22222")
    
    def test_filter_new_papers_all_seen(self):
        """Test filtering when all papers are already seen."""
        # Pre-mark all papers as seen
        self.state_manager.add_paper(
            arxiv_id="2401.11111",
            title="Existing Paper 1",
            authors=["A"],
            published=datetime.now(),
            topic="Existing Topic"
        )
        self.state_manager.add_paper(
            arxiv_id="2401.22222",
            title="Existing Paper 2",
            authors=["B"],
            published=datetime.now(),
            topic="Existing Topic"
        )
        
        papers = [
            MockPaper("2401.11111", "Paper 1"),
            MockPaper("2401.22222", "Paper 2"),
        ]
        
        new_papers = self.filter.filter_new_papers(papers, "Test Topic")
        
        self.assertEqual(len(new_papers), 0)
    
    def test_deduplicate_across_topics(self):
        """Test deduplication across multiple topics."""
        papers_by_topic = {
            "Topic A": [
                MockPaper("2401.11111", "Paper 1"),
                MockPaper("2401.22222", "Paper 2"),
            ],
            "Topic B": [
                MockPaper("2401.22222", "Paper 2"),  # Duplicate
                MockPaper("2401.33333", "Paper 3"),
            ]
        }
        
        result = self.filter.deduplicate_across_topics(papers_by_topic)
        
        # Topic A should have both papers
        self.assertEqual(len(result["Topic A"]), 2)
        # Topic B should only have paper 3 (paper 2 is duplicate from Topic A)
        self.assertEqual(len(result["Topic B"]), 1)
        self.assertEqual(result["Topic B"][0].arxiv_id, "2401.33333")


class TestCreateStateManager(unittest.TestCase):
    """Test the factory function."""
    
    def test_create_with_default_path(self):
        """Test creating state manager with default path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = create_state_manager(tmpdir)
            
            self.assertIsInstance(manager, StateManager)
            self.assertEqual(manager.state_file, Path(tmpdir) / "seen_papers.json")


if __name__ == '__main__':
    unittest.main()
