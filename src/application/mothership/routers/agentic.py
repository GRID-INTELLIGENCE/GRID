"""FastAPI router for agentic system endpoints."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.mothership.db.engine import get_async_sessionmaker
from application.mothership.repositories.agentic import AgenticRepository
from application.mothership.schemas.agentic import (
    AgentExperienceResponse,
    CaseCreateRequest,
    CaseEnrichRequest,
    CaseExecuteRequest,
    CaseResponse,
    ReferenceFileResponse,
)
from grid.agentic import AgenticSystem
from grid.agentic.event_bus import get_event_bus
from grid.agentic.events import CaseCategorizedEvent, CaseCreatedEvent, CaseReferenceGeneratedEvent
from tools.agent_prompts.processing_unit import ProcessingUnit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agentic", tags=["agentic"])

# Knowledge base path
KNOWLEDGE_BASE_PATH = Path("tools/agent_prompts")
REFERENCE_OUTPUT_PATH = Path(".case_references")


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Get async database session."""
    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        yield session


def get_agentic_system(session: AsyncSession = Depends(get_async_session)) -> AgenticSystem:
    """Get agentic system instance."""
    repository = AgenticRepository(session)
    event_bus = get_event_bus()
    return AgenticSystem(
        knowledge_base_path=KNOWLEDGE_BASE_PATH,
        event_bus=event_bus,
        repository=repository,
    )


def get_processing_unit():
    """Get processing unit instance using tools integration."""
    from application.integration.tools_provider import get_tools_provider

    provider = get_tools_provider()
    processor = provider.get_agent_processor(
        required=True,  # Agent processor is required for agentic endpoints
        knowledge_base_path=str(KNOWLEDGE_BASE_PATH),
    )

    if processor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent processor (ProcessingUnit) is not available. Ensure tools.agent_prompts is properly installed.",
        )

    return processor


from application.mothership.dependencies import RequiredAuth


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    request: CaseCreateRequest,
    auth: RequiredAuth,
    processing_unit=Depends(get_processing_unit),
    agentic_system: AgenticSystem = Depends(get_agentic_system),
) -> CaseResponse:
    """Create a new case (receptionist intake).

    This endpoint receives raw input and processes it through the receptionist workflow.
    """
    try:
        # Process input through processing unit
        result = processing_unit.process_input(
            raw_input=request.raw_input,
            user_context=request.user_context,
            examples=request.examples or [],
            scenarios=request.scenarios or [],
        )

        # Emit case.created event
        created_event = CaseCreatedEvent(
            case_id=result.case_id,
            raw_input=request.raw_input,
            user_id=request.user_id,
            examples=request.examples or [],
            scenarios=request.scenarios or [],
        )
        await agentic_system.event_bus.publish(created_event.to_dict())

        # Emit case.categorized event
        categorized_event = CaseCategorizedEvent(
            case_id=result.case_id,
            category=result.category.value,
            priority=result.structured_data.priority,
            confidence=result.structured_data.confidence,
            structured_data=result.structured_data.__dict__,
            labels=result.structured_data.labels,
            keywords=result.structured_data.keywords,
        )
        await agentic_system.event_bus.publish(categorized_event.to_dict())

        # Emit case.reference_generated event
        reference_event = CaseReferenceGeneratedEvent(
            case_id=result.case_id,
            reference_file_path=result.reference_file_path,
            recommended_roles=result.structured_data.__dict__.get("recommended_roles", []),
            recommended_tasks=result.structured_data.__dict__.get("recommended_tasks", []),
        )
        await agentic_system.event_bus.publish(reference_event.to_dict())

        return CaseResponse(
            case_id=result.case_id,
            status="categorized",
            category=result.category.value,
            priority=result.structured_data.priority,
            confidence=result.structured_data.confidence,
            reference_file_path=result.reference_file_path,
            events=["case.created", "case.categorized", "case.reference_generated"],
            created_at=result.timestamp,
            updated_at=result.timestamp,
            completed_at="",
            outcome="",
            solution="",
        )

    except Exception as e:
        logger.error(f"Error creating case: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating case: {str(e)}",
        ) from e


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    agentic_system: AgenticSystem = Depends(get_agentic_system),
) -> CaseResponse:
    """Get case status and details."""
    if not agentic_system.repository:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Repository not available",
        )

    case = await agentic_system.repository.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )

    # Get event history
    events = await agentic_system.event_bus.get_event_history(event_type=None, limit=100)
    case_events: list[str] = [str(e.get("event_type", "")) for e in events if e.get("case_id") == case_id]

    return CaseResponse(
        case_id=case.case_id,
        status=case.status,
        category=case.category,
        priority=case.priority,
        confidence=case.confidence,
        reference_file_path=case.reference_file_path,
        events=case_events,
        created_at=case.created_at.isoformat() if case.created_at else "",
        updated_at=case.updated_at.isoformat() if case.updated_at else None,
        completed_at=case.completed_at.isoformat() if case.completed_at else None,
        outcome=case.outcome,
        solution=case.solution,
    )


@router.post("/cases/{case_id}/enrich", response_model=CaseResponse)
async def enrich_case(
    case_id: str,
    request: CaseEnrichRequest,
    processing_unit=Depends(get_processing_unit),
    agentic_system: AgenticSystem = Depends(get_agentic_system),
) -> CaseResponse:
    """Enrich an existing case with additional user input."""
    try:
        enriched = processing_unit.enrich_with_user_input(
            case_id=case_id,
            additional_context=request.additional_context,
            examples=request.examples or [],
            scenarios=request.scenarios or [],
        )

        # Update repository if available
        if agentic_system.repository:
            await agentic_system.repository.update_case_status(
                case_id=case_id,
                structured_data=enriched.get("structured_data", {}),
            )

        # Get updated case
        if agentic_system.repository:
            case = await agentic_system.repository.get_case(case_id)
            if case:
                events = await agentic_system.event_bus.get_event_history(event_type=None, limit=100)
                case_events: list[str] = [str(e.get("event_type", "")) for e in events if e.get("case_id") == case_id]

                return CaseResponse(
                    case_id=case.case_id,
                    status=case.status,
                    category=case.category,
                    priority=case.priority,
                    confidence=case.confidence,
                    reference_file_path=case.reference_file_path,
                    events=case_events,
                    created_at=case.created_at.isoformat() if case.created_at else "",
                    updated_at=case.updated_at.isoformat() if case.updated_at else None,
                    completed_at="",
                    outcome="",
                    solution="",
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )

    except Exception as e:
        logger.error(f"Error enriching case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enriching case: {str(e)}",
        ) from e


@router.post("/cases/{case_id}/execute", response_model=CaseResponse)
async def execute_case(
    case_id: str,
    request: CaseExecuteRequest,
    agentic_system: AgenticSystem = Depends(get_agentic_system),
) -> CaseResponse:
    """Execute a case (lawyer processes case)."""
    if not agentic_system.repository:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Repository not available",
        )

    # Get case
    case = await agentic_system.repository.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )

    # Check if case is ready for execution
    if case.status not in ["reference_generated", "categorized"] and not request.force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case {case_id} is not ready for execution. Status: {case.status}",
        )

    if not case.reference_file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case {case_id} has no reference file",
        )

    try:
        # Execute case
        await agentic_system.execute_case(
            case_id=case_id,
            reference_file_path=case.reference_file_path,
            agent_role=request.agent_role,
            task=request.task,
        )

        # Get updated case
        case = await agentic_system.repository.get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {case_id} not found after execution",
            )

        events = await agentic_system.event_bus.get_event_history(event_type=None, limit=100)
        case_events: list[str] = [str(e.get("event_type", "")) for e in events if e.get("case_id") == case_id]

        return CaseResponse(
            case_id=case.case_id,
            status=case.status,
            category=case.category,
            priority=case.priority,
            confidence=case.confidence,
            reference_file_path=case.reference_file_path,
            events=case_events,
            created_at=case.created_at.isoformat() if case.created_at else "",
            updated_at=case.updated_at.isoformat() if case.updated_at else None,
            completed_at=case.completed_at.isoformat() if case.completed_at else "",
            outcome=case.outcome or "",
            solution=case.solution or "",
        )

    except Exception as e:
        logger.error(f"Error executing case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing case: {str(e)}",
        ) from e


@router.post("/cases/{case_id}/execute-iterative", summary="Execute iterative lawyer phase")
async def execute_case_iterative(
    case_id: str,
    max_iterations: int = 3,
    processing_unit: ProcessingUnit = Depends(get_processing_unit),
):
    """Execute the lawyer phase iteratively for a case."""
    try:
        case = await processing_unit.repository.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        result = await processing_unit.agentic_system.iterative_execute(
            case_id=case_id, reference_file_path=case.reference_file_path, max_iterations=max_iterations
        )

        await processing_unit.repository.update_case(
            case_id,
            {
                "status": "completed",
                "outcome": result["summary_report"]["final_outcome"],
                "solution": result["summary_report"]["summary"],
                "agent_experience": result["summary_report"]["audit_trail"],
            },
        )

        return result
    except Exception as e:
        logger.error(f"Error in iterative execution: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/cases/{case_id}/reference", summary="Get case reference file contents")
async def get_reference_file(
    case_id: str,
    processing_unit=Depends(get_processing_unit),
) -> ReferenceFileResponse:
    """Get reference file for a case."""
    reference = processing_unit.get_reference_file(case_id)
    if not reference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference file not found for case {case_id}",
        )

    return ReferenceFileResponse(
        case_id=case_id,
        reference_file_path=reference.get("reference_file_path", ""),
        content=reference,
        recommended_roles=reference.get("recommended_roles", []),
        recommended_tasks=reference.get("recommended_tasks", []),
        workflow=reference.get("recommended_workflow", []),
    )


@router.get("/experience", response_model=AgentExperienceResponse)
async def get_agent_experience(
    agentic_system: AgenticSystem = Depends(get_agentic_system),
) -> AgentExperienceResponse:
    """Get agent experience summary."""
    if not agentic_system.repository:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Repository not available",
        )

    experience = await agentic_system.repository.get_agent_experience()

    return AgentExperienceResponse(
        total_cases=experience.get("total_cases", 0),
        success_rate=experience.get("success_rate", 0.0),
        category_distribution=experience.get("category_distribution", {}),
        experience_by_category=experience.get("experience_by_category", {}),
        common_patterns=[],  # Would be populated from learning system
        learning_insights=[],  # Would be populated from learning system
    )
