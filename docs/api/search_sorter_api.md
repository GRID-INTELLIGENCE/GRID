# GRID Search Sorter API Documentation

## Overview

The GRID Search Sorter provides advanced sorting capabilities for search results with integrated safety validation and relevance scoring. It's designed for MCP server contexts within the GRID framework.

## Components

### 1. CanvasSearchSorter (`src/application/canvas/search_sorter.py`)

Main sorting engine for Canvas search results with safety and relevance integration.

#### Key Methods

- `sort_by_relevance(results)` - Sort by relevance score (descending)
- `sort_by_recency(results)` - Sort by timestamp (newest first)
- `sort_by_safety_then_relevance(results)` - Safety-first sorting (clean → PII → unsafe)
- `sort_by_confidence_then_score(results)` - Multi-criteria: confidence then score
- `sort_by_path_complexity(results)` - Sort by path complexity (simpler first)
- `create_search_result(route, query, content)` - Create analyzed search result

#### Data Structures

```python
@dataclass
class CanvasSearchResult:
    id: str
    content: str
    route: Path
    score: float
    timestamp: datetime
    safety_verdict: str
    pii_detected: bool
    relevance_metrics: dict[str, float]
    metadata: dict[str, Any]
```

### 2. SearchSafetyGuard (`src/mycelium/search_safety.py`)

Safety validation and PII detection for search content.

#### Key Methods

- `validate_search_result(content, route)` - Comprehensive safety validation
- `_detect_pii_types(text)` - Detect PII types in content
- `stats` - Get validation statistics

#### Safety Verdicts

- `PASS` - Content is safe to process
- `WARN` - Content is safe but has issues (PII detected)
- `REJECT` - Content is unsafe and should not be processed

#### PII Types Detected

- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers
- IP addresses

## MCP Server Tools

### Tool: `sort_canvas_search_results`

Sorts Canvas search results by specified criteria.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "description": "Array of search results to sort",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "content": {"type": "string"},
          "route": {"type": "string"},
          "score": {"type": "number"},
          "timestamp": {"type": "string"},
          "safety_verdict": {"type": "string"},
          "pii_detected": {"type": "boolean"}
        }
      }
    },
    "sort_method": {
      "type": "string",
      "enum": ["relevance", "recency", "safety_first", "confidence", "complexity"],
      "default": "relevance",
      "description": "Sorting method to use"
    }
  },
  "required": ["results"]
}
```

**Example Usage:**
```python
results = [
    {
        "id": "src/safety.py",
        "content": "Safety validation code",
        "route": "src/mycelium/safety.py",
        "score": 0.85,
        "timestamp": "2026-03-12T10:00:00Z",
        "safety_verdict": "pass",
        "pii_detected": false
    }
]

sorted_results = sorter.sort_canvas_search_results(
    results=results,
    sort_method="safety_first"
)
```

### Tool: `create_canvas_search_result`

Creates a new search result with automatic safety and relevance analysis.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "route": {"type": "string", "description": "File route path"},
    "query": {"type": "string", "description": "Search query"},
    "content": {"type": "string", "description": "File content"},
    "timestamp": {"type": "string", "description": "ISO timestamp (optional)"}
  },
  "required": ["route", "query", "content"]
}
```

**Example Usage:**
```python
result = sorter.create_canvas_search_result(
    route="src/application/canvas/relevance.py",
    query="relevance scoring",
    content="Relevance scoring implementation with semantic similarity"
)
```

## Sorting Methods

### 1. Relevance Sorting
- **Criteria**: Final relevance score (descending), then confidence
- **Use Case**: Standard search result ranking
- **Safety**: Filters out unsafe results

### 2. Recency Sorting
- **Criteria**: Timestamp (newest first)
- **Use Case**: Time-sensitive searches
- **Safety**: Filters out unsafe results

### 3. Safety-First Sorting
- **Criteria**: Safety status (clean → PII → unsafe), then relevance
- **Use Case**: Privacy-sensitive applications
- **Safety**: Preserves all results but prioritizes safe ones

### 4. Confidence Sorting
- **Criteria**: Confidence score (descending), then relevance score
- **Use Case**: Quality-focused ranking
- **Safety**: Filters out unsafe results

### 5. Path Complexity Sorting
- **Criteria**: Path complexity (simpler first)
- **Use Case**: Simplicity-focused navigation
- **Safety**: Filters out unsafe results

## Relevance Scoring

The relevance engine calculates scores based on:

### Metrics
- **Semantic Similarity**: Text overlap between query and route
- **Path Complexity**: Depth and complexity of file path
- **Context Match**: Keyword matching in context
- **Usage Frequency**: Historical usage patterns
- **Integration Alignment**: System integration score

### Scoring Formula
```
final_score = (
    semantic_similarity * 0.4 +
    (1.0 - path_complexity) * 0.2 +
    usage_frequency * 0.2 +
    context_match * 0.1 +
    integration_alignment * 0.1
)
```

### Confidence Calculation
Confidence is based on:
- Consistency of metrics (lower variance = higher confidence)
- Average score across all metrics
- Historical accuracy

## Safety Validation

### Content Checks
1. **Type Validation**: Ensures content is a string
2. **Length Limits**: Enforces maximum content length (100KB)
3. **Empty Content**: Rejects empty or whitespace-only content
4. **Control Characters**: Removes dangerous control characters
5. **PII Detection**: Identifies potential personally identifiable information

### PII Detection Patterns
- **Email**: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- **Phone**: `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`
- **SSN**: `\b\d{3}-\d{2}-\d{4}\b`
- **Credit Card**: `\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b`
- **IP Address**: `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`

### Safety Philosophy
- **Non-punitive**: PII detection triggers warnings, not blocking
- **Local-only**: All PII detection happens locally, no data transmission
- **Descriptive patterns**: Uses noun-based descriptions per Trust Layer Rule 1.1

## Performance Considerations

### Optimization Features
- **Bounded PII Scanning**: Only first 5KB scanned for PII
- **Usage History Caching**: Tracks usage patterns for frequency scoring
- **Efficient Sorting**: Uses Python's built-in sorting algorithms
- **Safety First**: Unsafe results filtered early to reduce processing

### Limits
- Maximum content length: 100KB
- PII scan limit: 5KB
- Usage history: Unlimited (but can be pruned)
- Processing time: Tracked per validation

## Integration Examples

### Basic Usage
```python
from src.application.canvas.search_sorter import CanvasSearchSorter

sorter = CanvasSearchSorter()

# Create and sort results
result = sorter.create_search_result(
    route="src/mycelium/safety.py",
    query="safety validation",
    content="Safety validation implementation"
)

sorted_results = sorter.sort_by_relevance([result])
```

### Safety Integration
```python
from src.mycelium.search_safety import SearchSafetyGuard

guard = SearchSafetyGuard()
report = guard.validate_search_result(content)

if report.is_safe:
    # Process content
    pass
else:
    # Handle unsafe content
    pass
```

### MCP Server Integration
```python
# In MCP server tool handler
def handle_sort_search_results(arguments):
    sorter = CanvasSearchSorter()
    method = arguments.get("sort_method", "relevance")
    results = arguments["results"]
    
    if method == "relevance":
        return sorter.sort_by_relevance(results)
    elif method == "safety_first":
        return sorter.sort_by_safety_then_relevance(results)
    # ... other methods
```

## Testing

Run the test suite:
```bash
cd c:/Users/USER/CascadeProjects/GRID-main
python -m pytest tests/unit/test_search_sorter.py -v
```

Run the demo:
```bash
python examples/search_sorter_demo.py
```

## Limitations

- **Heuristic PII Detection**: Pattern-based detection is not foolproof
- **Local Processing**: All processing happens locally (by design)
- **Content Bounds**: Large content may be truncated for PII scanning
- **Semantic Limits**: Relevance scoring is based on text overlap, not true semantics

## Security Considerations

- **No Data Transmission**: All safety checks happen locally
- **PII Protection**: Detected PII triggers warnings, not storage
- **Input Validation**: All inputs are validated before processing
- **Memory Safety**: Bounded processing prevents resource exhaustion
