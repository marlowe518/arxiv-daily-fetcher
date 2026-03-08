"""
Tests for the Markdown writer module.
"""

import tempfile
import unittest
from pathlib import Path

from src.markdown_writer import MarkdownTableEntry, MarkdownTableWriter, create_writer


class TestMarkdownTableEntry(unittest.TestCase):
    """Test the MarkdownTableEntry class."""
    
    def test_format_title_link(self):
        """Test title link formatting."""
        entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="Test",
            title="Amazing Paper",
            arxiv_id="2401.12345",
            authors=["Author"],
            categories=["cs.LG"],
            summary="Summary",
            arxiv_url="https://arxiv.org/abs/2401.12345"
        )
        
        result = entry.format_title_link()
        self.assertEqual(result, "[Amazing Paper](https://arxiv.org/abs/2401.12345)")
    
    def test_format_title_with_pipe(self):
        """Test escaping pipe characters in title."""
        entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="Test",
            title="Paper | A Study",
            arxiv_id="2401.12345",
            authors=["Author"],
            categories=["cs.LG"],
            summary="Summary",
            arxiv_url="https://arxiv.org/abs/2401.12345"
        )
        
        result = entry.format_title_link()
        self.assertIn("\\|", result)  # Pipe should be escaped
        self.assertIn("[Paper \\| A Study]", result)
    
    def test_to_row(self):
        """Test converting entry to table row (simplified format)."""
        entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="GNN",
            title="Graph Neural Networks Survey",
            arxiv_id="2401.12345",
            authors=["A. Author", "B. Writer"],
            categories=["cs.LG", "cs.AI"],
            summary="A comprehensive survey of GNNs.",
            arxiv_url="https://arxiv.org/abs/2401.12345"
        )
        
        row = entry.to_row()
        
        # Simplified format: only Date, Title, Summary
        self.assertIn("2024-01-15", row)
        self.assertIn("[Graph Neural Networks Survey]", row)
        self.assertIn("A comprehensive survey of GNNs.", row)
        # Should NOT have authors, categories in the row text (only in URL)
        self.assertNotIn("A. Author", row)
        self.assertNotIn("cs.LG", row)
        # Note: arxiv_id is in the URL, so we don't check for it here


class TestMarkdownTableWriter(unittest.TestCase):
    """Test the MarkdownTableWriter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.writer = MarkdownTableWriter(self.temp_dir, backup=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_new_file(self):
        """Test creating a new Markdown file for a topic."""
        entries = [
            MarkdownTableEntry(
                date="2024-01-15",
                topic="GNN",
                title="Paper 1",
                arxiv_id="2401.11111",
                authors=["Author A"],
                categories=["cs.LG"],
                summary="Summary 1",
                arxiv_url="https://arxiv.org/abs/2401.11111"
            )
        ]
        
        results = self.writer.insert_entries(entries)
        
        # Check file was created
        expected_file = Path(self.temp_dir) / "gnn.md"
        self.assertTrue(expected_file.exists())
        
        content = expected_file.read_text()
        # Should have simplified header
        self.assertIn("| Date | Title | One-line Summary |", content)
        self.assertIn("|------|-------|------------------|", content)
        self.assertIn("2401.11111", content)
    
    def test_insert_at_top(self):
        """Test that new entries are inserted at the top."""
        # First entry
        old_entry = MarkdownTableEntry(
            date="2024-01-10",
            topic="GNN",
            title="Old Paper",
            arxiv_id="2401.00001",
            authors=["Author A"],
            categories=["cs.LG"],
            summary="Old summary",
            arxiv_url="https://arxiv.org/abs/2401.00001"
        )
        self.writer.insert_entries([old_entry])
        
        # New entry
        new_entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="GNN",
            title="New Paper",
            arxiv_id="2401.00002",
            authors=["Author B"],
            categories=["cs.CR"],
            summary="New summary",
            arxiv_url="https://arxiv.org/abs/2401.00002"
        )
        self.writer.insert_entries([new_entry])
        
        content = (Path(self.temp_dir) / "gnn.md").read_text()
        lines = content.split('\n')
        
        # Find the data rows (skip header)
        data_rows = [l for l in lines if l.startswith('|') and 'Date' not in l and '---' not in l]
        
        # New paper should come before old paper
        self.assertIn("2401.00002", data_rows[0])
        self.assertIn("2401.00001", data_rows[1])
    
    def test_multiple_topics(self):
        """Test that different topics get different files."""
        entries = [
            MarkdownTableEntry(
                date="2024-01-15",
                topic="GNN",
                title="GNN Paper",
                arxiv_id="2401.11111",
                authors=["A"],
                categories=["cs.LG"],
                summary="GNN summary",
                arxiv_url="https://arxiv.org/abs/2401.11111"
            ),
            MarkdownTableEntry(
                date="2024-01-14",
                topic="Differential Privacy",
                title="DP Paper",
                arxiv_id="2401.22222",
                authors=["B"],
                categories=["cs.CR"],
                summary="DP summary",
                arxiv_url="https://arxiv.org/abs/2401.22222"
            )
        ]
        
        self.writer.insert_entries(entries)
        
        # Check both files were created
        gnn_file = Path(self.temp_dir) / "gnn.md"
        dp_file = Path(self.temp_dir) / "differential_privacy.md"
        
        self.assertTrue(gnn_file.exists())
        self.assertTrue(dp_file.exists())
        
        # Check content
        self.assertIn("GNN Paper", gnn_file.read_text())
        self.assertIn("DP Paper", dp_file.read_text())
    
    def test_dry_run(self):
        """Test dry-run mode doesn't modify file."""
        # Create initial file
        self.writer.insert_entries([
            MarkdownTableEntry(
                date="2024-01-10",
                topic="GNN",
                title="Existing",
                arxiv_id="2401.00001",
                authors=["Author"],
                categories=["cs.LG"],
                summary="Summary",
                arxiv_url="https://arxiv.org/abs/2401.00001"
            )
        ])
        
        initial_content = (Path(self.temp_dir) / "gnn.md").read_text()
        
        # Dry run with new entry
        new_entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="GNN",
            title="New",
            arxiv_id="2401.00002",
            authors=["Author"],
            categories=["cs.CR"],
            summary="New summary",
            arxiv_url="https://arxiv.org/abs/2401.00002"
        )
        
        self.writer.insert_entries([new_entry], dry_run=True)
        
        # Content should be unchanged
        final_content = (Path(self.temp_dir) / "gnn.md").read_text()
        self.assertEqual(initial_content, final_content)
    
    def test_empty_entries(self):
        """Test handling of empty entries list."""
        results = self.writer.insert_entries([])
        
        # Should return empty dict
        self.assertEqual(results, {})


class TestCreateWriter(unittest.TestCase):
    """Test the factory function."""
    
    def test_create_with_defaults(self):
        """Test creating writer with default paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = create_writer(tmpdir)
            
            self.assertIsInstance(writer, MarkdownTableWriter)
            self.assertEqual(writer.output_dir, Path(tmpdir))


if __name__ == '__main__':
    unittest.main()
