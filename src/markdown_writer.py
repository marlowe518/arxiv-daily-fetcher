"""
Markdown Table Writer Module

Handles creating and updating Markdown tables with paper entries.
Newest entries are always inserted at the top (below the header).
Each topic gets its own markdown file.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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
        Simplified: only Date, Title, Summary
        
        Returns:
            Table row string with | separators
        """
        # Escape pipe characters in summary
        safe_summary = self.summary.replace('|', '\\|')
        # Escape newlines in summary
        safe_summary = safe_summary.replace('\n', ' ')
        
        return (
            f"| {self.date} | "
            f"{self.format_title_link()} | "
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
    Each topic gets its own file.
    
    Ensures:
    - Newest entries appear at the top (below header)
    - Table format remains valid
    - Backups are created before modifications
    """
    
    # Simplified header - only 3 columns
    HEADER = "| Date | Title | One-line Summary |"
    SEPARATOR = "|------|-------|------------------|"
    
    def __init__(self, output_dir: str, backup: bool = True):
        """
        Initialize the table writer.
        
        Args:
            output_dir: Directory for output files
            backup: Whether to create backups before modifying
        """
        self.output_dir = Path(output_dir)
        self.backup = backup
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_topic_filename(self, topic: str) -> Path:
        """
        Generate a safe filename for a topic.
        
        Args:
            topic: Topic name
            
        Returns:
            Path object for the topic file
        """
        # Convert topic name to safe filename
        safe_name = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
        safe_name = safe_name.lower()
        return self.output_dir / f"{safe_name}.md"
    
    def _read_existing(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """
        Read existing file and split into header and data rows.
        
        Returns:
            Tuple of (header_lines, data_rows)
        """
        if not file_path.exists():
            return [], []
        
        content = file_path.read_text(encoding='utf-8')
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
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Create a backup of the existing file.
        
        Returns:
            Path to backup file or None if no backup created
        """
        if not self.backup or not file_path.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.with_suffix(f'.backup.{timestamp}.md')
        
        backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
        return backup_path
    
    def _create_header(self, topic: str) -> List[str]:
        """Create the table header lines for a topic file."""
        return [
            f"# {topic} Papers",
            "",
            f"Latest papers on {topic} from arXiv.",
            "Newest entries appear at the top.",
            "",
            self.HEADER,
            self.SEPARATOR
        ]
    
    def insert_entries(self, entries: List[MarkdownTableEntry], dry_run: bool = False) -> Dict[str, str]:
        """
        Insert new entries into topic-specific files.
        
        Args:
            entries: List of new entries to insert
            dry_run: If True, don't write to file, just return content
            
        Returns:
            Dict mapping topic names to file content
        """
        results = {}
        
        # Group entries by topic
        entries_by_topic: Dict[str, List[MarkdownTableEntry]] = {}
        for entry in entries:
            if entry.topic not in entries_by_topic:
                entries_by_topic[entry.topic] = []
            entries_by_topic[entry.topic].append(entry)
        
        # Process each topic
        for topic, topic_entries in entries_by_topic.items():
            content = self._update_topic_file(topic, topic_entries, dry_run)
            results[topic] = content
        
        return results
    
    def _update_topic_file(
        self, 
        topic: str, 
        entries: List[MarkdownTableEntry], 
        dry_run: bool = False
    ) -> str:
        """
        Update a single topic file.
        
        Args:
            topic: Topic name
            entries: New entries for this topic
            dry_run: If True, don't write to file
            
        Returns:
            The resulting Markdown content
        """
        file_path = self._get_topic_filename(topic)
        
        # Create backup if needed
        if not dry_run:
            self._create_backup(file_path)
        
        # Read existing content
        existing_header, existing_rows = self._read_existing(file_path)
        
        # Convert new entries to rows
        new_rows = [entry.to_row() for entry in entries]
        
        # Combine: header + new rows + existing rows
        all_lines = self._create_header(topic)
        all_lines.extend(new_rows)
        all_lines.extend(existing_rows)
        
        # Generate content
        content = '\n'.join(all_lines) + '\n'
        
        # Write to file
        if not dry_run:
            file_path.write_text(content, encoding='utf-8')
        
        return content
    
    def rebuild_from_entries(
        self, 
        entries: List[MarkdownTableEntry], 
        dry_run: bool = False
    ) -> Dict[str, str]:
        """
        Rebuild all topic files from a list of entries.
        
        Useful for recovery or reorganization.
        
        Args:
            entries: All entries to include (will be sorted by date descending)
            dry_run: If True, don't write to file
            
        Returns:
            Dict mapping topic names to file content
        """
        # Group by topic
        entries_by_topic: Dict[str, List[MarkdownTableEntry]] = {}
        for entry in entries:
            if entry.topic not in entries_by_topic:
                entries_by_topic[entry.topic] = []
            entries_by_topic[entry.topic].append(entry)
        
        results = {}
        for topic, topic_entries in entries_by_topic.items():
            # Sort entries by date descending (newest first)
            sorted_entries = sorted(
                topic_entries, 
                key=lambda e: e.date, 
                reverse=True
            )
            
            file_path = self._get_topic_filename(topic)
            
            # Create backup
            if not dry_run:
                self._create_backup(file_path)
            
            # Build content
            lines = self._create_header(topic)
            for entry in sorted_entries:
                lines.append(entry.to_row())
            
            content = '\n'.join(lines) + '\n'
            
            # Write to file
            if not dry_run:
                file_path.write_text(content, encoding='utf-8')
            
            results[topic] = content
        
        return results


def create_writer(output_dir: str = "output") -> MarkdownTableWriter:
    """
    Factory function to create a MarkdownTableWriter with default paths.
    
    Args:
        output_dir: Output directory
        
    Returns:
        Configured MarkdownTableWriter instance
    """
    return MarkdownTableWriter(output_dir)
