# GRID Models — Story-Based Testing Framework

## Overview

The `models/` directory contains dragon archetypes that represent different behavioral patterns in the GRID acceleration framework. Each dragon emerged from **observed test behavior**, not predefined mappings.

## The Dragons

### Initial Set (Predefined Stories)

| Dragon | Title | Story Focus |
|--------|-------|-------------|
| **CARAXES** | The Blood Wyrm | Edge case hunter—found boundaries before tests existed |
| **DROGON** | The Semantic Architect | Meaning analyzer—burns concepts, not symptoms |
| **VHAGAR** | The Temporal Accumulator | Momentum tracker—patience is power |

### Extended Set (Emerged from Tests)

| Dragon | Title | Emerged From |
|--------|-------|--------------|
| **BALERION** | The Black Dread | Observation: momentum was constant (0.5) regardless of complexity |
| **SYRAX** | The Golden | Observation: context created single-layer markers, not nested |

## Test Results

**Baseline:** 26 tests collected, 12 passed
**Story Tests:** 12 tests (8 individual + 4 integration), all passed
**Scenarios:** 9 embedded scenarios (3 per initial dragon)

### Emerged Patterns

From `models/data/behavior_report.json`:

```json
{
  "total_scenarios": 9,
  "dragons_tested": ["VHAGAR", "CARAXES", "DROGON"],
  "patterns": {
    "VHAGAR": "Consistent 0.5 momentum per scenario (3 steps each)",
    "DROGON": "Context creates markers (2/3 had ~prefix)",
    "CARAXES": "All 3 edge cases handled gracefully"
  }
}
```

## Architecture

```
models/
├── __init__.py              # Package exports
├── base.py                  # DragonModel base class
├── dragons.py               # Initial 3 dragons
├── dragons_extended.py      # Extended 2 dragons (from patterns)
└── data/
    ├── scenarios.json       # 9 embedded test scenarios
    └── behavior_report.json # Test behavior observations
```

## Usage

```python
from models import VHAGAR, DROGON, CARAXES, BALERION, SYRAX
from core.products import Product
from core.products.accelerator import AccelerationPipeline

# Run acceleration
product = Product("Beauty / Fashion", "LUEUR Extension", "16-40", "fiber")
pipeline = AccelerationPipeline()
trace = pipeline.run(product, context="TikTok + Instagram")

# Record observation
VHAGAR.record_observation("momentum_test", {
    "total_momentum": trace.total_momentum,
    "step_count": len(trace.steps),
})
```

## Key Insights

### 1. Category Transformation Pattern
- Input: `"A / B / C"` → Output: `"B ( C  D  E)"`
- First element preserved, rest parenthesized
- Slashes replaced with spaces, then parentheses added

### 2. Context Injection Pattern
- When context provided → creates `~context` annotation
- Without context → no annotations
- **Gap:** Only single-layer marking (SYRAX's opportunity)

### 3. Momentum Pattern
- Consistent 0.5 per product
- 3 steps per acceleration (compress, modify, adjust)
- **Gap:** No complexity scaling (BALERION's opportunity)

## Testing

```bash
# Run all model tests
pytest tests/models/ -v -s

# Run integration test with behavior collection
pytest tests/models/test_story_integration.py -v -s

# View behavior report
cat models/data/behavior_report.json
```

## Future Directions

Based on emerged patterns:

1. **Complexity-Aware Momentum** (BALERION)
   - Implement variable momentum based on input complexity
   - Scale: `momentum = base * complexity_factor`

2. **Multi-Layer Context** (SYRAX)
   - Nested context weaving instead of flat markers
   - Example: `["~Healthcare", "~B2B", "~Wellness::Professional"]`

3. **Additional Dragons**
   - Let more patterns emerge from extended testing
   - Generate new archetypes organically

## Philosophy

> "Don't predefine—run tests, observe, reason, discuss."

This framework follows organic discovery:
1. Create minimal structure
2. Run tests, collect behavior
3. Observe patterns
4. Generate new models based on gaps
5. Iterate

---

*Generated from test observations on 2025-12-05*
