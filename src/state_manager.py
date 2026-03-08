"""
State Manager Module

Manages the persistent storage of seen paper IDs to enable
deduplication across multiple runs of the pipeline.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


class StateManager:
    """
    Manages the state of seen papers to prevent duplicates.
    
    Stores paper metadata including:
    - arXiv ID (primary key)
    - Title
    - Authors
    - Publication date
    - First seen timestamp
    - Topic tags
    """
    
    def __init__(self, state_file: str):
        """
        Initialize the state manager.
        
        Args:
            state_file: Path to the JSON state file
        """
        self.state_file = Path(state_file)
        self._papers: Dict[str, dict] = {}
        self._load()
    
    def _load(self) -> None:
        """Load the state from the JSON file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both old format (list) and new format (dict)
                    if isinstance(data, list):
                        self._papers = {p['arxiv_id']: p for p in data}
                    elif isinstance(data, dict):
                        self._papers = data.get('papers', {})
                    else:
                        self._papers = {}
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load state file: {e}")
                self._papers = {}
        else:
            self._papers = {}
    
    def save(self) -> None:
        """Save the current state to the JSON file."""
        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'papers': self._papers
        }
        
        # Write to temp file first, then rename for atomicity
        temp_file = self.state_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.state_file)
        except IOError as e:
            print(f"Error saving state: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def has_seen(self, arxiv_id: str) -> bool:
        """
        Check if a paper has been seen before.
        
        Args:
            arxiv_id: The arXiv ID to check
            
        Returns:
            True if the paper has been seen, False otherwise
        """
        return arxiv_id in self._papers
    
    def add_paper(
        self,
        arxiv_id: str,
        title: str,
        authors: List[str],
        published: datetime,
        topic: str,
        categories: Optional[List[str]] = None
    ) -> None:
        """
        Add a paper to the seen set.
        
        Args:
            arxiv_id: The arXiv ID
            title: Paper title
            authors: List of authors
            published: Publication date
            topic: The topic this paper was found under
            categories: arXiv categories
        """
        self._papers[arxiv_id] = {
            'arxiv_id': arxiv_id,
            'title': title,
            'authors': authors,
            'published': published.isoformat() if published else None,
            'first_seen': datetime.now().isoformat(),
            'topic': topic,
            'categories': categories or []
        }
    
    def add_papers_batch(self, papers: List[dict]) -> None:
        """
        Add multiple papers at once.
        
        Args:
            papers: List of paper dicts with keys: arxiv_id, title, authors, 
                   published, topic, categories
        """
        for paper in papers:
            self.add_paper(
                arxiv_id=paper['arxiv_id'],
                title=paper['title'],
                authors=paper.get('authors', []),
                published=paper.get('published'),
                topic=paper.get('topic', 'unknown'),
                categories=paper.get('categories', [])
            )
    
    def get_seen_ids(self) -> Set[str]:
        """
        Get the set of all seen arXiv IDs.
        
        Returns:
            Set of arXiv IDs
        """
        return set(self._papers.keys())
    
    def get_paper(self, arxiv_id: str) -> Optional[dict]:
        """
        Get the stored metadata for a paper.
        
        Args:
            arxiv_id: The arXiv ID
            
        Returns:
            Paper dict or None if not found
        """
        return self._papers.get(arxiv_id)
    
    def get_all_papers(self) -> List[dict]:
        """
        Get all stored papers as a list.
        
        Returns:
            List of paper dicts
        """
        return list(self._papers.values())
    
    def remove_paper(self, arxiv_id: str) -> bool:
        """
        Remove a paper from the seen set.
        
        Args:
            arxiv_id: The arXiv ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if arxiv_id in self._papers:
            del self._papers[arxiv_id]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all stored papers (use with caution)."""
        self._papers.clear()
    
    def get_stats(self) -> dict:
        """
        Get statistics about the stored papers.
        
        Returns:
            Dict with statistics
        """
        topics = {}
        for paper in self._papers.values():
            topic = paper.get('topic', 'unknown')
            topics[topic] = topics.get(topic, 0) + 1
        
        return {
            'total_papers': len(self._papers),
            'papers_by_topic': topics,
            'last_updated': datetime.now().isoformat()
        }


class PaperFilter:
    """
    Filters papers based on various criteria.
    
    Works with StateManager to filter out duplicates.
    """
    
    def __init__(self, state_manager: StateManager):
        """
        Initialize the filter.
        
        Args:
            state_manager: StateManager instance for deduplication
        """
        self.state_manager = state_manager
    
    def filter_new_papers(
        self, 
        papers: List,
        topic_name: str
    ) -> List:
        """
        Filter papers to return only new (unseen) ones.
        
        Args:
            papers: List of ArxivPaper objects
            topic_name: Name of the topic being processed
            
        Returns:
            List of new ArxivPaper objects
        """
        new_papers = []
        for paper in papers:
            if not self.state_manager.has_seen(paper.arxiv_id):
                new_papers.append(paper)
        
        return new_papers
    
    def deduplicate_across_topics(self, papers_by_topic: Dict[str, List]) -> Dict[str, List]:
        """
        Deduplicate papers across multiple topics.
        
        If a paper appears in multiple topics, it will only be kept
        in the first topic encountered.
        
        Args:
            papers_by_topic: Dict mapping topic names to lists of papers
            
        Returns:
            Dict with deduplicated papers per topic
        """
        seen_ids = self.state_manager.get_seen_ids()
        result = {}
        
        for topic, papers in papers_by_topic.items():
            topic_papers = []
            for paper in papers:
                if paper.arxiv_id not in seen_ids:
                    topic_papers.append(paper)
                    seen_ids.add(paper.arxiv_id)
            result[topic] = topic_papers
        
        return result


def create_state_manager(data_dir: str = "data") -> StateManager:
    """
    Factory function to create a StateManager with default paths.
    
    Args:
        data_dir: Directory for data files
        
    Returns:
        Configured StateManager instance
    """
    state_file = os.path.join(data_dir, "seen_papers.json")
    return StateManager(state_file)
