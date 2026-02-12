# Alert API Documentation

## Alert Endpoint Configuration

### `send_alert()` Method

**Location:** `modules/gap_detection.py`

**Signature:**
```python
def send_alert(self, alert: Dict[str, Any], endpoint: Optional[str] = None) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `alert` | Dict | Yes | Alert object to send |
| `endpoint` | str | No | URL of API endpoint. If None, stores locally |

**Alert Object Structure:**
```json
{
  "alert_id": "string",
  "provider": "string",
  "url": "string",
  "gap": "string",
  "severity": "critical|high|medium|low",
  "timestamp": "ISO8601",
  "status": "detected",
  "action_required": true|false
}
```

### Usage Examples

**1. Send to custom endpoint:**
```python
detector = SafetyGapDetector()
detector.send_alert(alert, endpoint="https://your-api.com/alerts")
```

**2. Store locally (no endpoint):**
```python
detector = SafetyGapDetector()
detector.send_alert(alert)  # Stores in alert_history
```

**3. Retrieve alert history:**
```python
history = detector.get_alert_history(limit=100)
```

## Recommended Endpoint Formats

### Slack Webhook
```
https://hooks.slack.com/services/xxx/xxx/xxx
```

### Generic HTTP POST
```
https://api.example.com/alerts
```

### PagerDuty Event
```
https://events.pagerduty.com/v2/enqueue
```

## Severity Levels

| Level | Gap Count | Action Required |
|-------|-----------|----------------|
| critical | 8+ | Immediate |
| high | 5-7 | Urgent |
| medium | 3-4 | Soon |
| low | 1-2 | Scheduled |
