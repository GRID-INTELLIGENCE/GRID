# Coinbase Analysis Workflow

## Overview
This workflow defines the end-to-end process for crypto-focused analysis using the GRID agentic system.

## Workflow Stages

### Stage 1: Initialization
```
1. Create AgenticSystem with crypto scope
2. Register handlers:
   - data_processing: Raw data ingestion and normalization
   - analysis: Pattern detection and insight generation
   - reporting: Result formatting and visualization
3. Configure skill store path: ~/.grid/knowledge/
4. Initialize cognitive engine for user state tracking
```

### Stage 2: Data Ingestion
```
1. Execute case: data_processing
   - Input: Raw crypto data (prices, volumes, transactions)
   - Process: Normalize, validate, clean
   - Output: Structured dataset
   - Track: Operation duration, data quality metrics
2. Record decision points:
   - Routing to data_processing handler
   - Confidence: 1.0 (deterministic)
   - Rationale: "Data preprocessing required"
```

### Stage 3: Analysis Execution
```
1. Execute case: analysis
   - Input: Structured dataset
   - Process: Pattern detection, anomaly detection, trend analysis
   - Output: Insights and predictions
   - Track: Processing time, confidence scores
2. Apply cognitive scaffolding if needed:
   - HIGH load: Provide detailed explanations
   - MEDIUM load: Standard analysis
   - LOW load: Autonomous mode with minimal guidance
3. Record decision points:
   - Analysis type selection
   - Confidence in predictions
   - Alternative analysis methods considered
```

### Stage 4: Report Generation
```
1. Execute case: reporting
   - Input: Analysis results
   - Process: Format for target audience
   - Output: Structured report
   - Track: Report generation time
2. Event publishing:
   - case_executed: Notification of completion
   - case_completed: Skill generation trigger
```

### Stage 5: Skill Generation
```
1. SkillGenerator.handle_case_completed():
   - Check outcome: success?
   - Create skill directory: ~/.grid/knowledge/{skill_id}
   - Generate metadata.json:
     * Title: Skill: {case_id}
     * Summary: Description of analysis
     * References: case_id, agent_role, task
     * Generated at: timestamp
   - Create artifacts/overview.md:
     * Execution details
     * Solution/approach
     * Results summary
2. Update LearningCoordinator:
   - Increment usage_count
   - Increment success_count on success
   - Update avg_latency_ms
```

### Stage 6: Learning & Ranking
```
1. LearningCoordinator.record_execution_outcome():
   - Track skill usage statistics
   - Calculate success_rate = success_count / usage_count
   - Update skill rankings
2. Get ranked skills:
   - Sort by: success_rate (primary), -avg_latency_ms (secondary)
   - Top skills recommended for future analyses
```

### Stage 7: Progress Checkpoint
```
1. Every 10 execution samples:
   - Log checkpoint: "🎓 Online Learning Checkpoint: processed {n} samples"
   - Validate momentum: scores[-1] >= scores[0]
   - Decision point: Stabilize or compound?
     - Stabilize: Save progress, set scale
     - Compound: Build on momentum with 10x value scaling
```

## Error Recovery Flow

```
1. Error occurs during execution
2. ErrorClassifier.classify():
   - TRANSIENT: retry_with_backoff (max 3 attempts)
   - PERMISSION: abort immediately
   - DEPENDENCY: circuit_break
   - VALIDATION: abort
   - UNKNOWN: retry_with_backoff
3. RecoveryEngine.execute_with_recovery():
   - Calculate backoff delay: base_delay * (2^(attempt-1))
   - Wait: delay seconds
   - Retry: Execute task again
4. If all retries exhausted:
   - Record FAILURE outcome
   - Generate diagnostics
   - Publish case_completed event (failure)
```

## Version Scoring Flow

```
1. Calculate version score:
   score = weighted_sum(metrics)
   metrics:
   - coherence_accumulation (20%)
   - evolution_count (15%)
   - pattern_emergence_rate (10%)
   - operation_success_rate (15%)
   - avg_confidence (10%)
   - skill_retrieval_score (10%)
   - resource_efficiency (10%)
   - error_recovery_rate (10%)

2. Determine version tier:
   - score >= 0.85: "3.5" (Gold coin)
   - score >= 0.70: "3.0"
   - score >= 0.50: "2.0"
   - score < 0.50: "1.0"

3. Record checkpoint:
   - Append to version_history
   - Validate momentum
   - Get latest version
```

## Event Flow

```
1. AgenticSystem.execute_case()
   ↓
2. AgentExecutor.execute_task()
   ↓
3. EventBus.publish("case_executed")
   ↓
4. EventBus.publish("case_completed")
   ↓
5. SkillGenerator.handle_case_completed()
   ↓
6. LearningCoordinator.record_execution_outcome()
```

## Cognitive State Flow

```
1. InteractionEvent created
   ↓
2. CognitiveEngine.track_interaction()
   ↓
3. Update cognitive load:
   - Error/fail keywords → HIGH
   - Success/complete keywords → LOW
   - Default → MEDIUM
   ↓
4. Adjust processing mode:
   - HIGH → scaffolded (detailed guidance)
   - LOW → autonomous (minimal guidance)
   - MEDIUM → standard
   ↓
5. Check scaffolding:
   - should_apply_scaffolding() → bool
```

## Continuous Improvement

```
1. Track performance metrics:
   - p50_latency_ms
   - p95_latency_ms
   - success_rate
   - avg_llm_calls
   - avg_tokens_used

2. Analyze patterns:
   - Which skills succeed most?
   - What error patterns emerge?
   - Where do bottlenecks occur?

3. Optimize:
   - Adjust retry strategies
   - Refine skill rankings
   - Update cognitive thresholds
   - Improve error classification
```

## Exit Criteria

Workflow completes when:
- All cases executed successfully
- Skills generated for successful cases
- Learning coordinator updated
- Performance metrics recorded
- Momentum validated
- Checkpoint logged (every 10 samples)
