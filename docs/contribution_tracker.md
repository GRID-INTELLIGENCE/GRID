# Contribution Tracker

The **Contribution Tracker** is a developer tool designed to quantify the "cost" and "value" of development work. It moves beyond simple commit counts to track effort, energy expenditure, and decision-making context.

## Purpose

- **Quantify Effort**: Track time spent and lines of code (LOC) changed.
- **Estimate Energy**: Calculate estimated energy expenditure (Joules) based on compute intensity.
- **Contextualize Changes**: Log the "why" behind changes, not just the "what".
- **Generate Insights**: Provide data-driven summaries of development sessions.

## Key Metrics

| Metric | Description |
| :--- | :--- |
| **Time** | Duration of the work session (minutes). |
| **LOC** | Lines of code added, modified, or deleted. |
| **Energy** | Estimated computational energy used (Joules). |
| **Decisions** | Key architectural or implementation decisions made. |
| **Files** | List of files modified during the session. |

## Usage

The tool is run via the command line:

```bash
# Start a tracking session
python -m src.tools.contribution_tracker start

# Stop the session and generate a report
python -m src.tools.contribution_tracker stop

# View the current session summary
python -m src.tools.contribution_tracker summary
```

## Output

The tracker generates:
1.  **JSON Data**: `contribution_stats.json` (raw data).
2.  **Markdown Report**: `contribution_report.md` (human-readable summary).

## Integration

The Contribution Tracker is integrated with the **Finalization Tool** (`finalize_iteration.py`), allowing you to see contribution stats automatically when wrapping up an iteration.
