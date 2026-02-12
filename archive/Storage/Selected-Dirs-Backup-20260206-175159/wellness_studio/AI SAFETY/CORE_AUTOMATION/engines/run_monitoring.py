#!/usr/bin/env python3
"""
Scheduled monitoring runner for OpenAI safety research sources.

- Fetches configured sources
- Applies keyword filters
- Stores snapshots
- Generates diffs
- Logs structured JSON lines
- Writes last-run status

This script is designed to be scheduled by an external system (cron/Task Scheduler).
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import sys
import time
import uuid
from pathlib import Path
from typing import cast
from urllib.request import Request, urlopen

DEFAULT_CONFIG_PATH = "AI SAFETY - OPENAI/monitoring/monitoring_config.json"
DEFAULT_TIMEOUT_SECONDS = 30

JsonDict = dict[str, object]
StrDict = dict[str, str]
ObjDict = dict[str, object]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def repo_root() -> Path:
    # .../wellness_studio/AI SAFETY - OPENAI/monitoring/run_monitoring.py
    # parents[2] -> .../wellness_studio
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return cast(JsonDict, data)
    return {}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_output_path(root: Path, raw_path: str) -> Path:
    p = Path(raw_path)
    if p.is_absolute():
        return p
    return root / p


def read_latest_snapshot(latest_path: Path) -> str | None:
    if not latest_path.exists():
        return None
    return latest_path.read_text(encoding="utf-8", errors="ignore")


def write_snapshot(snapshot_dir: Path, source_id: str, content: str, ts: str) -> Path:
    safe_id = source_id.replace(" ", "_")
    snapshot_path = snapshot_dir / f"{safe_id}_{ts}.txt"
    snapshot_path.write_text(content, encoding="utf-8")
    latest_path = snapshot_dir / f"latest_{safe_id}.txt"
    latest_path.write_text(content, encoding="utf-8")
    return snapshot_path


def write_diff(
    diff_dir: Path, source_id: str, before: str, after: str, ts: str
) -> Path | None:
    if before == after:
        return None
    safe_id = source_id.replace(" ", "_")
    diff_path = diff_dir / f"diff_{safe_id}_{ts}.diff"
    diff_lines = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile="before",
        tofile="after",
        lineterm="",
    )
    diff_path.write_text("\n".join(diff_lines), encoding="utf-8")
    return diff_path


def log_event(
    log_path: Path,
    run_id: str,
    level: str,
    event: str,
    source: StrDict,
    message: str,
    status: str | None = None,
    duration_ms: int | None = None,
    http: ObjDict | None = None,
    diff: ObjDict | None = None,
    errors: list[ObjDict] | None = None,
    metrics: ObjDict | None = None,
    tags: list[str] | None = None,
) -> None:
    record: ObjDict = {
        "timestamp": utc_now(),
        "level": level,
        "event": event,
        "source": source,
        "message": message,
        "run_id": run_id,
    }
    if status is not None:
        record["status"] = status
    if duration_ms is not None:
        record["duration_ms"] = duration_ms
    if http is not None:
        record["http"] = http
    if diff is not None:
        record["diff"] = diff
    if errors is not None:
        record["errors"] = errors
    if metrics is not None:
        record["metrics"] = metrics
    if tags is not None:
        record["tags"] = tags

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def fetch_url(url: str, timeout: int) -> tuple[int, str, StrDict]:
    req = Request(url, headers={"User-Agent": "OpenAI-Safety-Monitor/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        status = resp.getcode() or 0
        headers: StrDict = {str(k).lower(): str(v) for k, v in resp.headers.items()}
        content = resp.read().decode("utf-8", errors="ignore")
        return status, content, headers


def apply_filters(content: str, include: list[str], exclude: list[str]) -> bool:
    text = content.lower()
    if include and not any(k.lower() in text for k in include):
        return False
    if exclude and any(k.lower() in text for k in exclude):
        return False
    return True


def write_last_run(status_path: Path, payload: ObjDict) -> None:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_dict(data: JsonDict, key: str) -> JsonDict:
    value = data.get(key)
    return cast(JsonDict, value) if isinstance(value, dict) else {}


def get_list_str(data: JsonDict, key: str) -> list[str]:
    value = data.get(key)
    if isinstance(value, list):
        return [str(v) for v in value if isinstance(v, str)]
    return []


def get_str_from_dict(data: JsonDict, key: str, default: str = "") -> str:
    value = data.get(key)
    return str(value) if isinstance(value, str) else default


def run_monitoring(config_path: Path, timeout: int) -> int:
    root = repo_root()
    config = load_json(config_path)

    outputs = get_dict(config, "outputs")
    log_path = resolve_output_path(
        root,
        get_str_from_dict(
            outputs, "log_path", "AI SAFETY - OPENAI/monitoring/logs/monitoring.log"
        ),
    )
    status_path = resolve_output_path(
        root,
        get_str_from_dict(
            outputs,
            "status_path",
            "AI SAFETY - OPENAI/monitoring/status/last_run.json",
        ),
    )
    diff_dir = resolve_output_path(
        root,
        get_str_from_dict(outputs, "diff_path", "AI SAFETY - OPENAI/monitoring/diffs"),
    )
    reports_dir = resolve_output_path(
        root,
        get_str_from_dict(
            outputs, "reports_path", "AI SAFETY - OPENAI/monitoring/reports"
        ),
    )
    snapshots_dir = resolve_output_path(
        root,
        get_str_from_dict(
            outputs, "snapshots_path", "AI SAFETY - OPENAI/monitoring/snapshots"
        ),
    )

    ensure_dir(diff_dir)
    ensure_dir(reports_dir)
    ensure_dir(snapshots_dir)

    run_id = str(uuid.uuid4())
    run_start = time.time()

    filters = get_dict(config, "filters")
    include_keywords = get_list_str(filters, "include_keywords")
    exclude_keywords = get_list_str(filters, "exclude_keywords")

    sources_raw = config.get("sources", [])
    sources: list[JsonDict] = []
    if isinstance(sources_raw, list):
        sources = [cast(JsonDict, s) for s in sources_raw if isinstance(s, dict)]

    metrics: dict[str, int] = {
        "items_processed": 0,
        "items_new": 0,
        "items_updated": 0,
        "items_filtered_out": 0,
    }

    schedule = get_dict(config, "schedule")
    retry_policy = get_dict(schedule, "retry_policy")
    retries_raw = retry_policy.get("max_retries", 0)
    retries = int(retries_raw) if isinstance(retries_raw, (int, float, str)) else 0
    backoff_raw = retry_policy.get("backoff_seconds", [])
    backoff: list[int] = []
    if isinstance(backoff_raw, list):
        for v in backoff_raw:
            if isinstance(v, (int, float, str)):
                backoff.append(int(v))

    for source in sources:
        metrics["items_processed"] += 1
        source_id = get_str_from_dict(source, "id", "unknown")
        source_url = get_str_from_dict(source, "url", "")
        source_type = get_str_from_dict(source, "type", "unknown")

        source_meta: StrDict = {
            "id": source_id,
            "url": source_url,
            "type": source_type,
        }

        log_event(
            log_path=log_path,
            run_id=run_id,
            level="INFO",
            event="fetch_start",
            source=source_meta,
            message=f"Fetching {source_url}",
            status="started",
        )

        t0 = time.time()
        attempt = 0

        while True:
            try:
                status_code, content, headers = fetch_url(source_url, timeout=timeout)
                duration_ms = int((time.time() - t0) * 1000)

                if status_code >= 400:
                    raise RuntimeError(f"HTTP {status_code}")

                if not apply_filters(content, include_keywords, exclude_keywords):
                    metrics["items_filtered_out"] = (
                        int(metrics["items_filtered_out"]) + 1
                    )
                    log_event(
                        log_path=log_path,
                        run_id=run_id,
                        level="INFO",
                        event="filtered_out",
                        source=source_meta,
                        message="Content filtered out by keywords.",
                        status="skipped",
                        duration_ms=duration_ms,
                        http={
                            "status_code": status_code,
                            "etag": headers.get("etag", ""),
                            "last_modified": headers.get("last-modified", ""),
                        },
                    )
                    break

                safe_id = source_id.replace(" ", "_")
                latest_path = snapshots_dir / f"latest_{safe_id}.txt"
                before = read_latest_snapshot(latest_path) or ""
                timestamp = utc_now().replace(":", "").replace("-", "")
                snapshot_path = write_snapshot(
                    snapshots_dir, safe_id, content, timestamp
                )
                diff_path = write_diff(diff_dir, safe_id, before, content, timestamp)

                changed = before != content
                if before == "":
                    metrics["items_new"] += 1
                elif changed:
                    metrics["items_updated"] += 1

                log_event(
                    log_path=log_path,
                    run_id=run_id,
                    level="INFO",
                    event="fetch_success",
                    source=source_meta,
                    message="Fetch and snapshot completed.",
                    status="completed",
                    duration_ms=duration_ms,
                    http={
                        "status_code": status_code,
                        "etag": headers.get("etag", ""),
                        "last_modified": headers.get("last-modified", ""),
                    },
                    diff={
                        "changed": changed,
                        "snapshot_before": str(latest_path) if before else "",
                        "snapshot_after": str(snapshot_path),
                        "diff_path": str(diff_path) if diff_path else "",
                    },
                    metrics={
                        "items_processed": metrics["items_processed"],
                        "items_new": metrics["items_new"],
                        "items_updated": metrics["items_updated"],
                        "items_filtered_out": metrics["items_filtered_out"],
                    },
                )
                break

            except Exception as exc:
                duration_ms = int((time.time() - t0) * 1000)
                attempt += 1
                log_event(
                    log_path=log_path,
                    run_id=run_id,
                    level="ERROR",
                    event="fetch_error",
                    source=source_meta,
                    message="Fetch failed.",
                    status="failed",
                    duration_ms=duration_ms,
                    errors=[{"code": "FETCH_ERROR", "detail": str(exc)}],
                )
                if attempt > retries:
                    break
                sleep_for = (
                    backoff[min(attempt - 1, len(backoff) - 1)] if backoff else 0
                )
                time.sleep(sleep_for)

    run_duration_ms = int((time.time() - run_start) * 1000)
    last_run_payload: ObjDict = {
        "run_id": run_id,
        "timestamp": utc_now(),
        "duration_ms": run_duration_ms,
        "metrics": metrics,
        "sources_count": len(sources),
    }
    write_last_run(status_path, last_run_payload)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run scheduled monitoring for OpenAI safety sources."
    )
    _ = parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to monitoring_config.json (relative to repo root).",
    )
    _ = parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout in seconds.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = resolve_output_path(repo_root(), args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 1
    return run_monitoring(config_path, timeout=args.timeout)


if __name__ == "__main__":
    sys.exit(main())
