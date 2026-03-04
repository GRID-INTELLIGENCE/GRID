# Operational safety checklist

Use this checklist in PRs that touch execution, subprocess, or guardrail admin.

## Before merge

- [ ] **Subprocess / execution**: New subprocess use in service logic (ingestion, MCP, scripts) must use `SecureSubprocess` from `src/grid/security/subprocess_wrapper.py` with an allowlist and timeout. No raw `subprocess.run` with `shell=True` or user-controlled command strings.
- [ ] **Admin gating**: When `guardrail_admin_identities` is non-empty, admin is required to be in that list (header-only is disabled). See `src/search/api/routes.py` and `src/search/config.py`.
- [ ] **Prevention**: Run or reference the prevention framework so new `subprocess` with `shell=True` and `eval`/`exec` are flagged in review.

## Reference

- Secure subprocess: `src/grid/security/subprocess_wrapper.py`
- Search admin gating: `src/search/api/routes.py` (`_require_admin`)
