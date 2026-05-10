# UsageTracker Queue-Worker Redesign (Wireframe)

## Scope
This document defines a minimal, implementation-ready redesign for `src/grid/billing/usage_tracker.py` to remove unbounded task fan-out under burst traffic.

## Current Behavior (Risk)
- `track_event()` appends to in-memory buffer.
- When threshold is hit, it calls `asyncio.create_task(self.flush())`.
- Under spikes, many concurrent callers can create many flush tasks.
- Locking prevents corruption, but task churn can still increase event-loop load and latency.

## Target Design
Replace threshold-triggered `create_task(flush)` fan-out with:
- Bounded `asyncio.Queue[UsageEvent]`
- Single long-lived consumer worker task
- Deterministic flush cadence (`batch_size` or `flush_interval`)

### Core Flow
1. `track_event()` constructs event and `put_nowait()` into queue.
2. Worker drains queue into local batch.
3. Worker flushes on either:
   - `len(batch) >= batch_size`, or
   - `flush_interval` elapsed.
4. On flush failure, batch goes to dead-letter buffer and is retried by worker.
5. `stop()` signals shutdown, drains queue, flushes remaining events, exits worker.

## Backpressure Policy (Initial)
- Queue capacity: fixed (`max_queue_size`, default e.g. 10_000).
- If queue is full:
  - Default: route event to dead-letter and increment `dropped_events` metric.
  - Optional mode (future flag): await queue space for strict durability paths.

## State Model
- `self._queue: asyncio.Queue[dict[str, Any]]`
- `self._worker_task: asyncio.Task | None`
- `self._stop_event: asyncio.Event`
- `self._dead_letter: list[dict[str, Any]]` (bounded cap retained)
- Counters:
  - `events_enqueued`
  - `events_flushed`
  - `events_dead_lettered`
  - `events_dropped`
  - `flush_failures`

## Pseudocode
```python
async def track_event(...):
    event = make_event(...)
    try:
        self._queue.put_nowait(event)
        self.events_enqueued += 1
    except asyncio.QueueFull:
        self._dead_letter.append(event)
        self.events_dropped += 1

async def _worker_loop():
    batch = []
    while not stop_requested or not self._queue.empty() or batch:
        try:
            item = await asyncio.wait_for(self._queue.get(), timeout=self._flush_interval)
            batch.append(item)
            if len(batch) >= self._batch_size:
                await _flush_batch(batch); batch.clear()
        except TimeoutError:
            if batch:
                await _flush_batch(batch); batch.clear()
    if batch:
        await _flush_batch(batch)
```

## Migration Steps (Monday)
1. Add queue/worker fields and startup/shutdown lifecycle.
2. Refactor `track_event()` to enqueue-only path.
3. Introduce `_worker_loop()` + `_flush_batch()`.
4. Keep existing dead-letter semantics, but move retries into worker.
5. Add lightweight metrics/logging for queue depth and flush outcomes.
6. Remove direct `create_task(self.flush())` call path.

## Test Plan
1. Burst enqueue test:
   - Simulate high concurrent `track_event()` calls.
   - Assert only one worker flush path is active (no flush task fan-out).
2. Queue full test:
   - Small queue size, overload producer.
   - Assert drops/dead-letter behavior matches policy.
3. Flush retry test:
   - Force DB write failure, confirm dead-letter capture and retry.
4. Graceful shutdown test:
   - Enqueue events, call `stop()`, verify queue drained and persisted.
5. Throughput sanity test:
   - Compare event-loop stability before/after under same synthetic burst.

## Non-Goals (This Slice)
- Cross-process durable queue.
- Exactly-once delivery semantics across crashes.
- External broker integration (Redis/Kafka/Celery).

## Acceptance Criteria
- No unbounded flush task creation under burst load.
- Predictable memory growth bounded by queue capacity + dead-letter cap.
- Clean shutdown drains pending events.
- Existing billing usage tests remain green, with new burst/concurrency tests added.
