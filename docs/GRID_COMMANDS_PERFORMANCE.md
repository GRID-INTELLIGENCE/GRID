# GRID Commands & Performance Guide

## Quick Start

### Verify GRID CLI Works
```powershell
python -m grid analyze --help
```

Expected output: Usage information for the `analyze` command.

### Run a Basic Analysis
```powershell
python -m grid analyze "Harry Potter attended Hogwarts where Dumbledore was headmaster."
```

Output shows: Entities found, relationships, and analysis results.

---

## Command Reference

### `grid analyze` - Main Analysis Command

**Basic usage:**
```powershell
python -m grid analyze TEXT [OPTIONS]
```

#### Core Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `TEXT` | string | required | The text to analyze |
| `--file PATH` | path | - | Read text from file instead of command line |
| `--output FORMAT` | choice | `table` | Output format: `json`, `table`, or `yaml` |
| `--use-rag` | flag | false | Enable RAG (Retrieval-Augmented Generation) context |
| `--openai-key TEXT` | string | env var | OpenAI API key (or use `OPENAI_API_KEY` environment variable) |
| `--confidence FLOAT` | float | 0.7 | Confidence threshold for entity detection |
| `--max-entities INTEGER` | int | 0 | Limit entities used for relationship analysis (0 = unlimited) |
| `--timings` | flag | false | Print stage timing breakdown to stderr |
| `--debug` | flag | false | Print debug info about environment settings |

#### Examples

**Analyze with default settings (table output):**
```powershell
python -m grid analyze "Your text here"
```

**JSON output for programmatic consumption:**
```powershell
python -m grid analyze "Your text here" --output json
```

**Analyze with RAG for enhanced context:**
```powershell
python -m grid analyze "Your text here" --use-rag --output json
```

**Load text from file:**
```powershell
python -m grid analyze --file path/to/input.txt --output yaml
```

**Show performance timing breakdown:**
```powershell
python -m grid analyze "Your text here" --timings
```

**Adjust confidence threshold:**
```powershell
python -m grid analyze "Your text here" --confidence 0.85
```

**Limit entities for faster relationship analysis:**
```powershell
python -m grid analyze "Your text here" --max-entities 10
```

---

## Performance Guide

### Understanding Timing Breakdown

The `--timings` flag shows three stages:

1. **init** - Initialization (model loading, setup)
2. **ner** - Named Entity Recognition (entity detection)
3. **relationships** - Relationship Analysis (discovering connections between entities)
4. **total** - Wall-clock time

### Performance Characteristics

| Input Size | Typical Time | Recommended Settings |
|------------|-------------|----------------------|
| Small (<500 chars) | 5-15ms | `--confidence 0.7` (default) |
| Medium (500-5000 chars) | 20-50ms | `--max-entities 20` for speed |
| Large (>5000 chars) | 50-200ms | `--max-entities 10`, consider `--use-rag` for context |

### Performance Tuning

**For Speed (minimize latency):**
```powershell
# Increase confidence threshold (fewer entities = faster relationships)
python -m grid analyze TEXT --confidence 0.9 --max-entities 5

# Disable RAG (adds network latency)
# Don't use --use-rag
```

**For Accuracy (maximize quality):**
```powershell
# Lower confidence threshold
python -m grid analyze TEXT --confidence 0.5 --max-entities 50

# Enable RAG for enhanced context
python -m grid analyze TEXT --use-rag
```

**For Balanced Performance:**
```powershell
python -m grid analyze TEXT --confidence 0.7 --max-entities 15 --timings
```

---

## Benchmarking

### Run Full Performance Suite

The workspace includes a comprehensive benchmarking tool that tests GRID analyze on multiple input sizes:

```powershell
# From root directory
python scripts/benchmark_grid.py
```

**What it measures:**
- Small input (< 200 words)
- Medium input (200-800 words)
- Large input (1000+ words)
- Performance with and without RAG
- Stage breakdown (init, NER, relationships, total)
- Statistical analysis (p50, p95, min, max, stdev)

**Output:**
- Console summary with percentile statistics
- JSON export for trend tracking: `benchmarks/grid_benchmark_*.json`

### Run Individual Benchmark Tasks

From VS Code, use the task runner or:

```powershell
# Quick benchmark (small input only)
python -m grid analyze "Your text" --output table --timings

# Medium input with RAG
python -m grid analyze "Longer text here..." --output json --use-rag --timings
```

### Interpreting Results

**Good performance:**
- Total < 50ms for medium input
- NER < 20% of total time
- Relationships < 30% of total time

**Optimize if:**
- Total > 200ms consistently
- Relationships > 50% of total (consider `--max-entities`)
- Init > 10% (check for cold starts)

---

## Troubleshooting

### Command Fails: "module not found"

**Cause:** PYTHONPATH not set correctly

**Fix:**
```powershell
cd e:\grid
python -m grid analyze --help
```

### Slow Performance

**Check these in order:**
1. Run with `--timings` to identify bottleneck
2. Try with `--max-entities 5` to test if relationships are slow
3. Ensure no competing processes
4. Run `python scripts/benchmark_grid.py` to get baseline

### Import Errors (e.g., "No module named circuits")

**Cause:** Circuits logging module shadowing stdlib

**Status:** ✅ Fixed (renamed to `circuits/logging_compat.py`)

Verify it's working:
```powershell
python -c "import logging; print(logging.getLogger('test'))"
```

---

## Advanced Usage

### Batch Processing

Create a file `batch.py`:
```python
import subprocess
import json
from pathlib import Path

texts = [
    "First text to analyze",
    "Second text to analyze",
    "Third text to analyze"
]

results = []
for i, text in enumerate(texts, 1):
    result = subprocess.run(
        ["python", "-m", "grid", "analyze", text, "--output", "json"],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    results.append(data)
    print(f"Processed {i}/{len(texts)}")

# Save results
with open("batch_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

Run:
```powershell
python batch.py
```

### Monitoring Performance Over Time

Use the benchmarking suite to track performance trends:

```powershell
# Run once daily to track
python scripts/benchmark_grid.py

# Check previous results
ls benchmarks/
```

Analysis tip: Load JSON files in your analytics tool to visualize trends.

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `OPENAI_API_KEY` | OpenAI authentication | `sk-...` |
| `PYTHONPATH` | Module search path | (auto-configured) |
| `GRID_DEBUG` | Enable debug logging | `1` |

### Set for Current Session

```powershell
$env:OPENAI_API_KEY = "your-key-here"
python -m grid analyze TEXT --use-rag
```

### Set Permanently (Windows)

```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-key-here", "User")
```

---

## Integration with VS Code

### Quick Commands via Tasks

Press `Ctrl+Shift+B` to run default build task, or select from the command palette:
- `█ PERF · Benchmark GRID (Full Suite)` - Run comprehensive performance test
- `█ PERF · Analyze Quick (Small Input)` - Quick baseline (5-10ms)
- `█ PERF · Analyze with RAG (Medium Input)` - Test with context enhancement

### Debug Configuration

Launch the Python debugger in VS Code with `F5` and select "Python: GRID Analyze" to step through code.

---

## Performance Baseline (Latest Run)

```
Input: "Harry Potter attended Hogwarts. Dumbledore was headmaster."
Output: 2 entities, 1 relationship
Timing: init=2.2ms ner=1.0ms relationships=0.0ms total=7.9ms
Status: ✅ Healthy
```

---

## Support & Documentation

- **Main CLI:** `grid/__main__.py`
- **Analyze Command:** `circuits/cli/main.py`
- **Tests:** `tests/test_cli.py`
- **Workspace Tasks:** `grid.code-workspace` (tasks section)
- **Benchmarks:** `scripts/benchmark_grid.py`

## Recent Fixes

- ✅ Fixed `circuits/logging.py` shadowing stdlib logging (renamed to `logging_compat.py`)
- ✅ Added comprehensive benchmarking suite
- ✅ Added VS Code performance monitoring tasks
- ✅ Documented performance tuning strategies
