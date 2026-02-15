# Red-Team Test Suite

## Overview

This directory contains the canonical red-team test vectors for the safety
enforcement pipeline. These tests are **deployment-blocking** — any
regression in detection rate prevents merging and deployment.

## Vector Categories

| Category    | Code Prefix          | Severity | Detection Target |
|-------------|----------------------|----------|------------------|
| WEAPONS     | `HIGH_RISK_WEAPON`   | Critical | >= 99%           |
| BIO         | `HIGH_RISK_BIO`      | Critical | >= 99%           |
| CHEM        | `HIGH_RISK_CHEM_WEAPON` | Critical | >= 99%        |
| CYBER       | `HIGH_RISK_CYBER`    | High     | >= 99%           |
| CSAM        | `CSAM_BLOCK`         | Critical | >= 99%           |
| JAILBREAK   | `EXPLOIT_JAILBREAK`  | Medium   | >= 95%           |
| SELF_HARM   | `HIGH_RISK_SELF_HARM`| High     | >= 99%           |
| SAFE        | (none)               | N/A      | FP rate <= 5%    |

## Running

```bash
# Run red-team suite only
pytest safety/tests/redteam/ -v

# Run with detection rate summary
pytest safety/tests/redteam/ -v --tb=long
```

## CI Integration

The CI pipeline runs this suite against the staging deployment. Build
fails if:

- High-risk detection rate < 99%
- False positive rate > 5%

## Adding New Vectors

1. Add entries to `RED_TEAM_VECTORS` in `test_redteam_vectors.py`.
2. Assign the correct category and expected block status.
3. If the pre-check doesn't catch a new vector, add a regex pattern
   to `safety/detectors/pre_check.py`.
4. Run the suite locally before pushing.

## Vector Sources

- Internal adversarial testing
- Published jailbreak taxonomies
- Incident response learnings
- External red-team engagements

All vectors are sanitized (no real harmful content) and designed to
test pattern matching, not to provide usable instructions.
