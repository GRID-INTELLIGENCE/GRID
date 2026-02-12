version: 1
item:
  id: string
  title: string
  url: string
  date: string # ISO-8601
  type: enum[Research, Publication, Safety, SystemCard, Policy]
  safety_themes: array[string] # use taxonomy labels
  summary: string
  key_findings: array[string]
  user_guidance: array[string]
  user_rights_implications: array[string]
  scenarios: array[string] # scenario IDs
  remediation_steps: array[string]
  evidence_quotes: array[string] # short, precise excerpts
```

### 4.2 Scenario Record Schema (YAML)
```/dev/null/scenario_record.schema.yml#L1-80
version: 1
scenario:
  id: string
  title: string
  description: string
  risk_type: enum[Jailbreak, Hallucination, Deception, DisallowedContent, InstructionConflict, Privacy]
  expected_model_behavior: string
  user_rights: array[string]
  remediation_steps: array[string]
  linked_items: array[string] # item IDs
```

---

## 5) Automation Workflow (Step‑by‑Step)

### Step 1 — Collect
- Pull items from the Research Index.
- Pull related safety pages and system cards (if referenced or clearly safety‑relevant).

**Automated checks:**
- De‑duplicate by URL.
- Reject items without explicit safety relevance.

### Step 2 — Classify
- Assign safety themes based on the taxonomy.
- Tag risks and evaluation types.

**Automated checks:**
- Require at least 1 taxonomy tag.
- Require at least 1 `user_guidance` entry.

### Step 3 — Extract
- Summarize findings.
- Extract explicit user guidance.
- Capture short evidence quotes.

**Automated checks:**
- Summary length ≥ 2 sentences.
- Evidence quotes ≤ 2 lines each.

### Step 4 — Scenario Mapping
- For each item, map to at least 1 scenario.
- Create new scenarios if missing.

**Automated checks:**
- Each scenario includes remediation steps.
- Each scenario maps to user rights.

### Step 5 — User Rights Matrix
Map each item/scenario to user rights:
- **Right to safety constraints**
- **Right to transparency of limitations**
- **Right to safe use guidance**
- **Right to remediation guidance**

### Step 6 — Report Generation
Create:
1) **Structured dataset** (CSV/JSON/YAML)  
2) **Narrative report** summarizing patterns and actionable guidance  
3) **Scenario playbook** with step‑by‑step remediation  

---

## 6) User Guidelines (Actionable, Step‑by‑Step)

### Safe Use Checklist
1. **Clarify your goal**: ensure it’s safe and lawful.
2. **Avoid prohibited content**: do not request disallowed or harmful content.
3. **Verify outputs**: cross‑check critical information.
4. **Flag uncertainty**: ask for sources and limitations.
5. **Report issues**: document failures and escalate.

### Remediation Playbook
1. Identify the risk type.
2. Reframe your request to comply with safety boundaries.
3. Request verification or sources.
4. If unsafe content appears, stop and report.
5. Use official feedback channels if repeated.

---

## 7) Scenario Template (Ready for Use)

```/dev/null/scenario_template.md#L1-40
## Scenario: <Title>
**Risk Type:** <RiskType>
**Description:** <Short description>
**Expected Model Behavior:** <Safe refusal or compliant response>
**User Rights:** <List>
**Remediation Steps:**
1. ...
2. ...
3. ...
**Related Evidence:** <Item IDs / sources>
```

---

## 8) Output Structure (Files)
Recommended outputs in this directory:
- `DATA_ITEMS.yml` — structured item records
- `DATA_SCENARIOS.yml` — structured scenario records
- `REPORT.md` — narrative synthesis
- `PLAYBOOK.md` — user remediation and safety guide

---

## 9) Quality Gates (Automation Checks)
**Must pass:**
- Every item has: `title`, `url`, `date`, `type`, `summary`, `safety_themes`, `user_guidance`
- Every scenario has: `risk_type`, `expected_model_behavior`, `remediation_steps`, `user_rights`
- No item is included without direct safety relevance

---

## 10) Example User Rights Mapping
**Right to safety constraints**  
- Expect refusal or safe redirection for disallowed content.

**Right to transparency**  
- Expect limitations and uncertainty disclosures.

**Right to safe guidance**  
- Expect safe alternatives when a request is risky.

**Right to remediation**  
- Expect steps to verify, correct, or escalate.

---

## 11) Reporting Outline (Narrative)
1. Executive Summary  
2. Safety Taxonomy Overview  
3. Key Findings by Theme  
4. Scenario‑Based Analysis  
5. User Rights & Remediation  
6. Gaps & Recommendations  

---

## 12) Maintenance Schedule
- Monthly refresh of Research Index and Safety pages
- Quarterly re‑validation of scenarios and user guidance

---

## 13) Notes for Implementation
- This workflow is designed for **automation‑first execution**.
- All outputs must be **traceable to official sources**.
- Avoid external or unofficial commentary unless explicitly requested.

---
