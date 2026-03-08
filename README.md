# arXiv Daily Paper Fetcher

> Automated daily retrieval and summarization of arXiv papers for configured research topics.

[![Tests](https://img.shields.io/badge/tests-83%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## Overview

This project automatically fetches the latest arXiv papers for user-defined research topics, generates one-sentence summaries, and maintains a Markdown table with the newest entries at the top.

### Key Features

- **📚 Daily Automation**: GitHub Actions workflow runs automatically every day
- **🔧 Configurable Topics**: Define topics via YAML configuration
- **🔍 Smart Deduplication**: Tracks seen papers to avoid duplicates
- **📝 One-Line Summaries**: Automatic summary generation from abstracts
- **📊 Clean Markdown Output**: Papers organized in a sortable table format
- **🧪 Dry-Run Mode**: Test changes safely before committing
- **🔄 Rebuild Support**: Recover or reformat output from stored state

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline (dry-run mode for testing)
python scripts/run.py --dry-run

# Run the pipeline (full execution)
python scripts/run.py

# Run tests
python -m pytest tests/ -v
```

## Example Output

The system generates a Markdown table like this:

| Date | Topic | Title | Authors | Categories | arXiv ID | One-line Summary |
|------|-------|-------|---------|------------|----------|------------------|
| 2024-01-15 | Graph Neural Networks | [Attention-based GNNs](https://arxiv.org/abs/2401.12345) | John Doe, Jane Smith | cs.LG, cs.AI | 2401.12345 | This paper proposes a novel attention mechanism for graph data... |
| 2024-01-14 | Differential Privacy | [DP-SGD Improvements](https://arxiv.org/abs/2401.12344) | Alice Johnson et al. (5 authors) | cs.CR | 2401.12344 | New analysis of privacy-utility tradeoffs in differential privacy... |

## Project Structure

```
arxiv-daily-fetcher/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore patterns
│
├── config/
│   └── topics.yaml            # Topic configuration (edit this!)
│
├── data/
│   └── seen_papers.json       # Deduplication database (auto-generated)
│
├── output/
│   └── papers.md              # Generated Markdown output (auto-generated)
│
├── src/                        # Source code modules
│   ├── __init__.py
│   ├── config.py              # Configuration loading/validation
│   ├── fetcher.py             # arXiv API client
│   ├── summarizer.py          # Summary generation
│   ├── markdown_writer.py     # Markdown table management
│   ├── state_manager.py       # Seen papers tracking
│   └── pipeline.py            # Main orchestrator
│
├── scripts/                    # Utility scripts
│   ├── run.py                 # Main entry point
│   └── rebuild_output.py      # Rebuild from state
│
├── tests/                      # Test suite (84 tests)
│   ├── test_config.py
│   ├── test_fetcher.py
│   ├── test_markdown_writer.py
│   ├── test_pipeline.py
│   ├── test_state_manager.py
│   └── test_summarizer.py
│
├── .github/
│   └── workflows/
│       └── daily_arxiv.yml    # GitHub Actions automation
│
└── docs/                       # Documentation
    ├── DEV_LOG.md             # Development log
    ├── FINAL_REPORT.md        # Architecture & design report
    └── USAGE.md               # Detailed usage guide
```

## Configuration

Edit `config/topics.yaml` to customize your topics:

```yaml
# Maximum papers to fetch per topic per run
max_results_per_topic: 20

# Only fetch papers from last N days
lookback_days: 7

# Topic definitions
topics:
  - name: "Graph Neural Networks"
    description: "Papers on GNNs and graph learning"
    queries:
      - "graph neural networks"
      - "GNN"
    categories:
      - "cs.LG"
      - "cs.AI"

  - name: "Differential Privacy"
    queries:
      - "differential privacy"
    categories:
      - "cs.CR"
      - "cs.LG"
```

See [docs/USAGE.md](docs/USAGE.md) for detailed configuration options.

## Documentation

- **[Usage Guide](docs/USAGE.md)** - Detailed setup and usage instructions
- **[Final Report](docs/FINAL_REPORT.md)** - Architecture overview and design decisions
- **[Development Log](docs/DEV_LOG.md)** - Development progress and decisions

## How It Works

1. **Configuration Loading**: Reads topics from `config/topics.yaml`
2. **Paper Fetching**: Queries arXiv API for each topic with rate limiting
3. **Deduplication**: Filters out papers already in `data/seen_papers.json`
4. **Summarization**: Generates one-sentence summaries using heuristics
5. **Markdown Update**: Inserts new entries at the top of `output/papers.md`
6. **State Saving**: Updates `data/seen_papers.json` with new paper IDs

## Automation

The project includes a GitHub Actions workflow (`.github/workflows/daily_arxiv.yml`) that:

- Runs daily at 08:00 UTC
- Can be triggered manually with dry-run option
- Commits changes back to the repository

To enable:
1. Push to GitHub
2. Go to Actions tab and enable workflows
3. Ensure "Read and write permissions" is enabled in Settings → Actions → General

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific module
python -m pytest tests/test_fetcher.py -v
```

**Test Coverage**: 83 tests covering all modules (~95% coverage)

## Requirements

- Python 3.9+
- feedparser >= 6.0.0
- pyyaml >= 6.0
- requests >= 2.28.0

## Customization

### Adding a New Topic

1. Edit `config/topics.yaml`
2. Add a new topic entry with queries and/or categories
3. Run with `--dry-run` to test
4. Run normally to fetch papers

### Custom Summarizer

The default summarizer extracts the first sentence of the abstract. To use a custom summarizer (e.g., LLM-based), subclass `Summarizer` and pass it to the pipeline.

### Local Scheduling

Instead of GitHub Actions, you can use cron:

```bash
# Daily at 8am
0 8 * * * cd /path/to/arxiv-daily-fetcher && python scripts/run.py
```

## Limitations

- arXiv API rate limiting (3-second delays between requests)
- No full-text search (titles and abstracts only)
- Heuristic summaries may not capture nuance of complex papers
- Single output file (all topics in one table)

See [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md) for full limitations and future improvements.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- arXiv API for providing open access to research papers
- feedparser library for Atom feed parsing
