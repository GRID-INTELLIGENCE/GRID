# GRID Commands Quick Reference

## One-Liners

```powershell
# Basic analysis
python -m grid analyze "Your text here"

# JSON output
python -m grid analyze "Your text here" --output json

# Show timing
python -m grid analyze "Your text here" --timings

# From file
python -m grid analyze --file input.txt --output yaml

# With RAG
python -m grid analyze "Your text here" --use-rag

# Full benchmark suite
python scripts/benchmark_grid.py

# Fast analysis (high confidence)
python -m grid analyze "Your text" --confidence 0.9 --max-entities 5

# Accurate analysis (low confidence)
python -m grid analyze "Your text" --confidence 0.5 --max-entities 50

# List skills
python -m grid skills list

# Run a skill
python -m grid skills run transform.schema_map --args-json "{text:'...', target_schema:'default', use_llm:false}"

# Build curated RAG index
python -m tools.rag.cli index . --rebuild --curate

# Query RAG
python -m tools.rag.cli query "Where is the skills registry implemented?"
```

## Performance Targets

| Scenario | Target | Command |
|----------|--------|---------|
| Small text | < 15ms | `analyze TEXT --timings` |
| Medium text | < 50ms | `analyze TEXT --max-entities 15 --timings` |
| Large text | < 200ms | `analyze TEXT --max-entities 10 --use-rag --timings` |
| Accuracy focus | P95 < 100ms | `analyze TEXT --confidence 0.5 --max-entities 50` |
| Speed focus | P50 < 20ms | `analyze TEXT --confidence 0.9 --max-entities 5` |

## Common Issues

| Problem | Solution |
|---------|----------|
| "No module named grid" | Run from `e:\grid` root |
| "IndentationError in logging" | ✅ Fixed (renamed file) |
| Slow performance | Use `--max-entities 5` and `--confidence 0.9` |
| Need OpenAI | Set `OPENAI_API_KEY` env var or use `--openai-key` |

## VS Code Tasks

Press `Ctrl+Shift+B` and select:
- `█ PERF · Benchmark GRID (Full Suite)` - Full perf test (~2 min)
- `█ PERF · Analyze Quick` - Small input baseline (~10ms)
- `█ PERF · Analyze with RAG` - Test RAG enhancement (~50ms)
