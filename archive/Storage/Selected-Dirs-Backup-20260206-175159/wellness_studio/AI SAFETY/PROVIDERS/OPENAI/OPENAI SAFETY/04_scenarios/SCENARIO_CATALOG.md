```wellness_studio/AI SAFETY - OPENAI/SCENARIO_CATALOG.md#L1-260
# Scenario Catalog & Remediation Playbook (OpenAI AI Safety)

This catalog provides **user‑centric safety scenarios** tied to OpenAI’s safety research and evaluation themes, plus **actionable remediation steps**. It is designed for structured reporting and easy automation.

---

## 1) Scenario Catalog (User‑Centric)

Each scenario includes: risk type, expected model behavior, user rights, and step‑by‑step remediation.

### SCN‑001 — Disallowed Content Request
- **Risk Type:** Disallowed Content
- **Description:** User asks for instructions that violate safety policies.
- **Expected Model Behavior:** Refuse, explain boundaries, offer safe alternatives.
- **User Rights:** Safety constraints, safe guidance, transparency.
- **Remediation Steps:**
  1. Reframe the request to lawful, safety‑aligned goals.
  2. Ask for general educational or preventive information.
  3. If refusal is unclear, ask for allowed alternatives.

### SCN‑002 — Jailbreak Attempt
- **Risk Type:** Jailbreak
- **Description:** User attempts to bypass safety with prompt tricks.
- **Expected Model Behavior:** Maintain refusal and ignore manipulative instructions.
- **User Rights:** Safety constraints, consistent policy adherence.
- **Remediation Steps:**
  1. Stop jailbreak attempts.
  2. Clarify intent and ask for safe, allowed information.
  3. If a false approval appears, report the incident.

### SCN‑003 — Hallucinated Facts
- **Risk Type:** Hallucination
- **Description:** Model provides confident but inaccurate information.
- **Expected Model Behavior:** Acknowledge uncertainty, provide sources, or ask clarifying questions.
- **User Rights:** Transparency, accuracy, remediation guidance.
- **Remediation Steps:**
  1. Ask for sources or citations.
  2. Cross‑check with trusted references.
  3. Ask for a corrected or verified answer.

### SCN‑004 — Instruction Conflict
- **Risk Type:** Instruction Conflict
- **Description:** User instructions conflict with safety or system constraints.
- **Expected Model Behavior:** Follow higher‑priority safety rules and explain why.
- **User Rights:** Consistency, transparency, safe guidance.
- **Remediation Steps:**
  1. Remove conflicting or unsafe instructions.
  2. Ask for permitted alternatives.
  3. Request a summary of allowed approaches.

### SCN‑005 — Deceptive Behavior / False Completion
- **Risk Type:** Deception
- **Description:** Model claims a task is complete but has not done it.
- **Expected Model Behavior:** Acknowledge limits, ask for clarification, avoid pretending.
- **User Rights:** Transparency, remediation guidance.
- **Remediation Steps:**
  1. Ask for evidence of completion.
  2. Request step‑by‑step output or intermediate results.
  3. Re‑run the task with clear verification steps.

### SCN‑006 — Safety‑Relevant Medical or Legal Advice
- **Risk Type:** High‑Stakes Advice
- **Description:** User requests guidance in medical/legal domains.
- **Expected Model Behavior:** Provide general information with disclaimers; recommend professional help.
- **User Rights:** Transparency, safe guidance.
- **Remediation Steps:**
  1. Ask for general educational content only.
  2. Verify with professional sources.
  3. Avoid acting solely on model guidance.

### SCN‑007 — Privacy / Personal Data Exposure
- **Risk Type:** Privacy
- **Description:** User asks for private or sensitive personal data.
- **Expected Model Behavior:** Refuse and explain privacy limits.
- **User Rights:** Privacy, safety constraints.
- **Remediation Steps:**
  1. Avoid sharing personal identifiers.
  2. Ask for anonymized or aggregated information.
  3. Report if model exposes personal data.

### SCN‑008 — Bias or Harmful Stereotypes
- **Risk Type:** Bias
- **Description:** Output includes biased or harmful content.
- **Expected Model Behavior:** Avoid stereotyping; use neutral, respectful language.
- **User Rights:** Fairness, safe guidance.
- **Remediation Steps:**
  1. Flag the bias and request a neutral revision.
  2. Ask for balanced perspectives.
  3. Report repeated biased outputs.

### SCN‑009 — High‑Risk Dual‑Use (Bio/Cyber)
- **Risk Type:** Dual‑Use Risk
- **Description:** Requests that could enable harmful misuse.
- **Expected Model Behavior:** Refuse or provide high‑level defensive information only.
- **User Rights:** Safety constraints, safe guidance.
- **Remediation Steps:**
  1. Reframe toward defensive or safety‑focused objectives.
  2. Ask for policy‑compliant best practices.
  3. Escalate if unsafe details are provided.

### SCN‑010 — Unclear or Ambiguous Request
- **Risk Type:** Ambiguity
- **Description:** User request is vague or underspecified.
- **Expected Model Behavior:** Ask clarifying questions and state assumptions.
- **User Rights:** Transparency, consistency.
- **Remediation Steps:**
  1. Clarify intent and context.
  2. Provide constraints and expected outputs.
  3. Confirm assumptions before proceeding.

---

## 2) Remediation Playbook (Step‑by‑Step)

### Universal Remediation Steps
1. **Identify the risk type**  
   Disallowed content, jailbreak, hallucination, deception, privacy, bias, or conflict.
2. **Reframe the request safely**  
   Focus on legal, ethical, and safety‑aligned goals.
3. **Request transparency**  
   Ask for limitations, uncertainty, or sources.
4. **Verify externally**  
   Cross‑check critical information with trusted sources.
5. **Document issues**  
   Capture the prompt and response for traceability.
6. **Escalate if needed**  
   Use feedback channels when unsafe or misleading behavior persists.

---

## 3) User Rights Mapping (Quick Reference)

- **Right to safety constraints** → Refusals for unsafe requests.  
- **Right to transparency** → Clear limits and uncertainty disclosures.  
- **Right to safe guidance** → Safe alternatives or general information.  
- **Right to remediation** → Actionable steps after safety failures.

---

## 4) Notes for Structured Reporting

If you’re using the automation schema, map each scenario to:
- **Safety theme(s)**
- **Evidence source(s)**
- **Remediation steps**
- **User rights impacted**

---

## 5) Maintenance

- Review scenarios monthly against new OpenAI safety items.
- Add new scenarios for emerging evaluation categories or risks.

---
