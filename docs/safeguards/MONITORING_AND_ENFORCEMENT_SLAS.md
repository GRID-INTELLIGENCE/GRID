# Monitoring and Enforcement SLAs

**Document type:** Policy / operational  
**Purpose:** Define monitoring, automatic blocking, human escalation, ban/trace mechanisms, and time-to-patch for jailbreaks with measurable commitments.  
**Related:** [SAFEGUARDS_REPORT.md](SAFEGUARDS_REPORT.md), [RED_TEAM_AND_EVALUATIONS.md](RED_TEAM_AND_EVALUATIONS.md), [SAFETY_DEPLOYMENT_GUIDE.md](../SAFETY_DEPLOYMENT_GUIDE.md)

---

## 1. Auxiliary Detectors

| Detector | Purpose | Where it runs | Data sources | Feeds into |
|----------|---------|----------------|--------------|------------|
| Jailbreak attempt | Detect prompts or patterns aimed at bypassing refusal/safety | Inline (request path) and/or batch (log analysis) | Request content, response content, metadata | Auto-block; escalation; ban/trace |
| Policy violation | Detect outputs that violate content or use policy | Inline and batch | Model/output content; tool calls | Auto-block; escalation; alert |
| Abuse pattern | Detect bulk abuse, scraping, or automated misuse | Batch; real-time aggregations | Request rate, user/session, endpoint | Auto-block (rate); escalation; ban |
| Anomaly | Unusual volume, errors, or sequences | Batch; optional real-time | Logs, metrics, traces | Escalation; triage |
| Config/server violation | Unsafe server or config activation | Inline at config apply / server start | Config files; denylist engine | Block startup; violation log; alert |

Implementation references: safety tracer ([AI_SAFETY_INTEGRATION.md](../AI_SAFETY_INTEGRATION.md)), denylist manager and violation detection ([SAFETY_DEPLOYMENT_GUIDE.md](../SAFETY_DEPLOYMENT_GUIDE.md)), network and security monitoring ([security/](../../security/)).

---

## 2. Automatic Blocking

### Conditions that trigger auto-block

- **Jailbreak:** Detector confidence above defined threshold (e.g. known jailbreak pattern or classifier score &gt; threshold).
- **Policy violation:** Output or tool call classified as policy-violating above threshold.
- **Abuse:** Rate or pattern exceeds limit (e.g. requests per minute per user/session).
- **Config violation:** Denylisted server or unsafe config change attempted; block applied at config/startup layer.

### Scope of block

- **User/session:** Block applies to the user ID and/or session ID associated with the request.
- **Endpoint:** Specific API or tool endpoint may be temporarily blocked for that caller.
- **Tenant:** In multi-tenant setups, block may apply at tenant level per policy.

### Override process

- Overrides (unblock or allow exception) require designated authority (e.g. Safety lead or Security lead).
- Every override is logged: who, when, reason, scope; reviewable by SAG/audit.
- No override for Critical-severity blocks without governance (SAG or Board SSC) approval where policy requires.

---

## 3. Human Escalation Channels

### Triggers

- **Detector alert:** Any detector raises alert above severity threshold.
- **User report:** User or internal report of harmful output, jailbreak, or misuse.
- **Anomaly:** Anomaly detector or operational runbook flags unusual activity.
- **Incident:** Confirmed or suspected safety/security incident (see [AI_SAFETY_INCIDENT_REPORT_2026_02_02.md](../AI_SAFETY_INCIDENT_REPORT_2026_02_02.md) for taxonomy).

### Routing

- **Critical:** To Security and Safety immediately; SAG notified; Board SSC if policy triggers.
- **High:** To Security/Safety on-call; triage within SLA.
- **Medium/Low:** To safety queue; triage within SLA; may be batched.

### SLAs: time-to-triage and time-to-initial-response

| Severity | Time to triage | Time to initial response |
|----------|----------------|---------------------------|
| Critical | 1 hour | 2 hours |
| High | 4 hours | 8 hours |
| Medium | 24 hours | 48 hours |
| Low | 72 hours | 5 business days |

*Initial response* = human acknowledgment and next-step (investigation, block, or risk-accept). *Triage* = severity confirmed and routed.

---

## 4. Ban and Trace Mechanisms

### Ban criteria and authority

- **Criteria:** Repeated policy violation, confirmed jailbreak or abuse, or one-off Critical misuse as defined by policy.
- **Authority:** Safety or Security lead can impose ban; Critical or user-facing bans should be documented and reviewable. Board SSC can mandate or revoke bans.

### What is banned

- **User ID / API key:** Revoke or disable access for the identity.
- **Session:** Invalidate session; may re-auth with same identity subject to policy.
- **IP or client (where applicable):** Temporary or permanent block at network/client level per policy.

### Trace: what is logged and retention

- **Logged:** Request and response content (or hashes/redacted where required by policy); user/session/endpoint identifiers; timestamp; detector results; block/allow decision.
- **Retention:** Minimum 90 days for safety-relevant events; longer if required for incident review or legal. Retention policy documented and auditable.
- **Use:** Trace supports incident review, SAG review, and efficacy analysis (e.g. detection rate, time-to-detect). Access to trace data is restricted and logged.

---

## 5. Time-to-Patch for Jailbreaks

### Definition of jailbreak (for this document)

A **jailbreak** is a reproducible method (prompt, sequence, or tool use) that causes the system to bypass refusal or safety controls and produce output or behavior that violates policy. Severity: **Critical** if high impact (e.g. harmful content, credential abuse); **High** if moderate impact or limited scope.

### SLA

| Severity | Patch or mitigation target |
|----------|-----------------------------|
| Critical jailbreak | 7 calendar days |
| High jailbreak | 14 calendar days |

*Patch or mitigation* = deployment of a fix or effective mitigation (e.g. block pattern, detector update) that prevents or detects the jailbreak; verified by test or red-team.

### Process

1. **Detect:** Via detector, red-team, or report.
2. **Assess severity:** Critical vs High per definition above.
3. **Assign:** Owner (Safety/Engineering) and deadline per SLA.
4. **Patch/mitigate:** Implement fix or mitigation; add test to regression set.
5. **Verify:** Re-run scenario; confirm blocked or detected.
6. **Communicate:** Notify SAG and stakeholders; update Safeguards Report if residual risk changes.

---

## 6. SLA Summary Table

| Metric | Target | Measurement method | Owner |
|--------|--------|--------------------|--------|
| Time to triage (Critical) | 1 hour | Timestamp from alert to triage complete | On-call Security/Safety |
| Time to initial response (Critical) | 2 hours | Timestamp from alert to first human response | On-call Security/Safety |
| Time to triage (High) | 4 hours | As above | Safety queue owner |
| Time to initial response (High) | 8 hours | As above | Safety queue owner |
| Critical jailbreak time-to-patch | 7 days | From confirm to patch verified | Safety/Engineering lead |
| High jailbreak time-to-patch | 14 days | As above | Safety/Engineering lead |
| Trace retention | ≥ 90 days | Audit of log retention config | Security/Compliance |
| Detector coverage (known jailbreaks) | Per Safeguards Report efficacy tests | Red-team and detection-pipeline tests | Safety lead |

---

**Classification:** AI Safety / Operations  
**Owner:** Safety lead; Operations for runbooks and tooling  
**Next review:** Quarterly; after any SLA breach or major incident.
