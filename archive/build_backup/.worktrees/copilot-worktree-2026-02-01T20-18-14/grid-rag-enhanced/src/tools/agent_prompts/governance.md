# Governance & Audit

Governance rules, audit patterns, and safety procedures for system evolution.

## Change Metadata Requirements

Every change must include `change_metadata.json` with:

```json
{
  "change_id": "CHANGE-1",
  "author": "author_name",
  "owner": "owner_name",
  "timestamp": "2025-01-08T10:00:00Z",
  "rationale": "Change rationale and motivation",
  "impact": "Impact description (modules affected, breaking changes, etc.)",
  "tests_run": [
    "test_module.py::test_function",
    "test_integration.py::test_integration"
  ],
  "artifacts": [
    "path/to/artifact1",
    "path/to/artifact2"
  ],
  "approvals": [
    {
      "approver": "approver_name",
      "timestamp": "2025-01-08T11:00:00Z",
      "rationale": "Approval rationale"
    }
  ],
  "rollback_plan": "Rollback steps",
  "risk_level": "low|medium|high|critical"
}
```

## Audit Log Format

The orchestrator writes an `audit.log` for each `compose_section()` invocation:

```json
{
  "timestamp": "2025-01-08T10:00:00Z",
  "operation": "compose_section",
  "section_spec": {
    "name": "Intro",
    "bars": 32
  },
  "modules_loaded": [
    {
      "name": "kick",
      "version": "1.0.0",
      "interface_schema": "contracts/kick.json"
    }
  ],
  "manifest_version": "1.2.0",
  "seed_used": 12345,
  "result": "success|failure",
  "duration_ms": 123,
  "metadata": {}
}
```

## Approval Workflows

### Standard Change Approval

1. **Author** creates PR with change metadata
2. **Owner** reviews and approves
3. **CI** validates (tests, contracts, coverage)
4. **Merge** after all checks pass

### High-Risk Change Approval

1. **Author** creates PR with change metadata
2. **Owner** + **Security Lead** review
3. **CI** validates + security scan
4. **Canary** deployment (5% traffic)
5. **Monitor** for 60 minutes
6. **Promote** or **Rollback** based on metrics
7. **Merge** after approval

### Critical Change Approval

1. **Author** creates PR with change metadata
2. **Owner** + **Security Lead** + **Architecture Lead** review
3. **CI** validates + security scan + architecture review
4. **Staging** deployment
5. **Integration** testing in staging
6. **Canary** deployment (1% traffic)
7. **Monitor** for 24 hours
8. **Gradual rollout** (1% → 5% → 25% → 100%)
9. **Merge** after full approval

## Contract Change Process

Contract changes require:

1. **Consumer Impact Assessment**
   - List all consumers of the contract
   - Assess breaking vs. non-breaking changes
   - Provide migration path if breaking

2. **Compatibility Report**
   ```json
   {
     "contract": "contracts/openapi.yaml#/components/schemas/BassSpec",
     "change_type": "breaking|non_breaking|additive",
     "consumers": [
       {
         "module": "module_name",
         "impact": "high|medium|low",
         "migration_required": true
       }
     ],
     "migration_guide": "Migration steps"
   }
   ```

3. **Contract Tests**
   - Update consumer-driven contract tests
   - Add backward compatibility tests (if applicable)
   - Ensure all tests pass

4. **Version Bump**
   - Breaking changes: MAJOR version bump
   - Non-breaking additions: MINOR version bump
   - Bug fixes: PATCH version bump

## Canary Deployment Strategy

### Configuration

```json
{
  "canary_strategy": {
    "enabled": true,
    "traffic_percentage": 5,
    "monitoring_duration_minutes": 60,
    "rollback_thresholds": {
      "error_rate": 0.01,
      "latency_p95_ms": 1000,
      "throughput_degradation": 0.1
    },
    "promotion_criteria": {
      "error_rate": "<0.005",
      "latency_p95_ms": "<500",
      "satisfaction_score": ">0.95"
    }
  }
}
```

### Rollback Triggers

Automatic rollback if:
- Error rate > 1%
- P95 latency > 1000ms
- Throughput degradation > 10%
- Model drift score > 0.3 (for ML changes)
- Any critical alert

## Model Update Safeguards

For adaptive learning modules (Real-Time Adapter, Neural Pattern Detector):

### Requirements

1. **Human Approval Required**
   - All model updates require explicit human approval
   - Approval must include rationale and risk assessment

2. **Freeze Window**
   - 48-hour observation window after model update
   - No further model updates during freeze window
   - Automated monitoring with rollback triggers

3. **Immutable Artifacts**
   - Training datasets stored as immutable artifacts
   - Model weights versioned and stored
   - Provenance metadata required:
     ```json
     {
       "model_id": "model_v1.2.0",
       "training_dataset": "dataset_v1.0.0",
       "training_config": "config_v1.1.0",
       "training_timestamp": "2025-01-08T10:00:00Z",
       "metrics": {
         "accuracy": 0.95,
         "f1_score": 0.92
       }
     }
     ```

4. **Deterministic Test Harnesses**
   - All tests must use seeded RNGs
   - Tests must be reproducible
   - CI must run tests with fixed seeds

## Security Checklist

Pre-deploy security checklist:

- [ ] No secrets in code or config files
- [ ] Security scan passed (Snyk, OWASP, etc.)
- [ ] Dependencies updated and scanned
- [ ] Input validation for all user inputs
- [ ] Output sanitization for all outputs
- [ ] Authentication/authorization verified
- [ ] Rate limiting configured (if applicable)
- [ ] Encryption in transit and at rest
- [ ] GDPR/privacy compliance (if applicable)

## Privacy Checklist

Pre-deploy privacy checklist:

- [ ] No PII in logs or metrics
- [ ] Data retention policies followed
- [ ] User consent obtained (if applicable)
- [ ] Data anonymization applied (if applicable)
- [ ] Privacy policy updated (if applicable)

## Audit Checklist

Pre-deploy audit checklist:

- [ ] Change metadata recorded
- [ ] Approval trail documented
- [ ] Rollback plan verified
- [ ] Test results archived
- [ ] Artifacts versioned
- [ ] Documentation updated

## Governance Document Template

```markdown
# Governance Document - CHANGE-1

## Change Summary
- **ID**: CHANGE-1
- **Author**: author_name
- **Owner**: owner_name
- **Risk Level**: medium
- **Type**: feature|bugfix|refactor|security

## Pre-Deploy Checklist

### Security
- [ ] Security scan passed
- [ ] No secrets in code
- [ ] Dependencies updated

### Privacy
- [ ] No PII in logs
- [ ] Data retention followed

### Audit
- [ ] Change metadata recorded
- [ ] Approval trail documented

## Approval Template

**Approver**: _______________
**Timestamp**: _______________
**Rationale**: _______________
**Signature**: _______________

## Canary Strategy
- Traffic percentage: 5%
- Monitoring duration: 60 minutes
- Rollback thresholds: [see canary config]

## Rollback Plan
1. Revert commit: `git revert <commit_hash>`
2. Re-deploy previous artifact
3. Verify system health
```
