# GRID Agentic System - Architecture Flowchart

```mermaid
graph TD
    subgraph "User Layer"
        A[User] --> B[Coinbase CLI]
        B --> C[Main Entry Point]
    end
    
    subgraph "Orchestration Layer"
        C --> D[AgenticSystem]
        D --> E[EventBus]
        D --> F[AgentExecutor]
        D --> G[CognitiveEngine]
    end
    
    subgraph "Execution Layer"
        F --> H[RuntimeBehaviorTracer]
        F --> I[RecoveryEngine]
        H --> J[ExecutionBehavior]
        I --> K[ErrorClassifier]
    end
    
    subgraph "Learning Layer"
        E --> L[SkillGenerator]
        E --> M[LearningCoordinator]
        L --> N[Skill Store]
        M --> O[Skill Rankings]
    end
    
    subgraph "Analysis Layer"
        F --> P[CryptoSkillsRegistry]
        P --> Q[Data Processing Skills]
        P --> R[Analysis Skills]
        P --> S[Backtesting Skills]
        P --> T[Pattern Recognition Skills]
        P --> U[Risk Management Skills]
        P --> V[Reporting Skills]
    end
    
    subgraph "Scoring Layer"
        M --> W[VersionScorer]
        W --> X[VersionMetrics]
        W --> Y[Version History]
        W --> Z[Momentum Validation]
    end
    
    subgraph "Output Layer"
        D --> AA[Performance Metrics]
        D --> AB[Execution Results]
        D --> AC[Generated Skills]
        D --> AD[Learning Insights]
    end
    
    style A fill:#e1f5ff
    style D fill:#fff4e6
    style E fill:#e8f5e9
    style F fill:#fce4ec
    style G fill:#f3e5f5
    style L fill:#e0f2f1
    style M fill:#fff3e0
    style P fill:#e1f5ff
    style W fill:#fff4e6
    style AA fill:#e8f5e9
```

## Architecture Components

### User Layer
- **User**: Initiates requests
- **Coinbase CLI**: Command-line interface
- **Main Entry Point**: Entry point for all operations

### Orchestration Layer
- **AgenticSystem**: Main orchestrator
- **EventBus**: Decoupled communication
- **AgentExecutor**: Task execution
- **CognitiveEngine**: User state tracking

### Execution Layer
- **RuntimeBehaviorTracer**: Behavior tracking
- **RecoveryEngine**: Error recovery
- **ExecutionBehavior**: Trace data
- **ErrorClassifier**: Error categorization

### Learning Layer
- **SkillGenerator**: Skill creation
- **LearningCoordinator**: Skill ranking
- **Skill Store**: Persistent storage
- **Skill Rankings**: Skill performance data

### Analysis Layer
- **CryptoSkillsRegistry**: Skill registry
- **Data Processing Skills**: Data normalization, validation
- **Analysis Skills**: Price trends, volume analysis
- **Backtesting Skills**: Strategy backtesting
- **Pattern Recognition Skills**: Chart patterns
- **Risk Management Skills**: Risk assessment
- **Reporting Skills**: Report generation

### Scoring Layer
- **VersionScorer**: Score calculation
- **VersionMetrics**: Score components
- **Version History**: Progress tracking
- **Momentum Validation**: Trend validation

### Output Layer
- **Performance Metrics**: Execution statistics
- **Execution Results**: Task outcomes
- **Generated Skills**: Persistent knowledge
- **Learning Insights**: Performance data
