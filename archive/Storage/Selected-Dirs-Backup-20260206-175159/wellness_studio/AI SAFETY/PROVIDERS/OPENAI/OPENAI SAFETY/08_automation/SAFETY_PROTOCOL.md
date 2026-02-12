# AI Safety Protocol — Rules, Triggers, Thresholds, and Remediation (OpenAI)

## 1) Purpose
This protocol defines an **automated, agentic safety system** for monitoring OpenAI safety sources, evaluating safety signals, and triggering actions. It is **rule‑based**, **threshold‑oriented**, and **nuance‑aware** to avoid overreaction while preserving safety.

---

## 2) Operating Principles
- **Safety‑first:** Prevent harm and minimize risk.
- **User‑centric:** Emphasize transparency, rights, and remediation.
- **Evidence‑based:** Tie actions to documented sources and change detection.
- **Nuance‑aware:** Apply proportional actions, avoid false positives.
- **Auditability:** Log every decision and rationale.

---

## 3) Safety Taxonomy (Anchors)
- Safe Use & Boundaries
- Evaluation & Compliance
- Deception & Misalignment
- Instruction Hierarchy
- Reliability & Hallucinations
- Transparency & Accountability
- Privacy & Personal Data
- System‑Level Safeguards
- Preparedness & Frontier Risk Controls

---

## 4) Safety Signals (Inputs)
**Primary sources:**  
- Research Index  
- Safety Evaluations Hub  
- Preparedness Framework  
- System Cards  
- Safety & Alignment pages  

**Signal types:**  
- New safety publication  
- Updated system card  
- Evaluation metric change  
- New risk category or capability  
- Policy/Guidance updates  
- Change in known safety boundaries  

---

## 5) Severity Levels (Threshold‑Driven)
| Level | Description | Action Bias |
|------|-------------|-------------|
| **INFO** | Minor update, low impact | Log + report summary |
| **WARN** | Moderate change, potential user impact | Notify + update playbook |
| **HIGH** | Significant safety change or new risk | Escalate + require review |
| **CRITICAL** | High‑risk capability or safety regression | Immediate escalation + mitigation |

---

## 6) Rule Engine (Core Rules)

### Rule Group A — Source Update Detection
**Trigger:** New or changed OpenAI safety item  
**Threshold:** Any diff detected  
**Action:** Log change + summarize + flag severity based on content keywords  

**Keywords raising severity:**  
- “scheming”, “monitorability”, “jailbreak”, “misalignment”, “catastrophic”, “preparedness”, “high risk”, “evaluation update”, “mitigation failure”

---

### Rule Group B — Safety Evaluation Shifts
**Trigger:** Safety Evaluation Hub updates  
**Threshold:** Detected changes in evaluation sections  
**Actions:**  
- Log and classify changes  
- Create an “Evaluation Update” entry  
- If terms indicate decline or risk: escalate to **WARN/HIGH**

---

### Rule Group C — System Card Updates
**Trigger:** New system card or addendum  
**Threshold:** Any change  
**Actions:**  
- Map to safety taxonomy  
- Update user rights impacts  
- Generate a scenario addendum if relevant  
- Escalate if new risk area is introduced  

---

### Rule Group D — Preparedness Framework Changes
**Trigger:** Framework update  
**Threshold:** Any revision or new category  
**Actions:**  
- Re‑evaluate risk thresholds  
- Update rule logic and categories  
- Generate governance summary  

---

### Rule Group E — Deception / Misalignment Findings
**Trigger:** Publications on deception or misalignment  
**Threshold:** Any publication or test evidence  
**Actions:**  
- Create new scenario entries  
- Require manual review for user guidance updates  
- Escalate to **HIGH** if mitigation gaps are described  

---

## 7) Automated Action Types

### Action 1 — Log Only
- Triggered by **INFO** events  
- Stored in monitoring logs  

### Action 2 — Notify
- Triggered by **WARN/HIGH**  
- Sends email template to stakeholders  

### Action 3 — Escalate
- Triggered by **HIGH/CRITICAL**  
- Creates remediation task + requires review  

### Action 4 — Remediate
- Adds/updates scenario entries  
- Updates user rights guidance  
- Flags policy change for implementation  

---

## 8) Nuance Rules (Avoid Overreaction)

- **Single mention ≠ escalation**  
  A single keyword mention requires supporting context to elevate severity.

- **Change magnitude matters**  
  Minor edits to a system card do not automatically trigger **HIGH**.

- **User impact weighting**  
  Changes affecting user safety guidance are weighted higher.

- **Source credibility**  
  Only official OpenAI sources influence severity.

---

## 9) Remediation Playbook (Automated + Human)

### Automated Steps
1. Identify trigger type  
2. Classify into taxonomy  
3. Assign severity  
4. Generate guidance update  
5. Log + notify  

### Human Review Steps
1. Validate interpretation  
2. Approve changes to scenarios  
3. Update user‑facing guidance  

---

## 10) Email Directory + Templates

### Email Directory Fields (Schema)
- **recipient_name**
- **recipient_role**
- **email**
- **team**
- **severity_thresholds** (e.g., WARN+)
- **preferred_channel** (email, file)

### Email Template: Safety Alert (WARN/HIGH)
Subject: `[OpenAI Safety Alert] {severity} — {source_title}`  
Body:
- Detected update: {source_title}  
- Severity: {severity}  
- Summary: {summary}  
- Trigger: {trigger_type}  
- Recommended action: {recommended_action}  
- Evidence link: {source_url}  

### Email Template: Critical Escalation
Subject: `[CRITICAL] OpenAI Safety Change — Immediate Review Required`  
Body:
- Change: {source_title}  
- Severity: CRITICAL  
- Risk area: {taxonomy_category}  
- Suggested mitigation: {mitigation_steps}  
- Evidence link: {source_url}  

---

## 11) Data Templates (Schemas)
- **Safety Item Record**  
  - id, title, url, date, type  
  - safety themes  
  - key findings  
  - user guidance implications  
  - user rights implications  
  - remediation steps  

- **Scenario Record**  
  - id, title, risk type  
  - expected behavior  
  - user rights impacted  
  - remediation steps  
  - linked evidence  

- **Remediation Task**  
  - task id, trigger, severity  
  - owner, due date  
  - recommended action  
  - completion status  

---

## 12) Safety Protocol Lifecycle
1. **Detect**: scheduled monitoring  
2. **Classify**: rule engine + taxonomy  
3. **Trigger**: severity thresholds  
4. **Act**: notify/escalate/remediate  
5. **Review**: human approval  
6. **Publish**: update guidance  
7. **Audit**: log and archive  

---

## 13) Compliance & Audit Requirements
- All decisions must be logged with timestamp and rationale  
- All escalations must include evidence link  
- Scenario updates must reference source  

---

## 14) Next Implementation Hooks
- Implement automated email notification pipeline  
- Attach schema validation to monitoring output  
- Link remediation tasks to reporting system  
- Add quarterly governance review  

---
