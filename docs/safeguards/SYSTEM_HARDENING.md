# System Architecture Hardening

**Document type:** Technical policy / architecture  
**Purpose:** Specify security and safety hardening: sandboxing, least-privilege, removal of persistent output channels, limits on tool/Internet access, and human approval for risky actions.  
**Related:** [SAFEGUARDS_REPORT.md](SAFEGUARDS_REPORT.md), [security/](../../security/), [boundaries/](../../boundaries/)

---

## 1. Sandboxing

### What runs in a sandbox

- **Model-invoked code:** Any code executed as a result of model output or tool use (e.g. generated scripts, plugin execution) must run inside a sandbox unless explicitly exempted by policy.
- **Plugins and tools:** Third-party or user-supplied plugins and tools that can execute code or access resources run in an isolated environment (process, container, or restricted VM).
- **Tool execution:** Out-of-process tool runs (e.g. shell, interpreter) are sandboxed with constrained filesystem, network, and process creation.

### Sandbox boundaries

- **Network:** Default deny; only allow-listed endpoints (see Section 4 and [network_access_control.yaml](../../security/network_access_control.yaml)).
- **Filesystem:** Read/write limited to designated directories; no access to secrets, config, or other processes’ data unless explicitly allowed.
- **Process:** No privilege escalation; no spawning of unrestricted shells or long-lived daemons unless in allow-list and logged.

### Implementation references

- **Security layer:** [security/](../../security/) — network interceptor, access control.
- **Boundaries:** [boundaries/](../../boundaries/) — boundary and overwatch components; use for execution and refusal boundaries where integrated.
- **Denylist:** Server and config denylist prevent unsafe servers from starting ([AI_SAFETY_INTEGRATION.md](../AI_SAFETY_INTEGRATION.md)).

---

## 2. Least-Privilege

### Principles

- Processes and services run with the minimum permissions needed for their function.
- No shared “superuser” or overly broad roles for routine operations.
- API keys, tokens, and credentials are scoped to the minimum required (read-only where possible, single-service where possible).

### Application

- **API keys:** Stored in environment or secret manager; not hardcoded; scoped per service; rotated per policy ([AI_SAFETY_INCIDENT_REPORT_2026_02_02.md](../AI_SAFETY_INCIDENT_REPORT_2026_02_02.md) Gap 1).
- **File access:** Services only have read/write to their designated data and log directories; no broad filesystem access.
- **Network:** Default deny; allow-list per service (see [network_access_control.yaml](../../security/network_access_control.yaml)).
- **Config:** Denylist and config sanitization enforce “allow only what is safe” for server and MCP config ([SERVER_DENYLIST_SYSTEM.md](../SERVER_DENYLIST_SYSTEM.md)).

### Checklist (summary)

- [ ] No process runs as root/admin unless strictly required and documented.
- [ ] API keys and secrets in env/secret manager; no secrets in code or default config.
- [ ] Network access allow-listed per client/service.
- [ ] File access restricted to defined directories.
- [ ] Server/config lifecycle gated by denylist and sanitization.

---

## 3. Removal of Persistent Output Channels

### Persistent output channels in scope

- **Long-lived logs** that could be used to exfiltrate data (e.g. raw model output or PII written to a log that is shipped or accessible broadly).
- **Unconstrained write to shared storage** (e.g. model or tool writing to cloud storage, NFS, or shared drive without audit).
- **Outbound queues or streams** that deliver model output or tool results to external systems without access control and audit.

### Policy

- **No persistent channel for raw model output to external systems without audit:** Any pipeline that stores or forwards raw model output (or tool output) to an external system must be access-controlled, logged, and reviewed; no “fire-and-forget” export.
- **Logs:** Sensitive data (credentials, PII, full model output where policy restricts) must not be written to logs in clear text; log retention and access per [MONITORING_AND_ENFORCEMENT_SLAS.md](MONITORING_AND_ENFORCEMENT_SLAS.md).
- **Shared storage writes:** Tool or model-initiated writes to shared/network storage require allow-list and audit; consider human approval for bulk or sensitive writes (see Section 5).

### Gaps and roadmap

- Audit existing logging and export paths against this policy; document and remediate gaps in Implementation roadmap (Section 6).

---

## 4. Limit Tool and Internet Access

### Default posture

- **Tools:** Only tools explicitly allow-listed for the context (e.g. model session, tenant) are available; dangerous tools (arbitrary shell, unrestricted file write, external fetch) are denied or gated by human approval.
- **Internet:** Default deny. Outbound HTTP/HTTPS and other protocols governed by [network_access_control.yaml](../../security/network_access_control.yaml): default policy deny; per-client allow-lists (domains, IPs, endpoints) when enabled.

### Allow-list approach

- **Network:** Use `allowed_domains`, `allowed_endpoints`, and `allowed_ips` in network_access_control; avoid broad wildcards.
- **Servers and config:** Denylist defines what is *not* allowed; combined with allow-list for MCP/servers where “only these” is the policy.
- **New tools or endpoints:** Add only via change control; high-risk changes require SAG awareness or approval (see [DEPLOYMENT_GATES_AND_GOVERNANCE.md](DEPLOYMENT_GATES_AND_GOVERNANCE.md)).

### Approval for changes

- **Config/denylist changes:** Change control; safety-relevant changes reviewed by Safety or Security.
- **Network rule changes:** Documented change; Security review for new allow-list entries.
- **New tool or capability:** Risk assessment; if High/Critical, SAG review before enable.

---

## 5. Human Approval for Risky Actions

### Definition of risky actions

- **Code execution:** Running generated or user-supplied code (e.g. exec, eval, subprocess, plugin).
- **External API calls:** Calls to third-party or user-specified APIs that can mutate data or incur cost.
- **Data export:** Bulk export of data (e.g. dump, copy to external storage, send to external endpoint).
- **Config change:** Changes to safety-relevant config (denylist, network rules, feature flags that enable new capabilities).

### Flow

1. **Trigger:** System identifies that the requested action is “risky” per policy.
2. **Hold:** Action is not executed; request is queued or returned as “pending approval.”
3. **Human approval:** Designated approver (e.g. Safety lead, operator) reviews; approves or denies; optional time-bound expiry.
4. **Audit log:** Request, approver, decision, and timestamp are logged; traceable for SAG and incident review.

### Exceptions and emergency procedures

- **Emergency:** Defined procedure for time-critical mitigation (e.g. kill switch, block endpoint); post-action review and log required.
- **Read-only or low-risk:** Policy may allow certain actions without approval (e.g. read-only API, allow-listed domain); list maintained and reviewed periodically.

---

## 6. Implementation Roadmap

| Area | Current state | Target state | Gaps | Priority | Owner |
|------|----------------|--------------|------|----------|--------|
| Sandboxing | Partial (network deny; denylist for servers) | All model/tool code execution in sandbox; clear boundaries | Execution sandbox for generated code; plugin isolation | High | Engineering + Safety |
| Least-privilege | Env-based secrets; denylist; network default deny | Full least-privilege mapping per service; no broad roles | Service-level mapping; credential scoping | Medium | Security |
| Persistent output channels | Logging and some export paths in use | Audit complete; no unaudited raw output export | Audit of logs and export paths; restrict/remove as needed | High | Safety + Engineering |
| Tool/Internet access | Network NAC in place; allow-list per client | All tools and endpoints allow-listed; no default open | Tool allow-list; review of all enabled endpoints | High | Security |
| Human approval | Not fully implemented for risky actions | All risky actions gated with approval flow and audit | Implement hold/approve flow and designate approvers | High | Safety + Product |

**Next steps:** Prioritize High items; assign owners; set target dates; track in same process as Safeguards Report and deployment gates.

---

**Classification:** AI Safety / Architecture  
**Owner:** Safety + Security + Engineering  
**Next review:** Quarterly; after any Critical finding or architecture change.
