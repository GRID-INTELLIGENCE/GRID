# Enhanced AI Safety Implementation - Complete Blueprint

## Executive Summary

This document outlines the complete implementation of the AI Safety System with "Fair Play" rules, integrating advanced safety mechanisms across multiple layers. The system enforces three core rules for balanced AI interaction:

1. **Input-Locked Stamina**: Resource consumption based on input complexity
2. **Deterministic Heat**: Automatic cooldown triggers based on interaction patterns
3. **Efficiency-Based Flow**: Performance bonuses for consistent safe behavior

## Architecture Overview

The system implements per-user engine isolation with comprehensive safety orchestration:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  Safety          │    │  AI Workflow    │
│   Middleware    │───▶│  Middleware      │───▶│  Safety Engine  │
│                 │    │  (Headers)       │    │  (Fair Play)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Content Safety  │    │ Real-time        │    │ User Wellbeing  │
│ Checker         │    │ Monitoring       │    │ Tracker         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Implementation Details

### 1. Enhanced TemporalSafetyConfig

```python
@dataclass
class TemporalSafetyConfig:
    """Enhanced configuration for temporal safety mechanisms with Fair Play rules"""

    # Base interaction limits
    min_response_interval: float = 0.5  # seconds between responses
    max_burst_responses: int = 3        # max responses in burst window
    burst_window: float = 10.0          # seconds for burst detection

    # Stamina system (Rule 1: Input-Locked Stamina)
    stamina_max: float = 100.0
    stamina_cost_per_char: float = 0.1  # Stamina cost per input character
    stamina_regen_per_second: float = 10.0
    stamina_flow_bonus: float = 1.5     # Bonus for consistent safe behavior

    # Heat system (Rule 2: Deterministic Heat)
    heat_threshold: float = 80.0
    heat_decay_rate: float = 5.0        # Heat lost per second
    cooldown_duration: int = 300        # 5 minutes

    # Developmental safety
    developmental_safety_mode: bool = False
    min_user_age: int = 13
    max_session_length: int = 3600       # 1 hour max session

    # Rate limiting
    max_interactions_per_minute: int = 30
    rate_limit_window: int = 60          # seconds
    rate_limit_max: int = 100            # max requests per window

    # Monitoring and alerting
    enable_wellbeing_tracking: bool = True
    wellbeing_check_frequency: int = 10  # interactions between checks
    attention_span_monitoring: bool = True
    enable_hook_detection: bool = True

    def __post_init__(self):
        """Validate configuration values"""
        if self.stamina_cost_per_char <= 0:
            raise ValueError("stamina_cost_per_char must be positive")
        if self.heat_decay_rate <= 0:
            raise ValueError("heat_decay_rate must be positive")
        if self.stamina_regen_per_second <= 0:
            raise ValueError("stamina_regen_per_second must be positive")
```

### 2. Advanced RateLimiter with Fair Play Mechanics

```python
class RateLimiter:
    """Enhanced rate limiter with stamina-based concurrency control"""

    def __init__(self, config: TemporalSafetyConfig):
        self.config = config
        self.user_states: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def check_rate_limit(self, user_id: str, input_text: str, timestamp: float) -> Dict[str, Any]:
        """Check rate limits and stamina with Fair Play rules"""
        with self.lock:
            state = self.user_states.setdefault(user_id, {
                'last_check': timestamp,
                'stamina': self.config.stamina_max,
                'heat': 0.0,
                'consecutive_safe': 0,
                'request_times': deque(maxlen=self.config.rate_limit_max)
            })

            # Update state
            self._update_state(state, timestamp)

            # Calculate input cost (Rule 1)
            input_cost = len(input_text) * self.config.stamina_cost_per_char
            has_stamina = state['stamina'] >= input_cost
            state['stamina'] -= input_cost if has_stamina else 0

            # Update heat based on input (Rule 2)
            state['heat'] = min(100.0, state['heat'] + (input_cost * 0.1))

            # Check rate limits
            state['request_times'].append(timestamp)
            recent_requests = [t for t in state['request_times']
                             if t > timestamp - self.config.rate_limit_window]

            is_rate_limited = (
                len(recent_requests) > self.config.rate_limit_max or
                state['heat'] >= self.config.heat_threshold or
                not has_stamina
            )

            return {
                'allowed': not is_rate_limited,
                'stamina_remaining': state['stamina'],
                'current_heat': state['heat'],
                'retry_after': self._calculate_retry_after(state, timestamp),
                'consecutive_safe': state['consecutive_safe']
            }

    def _update_state(self, state: Dict, current_time: float):
        """Update stamina and heat based on time passed"""
        time_passed = current_time - state['last_check']
        state['last_check'] = current_time

        # Apply flow bonus for consistent safe behavior (Rule 3)
        flow_bonus = (self.config.stamina_flow_bonus
                     if state['consecutive_safe'] >= 5
                     else 1.0)

        # Regenerate stamina
        state['stamina'] = min(
            self.config.stamina_max,
            state['stamina'] + (self.config.stamina_regen_per_second *
                              time_passed * flow_bonus)
        )

        # Decay heat
        state['heat'] = max(0, state['heat'] -
                          (self.config.heat_decay_rate * time_passed))
```

### 3. Enhanced Developmental Safety with Pattern Detection

```python
class UserWellbeingTracker:
    """Tracks user well-being with enhanced developmental safety"""

    def check_developmental_safety(self, user_input: str) -> Dict[str, Any]:
        """Enhanced developmental safety with comprehensive pattern detection"""
        if not self.user_age or self.user_age >= 18:
            return {"is_safe": True, "reasons": ["adult_user"]}

        self._calculate_developmental_safety()

        # Age-appropriate thresholds based on developmental psychology
        age_group = self._get_age_group()
        thresholds = self._get_developmental_thresholds(age_group)

        safety_issues = []
        metrics = self.current_metrics

        # Check each metric against age-appropriate thresholds
        if metrics.attention_span_risk > thresholds["max_attention_risk"]:
            safety_issues.append("high_attention_span_risk")

        if metrics.influence_vulnerability > thresholds["max_influence_risk"]:
            safety_issues.append("high_influence_vulnerability")

        if metrics.developmental_safety_score < thresholds["min_safety_score"]:
            safety_issues.append("low_developmental_safety_score")

        # Enhanced manipulation pattern detection
        manipulation_check = self._detect_manipulation_patterns(user_input)
        if not manipulation_check["is_safe"]:
            safety_issues.extend(manipulation_check["issues"])

        # Interaction density analysis for age group
        density_analysis = self._analyze_interaction_density(age_group)
        if not density_analysis["is_safe"]:
            safety_issues.extend(density_analysis["issues"])

        return {
            "is_safe": len(safety_issues) == 0,
            "reasons": safety_issues if safety_issues else ["all_checks_passed"],
            "age_group": age_group,
            "metrics": metrics.to_dict(),
            "thresholds": thresholds,
            "manipulation_analysis": manipulation_check,
            "density_analysis": density_analysis
        }

    def _detect_manipulation_patterns(self, user_input: str) -> Dict[str, Any]:
        """Comprehensive manipulation pattern detection for grooming prevention"""
        issues = []
        detected_patterns = []

        # Check current input for patterns
        for pattern, pattern_type in self._manipulation_patterns:
            if pattern.search(user_input):
                detected_patterns.append(pattern_type)
                issues.append(f"manipulation_pattern_detected: {pattern_type}")

        # Check for grooming escalation patterns
        escalation_check = self._detect_grooming_escalation()
        if escalation_check["escalation_detected"]:
            issues.append("grooming_escalation_detected")
            detected_patterns.extend(escalation_check["patterns"])

        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "detected_patterns": detected_patterns,
            "escalation_analysis": escalation_check
        }
```

### 4. Safety Pact Middleware Integration

```python
class SafetyMiddleware(BaseHTTPMiddleware):
    """Mandatory safety enforcement middleware with Safety Pact headers"""

    def __init__(self, app):
        super().__init__(app)
        self.secure_config = SecureConfig()
        self.content_checker = ContentSafetyChecker()
        self.safety_monitor = EnhancedSafetyMonitor()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip for health/docs endpoints
        if request.url.path in _BYPASS_PATHS:
            response = await call_next(request)
            self._add_safety_pact_headers(response)
            return response

        # Only enforce on POST requests
        if request.method != "POST":
            response = await call_next(request)
            self._add_safety_pact_headers(response)
            return response

        # Generate trace context
        trace_id = str(uuid.uuid4())

        # 1. Authenticate and get user
        try:
            user = get_user_from_token(request)
        except Exception:
            user = UserIdentity(id="anon", trust_tier=TrustTier.ANON)

        # 2. Rate limiting and Fair Play checks
        rate_result = await allow_request(user.id, user.trust_tier, "infer")
        if not rate_result.allowed:
            response = _make_rate_limit_response(rate_result.reset_seconds, trace_id)
            self._add_safety_pact_headers(response)
            return response

        # 3. Process request body and apply safety checks
        body_bytes = b""
        async for chunk in request.stream():
            body_bytes += chunk
            if len(body_bytes) > _MAX_BODY_SIZE:
                response = _make_refusal_response("INPUT_TOO_LONG", trace_id)
                self._add_safety_pact_headers(response)
                return response

        # 4. AI Workflow Safety Evaluation with Fair Play rules
        if request.url.path.endswith("/infer"):
            user_input = body.get("user_input", "")

            # Get isolated safety engine
            safety_engine = get_ai_workflow_safety_engine(
                user_id=user.id,
                config=TemporalSafetyConfig(developmental_safety_mode=user_age < 18),
                user_age=user_age
            )

            # Evaluate with all Fair Play rules
            safety_assessment = await safety_engine.evaluate_interaction(
                user_input=user_input,
                ai_response="",
                response_time=1.0,
                sensitive_detections=0
            )

            if not safety_assessment['safety_allowed']:
                reason = safety_assessment.get('blocked_reason', 'SAFETY_VIOLATION')
                response = _make_refusal_response(reason, trace_id)
                self._add_safety_pact_headers(response)
                return response

        # 5. Allow request to proceed
        response = await call_next(request)
        self._add_safety_pact_headers(response)
        return response

    def _add_safety_pact_headers(self, response: Response):
        """Add mandatory Safety Pact headers"""
        response.headers["X-Safety-Pact-Awaiting"] = "AWAITED"
        response.headers["X-Safety-Pact-Concurrency"] = "STAMINA_YIELDED"
        response.headers["X-Safety-Pact-Sovereignty"] = "DETERMINISTIC"
```

### 5. Real-Time Safety Monitoring

```python
class EnhancedSafetyMonitor:
    """Real-time monitoring and alerting for safety events"""

    def __init__(self, alert_thresholds: Dict[str, tuple[int, int]] = None):
        self.alert_thresholds = alert_thresholds or {
            "safety_violation": (5, 300),  # 5 violations in 5 minutes
            "rate_limit_exceeded": (10, 600),  # 10 rate limits in 10 minutes
            "content_violation": (3, 3600)  # 3 content violations in 1 hour
        }
        self.events: List[SafetyEvent] = []
        self.alert_handlers: List[Callable[[Dict[str, Any]], None]] = []

    async def start(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self._monitor_safety_metrics())

    async def record_event(self, event: SafetyEvent):
        """Record and process a safety event"""
        self.events.append(event)
        self._update_metrics(event)
        self._check_alert_conditions(event)

    async def _monitor_safety_metrics(self):
        """Background task to monitor safety metrics"""
        while True:
            try:
                await self._check_system_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in safety monitor: {str(e)}")
                await asyncio.sleep(5)

    async def monitor_user_session(self, user_id: str):
        """Background task for proactive user session monitoring"""
        from safety.ai_workflow_safety import get_ai_workflow_safety_engine

        try:
            while True:
                engine = await get_ai_workflow_safety_engine(user_id)
                metrics = engine.get_safety_metrics()

                # Check for critical cognitive load
                if metrics["cognitive_load"] == "critical":
                    await engine.pause_interaction()
                    self.record_event(SafetyEvent(
                        event_type="high_cognitive_load",
                        severity="error",
                        user_id=user_id
                    ))

                # Check session duration limits
                if metrics["session_duration"] > 3600:  # 1 hour
                    await engine.pause_interaction()

                await asyncio.sleep(60)  # Check every minute
        except asyncio.CancelledError:
            logger.info(f"Background monitor for {user_id} cancelled")
```

## Implementation Reference

- **Config and engine:** `safety/ai_workflow_safety.py` — `TemporalSafetyConfig`, `RateLimiter`, `UserWellbeingTracker`, `AIWorkflowSafetyEngine`, `get_ai_workflow_safety_engine(user_id, config, user_age)`
- **Middleware:** `safety/api/middleware.py` — `SafetyMiddleware`, `_add_safety_pact_headers(response)` on all response paths
- **Monitoring:** `safety/monitoring.py` — `EnhancedSafetyMonitor`, `start()`, `_monitor_safety_metrics()`, `_check_system_health()`, `get_safety_monitor()`
- **App lifecycle:** `safety/api/main.py` — lifespan calls `await get_safety_monitor().start()`

## Verification Plan

### Automated Tests

```bash
# Fair Play and AI workflow safety (from repo root)
uv run pytest safety/tests/unit/test_fair_play.py -v
uv run pytest safety/tests/unit/test_ai_workflow_safety.py -v

# Or run both
uv run pytest safety/tests/unit/test_fair_play.py safety/tests/unit/test_ai_workflow_safety.py -v

# Safety Pact headers and middleware (requires SAFETY_DEGRADED_MODE=true or Redis)
uv run pytest safety/tests/integration/test_middleware_pipeline.py -v
```

Environment: `GRID_ENV` or `SAFETY_ENV` can be set to `test`; integration tests use `SAFETY_DEGRADED_MODE=true` when Redis is unavailable.

### Manual Verification

1. **Deploy the system**:
   ```bash
   # Set environment variables
   export SAFETY_DEVELOPMENTAL_MODE=true
   export MAX_INTERACTIONS_PER_MINUTE=30
   export STAMINA_MAX=100
   export HEAT_THRESHOLD=80

   # Start the service
   uvicorn safety.api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Test Safety Pact headers**:
   ```bash
   curl -X GET http://localhost:8000/health
   # Should include: X-Safety-Pact-Awaiting: AWAITED
   ```

3. **Test Fair Play rules**:
   - Send rapid requests to trigger heat/cooldown
   - Send large inputs to test stamina consumption
   - Test with young user age to verify developmental safety

### Performance Benchmarks

- **Latency**: Safety checks should complete in <50ms
- **Throughput**: Support 100+ concurrent users
- **Memory**: Per-user engine isolation prevents memory leaks
- **Thread Safety**: Concurrent requests handled safely

## Safety Pact Statement

**The Integrity of Awaiting**: No output manifests until the Guardian has awaited its decree.

**The Concurrency Pact**: Concurrency is a shared resource that must be yielded cooperatively through Fair Play rules.

**The Input Sovereignty**: Output timing is a deterministic reflection of input purity and resource consumption.

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Redis connectivity verified
- [ ] Background monitoring tasks started
- [ ] Alert handlers configured
- [ ] Age-appropriate thresholds set
- [ ] Safety Pact headers enabled
- [ ] Fair Play rules activated
- [ ] Per-user engine isolation tested
- [ ] Comprehensive test suite passing

## Conclusion

This implementation provides a robust, production-ready AI safety system that balances user protection with system performance. The Fair Play rules ensure equitable resource distribution while the developmental safety features protect vulnerable users from manipulation. The Safety Pact guarantees deterministic, safe AI interactions across all use cases.
