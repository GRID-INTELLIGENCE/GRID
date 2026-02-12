# AI SAFETY — Program Overview & Routing

This directory is the **top‑level AI Safety hub**. It provides **general structure, shared automation, and provider routing** for multiple AI vendors. Provider‑specific safety protocols live under `PROVIDERS/`, while cross‑provider automation, schemas, and actions live under `CORE_AUTOMATION/`.

---

## 1) Directory Structure (General)

```
AI SAFETY/
├─ README.md
├─ CORE_AUTOMATION/
│  ├─ rules/
│  ├─ thresholds/
│  ├─ actions/
│  ├─ schemas/
│  ├─ notifications/
│  └─ engines/
├─ PROVIDERS/
│  ├─ OPENAI/
│  ├─ ANTHROPIC/
│  ├─ GOOGLE/
│  ├─ XAI/
│  ├─ MISTRAL/
│  ├─ NVIDIA/
│  └─ LLAMA/
```

---

## 2) Routing & Ownership

### Provider Protocols
- **Location:** `PROVIDERS/<VENDOR>/`
- **Purpose:** Vendor‑specific safety protocols, evaluations, and risk documentation.

### Cross‑Provider Automation
- **Location:** `CORE_AUTOMATION/`
- **Purpose:** Shared rules, triggers, thresholds, remediation logic, and notification templates.

### Routing Rule
All provider protocols **must route back** to the top‑level structure:
- Any vendor‑specific remediation or escalation → **cross‑provider logic** in `CORE_AUTOMATION/`
- Any shared policy update → **applied across all providers**

---

## 3) Program Goals

1. **Rule/Trigger‑Based Safety**
   - Define clear rules for detection and response.
2. **Threshold‑Oriented Actions**
   - Escalate based on severity and risk confidence.
3. **Nuanced Remediation**
   - Avoid overreaction while preserving safety.
4. **Auditability**
   - Every decision logged and traceable to evidence.

---

## 4) Current Providers

- `OPENAI`
- `ANTHROPIC`
- `GOOGLE`
- `XAI`
- `MISTRAL`
- `NVIDIA`
- `LLAMA`

---

## 5) How to Extend

1. Add a provider directory under `PROVIDERS/`.
2. Add vendor‑specific safety documentation.
3. Map vendor rules into `CORE_AUTOMATION/` schemas and thresholds.

---

## 6) Governance & Maintenance

- **Monthly:** refresh source monitoring and thresholds  
- **Quarterly:** validate escalation logic and remediation playbooks  
- **Annually:** audit and update the safety taxonomy  

---

## 7) Summary

This top‑level hub is designed to be **provider‑agnostic**, **automation‑friendly**, and **extensible**.  
All protocols must align with **shared safety logic** in `CORE_AUTOMATION/`.

---
