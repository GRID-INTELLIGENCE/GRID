# Session Checkpoint

## Fixed
- `vinci_code/database/session.py` — SQLite fallback (was Databricks crash)
- `USE_DATABRICKS=false` required for tests

## Created
| File | Purpose |
|------|---------|
| `experiments/pattern_demo.py` | PatternEngine viz |
| `experiments/cascade_visualization.py` | B&W→color causality |
| `experiments/animation_engine.py` | Vectors, directions, physics |
| `experiments/doc_metrics.py` | Doc length optimizer |

## Tests
```bash
USE_DATABRICKS=false PYTHONPATH=. pytest tests/unit/test_pattern_engine.py tests/test_scoring.py -q
# 28 passed
```

## Key Concepts
- **Movement**: →←↑↓ (E/W/N/S), angles from East (0°), counterclockwise
- **Physics**: momentum = mass × velocity, gravity pulls −Y
- **Architecture**: Core pulls inward (gravity), adapters explore outward

## Next
- [ ] Z-axis for 3D depth
- [ ] Fix remaining test imports
- [ ] Clean name-clashed dirs

---
*Target: <150 words, scannable in 30s*
