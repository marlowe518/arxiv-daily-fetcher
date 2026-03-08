"""
Tests for the Markdown writer module.
"""

import tempfile
import unittest
from pathlib import Path

from src.markdown_writer import MarkdownTableEntry, MarkdownTableWriter, create_writer


class TestMarkdownTableEntry(unittest.TestCase):
    """Test the MarkdownTableEntry class."""
    
    def test_format_authors_single(self):
        """Test formatting single author."""
        entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="Test",
            title="Title",
            arxiv_id="2401.12345",
            authors=["John Doe"],
            categories=["cs.LG"],
            summary="Summary",
            arxiv_url="https://arxiv.org/abs/2401.12345"
        )
        
        self.assertEqual(entry.format_authors(), "John Doe")
    
    def test_format_authors_multiple(self):
        """Test formatting multiple authors."""
        entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="Test",
            title="Title",
            arxiv_id="2401.12345",
            authors=["John Doe", "Jane Smith", "Bob Johnson"],
            categories=["cs.LG"],
            summary="Summary",
            arxiv_url="https://arxiv.org/abs/2401.12345"
        )
        
        # Should show all 3 since max is 3
        self.assertEqual(entry.format_authors(), "John Doe, Jane Smith, Bob Johnson")
    
    def test_format_authors_many(self):
        """Test formatting many authors with et al."""
        entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="Test",
            title="Title",
            arxiv_id="2401.12345",
            authors=["A", "B", "C", "D", "E"],
            categories=["cs.LG"],
            summary="Summary",
            arxiv_url="https://arxiv.org/abs/2401.12345"
        )
        
        result = entry.format_authors(max_authors=3)
        self.assertIn("et al.", result)
        self.assertIn("(5 authors)", result)
    
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
        # The escaped pipe should be in the title part, not as table separator
        self.assertIn("[Paper \\| A Study]", result)
    
    def test_to_row(self):
        """Test converting entry to table row."""
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
        
        self.assertIn("2024-01-15", row)
        self.assertIn("GNN", row)
        self.assertIn("[Graph Neural Networks Survey]", row)
        self.assertIn("2401.12345", row)
        self.assertIn("A. Author, B. Writer", row)
        self.assertIn("cs.LG, cs.AI", row)
        self.assertIn("A comprehensive survey of GNNs.", row)


class TestMarkdownTableWriter(unittest.TestCase):
    """Test the MarkdownTableWriter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = Path(self.temp_dir) / "papers.md"
        self.writer = MarkdownTableWriter(str(self.output_file), backup=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_new_file(self):
        """Test creating a new Markdown file."""
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
        
        self.writer.insert_entries(entries)
        
        self.assertTrue(self.output_file.exists())
        content = self.output_file.read_text()
        
        # Should have header
        self.assertIn("| Date | Topic | Title |", content)
        self.assertIn("|------|-------|-------|", content)
        
        # Should have the entry
        self.assertIn("2401.11111", content)
        self.assertIn("Paper 1", content)
    
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
            topic="DP",
            title="New Paper",
            arxiv_id="2401.00002",
            authors=["Author B"],
            categories=["cs.CR"],
            summary="New summary",
            arxiv_url="https://arxiv.org/abs/2401.00002"
        )
        self.writer.insert_entries([new_entry])
        
        content = self.output_file.read_text()
        lines = content.split('\n')
        
        # Find the data rows (skip header)
        data_rows = [l for l in lines if l.startswith('|') and 'Date' not in l and '---' not in l]
        
        # New paper should come before old paper
        self.assertIn("2401.00002", data_rows[0])
        self.assertIn("2401.00001", data_rows[1])
    
    def test_insert_multiple_entries_at_top(self):
        """Test inserting multiple entries - they should appear in order."""
        entries = [
            MarkdownTableEntry(
                date="2024-01-15",
                topic="GNN",
                title="Newest Paper",
                arxiv_id="2401.00003",
                authors=["Author C"],
                categories=["cs.LG"],
                summary="Summary 3",
                arxiv_url="https://arxiv.org/abs/2401.00003"
            ),
            MarkdownTableEntry(
                date="2024-01-14",
                topic="DP",
                title="Middle Paper",
                arxiv_id="2401.00002",
                authors=["Author B"],
                categories=["cs.CR"],
                summary="Summary 2",
                arxiv_url="https://arxiv.org/abs/2401.00002"
            ),
            MarkdownTableEntry(
                date="2024-01-13",
                topic="CF",
                title="Oldest Paper",
                arxiv_id="2401.00001",
                authors=["Author A"],
                categories=["cs.IR"],
                summary="Summary 1",
                arxiv_url="https://arxiv.org/abs/2401.00001"
            ),
        ]
        
        self.writer.insert_entries(entries)
        
        content = self.output_file.read_text()
        lines = content.split('\n')
        
        # Find the data rows
        data_rows = [l for l in lines if l.startswith('|') and 'Date' not in l and '---' not in l]
        
        # Order should be preserved (newest first)
        self.assertIn("2401.00003", data_rows[0])
        self.assertIn("2401.00002", data_rows[1])
        self.assertIn("2401.00001", data_rows[2])
    
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
        
        initial_content = self.output_file.read_text()
        
        # Dry run with new entry
        new_entry = MarkdownTableEntry(
            date="2024-01-15",
            topic="DP",
            title="New",
            arxiv_id="2401.00002",
            authors=["Author"],
            categories=["cs.CR"],
            summary="New summary",
            arxiv_url="https://arxiv.org/abs/2401.00002"
        )
        
        self.writer.insert_entries([new_entry], dry_run=True)
        
        # Content should be unchanged
        final_content = self.output_file.read_text()
        self.assertEqual(initial_content, final_content)
    
    def test_rebuild_from_entries(self):
        """Test rebuilding table from scratch."""
        entries = [
            MarkdownTableEntry(
                date="2024-01-10",
                topic="Old",
                title="Old Paper",
                arxiv_id="2401.00001",
                authors=["A"],
                categories=["cs.LG"],
                summary="Old",
                arxiv_url="https://arxiv.org/abs/2401.00001"
            ),
            MarkdownTableEntry(
                date="2024-01-15",
                topic="New",
                title="New Paper",
                arxiv_id="2401.00002",
                authors=["B"],
                categories=["cs.CR"],
                summary="New",
                arxiv_url="https://arxiv.org/abs/2401.00002"
            ),
        ]
        
        self.writer.rebuild_from_entries(entries)
        
        content = self.output_file.read_text()
        lines = content.split('\n')
        data_rows = [l for l in lines if l.startswith('|') and 'Date' not in l and '---' not in l]
        
        # Should be sorted by date descending (newest first)
        self.assertIn("2401.00002", data_rows[0])
        self.assertIn("2401.00001", data_rows[1])
    
    def test_parse_existing_entries(self):
        """Test parsing existing Markdown file."""
        # Create a file
        content = """# arXiv Papers

| Date | Topic | Title | Authors | Categories | arXiv ID | One-line Summary |
|------|-------|-------|---------|------------|----------|------------------|
| 2024-01-15 | GNN | [Test Paper](https://arxiv.org/abs/2401.12345) | Author A, Author B | cs.LG, cs.AI | 2401.12345 | A test summary. |
"""
        self.output_file.write_text(content)
        
        entries = self.writer.parse_existing_entries()
        
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].date, "2024-01-15")
        self.assertEqual(entries[0].topic, "GNN")
        self.assertEqual(entries[0].title, "Test Paper")
        self.assertEqual(entries[0].arxiv_id, "2401.12345")
        self.assertEqual(entries[0].summary, "A test summary.")
    
    def test_empty_entries(self):
        """Test handling of empty entries list."""
        # First create a file with some content
        self.writer.insert_entries([
            MarkdownTableEntry(
                date="2024-01-10",
                topic="Test",
                title="Test Paper",
                arxiv_id="2401.00001",
                authors=["Author"],
                categories=["cs.LG"],
                summary="Summary",
                arxiv_url="https://arxiv.org/abs/2401.00001"
            )
        ])
        
        # Now insert empty entries - should return existing content without modification
        content = self.writer.insert_entries([])
        
        self.assertIn("| Date | Topic | Title |", content)
        self.assertIn("Test Paper", content)  # Should preserve existing


class TestCreateWriter(unittest.TestCase):
    """Test the factory function."""
    
    def test_create_with_defaults(self):
        """Test creating writer with default paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = create_writer(tmpdir, "test.md")
            
            self.assertIsInstance(writer, MarkdownTableWriter)
            self.assertEqual(writer.output_file, Path(tmpdir) / "test.md")


if __name__ == '__main__':
    unittest.main()
