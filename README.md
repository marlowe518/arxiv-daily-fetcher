# arXiv Daily Paper Fetcher

> Automated daily retrieval and summarization of arXiv papers for configured research topics.

## Overview

This project automatically fetches the latest arXiv papers for user-defined research topics, generates one-sentence summaries, and maintains a Markdown table with the newest entries at the top.

## Features

- **Daily Automation**: GitHub Actions workflow runs automatically every day
- **Configurable Topics**: Define topics via YAML configuration
- **Smart Deduplication**: Tracks seen papers to avoid duplicates
- **One-Line Summaries**: Automatic summary generation from abstracts
- **Clean Markdown Output**: Papers organized in a sortable table format
- **Dry-Run Mode**: Test changes safely before committing

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline (dry-run mode)
python scripts/run.py --dry-run

# Run the pipeline (full execution)
python scripts/run.py

# Run tests
python -m pytest tests/ -v
```

## Project Structure

```
arxiv-daily-fetcher/
├── config/topics.yaml          # Topic configuration
├── data/seen_papers.json       # Deduplication database
├── output/papers.md            # Generated Markdown output
├── src/                        # Source code modules
│   ├── config.py               # Configuration loading
│   ├── fetcher.py              # arXiv API client
│   ├── summarizer.py           # Summary generation
│   ├── markdown_writer.py      # Markdown table management
│   ├── state_manager.py        # Seen papers tracking
│   └── pipeline.py             # Main orchestrator
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
└── .github/workflows/          # GitHub Actions automation
```

## Documentation

- [Usage Guide](docs/USAGE.md) - Detailed usage instructions
- [Development Log](docs/DEV_LOG.md) - Development progress
- [Final Report](docs/FINAL_REPORT.md) - Architecture and design decisions

## License

MIT License
