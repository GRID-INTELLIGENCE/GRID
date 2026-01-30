# Grid CLI - Quick Reference Card

## Installation

```bash
pip install -e ".[dev]"
grid --version
```

## Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `-v, --verbose` | Enable verbose output |
| `--format {json,yaml,table,kv}` | Output format |
| `-h, --help` | Show help |

## Task Commands (`grid task` or `grid t`)

```bash
grid task create --name "Name" [--desc "Desc"] [--effort 1.5] [--priority 1]
grid task list [--state STATE] [--format FORMAT]
grid task get --id ID [--format FORMAT]
grid task update --id ID [--state STATE] [--effort N] [--priority N]
grid task delete --id ID
grid task count [--state STATE]
```

**States:** `queued`, `running`, `completed`, `failed`, `cancelled`

## Event Commands (`grid event` or `grid e`)

```bash
grid event emit --type TYPE --source SOURCE [--data JSON]
grid event list [--type TYPE] [--limit N] [--format FORMAT]
grid event clear
```

**Common Types:** `task.created`, `task.started`, `task.completed`, `task.failed`

## Workflow Commands (`grid workflow` or `grid w`)

```bash
grid workflow load-file --file PATH
grid workflow register --id ID --name NAME --steps JSON
grid workflow list [--format FORMAT]
grid workflow get --id ID [--format FORMAT]
grid workflow execute --id ID [--context JSON]
grid workflow delete --id ID
```

## Config Commands (`grid config` or `grid c`)

```bash
grid config show [--format FORMAT]
grid config formats
```

## Output Formats

| Format | Usage | Example |
|--------|-------|---------|
| `table` | Human-readable (default) | `grid task list` |
| `json` | Machine-readable JSON | `grid task list --format json` |
| `yaml` | YAML format | `grid task list --format yaml` |
| `kv` | Key-value pairs | `grid task list --format kv` |

## Common Workflows

### Create and Track Task

```bash
TASK=$(grid task create --name "Process Data" --effort 2.5 --format json)
TASK_ID=$(echo $TASK | jq -r '.id')
grid task update --id $TASK_ID --state running
grid event emit --type task.started --source cli --data "{\"task_id\": \"$TASK_ID\"}"
grid task update --id $TASK_ID --state completed
grid event emit --type task.completed --source cli --data "{\"task_id\": \"$TASK_ID\"}"
```

### Load and Execute Workflow

```bash
grid workflow load-file --file workflow.yaml
grid workflow execute --id "Data Processing Pipeline"
grid event list --type task.completed --limit 10 --format json
```

### Export Results

```bash
# Export tasks
grid task list --format json > tasks.json

# Export events
grid event list --format json > events.json

# Export workflow
grid workflow get --id my-workflow --format json > workflow.json
```

## File Formats

### Workflow YAML

```yaml
name: Pipeline Name
steps:
  - id: step1
    type: task_type
    config: {...}
  - id: step2
    depends_on: [step1]
```

### Workflow JSON

```json
{
  "name": "Pipeline Name",
  "steps": [
    {"id": "step1", "type": "task_type"},
    {"id": "step2", "depends_on": ["step1"]}
  ]
}
```

## Tips & Tricks

```bash
# Use aliases for faster typing
grid t list           # instead of grid task list
grid e emit ...       # instead of grid event emit ...
grid w list           # instead of grid workflow list

# Pipe for processing
grid task list --format json | jq '.[] | select(.state=="running")'

# Count items
grid task count
grid task count --state completed

# Import from files
grid workflow load-file --file workflow.yaml

# Monitor tasks
watch -n 1 'grid task count --state running'

# Clear all data
grid event clear
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Command not found | Run `pip install -e ".[dev]"` |
| Permission denied | Make executable: `chmod +x $(which grid)` |
| File not found | Use absolute path or check file exists |
| Invalid JSON | Validate with `python -m json.tool file.json` |
| Import error | Install dependencies: `pip install pyyaml` |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |
| 2 | Invalid arguments |
| 130 | Interrupted (Ctrl+C) |

## Environment Variables

```bash
export GRID_DEBUG=1              # Enable debug mode
export GRID_ENVIRONMENT=prod     # Set environment
export GRID_LOG_LEVEL=DEBUG      # Set log level
```

## Examples

### Task Management

```bash
# Create tasks
grid task create --name "Task 1" --effort 1.5 --priority 1
grid task create --name "Task 2" --effort 2.0 --priority 2

# List all tasks
grid task list

# List running tasks
grid task list --state running

# Get task details
grid task get --id <task-id>

# Update task
grid task update --id <task-id> --state running

# Delete task
grid task delete --id <task-id>
```

### Event Tracking

```bash
# Emit event
grid event emit --type task.created --source cli

# Emit with data
grid event emit --type task.completed --source cli --data '{"duration": 42}'

# List events
grid event list

# Filter events
grid event list --type task.completed

# Export events
grid event list --format json > events.json

# Clear events
grid event clear
```

### Workflow Automation

```bash
# Load workflow
grid workflow load-file --file workflow.yaml

# List workflows
grid workflow list

# Execute workflow
grid workflow execute --id "My Workflow"

# Execute with parameters
grid workflow execute --id "My Workflow" --context '{"env": "prod"}'

# Get workflow definition
grid workflow get --id "My Workflow" --format json
```

## Resources

- **Full Reference:** `docs/CLI_REFERENCE.md`
- **Usage Guide:** `docs/CLI_USAGE.md`
- **Implementation:** `CLI_IMPLEMENTATION.md`
- **Examples:** `config/workflow_example.yaml`, `config/ml_pipeline.json`

---

**Grid CLI v1.0.0** | Ready for Production
