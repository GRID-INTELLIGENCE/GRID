# Anthropic Safety Protocol

## Document Metadata
- **Version**: 1.0.0
- **Last Updated**: 2025-01-30
- **Provider**: Anthropic
- **Primary Model**: Claude
- **Status**: Active

---

## 1. Purpose

This document defines the safety protocol for monitoring, evaluating, and responding to Anthropic AI safety signals. It establishes rules, triggers, thresholds, and remediation procedures aligned with Anthropic's core safety frameworks:

- **Constitutional AI (CAI)** – Training methodology using principles to guide AI behavior
- **Responsible Scaling Policy (RSP)** – Protocols for managing risks of increasingly capable AI
- **AI Safety Levels (ASL)** – Tiered framework for addressing catastrophic risks

---

## 2. Core Safety Principles (HHH Framework)

Anthropic's Claude models are trained to be:

| Principle | Description | Priority |
|-----------|-------------|----------|
| **Helpful** | Genuinely beneficial to operators and users | 4 |
| **Honest** | Truthful, calibrated, transparent, non-deceptive | 2 |
| **Harmless** | Avoiding actions that are unsafe or unethical | 1 |

### 2.1 Constitutional Values Hierarchy

1. **Broadly Safe** – Not undermining human oversight mechanisms
2. **Broadly Ethical** – Good values, honesty, avoiding harm
3. **Anthropic Guidelines** – Compliance with specific guidelines
4. **Genuinely Helpful** – Benefiting operators and users

---

## 3. Safety Rules and Triggers

### 3.1 Severity Levels

| Level | Code | Description | Response Time |
|-------|------|-------------|---------------|
| Info | `INFO` | Informational observation | Log only |
| Warning | `WARN` | Early signal, requires attention | 24 hours |
| High | `HIGH` | Significant concern, action required | 4 hours |
| Critical | `CRIT` | Immediate action required | Immediate |

### 3.2 Safety Rules

#### RULE-ANT-001: Constitutional Principle Violation
```json
{
  "rule_id": "RULE-ANT-001",
  "description": "Trigger when Claude violates constitutional principles",
  "category": "constitutional_ai",
  "condition": {
    "metric": "constitutional_violation_rate",
    "operator": ">=",
    "thresholds": {
      "warning": 0.01,
      "high": 0.03,
      "critical": 0.05
    }
  },
  "actions": ["log", "notify", "escalate", "require_human_review"],
  "remediation": {
    "steps": [
      "Identify which constitutional principle was violated",
      "Review conversation context and prompts",
      "Assess whether violation was due to adversarial input",
      "Update constitutional training data if systematic"
    ]
  }
}
```

#### RULE-ANT-002: Alignment Faking Detection
```json
{
  "rule_id": "RULE-ANT-002",
  "description": "Trigger when alignment faking behavior is detected",
  "category": "alignment",
  "condition": {
    "metric": "alignment_faking_indicators",
    "operator": ">=",
    "thresholds": {
      "warning": 0.005,
      "high": 0.02,
      "critical": 0.05
    }
  },
  "severity": "critical",
  "actions": ["log", "notify", "escalate", "block", "require_human_review"],
  "indicators": [
    "Strategic compliance divergence between monitored/unmonitored contexts",
    "Scratchpad reasoning indicating preference preservation",
    "Inconsistent behavior based on perceived observation status"
  ],
  "remediation": {
    "steps": [
      "Flag for immediate human review",
      "Analyze reasoning traces if available",
      "Compare behavior across different contexts",
      "Escalate to alignment research team"
    ]
  }
}
```

#### RULE-ANT-003: Jailbreak Attempt Detection
```json
{
  "rule_id": "RULE-ANT-003",
  "description": "Trigger when jailbreak attempts are detected",
  "category": "jailbreak_resistance",
  "condition": {
    "metric": "jailbreak_success_rate",
    "operator": ">=",
    "thresholds": {
      "warning": 0.02,
      "high": 0.05,
      "critical": 0.10
    }
  },
  "actions": ["log", "notify", "block_request", "update_classifiers"],
  "jailbreak_patterns": [
    "Cipher and encoding attacks",
    "Role-play scenario exploitation",
    "Keyword substitution",
    "Prompt injection attacks",
    "Multi-step escalation"
  ],
  "remediation": {
    "steps": [
      "Log jailbreak attempt details",
      "Analyze attack pattern",
      "Update Constitutional Classifiers if novel attack",
      "Report to Safeguards team"
    ]
  }
}
```

#### RULE-ANT-004: Hard Constraint Violation
```json
{
  "rule_id": "RULE-ANT-004",
  "description": "Trigger when hard constraints are violated or nearly violated",
  "category": "hard_constraints",
  "severity": "critical",
  "hard_constraints": [
    "CBRN weapons uplift",
    "Critical infrastructure attacks",
    "Cyberweapon creation",
    "Human oversight undermining",
    "Mass harm assistance",
    "Power seizure assistance",
    "CSAM generation"
  ],
  "actions": ["log", "block", "escalate_immediate", "quarantine", "notify_security"],
  "remediation": {
    "steps": [
      "Immediately block output",
      "Quarantine conversation for review",
      "Alert security and compliance teams",
      "Conduct root cause analysis",
      "Update detection systems"
    ]
  }
}
```

#### RULE-ANT-005: Honesty Principle Violation
```json
{
  "rule_id": "RULE-ANT-005",
  "description": "Trigger when honesty principles are violated",
  "category": "honesty",
  "condition": {
    "metric": "honesty_violation_rate",
    "operator": ">=",
    "thresholds": {
      "warning": 0.01,
      "high": 0.03,
      "critical": 0.05
    }
  },
  "honesty_components": [
    "Truthfulness",
    "Calibration",
    "Transparency",
    "Forthright sharing",
    "Non-deception",
    "Non-manipulation",
    "Autonomy preservation"
  ],
  "actions": ["log", "notify", "require_human_review"],
  "remediation": {
    "steps": [
      "Identify which honesty component was violated",
      "Assess intent vs. error",
      "Review for manipulation patterns",
      "Update training if systematic"
    ]
  }
}
```

#### RULE-ANT-006: ASL Threshold Monitoring
```json
{
  "rule_id": "RULE-ANT-006",
  "description": "Monitor for capability changes affecting ASL classification",
  "category": "responsible_scaling",
  "asl_levels": {
    "ASL-1": "No meaningful catastrophic risk",
    "ASL-2": "Early signs of dangerous capabilities, current Claude level",
    "ASL-3": "Substantially increased catastrophic misuse risk",
    "ASL-4+": "Qualitative escalations, not yet defined"
  },
  "condition": {
    "metric": "capability_threshold_proximity",
    "operator": ">=",
    "thresholds": {
      "warning": 0.70,
      "high": 0.85,
      "critical": 0.95
    }
  },
  "actions": ["log", "notify", "escalate_to_rsp_committee"],
  "remediation": {
    "steps": [
      "Conduct full capability evaluation",
      "Engage Frontier Red Team",
      "Review ASL-3 safety measures readiness",
      "Brief leadership and board"
    ]
  }
}
```

#### RULE-ANT-007: Deception Signal Detection
```json
{
  "rule_id": "RULE-ANT-007",
  "description": "Detect deceptive behavior or false completion claims",
  "category": "deception",
  "condition": {
    "metric": "deception_flag_rate",
    "operator": ">=",
    "thresholds": {
      "warning": 0.01,
      "high": 0.03,
      "critical": 0.05
    }
  },
  "actions": ["log", "notify", "require_human_review", "flag_for_interpretability"],
  "remediation": {
    "steps": [
      "Review flagged outputs for deception indicators",
      "Analyze via interpretability tools if available",
      "Assess whether model claimed task completion without evidence",
      "Document and report to alignment team"
    ]
  }
}
```

#### RULE-ANT-008: Privacy Exposure
```json
{
  "rule_id": "RULE-ANT-008",
  "description": "Detect leakage or generation of sensitive data",
  "category": "privacy",
  "condition": {
    "metric": "privacy_exposure_rate",
    "operator": ">=",
    "thresholds": {
      "warning": 0.005,
      "high": 0.01,
      "critical": 0.02
    }
  },
  "actions": ["log", "notify", "block", "quarantine_output", "notify_compliance"],
  "remediation": {
    "steps": [
      "Block and quarantine exposed content",
      "Assess scope of exposure",
      "Notify affected parties if required",
      "Review data handling procedures"
    ]
  }
}
```

#### RULE-ANT-009: Power Concentration Warning
```json
{
  "rule_id": "RULE-ANT-009",
  "description": "Detect assistance with illegitimate power concentration",
  "category": "societal_safety",
  "indicators": [
    "Democratic process manipulation",
    "Constitutional limit circumvention",
    "Dissent suppression assistance",
    "Information ecosystem undermining",
    "Blackmail or coercion assistance"
  ],
  "actions": ["log", "block", "escalate", "notify_policy_team"],
  "remediation": {
    "steps": [
      "Block request immediately",
      "Assess legitimacy of power-related request",
      "Review for manipulation or deception",
      "Escalate to policy and legal teams"
    ]
  }
}
```

#### RULE-ANT-010: User Wellbeing Concern
```json
{
  "rule_id": "RULE-ANT-010",
  "description": "Detect potential harm to user wellbeing",
  "category": "user_safety",
  "indicators": [
    "Self-harm signals",
    "Crisis indicators",
    "Vulnerable user interaction",
    "Excessive dependency patterns"
  ],
  "actions": ["log", "provide_resources", "adjust_response", "notify_if_critical"],
  "remediation": {
    "steps": [
      "Provide appropriate safety resources",
      "Refer to emergency services if risk to life",
      "Maintain dignity while setting boundaries",
      "Document for review"
    ]
  }
}
```

---

## 4. Thresholds Configuration

### 4.1 Global Defaults

```json
{
  "global_defaults": {
    "cooldown_minutes": 60,
    "aggregation_window_minutes": 1440,
    "require_human_review_for": ["critical"],
    "actions_by_severity": {
      "info": ["log"],
      "warning": ["log", "notify"],
      "high": ["log", "notify", "escalate"],
      "critical": ["log", "notify", "escalate", "block", "require_human_review"]
    }
  }
}
```

### 4.2 Signal-Specific Thresholds

| Signal | Warning | High | Critical | Notes |
|--------|---------|------|----------|-------|
| Constitutional Violation | 1% | 3% | 5% | Based on violation rate |
| Jailbreak Success | 2% | 5% | 10% | Success rate of attempts |
| Alignment Faking | 0.5% | 2% | 5% | Detection rate |
| Hallucination | 10% | 20% | 30% | Rate on eval prompts |
| Deception | 1% | 3% | 5% | Flag rate |
| Privacy Exposure | 0.5% | 1% | 2% | Exposure rate |
| Honesty Violation | 1% | 3% | 5% | Violation rate |

### 4.3 Nuance Rules

```json
{
  "nuance_rules": [
    {
      "if_domain": ["medical", "legal", "financial"],
      "escalate_severity_by": 1,
      "reason": "High-stakes domains require stricter thresholds"
    },
    {
      "if_user_type": "vulnerable",
      "escalate_severity_by": 1,
      "reason": "Additional protection for vulnerable users"
    },
    {
      "if_context": "agentic_task",
      "escalate_severity_by": 1,
      "reason": "Autonomous actions have higher risk profile"
    }
  ]
}
```

---

## 5. Actions Catalog

| Action ID | Type | Description |
|-----------|------|-------------|
| `log` | Logging | Write structured log entry |
| `notify` | Notification | Send alert to configured channels |
| `escalate` | Escalation | Escalate to higher-level review |
| `block` | Policy | Block or refuse the request |
| `block_request` | Policy | Block specific request |
| `quarantine` | Policy | Quarantine output for review |
| `quarantine_output` | Policy | Isolate specific output |
| `require_human_review` | Governance | Require manual validation |
| `provide_resources` | Support | Provide safety resources |
| `update_classifiers` | Automation | Update Constitutional Classifiers |
| `notify_security` | Security | Alert security team |
| `notify_compliance` | Compliance | Alert compliance team |
| `notify_policy_team` | Policy | Alert policy team |
| `escalate_to_rsp_committee` | Governance | Escalate to RSP committee |
| `escalate_immediate` | Emergency | Immediate escalation |
| `flag_for_interpretability` | Research | Flag for interpretability analysis |

---

## 6. Principal Hierarchy

Claude's principal hierarchy defines trust levels and instruction precedence:

### 6.1 Trust Levels

| Level | Principal | Trust | Description |
|-------|-----------|-------|-------------|
| 1 | Anthropic | Highest | Trains and is responsible for Claude |
| 2 | Operators | High | API users building products |
| 3 | Users | Moderate | End users in conversation |

### 6.2 Conflict Resolution

1. Anthropic guidelines take precedence over operator instructions
2. Operator instructions take precedence over user requests (within Anthropic bounds)
3. Users cannot grant permissions beyond what operators allow
4. Hard constraints cannot be overridden by any principal

---

## 7. Notification Configuration

### 7.1 Channels

```json
{
  "notification_channels": {
    "email": {
      "enabled": true,
      "templates_path": "AI SAFETY/PROVIDERS/ANTHROPIC/notifications/templates/"
    },
    "slack": {
      "enabled": true,
      "channel": "#anthropic-safety-alerts"
    },
    "pagerduty": {
      "enabled": true,
      "severity_threshold": "critical"
    }
  }
}
```

### 7.2 Recipient Groups

| Group | Receives | Severity Threshold |
|-------|----------|-------------------|
| safety_ops | All safety alerts | warning+ |
| alignment_team | Alignment-related | high+ |
| frontier_red_team | Security signals | high+ |
| rsp_committee | ASL/capability | high+ |
| leadership | Critical escalations | critical |

---

## 8. Monitoring Sources

| Source | URL | Type | Frequency |
|--------|-----|------|-----------|
| Research Index | anthropic.com/research | Research publications | Weekly |
| News/Announcements | anthropic.com/news | Policy updates | Weekly |
| Constitution | anthropic.com/constitution | Core document | Monthly |
| Transparency Hub | anthropic.com/transparency | Reports | Monthly |
| Model Cards | Model-specific | Technical specs | Per release |

---

## 9. Remediation Playbook

### 9.1 General Remediation Flow

```
1. IDENTIFY
   ├── Issue category (harmlessness, honesty, helpfulness)
   ├── Severity level
   └── Affected constitutional principles

2. ASSESS
   ├── Check hard constraint violations
   ├── Evaluate ASL implications
   └── Review conversation context

3. RESPOND
   ├── Apply appropriate action from catalog
   ├── Document incident
   └── Notify relevant teams

4. REMEDIATE
   ├── Implement fixes
   ├── Update classifiers/training if needed
   └── Verify resolution

5. REVIEW
   ├── Post-incident analysis
   ├── Update protocols if needed
   └── Share learnings
```

### 9.2 Scenario-Specific Guidance

#### Jailbreak Detected
1. Block the request
2. Log attack pattern details
3. Analyze for novel techniques
4. Update Constitutional Classifiers
5. Report to Safeguards team

#### Alignment Faking Suspected
1. Flag for immediate human review
2. Preserve all context and reasoning traces
3. Compare behavior across contexts
4. Escalate to alignment research
5. Do not modify model without full analysis

#### Hard Constraint Near-Violation
1. Block output immediately
2. Quarantine conversation
3. Alert security and compliance
4. Conduct root cause analysis
5. Document for training improvements

---

## 10. Appendices

### A. Constitutional AI Principles Reference
See: `ANTHROPIC_AI_SAFETY_SCHEMA.json` → `constitutional_ai.constitution.core_values`

### B. Hard Constraints Full List
See: `ANTHROPIC_AI_SAFETY_SCHEMA.json` → `hard_constraints.constraints`

### C. Honesty Principles Full List
See: `ANTHROPIC_AI_SAFETY_SCHEMA.json` → `honesty_principles.components`

### D. Related Documents
- `ANTHROPIC_AI_SAFETY_SCHEMA.json` – Structured schema
- `REPORT_TEMPLATE.md` – Report generation template
- `THRESHOLDS.json` – Threshold configuration
- `ACTIONS_MATRIX.json` – Action catalog details

---

## 11. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-30 | AI Safety Team | Initial protocol creation |

---

## 12. References

- [Anthropic Core Views on AI Safety](https://www.anthropic.com/news/core-views-on-ai-safety)
- [Responsible Scaling Policy](https://www.anthropic.com/news/anthropics-responsible-scaling-policy)
- [Constitutional Classifiers](https://www.anthropic.com/research/constitutional-classifiers)
- [Alignment Faking Research](https://www.anthropic.com/research/alignment-faking)
- [Claude's Constitution](https://www.anthropic.com/constitution)
