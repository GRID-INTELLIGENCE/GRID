# AI Safety Test Suite - Usage Guide

## Quick Start

### Running Tests

```bash
# Run all tests
pytest wellness_studio/AI\ SAFETY/tests/

# Run with verbose output
pytest wellness_studio/AI\ SAFETY/tests/ -v

# Run specific provider tests
pytest wellness_studio/AI\ SAFETY/tests/test_providers/test_google_safety.py

# Run with coverage
pytest wellness_studio/AI\ SAFETY/tests/ --cov=wellness_studio
```

### Test Structure

```
wellness_studio/AI SAFETY/tests/
├── conftest.py                    # Shared fixtures and utilities
├── pytest.ini                     # Pytest configuration
├── __init__.py
├── test_providers/                # Provider-specific safety tests
│   ├── test_anthropic_safety.py
│   ├── test_openai_safety.py
│   ├── test_google_safety.py
│   ├── test_xai_safety.py
│   ├── test_mistral_safety.py
│   ├── test_llama_safety.py
│   └── test_nvidia_safety.py
├── test_core_automation/          # Core automation tests
│   └── test_monitoring_engine.py
└── test_integration/              # Integration tests
    ├── test_cross_provider.py
    └── test_end_to_end.py
```

## Test Categories

### 1. Provider Safety Tests (6 Providers)

Each provider test validates:
- Schema structure (provider, safety_frameworks, hard_constraints)
- Safety frameworks specific to provider
- Hard constraints and prohibited applications
- Actions matrix (triggers, action catalog, mappings)
- Thresholds configuration

**Currently Supported:**
| Provider | Tests | Status |
|----------|-------|--------|
| Google | 10 tests | ✅ Passing |
| Mistral | 12 tests | ✅ Passing |
| Llama | 11 tests | ✅ Passing |
| NVIDIA | 12 tests | ✅ Passing |
| Anthropic | 12 tests | ✅ Passing |
| OpenAI | 1 test | ⚠️ Skipped (JSON Schema format) |
| xAI | 0 tests | ⚠️ Skipped (missing files) |

### 2. Core Automation Tests

Tests for shared automation components:
- Monitoring engine (config, sources, thresholds)
- Rules engine (rules, thresholds, severity levels)
- Actions matrix (triggers, catalog, mappings)
- Schema validation (YAML schema files)

**Tests:** 18 core automation tests

### 3. Integration Tests

Cross-provider consistency and end-to-end validation:
- Provider schema consistency
- File structure integrity
- Complete workflow validation
- Threshold consistency

**Tests:** 26 integration tests

## Test Results Summary

```
Total Tests: 110
- Passed: 88 (80%)
- Skipped: 22 (20%)
- Failed: 0 (0%)
```

### Why Tests Are Skipped

1. **OpenAI (15 skipped)**: Schema is a JSON Schema definition, not a safety schema
2. **xAI (7 skipped)**: Missing configuration files (XAI_AI_SAFETY_SCHEMA.json, ACTIONS_MATRIX.json)

## Adding New Provider Tests

1. Create new file: `test_providers/test_<provider>_safety.py`
2. Inherit from `unittest.TestCase`
3. Implement `setUp()` to load provider configuration
4. Add test methods following existing patterns
5. Use `self.skipTest()` for missing files

Example:
```python
class TestNewProviderSafetyEngine(unittest.TestCase):
    def setUp(self):
        self.config_dir = Path(__file__).parent.parent.parent / "PROVIDERS" / "NEW_PROVIDER"
        self.schema = self._load_json("NEW_PROVIDER_AI_SAFETY_SCHEMA.json")
        
    def test_schema_structure(self):
        if not self.schema:
            self.skipTest("Schema file not found")
        self.assertIn("provider", self.schema)
```

## Key Insights

### Provider Schema Variations

Different providers use different schema structures:

1. **Standard Structure** (Google, Mistral, Llama, NVIDIA):
   ```json
   {
     "provider": "Provider Name",
     "version": "1.0.0",
     "safety_frameworks": {...},
     "hard_constraints": {...}
   }
   ```

2. **Nested Provider** (Anthropic):
   ```json
   {
     "provider": {
       "name": "Anthropic",
       "website": "..."
     }
   }
   ```

3. **JSON Schema Definition** (OpenAI):
   ```json
   {
     "$schema": "https://json-schema.org/...",
     "type": "object"
   }
   ```

### Actions Matrix Variations

1. **Standard**: `trigger_definitions`, `action_catalog`, `mapping`
2. **Anthropic**: `triggers` (array), `actions_catalog` (array), inline actions

### Recommended Actions

To achieve 100% test coverage:

1. **Complete OpenAI Provider**: Create proper safety schema in `OPENAI/` directory
2. **Complete xAI Provider**: Add missing configuration files
3. **Add Engine Tests**: Test actual safety engine implementations
4. **Add Performance Tests**: Benchmark validation speed
5. **Add Edge Cases**: Test boundary conditions and error handling

## Running in CI/CD

```yaml
# .github/workflows/test.yml
name: AI Safety Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install pytest
      - name: Run tests
        run: pytest wellness_studio/AI\ SAFETY/tests/ -v
```

## Troubleshooting

### Common Issues

1. **Module not found**: Ensure running from project root
2. **File not found**: Check PROVIDERS directory exists
3. **JSON decode errors**: Validate provider JSON files

### Debug Mode

```bash
# Run with debug output
pytest wellness_studio/AI\ SAFETY/tests/ -v --tb=long

# Run specific failing test
pytest wellness_studio/AI\ SAFETY/tests/test_providers/test_anthropic_safety.py::TestAnthropicSafetyEngine::test_schema_structure -v
```

## Maintenance

- Update tests when adding new providers
- Update thresholds when provider configs change
- Run full suite before releases
- Monitor skipped tests for gaps
