"""
Inference API Router (Mothership Integration).

Wraps Grid API inference functionality for unified Mothership deployment.
Provides model inference endpoints with Mothership authentication.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from application.mothership.dependencies import Auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inference", tags=["inference"])


class InferenceRequest(BaseModel):
    """Inference request payload."""

    prompt: str = Field(..., description="Prompt text for inference", min_length=1)
    model: str | None = Field(default=None, description="Model to use for inference")
    max_tokens: int | None = Field(default=None, description="Maximum tokens to generate")
    temperature: float | None = Field(default=0.7, description="Sampling temperature", ge=0.0, le=2.0)
    context: dict[str, Any] | None = Field(default=None, description="Additional context")


class InferenceResponse(BaseModel):
    """Inference response."""

    result: str = Field(..., description="Generated result")
    model: str = Field(..., description="Model used for inference")
    tokens_used: int = Field(default=0, description="Number of tokens used")
    processing_time: float = Field(..., description="Processing time in seconds")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


# In-memory task store for async inference (replace with Redis/Celery for production)
_inference_tasks: dict[str, dict[str, Any]] = {}


@router.post("/", response_model=InferenceResponse)
async def create_inference(
    request: InferenceRequest,
    background_tasks: BackgroundTasks,
    auth: Auth = Depends(),
):
    """Create a new inference request."""
    try:
        # Import here to avoid circular dependencies
        from grid.services.inference import InferenceService as GridInferenceService

        inference_service = GridInferenceService()

        # Convert to Grid model
        from grid.models.inference import InferenceRequest as GridInferenceRequest

        grid_request = GridInferenceRequest(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            context=request.context or {},
        )

        result = await inference_service.process(grid_request)

        # Log the request for auditing
        user_id = auth.get("user_id", "anonymous")
        background_tasks.add_task(
            _log_inference_request,
            user_id=user_id,
            request=request,
            response=result,
        )

        return InferenceResponse(
            result=result.result,
            model=result.model,
            tokens_used=result.tokens_used,
            processing_time=result.processing_time,
            metadata=result.metadata,
        )
    except ImportError as e:
        logger.error(f"Grid inference service not available: {e}")
        raise HTTPException(status_code=503, detail="Inference service not available")
    except Exception as e:
        logger.exception("Inference failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@router.post("/async")
async def create_async_inference(
    request: InferenceRequest,
    background_tasks: BackgroundTasks,
    auth: Auth = Depends(),
):
    """Create an asynchronous inference request."""
    try:
        user_id = auth.get("user_id", "anonymous")
        task_id = await _queue_inference_task(request, user_id, background_tasks=background_tasks)
        return {"task_id": task_id, "status": "queued", "message": "Inference request queued for processing"}
    except Exception as e:
        logger.exception("Failed to queue inference: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to queue inference: {str(e)}")


@router.get("/status/{task_id}")
async def get_inference_status(task_id: str, auth: Auth = Depends()):
    """Get the status of an asynchronous inference request."""
    try:
        user_id = auth.get("user_id", "anonymous")
        status = await _get_task_status(task_id, user_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to get task status: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/models")
async def list_available_models(auth: Auth = Depends()):
    """List available inference models."""
    return {
        "models": ["gpt-3.5-turbo", "gpt-4", "claude-2", "local-llama", "ollama-llama3"],
        "default": "ollama-llama3",
    }


async def _log_inference_request(user_id: str, request: InferenceRequest, response: InferenceResponse) -> None:
    """Log inference request for auditing."""
    try:
        from grid.security.audit_logger import AuditEventType, get_audit_logger

        audit = get_audit_logger()
        if audit:
            audit.log_event(
                event_type=AuditEventType.INFERENCE_REQUEST,
                message="Inference request processed",
                user_id=user_id,
                resource="inference",
                metadata={
                    "model": request.model,
                    "tokens_used": response.tokens_used,
                    "processing_time": response.processing_time,
                },
            )
    except Exception as e:
        logger.warning(f"Failed to log inference request: {e}")


async def _process_queued_inference(task_id: str, request: InferenceRequest, user_id: str) -> None:
    """Background processor for queued inference tasks."""
    try:
        from grid.models.inference import InferenceRequest as GridInferenceRequest
        from grid.services.inference import InferenceService as GridInferenceService

        service = GridInferenceService()
        grid_request = GridInferenceRequest(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            context=request.context or {},
        )
        result = await service.process(grid_request)
        _inference_tasks[task_id]["status"] = "completed"
        _inference_tasks[task_id]["result"] = {
            "result": result.result,
            "model": result.model,
            "tokens_used": result.tokens_used,
            "processing_time": result.processing_time,
            "metadata": result.metadata,
        }
    except Exception as e:
        logger.exception("Queued inference failed: %s", e)
        _inference_tasks[task_id]["status"] = "failed"
        _inference_tasks[task_id]["error"] = str(e)


async def _queue_inference_task(
    request: InferenceRequest, user_id: str, background_tasks: BackgroundTasks | None = None
) -> str:
    """Queue inference task for async processing."""
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    _inference_tasks[task_id] = {"status": "queued", "user_id": user_id, "request": request.model_dump()}
    if background_tasks:
        background_tasks.add_task(_process_queued_inference, task_id, request, user_id)
    else:
        asyncio.create_task(_process_queued_inference(task_id, request, user_id))
    return task_id


async def _get_task_status(task_id: str, user_id: str) -> dict[str, Any]:
    """Get status of async task."""
    if task_id not in _inference_tasks:
        raise ValueError("Task not found")
    rec = _inference_tasks[task_id]
    if rec.get("user_id") != user_id:
        raise ValueError("Task not found")
    out: dict[str, Any] = {"status": rec["status"]}
    if rec["status"] == "completed" and "result" in rec:
        out["result"] = rec["result"]
    if rec["status"] == "failed" and "error" in rec:
        out["error"] = rec["error"]
    return out
