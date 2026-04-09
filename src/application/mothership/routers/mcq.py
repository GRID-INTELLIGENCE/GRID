"""
MCQ (Multiple Choice Questions) management endpoints.

Provides CRUD operations for MCQ banks and questions with ownership-based access control.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from application.mothership.dependencies import Auth, RateLimited, RequestContext
from application.mothership.schemas import ApiResponse, ResponseMeta
from application.mothership.schemas.mcq import (
    MCQAnswerResponse,
    MCQAnswerSubmission,
    MCQBankCreate,
    MCQBankListParams,
    MCQBankResponse,
    MCQBankSummary,
    MCQBankUpdate,
    MCQDifficultySchema,
    MCQOptionCreate,
    MCQOptionResponse,
    MCQQuestionCreate,
    MCQQuestionListParams,
    MCQQuestionResponse,
    MCQQuestionUpdate,
    MCQSubmissionCreate,
    MCQSubmissionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcq", tags=["mcq"])

# =============================================================================
# In-Memory Storage (prototype)
# =============================================================================

# Bank storage: bank_id -> MCQBankResponse
_mcq_banks: dict[str, MCQBankResponse] = {}

# Question storage: question_id -> MCQQuestionResponse
_mcq_questions: dict[str, MCQQuestionResponse] = {}

# Bank -> questions mapping: bank_id -> list[question_id]
_bank_questions: dict[str, list[str]] = {}


# =============================================================================
# Helper Functions
# =============================================================================


def _generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def _get_current_user_id(auth: Auth) -> str:
    """Extract user ID from auth context."""
    # Auth is a dependency that provides user context
    # In development mode, return a default user
    if hasattr(auth, "user_id") and auth.user_id:
        return auth.user_id
    return "dev-user"


def _check_bank_ownership(bank_id: str, user_id: str) -> MCQBankResponse:
    """Check if user owns the bank and return it."""
    bank = _mcq_banks.get(bank_id)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank {bank_id} not found",
        )
    if bank.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this bank",
        )
    return bank


# =============================================================================
# Bank Endpoints
# =============================================================================


@router.post("/banks", response_model=ApiResponse[MCQBankResponse], status_code=status.HTTP_201_CREATED)
async def create_bank(
    request: MCQBankCreate,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[MCQBankResponse]:
    """
    Create a new MCQ bank.

    Creates a new question bank owned by the authenticated user.

    Args:
        request: Bank creation details
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with created bank details
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    bank_id = _generate_id()
    now = datetime.now(UTC)

    bank = MCQBankResponse(
        id=bank_id,
        name=request.name,
        description=request.description,
        tags=request.tags,
        is_public=request.is_public,
        owner_id=user_id,
        question_count=0,
        created_at=now,
        updated_at=None,
    )

    _mcq_banks[bank_id] = bank
    _bank_questions[bank_id] = []

    logger.info("MCQ bank created: %s by user %s (request_id=%s)", bank_id, user_id, request_id)

    return ApiResponse(
        success=True,
        data=bank,
        message="Bank created successfully",
        meta=ResponseMeta(request_id=request_id),
    )


@router.get("/banks", response_model=ApiResponse[list[MCQBankSummary]])
async def list_banks(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
    params: MCQBankListParams = Depends(),
) -> ApiResponse[list[MCQBankSummary]]:
    """
    List MCQ banks.

    Returns banks owned by the user or public banks.

    Args:
        params: Query parameters
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with list of banks
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    # Filter banks
    banks = []
    for bank in _mcq_banks.values():
        # Include if owned by user or public
        if bank.owner_id == user_id or bank.is_public:
            # Apply filters
            if params.owner_id and bank.owner_id != params.owner_id:
                continue
            if params.is_public is not None and bank.is_public != params.is_public:
                continue
            if params.tags and not all(tag in bank.tags for tag in params.tags):
                continue
            banks.append(
                MCQBankSummary(
                    id=bank.id,
                    name=bank.name,
                    description=bank.description,
                    owner_id=bank.owner_id,
                    question_count=bank.question_count,
                    is_public=bank.is_public,
                    created_at=bank.created_at,
                )
            )

    # Pagination
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    paginated_banks = banks[start:end]

    return ApiResponse(
        success=True,
        data=paginated_banks,
        meta=ResponseMeta(request_id=request_id),
    )


@router.get("/banks/{bank_id}", response_model=ApiResponse[MCQBankResponse])
async def get_bank(
    bank_id: str,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[MCQBankResponse]:
    """
    Get an MCQ bank by ID.

    Args:
        bank_id: Bank ID
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with bank details

    Raises:
        HTTPException: If bank not found or not accessible
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    bank = _mcq_banks.get(bank_id)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank {bank_id} not found",
        )

    # Check access: owner or public
    if bank.owner_id != user_id and not bank.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this bank",
        )

    return ApiResponse(
        success=True,
        data=bank,
        meta=ResponseMeta(request_id=request_id),
    )


@router.put("/banks/{bank_id}", response_model=ApiResponse[MCQBankResponse])
async def update_bank(
    bank_id: str,
    request: MCQBankUpdate,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[MCQBankResponse]:
    """
    Update an MCQ bank.

    Args:
        bank_id: Bank ID
        request: Update details
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with updated bank details

    Raises:
        HTTPException: If bank not found or user not owner
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    bank = _check_bank_ownership(bank_id, user_id)

    # Apply updates
    if request.name is not None:
        bank.name = request.name
    if request.description is not None:
        bank.description = request.description
    if request.tags is not None:
        bank.tags = request.tags
    if request.is_public is not None:
        bank.is_public = request.is_public
    bank.updated_at = datetime.now(UTC)

    _mcq_banks[bank_id] = bank

    logger.info("MCQ bank updated: %s by user %s (request_id=%s)", bank_id, user_id, request_id)

    return ApiResponse(
        success=True,
        data=bank,
        message="Bank updated successfully",
        meta=ResponseMeta(request_id=request_id),
    )


@router.delete("/banks/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank(
    bank_id: str,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> None:
    """
    Delete an MCQ bank and all its questions.

    Args:
        bank_id: Bank ID
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Raises:
        HTTPException: If bank not found or user not owner
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    bank = _check_bank_ownership(bank_id, user_id)

    # Delete all questions in the bank
    question_ids = _bank_questions.get(bank_id, [])
    for qid in question_ids:
        _mcq_questions.pop(qid, None)

    # Delete bank
    _mcq_banks.pop(bank_id, None)
    _bank_questions.pop(bank_id, None)

    logger.info("MCQ bank deleted: %s by user %s (request_id=%s)", bank_id, user_id, request_id)


# =============================================================================
# Question Endpoints
# =============================================================================


@router.post("/questions", response_model=ApiResponse[MCQQuestionResponse], status_code=status.HTTP_201_CREATED)
async def create_question(
    request: MCQQuestionCreate,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[MCQQuestionResponse]:
    """
    Create a new MCQ question.

    Args:
        request: Question creation details
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with created question details

    Raises:
        HTTPException: If bank not found or user not owner
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    # Check bank ownership
    _check_bank_ownership(request.bank_id, user_id)

    question_id = _generate_id()
    now = datetime.now(UTC)

    # Create options with IDs
    options = [
        MCQOptionResponse(
            id=_generate_id(),
            text=opt.text,
            is_correct=opt.is_correct,
        )
        for opt in request.options
    ]

    question = MCQQuestionResponse(
        id=question_id,
        bank_id=request.bank_id,
        question_text=request.question_text,
        options=options,
        explanation=request.explanation,
        tags=request.tags,
        difficulty=request.difficulty,
        created_by=user_id,
        created_at=now,
        updated_at=None,
    )

    _mcq_questions[question_id] = question
    _bank_questions[request.bank_id].append(question_id)

    # Update bank question count
    bank = _mcq_banks[request.bank_id]
    bank.question_count = len(_bank_questions[request.bank_id])

    logger.info(
        "MCQ question created: %s in bank %s by user %s (request_id=%s)",
        question_id,
        request.bank_id,
        user_id,
        request_id,
    )

    return ApiResponse(
        success=True,
        data=question,
        message="Question created successfully",
        meta=ResponseMeta(request_id=request_id),
    )


@router.get("/questions", response_model=ApiResponse[list[MCQQuestionResponse]])
async def list_questions(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
    params: MCQQuestionListParams = Depends(),
) -> ApiResponse[list[MCQQuestionResponse]]:
    """
    List MCQ questions.

    Args:
        params: Query parameters
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with list of questions
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    questions = []

    # If bank_id specified, check access and filter
    if params.bank_id:
        bank = _mcq_banks.get(params.bank_id)
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bank {params.bank_id} not found",
            )
        if bank.owner_id != user_id and not bank.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this bank",
            )
        question_ids = _bank_questions.get(params.bank_id, [])
        for qid in question_ids:
            if qid in _mcq_questions:
                questions.append(_mcq_questions[qid])
    else:
        # List all questions user has access to
        for bank in _mcq_banks.values():
            if bank.owner_id == user_id or bank.is_public:
                for qid in _bank_questions.get(bank.id, []):
                    if qid in _mcq_questions:
                        questions.append(_mcq_questions[qid])

    # Apply filters
    if params.difficulty:
        questions = [q for q in questions if q.difficulty == params.difficulty]
    if params.tags:
        questions = [q for q in questions if all(tag in q.tags for tag in params.tags)]
    if params.created_by:
        questions = [q for q in questions if q.created_by == params.created_by]

    # Pagination
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    paginated_questions = questions[start:end]

    return ApiResponse(
        success=True,
        data=paginated_questions,
        meta=ResponseMeta(request_id=request_id),
    )


@router.get("/questions/{question_id}", response_model=ApiResponse[MCQQuestionResponse])
async def get_question(
    question_id: str,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[MCQQuestionResponse]:
    """
    Get an MCQ question by ID.

    Args:
        question_id: Question ID
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with question details

    Raises:
        HTTPException: If question not found or not accessible
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    question = _mcq_questions.get(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found",
        )

    # Check bank access
    bank = _mcq_banks.get(question.bank_id)
    if bank and bank.owner_id != user_id and not bank.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this question",
        )

    return ApiResponse(
        success=True,
        data=question,
        meta=ResponseMeta(request_id=request_id),
    )


@router.put("/questions/{question_id}", response_model=ApiResponse[MCQQuestionResponse])
async def update_question(
    question_id: str,
    request: MCQQuestionUpdate,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[MCQQuestionResponse]:
    """
    Update an MCQ question.

    Args:
        question_id: Question ID
        request: Update details
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with updated question details

    Raises:
        HTTPException: If question not found or user not owner
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    question = _mcq_questions.get(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found",
        )

    # Check bank ownership
    _check_bank_ownership(question.bank_id, user_id)

    # Apply updates
    if request.question_text is not None:
        question.question_text = request.question_text
    if request.explanation is not None:
        question.explanation = request.explanation
    if request.tags is not None:
        question.tags = request.tags
    if request.difficulty is not None:
        question.difficulty = request.difficulty
    if request.options is not None:
        # Regenerate option IDs
        question.options = [
            MCQOptionResponse(
                id=_generate_id(),
                text=opt.text,
                is_correct=opt.is_correct,
            )
            for opt in request.options
        ]
    question.updated_at = datetime.now(UTC)

    _mcq_questions[question_id] = question

    logger.info("MCQ question updated: %s by user %s (request_id=%s)", question_id, user_id, request_id)

    return ApiResponse(
        success=True,
        data=question,
        message="Question updated successfully",
        meta=ResponseMeta(request_id=request_id),
    )


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: str,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> None:
    """
    Delete an MCQ question.

    Args:
        question_id: Question ID
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Raises:
        HTTPException: If question not found or user not owner
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    question = _mcq_questions.get(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found",
        )

    # Check bank ownership
    _check_bank_ownership(question.bank_id, user_id)

    # Remove from bank questions list
    if question.bank_id in _bank_questions:
        _bank_questions[question.bank_id] = [qid for qid in _bank_questions[question.bank_id] if qid != question_id]

        # Update bank question count
        bank = _mcq_banks.get(question.bank_id)
        if bank:
            bank.question_count = len(_bank_questions[question.bank_id])

    # Delete question
    _mcq_questions.pop(question_id, None)

    logger.info("MCQ question deleted: %s by user %s (request_id=%s)", question_id, user_id, request_id)


# =============================================================================
# Submission Endpoints
# =============================================================================


@router.post("/submit", response_model=ApiResponse[MCQSubmissionResponse], status_code=status.HTTP_201_CREATED)
async def submit_answers(
    request: MCQSubmissionCreate,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[MCQSubmissionResponse]:
    """
    Submit answers for an MCQ bank.

    Args:
        request: Submission details
        _: Rate limiting enforcement
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with submission results

    Raises:
        HTTPException: If bank not found or not accessible
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = _get_current_user_id(auth)

    # Check bank access
    bank = _mcq_banks.get(request.bank_id)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank {request.bank_id} not found",
        )
    if bank.owner_id != user_id and not bank.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this bank",
        )

    # Process answers
    answers = []
    correct_count = 0

    for answer in request.answers:
        question = _mcq_questions.get(answer.question_id)
        if not question or question.bank_id != request.bank_id:
            continue

        # Find correct option
        correct_option = next((opt for opt in question.options if opt.is_correct), None)
        is_correct = answer.selected_option_id == correct_option.id if correct_option else False

        if is_correct:
            correct_count += 1

        answers.append(
            MCQAnswerResponse(
                question_id=answer.question_id,
                selected_option_id=answer.selected_option_id,
                correct_option_id=correct_option.id if correct_option else None,
                is_correct=is_correct,
                explanation=question.explanation,
            )
        )

    total_questions = len(request.answers)
    score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0.0

    submission = MCQSubmissionResponse(
        id=_generate_id(),
        bank_id=request.bank_id,
        user_id=user_id,
        total_questions=total_questions,
        correct_answers=correct_count,
        score_percentage=score_percentage,
        answers=answers,
        submitted_at=datetime.now(UTC),
    )

    logger.info(
        "MCQ submission: %s by user %s, score %.1f%% (request_id=%s)",
        submission.id,
        user_id,
        score_percentage,
        request_id,
    )

    return ApiResponse(
        success=True,
        data=submission,
        message="Submission processed successfully",
        meta=ResponseMeta(request_id=request_id),
    )
