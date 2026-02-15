# Cognitive Pattern System - Practical Usage Examples

## 🎬 Real-World Scenarios

### Scenario 1: Document Analysis Pipeline

**User uploads a document (PDF/Image) for analysis**

#### Frontend (HTML/JavaScript)
```html
<form id="uploadForm">
  <input type="file" id="docFile" accept=".pdf,image/*">
  <textarea id="instructions" placeholder="What do you want analyzed?"></textarea>
  <button>Analyze</button>
</form>

<div id="status">Ready...</div>
<div id="results"></div>

<script>
document.getElementById('uploadForm').onsubmit = async (e) => {
  e.preventDefault();
  
  const form = new FormData();
  form.append('file', document.getElementById('docFile').files[0]);
  form.append('context', document.getElementById('instructions').value);
  form.append('analysis_type', 'multi_modal_reasoning');
  
  // Submit analysis
  const res = await fetch('/api/cognitive/vision/analyze', {
    method: 'POST',
    body: form
  });
  
  const {correlation_id} = await res.json();
  document.getElementById('status').textContent = 'Processing...';
  
  // Connect to updates
  const ws = new WebSocket(
    `ws://localhost:8000/api/cognitive/ws/updates/${correlation_id}`
  );
  
  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    if (update.type.includes('notification:cognitive_pattern')) {
      // Show result
      document.getElementById('results').innerHTML += `
        <div class="result">
          <h3>${update.pattern}</h3>
          <p class="message">${update.data.message}</p>
          <p class="load">Load: ${update.load_level}</p>
        </div>
      `;
      document.getElementById('status').textContent = 'Complete!';
    } else if (update.type.includes('output:sound')) {
      // Sound was played
      console.log('📢 Notification sound played');
    } else if (update.type.includes('accessibility')) {
      // Screen reader announcement
      console.log('♿ Accessibility:', update.data.message);
    }
  };
};
</script>
```

#### Backend (FastAPI)
```python
# apps/backend/routers/documents.py
from fastapi import APIRouter
from cognitive.integration import event_bus

router = APIRouter()

@router.post("/api/cognitive/vision/analyze")
async def analyze_document(file: UploadFile, context: str):
    # Endpoint automatically provided by integrate_cognitive_patterns()
    # System handles:
    # 1. Event emission
    # 2. Load assessment
    # 3. Domain routing (ML → VLM → CV)
    # 4. Notification system
    # 5. WebSocket streaming
    pass
```

---

### Scenario 2: Real-Time Progress Updates

**Complex analysis that takes 10+ seconds - show progress**

#### Handler Code
```python
# grid/src/cognitive/handlers/document_analyzer.py
from grid.events import Event, EventBus, EventPriority
import asyncio

class DocumentAnalysisHandler:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.bus.subscribe(
            pattern="vision:multi_modal_reasoning",
            handler=self.handle_analysis,
            priority=EventPriority.HIGH
        )
    
    async def handle_analysis(self, event: Event) -> None:
        """Analyze document with progress updates."""
        stages = [
            ("preprocessing", "Extracting text and structure"),
            ("entity_extraction", "Identifying entities and relationships"),
            ("inference", "Running language model"),
            ("summarization", "Generating summary"),
            ("validation", "Validating results"),
        ]
        
        for stage, description in stages:
            # Emit progress update
            progress_event = event.spawn_child(
                event_type="vision:analysis_update",
                data={
                    "stage": stage,
                    "description": description,
                    "progress": len([s for s in stages[:stages.index((stage, description))+1]]) / len(stages),
                },
                source="document_analyzer"
            )
            self.bus.emit(progress_event)
            
            # Simulate stage processing
            await asyncio.sleep(2)
        
        # Emit completion
        completion_event = event.spawn_child(
            event_type="notification:cognitive_pattern_update",
            data={
                "pattern": "document_analysis",
                "status": "complete",
                "output_summary": "Document analyzed: 47 entities found, 3 key insights",
                "confidence": 0.96,
            },
            source="document_analyzer",
            priority=EventPriority.HIGH
        )
        self.bus.emit(completion_event)
```

#### Frontend Display
```javascript
// Update progress bar as events arrive
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  if (update.type.includes('vision:analysis_update')) {
    // Update progress bar
    const percent = Math.round(update.data.progress * 100);
    document.getElementById('progress').style.width = percent + '%';
    document.getElementById('stage').textContent = update.data.description;
  }
};
```

---

### Scenario 3: Load-Aware User Experience

**User is busy (high cognitive load) - reduce notification detail**

#### How It Works
```python
# Notification system automatically detects load

# SCENARIO A: User has low load
# → Detail level = HIGH
# → Message = "Document analysis complete (96% confidence). 
#   Found 47 entities: Person (23), Organization (15), Location (9). 
#   Key insights: 1) Company restructuring, 2) New partnerships, 3) Market expansion"
# → Sound: Played (0.9 volume)
# → Accessibility: Full announcement with details

# SCENARIO B: User has HIGH load (multiple analyses running)
# → Detail level = LOW
# → Message = "Document analysis: 47 entities found, 3 insights"
# → Sound: Not played (queue at max)
# → Accessibility: Polite announcement (doesn't interrupt)

# SCENARIO C: User has CRITICAL load (system saturated)
# → Detail level = MINIMAL
# → Message = "Analysis ready"
# → Sound: Definitely not played
# → Accessibility: Minimal label only
```

#### Configuration
```python
# apps/backend/config.py
from cognitive.notification_system import NotificationConfig

NOTIFICATION_CONFIG = NotificationConfig(
    enable_persistent_context=True,      # Track context across notifications
    sound_enabled=True,                  # Enable audio
    haptic_enabled=False,                # No haptic yet
    max_queue_depth=100,                 # Prevent queue overflow
    dedup_window_seconds=300,            # 5 minute dedup window
    max_sound_per_minute=5,              # Max 5 sounds/min
)
```

---

### Scenario 4: Error Handling & Recovery

**Analysis fails - graceful notification**

#### Error Handler
```python
# grid/src/cognitive/handlers/error_handler.py
async def handle_vision_error(original_event: Event, error: Exception) -> None:
    """Handle vision analysis errors."""
    
    # Emit error notification
    error_event = original_event.spawn_child(
        event_type="notification:cognitive_pattern_update",
        data={
            "pattern": "document_analysis",
            "status": "failed",
            "error": str(error),
            "output_summary": f"Analysis failed: {type(error).__name__}",
            "confidence": 0.0,
        },
        source="error_handler",
        priority=EventPriority.HIGHEST  # High priority errors
    )
    
    event_bus.emit(error_event)
    
    # Optionally retry
    if should_retry(error):
        logger.info(f"Retrying analysis: {original_event.correlation_id}")
        await asyncio.sleep(1)
        event_bus.emit(original_event)  # Replay event
```

#### Frontend Error Display
```javascript
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  if (update.data.status === 'failed') {
    document.getElementById('error').innerHTML = `
      <div class="error-box">
        <h3>⚠️ Analysis Failed</h3>
        <p>${update.data.error}</p>
        <button onclick="retryAnalysis()">Retry</button>
      </div>
    `;
  }
};
```

---

### Scenario 5: Multi-Step Cognitive Pattern

**Chain multiple patterns: Extract → Analyze → Summarize**

#### Orchestration
```python
# grid/src/cognitive/orchestrators/multi_step_analyzer.py
from grid.events import EventBus, Event, EventPriority

class MultiStepAnalyzer:
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.bus.subscribe(
            pattern="vision:*",
            handler=self.orchestrate,
            priority=EventPriority.HIGH
        )
    
    async def orchestrate(self, event: Event) -> None:
        """Run multi-step analysis pipeline."""
        
        # Step 1: Extract
        extract_event = event.spawn_child(
            event_type="vision:extract",
            data=event.data,
            source="orchestrator"
        )
        self.bus.emit(extract_event)
        await self._wait_for_completion(extract_event.event_id)
        
        # Step 2: Analyze
        analysis_event = extract_event.spawn_child(
            event_type="vision:analyze_extracted",
            data={...},
            source="orchestrator"
        )
        self.bus.emit(analysis_event)
        await self._wait_for_completion(analysis_event.event_id)
        
        # Step 3: Summarize
        summary_event = analysis_event.spawn_child(
            event_type="vision:summarize",
            data={...},
            source="orchestrator"
        )
        self.bus.emit(summary_event)
        await self._wait_for_completion(summary_event.event_id)
        
        # Final notification
        final_event = summary_event.spawn_child(
            event_type="notification:cognitive_pattern_update",
            data={
                "pattern": "multi_step_analysis",
                "status": "complete",
                "steps": ["extract", "analyze", "summarize"],
                "output_summary": "Multi-step analysis complete",
            },
            source="orchestrator",
            priority=EventPriority.HIGH
        )
        self.bus.emit(final_event)
```

---

### Scenario 6: Accessibility Integration

**Full accessibility support: Screen reader + Haptic**

#### Accessibility Output
```python
# Automatic accessibility events emitted

event = Event(
    type="output:accessibility:announce",
    data={
        "message": "Document analysis complete. 47 entities found. Summary: Document shows company restructuring, new partnerships, and market expansion initiatives.",
        "priority": "assertive" if urgent else "polite",
        "role": "alert" if error else "status",
    },
    source="notification_system"
)

# Also emit for haptic
event = Event(
    type="output:haptic:feedback",
    data={
        "pattern": "pulse",  # or "double_tap", "success", "error"
        "intensity": 0.8,
        "duration_ms": 200,
    },
    source="notification_system"
)
```

#### Frontend Implementation
```javascript
// Listen for accessibility events
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  if (update.type.includes('accessibility:announce')) {
    // Screen reader announcement
    const announcement = document.createElement('div');
    announcement.className = 'sr-only';
    announcement.role = update.data.role;
    announcement.setAttribute('aria-live', update.data.priority);
    announcement.textContent = update.data.message;
    document.body.appendChild(announcement);
    
    // Auto-remove after announcement
    setTimeout(() => announcement.remove(), 1000);
  }
  
  if (update.type.includes('haptic:feedback')) {
    // Haptic feedback via Vibration API
    navigator.vibrate([
      update.data.intensity * 1000,  // Vibrate
      100,                            // Pause
      update.data.intensity * 500,    // Vibrate again
    ]);
  }
};
```

---

## 🧪 Testing & Debugging

### Test Notification System Directly

```python
# test_notification_system.py
from grid.events import EventBus, Event
from cognitive.notification_system import CognitivePatternNotificationSystem

bus = EventBus()
notifier = CognitivePatternNotificationSystem(bus)

# Test 1: Normal notification
event = Event(
    type="notification:cognitive_pattern_update",
    data={"pattern": "vision_analysis", "status": "complete"},
    source="test"
)
bus.emit(event)

# Test 2: Duplicate prevention
bus.emit(event)  # Should be deduped
metrics = notifier.get_metrics()
print(f"Sent: {metrics['notifications_sent']}, Deduped: {metrics['notifications_deduped']}")
# Expected: Sent: 1, Deduped: 1

# Test 3: Load-aware detail
high_load_event = event.spawn_child(
    event_type="notification:cognitive_pattern_update",
    data=event.data,
    source="test",
    metadata={"load_level": "CRITICAL"}
)
bus.emit(high_load_event)
# Detail level should be MINIMAL
```

### Monitor in Production

```bash
# Check metrics endpoint
watch -n 1 'curl -s http://localhost:8000/api/cognitive/metrics | python -m json.tool'

# Watch logs
tail -f /var/log/cognitive_patterns.log | grep notification

# Test WebSocket connection
wscat -c ws://localhost:8000/api/cognitive/ws/updates/test-correlation-id
```

---

## 🚀 Integration Checklist

- [ ] Import `integrate_cognitive_patterns` in main.py
- [ ] Call `integrate_cognitive_patterns(app)` after FastAPI setup
- [ ] Test `POST /api/cognitive/vision/analyze` endpoint
- [ ] Test WebSocket connection at `ws://host/api/cognitive/ws/updates/{id}`
- [ ] Verify notification system metrics at `GET /api/cognitive/metrics`
- [ ] Configure `NotificationConfig` for your requirements
- [ ] Test accessibility output with screen reader
- [ ] Monitor queue depth and dedup cache size
- [ ] Set up logging for cognitive pattern events
- [ ] Add error handling for failed analyses

---

**Ready to use!** Start with Scenario 1 and adapt to your needs.
