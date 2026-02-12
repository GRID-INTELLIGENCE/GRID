# Example Kickoff Dialogue

This example shows how to use the agent prompts to kick off a system evolution workflow.

## Initial Setup

**User to Agent**:

```
SYSTEM (set): <system prompt from tools/agent_prompts/system_prompt.md>
```

---

## Step 1: Inventory

**User**:
```
/inventory root=/workspace/grid
```

**Agent Response**:
```json
{
  "manifest_paths": [
    "scaffolds/DOC/system_template.json",
    "scaffolds/ice-cubes/project_template.json"
  ],
  "modules": [
    {
      "name": "kick",
      "path": "scaffolds/DOC/components.json",
      "interface_schema": null,
      "version": "1.0.0",
      "owner": "drums",
      "type": "artifact"
    },
    {
      "name": "analog_bass",
      "path": "scaffolds/DOC/components.json",
      "interface_schema": "contracts/openapi.yaml#/components/schemas/BassSpec",
      "version": "1.2.0",
      "owner": "low_end",
      "type": "module"
    },
    {
      "name": "compress_secure",
      "path": "grid/skills/compress_secure.py",
      "interface_schema": null,
      "version": null,
      "owner": null,
      "type": "library"
    }
  ],
  "ci_files": [
    {
      "path": ".github/workflows/ci.yml",
      "provider": "github_actions",
      "triggers": ["push", "pull_request"],
      "stages": ["lint", "unit_test"]
    }
  ],
  "tests": {
    "unit": {
      "files": ["tests/test_compress_secure.py", "tests/test_embedded_agentic.py"],
      "runner": "pytest",
      "count": 50
    },
    "integration": {
      "files": ["tests/integration/test_ai_brain_integration.py"],
      "runner": "pytest",
      "count": 12
    },
    "contract": {
      "files": [],
      "runner": "pytest",
      "count": 0
    }
  },
  "owners": {
    "kick": "drums",
    "analog_bass": "low_end"
  },
  "evidence": [
    {"file": "scaffolds/DOC/components.json", "line": 4, "type": "module_definition"},
    {"file": "grid/skills/compress_secure.py", "line": 1, "type": "module_definition"}
  ]
}
```

**Assumptions**:
- Repository root is `/workspace/grid`
- Using existing validation patterns from `scaffolds/DOC/validate_system.py`

**Next Actions**:
- Review inventory JSON
- Proceed to gap analysis: `/gapanalysis {inventory_json}`

---

## Step 2: Gap Analysis

**User**:
```
/gapanalysis {
  "manifest_paths": [...],
  "modules": [...],
  ...
}
```

**Agent Response**:
```json
{
  "gaps": [
    {
      "id": "GAP-1",
      "category": "missing_interface_schema",
      "severity": 4,
      "description": "Module 'compress_secure' lacks interface_schema",
      "impact": "Cannot validate contract, cannot run contract tests",
      "affected_modules": ["compress_secure"],
      "minimal_remediation": "Add interface_schema to module definition or create OpenAPI schema",
      "estimated_effort_hours": 2,
      "priority": "high",
      "evidence": [
        {"file": "grid/skills/compress_secure.py", "line": 1, "type": "module_definition"}
      ]
    },
    {
      "id": "GAP-2",
      "category": "missing_contract_tests",
      "severity": 5,
      "description": "No contract tests found in test suite",
      "impact": "Cannot validate interface contracts, risk of breaking changes",
      "affected_modules": ["all"],
      "minimal_remediation": "Add contract test stage to CI and create contract test files",
      "estimated_effort_hours": 8,
      "priority": "critical",
      "evidence": [
        {"file": "inventory.json", "line": 0, "type": "test_summary"}
      ]
    },
    {
      "id": "GAP-3",
      "category": "missing_ci_stage",
      "severity": 4,
      "description": "CI pipeline missing 'contract_test' stage",
      "impact": "Contract tests not run automatically, breaking changes may slip through",
      "affected_modules": ["all"],
      "minimal_remediation": "Add contract_test job to .github/workflows/ci.yml",
      "estimated_effort_hours": 1,
      "priority": "high",
      "evidence": [
        {"file": ".github/workflows/ci.yml", "line": 0, "type": "ci_config"}
      ]
    }
  ],
  "summary": {
    "total_gaps": 3,
    "critical": 1,
    "high": 2,
    "medium": 0,
    "low": 0
  }
}
```

**Assumptions**:
- Contract tests should use pytest
- OpenAPI schemas preferred for HTTP interfaces
- JSON Schema acceptable for message interfaces

**Next Actions**:
- Review gaps
- Proceed to planning: `/plan {GAPS[]} constraints={"team_size":2, "sprint_length_weeks":2}`

---

## Step 3: Plan & Backlog

**User**:
```
/plan {
  "gaps": [...]
} constraints={"team_size":2, "sprint_length_weeks":2, "risk_tolerance":"medium"}
```

**Agent Response**:
```json
{
  "backlog": {
    "epics": [
      {
        "id": "EPIC-1",
        "title": "Establish Contract Testing Infrastructure",
        "description": "Add contract testing capabilities to ensure interface stability",
        "stories": [
          {
            "id": "STORY-1",
            "title": "Add contract_test stage to CI pipeline",
            "description": "Add contract_test job to GitHub Actions workflow",
            "priority": "High",
            "effort_hours": 1,
            "owner": "devops",
            "acceptance_criteria": [
              "contract_test job exists in .github/workflows/ci.yml",
              "contract_test job runs on pull requests",
              "contract_test job validates OpenAPI schemas",
              "contract_test job exits with code 0 when all tests pass"
            ],
            "validation_commands": [
              "python -m pytest tests/contract/ -v",
              "python tools/agent_validate.py --check-contracts"
            ],
            "rollback_plan": "Remove contract_test job from CI workflow",
            "dependencies": [],
            "tags": ["ci", "contract", "infrastructure"]
          },
          {
            "id": "STORY-2",
            "title": "Add interface schemas for core modules",
            "description": "Create OpenAPI/JSON schemas for modules missing interface_schema",
            "priority": "High",
            "effort_hours": 4,
            "owner": "backend",
            "acceptance_criteria": [
              "All modules in grid/skills/ have interface_schema",
              "All schemas are parseable (OpenAPI validator passes)",
              "validate_system.py reports 100% contract coverage"
            ],
            "validation_commands": [
              "python validate_system.py manifest.json",
              "openapi-spec-validator contracts/openapi.yaml"
            ],
            "rollback_plan": "Revert schema files, update module definitions",
            "dependencies": ["STORY-1"],
            "tags": ["contract", "schema", "modules"]
          },
          {
            "id": "STORY-3",
            "title": "Create contract test suite",
            "description": "Add contract tests for all modules with interface schemas",
            "priority": "High",
            "effort_hours": 8,
            "owner": "backend",
            "acceptance_criteria": [
              "Contract tests exist for all modules with interface_schema",
              "All contract tests pass",
              "Contract test coverage ≥80%"
            ],
            "validation_commands": [
              "pytest tests/contract/ -v --cov=tests/contract",
              "python tools/agent_validate.py --check-contracts"
            ],
            "rollback_plan": "Remove contract test files",
            "dependencies": ["STORY-1", "STORY-2"],
            "tags": ["contract", "test", "coverage"]
          }
        ]
      }
    ]
  },
  "roadmap": {
    "sprint_1": {
      "duration_weeks": 2,
      "milestones": [
        "Milestone 1: CI pipeline includes contract_test stage",
        "Milestone 2: Core modules have interface schemas"
      ],
      "stories": ["STORY-1", "STORY-2"],
      "demo": "Demo: Run contract_test job in CI, show schema validation"
    },
    "sprint_2": {
      "duration_weeks": 2,
      "milestones": [
        "Milestone 3: Contract test suite complete"
      ],
      "stories": ["STORY-3"],
      "demo": "Demo: All contract tests passing, coverage report"
    },
    "sprint_3": {
      "duration_weeks": 2,
      "milestones": [
        "Milestone 4: 100% contract coverage, all tests passing"
      ],
      "stories": [],
      "demo": "Demo: Full system validation, all metrics green"
    }
  }
}
```

**Assumptions**:
- Team can work on 2 stories in parallel
- Contract tests use pytest framework
- OpenAPI schemas stored in `contracts/` directory

**Next Actions**:
- Review backlog and roadmap
- Approve story for execution: `/execute story=STORY-1 assign=alice`

---

## Step 4: Execute Story

**User**:
```
/execute story=STORY-1 assign=alice
```

**Agent Response**:
```json
{
  "task_id": "STORY-1",
  "diff": "--- a/.github/workflows/ci.yml\n+++ b/.github/workflows/ci.yml\n@@ -20,6 +20,25 @@ jobs:\n       - name: Run unit tests\n         run: pytest tests/ --cov=grid\n \n+  contract_test:\n+    runs-on: ubuntu-latest\n+    needs: analyze\n+    steps:\n+      - uses: actions/checkout@v4\n+      - name: Set up Python\n+        uses: actions/setup-python@v4\n+        with:\n+          python-version: '3.11'\n+      - name: Install dependencies\n+        run: pip install openapi-spec-validator jsonschema pyyaml\n+      - name: Validate contract schemas\n+        run: python tools/agent_validate.py --check-contracts\n+      - name: Run consumer-driven contract tests\n+        run: pytest tests/contract/ -v\n",
  "files": [
    {
      "path": ".github/workflows/ci.yml",
      "content": "# Existing workflow content...\n\n  contract_test:\n    runs-on: ubuntu-latest\n    needs: analyze\n    steps:\n      - uses: actions/checkout@v4\n      - name: Set up Python\n        uses: actions/setup-python@v4\n        with:\n          python-version: '3.11'\n      - name: Install dependencies\n        run: pip install openapi-spec-validator jsonschema pyyaml\n      - name: Validate contract schemas\n        run: python tools/agent_validate.py --check-contracts\n      - name: Run consumer-driven contract tests\n        run: pytest tests/contract/ -v\n",
      "action": "update"
    }
  ],
  "tests": [
    {
      "path": "tests/contract/__init__.py",
      "content": "# Contract tests package\n",
      "coverage_target": 0.0
    }
  ],
  "ci_snippet": {
    "file": ".github/workflows/ci.yml",
    "content": "  contract_test:\n    runs-on: ubuntu-latest\n    needs: analyze\n    steps:\n      - uses: actions/checkout@v4\n      - name: Set up Python\n        uses: actions/setup-python@v4\n        with:\n          python-version: '3.11'\n      - name: Install dependencies\n        run: pip install openapi-spec-validator jsonschema pyyaml\n      - name: Validate contract schemas\n        run: python tools/agent_validate.py --check-contracts\n      - name: Run consumer-driven contract tests\n        run: pytest tests/contract/ -v\n",
    "stage": "contract_test",
    "insert_after": "unit_test"
  },
  "pr_text": {
    "title": "feat: Add contract_test stage to CI pipeline",
    "body": "## Motivation\n\nAdd contract testing to CI pipeline to ensure interface stability and catch breaking changes early.\n\n## Changes\n\n- Added `contract_test` job to `.github/workflows/ci.yml`\n- Job validates OpenAPI schemas and runs contract tests\n- Job runs after `analyze` job completes\n\n## Testing\n\nRun locally:\n```bash\npython tools/agent_validate.py --check-contracts\npytest tests/contract/ -v\n```\n\n## Rollback\n\n```bash\ngit revert <commit_hash>\n# Or manually remove contract_test job from CI workflow\n```\n\n## Checklist\n\n- [ ] CI workflow updated\n- [ ] Contract test job runs successfully\n- [ ] Schema validation passes\n- [ ] No breaking changes to existing workflow",
    "checklist": [
      "- [ ] CI workflow updated",
      "- [ ] Contract test job runs successfully",
      "- [ ] Schema validation passes",
      "- [ ] No breaking changes to existing workflow"
    ]
  },
  "changelog_entry": "### Added\n- Contract test stage to CI pipeline\n- Contract schema validation in CI",
  "readme_updates": [
    {
      "section": "CI/CD",
      "content": "The CI pipeline now includes a `contract_test` stage that validates interface schemas and runs contract tests."
    }
  ],
  "rollback_commands": [
    "git revert <commit_hash>",
    "# Or manually edit .github/workflows/ci.yml to remove contract_test job"
  ],
  "git_commands": [
    "git checkout -b feat/add-contract-test-stage",
    "git add .github/workflows/ci.yml",
    "git commit -m 'feat: Add contract_test stage to CI pipeline'",
    "git push origin feat/add-contract-test-stage"
  ]
}
```

**Assumptions**:
- GitHub Actions workflow exists at `.github/workflows/ci.yml`
- Python 3.11 is available in CI
- `tools/agent_validate.py` script exists or will be created

**Evidence**:
- File: `.github/workflows/ci.yml` (existing workflow structure)
- File: `tools/agent_prompts/ci_automation.md` (reference implementation)

**Next Actions**:
- **Human approval required**: Review generated artifacts
- **Action**: Run `APPROVE_PR STORY-1` to proceed with creating branch/PR
- **Or**: Review and modify artifacts before approval

---

## Step 5: Approval & Execution

**User**:
```
APPROVE_PR STORY-1
```

**Agent Response**:
```
Approval received for STORY-1. Executing git commands:

Executing:
  git checkout -b feat/add-contract-test-stage
  git add .github/workflows/ci.yml
  git commit -m 'feat: Add contract_test stage to CI pipeline'
  git push origin feat/add-contract-test-stage

Branch created and pushed. Creating PR...

PR created: https://github.com/owner/repo/pull/123

Next steps:
1. Review PR: https://github.com/owner/repo/pull/123
2. CI will run automatically
3. Once CI passes, merge PR
4. Proceed to next story: /execute story=STORY-2 assign=bob
```

**Next Actions**:
- Monitor CI run for PR #123
- Once CI passes, merge PR
- Continue with next story in backlog

---

## Summary

This dialogue demonstrates the complete workflow:

1. **Inventory** → System discovery
2. **Gap Analysis** → Identify issues
3. **Planning** → Prioritized backlog
4. **Execution** → Generate artifacts
5. **Approval** → Human sign-off
6. **Validation** → CI/CD automation

Each step produces machine-readable JSON and human-friendly summaries, enabling both automated workflows and human oversight.
