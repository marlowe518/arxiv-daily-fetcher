#!/usr/bin/env python3
"""
Main entry point for running the arXiv paper fetcher pipeline.

Usage:
    python scripts/run.py                    # Run normally
    python scripts/run.py --dry-run          # Run without modifying files
    python scripts/run.py --config path.yaml # Use custom config
    python scripts/run.py --verbose          # Enable verbose logging
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import create_pipeline, run_pipeline


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and summarize arXiv papers for configured topics"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Path to configuration file (default: config/topics.yaml)"
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
        help="Run without modifying state or output files"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run pipeline
    try:
        result = run_pipeline(
            config_path=args.config,
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            dry_run=args.dry_run
        )
        
        # Print summary
        print()
        print(result.summary())
        
        # Exit with error code if there were errors
        if result.errors:
            sys.exit(1)
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
