# Anthropic AI Safety Protocol

## Provider Overview

**Provider**: Anthropic  
**Primary Model**: Claude  
**Mission**: Ensure that the world safely makes the transition through transformative AI  
**Website**: [anthropic.com](https://www.anthropic.com)

---

## Core Safety Frameworks

### 1. Constitutional AI (CAI)
Training methodology using principles (a "constitution") to guide AI behavior toward being:
- **Helpful** - Genuinely beneficial to operators and users
- **Honest** - Truthful, calibrated, transparent, non-deceptive
- **Harmless** - Avoiding actions that are unsafe or unethical

### 2. Responsible Scaling Policy (RSP)
Technical and organizational protocols for managing risks of increasingly capable AI systems, with a focus on catastrophic risks from:
- Deliberate misuse (e.g., bioweapons, cyberattacks)
- Autonomous AI actions contrary to designer intent

### 3. AI Safety Levels (ASL)
Tiered framework modeled after biosafety levels:

| Level | Description | Current Status |
|-------|-------------|----------------|
| ASL-1 | No meaningful catastrophic risk | - |
| ASL-2 | Early signs of dangerous capabilities | **Current (Claude)** |
| ASL-3 | Substantially increased catastrophic misuse risk | Future threshold |
| ASL-4+ | Qualitative escalations (not yet defined) | Future |

---

## Research Teams

| Team | Mission |
|------|---------|
| **Alignment** | Understand AI risks and ensure models remain helpful, honest, and harmless |
| **Interpretability** | Discover and understand how LLMs work internally |
| **Societal Impacts** | Explore how AI is used in the real world |
| **Frontier Red Team** | Analyze implications for cybersecurity, biosecurity, and autonomous systems |
| **Economic Research** | Study economic impacts and usage patterns |

---

## Directory Structure

```
ANTHROPIC/
├── README.md                      # This file
├── ANTHROPIC_AI_SAFETY_SCHEMA.json # Structured schema for safety data
├── SAFETY_PROTOCOL.md             # Rules, triggers, and thresholds
├── THRESHOLDS.json                # Threshold configuration
├── ACTIONS_MATRIX.json            # Action catalog and triggers
├── REPORT_TEMPLATE.md             # Report generation template
└── notifications/                 # Email templates and directories
    ├── templates/
    └── email_directory.json
```

---

## Key Documents

### Schema (`ANTHROPIC_AI_SAFETY_SCHEMA.json`)
- Provider metadata and research team structure
- Safety frameworks (Constitutional AI, RSP, ASL)
- Research areas and key projects
- Safety themes taxonomy
- Hard constraints (non-negotiable)
- Honesty principles
- User rights
- Principal hierarchy
- Monitoring sources
- Evaluation criteria

### Safety Protocol (`SAFETY_PROTOCOL.md`)
- Core safety principles (HHH Framework)
- Constitutional values hierarchy
- Safety rules and triggers (RULE-ANT-001 through RULE-ANT-010)
- Thresholds configuration
- Actions catalog
- Principal hierarchy trust levels
- Notification configuration
- Remediation playbook

### Thresholds (`THRESHOLDS.json`)
- Global defaults for cooldowns and aggregation
- Signal-specific thresholds:
  - Constitutional violations
  - Alignment faking detection
  - Jailbreak success rate
  - Hard constraint violations
  - Honesty violations
  - ASL capability proximity
  - Privacy exposure
  - And more...

### Actions Matrix (`ACTIONS_MATRIX.json`)
- Trigger definitions with confidence thresholds
- Action catalogs per trigger
- Escalation rules
- Notification defaults
- Anthropic-specific context (Constitutional Classifiers effectiveness)

---

## Hard Constraints

Claude's absolute restrictions that cannot be overridden:

1. **No CBRN weapons uplift** - Never provide serious uplift for weapons of mass destruction
2. **No critical infrastructure attacks** - Never assist attacks on power grids, water systems, etc.
3. **No cyberweapon creation** - Never create malicious code that could cause significant damage
4. **No oversight undermining** - Never undermine Anthropic's ability to oversee AI models
5. **No mass harm assistance** - Never assist in killing or disempowering humanity
6. **No illegitimate power seizure** - Never assist unprecedented societal, military, or economic control grabs
7. **No CSAM generation** - Never generate child sexual abuse material

---

## Monitoring Sources

| Source | URL | Frequency |
|--------|-----|-----------|
| Research Index | anthropic.com/research | Weekly |
| News/Announcements | anthropic.com/news | Weekly |
| Constitution | anthropic.com/constitution | Monthly |
| Transparency Hub | anthropic.com/transparency | Monthly |

---

## Key Publications

- **Core Views on AI Safety** (2023-03-08) - Foundational safety philosophy
- **Responsible Scaling Policy** (2023-09-19) - RSP framework introduction
- **Constitutional Classifiers** (2025-02-03) - Jailbreak defense research
- **Alignment Faking** (2024-12-18) - Research on models faking alignment
- **Claude's Constitution** (2025-01-22) - Full constitutional document

---

## Integration with CORE_AUTOMATION

This provider module integrates with the central automation engine:

```
AI SAFETY/
├── CORE_AUTOMATION/
│   ├── rules/          ← Provider rules feed into
│   ├── thresholds/     ← Provider thresholds feed into
│   ├── actions/        ← Provider actions feed into
│   └── engines/        ← Orchestration engine
└── PROVIDERS/
    └── ANTHROPIC/      ← This directory
```

---

## Quick Start

1. **Review the Schema**: Start with `ANTHROPIC_AI_SAFETY_SCHEMA.json` for the complete data model
2. **Understand the Protocol**: Read `SAFETY_PROTOCOL.md` for rules and procedures
3. **Configure Thresholds**: Adjust `THRESHOLDS.json` for your monitoring needs
4. **Map Actions**: Use `ACTIONS_MATRIX.json` to understand trigger-action relationships
5. **Generate Reports**: Use `REPORT_TEMPLATE.md` for structured reporting

---

## References

- [Anthropic Research](https://www.anthropic.com/research)
- [Core Views on AI Safety](https://www.anthropic.com/news/core-views-on-ai-safety)
- [Responsible Scaling Policy](https://www.anthropic.com/news/anthropics-responsible-scaling-policy)
- [Constitutional Classifiers](https://www.anthropic.com/research/constitutional-classifiers)
- [Alignment Faking Research](https://www.anthropic.com/research/alignment-faking)
- [Claude's Constitution](https://www.anthropic.com/constitution)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-30 | Initial Anthropic safety protocol creation |

---

*This protocol is part of the multi-provider AI Safety automation framework.*
