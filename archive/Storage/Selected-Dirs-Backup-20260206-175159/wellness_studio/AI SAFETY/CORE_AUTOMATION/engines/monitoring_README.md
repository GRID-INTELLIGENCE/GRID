# Monitoring Setup Instructions (AI SAFETY - OPENAI)

This document explains how to set up **persistent, scheduled monitoring and logging** for OpenAI safety research sources using the configuration in `monitoring_config.json`.

---

## 1) Purpose

The monitoring system is designed to:
- Track updates from OpenAI safety‑relevant sources.
- Log changes, errors, and run metadata.
- Preserve snapshots, diffs, and reports for auditing.

---

## 2) Configuration

Primary configuration:
- `AI SAFETY - OPENAI/monitoring/monitoring_config.json`

Key settings:
- Schedule cadence: **monthly**
- Default run time (UTC): **02:00**
- Retry policy: 3 attempts (60s, 300s, 900s)
- Sources include:
  - Research Index
  - Safety Evaluations Hub
  - Safety & Alignment page
  - Preparedness Framework

---

## 3) Required Folders

These folders are already created and must remain:
- `AI SAFETY - OPENAI/monitoring/logs/`
- `AI SAFETY - OPENAI/monitoring/status/`
- `AI SAFETY - OPENAI/monitoring/diffs/`
- `AI SAFETY - OPENAI/monitoring/reports/`
- `AI SAFETY - OPENAI/monitoring/alerts/`
- `AI SAFETY - OPENAI/monitoring/snapshots/`

---

## 4) Log Structure

Logs should comply with:
- `AI SAFETY - OPENAI/monitoring/monitoring_log_schema.json`

Expected log fields include:
- `timestamp`, `level`, `event`, `source`, `message`, `run_id`
- Optional: `http`, `diff`, `errors`, `metrics`

---

## 5) Scheduled Execution (Persistent)

### Windows Task Scheduler (Recommended on Windows)
1. Create a task named: **OpenAI Safety Monitoring**
2. Trigger: Monthly (Day 1), 02:00 UTC (convert to local time)
3. Action: run a monitoring script (see section 6)
4. Set “Run whether user is logged on or not”
5. Enable “Run with highest privileges”

### Linux/macOS (cron)
Example schedule (monthly at 02:00 UTC):
- `0 2 1 * * /path/to/monitoring_script.sh`

---

## 6) Monitoring Runner (Required)

You need a runner script that:
- Reads `monitoring_config.json`
- Fetches sources
- Creates snapshots
- Computes diffs
- Writes logs and status

**Expected outputs**
- Logs → `monitoring/logs/monitoring.log`
- Run status → `monitoring/status/last_run.json`
- Diffs → `monitoring/diffs/`
- Reports → `monitoring/reports/`

---

## 7) Status Tracking

Each run should update:
- `monitoring/status/last_run.json`

Minimum fields:
- `run_id`
- `started_at`
- `completed_at`
- `status`
- `items_processed`
- `items_new`
- `items_updated`
- `errors`

---

## 8) Alerts

Alerts are written to:
- `monitoring/alerts/alerts.json`

Recommended triggers:
- New source detected
- Source updated
- Schema violation
- Fetch error

---

## 9) Maintenance

- **Monthly**: Verify logs, diffs, and reports.
- **Quarterly**: Review sources list and keyword filters.
- **Annually**: Audit logging schema and retention policy.

---

## 10) Next Implementation Steps

1. Implement the monitoring runner script.
2. Schedule it via Task Scheduler (Windows) or cron (Linux/macOS).
3. Validate that logs, status, diffs, and alerts are created.

---

## Notes

This setup is designed to be **automation‑friendly** and **auditable**, with a focus on safety relevance and persistent change tracking.
