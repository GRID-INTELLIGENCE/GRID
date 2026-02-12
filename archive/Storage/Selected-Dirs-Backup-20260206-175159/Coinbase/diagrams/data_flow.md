# GRID Agentic System - Data Flow Diagram

```mermaid
graph TD
    A[User Input] --> B[AgenticSystem]
    
    B --> C{Crypto Scope?}
    C -->|Yes| D[Initialize Crypto Handlers]
    C -->|No| E[Standard Handlers]
    
    D --> F[AgentExecutor]
    E --> F
    
    F --> G[RuntimeBehaviorTracer]
    G --> H[Start Trace]
    
    H --> I[RecoveryEngine]
    I --> J{Error?}
    J -->|Yes| K[ErrorClassifier]
    J -->|No| L[Execute Handler]
    
    K --> M{Recoverable?}
    M -->|Yes| N[Retry with Backoff]
    M -->|No| O[Record Failure]
    
    N --> I
    L --> P[ExecutionResult]
    P --> Q[End Trace]
    
    Q --> R{Success?}
    R -->|Yes| S[EventBus: case_completed]
    R -->|No| T[EventBus: case_executed]
    
    S --> U[SkillGenerator]
    T --> U
    
    U --> V{Outcome=success?}
    V -->|Yes| W[Generate Skill]
    V -->|No| X[Skip]
    
    W --> Y[LearningCoordinator]
    X --> Y
    
    Y --> Z[Update Skill Stats]
    Z --> AA[Rank Skills]
    
    AA --> AB[Performance Metrics]
    AB --> AC[VersionScorer]
    
    AC --> AD[Calculate Score]
    AD --> AE[Assign Tier]
    
    AE --> AF[Version History]
    AF --> AG[Validate Momentum]
    
    AG --> AH{Checkpoint?}
    AH -->|Yes| AI[Log Checkpoint]
    AH -->|No| AJ[Continue]
    
    AI --> AK[Decision: Stabilize or Compound]
    AK --> AL[Output Results]
    
    style A fill:#e1f5ff
    style B fill:#fff4e6
    style G fill:#e8f5e9
    style I fill:#fce4ec
    style U fill:#f3e5f5
    style Y fill:#e0f2f1
    style AC fill:#fff3e0
    style AL fill:#e8f5e9
```

## Data Flow Description

### 1. Input Phase
- User provides input to AgenticSystem
- System checks if crypto scope is enabled
- Initializes appropriate handlers based on scope

### 2. Execution Phase
- AgentExecutor starts task execution
- RuntimeBehaviorTracer begins tracking
- RecoveryEngine wraps execution with error handling
- ErrorClassifier determines error type and recovery strategy
- Transient errors trigger retry with exponential backoff
- Non-recoverable errors abort immediately

### 3. Event Phase
- EventBus publishes case_executed event
- EventBus publishes case_completed event
- SkillGenerator handles completion events
- Only successful cases generate skills

### 4. Learning Phase
- LearningCoordinator updates skill statistics
- Skills ranked by success rate and latency
- Performance metrics collected
- VersionScorer calculates weighted scores
- Tier assigned based on score thresholds

### 5. Momentum Phase
- Version history tracked
- Momentum validated (non-decreasing scores)
- Checkpoints logged every 10 samples
- Decision to stabilize or compound

### 6. Output Phase
- Results returned to user
- Performance metrics available
- Skills available for reuse
- Learning insights available
