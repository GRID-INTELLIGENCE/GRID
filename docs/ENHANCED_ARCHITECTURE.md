# Grid System Architecture

## Machine-Readable Terminology

### Core Concepts

**IntegrationPipeline**: Event bus with history tracking, filtering, and replay capabilities for cross-component communication

**RetryPolicy**: Exponential backoff strategy for handling transient failures with configurable max attempts and initial delay

**HeuristicRouter**: Value-aware routing system that predicts optimal paths based on risk assessment and event priority

**NERService**: Named Entity Recognition service with RAG integration for extracting structured entities from unstructured text

**PipelineEvent**: Base dataclass for events with priority, event_id, source, and context fields

**DLQMessage**: Dead Letter Queue message containing failed events with retry count and error details

## Structured Component Definitions

### Kernel Layer

#### Message Broker
- **Purpose**: In-memory message routing with retry and DLQ support
- **Key Classes**: `InMemoryBroker`, `RetryPolicy`, `HeuristicRouter`
- **Retry Mechanism**: Exponential backoff with configurable multiplier
- **DLQ Strategy**: Move to dead letter queue after exhausting max retries

#### Integration Pipeline
- **Purpose**: Event orchestration with validation and history
- **Features**: Priority-based dispatch, event replay, layer filtering
- **Validation**: Middleware-based quality checks before dispatch
- **History**: Circular buffer with configurable max size (default: 1000)

### Services Layer

#### NER Service
- **Purpose**: Extract entities and relationships from text
- **Capabilities**: OpenAI integration, RAG context, confidence filtering
- **Fallback**: Deterministic pattern-based extraction when API unavailable
- **Output**: Tuple of (entities, relationships) with confidence scores

#### Pattern Engine
- **Purpose**: Analyze entity patterns using concept-based framework
- **Integration**: Works with NER output for pattern detection
- **Edge Cases**: Handles empty lists and missing attributes gracefully

### Database Layer

#### Models
- **RetryRecord**: Tracks retry attempts with unique constraint on (target_type, target_id)
- **Entity**: Stores extracted entities with confidence in data field
- **EntityRelationship**: Maps relationships between entities
- **Event**: Base event record with type, source, and raw_text

#### Migrations
- **Strategy**: Batch mode for SQLite ALTER TABLE operations
- **Constraint**: Use `batch_alter_table` for adding unique constraints
- **Compatibility**: Supports both SQLite and PostgreSQL

## Validation Checklist

### Required Components
- ✅ Event bus with retry logic
- ✅ NER service with fallback
- ✅ Database migrations with SQLite support
- ✅ Pattern recognition engine
- ✅ Dead letter queue handling

### Quality Standards
- ✅ Type hints on all public methods
- ✅ Docstrings with Args/Returns sections
- ✅ Test coverage > 70% for core services
- ✅ Error handling with graceful degradation
- ✅ Logging for debugging and monitoring

## Integration Patterns

### Event Flow
```
User Action → Pipeline.publish_sync() → Heuristic Priority Upgrade →
Validation Middleware → Broker.publish() → Retry Loop →
Handler Execution → Success/DLQ
```

### Retry Flow
```
Handler Fails → Check Retry Policy → Sleep(backoff_ms) →
Retry Handler → Increment Attempt → Exhausted? → Move to DLQ
```

### NER Flow
```
Text Input → RAG Context (optional) → OpenAI API →
JSON Parse → Confidence Filter → Fallback (if error) →
(Entities, Relationships)
```

## Configuration

### Retry Policy
- `max_retries`: Maximum retry attempts (default: 3)
- `initial_backoff_ms`: Initial delay in milliseconds (default: 100)
- `multiplier`: Backoff multiplier for exponential growth (default: 2.0)

### NER Service
- `confidence_threshold`: Minimum confidence for entity inclusion (default: 0.7)
- `enable_hidden_player_detection`: Enable AI-based hidden player analysis
- `use_rag`: Enable RAG context for entity extraction
- `rag_top_k`: Number of context documents to retrieve (default: 3)

### Integration Pipeline
- `max_history_size`: Maximum events in history buffer (default: 1000)
- `async_mode`: Enable asynchronous event processing (default: false)

## Best Practices

### Error Handling
1. Always provide fallback mechanisms for external API calls
2. Use try-except blocks with specific exception types
3. Log errors with context for debugging
4. Move failed operations to DLQ after retries

### Testing
1. Use fixtures with `yield` for proper cleanup
2. Patch settings at module level for consistency
3. Mock external dependencies (OpenAI, databases)
4. Test both success and failure paths

### Database Operations
1. Use batch mode for SQLite schema changes
2. Avoid redundant rollbacks in fixtures
3. Store metadata in JSON fields when schema is flexible
4. Use unique constraints to prevent duplicates

### Documentation
1. Define domain-specific terminology upfront
2. Use structured formats (JSON, YAML) for configuration
3. Include validation checklists for completeness
4. Provide integration flow diagrams
