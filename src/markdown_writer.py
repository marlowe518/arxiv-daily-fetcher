"""
Markdown Table Writer Module

Handles creating and updating Markdown tables with paper entries.
Newest entries are always inserted at the top (below the header).
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class MarkdownTableEntry:
    """Represents a single row in the papers table."""
    
    def __init__(
        self,
        date: str,
        topic: str,
        title: str,
        arxiv_id: str,
        authors: List[str],
        categories: List[str],
        summary: str,
        arxiv_url: str
    ):
        """
        Initialize a table entry.
        
        Args:
            date: Publication date (YYYY-MM-DD format)
            topic: Topic name
            title: Paper title
            arxiv_id: arXiv ID
            authors: List of authors
            categories: List of arXiv categories
            summary: One-line summary
            arxiv_url: URL to arXiv abstract page
        """
        self.date = date
        self.topic = topic
        self.title = title
        self.arxiv_id = arxiv_id
        self.authors = authors
        self.categories = categories
        self.summary = summary
        self.arxiv_url = arxiv_url
    
    def format_authors(self, max_authors: int = 3) -> str:
        """
        Format author list for display.
        
        Args:
            max_authors: Maximum number of authors to show
            
        Returns:
            Formatted author string
        """
        if not self.authors:
            return "Unknown"
        
        if len(self.authors) <= max_authors:
            return ", ".join(self.authors)
        else:
            return ", ".join(self.authors[:max_authors]) + f" et al. ({len(self.authors)} authors)"
    
    def format_categories(self, max_cats: int = 3) -> str:
        """
        Format category list for display.
        
        Args:
            max_cats: Maximum number of categories to show
            
        Returns:
            Formatted category string
        """
        if not self.categories:
            return ""
        
        cats = self.categories[:max_cats]
        return ", ".join(cats)
    
    def format_title_link(self) -> str:
        """
        Format title as a Markdown link.
        
        Returns:
            Markdown link format: [Title](URL)
        """
        # Escape pipe characters in title to avoid breaking table
        safe_title = self.title.replace('|', '\\|')
        return f"[{safe_title}]({self.arxiv_url})"
    
    def to_row(self) -> str:
        """
        Convert entry to a Markdown table row.
        
        Returns:
            Table row string with | separators
        """
        # Escape pipe characters in summary
        safe_summary = self.summary.replace('|', '\\|')
        # Escape newlines in summary
        safe_summary = safe_summary.replace('\n', ' ')
        
        return (
            f"| {self.date} | "
            f"{self.topic} | "
            f"{self.format_title_link()} | "
            f"{self.format_authors()} | "
            f"{self.format_categories()} | "
            f"{self.arxiv_id} | "
            f"{safe_summary} |"
        )
    
    @classmethod
    def from_paper(cls, paper, topic: str, summary: str) -> 'MarkdownTableEntry':
        """
        Create entry from an ArxivPaper object.
        
        Args:
            paper: ArxivPaper object
            topic: Topic name
            summary: Generated summary
            
        Returns:
            MarkdownTableEntry instance
        """
        date_str = paper.published.strftime('%Y-%m-%d') if paper.published else 'Unknown'
        
        return cls(
            date=date_str,
            topic=topic,
            title=paper.title,
            arxiv_id=paper.arxiv_id,
            authors=paper.authors,
            categories=paper.categories,
            summary=summary,
            arxiv_url=f"https://arxiv.org/abs/{paper.arxiv_id}"
        )


class MarkdownTableWriter:
    """
    Manages the creation and updating of Markdown tables.
    
    Ensures:
    - Newest entries appear at the top (below header)
    - Table format remains valid
    - Backups are created before modifications
    """
    
    HEADER = "| Date | Topic | Title | Authors | Categories | arXiv ID | One-line Summary |"
    SEPARATOR = "|------|-------|-------|---------|------------|----------|------------------|"
    
    def __init__(self, output_file: str, backup: bool = True):
        """
        Initialize the table writer.
        
        Args:
            output_file: Path to the Markdown output file
            backup: Whether to create backups before modifying
        """
        self.output_file = Path(output_file)
        self.backup = backup
    
    def _read_existing(self) -> Tuple[List[str], List[str]]:
        """
        Read existing file and split into header and data rows.
        
        Returns:
            Tuple of (header_lines, data_rows)
        """
        if not self.output_file.exists():
            return [], []
        
        content = self.output_file.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        
        header_lines = []
        data_rows = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip header and separator lines
            if i < 2 or line.startswith('|--') or line.startswith('| Date'):
                header_lines.append(line)
            elif line.startswith('|'):
                data_rows.append(line)
        
        return header_lines, data_rows
    
    def _create_backup(self) -> Optional[Path]:
        """
        Create a backup of the existing file.
        
        Returns:
            Path to backup file or None if no backup created
        """
        if not self.backup or not self.output_file.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.output_file.with_suffix(f'.backup.{timestamp}.md')
        
        backup_path.write_text(self.output_file.read_text(encoding='utf-8'), encoding='utf-8')
        return backup_path
    
    def _create_header(self) -> List[str]:
        """Create the table header lines."""
        return [
            "# arXiv Papers",
            "",
            "This file contains the latest arXiv papers organized by topic.",
            "Newest entries appear at the top.",
            "",
            self.HEADER,
            self.SEPARATOR
        ]
    
    def _ensure_header(self, lines: List[str]) -> List[str]:
        """
        Ensure the content has proper header lines.
        
        Args:
            lines: Existing lines
            
        Returns:
            Lines with proper header prepended if needed
        """
        if not lines:
            return self._create_header()
        
        # Check if first non-empty line is the table header
        for line in lines:
            if line.strip().startswith('| Date'):
                return lines
        
        # No header found, prepend it
        return self._create_header() + [''] + lines
    
    def insert_entries(self, entries: List[MarkdownTableEntry], dry_run: bool = False) -> str:
        """
        Insert new entries at the top of the table.
        
        Args:
            entries: List of new entries to insert (newest first)
            dry_run: If True, don't write to file, just return content
            
        Returns:
            The resulting Markdown content
        """
        if not entries:
            # Read and return existing content
            if self.output_file.exists():
                return self.output_file.read_text(encoding='utf-8')
            else:
                return '\n'.join(self._create_header())
        
        # Create backup if needed
        if not dry_run:
            self._create_backup()
        
        # Read existing content
        existing_header, existing_rows = self._read_existing()
        
        # Convert new entries to rows
        new_rows = [entry.to_row() for entry in entries]
        
        # Combine: header + new rows + existing rows
        all_lines = self._create_header()
        all_lines.extend(new_rows)
        all_lines.extend(existing_rows)
        
        # Generate content
        content = '\n'.join(all_lines) + '\n'
        
        # Write to file
        if not dry_run:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            self.output_file.write_text(content, encoding='utf-8')
        
        return content
    
    def rebuild_from_entries(
        self, 
        entries: List[MarkdownTableEntry], 
        dry_run: bool = False
    ) -> str:
        """
        Rebuild the entire table from a list of entries.
        
        Useful for recovery or reorganization.
        
        Args:
            entries: All entries to include (will be sorted by date descending)
            dry_run: If True, don't write to file
            
        Returns:
            The resulting Markdown content
        """
        # Sort entries by date descending (newest first)
        sorted_entries = sorted(
            entries, 
            key=lambda e: e.date, 
            reverse=True
        )
        
        # Create backup
        if not dry_run:
            self._create_backup()
        
        # Build content
        lines = self._create_header()
        for entry in sorted_entries:
            lines.append(entry.to_row())
        
        content = '\n'.join(lines) + '\n'
        
        # Write to file
        if not dry_run:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            self.output_file.write_text(content, encoding='utf-8')
        
        return content
    
    def parse_existing_entries(self) -> List[MarkdownTableEntry]:
        """
        Parse existing Markdown file and extract entries.
        
        Returns:
            List of MarkdownTableEntry objects
        """
        if not self.output_file.exists():
            return []
        
        content = self.output_file.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        
        entries = []
        for line in lines:
            line = line.strip()
            # Skip header, separator, and non-table lines
            if not line.startswith('|') or 'Date' in line or '---' in line:
                continue
            
            entry = self._parse_row(line)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_row(self, row: str) -> Optional[MarkdownTableEntry]:
        """
        Parse a table row into a MarkdownTableEntry.
        
        Args:
            row: Table row string
            
        Returns:
            MarkdownTableEntry or None if parsing fails
        """
        # Split by | but handle escaped pipes
        # Simple approach: split and strip
        parts = [p.strip() for p in row.split('|')]
        # Remove empty parts from leading/trailing | (first and last will be empty)
        parts = [p for p in parts if p]
        
        # Expected format: Date | Topic | Title | Authors | Categories | arXiv ID | Summary
        if len(parts) < 7:
            return None
        
        # Extract title and URL from markdown link format [Title](URL)
        title_with_link = parts[2]
        match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', title_with_link)
        if match:
            title = match.group(1).replace('\\|', '|')
            arxiv_url = match.group(2)
        else:
            title = title_with_link.replace('\\|', '|')
            arxiv_url = ""
        
        # arXiv ID
        arxiv_id = parts[5]
        
        # Parse authors (handle "et al." format)
        authors_str = parts[3]
        if "et al." in authors_str:
            # Just take what we have
            authors = [a.strip() for a in authors_str.split(',')]
        else:
            authors = [a.strip() for a in authors_str.split(',') if a.strip()]
        
        # Parse categories
        categories = [c.strip() for c in parts[4].split(',') if c.strip()]
        
        # Parse summary
        summary = parts[6].replace('\\|', '|')
        
        return MarkdownTableEntry(
            date=parts[0],
            topic=parts[1],
            title=title,
            arxiv_id=arxiv_id,
            authors=authors,
            categories=categories,
            summary=summary,
            arxiv_url=arxiv_url
        )


def create_writer(output_dir: str = "output", filename: str = "papers.md") -> MarkdownTableWriter:
    """
    Factory function to create a MarkdownTableWriter with default paths.
    
    Args:
        output_dir: Output directory
        filename: Output filename
        
    Returns:
        Configured MarkdownTableWriter
    """
    output_path = Path(output_dir) / filename
    return MarkdownTableWriter(str(output_path))
