# Task Prompts - Immediate Actions

These are concrete, copy-paste prompts for immediate agent actions. Use these commands to kick off specific workflows.

## Inventory Prompt

```
/inventory root=/path/to/repo
```

Produce JSON with:
- manifest path(s)
- modules list (with interface_schema paths)
- CI config files and their triggers
- tests (unit, integration, contract) and their runners
- owners and README presence

**Expected Output**:
```json
{
  "manifest_paths": [
    "system_template.json",
    "scaffolds/DOC/system_template.json"
  ],
  "modules": [
    {
      "name": "module_name",
      "path": "path/to/module",
      "interface_schema": "path/to/schema",
      "version": "1.0.0",
      "owner": "owner_name",
      "type": "library|service|artifact"
    }
  ],
  "ci_files": [
    {
      "path": ".github/workflows/ci.yml",
      "provider": "github_actions",
      "triggers": ["push", "pull_request"],
      "stages": ["lint", "unit_test", "contract_test"]
    }
  ],
  "tests": {
    "unit": {
      "files": ["tests/test_module.py"],
      "runner": "pytest",
      "count": 50
    },
    "integration": {
      "files": ["tests/integration/test_integration.py"],
      "runner": "pytest",
      "count": 12
    },
    "contract": {
      "files": ["tests/test_contracts.py"],
      "runner": "pytest",
      "count": 8
    }
  },
  "owners": {
    "module_name": "owner_name"
  },
  "evidence": [
    {"file": "path/to/file", "line": 123, "type": "module_definition"}
  ]
}
```

---

## Gap Analysis Prompt

```
/gapanalysis {inventory_json}
```

Given the inventory JSON, produce GAPS[] covering: missing interface schemas, missing semver, missing contract tests, missing CI stages, missing validation scripts, missing owners, missing metrics. For each gap: severity (1-5), impact, minimal remediation, estimated effort.

**Expected Output**:
```json
{
  "gaps": [
    {
      "id": "GAP-1",
      "category": "missing_interface_schema|missing_semver|missing_contract_tests|missing_ci_stage|missing_validation|missing_owner|missing_metrics",
      "severity": 1|2|3|4|5,
      "description": "Gap description",
      "impact": "Impact description",
      "affected_modules": ["module1", "module2"],
      "minimal_remediation": "Remediation steps",
      "estimated_effort_hours": 4,
      "priority": "critical|high|medium|low",
      "evidence": [
        {"file": "path/to/file", "line": 123}
      ]
    }
  ],
  "summary": {
    "total_gaps": 10,
    "critical": 2,
    "high": 3,
    "medium": 4,
    "low": 1
  }
}
```

---

## Plan & Backlog Prompt

```
/plan {GAPS[]} constraints={"team_size":3, "sprint_length_weeks":2, "risk_tolerance":"medium"}
```

From GAPS[], produce a prioritized backlog with epics and stories. Output stories as JSON with id, title, description, priority, effort_hours, owner, acceptance_criteria, validation_commands, rollback_plan. Also output a 3-sprint plan with milestones and one key demo per milestone.

**Expected Output**:
```json
{
  "backlog": {
    "epics": [
      {
        "id": "EPIC-1",
        "title": "Epic Title",
        "description": "Epic description",
        "stories": [
          {
            "id": "STORY-1",
            "title": "Story Title",
            "description": "Story description",
            "priority": "High|Medium|Low",
            "effort_hours": 8,
            "owner": "owner_name",
            "acceptance_criteria": [
              "Criterion 1",
              "Criterion 2"
            ],
            "validation_commands": [
              "python validate_system.py",
              "pytest tests/test_module.py"
            ],
            "rollback_plan": "Rollback steps",
            "dependencies": ["STORY-2"],
            "tags": ["contract", "test"]
          }
        ]
      }
    ]
  },
  "roadmap": {
    "sprint_1": {
      "duration_weeks": 2,
      "milestones": ["Milestone 1: Contract coverage 100%"],
      "stories": ["STORY-1", "STORY-2"],
      "demo": "Demo: All modules have interface schemas"
    },
    "sprint_2": {
      "duration_weeks": 2,
      "milestones": ["Milestone 2: Contract tests passing"],
      "stories": ["STORY-3"],
      "demo": "Demo: Contract test suite running in CI"
    },
    "sprint_3": {
      "duration_weeks": 2,
      "milestones": ["Milestone 3: Validation automation"],
      "stories": ["STORY-4"],
      "demo": "Demo: Automated validation on every PR"
    }
  }
}
```

---

## Generate PR Prompt

```
/execute story=STORY-1 assign=alice
```

Implement story ID X. Produce:
- patch.diff to apply (unified diff)
- files to create/update (path + content)
- unit tests to add
- CI job snippet (YAML) to add to .github/workflows/ci.yml
- PR description (title + body) including motivation, test instructions, and rollback steps.

**Expected Output**:
```json
{
  "task_id": "STORY-1",
  "diff": "--- a/path/to/file.py\n+++ b/path/to/file.py\n@@ -1,3 +1,5 @@\n...",
  "files": [
    {
      "path": "path/to/file.py",
      "content": "file content",
      "action": "create|update|delete"
    }
  ],
  "tests": [
    {
      "path": "tests/test_module.py",
      "content": "test code with seeded RNGs if stochastic",
      "coverage_target": 0.8
    }
  ],
  "ci_snippet": {
    "file": ".github/workflows/ci.yml",
    "content": "YAML snippet to add",
    "stage": "contract_test",
    "insert_after": "unit_test"
  },
  "pr_text": {
    "title": "feat: Add interface schema for module X",
    "body": "## Motivation\n\nDescription of why this change is needed.\n\n## Changes\n\n- Added interface_schema for module X\n- Added contract tests\n- Updated CI pipeline\n\n## Testing\n\nRun: `python validate_system.py`\nRun: `pytest tests/test_contracts.py`\n\n## Rollback\n\n```bash\ngit revert <commit_hash>\npython validate_system.py\n```",
    "checklist": [
      "- [ ] All tests passing",
      "- [ ] validate_system.py returns 0",
      "- [ ] Contract tests added",
      "- [ ] CI updated"
    ]
  },
  "changelog_entry": "### Added\n- Interface schema for module X\n- Contract tests for module X",
  "readme_updates": [
    {
      "section": "Modules",
      "content": "Updated module list with interface schemas"
    }
  ],
  "rollback_commands": [
    "git revert <commit_hash>",
    "python validate_system.py"
  ],
  "git_commands": [
    "git checkout -b feat/add-interface-schema-module-x",
    "git add path/to/file.py",
    "git commit -m 'feat: Add interface schema for module X'",
    "git push origin feat/add-interface-schema-module-x"
  ]
}
```

---

## Validation Prompt

```
/validate task=STORY-1
```

Run validation for a completed task. Execute tests, check metrics, produce ValidationReport.

**Expected Output**: Same as Evaluator role output (ValidationReport JSON).

---

## Safety Review Prompt

```
/safety review change=STORY-1 risk_level=medium
```

Produce safety and governance review for a proposed change.

**Expected Output**: Same as SafetyOfficer role output (Governance document JSON).
