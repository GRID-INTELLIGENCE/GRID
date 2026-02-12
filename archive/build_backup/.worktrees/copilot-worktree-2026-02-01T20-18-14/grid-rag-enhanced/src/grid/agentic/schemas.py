"""Pydantic schemas for agentic system requests and responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CaseCreateRequest(BaseModel):
    """Request schema for creating a new case."""

    raw_input: str = Field(..., description="Raw user input (case description)")
    user_id: str | None = Field(None, description="User identifier")
    examples: list[str] | None = Field(default_factory=list, description="User-provided examples")
    scenarios: list[str] | None = Field(default_factory=list, description="User-provided scenarios")
    user_context: dict[str, Any] | None = Field(default_factory=dict, description="Additional user context")


class CaseEnrichRequest(BaseModel):
    """Request schema for enriching an existing case."""

    additional_context: str = Field(..., description="Additional context to add")
    examples: list[str] | None = Field(default_factory=list, description="Additional examples")
    scenarios: list[str] | None = Field(default_factory=list, description="Additional scenarios")


class CaseExecuteRequest(BaseModel):
    """Request schema for executing a case."""

    agent_role: str | None = Field(None, description="Specific agent role to use (optional)")
    task: str | None = Field(None, description="Specific task to execute (optional)")
    force: bool = Field(False, description="Force execution even if case is not ready")


class CaseResponse(BaseModel):
    """Response schema for case operations."""

    case_id: str = Field(..., description="Unique case identifier")
    status: str = Field(..., description="Current case status")
    category: str | None = Field(None, description="Case category")
    priority: str | None = Field(None, description="Case priority")
    confidence: float | None = Field(None, description="Classification confidence")
    reference_file_path: str | None = Field(None, description="Path to reference file")
    events: list[str] = Field(default_factory=list, description="Events emitted so far")
    created_at: str = Field(..., description="Case creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")
    completed_at: str | None = Field(None, description="Completion timestamp")
    outcome: str | None = Field(None, description="Case outcome")
    solution: str | None = Field(None, description="Solution applied")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "case_id": "CASE-abc123",
                "status": "categorized",
                "category": "testing",
                "priority": "high",
                "confidence": 0.85,
                "reference_file_path": ".case_references/CASE-abc123_reference.json",
                "events": ["case.created", "case.categorized"],
                "created_at": "2025-01-08T10:00:00Z",
                "updated_at": "2025-01-08T10:01:00Z",
            }
        }
    )


class AgentExperienceResponse(BaseModel):
    """Response schema for agent experience summary."""

    total_cases: int = Field(..., description="Total cases processed")
    success_rate: float = Field(..., description="Overall success rate")
    category_distribution: dict[str, int] = Field(default_factory=dict, description="Cases by category")
    experience_by_category: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Experience breakdown by category"
    )
    common_patterns: list[dict[str, Any]] = Field(default_factory=list, description="Common solution patterns")
    learning_insights: list[str] = Field(default_factory=list, description="Learning insights")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_cases": 100,
                "success_rate": 0.85,
                "category_distribution": {
                    "testing": 25,
                    "architecture": 20,
                    "bug_fix": 15,
                },
                "experience_by_category": {
                    "testing": {
                        "total": 25,
                        "successes": 22,
                        "success_rate": 0.88,
                    }
                },
                "common_patterns": [
                    {
                        "category": "testing",
                        "pattern_type": "solution",
                        "pattern": "Add pytest tests",
                        "frequency": 15,
                    }
                ],
                "learning_insights": [
                    "Processed 100 cases total",
                    "High success rate (85%) - system performing well",
                ],
            }
        }
    )


class ReferenceFileResponse(BaseModel):
    """Response schema for reference file."""

    case_id: str = Field(..., description="Case identifier")
    reference_file_path: str = Field(..., description="Path to reference file")
    content: dict[str, Any] = Field(..., description="Reference file content")
    recommended_roles: list[str] = Field(default_factory=list, description="Recommended agent roles")
    recommended_tasks: list[str] = Field(default_factory=list, description="Recommended tasks")
    workflow: list[str] = Field(default_factory=list, description="Recommended workflow")
