import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class Severity(StrEnum):
    CRITICAL = "🔴"
    HIGH = "🟠"
    MEDIUM = "🟡"
    LOW = "🟢"


class Impact(StrEnum):
    BLOCKING = "🎯"
    WARNING = "⚠️"
    INFO = "💡"


class Status(StrEnum):
    RESOLVED = "✅"
    UNRESOLVED = "❌"


@dataclass
class PlanItem:
    """Represents a single item in a plan"""

    text: str
    number: int | None = None
    resolved: bool = False
    reference: str | None = None
    severity: Severity = Severity.MEDIUM
    impact: Impact = Impact.INFO
    status: Status = Status.UNRESOLVED
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanReference:
    """Represents a resolved reference"""

    path: str
    symbol: str | None = None
    file_type: str = "file"
    exists: bool = False
    is_workspace_relative: bool = True

    @property
    def full_reference(self) -> str:
        """Returns the full reference path:symbol format"""
        if self.symbol:
            return f"{self.path}:{self.symbol}"
        return self.path


@dataclass
class ResolutionResult:
    """Result of resolving a plan item to references"""

    plan_item: PlanItem
    candidates: list[PlanReference] = field(default_factory=list)
    selected_reference: PlanReference | None = None
    confidence_score: float = 0.0
    error_message: str | None = None


@dataclass
class PlanResolution:
    """Complete resolution of a plan"""

    source: str
    items: list[ResolutionResult] = field(default_factory=list)
    total_items: int = 0
    resolved_count: int = 0
    unresolved_count: int = 0
    severity_breakdown: dict[Severity, int] = field(default_factory=dict)
    impact_breakdown: dict[Impact, int] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FormatPivot:
    """Configuration for format conversion"""

    output_format: str  # 'csv', 'markdown', 'mermaid', 'verification_chain'
    include_metadata: bool = True
    include_verification: bool = True
    custom_headers: dict[str, str] | None = None


@dataclass
class FlowTraceNode:
    """Node in a flow trace diagram"""

    id: str
    label: str
    reference: str | None = None
    connections: list[str] = field(default_factory=list)
    node_type: str = "process"  # process, decision, start, end


@dataclass
class VerificationChain:
    """Verification workflow chain"""

    stages: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    checkpoints: list[str] = field(default_factory=list)


class PlanParser:
    """Parses various plan formats into structured items"""

    @staticmethod
    def parse_numbered_plan(text: str) -> list[PlanItem]:
        """Parse numbered list format: 1. Item 2. Item"""
        items = []
        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match numbered items: "1. Item" or "1) Item"
            match = re.match(r"^(\d+)[\.\)\s]+\s*(.+)$", line)
            if match:
                number = int(match.group(1))
                text_content = match.group(2).strip()
                items.append(PlanItem(text=text_content, number=number))

        return items

    @staticmethod
    def parse_bullet_plan(text: str) -> list[PlanItem]:
        """Parse bullet list format: - Item • Item"""
        items = []
        lines = text.strip().split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Match bullet items
            if line.startswith(("- ", "• ", "* ")):
                text_content = line[2:].strip()
                items.append(PlanItem(text=text_content, number=i))

        return items

    @staticmethod
    def parse_checklist_plan(text: str) -> list[PlanItem]:
        """Parse checklist format: ☐ Item ☑ Item"""
        items = []
        lines = text.strip().split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Match checklist items
            if line.startswith(("☐ ", "☑ ", "□ ", "☒ ")):
                text_content = line[2:].strip()
                items.append(PlanItem(text=text_content, number=i))

        return items


class ReferenceResolver:
    """Resolves plan items to concrete file/symbol references"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.reference_patterns = {
            "auth": ["src/grid/api/routers/auth.py", "src/grid/crud/user.py"],
            "config": ["src/grid/core/config.py", ".vscode/settings.json"],
            "test": ["tests/", "test_"],
            "docs": ["docs/", ".md"],
            "rules": [".claude/rules/", ".md"],
            "skills": [".cursor/skills/", "SKILL.md"],
        }

    def resolve_plan(self, plan_items: list[PlanItem]) -> PlanResolution:
        """Resolve all items in a plan"""
        results = []

        for item in plan_items:
            result = self._resolve_single_item(item)
            results.append(result)

        resolution = PlanResolution(source="parsed plan", items=results, total_items=len(plan_items))

        self._calculate_statistics(resolution)
        return resolution

    def _resolve_single_item(self, item: PlanItem) -> ResolutionResult:
        """Resolve a single plan item"""
        result = ResolutionResult(plan_item=item)

        # Try different resolution strategies
        candidates = self._find_direct_matches(item.text)
        if not candidates:
            candidates = self._find_pattern_matches(item.text)
        if not candidates:
            candidates = self._find_contextual_matches(item.text)

        result.candidates = candidates

        if candidates:
            # Select best candidate (first one for now)
            result.selected_reference = candidates[0]
            result.confidence_score = 0.8
            item.resolved = True
            item.reference = candidates[0].full_reference
            item.status = Status.RESOLVED
        else:
            result.error_message = f"No matching references found for: {item.text}"
            item.status = Status.UNRESOLVED

        return result

    def _find_direct_matches(self, text: str) -> list[PlanReference]:
        """Find direct file/symbol matches"""
        candidates = []

        # Check for explicit file references in text
        file_refs = re.findall(r"`([^`]+)`", text)
        for ref in file_refs:
            path = Path(ref)
            if path.exists() or self._is_workspace_path(path):
                candidates.append(
                    PlanReference(
                        path=str(path), exists=path.exists(), is_workspace_relative=self._is_workspace_path(path)
                    )
                )

        return candidates

    def _find_pattern_matches(self, text: str) -> list[PlanReference]:
        """Find matches using keyword patterns"""
        candidates = []
        text_lower = text.lower()

        for keyword, patterns in self.reference_patterns.items():
            if keyword in text_lower:
                for pattern in patterns:
                    path = Path(pattern)
                    if path.exists() or pattern.endswith("/"):
                        # Directory pattern
                        candidates.append(
                            PlanReference(
                                path=pattern.rstrip("/"),
                                file_type="directory",
                                exists=path.exists(),
                                is_workspace_relative=True,
                            )
                        )
                    else:
                        # File pattern
                        candidates.append(PlanReference(path=pattern, exists=path.exists(), is_workspace_relative=True))

        return candidates

    def _find_contextual_matches(self, text: str) -> list[PlanReference]:
        """Find matches using conversation context (placeholder)"""
        # This would use conversation history to find relevant files
        return []

    def _is_workspace_path(self, path: Path) -> bool:
        """Check if path is within workspace"""
        try:
            path.resolve().relative_to(self.workspace_root.resolve())
            return True
        except ValueError:
            return False

    def _calculate_statistics(self, resolution: PlanResolution):
        """Calculate resolution statistics"""
        resolved = sum(1 for r in resolution.items if r.selected_reference)
        unresolved = len(resolution.items) - resolved

        resolution.resolved_count = resolved
        resolution.unresolved_count = unresolved

        # Calculate severity/impact breakdowns
        for result in resolution.items:
            item = result.plan_item
            resolution.severity_breakdown[item.severity] = resolution.severity_breakdown.get(item.severity, 0) + 1
            resolution.impact_breakdown[item.impact] = resolution.impact_breakdown.get(item.impact, 0) + 1


class OutputGenerator:
    """Generates various output formats from resolved plans"""

    @staticmethod
    def generate_reference_map(resolution: PlanResolution) -> str:
        """Generate reference map in markdown format"""
        output = ["# Plan Reference Map\n"]
        output.append(f"**Source:** {resolution.source}")
        output.append(f"**Date:** {resolution.created_at}\n")

        output.append("## Executive Summary\n")
        output.append(f"- Total items: {resolution.total_items}")
        output.append(f"- Resolved: {resolution.resolved_count} | Unresolved: {resolution.unresolved_count}")

        severity_summary = ", ".join(f"{k.value} {v}" for k, v in resolution.severity_breakdown.items())
        impact_summary = ", ".join(f"{k.value} {v}" for k, v in resolution.impact_breakdown.items())
        output.append(f"- Severity: {severity_summary}")
        output.append(f"- Impact: {impact_summary}\n")

        output.append("## Reference Mapping\n")

        for i, result in enumerate(resolution.items, 1):
            item = result.plan_item
            output.append(f"### {i}. {item.text}\n")
            output.append(f"**Reference:** `{item.reference or '[UNRESOLVED]'}`")
            output.append(f"**Severity:** {item.severity.value}")
            output.append(f"**Impact:** {item.impact.value}")
            output.append(f"**Status:** {item.status.value}\n")

        output.append("## Verification Steps\n")
        output.append("1. Check all resolved references exist")
        output.append("2. Validate symbol names are correct")
        output.append("3. Confirm file paths are accessible")
        output.append("4. Review unresolved items for manual resolution")

        return "\n".join(output)

    @staticmethod
    def generate_csv_export(resolution: PlanResolution) -> str:
        """Generate CSV format for project management tools"""
        output = ["Item,Reference,Severity,Impact,Status"]

        for i, result in enumerate(resolution.items, 1):
            item = result.plan_item
            row = [
                f'"{item.text}"',
                f'"{item.reference or ""}"',
                item.severity.name,
                item.impact.name,
                item.status.name,
            ]
            output.append(",".join(row))

        return "\n".join(output)

    @staticmethod
    def generate_mermaid_flowchart(resolution: PlanResolution) -> str:
        """Generate Mermaid flowchart visualization"""
        output = ["flowchart TD"]

        for i, result in enumerate(resolution.items, 1):
            item = result.plan_item
            node_id = f"item{i}"
            label = item.text[:30] + "..." if len(item.text) > 30 else item.text

            if item.reference:
                output.append(f'{node_id}["{label}\\n{item.reference}"]')
            else:
                output.append(f'{node_id}["{label}\\n[UNRESOLVED]"]')

            # Connect items in sequence
            if i > 1:
                prev_id = f"item{i - 1}"
                output.append(f"{prev_id} --> {node_id}")

        return "\n".join(output)


class PlanToReferenceService:
    """Main service for plan-to-reference functionality"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.parser = PlanParser()
        self.resolver = ReferenceResolver(workspace_root)
        self.generator = OutputGenerator()

    def process_plan_text(self, plan_text: str, output_format: str = "reference_map") -> str:
        """Process plan text and return formatted output"""
        # Parse the plan
        items = self.parser.parse_numbered_plan(plan_text)
        if not items:
            items = self.parser.parse_bullet_plan(plan_text)
        if not items:
            items = self.parser.parse_checklist_plan(plan_text)

        if not items:
            return "No plan items detected in the input text."

        # Resolve references
        resolution = self.resolver.resolve_plan(items)

        # Generate output
        if output_format == "csv":
            return self.generator.generate_csv_export(resolution)
        elif output_format == "mermaid":
            return self.generator.generate_mermaid_flowchart(resolution)
        elif output_format == "verification_chain":
            # Placeholder for verification chain generation
            return "Verification chain generation not yet implemented"
        else:
            return self.generator.generate_reference_map(resolution)

    def validate_workspace_boundary(self, path: str) -> bool:
        """Validate that a path is within workspace boundaries"""
        return self.resolver._is_workspace_path(Path(path))

    def get_resolution_statistics(self, resolution: PlanResolution) -> dict[str, Any]:
        """Get statistics about a resolution"""
        return {
            "total_items": resolution.total_items,
            "resolved_count": resolution.resolved_count,
            "unresolved_count": resolution.unresolved_count,
            "resolution_rate": resolution.resolved_count / resolution.total_items if resolution.total_items > 0 else 0,
            "severity_breakdown": {k.name: v for k, v in resolution.severity_breakdown.items()},
            "impact_breakdown": {k.name: v for k, v in resolution.impact_breakdown.items()},
        }
