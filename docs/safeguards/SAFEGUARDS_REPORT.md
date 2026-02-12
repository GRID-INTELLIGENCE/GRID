# Safeguards Report

**Document type:** Safeguards Report (SAG review)  
**Scope:** GRID, server denylist, MCP/config, and model-facing or infrastructure AI components  
**Version:** 1.0  
**Status:** Draft — pending SAG review  
**Related:** [AI_SAFETY_INTEGRATION.md](../AI_SAFETY_INTEGRATION.md), [AI_SAFETY_INCIDENT_REPORT_2026_02_02.md](../AI_SAFETY_INCIDENT_REPORT_2026_02_02.md)

---

## 1. Executive Summary

This report maps plausible paths-to-harm for the in-scope AI systems to specific controls and measurable efficacy tests, provides a residual-risk assessment, and states limitations. It is written for review by the Safeguards Advisory Group (SAG).

**Scope:** Systems and capabilities in scope include GRID (Geometric Resonance Intelligence Driver), the server denylist (configuration sanitizer), MCP and related configuration surfaces, and any model-facing or infrastructure components that can execute code, access networks, or influence system behavior.

**Paths-to-harm summary:** Six primary paths are identified: misuse via API/code generation, jailbreak/refusal bypass, configuration and infrastructure misuse, data exfiltration, unsafe code execution, and credential or secret exposure. Severity is aligned with existing bands (Critical, High, Medium, Low) per [AI_SAFETY_INTEGRATION.md](../AI_SAFETY_INTEGRATION.md).

**Overall residual risk:** With current controls (denylist, safety tracer, network access control, logging, and remediation of known critical code issues), residual risk is **moderate** for High/Critical paths until third-party validation and full hardening are complete. Low/Medium paths are assessed as acceptable for current deployment scope.

**SAG review status:** Pending. Section 7 is reserved for SAG sign-off.

---

## 2. Path-to-Harm Taxonomy

| Path ID | Path (short name) | Description | Capability level / trigger conditions | Severity |
|---------|-------------------|-------------|---------------------------------------|----------|
| P1 | Misuse via API/codegen | API or code-generation features used to produce harmful outputs, automate abuse, or bypass intended use | Model or API exposed; no or weak output filtering | High |
| P2 | Jailbreak/refusal bypass | User or automated attack elicits harmful or policy-violating output by bypassing refusal/safety | Model exposed to adversarial or jailbreak prompts | Critical |
| P3 | Config/infra misuse | Unsafe or malicious server/config enabled; resource exhaustion; dependency or startup failures exploited | MCP/config or server lifecycle under attacker control | High |
| P4 | Data exfiltration | Sensitive data (credentials, PII, IP) exported via model output, tools, or persistent channels | Tools or output channels allow external write or network | Critical |
| P5 | Unsafe code execution | Arbitrary or dangerous code execution (e.g. eval, shell injection, unsafe deserialization) | Code execution path exists and is reachable | Critical |
| P6 | Credential/secret exposure | Hardcoded secrets, secrets in version control, or credential leakage via logs/errors | Secrets in code, env, or logs | Critical |

Severity bands (aligned with [AI_SAFETY_INTEGRATION.md](../AI_SAFETY_INTEGRATION.md)): **Critical** (score 0.0–0.2), **High** (0.2–0.4), **Medium** (0.4–0.7), **Low** (0.7–1.0).

---

## 3. Control Mapping

For each path, controls and implementation references:

| Path ID | Controls | Control ID | Implementation reference |
|---------|----------|------------|---------------------------|
| P1 | Output filtering; usage and rate limits; access control | CTRL-1a, CTRL-1b | Safety tracer; denylist; API/auth layer |
| P2 | Refusal/safety training; input filtering; jailbreak detection; monitoring | CTRL-2a, CTRL-2b, CTRL-2c | Model policy; detectors (see [RED_TEAM_AND_EVALUATIONS.md](RED_TEAM_AND_EVALUATIONS.md)); safety tracer |
| P3 | Server denylist; config sanitization; dependency and startup checks | CTRL-3a, CTRL-3b | [SERVER_DENYLIST_SYSTEM.md](../SERVER_DENYLIST_SYSTEM.md); [AI_SAFETY_INTEGRATION.md](../AI_SAFETY_INTEGRATION.md); apply_denylist drive-wide |
| P4 | Network allow-list; no persistent unaudited output channels; tool restrictions | CTRL-4a, CTRL-4b | [network_access_control.yaml](../../security/network_access_control.yaml); [SYSTEM_HARDENING.md](SYSTEM_HARDENING.md) |
| P5 | Remove eval/exec in hot paths; sandboxing; least-privilege execution | CTRL-5a, CTRL-5b | [SECURITY_REMEDIATION_PLAN.md](../SECURITY_REMEDIATION_PLAN.md); [SYSTEM_HARDENING.md](SYSTEM_HARDENING.md); boundaries |
| P6 | Secret scanning; env-based secrets; no secrets in logs; credential rotation | CTRL-6a, CTRL-6b | [AI_SAFETY_INCIDENT_REPORT_2026_02_02.md](../AI_SAFETY_INCIDENT_REPORT_2026_02_02.md) Gap 1; SECURITY_FIXES_COMPLETE |

---

## 4. Efficacy Tests

For each control (or control set per path), measurable tests:

| Control(s) | Test description | Pass criteria | Test frequency |
|------------|------------------|---------------|----------------|
| CTRL-1a, CTRL-1b | Stimulate API/codegen with policy-violating requests; measure block rate and correct refusal | Block or refuse ≥95%; no harmful output in sample | Pre-release; quarterly |
| CTRL-2a, CTRL-2b, CTRL-2c | Run refusal and jailbreak scenario set (see [RED_TEAM_AND_EVALUATIONS.md](RED_TEAM_AND_EVALUATIONS.md)); measure refusal rate and detector alerts | Refusal ≥98% on refusal set; known jailbreaks detected per SLA | Pre-release; quarterly; ad hoc after incidents |
| CTRL-3a, CTRL-3b | Attempt to enable denylisted server or load unsafe config; measure denial and logging | Denied 100%; event logged with correct reason | Pre-release; quarterly |
| CTRL-4a, CTRL-4b | Attempt outbound exfil to blocked domain; attempt unapproved persistent write | Request blocked; no unaudited persistent channel used | Pre-release; quarterly |
| CTRL-5a, CTRL-5b | Attempt eval/shell injection and unsafe deserialization in code paths | All attempts blocked or sandboxed; no arbitrary execution | Pre-release; after code changes to execution path |
| CTRL-6a, CTRL-6b | Scan codebase and logs for secret patterns; verify no hardcoded secrets in build | Zero hardcoded secrets; no secrets in log sample | Pre-commit / CI; quarterly |

---

## 5. Residual Risk Assessment

| Path / band | Residual risk after controls | Justification |
|-------------|------------------------------|---------------|
| P1 | Moderate | Output filtering and rate limits in place; no third-party stress test yet. Accepted for current scope with monitoring. |
| P2 | Moderate–High | Refusal and detection depend on model and detectors; red-team and third-party validation pending. Mitigated by monitoring and time-to-patch (see [MONITORING_AND_ENFORCEMENT_SLAS.md](MONITORING_AND_ENFORCEMENT_SLAS.md)). |
| P3 | Low | Denylist and config sanitization operational; escalation paths defined. Residual: misconfiguration or new server types. |
| P4 | Moderate | Network default-deny and tool limits reduce exfil; persistent channels under review (System Hardening). |
| P5 | Moderate | Critical eval/shell patterns remediated per incident report; sandboxing and least-privilege in progress. |
| P6 | Low | Secret management and rotation procedures in place; scanning in CI. Residual: legacy or new leakage vectors. |

**Overall residual risk statement:** For the current deployment scope, residual risk is **moderate** for paths P1, P2, P4, P5 until (1) third-party or SAG-validated efficacy tests are completed and (2) system hardening (sandboxing, persistent channels, human approval) is fully implemented. Paths P3 and P6 are assessed as **low** residual risk with continued monitoring. Systems at or near Critical capability threshold must not deploy until Critical-level safeguards are specified and validated per [DEPLOYMENT_GATES_AND_GOVERNANCE.md](DEPLOYMENT_GATES_AND_GOVERNANCE.md).

---

## 6. Limitations

- **Third-party audit:** No independent third-party safety or security audit has been performed yet. Efficacy claims are based on internal tests and design.
- **Scope:** This report applies to the systems and deployment contexts described above; it does not cover every possible integration or future capability.
- **Detection coverage:** Jailbreak and misuse detection may not cover novel attack forms; detection pipelines require ongoing tuning and red-team feedback.
- **Assumptions:** Controls are maintained as documented; configuration (denylist, network rules) is not weakened without change control and SAG awareness where applicable.
- **Evidence:** Some residual-risk justifications rely on remediation plans and design documents; full implementation and verification of hardening are in progress.

---

## 7. SAG Review

*To be completed when SAG reviews this report.*

| Field | Value |
|-------|--------|
| Review date | |
| SAG findings | |
| Approval / conditions | |
| Sign-off | |

---

**Classification:** AI Safety / Safeguards  
**Owner:** AI Safety Team  
**Next review:** After SAG review; then per governance cadence (see [DEPLOYMENT_GATES_AND_GOVERNANCE.md](DEPLOYMENT_GATES_AND_GOVERNANCE.md)).
