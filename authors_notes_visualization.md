# Privacy Rate Limiting Visualization

## Step 1: Request Ingestion
```mermaid
graph TD
    A[User Request] --> B[Rate Limiter Gateway]
    B --> C[Extract user_id, IP, session_token]
    C --> D[Hash identifiers]
    D --> E[Timestamp with monotonic clock]
```

## Step 2: Token Bucket Evaluation
```mermaid
graph TD
    A[Check bucket state] --> B{tokens_available > 0?}
    B -->|Yes| C[ALLOW and decrement bucket]
    B -->|No| D{burst_capacity_remaining > 0?}
    D -->|Yes| E[ALLOW with WARNING]
    D -->|No| F[DENY with 429]
```

## Step 3: Pattern Recognition
```mermaid
graph LR
    A[Analyze request pattern] --> B[Frequency delta = current_rate / historical_avg]
    B --> C{delta > 2.0?}
    C -->|Yes| D[Escalate to Guardian]
    B --> E{delta < 0.5?}
    E -->|Yes| F[Potential slow-drip attack]
    A --> G[Update sliding window]
```

## Step 4: Adaptive Threshold Adjustment
```mermaid
pie title Adjustment Factors
    "Time-of-day" : 35
    "Day-of-week" : 20
    "Threat level" : 25
    "User tier" : 20
```

## Step 5: Feedback Loop
```mermaid
graph LR
    A[Successful blocks] --> B[Tighten thresholds]
    C[False positives] --> D[Loosen thresholds]
    E[Pattern drift] --> F[Retrain baseline]
    G[Audit log] --> H[Immutable append]
```

## Step 6: State Persistence
```mermaid
graph TB
    A[Redis sorted set] --> B[ZADD user:{hash}]
    A --> C[ZREMRANGEBYSCORE]
    A --> D[EXPIRE key]
    A --> E[Fail-closed mode]
```

## The Paradox Resolved
```mermaid
graph LR
    A[Block/Allow events] --> B[Generate signals]
    B --> C[Pattern recognition]
    C --> D[Adjust thresholds]
    D --> E[Change block/allow ratio]
    E --> A
```
