#!/usr/bin/env python3
"""
Utility script to rebuild the Markdown output from stored state.

This is useful for:
- Recovering from Markdown corruption
- Changing the output format
- Reorganizing the table

Usage:
    python scripts/rebuild_output.py              # Rebuild from default state
    python scripts/rebuild_output.py --dry-run    # Preview without writing
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state_manager import create_state_manager
from src.markdown_writer import MarkdownTableEntry, create_writer


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rebuild Markdown output from stored state"
    )
    
    parser.add_argument(
        "--data-dir", "-d",
        type=str,
        default="data",
        help="Directory for data files (default: data)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="output",
        help="Directory for output files (default: output)"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview output without writing files"
    )
    
    args = parser.parse_args()
    
    # Load state
    try:
        state_manager = create_state_manager(args.data_dir)
        papers = state_manager.get_all_papers()
        
        if not papers:
            print("No papers found in state. Nothing to rebuild.")
            sys.exit(0)
        
        print(f"Found {len(papers)} papers in state")
        
        # Convert to entries
        entries = []
        for paper in papers:
            entry = MarkdownTableEntry(
                date=paper.get('published', 'Unknown')[:10] if paper.get('published') else 'Unknown',
                topic=paper.get('topic', 'Unknown'),
                title=paper.get('title', 'Unknown'),
                arxiv_id=paper.get('arxiv_id', 'Unknown'),
                authors=paper.get('authors', []),
                categories=paper.get('categories', []),
                summary="",  # Summaries not stored in state
                arxiv_url=f"https://arxiv.org/abs/{paper.get('arxiv_id', '')}"
            )
            entries.append(entry)
        
        # Create writer and rebuild
        writer = create_writer(args.output_dir)
        results = writer.rebuild_from_entries(entries, dry_run=args.dry_run)
        
        if args.dry_run:
            print(f"\n--- Preview (showing first topic) ---")
            for topic, content in list(results.items())[:1]:
                lines = content.split('\n')
                for line in lines[:30]:
                    print(line)
                if len(lines) > 30:
                    print(f"\n... ({len(lines) - 30} more lines)")
        else:
            print(f"Successfully rebuilt {len(results)} topic files with {len(entries)} total entries")
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"Error: State file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
