"""
MCQ (Multiple Choice Questions) Schemas.

Request and response models for MCQ bank and question management.
Uses Pydantic v2 for validation, serialization, and OpenAPI schema generation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from . import BaseSchema

# =============================================================================
# Enums
# =============================================================================


class MCQDifficultySchema(StrEnum):
    """Difficulty level for MCQ questions."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# =============================================================================
# MCQ Option Schemas
# =============================================================================


class MCQOptionBase(BaseSchema):
    """Base schema for MCQ options."""

    text: str = Field(min_length=1, max_length=2000)
    is_correct: bool = False


class MCQOptionCreate(MCQOptionBase):
    """Request schema for creating an MCQ option."""

    pass


class MCQOptionResponse(MCQOptionBase):
    """Response schema for an MCQ option."""

    id: str


class MCQOptionUpdate(BaseSchema):
    """Request schema for updating an MCQ option."""

    text: str | None = Field(None, min_length=1, max_length=2000)
    is_correct: bool | None = None


# =============================================================================
# MCQ Question Schemas
# =============================================================================


class MCQQuestionBase(BaseSchema):
    """Base schema for MCQ questions."""

    question_text: str = Field(min_length=1, max_length=10000)
    explanation: str | None = Field(None, max_length=5000)
    tags: list[str] = Field(default_factory=list)
    difficulty: MCQDifficultySchema = MCQDifficultySchema.MEDIUM

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags are non-empty strings."""
        return [tag.strip() for tag in v if tag.strip()]


class MCQQuestionCreate(MCQQuestionBase):
    """Request schema for creating an MCQ question."""

    bank_id: str = Field(min_length=1, max_length=100)
    options: list[MCQOptionCreate] = Field(min_length=2, max_length=10)

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[MCQOptionCreate]) -> list[MCQOptionCreate]:
        """Validate that at least one option is correct."""
        if not any(opt.is_correct for opt in v):
            raise ValueError("At least one option must be marked as correct")
        return v


class MCQQuestionUpdate(BaseSchema):
    """Request schema for updating an MCQ question."""

    question_text: str | None = Field(None, min_length=1, max_length=10000)
    explanation: str | None = Field(None, max_length=5000)
    tags: list[str] | None = None
    difficulty: MCQDifficultySchema | None = None
    options: list[MCQOptionCreate] | None = Field(None, min_length=2, max_length=10)

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[MCQOptionCreate] | None) -> list[MCQOptionCreate] | None:
        """Validate that at least one option is correct if options provided."""
        if v is not None and not any(opt.is_correct for opt in v):
            raise ValueError("At least one option must be marked as correct")
        return v


class MCQQuestionResponse(BaseSchema):
    """Response schema for an MCQ question."""

    id: str
    bank_id: str
    question_text: str
    options: list[MCQOptionResponse]
    explanation: str | None
    tags: list[str]
    difficulty: MCQDifficultySchema
    created_by: str
    created_at: datetime
    updated_at: datetime | None


class MCQQuestionListParams(BaseSchema):
    """Query parameters for listing MCQ questions."""

    bank_id: str | None = None
    difficulty: MCQDifficultySchema | None = None
    tags: list[str] | None = None
    created_by: str | None = None
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)


# =============================================================================
# MCQ Bank Schemas
# =============================================================================


class MCQBankBase(BaseSchema):
    """Base schema for MCQ banks."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate bank name."""
        if not v.replace("-", "").replace("_", "").replace(" ", "").isalnum():
            raise ValueError("Name must be alphanumeric with dashes, underscores, or spaces")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags are non-empty strings."""
        return [tag.strip() for tag in v if tag.strip()]


class MCQBankCreate(MCQBankBase):
    """Request schema for creating an MCQ bank."""

    pass


class MCQBankUpdate(BaseSchema):
    """Request schema for updating an MCQ bank."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    tags: list[str] | None = None
    is_public: bool | None = None


class MCQBankResponse(BaseSchema):
    """Response schema for an MCQ bank."""

    id: str
    name: str
    description: str | None
    tags: list[str]
    is_public: bool
    owner_id: str
    question_count: int = 0
    created_at: datetime
    updated_at: datetime | None


class MCQBankListParams(BaseSchema):
    """Query parameters for listing MCQ banks."""

    owner_id: str | None = None
    is_public: bool | None = None
    tags: list[str] | None = None
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)


class MCQBankSummary(BaseSchema):
    """Summary schema for MCQ bank listing."""

    id: str
    name: str
    description: str | None
    owner_id: str
    question_count: int
    is_public: bool
    created_at: datetime


# =============================================================================
# MCQ Submission Schemas
# =============================================================================


class MCQAnswerSubmission(BaseSchema):
    """Request schema for submitting an answer."""

    question_id: str
    selected_option_id: str


class MCQAnswerResponse(BaseSchema):
    """Response schema for an answer submission."""

    question_id: str
    selected_option_id: str
    correct_option_id: str
    is_correct: bool
    explanation: str | None


class MCQSubmissionCreate(BaseSchema):
    """Request schema for submitting multiple answers."""

    bank_id: str
    answers: list[MCQAnswerSubmission] = Field(min_length=1)


class MCQSubmissionResponse(BaseSchema):
    """Response schema for a submission."""

    id: str
    bank_id: str
    user_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    answers: list[MCQAnswerResponse]
    submitted_at: datetime


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "MCQDifficultySchema",
    # Option
    "MCQOptionBase",
    "MCQOptionCreate",
    "MCQOptionResponse",
    "MCQOptionUpdate",
    # Question
    "MCQQuestionBase",
    "MCQQuestionCreate",
    "MCQQuestionUpdate",
    "MCQQuestionResponse",
    "MCQQuestionListParams",
    # Bank
    "MCQBankBase",
    "MCQBankCreate",
    "MCQBankUpdate",
    "MCQBankResponse",
    "MCQBankListParams",
    "MCQBankSummary",
    # Submission
    "MCQAnswerSubmission",
    "MCQAnswerResponse",
    "MCQSubmissionCreate",
    "MCQSubmissionResponse",
]