# Grid CLI - Command Reference

**Subject:** CLI
**Version:** v1.0
**Canonical:** Yes

## 1. Overview

Grid CLI provides a comprehensive command-line interface for managing tasks, events, and workflows. It supports file ingestion from JSON, YAML, and CSV formats with rich output formatting.

### Key Features
- **Task Management:** Create, list, update, and delete tasks.
- **Event Tracking:** Emit and list events for system observability.
- **Workflow Orchestration:** Load, register, and execute workflows.
- **File Ingestion:** Support for JSON, YAML, and CSV.
- **Rich Output:** Tables, JSON, YAML, and Key-Value formats.

## 2. Installation

```bash
# Install Grid with CLI support
pip install -e ".[dev]"

# Verify installation
grid --version
```

## 3. Quick Reference

### Global Options

| Option | Description |
|---|---|
| `--version` | Show version and exit |
| `-v, --verbose` | Enable verbose output |
| `--format {json,yaml,table,kv}` | Output format |
| `-h, --help` | Show help |

### Common Commands

| Domain | Command | Description |
|---|---|---|
| **Task** | `grid task list` | List all tasks |
| | `grid task create` | Create a new task |
| **Event** | `grid event list` | List recent events |
| | `grid event emit` | Emit a custom event |
| **Workflow** | `grid workflow list` | List registered workflows |
| | `grid workflow execute` | Run a workflow |
| **Config** | `grid config show` | Display current config |

## 4. Usage Guide

### 4.1 Task Management (`grid task` or `grid t`)

#### List Tasks
```bash
# List all tasks
grid task list

# List running tasks only
grid task list --state running

# Output as JSON
grid task list --format json
```

#### Create Task
```bash
grid task create \
  --name "Process Payment" \
  --desc "Process customer payment" \
  --effort 2.5 \
  --priority 1
```

#### Update Task
```bash
grid task update --id <task-id> --state running
```

### 4.2 Event Management (`grid event` or `grid e`)

#### Emit Event
```bash
grid event emit \
  --type task.completed \
  --source workflow \
  --data '{"duration": 42, "status": "success"}'
```

#### List Events
```bash
grid event list --type task.created --limit 10
```

### 4.3 Workflow Management (`grid workflow` or `grid w`)

#### Load Workflow
```bash
grid workflow load-file --file workflow.yaml
```

#### Execute Workflow
```bash
grid workflow execute --id my-workflow --context '{"env": "prod"}'
```

## 5. Implementation Details

### 5.1 Architecture
The CLI is built on a modular architecture:
1.  **Entry Point:** `src/grid/cli/main.py` handles argument parsing and dispatch.
1.  **Commands:** `src/grid/cli/commands.py` contains the logic for each domain (Task, Event, Workflow).
1.  **Utilities:** `src/grid/cli/utils.py` provides formatters (Table, JSON, etc.).
1.  **Ingestion:** `src/grid/cli/ingestion.py` handles file parsing (JSON, YAML, CSV).

### 5.2 File Ingestion
The `FileIngestionService` supports:
1.  **JSON:** Native parsing.
1.  **YAML:** Uses `PyYAML`.
1.  **CSV:** Standard library `csv` module.

### 5.3 Output Formatting
The `OutputFormatter` class handles:
1.  **Table:** Uses `tabulate` (or custom implementation) for human-readable output.
1.  **JSON:** Standard `json.dumps`.
1.  **YAML:** `yaml.dump`.
1.  **KV:** Simple Key-Value text format.

## 6. Troubleshooting

### Common Issues

| Problem | Solution |
|---|---|
| **Command not found** | Ensure `pip install -e .` was run. Check `PATH`. |
| **Permission denied** | Run `chmod +x $(which grid)`. |
| **File not found** | Use absolute paths. Check file permissions. |
| **Invalid JSON** | Validate input with `python -m json.tool`. |
| **Import error** | Install dependencies: `pip install pyyaml`. |

### Debugging
Enable verbose logging to diagnose issues:
```bash
export GRID_DEBUG=1
grid -v task list
```

## 7. See Also
- [QUICKSTART.md](../../QUICKSTART.md)
- [README.md](../../docs/README.md)
