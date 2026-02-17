# Performance Optimization Guide

## Overview

This guide covers performance optimization strategies for the GRID Agentic System and related components.

## Event Bus Optimization

### In-Memory vs Redis

**Use In-Memory Event Bus** (default):
- Single-node deployments
- Low latency requirements
- Simple setup

**Use Redis Event Bus**:
- Distributed systems
- High throughput
- Event persistence needed

```python
# In-memory (default)
event_bus = EventBus(use_redis=False)

# Redis (distributed)
event_bus = EventBus(
    use_redis=True,
    redis_host="localhost",
    redis_port=6379
)
```

### Event Batching

Batch events when possible to reduce overhead:

```python
# Bad: Individual events
for case in cases:
    await event_bus.publish(event)

# Good: Batch processing
events = [create_event(case) for case in cases]
await asyncio.gather(*[event_bus.publish(e) for e in events])
```

### Event Queue Monitoring

Monitor event queue size to prevent memory issues:

```python
# Check queue size
queue_size = event_bus.event_queue.qsize()
if queue_size > 1000:
    logger.warning(f"Event queue size: {queue_size}")
```

## Database Optimization

### Connection Pooling

Configure connection pooling for better performance:

```python
# In application/mothership/config.py
database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
```

### Async Operations

Always use async database operations:

```python
# Good: Async
async def get_case(case_id: str):
    async with sessionmaker() as session:
        result = await session.execute(select(Case).where(Case.id == case_id))
        return result.scalar_one_or_none()

# Bad: Sync (blocks event loop)
def get_case(case_id: str):
    with sessionmaker() as session:
        return session.query(Case).filter(Case.id == case_id).first()
```

### Query Optimization

- Use indexes on frequently queried fields
- Limit result sets
- Use select_related for joins

```python
# Good: Indexed query with limit
query = select(AgenticCase).where(
    AgenticCase.category == category
).order_by(AgenticCase.created_at.desc()).limit(10)

# Bad: Full table scan
query = select(AgenticCase)
```

## Case Processing Optimization

### Reference File Caching

Cache reference files to avoid regeneration:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_reference_file(case_id: str):
    # Load from disk or generate
    pass
```

### Async Processing

Use async for I/O-bound operations:

```python
# Good: Async processing
async def process_case(case_id: str):
    reference = await load_reference_async(case_id)
    result = await execute_case_async(reference)
    return result

# Bad: Sync processing
def process_case(case_id: str):
    reference = load_reference(case_id)  # Blocks
    result = execute_case(reference)  # Blocks
    return result
```

### Batch Case Processing

Process multiple cases in parallel:

```python
# Process cases in parallel
cases = await get_pending_cases(limit=10)
results = await asyncio.gather(*[
    process_case(case.case_id) for case in cases
])
```

## Memory Optimization

### Case Memory Management

The continuous learning system manages memory automatically:

```python
learning_system = ContinuousLearningSystem(
    memory_path=Path(".case_memory"),
    max_memory_size_mb=100,  # Limit memory usage
    enable_auto_cleanup=True  # Auto-cleanup old entries
)
```

### Event History Limits

Limit event history to prevent memory growth:

```python
# Get recent events only
recent_events = await event_bus.get_event_history(limit=100)
```

## API Performance

### Response Caching

Cache API responses when appropriate:

```python
from functools import lru_cache
from fastapi import Response

@lru_cache(maxsize=100)
async def get_case_cached(case_id: str):
    return await repository.get_case(case_id)
```

### Pagination

Always paginate large result sets:

```python
# Good: Paginated
cases = await repository.list_cases(limit=20, offset=0)

# Bad: All cases
cases = await repository.list_cases()  # Could be thousands
```

### Compression

Enable GZip compression for API responses:

```python
# Already enabled in main.py
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Monitoring and Profiling

### Performance Metrics

Track key metrics:

```python
import time

start_time = time.perf_counter()
result = await process_case(case_id)
duration = time.perf_counter() - start_time

logger.info(f"Case {case_id} processed in {duration:.3f}s")
```

### Event Processing Time

Monitor event processing time:

```python
async def handle_event(event):
    start = time.perf_counter()
    # Process event
    duration = time.perf_counter() - start
    if duration > 1.0:  # Alert if slow
        logger.warning(f"Slow event processing: {duration:.3f}s")
```

## Best Practices

1. **Use async/await**: Always use async for I/O operations
2. **Batch operations**: Group similar operations together
3. **Cache aggressively**: Cache reference files and common queries
4. **Monitor metrics**: Track performance metrics and alert on anomalies
5. **Limit result sets**: Always paginate large queries
6. **Use connection pooling**: Configure appropriate pool sizes
7. **Optimize queries**: Use indexes and efficient queries
8. **Clean up resources**: Close connections and clean up memory

## Performance Targets

- **Case Creation**: < 100ms
- **Case Execution**: < 2s
- **Event Processing**: < 50ms per event
- **API Response**: < 200ms (p95)
- **Database Query**: < 100ms (p95)

## Tools

### Profiling

```bash
# Profile with cProfile
python -m cProfile -o profile.stats -m application.mothership.main

# Analyze with snakeviz
snakeviz profile.stats
```

### Monitoring

```bash
# Monitor API performance
curl -w "@curl-format.txt" http://localhost:8080/api/v1/agentic/cases

# Monitor database queries
# Enable SQLAlchemy echo in config.py
```

## Performance Monitoring Library

GRID includes a comprehensive performance monitoring library at `src/grid/libraries/performance_monitoring.py`:

### Key Features

- **System Metrics**: CPU, memory, disk, network I/O monitoring
- **Operation Tracking**: Track function execution time and success rates
- **Alert Generation**: Automatic alerts when thresholds exceeded
- **Trend Analysis**: Track performance trends over time
- **Export Capabilities**: Export metrics to JSON format

### Usage

```python
from grid.libraries.performance_monitoring import PerformanceMonitor, track_performance

# Get global monitor
monitor = PerformanceMonitor()

# Track operation
call_id = monitor.track_operation_start("my_operation")
# ... do work ...
monitor.track_operation_end("my_operation", call_id, success=True)

# Use decorator
@track_performance("expensive_function")
def expensive_function():
    # ... implementation ...
    pass

# Collect system metrics
metrics = await monitor.collect_system_metrics()

# Get performance summary
summary = monitor.get_performance_summary()
```

### Behavioral Analysis

The behavioral analyzer identifies optimization opportunities:

```python
from grid.skills.behavioral_analyzer import BehavioralAnalyzer

analyzer = BehavioralAnalyzer(execution_tracker, intelligence_tracker)

# Analyze skill behavior
analyses = analyzer.analyze_skill_behavior("skill_id")

# Get optimization recommendations
recommendations = analyzer.get_optimization_recommendations("skill_id")
```

### Patterns Detected

1. **Always Succeeds**: High success rate skills can reduce logging
2. **Always Fails**: Skills needing immediate investigation
3. **Slow Performance**: Skills with >5s average latency
4. **Inconsistent Confidence**: High variance in confidence scores
5. **High Fallback Rate**: Skills with >30% fallback usage

### Workflow Optimization

The workflow orchestrator provides optimization suggestions:

```python
from grid.workflow.orchestrator import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator(context_manager, pattern_service, recognizer)

# Get workflow suggestions
suggestions = orchestrator.get_workflow_suggestions()

# Suggestion types:
# - automation: For frequently repeated tasks with high success rate
# - optimization: For slow tasks (>20-30 minutes)
```

### Performance Analytics

Track detailed performance metrics:

```python
from grid.skills.performance_analytics import PerformanceAnalytics

analytics = PerformanceAnalytics()

# Analyze performance
summary = analytics.analyze_performance(
    skill_id="skill_name",
    time_window_hours=24
)

# Get recommendations
recommendations = analytics._generate_recommendations(summary, anomalies)
```

### Configuration Thresholds

Default thresholds (configurable):

```python
thresholds = {
    "cpu_usage": 80.0,      # Alert when CPU > 80%
    "memory_usage": 85.0,    # Alert when memory > 85%
    "disk_usage": 90.0,      # Alert when disk > 90%
    "response_time": 2.0,    # Alert when response > 2s
    "error_rate": 5.0,       # Alert when error rate > 5%
    "success_rate": 95.0,    # Alert when success rate < 95%
}
```

### Continuous Monitoring

Enable background monitoring:

```python
monitor = PerformanceMonitor(config_path="performance_config.json")

# Start monitoring (60s interval)
monitor.start_monitoring(interval=60)

# ... do work ...

# Stop monitoring
monitor.stop_monitoring()
```

### Export Metrics

```python
# Export to JSON
monitor.export_metrics("metrics_export.json", format="json")
```

## Common Performance Bottlenecks

### 1. Synchronous I/O Operations

**Problem**: Blocking calls prevent concurrent processing

**Solution**: Use async/await for I/O-bound operations

```python
# Bad
def load_data():
    with open("file.txt") as f:
        return f.read()

# Good
async def load_data():
    async with aiofiles.open("file.txt") as f:
        return await f.read()
```

### 2. Excessive Memory Usage

**Problem**: Loading large datasets into memory

**Solution**: Use streaming or chunking

```python
# Bad
data = load_large_file()  # Loads entire file
process(data)

# Good
async def process_stream():
    async for chunk in stream_large_file():
        yield process_chunk(chunk)
```

### 3. N+1 Query Problem

**Problem**: Multiple database queries in loops

**Solution**: Use eager loading or batch queries

```python
# Bad
for user in users:
    orders = get_orders(user.id)  # N queries

# Good
users_with_orders = get_users_with_orders()  # 1 query with join
```

### 4. Inefficient Algorithms

**Problem**: O(n²) algorithms for large datasets

**Solution**: Use more efficient algorithms

```python
# Bad: O(n²)
for i in range(len(items)):
    for j in range(i+1, len(items)):
        compare(items[i], items[j])

# Good: O(n log n) with sorting
sorted_items = sorted(items)
for i in range(len(sorted_items)-1):
    compare(sorted_items[i], sorted_items[i+1])
```

### 5. Missing Caching

**Problem**: Repeated expensive computations

**Solution**: Cache results

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_computation(data):
    # ... expensive operation ...
    return result
```

## Optimization Checklist

### Before Deployment

- [ ] Enable performance monitoring
- [ ] Set appropriate thresholds
- [ ] Configure connection pooling
- [ ] Enable response compression
- [ ] Set up alerting
- [ ] Profile critical paths
- [ ] Test under load

### During Development

- [ ] Use async/await for I/O
- [ ] Batch operations where possible
- [ ] Cache expensive computations
- [ ] Limit result sets with pagination
- [ ] Use indexes on database queries
- [ ] Monitor memory usage
- [ ] Profile slow functions

### In Production

- [ ] Monitor metrics continuously
- [ ] Alert on anomalies
- [ ] Review performance trends
- [ ] Optimize based on data
- [ ] Scale resources as needed
- [ ] Document findings
- [ ] Iterate on improvements

## References

- **Event Bus**: `grid/agentic/event_bus.py`
- **Repository**: `application/mothership/repositories/agentic.py`
- **API**: `application/mothership/routers/agentic.py`
- **Performance Monitor**: `src/grid/libraries/performance_monitoring.py`
- **Performance Analytics**: `src/grid/skills/performance_analytics.py`
- **Behavioral Analyzer**: `src/grid/skills/behavioral_analyzer.py`
- **Workflow Orchestrator**: `src/grid/workflow/orchestrator.py`
