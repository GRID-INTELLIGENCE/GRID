# Discussion Service

Current Events Discussion Service for Arena API - provides intelligent topic extraction and recursive reasoning capabilities.

## Features

- **Topic Extraction**: Extract key topics from text using wall-board metaphor
- **Recursive Reasoning**: Multi-depth discussion analysis with TracedDiscussionAgent
- **AI Safety**: Integrated safety checks for content moderation
- **Authentication**: JWT/API Key support
- **Monitoring**: Full metrics and logging

## Endpoints

### Health Check
```bash
GET /health
```

### Discuss Current Events
```bash
POST /discuss
{
  "text": "Your current event text here...",
  "max_depth": 3,
  "extract_topics": true,
  "use_llm_topics": false
}
```

**Response:**
```json
{
  "discussion_id": "disc_1234567890",
  "topics": {
    "wall_board": {
      "topics": [...],
      "total_topics": 5,
      "connections": 3
    }
  },
  "reasoning_trace": {...},
  "summary": "Identified 5 key topics...",
  "processing_time": 0.145,
  "timestamp": "2026-02-14T..."
}
```

### Extract Topics Only
```bash
POST /topics/extract
{
  "text": "Text to analyze...",
  "use_llm": false,
  "max_topics": 8
}
```

**Response:**
```json
{
  "topics": [
    {
      "topic": "api gateway",
      "pins": ["routing", "safety", "auth"],
      "connections": [...],
      "weight": 8
    }
  ],
  "total_topics": 5,
  "connections": 3,
  "metaphor": "Each topic is a note pinned to the wall...",
  "processing_time": 0.089
}
```

### List Discussions
```bash
GET /discussions
```

### Get Specific Discussion
```bash
GET /discussions/{discussion_id}
```

## Running the Service

```bash
# Standalone
cd arena_api/services/discussion_service
python main.py

# With API Gateway
# Gateway auto-registers on startup at localhost:8003
```

## Environment Variables

- `DISCUSSION_SERVICE_URL`: Service URL (default: http://localhost:8003)
- `DISCUSSION_SERVICE_PORT`: Service port (default: 8003)

## Architecture

```
Request → API Gateway → Discussion Service
                         ├─ Topic Extractor (wall-board metaphor)
                         ├─ TracedDiscussionAgent (recursive reasoning)
                         ├─ AI Safety Checks
                         └─ Response with topics + reasoning trace
```

## Testing

```bash
pytest arena_api/services/discussion_service/test_main.py -v
```

## Integration with Arena

The service integrates with Arena's architecture:
- **Service Discovery**: Auto-registered on gateway startup
- **Rate Limiting**: Enforced by API Gateway
- **Authentication**: JWT/API Key via AuthManager
- **AI Safety**: Content moderation via AISafetyManager
- **Monitoring**: Metrics tracked via MonitoringManager

## Wall-Board Metaphor

Topics are visualized as notes pinned to a wall:
- **Pins**: Key points/sub-topics (bullet points)
- **Threads**: Connections showing conversation flow
- **Weight**: Topic importance (1-10 scale)
