# Benchmark JSON Output & Migration Guide

## Overview

The Grid NER benchmark runner (`circuits/run_benchmark.py` and `circuits/perf_benchmark.py`) now supports structured JSON output. This output format is defined by a JSON schema and supports machine-readable consumption for CI/CD pipelines, dashboards, and automated analysis.

## Usage

### Using the Runner (`run_benchmark.py`)

To generate a consolidated JSON report for all benchmark configurations in the suite:

```bash
python circuits/run_benchmark.py --json-output report.json
```

This will run the benchmarks (Baseline, Medium, Heavy) and write a single JSON file to `report.json` containing the results of all runs.

To print to `stdout`:

```bash
python circuits/run_benchmark.py --json-output -
```

### Using the Worker (`perf_benchmark.py`)

If you want to run a specific benchmark configuration and get JSON output:

```bash
python -m circuits.perf_benchmark \
  --entities 20 \
  --max-pairs 100 \
  --iterations 50 \
  --json-output run_output.json
```

## JSON Schema

The output follows the `grid.baseline_suite.v1` schema.

**Top-level fields:**
- `schema_version`: String identifier.
- `generated_at`: ISO timestamp.
- `environment`: Details about the Python, Platform, and Server env.
- `runs`: Array of benchmark run objects.

**Run object fields:**
- `name`: Name of the benchmark config.
- `config`: Input parameters (entities, max_pairs, etc.).
- `counts_mean`: Average number of entities/relationships processed.
- `client_latency_ms`: Client-side latency stats (min, p50, p95, max, mean, stddev).
- `server_timings_ms`: Server-side timing breakdown.
- `overhead`: Network overhead metrics.
- `server_breakdown_mean`: Percentage breakdown of server stages.

## Migration Guide

If you previously parsed the human-readable text output from stdout, we recommend switching to `--json-output` for robustness.

**Before (Parsing Text):**
```python
# Fragile regex parsing
output = subprocess.check_output([...])
match = re.search(r"client_ms: mean=([\d\.]+)", output)
latency = float(match.group(1))
```

**After (Parsing JSON):**
```python
# Robust JSON parsing
subprocess.run([..., "--json-output", "report.json"])
with open("report.json") as f:
    data = json.load(f)
    latency = data["runs"][0]["client_latency_ms"]["mean"]
```

## Feature Flagging

For experimental usage or incremental rollout, you can control the usage of this flag via your CI configuration. The JSON output path is strictly opt-in via the `--json-output` flag.
