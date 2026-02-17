# Cognitive Pattern System - Quick Reference Guide

## 📋 Overview

The Cognitive Pattern System coordinates multi-domain operations (ML, VLM, CV, Animation) through event-driven architecture with load-aware notifications.

## 🚀 Quick Start

### 1. Initialize in FastAPI

```python
from fastapi import FastAPI
from cognitive.integration import integrate_cognitive_patterns

app = FastAPI()
integrate_cognitive_patterns(app)
```

This automatically:
- Starts EventBus
- Initializes CognitiveLoadEstimator
- Creates NotificationSystem
- Mounts `/api/cognitive/*` endpoints

### 2. Call Vision Analysis Endpoint

```bash
curl -X POST http://localhost:8000/api/cognitive/vision/analyze \
  -F "file=@image.jpg" \
  -F "context=Analyze this image"
```

Response:
```json
{
  "correlation_id": "abc-123-def-456",
  "status": "processing",
  "expected_duration_ms": 2000
}
```

### 3. Connect WebSocket for Updates

```javascript
// JavaScript client
const correlationId = "abc-123-def-456";
const ws = new WebSocket(
  `ws://localhost:8000/api/cognitive/ws/updates/${correlationId}`
);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Pattern: ${update.pattern}, Status: ${update.status}`);
  console.log(`Detail Level: ${update.detail_level}`);
  console.log(`Load Level: ${update.load_level}`);
};
```

## 🔌 Event System

### Event Types

```python
# Vision events
"vision:multi_modal_reasoning"   # Image + context through VLM
"vision:image_analysis"          # CV detection/segmentation
"vision:load_assessed"           # Load state computed

# ML events
"ml:inference:start"             # Model inference started
"ml:inference:complete"          # Model inference done

# Notification events
"notification:cognitive_pattern_update"  # Pattern completed

# Output events
"output:notification:display"    # UI display
"output:sound:play"              # Audio notification
"output:accessibility:announce"  # Screen reader
```

### Subscribing to Events

```python
from grid.events import EventBus, EventPriority

bus = EventBus()

# Subscribe with pattern matching
async def handle_vision_event(event):
    print(f"Vision event: {event.type}")
    print(f"Correlation: {event.correlation_id}")
    print(f"Load level: {event.metadata.get('load_level')}")

bus.subscribe(
    pattern="vision:*",
    handler=handle_vision_event,
    priority=EventPriority.HIGH
)

# Subscribe to output events
bus.subscribe(
    pattern="output:*",
    handler=handle_output_event,
    priority=EventPriority.NORMAL
)
```

### Emitting Events

```python
from grid.events import Event, EventPriority

event = Event(
    type="vision:multi_modal_reasoning",
    data={
        "image": image_bytes,
        "context": "Analyze this",
    },
    source="web_api",
    priority=EventPriority.HIGH,
    metadata={
        "load_level": "MODERATE",
    }
)

bus.emit(event)

# Create child event (preserves correlation_id)
child_event = event.spawn_child(
    event_type="ml:inference:start",
    data={"model_type": "vlm"},
    source="vision_handler"
)
bus.emit(child_event)
```

## 📢 Notification System

### Configuration

```python
from cognitive.notification_system import (
    CognitivePatternNotificationSystem,
    NotificationConfig,
)

config = NotificationConfig(
    enable_persistent_context=True,   # Track context across notifications
    sound_enabled=True,               # Play sounds for events
    haptic_enabled=False,             # Haptic feedback
    max_queue_depth=100,              # Max queued notifications
    dedup_window_seconds=300,         # 5-min dedup window
    max_sound_per_minute=5,           # Limit audio frequency
)

notifier = CognitivePatternNotificationSystem(
    event_bus=bus,
    config=config
)
```

### Notification Details

Notifications are dynamically detailed based on cognitive load:

| Load Level | Detail Level | Example |
|-----------|--------------|---------|
| CRITICAL  | MINIMAL      | "Pattern ready" |
| HIGH      | LOW          | "Vision analysis: Results ready" |
| MODERATE  | MEDIUM       | "Pattern complete (92% confidence)" |
| LOW/IDLE  | HIGH         | "Full details: Model inference, timing, confidence, results" |

### Metrics

```python
metrics = notifier.get_metrics()
# {
#   "notifications_sent": 45,
#   "notifications_deduped": 12,
#   "queue_depth": 2,
#   "dedup_cache_size": 8,
#   "sound_emissions_this_minute": 3
# }
```

## 🔗 Integration Points

### Web API Endpoints

```
POST   /api/cognitive/vision/analyze
       Upload image + context, returns correlation_id

WS     /api/cognitive/ws/updates/{correlation_id}
       Stream real-time updates to client

GET    /api/cognitive/metrics
       System metrics and statistics

GET    /api/cognitive/health
       Health check status
```

### Event Middleware

```python
@app.middleware("http")
async def cognitive_middleware(request, call_next):
    # Track request correlation
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    response = await call_next(request)
    
    # Emit request completion event
    event = Event(
        type="processing:http_request:completed",
        data={"path": request.url.path, "status": response.status_code},
        source="http_middleware",
        correlation_id=correlation_id
    )
    bus.emit(event)
    
    return response
```

## 🧠 Cognitive Load States

```python
from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import CognitiveLoadType

# Load levels (from lowest to highest cognitive demand)
CognitiveLoadType.IDLE         # No processing
CognitiveLoadType.LOW          # Simple tasks
CognitiveLoadType.MODERATE     # Normal processing
CognitiveLoadType.HIGH         # Complex tasks
CognitiveLoadType.CRITICAL     # System overloaded
```

## 🛠️ Development Patterns

### Pattern 1: Vision + Multi-Modal Analysis

```python
async def analyze_document(image, context):
    # Emit multi-modal event
    event = Event(
        type="vision:multi_modal_reasoning",
        data={
            "image": image,
            "context": context,
        },
        source="document_processor"
    )
    bus.emit(event)
    
    # Notification automatically sent via notification system
    # - Load-aware detail level
    # - Sound (if not overloaded)
    # - Accessibility announcement
```

### Pattern 2: Progressive Analysis Updates

```python
async def progressive_analysis(event):
    # Emit load assessment
    load_event = event.spawn_child(
        event_type="vision:load_assessed",
        data={"complexity": 5},
        source="analyzer"
    )
    bus.emit(load_event)
    
    # Process in stages, emit updates
    for i, stage in enumerate(["preprocessing", "inference", "postprocessing"]):
        update = event.spawn_child(
            event_type="vision:analysis_update",
            data={"stage": stage, "progress": (i+1)/3},
            source="analyzer"
        )
        bus.emit(update)
        await asyncio.sleep(0.5)
    
    # Emit completion (triggers notification)
    completion = event.spawn_child(
        event_type="notification:cognitive_pattern_update",
        data={"pattern": "vision_analysis", "status": "complete"},
        source="analyzer"
    )
    bus.emit(completion)
```

### Pattern 3: Error Handling with Notifications

```python
try:
    result = await process_vision(image)
except Exception as e:
    error_event = event.spawn_child(
        event_type="notification:cognitive_pattern_update",
        data={
            "pattern": "vision_analysis",
            "status": "failed",
            "error": str(e),
        },
        source="error_handler",
        priority=EventPriority.HIGH
    )
    bus.emit(error_event)
```

## 📊 Monitoring & Diagnostics

### Health Check

```python
response = requests.get("http://localhost:8000/api/cognitive/health")
# {
#   "status": "healthy",
#   "event_bus": "running",
#   "notification_system": "running"
# }
```

### Metrics

```python
response = requests.get("http://localhost:8000/api/cognitive/metrics")
# {
#   "notifications": {
#     "notifications_sent": 45,
#     "notifications_deduped": 12,
#     "queue_depth": 2
#   },
#   "active_connections": {
#     "abc-123": 1,
#     "def-456": 2
#   }
# }
```

### Event Logging

```python
import logging

logger = logging.getLogger("cognitive_patterns")
logger.setLevel(logging.DEBUG)

# Events automatically logged:
# - Vision event received
# - Load assessment computed
# - Notification sent/deduped
# - WebSocket connection/disconnection
```

## 🔐 Persistence & Organization (15% Context)

### Cache Management

```bash
# Monitor cache sizes
du -sh E:\grid\.rag_db/
du -sh E:\Apps\data/cache/

# Clear old data
find E:\Apps\data -name "*.json.gz" -mtime +7 -delete
```

### Notification Queue Monitoring

```python
# Prevent queue overflow
metrics = notifier.get_metrics()
if metrics["queue_depth"] > 50:
    logger.warning("Notification queue backing up")
    await notifier._drain_queue()
```

### Dedup Cache Cleanup

```python
# Automatic cleanup every 5 minutes
while True:
    await asyncio.sleep(300)
    await notifier._cleanup_expired_records()
    logger.debug(f"Dedup cache: {len(notifier.dedup_records)} entries")
```

## 📚 Complete Example: Web Form Integration

```python
# Frontend: index.html
<form id="analysisForm">
  <input type="file" id="imageInput" accept="image/*">
  <textarea id="contextInput" placeholder="Enter context..."></textarea>
  <button type="submit">Analyze</button>
</form>

<div id="results"></div>

<script>
document.getElementById('analysisForm').onsubmit = async (e) => {
  e.preventDefault();
  
  const formData = new FormData();
  formData.append('file', document.getElementById('imageInput').files[0]);
  formData.append('context', document.getElementById('contextInput').value);
  
  const response = await fetch('/api/cognitive/vision/analyze', {
    method: 'POST',
    body: formData
  });
  
  const {correlation_id} = await response.json();
  
  // Connect WebSocket
  const ws = new WebSocket(`ws://localhost:8000/api/cognitive/ws/updates/${correlation_id}`);
  
  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    document.getElementById('results').innerHTML += `<p>${update.pattern}: ${update.status}</p>`;
  };
};
</script>
```

---

## 🎯 Next Steps

1. **Integrate into FastAPI app**: Call `integrate_cognitive_patterns(app)`
2. **Test vision endpoint**: POST to `/api/cognitive/vision/analyze`
3. **Connect WebSocket**: Subscribe to updates via `ws://.../updates/{correlation_id}`
4. **Monitor metrics**: Check `/api/cognitive/metrics` and `/api/cognitive/health`
5. **Configure notifications**: Customize `NotificationConfig` based on requirements
