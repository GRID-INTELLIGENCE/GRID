# 🎯 GRID Commands & Performance Support - Complete Setup

## What's Ready

### ✅ CLI Commands
The `grid analyze` command is fully operational:

```powershell
# Start here - basic analysis
python -m grid analyze "Your text here"

# See all options
python -m grid analyze --help
```

---

## 📚 Documentation (3 Guides)

### 1. **[GRID_COMMANDS_PERFORMANCE.md](./GRID_COMMANDS_PERFORMANCE.md)** ← START HERE
- **1500+ lines** - Complete reference
- Command syntax and options
- Real-world examples
- Performance tuning strategies
- Troubleshooting guide
- Environment variables
- VS Code integration

### 2. **[GRID_QUICK_REFERENCE.md](./GRID_QUICK_REFERENCE.md)** ← QUICK LOOKUP
- One-liner commands
- Performance targets table
- Common issues & fixes
- Quick task access

### 3. **[PERFORMANCE_STATUS.md](./PERFORMANCE_STATUS.md)** ← STATUS CHECK
- What was fixed
- Current performance baseline
- Available tools
- Next steps

---

## 🚀 Quick Start (Choose Your Path)

### Path A: I want to analyze text RIGHT NOW
```powershell
python -m grid analyze "Harry Potter attended Hogwarts School of Witchcraft"
```

### Path B: I want to see performance timing
```powershell
python -m grid analyze "Harry Potter attended Hogwarts..." --timings
```

### Path C: I want to benchmark performance
```powershell
python scripts/benchmark_grid.py
```

### Path D: I want to use VS Code tasks
1. Press `Ctrl+Shift+B`
2. Select one of:
   - `█ PERF · Benchmark GRID (Full Suite)`
   - `█ PERF · Analyze Quick (Small Input)`
   - `█ PERF · Analyze with RAG (Medium Input)`

---

## 🎛️ Command Options Quick Lookup

| What You Want | Command |
|--------------|---------|
| Basic analysis | `python -m grid analyze TEXT` |
| JSON output | `--output json` |
| YAML output | `--output yaml` |
| Table output (default) | `--output table` |
| Show timing breakdown | `--timings` |
| Read from file | `--file path/to/file.txt` |
| Better accuracy | `--confidence 0.5` |
| Better speed | `--confidence 0.9` |
| Limit entities | `--max-entities 10` |
| Use AI context | `--use-rag` |
| Custom API key | `--openai-key sk-xxx` |

---

## ⚡ Performance Targets

| Scenario | Command | Target |
|----------|---------|--------|
| Baseline | `analyze TEXT` | < 20ms |
| Fast | `analyze TEXT --confidence 0.9 --max-entities 5` | < 10ms |
| Accurate | `analyze TEXT --confidence 0.5 --max-entities 50` | < 100ms |
| With RAG | `analyze TEXT --use-rag` | < 200ms |

---

## 🔧 Tools Included

### Benchmark Suite (`scripts/benchmark_grid.py`)
Comprehensive performance testing:
- ✅ Tests small, medium, large inputs
- ✅ Measures 5+ runs per scenario
- ✅ Calculates p50, p95, min, max, stdev
- ✅ Exports JSON results for tracking
- ✅ Shows stage breakdown (init, NER, relationships, total)

**Usage:**
```powershell
python scripts/benchmark_grid.py
# Creates: benchmarks/grid_benchmark_<timestamp>.json
```

### VS Code Tasks
3 performance monitoring tasks in workspace:
- **█ PERF · Benchmark GRID (Full Suite)** - 13-run comprehensive test
- **█ PERF · Analyze Quick** - Fast baseline (8-15ms)
- **█ PERF · Analyze with RAG** - Test context enhancement

Access: Press `Ctrl+Shift+B` or `Ctrl+Shift+P` → Tasks: Run Task

---

## 🐛 Known Issues & Fixes

### ✅ Issue: IndentationError in logging
**Status**: FIXED
- Root cause: `circuits/logging.py` shadowed stdlib `logging`
- Solution: Renamed to `circuits/logging_compat.py`
- Verification: `python -m grid analyze --help` works

### ✅ Issue: Slow relationship analysis
**Status**: MANAGEABLE
- Solution: Use `--max-entities 5` to limit entity pairs
- Alternative: Increase `--confidence` to reduce entities
- Expected: < 50ms for medium input with these options

### ⚠️ Issue: OpenAI key needed for RAG
**Status**: OPTIONAL
- RAG requires `OPENAI_API_KEY` environment variable
- Works without RAG (just without enhanced context)
- Set via: `$env:OPENAI_API_KEY = "your-key"`

---

## 📊 Latest Baseline

```
Test Text: "Harry Potter is a wizard. Hermione is smart. Ron is his friend..."
Length: 85 characters
Entities Found: 7
Relationships: 8

Performance:
  init: 2.2ms
  ner: 1.0ms
  relationships: 0.0ms
  total: 7.9ms

Status: ✅ HEALTHY
```

---

## 📖 Examples by Use Case

### Academic/Research Analysis
```powershell
python -m grid analyze TEXT --confidence 0.5 --output json --max-entities 50
```
Goal: Maximize accuracy and entity/relationship coverage

### Real-time Application
```powershell
python -m grid analyze TEXT --confidence 0.9 --output json --max-entities 5
```
Goal: Fast response (< 20ms)

### Enhanced Context Analysis
```powershell
python -m grid analyze TEXT --use-rag --output json --timings
```
Goal: Add external knowledge context

### Batch Processing
```powershell
# See GRID_COMMANDS_PERFORMANCE.md for batch processing example
python batch_process.py < input_file.txt > results.json
```

### Performance Monitoring
```powershell
python scripts/benchmark_grid.py
# Daily tracking: Run monthly to track trends
```

---

## 🎓 Learning Path

**New to GRID?**
1. Read: [GRID_QUICK_REFERENCE.md](./GRID_QUICK_REFERENCE.md) (2 min)
2. Try: `python -m grid analyze "Your text"` (1 min)
3. Explore: `python -m grid analyze --help` (2 min)

**Want Performance Details?**
1. Read: [GRID_COMMANDS_PERFORMANCE.md](./GRID_COMMANDS_PERFORMANCE.md) (15 min)
2. Run: `python scripts/benchmark_grid.py` (2 min)
3. Review: `benchmarks/grid_benchmark_*.json` (5 min)

**Integrating Into Your Workflow?**
1. Copy benchmark tool: `scripts/benchmark_grid.py`
2. Set up daily monitoring: Add to CI/CD or task scheduler
3. Track performance: Import JSON results into dashboard

---

## 🆘 Troubleshooting

**Command not found?**
```powershell
cd e:\grid
python -m grid analyze --help
```

**Slow performance?**
```powershell
python -m grid analyze TEXT --timings
# Shows breakdown: init | ner | relationships | total
# If relationships is slow: use --max-entities 5
```

**Import errors?**
```powershell
python -c "import logging; print('OK')"
# If fails, check: circuits/logging_compat.py exists
```

See [GRID_COMMANDS_PERFORMANCE.md](./GRID_COMMANDS_PERFORMANCE.md) Troubleshooting section for more.

---

## ✅ Final Checklist

- ✅ CLI working: `python -m grid analyze --help`
- ✅ Benchmark tool ready: `scripts/benchmark_grid.py`
- ✅ VS Code tasks configured
- ✅ Documentation complete (3 guides)
- ✅ Examples provided
- ✅ Baseline performance established
- ✅ Troubleshooting guide available

---

## 📞 Quick Links

| Need | File |
|------|------|
| Complete reference | [GRID_COMMANDS_PERFORMANCE.md](./GRID_COMMANDS_PERFORMANCE.md) |
| Quick lookup | [GRID_QUICK_REFERENCE.md](./GRID_QUICK_REFERENCE.md) |
| Status check | [PERFORMANCE_STATUS.md](./PERFORMANCE_STATUS.md) |
| Benchmark tool | `scripts/benchmark_grid.py` |
| CLI source | `circuits/cli/main.py` |

---

**Status**: ✅ READY TO USE

All GRID commands and performance support systems are operational and documented.
Start with: `python -m grid analyze "Your text here"`
