"""
Pipeline Orchestrator Module

Coordinates the entire paper fetching, processing, and output pipeline.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import Config, load_config, get_default_config_path
from src.fetcher import ArxivFetcher, ArxivPaper, fetch_for_topic
from src.state_manager import StateManager, PaperFilter, create_state_manager
from src.summarizer import Summarizer, HybridSummarizer, batch_summarize_papers
from src.markdown_writer import MarkdownTableEntry, MarkdownTableWriter, create_writer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PipelineResult:
    """Result of a pipeline run."""
    
    def __init__(self):
        self.papers_by_topic: Dict[str, List[ArxivPaper]] = {}
        self.new_papers_count = 0
        self.duplicates_filtered = 0
        self.errors: List[str] = []
    
    def add_papers(self, topic: str, papers: List[ArxivPaper]) -> None:
        """Add papers for a topic."""
        self.papers_by_topic[topic] = papers
        self.new_papers_count += len(papers)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
    
    def summary(self) -> str:
        """Generate a text summary of the run."""
        lines = [
            "Pipeline Run Summary",
            "=" * 40,
            f"Topics processed: {len(self.papers_by_topic)}",
            f"New papers added: {self.new_papers_count}",
            f"Duplicates filtered: {self.duplicates_filtered}",
        ]
        
        for topic, papers in self.papers_by_topic.items():
            lines.append(f"  - {topic}: {len(papers)} papers")
        
        if self.errors:
            lines.append(f"\nErrors: {len(self.errors)}")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        return '\n'.join(lines)


class ArxivPipeline:
    """
    Main pipeline for fetching and processing arXiv papers.
    """
    
    def __init__(
        self,
        config: Config,
        state_manager: StateManager,
        markdown_writer: MarkdownTableWriter,
        summarizer: Optional[Summarizer] = None,
        fetcher: Optional[ArxivFetcher] = None
    ):
        """
        Initialize the pipeline.
        
        Args:
            config: Configuration object
            state_manager: State manager for deduplication
            markdown_writer: Markdown writer for output
            summarizer: Summarizer instance (uses default if None)
            fetcher: Fetcher instance (uses default if None)
        """
        self.config = config
        self.state_manager = state_manager
        self.markdown_writer = markdown_writer
        self.summarizer = summarizer or HybridSummarizer()
        self.fetcher = fetcher or ArxivFetcher()
        self.filter = PaperFilter(state_manager)
    
    def run(self, dry_run: bool = False) -> PipelineResult:
        """
        Run the complete pipeline.
        
        Args:
            dry_run: If True, don't modify state or output files
            
        Returns:
            PipelineResult with run statistics
        """
        result = PipelineResult()
        all_entries: List[MarkdownTableEntry] = []
        
        logger.info("Starting arXiv paper fetch pipeline")
        logger.info(f"Topics: {[t.name for t in self.config.topics]}")
        logger.info(f"Dry run: {dry_run}")
        
        # Process each topic
        for topic in self.config.topics:
            try:
                papers = self._process_topic(topic, result)
                
                if papers:
                    # Generate summaries
                    logger.info(f"Generating summaries for {len(papers)} papers in {topic.name}")
                    summaries = batch_summarize_papers(papers, self.summarizer)
                    
                    # Create table entries
                    for paper, summary in zip(papers, summaries):
                        entry = MarkdownTableEntry.from_paper(paper, topic.name, summary)
                        all_entries.append(entry)
                        
                        # Add to state if not dry run
                        if not dry_run:
                            self.state_manager.add_paper(
                                arxiv_id=paper.arxiv_id,
                                title=paper.title,
                                authors=paper.authors,
                                published=paper.published,
                                topic=topic.name,
                                categories=paper.categories
                            )
                
            except Exception as e:
                error_msg = f"Error processing topic '{topic.name}': {e}"
                logger.error(error_msg)
                result.add_error(error_msg)
        
        # Update Markdown output (always call to ensure headers exist)
        logger.info(f"Updating Markdown with {len(all_entries)} entries")
        try:
            self.markdown_writer.insert_entries(all_entries, dry_run=dry_run)
        except Exception as e:
            error_msg = f"Error updating Markdown: {e}"
            logger.error(error_msg)
            result.add_error(error_msg)
        
        # Save state if not dry run
        if not dry_run:
            try:
                self.state_manager.save()
                logger.info("State saved successfully")
            except Exception as e:
                error_msg = f"Error saving state: {e}"
                logger.error(error_msg)
                result.add_error(error_msg)
        
        logger.info("Pipeline completed")
        return result
    
    def _process_topic(
        self, 
        topic, 
        result: PipelineResult
    ) -> List[ArxivPaper]:
        """
        Process a single topic.
        
        Args:
            topic: TopicConfig object
            result: PipelineResult to update
            
        Returns:
            List of new (non-duplicate) papers
        """
        logger.info(f"Processing topic: {topic.name}")
        
        # Fetch papers
        papers = fetch_for_topic(
            fetcher=self.fetcher,
            topic_name=topic.name,
            queries=topic.queries,
            categories=topic.categories,
            max_results=self.config.max_results_per_topic,
            lookback_days=self.config.lookback_days
        )
        
        if not papers:
            logger.info(f"  No papers found for {topic.name}")
            return []
        
        logger.info(f"  Found {len(papers)} papers")
        
        # Filter duplicates
        new_papers = self.filter.filter_new_papers(papers, topic.name)
        duplicates = len(papers) - len(new_papers)
        
        logger.info(f"  New papers: {len(new_papers)}, Duplicates: {duplicates}")
        
        result.duplicates_filtered += duplicates
        result.add_papers(topic.name, new_papers)
        
        return new_papers


def create_pipeline(
    config_path: Optional[str] = None,
    data_dir: str = "data",
    output_dir: str = "output"
) -> ArxivPipeline:
    """
    Factory function to create a configured pipeline.
    
    Args:
        config_path: Path to config file (uses default if None)
        data_dir: Directory for data files
        output_dir: Directory for output files
        
    Returns:
        Configured ArxivPipeline instance
    """
    # Load config
    config_path = config_path or get_default_config_path()
    config = load_config(config_path)
    
    # Create state manager
    state_manager = create_state_manager(data_dir)
    
    # Create markdown writer
    markdown_writer = create_writer(output_dir, "papers.md")
    
    return ArxivPipeline(
        config=config,
        state_manager=state_manager,
        markdown_writer=markdown_writer
    )


def run_pipeline(
    config_path: Optional[str] = None,
    data_dir: str = "data",
    output_dir: str = "output",
    dry_run: bool = False
) -> PipelineResult:
    """
    Convenience function to create and run the pipeline.
    
    Args:
        config_path: Path to config file
        data_dir: Directory for data files
        output_dir: Directory for output files
        dry_run: If True, don't modify state or output
        
    Returns:
        PipelineResult
    """
    pipeline = create_pipeline(config_path, data_dir, output_dir)
    return pipeline.run(dry_run=dry_run)
