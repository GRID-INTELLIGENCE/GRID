# GRID Agentic System Rules

## Core Principles

1. **Synchronous Execution**: All operations must be synchronous (no async/await)
2. **Behavior Tracking**: Every execution must be traced with RuntimeBehaviorTracer
3. **Error Recovery**: All transient errors must be automatically retried with exponential backoff
4. **Skill Generation**: Successful cases must generate persistent skills automatically
5. **Event-Driven**: All components communicate via EventBus for loose coupling
6. **Learning**: All executions update LearningCoordinator for skill ranking

## Execution Rules

### Task Execution
- Every task must be registered with `AgentExecutor.register_handler()`
- Tasks must return `ExecutionResult` with success/failure status
- Duration must be tracked for performance metrics
- Decision points must be logged with rationale and confidence

### Error Handling
- Transient errors (timeout, rate limit) must trigger retry_with_backoff
- Permission errors must abort immediately
- Validation errors must abort immediately
- Dependency errors must trigger circuit_break
- Max retry attempts: 3 (configurable)

### Skill Generation
- Only successful cases (outcome == "success") generate skills
- Skills stored in `~/.grid/knowledge/` by default
- Each skill has: metadata.json and artifacts/overview.md
- Skills track usage_count and success_count for ranking

### Cognitive State
- Track cognitive load: LOW (autonomous), MEDIUM (standard), HIGH (scaffolded)
- Apply scaffolding when cognitive load is HIGH
- Update confidence based on interaction outcomes

## Version Scoring Rules

### Tier Assignment
- **Gold (3.5)**: Score >= 0.85
- **Silver (3.0)**: Score >= 0.70
- **Bronze (2.0)**: Score >= 0.50
- **Basic (1.0)**: Score < 0.50

### Score Components (weighted)
- Coherence accumulation: 20%
- Evolution count: 15%
- Pattern emergence rate: 10%
- Operation success rate: 15%
- Average confidence: 10%
- Skill retrieval score: 10%
- Resource efficiency: 10%
- Error recovery rate: 10%

## Momentum Rules

- Version scores must be non-decreasing
- Momentum validation: `scores[-1] >= scores[0]`
- Checkpoint every 10 execution samples
- Compounding value: skills with higher success rates rank higher

## Coinbase-Specific Rules

### Crypto Scope
- All operations must respect `--crypto` flag
- Crypto operations require explicit scope activation
- Non-crypto operations blocked when crypto scope disabled

### Analysis Workflow
1. Initialize AgenticSystem with crypto scope
2. Register handlers for: data_processing, analysis, reporting
3. Execute cases with behavior tracking
4. Generate skills from successful analyses
5. Update learning coordinator with outcomes
6. Provide performance metrics

## Data Flow Rules

1. **Input**: Sensory data → Intelligence Layer → RuntimeBehavior
2. **Processing**: AgentExecutor → RecoveryEngine → Handler
3. **Output**: Result → EventBus → SkillGenerator → LearningCoordinator
4. **Tracking**: Tracer records all decisions, timings, outcomes
5. **Learning**: Coordinator updates skill rankings based on success rates

## Testing Rules

- All tests must be synchronous
- Tests must use small delays (0.001s) for duration tracking
- Tests must verify event publishing
- Tests must check skill generation
- Tests must validate learning coordinator updates
