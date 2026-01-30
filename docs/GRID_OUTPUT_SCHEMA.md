# GRID Output Schema Documentation

## Overview

This document specifies the canonical JSON schema for all `grid analyze` command output. Every GRID analysis result must conform to this schema for:
- **Consistency**: All CLI outputs have the same shape
- **Interoperability**: Downstream tools can reliably parse results
- **Validation**: Automated checking of output correctness
- **Benchmarking**: Metrics and timings are standardized

## Complete Schema

```json
{
  "version": "1.0",
  "type": "object",
  "required": [
    "entities",
    "relationships",
    "ner_relationships",
    "counts",
    "timings_ms",
    "profile"
  ],
  "properties": {
    "entities": {
      "description": "Array of detected named entities",
      "type": "array",
      "items": {
        "type": "object",
        "required": ["text", "type", "start_char", "end_char"],
        "properties": {
          "text": {
            "type": "string",
            "description": "Entity text as found in source"
          },
          "type": {
            "type": "string",
            "description": "Entity type (PERSON, ORG, PRODUCT, LOCATION, etc.)"
          },
          "start_char": {
            "type": "integer",
            "minimum": 0,
            "description": "Character offset where entity starts"
          },
          "end_char": {
            "type": "integer",
            "minimum": 0,
            "description": "Character offset where entity ends (exclusive)"
          }
        }
      }
    },
    "relationships": {
      "description": "Array of relationships with semantic polarity",
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "source",
          "target",
          "polarity_score",
          "polarity_label",
          "confidence",
          "explanation"
        ],
        "properties": {
          "source": {
            "type": "string",
            "description": "Source entity name"
          },
          "target": {
            "type": "string",
            "description": "Target entity name"
          },
          "polarity_score": {
            "type": "number",
            "minimum": -1.0,
            "maximum": 1.0,
            "description": "Polarity score: -1.0 (negative) to +1.0 (positive)"
          },
          "polarity_label": {
            "type": "string",
            "enum": ["positive", "negative", "neutral"],
            "description": "Human-readable polarity label"
          },
          "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Confidence level in relationship (0.0 to 1.0)"
          },
          "explanation": {
            "type": "string",
            "description": "Natural language explanation of the relationship"
          }
        }
      }
    },
    "ner_relationships": {
      "description": "Array of typed relationships from NER module",
      "type": "array",
      "items": {
        "type": "object",
        "required": ["source", "target", "type", "score"],
        "properties": {
          "source": {
            "type": "string",
            "description": "Source entity name"
          },
          "target": {
            "type": "string",
            "description": "Target entity name"
          },
          "type": {
            "type": "string",
            "description": "Relationship type (WORKS_WITH, OWNS, LEADS, MENTIONS, etc.)"
          },
          "score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Confidence score for relationship type classification"
          }
        }
      }
    },
    "counts": {
      "description": "Summary counts of results",
      "type": "object",
      "required": ["entities", "relationships", "ner_relationships"],
      "properties": {
        "entities": {
          "type": "integer",
          "minimum": 0,
          "description": "Total number of entities detected"
        },
        "relationships": {
          "type": "integer",
          "minimum": 0,
          "description": "Total number of relationships detected"
        },
        "ner_relationships": {
          "type": "integer",
          "minimum": 0,
          "description": "Total number of NER relationships detected"
        }
      }
    },
    "timings_ms": {
      "description": "Performance metrics in milliseconds",
      "type": "object",
      "required": ["init", "ner", "relationships", "total"],
      "properties": {
        "init": {
          "type": "number",
          "minimum": 0.0,
          "description": "Time to initialize models and load (ms)"
        },
        "ner": {
          "type": "number",
          "minimum": 0.0,
          "description": "Time for NER stage (ms)"
        },
        "relationships": {
          "type": "number",
          "minimum": 0.0,
          "description": "Time for relationship analysis stage (ms)"
        },
        "total": {
          "type": "number",
          "minimum": 0.0,
          "description": "Total wall-clock time (ms)"
        }
      }
    },
    "profile": {
      "type": "string",
      "minLength": 1,
      "description": "Configuration profile used (e.g., 'default', 'fast', 'accurate')"
    }
  }
}
```

---

## Field Reference

### `entities` (Array)

**Purpose**: Named entities detected in the input text.

**Item Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✓ | The entity text as it appears in source |
| `type` | string | ✓ | Entity type (PERSON, ORG, PRODUCT, LOCATION, etc.) |
| `start_char` | integer | ✓ | Character index where entity starts (0-indexed) |
| `end_char` | integer | ✓ | Character index where entity ends (exclusive, so end - start = length) |

**Validation Rules**:
- `start_char` and `end_char` must be non-negative
- `start_char` must be ≤ `end_char`
- Both should be within bounds of input text

**Example**:
```json
{
  "text": "Microsoft",
  "type": "ORG",
  "start_char": 0,
  "end_char": 9
}
```

---

### `relationships` (Array)

**Purpose**: Semantic relationships between entities with polarity and confidence.

**Item Schema**:
| Field | Type | Required | Range/Enum | Description |
|-------|------|----------|-----------|-------------|
| `source` | string | ✓ | - | Source entity name |
| `target` | string | ✓ | - | Target entity name |
| `polarity_score` | number | ✓ | [-1.0, 1.0] | Numeric polarity: -1=negative, 0=neutral, +1=positive |
| `polarity_label` | string | ✓ | positive\|negative\|neutral | Human-readable label matching score |
| `confidence` | number | ✓ | [0.0, 1.0] | Confidence in relationship (0=unsure, 1=certain) |
| `explanation` | string | ✓ | - | Natural language justification |

**Validation Rules**:
- `polarity_score` must be in [-1.0, 1.0]
- `confidence` must be in [0.0, 1.0]
- `polarity_label` should semantically match score:
  - "positive" → score > 0.3
  - "negative" → score < -0.3
  - "neutral" → -0.3 ≤ score ≤ 0.3
- Both entities in `source` and `target` should exist in the `entities` array

**Example**:
```json
{
  "source": "Microsoft",
  "target": "Azure",
  "polarity_score": 0.87,
  "polarity_label": "positive",
  "confidence": 0.93,
  "explanation": "Microsoft developed and heavily invests in Azure cloud platform."
}
```

---

### `ner_relationships` (Array)

**Purpose**: Typed relationships from the NER module, complementing semantic relationships.

**Item Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | ✓ | Source entity name |
| `target` | string | ✓ | Target entity name |
| `type` | string | ✓ | Relationship type (OWNS, WORKS_WITH, LEADS, MENTIONS, etc.) |
| `score` | number | ✓ | Confidence in relationship type (0.0–1.0) |

**Common Relationship Types**:
- `OWNS` - Entity owns/controls target
- `WORKS_WITH` - Entities collaborate or interact
- `LEADS` - Person leads an organization
- `MENTIONS` - Source mentions target
- `COMPETES_WITH` - Entities compete
- `DEVELOPS` - Entity develops/creates target product
- `LOCATED_IN` - Entity is located in place

**Example**:
```json
{
  "source": "Microsoft",
  "target": "Azure",
  "type": "OWNS",
  "score": 0.99
}
```

---

### `counts` (Object)

**Purpose**: Validation totals that should match array lengths.

**Fields**:
| Field | Type | Required | Min | Description |
|-------|------|----------|-----|-------------|
| `entities` | integer | ✓ | 0 | Length of `entities` array |
| `relationships` | integer | ✓ | 0 | Length of `relationships` array |
| `ner_relationships` | integer | ✓ | 0 | Length of `ner_relationships` array |

**Validation Rules**:
- `counts.entities` must equal `len(entities)`
- `counts.relationships` must equal `len(relationships)`
- `counts.ner_relationships` must equal `len(ner_relationships)`

**Example**:
```json
{
  "entities": 3,
  "relationships": 2,
  "ner_relationships": 2
}
```

---

### `timings_ms` (Object)

**Purpose**: Performance metrics for analysis stages (all in milliseconds).

**Fields**:
| Field | Type | Required | Min | Description |
|-------|------|----------|-----|-------------|
| `init` | number | ✓ | 0 | Model initialization time |
| `ner` | number | ✓ | 0 | NER/entity detection time |
| `relationships` | number | ✓ | 0 | Relationship analysis time |
| `total` | number | ✓ | 0 | Total wall-clock time |

**Validation Rules**:
- All values must be ≥ 0
- `total` should approximately equal `init + ner + relationships` (allow 10% tolerance for overhead)
- All times are in milliseconds

**Example**:
```json
{
  "init": 2.4,
  "ner": 27.8,
  "relationships": 15.6,
  "total": 56.2
}
```

---

### `profile` (String)

**Purpose**: Identifies which configuration profile was used.

**Rules**:
- Non-empty string
- Common values: `default`, `fast`, `accurate`, `rag-enhanced`

**Example**:
```json
{
  "profile": "default"
}
```

---

## Validation Rules Summary

| Category | Rule | Consequence if Violated |
|----------|------|------------------------|
| **Required Fields** | All 6 top-level fields must exist | Validation ERROR |
| **Array Lengths** | Count fields must match array lengths | Validation ERROR |
| **Character Positions** | start_char ≤ end_char; both ≥ 0 | Validation ERROR |
| **Ranges** | polarity_score ∈ [-1,1]; confidence ∈ [0,1] | Validation ERROR |
| **Semantic Consistency** | polarity_label matches polarity_score sign | Validation WARNING (error in strict mode) |
| **Timing Sum** | total ≈ init+ner+relationships (10% tolerance) | Validation WARNING (error in strict mode) |

---

## Example: Complete Valid Output

```json
{
  "entities": [
    {
      "text": "Microsoft",
      "type": "ORG",
      "start_char": 0,
      "end_char": 9
    },
    {
      "text": "Azure",
      "type": "PRODUCT",
      "start_char": 12,
      "end_char": 17
    },
    {
      "text": "John Doe",
      "type": "PERSON",
      "start_char": 20,
      "end_char": 28
    }
  ],
  "relationships": [
    {
      "source": "Microsoft",
      "target": "Azure",
      "polarity_score": 0.87,
      "polarity_label": "positive",
      "confidence": 0.93,
      "explanation": "Microsoft announced a new partnership with Azure, indicating favorable outlook."
    },
    {
      "source": "Azure",
      "target": "John Doe",
      "polarity_score": -0.42,
      "polarity_label": "negative",
      "confidence": 0.78,
      "explanation": "John Doe expressed concerns about Azure pricing."
    }
  ],
  "ner_relationships": [
    {
      "source": "Microsoft",
      "target": "Azure",
      "type": "OWNS",
      "score": 0.91
    },
    {
      "source": "Azure",
      "target": "John Doe",
      "type": "MENTIONS",
      "score": 0.64
    }
  ],
  "counts": {
    "entities": 3,
    "relationships": 2,
    "ner_relationships": 2
  },
  "timings_ms": {
    "init": 12.4,
    "ner": 27.8,
    "relationships": 15.6,
    "total": 56.2
  },
  "profile": "default"
}
```

---

## Using the Validator

### Python API

```python
from grid.schemas.grid_output_validator import GridOutputValidator, validate_grid_output
import json

# Option 1: Quick validation
is_valid, errors = validate_grid_output(json_string_or_dict, strict=True)
if is_valid:
    print("✓ Output is valid")
else:
    for error in errors:
        print(f"✗ {error}")

# Option 2: Detailed validation
validator = GridOutputValidator()
is_valid, issues = validator.validate(data, strict=False)  # warnings allowed
for issue in issues:
    print(f"[{issue.severity}] {issue.field}: {issue.message}")

# Option 3: Get schema
schema = GridOutputValidator.get_schema_dict()
print(json.dumps(schema, indent=2))
```

### Command-Line Usage (planned)

```bash
# Validate from file
python -m grid.schemas.grid_output_validator --file output.json --strict

# Validate from stdin
cat output.json | python -m grid.schemas.grid_output_validator --stdin
```

---

## Test Fixtures

Reference fixtures are provided in `tests/fixtures/grid_output/`:

| Fixture | Purpose | Use Case |
|---------|---------|----------|
| `small_single_entity.json` | Single entity, no relationships | Baseline performance |
| `medium_canonical.json` | 3 entities, 2 relationships | Standard test case |
| `large_complex.json` | 10 entities, 8 relationships | Load testing |
| `edge_neutral_polarity.json` | Neutral polarity (score=0) | Boundary conditions |
| `edge_empty_results.json` | No entities or relationships | Minimal case |
| `edge_extreme_polarities.json` | Extreme scores (-1, +1) | Range limits |

**Usage**:
```python
import json

# Load fixture
with open("tests/fixtures/grid_output/medium_canonical.json") as f:
    fixture = json.load(f)

# Validate
is_valid, errors = validate_grid_output(fixture)
print(f"Fixture valid: {is_valid}")
```

---

## Integration

### With CLI

The `grid analyze` command will support:
```bash
# Automatic validation with --validate flag
python -m grid analyze TEXT --output json --validate

# Pretty-printed output with schema awareness
python -m grid analyze TEXT --output pretty

# Strict validation mode
python -m grid analyze TEXT --validate --strict
```

### With Benchmarking

The `benchmark_grid.py` tool will:
1. Run analysis
2. Validate output shape
3. Extract timings for metrics
4. Compare against baseline fixtures

### With Formatters

Output formatters in `grid/schemas/grid_output_formatter.py`:
```python
from grid.schemas.grid_output_formatter import format_output

# Guaranteed schema-compliant formatting
json_str = format_output(data, fmt="json")
table_str = format_output(data, fmt="table")
pretty_str = format_output(data, fmt="pretty")
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial release; canonical schema with 6 required fields |

---

## Questions & Support

- **Schema Issues**: Check [GRID_COMMANDS_PERFORMANCE.md](./GRID_COMMANDS_PERFORMANCE.md)
- **Validation Errors**: Run with `--debug` flag
- **Custom Extensions**: Contact development team
