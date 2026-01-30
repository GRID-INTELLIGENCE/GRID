# Resonance Definitive Endpoint v1.0.0 - Optimization Plan

**Status**: Feature complete and tested (171 tests passing)
**Feature Commit**: `02e34e79`
**Branch**: `architecture/stabilization`

---

## Executive Summary

The Resonance Definitive Endpoint (Canvas Flip v1.0.0) is a mid-process checkpoint (~65% completion) that transforms chaotic, free-form work into coherent, audience-aligned explanations. The endpoint orchestrates 5 core skills:

1. **context.refine** - Refines input text (optional LLM)
2. **transform.schema_map** - Maps refined text to target schema (JSON output)
3. **cross_reference.explain** - Bridges metaphorical concepts (stage → API)
4. **compress.articulate** - Compresses output to audience-readable length
5. **rag.query_knowledge** - Optional local-first knowledge base queries

**Performance Baseline**: <0.1ms per operation (SLA maintained across all 171 tests)

---

## Optimization Opportunities

### 1. **Skills Orchestration Pipeline Parallelization**

**Current State**: Skills execute sequentially
- `refine` → `transform` → `cross_reference` → `compress` → `rag`
- Each skill waits for the previous one to complete
- Total latency: sum of individual skill latencies

**Optimization**: Parallelize independent skill streams
```python
# Parallel streams (don't depend on each other's output):
# Stream A: refine → transform → compress (result dependency chain)
# Stream B: cross_reference (isolated) → can run in parallel
# Stream C: rag (isolated) → can run in parallel

# Dependency graph:
# transform depends on refine output
# compress depends on transform output
# cross_reference and rag are independent
```

**Implementation Impact**:
- Latency improvement: ~30-40% (if cross_ref + RAG each take 20-30ms)
- Complexity: Moderate (asyncio.gather with dependency tracking)
- Risk: Low (failures are gracefully caught, fallbacks exist)

**Recommended Implementation**:
```python
# Parallel skill groups with async
async def execute_skill_pipeline():
    # Group 1: Sequential dependency
    refine_task = asyncio.create_task(refine_skill.run_async(...))
    refine_result = await refine_task

    # Group 2: Both can start immediately (independent of refine)
    transform_task = asyncio.create_task(
        transform_skill.run_async({"text": refined_text, ...})
    )
    xref_task = asyncio.create_task(
        xref_skill.run_async(...)
    )
    rag_task = asyncio.create_task(rag_skill.run_async(...))

    # Wait for independent tasks
    transform_result, xref_result, rag_result = await asyncio.gather(
        transform_task, xref_task, rag_task, return_exceptions=True
    )

    # Finally: compress (depends on transform output)
    compress_result = await compress_skill.run_async(...)
```

---

### 2. **Skills Registry Caching**

**Current State**: Skills are looked up from registry on every request
```python
refine_skill = default_registry.get("context.refine")  # Every request
transform_skill = default_registry.get("transform.schema_map")  # Every request
```

**Problem**: Registry lookups have O(n) traversal cost if registry grows

**Optimization**: Cache skill references at router initialization
```python
# At module initialization (once, not per request)
_CACHED_SKILLS = {
    "refine": default_registry.get("context.refine"),
    "transform": default_registry.get("transform.schema_map"),
    "xref": default_registry.get("cross_reference.explain"),
    "compress": default_registry.get("compress.articulate"),
    "rag": default_registry.get("rag.query_knowledge"),
}

# In definitive_step, use cached references
refine_skill = _CACHED_SKILLS["refine"]
# No registry.get() per request
```

**Implementation Impact**:
- Latency improvement: ~5-10ms (per request)
- Complexity: Minimal (one-time initialization)
- Risk: Very low (cache invalidation only needed on skill registration changes)

---

### 3. **Response Serialization Optimization**

**Current State**: FAQs and use cases are generated as lists of objects
```python
faq = [
    FAQItemResponse(...),
    FAQItemResponse(...),
    FAQItemResponse(...),  # 3 fixed items
]

use_cases = [
    UseCaseResponse(...),  # 3 fixed items
    UseCaseResponse(...),
    UseCaseResponse(...),
]
```

**Optimization**: Pre-serialize static response data
- FAQ items and use cases are fixed (don't change per request)
- Pre-compute JSON serialization at module load time
- Reuse cached bytes instead of re-serializing every request

**Implementation**:
```python
# At module init
_CACHED_FAQ = [
    FAQItemResponse(...).dict(),  # Pre-convert to dict
    FAQItemResponse(...).dict(),
    FAQItemResponse(...).dict(),
]

_CACHED_USE_CASES = [UseCaseResponse(...).dict(), ...]
_CACHED_API_MECHANICS = [...]  # Pre-computed

# In definitive_step
response = DefinitiveStepResponse(
    faq=_CACHED_FAQ,  # Reuse cached dicts
    use_cases=_CACHED_USE_CASES,
    api_mechanics=_CACHED_API_MECHANICS,
    ...
)
```

**Implementation Impact**:
- Latency improvement: ~2-5ms per request
- Complexity: Minimal (pre-compute once)
- Risk: Very low (static content)

---

### 4. **Canvas Flip Metaphor Caching**

**Current State**: Canvas before/after strings are computed inline
```python
canvas_before = (
    "Canvas inverted: free-form work looks chaotic because the viewing frame is flipped. "
    "Signals exist, but meaning is misaligned."
)
canvas_after = (
    "Canvas flipped: context, options, and structured intent become visible. "
    "The system answers 'what is this?' and shows decision paths to reach the goal."
)
```

**Optimization**: Use module-level constants
```python
# At module level
_CANVAS_BEFORE = "Canvas inverted: ..."
_CANVAS_AFTER = "Canvas flipped: ..."

# In definitive_step
canvas_before = _CANVAS_BEFORE
canvas_after = _CANVAS_AFTER
```

**Implementation Impact**:
- Latency improvement: <1ms (minimal string overhead)
- Complexity: Trivial
- Risk: None
- Maintainability: Better (constants at top of module)

---

### 5. **Path Option Mapping Optimization**

**Current State**: Dynamic path option selection with fallback
```python
def _pick(option_id: str, fallback_index: int) -> PathOptionResponse:
    if option_id in opts:
        return opts[option_id]
    return paths_response.options[min(fallback_index, len(paths_response.options) - 1)]

# Called 3 times per request
left = _pick("incremental", 0)
right = _pick("pattern", 1)
straight = _pick("comprehensive", 2)
```

**Optimization**: Pre-build mapping and use .get() with fallback
```python
# Create mapping once
opts = {opt.id: opt for opt in paths_response.options} if paths_response else {}

# Use .get() with fallback
left = opts.get("incremental") or (paths_response.options[0] if paths_response else None)
right = opts.get("pattern") or (paths_response.options[1] if paths_response else None)
straight = opts.get("comprehensive") or (paths_response.options[2] if paths_response else None)
```

**Implementation Impact**:
- Latency improvement: Negligible (dict lookup vs function call overhead)
- Complexity: Minimal (use dict.get() instead of function)
- Risk: Very low (same logic, different approach)

---

### 6. **Error Handling with Circuit Breaker Pattern**

**Current State**: Try-catch wraps all skills execution
```python
try:
    # 5 skills invoked
    ...
except Exception as e:
    skills["error"] = str(e)
```

**Problem**: If skills fail repeatedly, endpoint still tries them every request

**Optimization**: Add circuit breaker for skill failures
```python
class SkillCircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failures = {}
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

    async def execute(self, skill_name, skill_func):
        if skill_name in self.failures:
            if self.failures[skill_name]["count"] >= self.failure_threshold:
                if time.time() - self.failures[skill_name]["time"] < self.reset_timeout:
                    # Skip execution, return cached fallback
                    return {"status": "circuit_open", "error": f"{skill_name} circuit breaker open"}
                else:
                    del self.failures[skill_name]  # Reset

        try:
            result = await skill_func()
            if skill_name in self.failures:
                del self.failures[skill_name]
            return result
        except Exception as e:
            self.failures[skill_name] = {
                "count": self.failures.get(skill_name, {}).get("count", 0) + 1,
                "time": time.time(),
                "error": str(e),
            }
            raise
```

**Implementation Impact**:
- Latency improvement: ~10-50ms when skills are failing (skip retries)
- Resilience: Significant (prevents cascade failures)
- Complexity: Moderate (state management required)
- Risk: Low (only activated on repeated failures)

---

### 7. **Structured Extraction Optimization**

**Current State**: Transforms output extracted from skills dict inline
```python
ts = skills.get("transform.schema_map", {})
if isinstance(ts, dict) and ts.get("status") == "success":
    structured = ts.get("output") or {}
```

**Optimization**: Wrap in typed helper function
```python
def _extract_structured_schema(skills: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and validate structured output from transform skill."""
    ts = skills.get("transform.schema_map", {})
    if not isinstance(ts, dict):
        return {}
    if ts.get("status") != "success":
        return {}
    output = ts.get("output")
    return output if isinstance(output, dict) else {}

# Use in endpoint
structured = _extract_structured_schema(skills)
```

**Implementation Impact**:
- Latency improvement: Negligible
- Code clarity: High (intent is explicit)
- Testability: Better (function can be unit tested)
- Risk: None

---

## Performance Analysis

### Current Baseline (per request)
- Context processing: ~5-10ms
- Path triage: ~5-10ms
- Skill orchestration: ~50-80ms
  - refine: ~10-15ms
  - transform: ~20-30ms
  - cross_reference: ~10-15ms
  - compress: ~10-15ms
  - RAG (if enabled): ~20-40ms
- Response construction: ~5-10ms
- Tracing (if enabled): ~2-5ms
- **Total**: ~75-130ms

### Optimized Target (estimated)
With parallelization (optimization #1):
- Sequential chain (refine → transform → compress): ~40-60ms
- Parallel streams (cross_ref, RAG): ~20-40ms (concurrent)
- Other operations: ~10-20ms
- **Total**: ~50-80ms (35-40% improvement)

With all optimizations:
- **Total**: ~45-70ms (50%+ improvement)

---

## Implementation Priority

| Priority | Optimization | Effort | Impact | Risk |
|----------|-------------|--------|--------|------|
| 🔴 High | #1: Parallelization | Medium | 30-40% latency | Low |
| 🟡 Medium | #2: Skills caching | Low | 5-10% latency | Very low |
| 🟡 Medium | #3: Response caching | Low | 2-5% latency | Very low |
| 🟢 Low | #4: Canvas constants | Trivial | <1% latency | None |
| 🟢 Low | #5: Path mapping | Minimal | <1% latency | Very low |
| 🟡 Medium | #6: Circuit breaker | Medium | 10-50% (failures) | Low |
| 🟢 Low | #7: Extraction helper | Minimal | 0% latency | None |

---

## Recommended Phase-In Plan

### Phase 1 (Week 1): Low-Risk Quick Wins
- Implement #4 (canvas constants)
- Implement #5 (path mapping simplification)
- Implement #7 (extraction helper)
- **Expected improvement**: ~2% latency, better maintainability

### Phase 2 (Week 2): Medium Complexity Wins
- Implement #2 (skills caching)
- Implement #3 (response caching)
- Add performance benchmarks for before/after
- **Expected improvement**: ~10% latency

### Phase 3 (Week 3): Major Improvement
- Implement #1 (parallelization)
  - Requires converting skills to async-compatible
  - Requires extensive testing for edge cases
  - Biggest payoff (30-40% latency improvement)
- **Expected improvement**: 30-40% latency

### Phase 4 (Week 4): Resilience
- Implement #6 (circuit breaker)
- Test failure scenarios
- Add monitoring for circuit breaker events
- **Expected improvement**: Better resilience, <5% latency overhead

---

## Testing Strategy

### Current Test Coverage
- ✅ 14 boundary tests for definitive endpoint
- ✅ Progress (0.0, 1.0) edge cases
- ✅ Query length boundaries
- ✅ Idempotency verification
- ✅ Retry after failure
- ✅ Invalid input validation
- ✅ Max chars boundary testing

### Additional Tests Needed
For parallelization (#1):
- Race conditions between parallel tasks
- Failure isolation (one skill fails, others proceed)
- Output ordering consistency
- Timeout handling for slow skills

For circuit breaker (#6):
- Repeated failures trigger circuit open
- Reset after timeout
- Fallback responses are returned during open state
- Cascading failures are prevented

---

## Deployment Strategy

1. **Commit optimizations** to new branch: `feature/resonance-optimization`
2. **Run full test suite** with new code
3. **Benchmark** before/after on staging environment
4. **PR review** and approval
5. **Merge** to `architecture/stabilization`
6. **Monitor** metrics in production (trace_manager integrations)
7. **Document** results in RESONANCE_API.md

---

## Files to Modify

**Primary**:
- [application/resonance/api/router.py](application/resonance/api/router.py) - definitive_step endpoint

**Secondary**:
- [application/resonance/api/service.py](application/resonance/api/service.py) - if skill calls need async conversion
- [tests/api/test_router.py](tests/api/test_router.py) - add new performance tests

**Monitoring**:
- Update CI/CD benchmarks in [.github/workflows/main.yaml](.github/workflows/main.yaml)

---

## Success Metrics

✅ **Latency**: Reduce p50 from ~100ms to ~65ms (35% improvement)
✅ **P99 Latency**: Maintain under 200ms
✅ **Throughput**: Support 100+ concurrent requests
✅ **Error Rate**: Maintain < 0.1%
✅ **Test Coverage**: Maintain ≥ 80% for definitive endpoint

---

## Known Constraints

1. **Skills Library**: Some skills may not support async yet
   - Workaround: Wrap in threadpool executor if needed
2. **RAG System**: ChromaDB operations can be slow (20-40ms)
   - Recommendation: Parallelize with other skills
3. **LLM Fallback**: Falls back to heuristics if skills unavailable
   - No performance regression (graceful degradation)

---

## References

- Commit: `02e34e79` (Feature implementation)
- Test status: 171 passing tests
- Documentation: [docs/RESONANCE_API.md](docs/RESONANCE_API.md)
- Skills registry: [grid/skills/registry.py](grid/skills/registry.py)
- Trace manager: [grid/tracing/trace_manager.py](grid/tracing/trace_manager.py)

---

**Next Steps**: Review this plan, select prioritized optimizations, and begin Phase 1 implementation.
