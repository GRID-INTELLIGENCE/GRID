# Grid CLI Usage Guide

## Quick Examples

### Task Management

```bash
# Create a task
grid task create \
  --name "Analyze Data" \
  --desc "Analyze customer data" \
  --effort 2.5 \
  --priority 1

# List all tasks
grid task list

# Filter by state
grid task list --state running

# Get task details
grid task get --id <task-id>

# Update task state
grid task update --id <task-id> --state completed

# Count tasks
grid task count --state completed
```

### Event Management

```bash
# Emit an event
grid event emit \
  --type task.completed \
  --source cli \
  --data '{"duration": 42, "status": "success"}'

# List events
grid event list

# Filter events
grid event list --type task.completed --limit 10

# Clear all events
grid event clear
```

### Workflow Management

```bash
# Load workflow from file
grid workflow load-file --file workflow.yaml

# List workflows
grid workflow list

# Get workflow definition
grid workflow get --id my-workflow

# Execute workflow
grid workflow execute --id my-workflow

# Execute with context
grid workflow execute \
  --id my-workflow \
  --context '{"env": "production", "debug": false}'

# Delete workflow
grid workflow delete --id my-workflow
```

### Output Formats

```bash
# Table format (default)
grid task list

# JSON format
grid task list --format json

# YAML format
grid task list --format yaml

# Key-value format
grid task list --format kv

# Export to file
grid task list --format json > tasks.json
```

## Real-World Scenarios

### Scenario 1: Processing Pipeline

```bash
# 1. Load workflow
grid workflow load-file --file config/workflow_example.yaml

# 2. Create tasks for monitoring
grid task create --name "Data Extraction" --effort 1.5
grid task create --name "Data Transformation" --effort 2.0
grid task create --name "Data Loading" --effort 1.0

# 3. List and verify tasks
grid task list

# 4. Execute workflow
grid workflow execute --id "Basic Data Processing"

# 5. Track events
grid event list --limit 20 --format json

# 6. Generate report
grid task list --format json | tee report.json
```

### Scenario 2: ML Model Training

```bash
# 1. Load ML pipeline
grid workflow load-file --file config/ml_pipeline.json

# 2. Create tracking tasks
grid task create --name "Data Preparation" --effort 3.0 --priority 1
grid task create --name "Model Training" --effort 5.0 --priority 2
grid task create --name "Model Evaluation" --effort 2.0 --priority 3

# 3. Monitor with events
grid event emit \
  --type ml.training_start \
  --source ml_pipeline \
  --data '{"model": "random_forest", "dataset": "customers"}'

# 4. Execute pipeline
grid workflow execute --id "Machine Learning Pipeline"

# 5. Log completion
grid event emit \
  --type ml.training_complete \
  --source ml_pipeline \
  --data '{"accuracy": 0.95, "duration": 1200}'

# 6. Check results
grid task list --state completed
grid event list --type ml.training_complete
```

### Scenario 3: Batch Job Monitoring

```bash
# Create parent task
grid task create --name "Batch Job #42" --effort 0.0 --priority 0

# Create subtasks
for i in {1..10}; do
  grid task create \
    --name "Batch Item $i" \
    --effort $((i * 0.5)) \
    --priority $((i % 3))
done

# List all batch tasks
grid task list

# Track progress with events
for i in {1..10}; do
  grid event emit \
    --type job.item_processed \
    --source batch_processor \
    --data "{\"item\": $i, \"status\": \"completed\"}"
  sleep 1
done

# View progress
grid event list --type job.item_processed
```

### Scenario 4: Configuration Management

```bash
# Show current configuration
grid config show

# Show configuration as JSON
grid config show --format json

# Export configuration
grid config show --format json > config_backup.json

# Show supported formats
grid config formats

# Supported formats: .json, .yaml, .yml, .csv
```

## Integration with Scripts

### Bash Script Integration

```bash
#!/bin/bash
# process_data.sh

set -e

echo "Starting data processing..."

# Create workflow
grid workflow load-file --file workflow.yaml

# Get workflow ID
WORKFLOW_ID=$(grid workflow list --format json | grep -o '"[^"]*"' | head -1)

echo "Executing workflow: $WORKFLOW_ID"

# Execute workflow
grid workflow execute --id "$WORKFLOW_ID"

# Check if successful
if [ $? -eq 0 ]; then
  echo "Workflow completed successfully"
  grid event emit \
    --type pipeline.success \
    --source bash_script \
    --data '{"script": "process_data.sh"}'
else
  echo "Workflow failed"
  grid event emit \
    --type pipeline.failure \
    --source bash_script \
    --data '{"script": "process_data.sh", "error": "execution_failed"}'
  exit 1
fi

# Export results
grid task list --format json > results.json
echo "Results exported to results.json"
```

### Python Integration

```python
#!/usr/bin/env python3
# monitor_pipeline.py

from grid.cli import GridCLI, TaskCommands, EventCommands, WorkflowCommands

# Initialize CLI components
cli = GridCLI()
task_cmd = TaskCommands()
event_cmd = EventCommands()
workflow_cmd = WorkflowCommands()

# Load workflow
print("Loading workflow...")
result = workflow_cmd.load_from_file("config/workflow_example.yaml")
print(result)

# Create tasks programmatically
print("\nCreating tasks...")
tasks = [
    {"name": "Task 1", "effort": 1.5},
    {"name": "Task 2", "effort": 2.0},
    {"name": "Task 3", "effort": 1.0},
]

for task in tasks:
    result = task_cmd.create(
        name=task["name"],
        effort_score=task["effort"]
    )
    print(f"Created: {result}")

# List tasks
print("\nListing tasks...")
tasks_list = task_cmd.list()
print(tasks_list)

# Emit events
print("\nEmitting events...")
event_cmd.emit(
    event_type="pipeline.start",
    source="python_monitor",
    data={"timestamp": "2024-01-01T10:00:00"}
)

# Execute workflow
print("\nExecuting workflow...")
result = workflow_cmd.execute("my-workflow")
print(result)
```

## Performance Tips

### 1. Batch Operations

```bash
# Inefficient: Individual commands
for i in {1..100}; do
  grid task create --name "Task $i"
done

# Better: Use programmatic approach
python batch_create_tasks.py
```

### 2. Output Filtering

```bash
# Filter on client side
grid task list --format json | grep 'running'

# Use native filtering when available
grid task list --state running
```

### 3. Large Data Export

```bash
# Export and process
grid task list --format json | jq '.[] | select(.state == "completed")'

# Pipe to file for big datasets
grid task list --format json > large_dataset.json
```

## Troubleshooting

### Check Installation

```bash
# Verify grid command
which grid
grid --version

# If not found, reinstall
pip install -e ".[dev]"
```

### Enable Debug Mode

```bash
# Run with verbose flag
grid -v task list

# Set environment variable
export GRID_DEBUG=1
grid task list
```

### File Issues

```bash
# Validate JSON
python -m json.tool workflow.json

# Validate YAML
yamllint workflow.yaml

# Check file exists
ls -l config/workflow_example.yaml
```

### Clear State

```bash
# Clear all events
grid event clear

# List remaining
grid event list

# Delete all tasks (use with caution)
for id in $(grid task list --format json | grep -o '"id":"[^"]*"' | cut -d'"' -f4); do
  grid task delete --id "$id"
done
```

## Advanced Usage

### Conditional Execution

```bash
#!/bin/bash
# Execute workflow only if no tasks are running

COUNT=$(grid task count --state running)

if [ "$COUNT" -eq 0 ]; then
  echo "No running tasks, executing workflow"
  grid workflow execute --id my-workflow
else
  echo "Tasks still running, skipping"
  exit 1
fi
```

### Task Status Monitoring

```bash
#!/bin/bash
# Monitor task and exit when complete

TASK_ID="$1"
MAX_WAIT=3600
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
  STATUS=$(grid task get --id "$TASK_ID" --format json | grep -o '"state":"[^"]*"' | cut -d'"' -f4)

  if [ "$STATUS" = "completed" ]; then
    echo "Task completed!"
    exit 0
  elif [ "$STATUS" = "failed" ]; then
    echo "Task failed!"
    exit 1
  fi

  echo "Status: $STATUS (${ELAPSED}s elapsed)"
  sleep 10
  ELAPSED=$((ELAPSED + 10))
done

echo "Task timeout after ${MAX_WAIT}s"
exit 1
```

## Best Practices

1. **Always use descriptive names** for tasks and workflows
2. **Set appropriate effort scores** for workload estimation
3. **Use priority levels** for task scheduling
4. **Track events** for audit trails and debugging
5. **Export results** in JSON for downstream processing
6. **Use aliases** (`t`, `e`, `w`, `c`) for faster typing
7. **Leverage output formats** for different use cases
8. **Validate files** before loading workflows

---

**Last Updated:** November 25, 2025
