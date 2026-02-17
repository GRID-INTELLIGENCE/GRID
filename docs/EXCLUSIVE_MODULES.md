# GRID Exclusive Modules

**Last Updated**: December 17, 2025
**Test Status**: ✅ 82 passed, 1 skipped (0.90s)

---

## Overview

Certain GRID modules are designated as **Exclusive/Proprietary** and are not covered by the project's open-source license. These modules require formal business consultation and licensing before access is granted.

---

## Exclusive Module: GRID-BET

### Description

**GRID-BET** is a Financial Intelligence & Risk Management module providing:

- Multi-factor risk assessment (VaR, CVaR, Sharpe, Sortino, Max Drawdown)
- Investment opportunity evaluation with weighted scoring
- Portfolio cost optimization and tax-loss harvesting
- Monte Carlo simulation and stress testing
- Strategic alliance and M&A opportunity detection
- Financial entity extraction (NER)

### Why Exclusive?

This module represents significant R&D investment in financial intelligence and contains proprietary algorithms for:

1. **Risk Quantification** - Advanced multi-factor risk models
2. **Decision Intelligence** - Weighted scoring with evidence collection
3. **Cost Optimization** - Tax-efficient portfolio management
4. **Scenario Simulation** - Realistic market stress testing

### Access Requirements

| Requirement | Description |
|-------------|-------------|
| **Formal Meeting** | Real human conversation with authorized personnel |
| **Use Case Review** | Documentation of intended application |
| **Licensing Agreement** | Signed contract covering terms and scope |
| **Access Token** | Provisioned only after consultation completion |

### What Is NOT Acceptable

❌ AI-assisted terminal interactions as "consultation"
❌ Automated integration without human review
❌ Sharing access tokens or authorization files
❌ Copying code to other repositories
❌ Exposing through public APIs without agreement

### What IS Required

✅ Scheduled meeting with project maintainer
✅ Real-time human conversation (video/phone/in-person)
✅ Written agreement signed by authorized parties
✅ Documented use case and scope
✅ Ongoing compliance with license terms

---

## Requesting Access

### Step 1: Initial Contact

Contact the project maintainer through official channels to express interest in GRID-BET licensing.

### Step 2: Prepare Documentation

Before the consultation, prepare:

- Organization name and legal entity details
- Intended use case (internal, commercial, research)
- Integration requirements and timeline
- Technical environment details
- Support and maintenance expectations

### Step 3: Schedule Consultation

A formal meeting will be scheduled to discuss:

- Your specific requirements
- Licensing options and terms
- Technical integration approach
- Pricing and payment terms
- Timeline and deliverables

### Step 4: Agreement

After successful consultation:

1. License agreement prepared and reviewed
2. Terms finalized and signed
3. Access token generated and provisioned
4. Technical onboarding scheduled

### Step 5: Ongoing Relationship

- Regular check-ins as needed
- Support for integration questions
- License renewal process
- Feature request discussions

---

## Technical Protection Measures

The GRID-BET module is protected by multiple layers:

### 1. Git Exclusion

The module is listed in `.gitignore` to prevent accidental commits to public repositories:

```gitignore
# GRID-BET: Exclusive Financial Intelligence Module
circuits/bet/
grid/bet/
circuits/cli/commands/bet.py
tests/fixtures/bet/
tests/unit/test_bet_*.py
```

### 2. Access Guard

The CLI and programmatic access require authorization:

```python
from grid.bet.access_guard import require_access

# This will check for valid authorization
require_access()  # Raises AuthorizationError if not authorized
```

### 3. Git Hooks

Pre-commit hooks prevent accidental commits of exclusive modules:

```bash
# In .git/hooks/pre-commit
# Checks for circuits/bet/ in staged files
```

### 4. Audit Logging

All access attempts (successful or not) are logged to:
- `~/.grid/logs/bet-access.log`

---

## Development Mode

For internal development, the access guard can be bypassed:

```bash
export GRID_BET_DEV_MODE=1  # Enables development bypass (default)
export GRID_BET_DEV_MODE=0  # Enforces authorization check
```

⚠️ **Warning**: Development mode must NOT be used in production or distribution.

---

## Frequently Asked Questions

### Q: Can I use GRID-BET in my open-source project?

A: No. GRID-BET is not open-source and cannot be included in open-source projects without a specific licensing agreement.

### Q: Is there a trial period?

A: Trial access may be discussed during consultation, subject to terms.

### Q: Can I modify the code?

A: Modification rights depend on your license type. Discuss during consultation.

### Q: What if I find a bug?

A: Licensed users receive support. Report issues through the designated channel.

### Q: Can multiple team members use one license?

A: Team licensing is available. Discuss your team size during consultation.

---

## Contact

For licensing inquiries, please contact the project maintainer through official channels.

**Note**: Unsolicited access attempts are logged and may result in IP restrictions.
