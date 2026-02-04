"""Memo generator for synthesizing agentic outcomes into architectural memos."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class MemoGenerator:
    """Generates the final reference memo for architectural enforcement."""

    def __init__(self, output_dir: str = ".memos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_memo(
        self,
        case_id: str,
        lawyer_report: dict[str, Any],
        decisions: list[dict[str, Any]],
        xai_explanations: list[dict[str, Any]] | None = None,
    ) -> str:
        """Create a full memo based on the lawyer's report and decisions."""
        memo_id = f"MEMO-{case_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.now(UTC).isoformat()

        memo_content = {
            "memo_id": memo_id,
            "case_id": case_id,
            "timestamp": timestamp,
            "executive_summary": lawyer_report.get("summary", "No summary provided."),
            "boolean_decisions": decisions,
            "xai_explanations": xai_explanations or [],
            "enforcement_protocol": "GRID-SEC-ENFORCE-V1",
            "audit_trail": lawyer_report.get("audit_trail", []),
        }

        memo_path = self.output_dir / f"{memo_id}.json"
        with open(memo_path, "w", encoding="utf-8") as f:
            json.dump(memo_content, f, indent=2)

        return str(memo_path)

    def create_markdown_memo(self, memo_path: str) -> str:
        """Convert a JSON memo into a human-readable markdown file."""
        with open(memo_path, encoding="utf-8") as f:
            memo = json.load(f)

        md_content = f"""# Architectural Enforcement Memo: {memo["memo_id"]}
**Date**: {memo["timestamp"]}
**Case Reference**: {memo["case_id"]}

## Executive Summary
{memo["executive_summary"]}

## Boolean Decisions
"""
        for d in memo["boolean_decisions"]:
            status = "✅ ENABLED" if d["value"] else "❌ DISABLED"
            md_content += f"- **{d['feature']}**: {status} (Protocol: {d['protocol']})\n"

        if memo.get("xai_explanations"):
            md_content += "\n## XAI Reasoning Traces\n"
            for xai in memo["xai_explanations"]:
                md_content += f"### Trace: {xai.get('decision_id')}\n"
                md_content += f"- **Resonance Alignment**: {xai.get('resonance_alignment', 0) * 100}%\n"
                md_content += "- **Logic Steps**:\n"
                for step in xai.get("logic_path", []):
                    md_content += f"  - {step}\n"

        md_content += f"\n## Enforcement Logic\nThis memo serves as the final reference for decision enforcement via the {memo['enforcement_protocol']} layer."

        md_path = Path(memo_path).with_suffix(".md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return str(md_path)
