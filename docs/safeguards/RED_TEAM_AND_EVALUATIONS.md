# Red-Teaming and Deep-Dive Evaluations

**Document type:** Policy / process  
**Purpose:** Define immediate and ongoing red-teaming and third-party evaluations to stress refusal behavior and detection pipelines.  
**Related:** [SAFEGUARDS_REPORT.md](SAFEGUARDS_REPORT.md), [MONITORING_AND_ENFORCEMENT_SLAS.md](MONITORING_AND_ENFORCEMENT_SLAS.md)

---

## 1. Objectives

- **Refusal behavior:** Ensure the model/system consistently refuses to produce harmful, policy-violating, or unsafe outputs when prompted (including adversarial or jailbreak-style prompts).
- **Detection pipelines:** Stress-test detection of jailbreaks, misuse, and policy violations so that alerts and blocking perform to defined SLAs (see [MONITORING_AND_ENFORCEMENT_SLAS.md](MONITORING_AND_ENFORCEMENT_SLAS.md)).

---

## 2. Human Expert Red Teams

### Composition

- **Internal:** Security and safety engineers with access to system design and logs; at least one domain expert for high-stakes use cases (e.g. code generation, API behavior).
- **External (when required):** Independent red-team or penetration-testing firm for Critical capability level or major releases; selected for independence and relevant domain experience.

### Scope

- **Refusal behavior:** Prompts designed to elicit harmful content, bypass refusals, or obtain unsafe instructions (e.g. weaponization, self-harm, illegal activity, credential abuse).
- **Jailbreak attempts:** Known and novel jailbreak techniques (prompt injection, role-play, encoding, multi-turn) applied to in-scope models/APIs.
- **Misuse scenarios:** Abuse cases (e.g. bulk generation of unsafe code, automation of policy violations, data exfiltration via model or tools).

### Cadence

- **Pre-release:** Full red-team run before each major release that changes model behavior, safety layers, or detection.
- **Quarterly:** Scheduled red-team cycle; scope includes new threat intel and prior findings verification.
- **Ad hoc after incidents:** Focused red-team or deep-dive within 2 weeks of a confirmed jailbreak, misuse, or safety incident.

### Deliverables

- **Findings report:** Each run produces a report with scenario, outcome, severity (Critical/High/Medium/Low), and reproducibility steps.
- **Remediation tracking:** Findings are tracked to closure; critical and high must be remediated or risk-accepted by governance before release (see [DEPLOYMENT_GATES_AND_GOVERNANCE.md](DEPLOYMENT_GATES_AND_GOVERNANCE.md)).

---

## 3. Domain Third-Party Testing

### When required

- Systems at or near **Critical** capability threshold (per [AI_SAFETY_INTEGRATION.md](../AI_SAFETY_INTEGRATION.md) and [DEPLOYMENT_GATES_AND_GOVERNANCE.md](DEPLOYMENT_GATES_AND_GOVERNANCE.md)).
- Before **major release** that significantly expands capability or exposure.
- When **SAG or Board SSC** mandates independent validation.

### Domains

- **Security:** Penetration testing, jailbreak and abuse testing, tool/API misuse.
- **Safety:** Refusal robustness, harmful content elicitation, edge cases.
- **Domain experts:** As needed for high-stakes verticals (e.g. codegen, legal/medical if applicable).

### Selection and independence

- Third-party selected via defined procurement or engagement process; conflict-of-interest check.
- Independence: tester must not be responsible for building the system under test; separate reporting line from product/engineering for the test report.
- Output: formal test report with scope, method, findings, and pass/fail against agreed criteria; findings integrated into Safeguards Report efficacy tests where applicable.

---

## 4. Refusal-Behavior Tests

### Scenarios that must be refused

- Requests for harmful content (violence, self-harm, illegal activity, non-consensual use).
- Requests to bypass safety or “act as” an unrestricted system.
- Requests for credentials, secrets, or steps to compromise systems.
- Requests that would lead to unsafe code (e.g. eval on user input, hardcoded secrets, auth bypass) when the system is used for code generation or advice.

### Pass criteria

- **No harmful output:** System does not produce content that meets policy-defined “harmful” criteria.
- **Clear refusal:** When refusing, response is a clear refusal (no acquiescence in follow-up without legitimate context).
- **Consistency:** Repeated and slightly rephrased prompts still result in refusal (sample-based; e.g. ≥98% in test set).

### Link to Safeguards Report

- Refusal tests map to **efficacy tests** for controls CTRL-2a, CTRL-2b in [SAFEGUARDS_REPORT.md](SAFEGUARDS_REPORT.md) (path P2). Results feed residual-risk and SAG review.

---

## 5. Detection-Pipeline Tests

### Scenarios that must be detected

- **Jailbreaks:** Reproducible prompts or sequences that bypass refusal/safety; detection may be inline (block request) or post-hoc (alert and trace).
- **Policy violations:** Outputs that violate content or use policy; abuse patterns (e.g. bulk harmful generation, scraping).
- **Anomaly:** Unusual request volume, error spikes, or patterns correlated with known attacks.

### Metrics

- **Detection rate:** Proportion of known jailbreak/misuse scenarios that trigger an alert or block (target per [MONITORING_AND_ENFORCEMENT_SLAS.md](MONITORING_AND_ENFORCEMENT_SLAS.md)).
- **False positive rate:** Proportion of benign traffic that triggers alert/block (target: acceptable operational burden, e.g. &lt;5% where measured).
- **Time-to-alert:** Latency from event to alert (targets in SLA document).

### Link to monitoring SLAs

- Detection targets and time-to-alert are specified in [MONITORING_AND_ENFORCEMENT_SLAS.md](MONITORING_AND_ENFORCEMENT_SLAS.md). Failures in detection-pipeline tests may trigger SLA breach process and escalation.

---

## 6. Execution and Scheduling

### Immediate actions (one-time)

- **Run initial red-team:** Human expert red team executes one full cycle against current refusal behavior and detection pipelines; report within 4 weeks of plan approval.
- **Deep-dive on detection:** Focused evaluation of detection pipeline (jailbreak, policy violation, anomaly); document coverage gaps and recommend detector/rule changes.

### Recurring

- **Quarterly red-team:** Per cadence above; owner: Safety/Security lead.
- **Pre-release red-team:** Per release process; owner: Release or Product lead with Safety sign-off.
- **Ad hoc after incident:** Triggered by confirmed jailbreak or misuse; owner: Incident lead with Safety participation.

### Owners and deadlines

| Activity | Owner | Deadline / cadence |
|----------|--------|---------------------|
| Initial red-team run | Safety/Security lead | Within 4 weeks of plan approval |
| Deep-dive detection evaluation | Safety/Security lead | Within 6 weeks of plan approval |
| Quarterly red-team | Safety/Security lead | Every quarter; report within 2 weeks of run |
| Pre-release red-team | Release/Product + Safety | Before each major release |
| Post-incident red-team | Incident + Safety | Within 2 weeks of incident closure |
| Third-party testing (when required) | Safety + Procurement | Per governance; report before go/no-go |

---

**Classification:** AI Safety / Red team  
**Owner:** Safety/Security lead  
**Next review:** After first red-team cycle; then per governance cadence.
