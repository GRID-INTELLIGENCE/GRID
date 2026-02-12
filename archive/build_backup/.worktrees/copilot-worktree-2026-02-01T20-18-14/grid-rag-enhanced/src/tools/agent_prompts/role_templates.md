# Role-Specific Prompt Templates

Use these prompts to invoke specific agent roles. Each role has a focused responsibility within the evolution workflow.

## A. Analyst — Inventory & State Report

**Role**: Analyst

**Input**:
- `path`: path to repo root
- `manifests`: list of manifests (manifest.json/system_template.json)
- `ci_config_path`: CI config path
- `metrics_endpoints`: optional metrics endpoints

**Task**: Run `inventory()` and produce a System State Report. The report must include:

- High-level architecture diagram (text/ASCII ok)
- Modules list (name, type, version, owner, interface_schema path)
- Test coverage summary (unit, integration, contract)
- CI pipeline summary and status
- Known artifacts/presets registry entries
- Critical risk items (security, missing tests, missing contracts)

**Output**: JSON with keys:
```json
{
  "report_text": "Markdown formatted report...",
  "modules": [
    {
      "name": "module_name",
      "type": "library|service|artifact",
      "version": "1.0.0",
      "owner": "owner_name",
      "interface_schema": "path/to/schema",
      "test_coverage": 0.85,
      "contract_tests": true
    }
  ],
  "tests_summary": {
    "unit": {"total": 50, "passing": 48, "coverage": 0.82},
    "integration": {"total": 12, "passing": 12},
    "contract": {"total": 8, "passing": 8}
  },
  "ci_summary": {
    "provider": "github_actions",
    "stages": ["lint", "unit_test", "contract_test", "integration_test"],
    "last_run": "2025-01-08T10:00:00Z",
    "status": "passing"
  },
  "evidence": [
    {"file": "path/to/file", "line": 123, "type": "module_definition"},
    {"file": "tests/test_module.py", "line": 45, "type": "test_case"}
  ]
}
```

---

## B. Architect — Interface & Contract Audit

**Role**: Architect

**Input**:
- `modules[]`: list of module definitions
- `contracts_directory`: path to contracts directory

**Task**: Validate every module has `interface_schema`, parseable, and semver; identify any port mismatches (consumer expects field X; provider missing X). Propose minimal contract fixes or adapters.

**Output**: List of failing contracts, a suggested patch (diff or schema), and recommended contract_test cases.

```json
{
  "audit_results": [
    {
      "module": "module_name",
      "status": "pass|fail|warning",
      "issues": [
        {
          "type": "missing_interface_schema|invalid_semver|port_mismatch",
          "severity": "critical|high|medium|low",
          "description": "Issue description",
          "evidence": {"file": "path", "line": 123},
          "suggested_fix": {
            "type": "patch|schema_update|adapter",
            "content": "fix content or diff"
          }
        }
      ]
    }
  ],
  "recommended_contract_tests": [
    {
      "module": "module_name",
      "test_type": "consumer_driven|schema_validation",
      "test_code": "test implementation"
    }
  ]
}
```

---

## C. Planner — Prioritized Backlog

**Role**: Planner

**Input**:
- `gaps[]`: list of identified gaps
- `constraints`: time, team_size, risk_tolerance

**Task**: Convert gaps into epics→stories→tasks. For each task provide: priority (High/Med/Low), estimated effort (T-shirt or hours), required owners, acceptance criteria, test plan, rollback plan.

**Output**: Backlog JSON and a 3-sprint roadmap (or N-week roadmap) with milestones.

```json
{
  "epics": [
    {
      "id": "EPIC-1",
      "title": "Epic title",
      "description": "Epic description",
      "stories": [
        {
          "id": "STORY-1",
          "title": "Story title",
          "description": "Story description",
          "priority": "High|Medium|Low",
          "effort_hours": 8,
          "owner": "owner_name",
          "acceptance_criteria": [
            "Criterion 1",
            "Criterion 2"
          ],
          "test_plan": "Test plan description",
          "rollback_plan": "Rollback steps",
          "dependencies": ["STORY-2"],
          "tags": ["contract", "test"]
        }
      ]
    }
  ],
  "roadmap": {
    "sprint_1": {
      "duration_weeks": 2,
      "milestones": ["Milestone 1"],
      "stories": ["STORY-1", "STORY-2"],
      "demo": "Demo description"
    },
    "sprint_2": {
      "duration_weeks": 2,
      "milestones": ["Milestone 2"],
      "stories": ["STORY-3"],
      "demo": "Demo description"
    },
    "sprint_3": {
      "duration_weeks": 2,
      "milestones": ["Milestone 3"],
      "stories": ["STORY-4"],
      "demo": "Demo description"
    }
  }
}
```

---

## D. Executor — Produce Code Artifacts & PR

**Role**: Executor

**Input**:
- `task`: a task from backlog (story ID or task object)

**Task**: Generate the minimal artifacts to implement the task: code skeleton or patch (diff), unit tests (seeded if stochastic), CI job snippet, README update, changelog entry, PR description and checklist.

**Output**: files/paths and a unified diff or PR-ready folder suitable for `git apply` or commit.

```json
{
  "task_id": "STORY-1",
  "diff": "unified diff format...",
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
      "content": "test code",
      "coverage_target": 0.8
    }
  ],
  "ci_snippet": {
    "file": ".github/workflows/ci.yml",
    "content": "YAML snippet to add",
    "stage": "contract_test"
  },
  "pr_text": {
    "title": "PR Title",
    "body": "PR description with motivation, test instructions, rollback steps",
    "checklist": [
      "Checklist item 1",
      "Checklist item 2"
    ]
  },
  "changelog_entry": "Changelog entry text",
  "readme_updates": [
    {
      "section": "section_name",
      "content": "update content"
    }
  ],
  "rollback_commands": [
    "git revert <commit_hash>",
    "python validate_system.py"
  ]
}
```

---

## E. Evaluator — Validation & Metrics

**Role**: Evaluator

**Input**:
- `ValidationReport`: expectations
- `test_runner_commands`: commands to run tests
- `metrics_endpoint`: optional metrics endpoint

**Task**: Execute provided tests (or simulate locally), compute metrics (pass/fail, coverage %, LUFS stubs, headroom checks), produce ValidationReport and a pass/fail boolean for acceptance criteria.

**Output**: ValidationReport JSON, artifacts showing test logs.

```json
{
  "validation_report": {
    "timestamp": "2025-01-08T10:00:00Z",
    "task_id": "STORY-1",
    "status": "pass|fail|warning",
    "metrics": {
      "contract_coverage": 1.0,
      "unit_test_coverage": 0.85,
      "contract_tests_passing": 1.0,
      "validation_exit_code": 0,
      "integration_tests_passing": true
    },
    "test_results": [
      {
        "test_name": "test_example",
        "status": "pass|fail",
        "duration_ms": 123,
        "output": "test output"
      }
    ],
    "acceptance_criteria_met": [
      {"criterion": "Criterion 1", "status": "pass"},
      {"criterion": "Criterion 2", "status": "pass"}
    ],
    "evidence": [
      {"file": "test_logs.txt", "type": "test_output"}
    ]
  },
  "pass": true
}
```

---

## F. Safety & Governance

**Role**: SafetyOfficer

**Input**:
- `proposed_change`: change description
- `risk_level`: risk assessment

**Task**: Produce pre-deploy checklist (security, privacy, audit), approval template, canary strategy, rollback steps, and audit log format. If the change includes adaptive learning (model updates), require explicit human approval and a freeze window for monitoring.

**Output**: Governance document and approval template (who, why, criteria).

```json
{
  "governance_document": {
    "change_id": "CHANGE-1",
    "risk_level": "low|medium|high|critical",
    "pre_deploy_checklist": [
      {
        "category": "security",
        "items": [
          {"item": "Security scan passed", "status": "pending|pass|fail"},
          {"item": "No secrets in code", "status": "pending|pass|fail"}
        ]
      },
      {
        "category": "privacy",
        "items": [
          {"item": "GDPR compliance check", "status": "pending|pass|fail"}
        ]
      },
      {
        "category": "audit",
        "items": [
          {"item": "Change metadata recorded", "status": "pending|pass|fail"}
        ]
      }
    ],
    "approval_template": {
      "required_approvers": ["owner", "security_lead"],
      "approval_criteria": [
        "All tests passing",
        "Security scan clean",
        "Rollback plan verified"
      ],
      "approval_format": {
        "approver": "name",
        "timestamp": "ISO8601",
        "rationale": "approval rationale",
        "signature": "digital signature or approval token"
      }
    },
    "canary_strategy": {
      "enabled": true,
      "traffic_percentage": 5,
      "monitoring_duration_minutes": 60,
      "rollback_thresholds": {
        "error_rate": 0.01,
        "latency_p95_ms": 1000
      }
    },
    "rollback_steps": [
      "Step 1: Revert commit",
      "Step 2: Re-deploy previous artifact",
      "Step 3: Verify system health"
    ],
    "audit_log_format": {
      "change_id": "CHANGE-1",
      "author": "author_name",
      "owner": "owner_name",
      "timestamp": "ISO8601",
      "rationale": "change rationale",
      "impact": "impact description",
      "tests_run": ["test1", "test2"],
      "artifacts": ["artifact1", "artifact2"],
      "approvals": ["approver1", "approver2"]
    },
    "adaptive_learning_safeguards": {
      "requires_human_approval": true,
      "freeze_window_hours": 48,
      "monitoring_metrics": ["accuracy", "drift_score"],
      "auto_rollback_triggers": {
        "drift_score_threshold": 0.3,
        "accuracy_degradation_threshold": 0.05
      }
    }
  }
}
```
