# Usage Guide - arXiv Daily Paper Fetcher

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Manual Execution](#manual-execution)
5. [Testing](#testing)
6. [GitHub Actions Setup](#github-actions-setup)
7. [Understanding the Output](#understanding-the-output)
8. [Adding New Topics](#adding-new-topics)
9. [Troubleshooting](#troubleshooting)

---

## Environment Setup

### Requirements

- Python 3.9 or higher
- pip package manager
- Git (for cloning and GitHub Actions)

### Supported Platforms

- Linux / macOS / Windows (WSL recommended)

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd arxiv-daily-fetcher
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `feedparser>=6.0.0` - Parse arXiv Atom feeds
- `pyyaml>=6.0` - YAML configuration parsing
- `requests>=2.28.0` - HTTP client for API calls

### 4. Verify Installation

```bash
python -c "import src; print('Installation successful')"
```

---

## Configuration

### Configuration File Location

Default: `config/topics.yaml`

### Configuration Format

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
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name for the topic |
| `description` | No | Optional longer description |
| `queries` | No* | List of search terms (OR combined) |
| `categories` | No* | arXiv category codes (OR combined) |

*At least one of `queries` or `categories` must be provided.

### Common arXiv Categories

| Category | Description |
|----------|-------------|
| `cs.LG` | Machine Learning |
| `cs.AI` | Artificial Intelligence |
| `cs.CL` | Computation and Language (NLP) |
| `cs.CR` | Cryptography and Security |
| `cs.DB` | Databases |
| `cs.IR` | Information Retrieval |
| `cs.DC` | Distributed Computing |

---

## Manual Execution

### Basic Usage

```bash
python scripts/run.py
```

This will:
1. Load configuration from `config/topics.yaml`
2. Fetch papers for all configured topics
3. Filter out duplicates
4. Generate summaries
5. Update `output/papers.md`
6. Save state to `data/seen_papers.json`

### Dry-Run Mode

Test without modifying files:

```bash
python scripts/run.py --dry-run
```

### Custom Configuration

```bash
python scripts/run.py --config /path/to/custom-config.yaml
```

### Custom Directories

```bash
python scripts/run.py --data-dir /path/to/data --output-dir /path/to/output
```

### Verbose Output

```bash
python scripts/run.py --verbose
```

### All Options

```bash
python scripts/run.py --help
```

Output:
```
usage: run.py [-h] [--config CONFIG] [--data-dir DATA_DIR]
              [--output-dir OUTPUT_DIR] [--dry-run] [--verbose] [--version]

Fetch and summarize arXiv papers for configured topics

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to configuration file (default: config/topics.yaml)
  --data-dir DATA_DIR, -d DATA_DIR
                        Directory for data files (default: data)
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Directory for output files (default: output)
  --dry-run, -n         Run without modifying state or output files
  --verbose, -v         Enable verbose logging
  --version             show program's version number and exit
```

### Rebuilding Output

If the Markdown file is corrupted or you want to change the format:

```bash
python scripts/rebuild_output.py
```

Preview without writing:

```bash
python scripts/rebuild_output.py --dry-run
```

---

## Testing

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Specific Test File

```bash
python -m pytest tests/test_fetcher.py -v
```

### Run with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Run Integration Test

Test with real arXiv API (limited to 1 result):

```bash
python -m pytest tests/test_fetcher.py::TestIntegrationRealFetch -v
```

---

## GitHub Actions Setup

### Enabling Automated Execution

1. **Push to GitHub**:
   ```bash
   git push origin main
   ```

2. **Verify Workflow File**:
   - File: `.github/workflows/daily_arxiv.yml`
   - Should be in the repository

3. **Enable Actions**:
   - Go to repository on GitHub
   - Click "Actions" tab
   - Enable GitHub Actions if prompted

4. **Manual Trigger** (optional):
   - Go to Actions → Daily arXiv Paper Fetch
   - Click "Run workflow"
   - Choose dry-run or normal mode

### Workflow Schedule

The workflow runs daily at **08:00 UTC** by default.

To change the schedule, edit `.github/workflows/daily_arxiv.yml`:

```yaml
on:
  schedule:
    - cron: '0 8 * * *'  # Change this line
```

Cron format: `minute hour day month weekday`

Examples:
- `0 8 * * *` - Daily at 08:00 UTC
- `0 */6 * * *` - Every 6 hours
- `0 8 * * 1` - Weekly on Monday at 08:00 UTC

### GitHub Actions Permissions

Ensure the workflow has permission to commit:

1. Go to Settings → Actions → General
2. Under "Workflow permissions", select "Read and write permissions"
3. Save changes

---

## Understanding the Output

### Output Files

| File | Description |
|------|-------------|
| `output/papers.md` | Markdown table with all papers |
| `data/seen_papers.json` | Deduplication database |

### Markdown Table Format

```markdown
# arXiv Papers

| Date | Topic | Title | Authors | Categories | arXiv ID | One-line Summary |
|------|-------|-------|---------|------------|----------|------------------|
| 2024-01-15 | GNN | [Paper Title](URL) | Author A, Author B | cs.LG | 2401.12345 | Summary... |
```

### Column Meanings

- **Date**: Publication date on arXiv
- **Topic**: Which configured topic matched this paper
- **Title**: Clickable link to arXiv abstract page
- **Authors**: First 3 authors + "et al." if more
- **Categories**: arXiv subject categories
- **arXiv ID**: Unique paper identifier
- **One-line Summary**: Generated from abstract

### Reading the Table

Newest papers are always at the **top**, immediately below the header row.

### Sample Entry

```markdown
| 2024-01-15 | Graph Neural Networks | [Attention-based Graph Neural Networks](https://arxiv.org/abs/2401.12345) | John Doe, Jane Smith | cs.LG, cs.AI | 2401.12345 | This paper proposes a novel attention mechanism for graph data that improves node classification accuracy by 15%... |
```

---

## Adding New Topics

### Step-by-Step

1. **Edit Configuration**:
   ```bash
   nano config/topics.yaml
   ```

2. **Add New Topic**:
   ```yaml
   topics:
     # ... existing topics ...
     
     - name: "Your New Topic"
       description: "Description of the topic"
       queries:
         - "search term 1"
         - "search term 2"
       categories:
         - "cs.LG"
         - "cs.AI"
   ```

3. **Test Configuration**:
   ```bash
   python scripts/run.py --dry-run
   ```

4. **Run for Real**:
   ```bash
   python scripts/run.py
   ```

### Topic Tips

- **Specific Queries**: More specific = fewer false positives
- **Category Filtering**: Combine with categories for precision
- **Multiple Queries**: Use variations (e.g., "GNN" and "graph neural networks")
- **Test First**: Use `--dry-run` to verify results before committing

### Example Topics

```yaml
# Computer Vision
topics:
  - name: "Computer Vision"
    queries:
      - "computer vision"
      - "image classification"
      - "object detection"
    categories:
      - "cs.CV"

# Natural Language Processing
topics:
  - name: "NLP"
    queries:
      - "natural language processing"
      - "transformer"
      - "large language model"
    categories:
      - "cs.CL"
      - "cs.LG"

# Reinforcement Learning
topics:
  - name: "Reinforcement Learning"
    queries:
      - "reinforcement learning"
      - "RL"
      - "policy gradient"
    categories:
      - "cs.LG"
      - "cs.AI"
```

---

## Troubleshooting

### Common Issues

#### "Config file not found"

**Error**: `FileNotFoundError: Config file not found: config/topics.yaml`

**Solution**: Ensure you're running from the project root:
```bash
cd /path/to/arxiv-daily-fetcher
python scripts/run.py
```

Or specify the full path:
```bash
python scripts/run.py --config /full/path/to/config/topics.yaml
```

#### "No papers found"

**Cause**: Topics too restrictive or no recent papers.

**Solutions**:
- Increase `lookback_days`
- Remove date filter (set to `null`)
- Broaden queries
- Add more categories

#### "Rate limit exceeded"

**Cause**: Too many requests to arXiv.

**Solution**: The system already has 3-second delays. If still hitting limits:
- Reduce `max_results_per_topic`
- Reduce number of topics
- Wait a few hours before retrying

#### "Permission denied" (GitHub Actions)

**Cause**: Workflow doesn't have write permissions.

**Solution**: Enable "Read and write permissions" in Settings → Actions → General.

#### Duplicate papers appearing

**Cause**: State file not being saved or loaded.

**Solutions**:
- Check that `data/seen_papers.json` exists and is writable
- Verify the pipeline completed without errors
- Check disk space

### Debug Mode

Enable verbose logging:

```bash
python scripts/run.py --verbose
```

### Reset State

To start fresh (WARNING: will re-add all papers):

```bash
rm data/seen_papers.json
rm output/papers.md
```

### Getting Help

1. Check logs: Look for error messages in output
2. Test with dry-run: `python scripts/run.py --dry-run`
3. Run tests: `python -m pytest tests/ -v`
4. Check GitHub Actions logs in repository

---

## Advanced Usage

### Custom Summarizer

Create a custom summarizer by subclassing `Summarizer`:

```python
from src.summarizer import Summarizer

class MySummarizer(Summarizer):
    def summarize(self, title: str, abstract: str) -> str:
        # Your summarization logic
        return f"Custom summary: {title}"
```

### Local Scheduling (cron)

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add line for daily 8am run
0 8 * * * cd /path/to/arxiv-daily-fetcher && /path/to/venv/bin/python scripts/run.py >> /var/log/arxiv-fetcher.log 2>&1
```

---

## Quick Reference Card

```bash
# Install
pip install -r requirements.txt

# Run
python scripts/run.py

# Dry run
python scripts/run.py --dry-run

# Test
python -m pytest tests/ -v

# Rebuild
python scripts/rebuild_output.py

# Help
python scripts/run.py --help
```
