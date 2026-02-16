import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ...core.security import get_current_active_user
from ...models.inference import InferenceRequest, InferenceResponse
from ...models.user import User
from ...security.audit_logger import AuditEventType, get_audit_logger
from ...services.inference import InferenceService

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory task store for async inference (replace with Redis/Celery for production)
_inference_tasks: dict[str, dict[str, Any]] = {}


@router.post("/", response_model=InferenceResponse)
async def create_inference(
    request: InferenceRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_active_user)
):
    """Create a new inference request"""
    try:
        inference_service = InferenceService()
        result = await inference_service.process(request)

        # Log the request for auditing
        background_tasks.add_task(
            log_inference_request, user_id=current_user.username, request=request, response=result
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@router.post("/async")
async def create_async_inference(
    request: InferenceRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_active_user)
):
    """Create an asynchronous inference request"""
    try:
        task_id = await queue_inference_task(
            request, current_user.username, background_tasks=background_tasks
        )
        return {"task_id": task_id, "status": "queued", "message": "Inference request queued for processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue inference: {str(e)}")


@router.get("/status/{task_id}")
async def get_inference_status(task_id: str, current_user: User = Depends(get_current_active_user)):
    """Get the status of an asynchronous inference request"""
    try:
        status = await get_task_status(task_id, current_user.username)
        return status
    except Exception:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/models")
async def list_available_models(current_user: User = Depends(get_current_active_user)):
    """List available inference models"""
    return {"models": ["gpt-3.5-turbo", "gpt-4", "claude-2", "local-model"], "default": "gpt-3.5-turbo"}


# Helper functions
async def log_inference_request(user_id: str, request: InferenceRequest, response: InferenceResponse) -> None:
    """Log inference request for auditing."""
    audit = get_audit_logger()
    if audit:
        audit.log_event(
            event_type=AuditEventType.INFERENCE_REQUEST,
            message="Inference request processed",
            user_id=user_id,
            resource="inference",
            metadata={
                "model": request.model,
                "tokens_used": getattr(response, "tokens_used", None),
                "processing_time": getattr(response, "processing_time", None),
            },
        )


async def _process_queued_inference(task_id: str, request: InferenceRequest, user_id: str) -> None:
    """Background processor for queued inference tasks."""
    try:
        service = InferenceService()
        result = await service.process(request)
        _inference_tasks[task_id]["status"] = "completed"
        _inference_tasks[task_id]["result"] = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    except Exception as e:
        logger.exception("Queued inference failed: %s", e)
        _inference_tasks[task_id]["status"] = "failed"
        _inference_tasks[task_id]["error"] = str(e)


async def queue_inference_task(
    request: InferenceRequest, user_id: str, background_tasks: BackgroundTasks | None = None
) -> str:
    """Queue inference task for async processing."""
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    _inference_tasks[task_id] = {"status": "queued", "user_id": user_id, "request": request}
    if background_tasks:
        background_tasks.add_task(_process_queued_inference, task_id, request, user_id)
    else:
        asyncio.create_task(_process_queued_inference(task_id, request, user_id))
    return task_id


async def get_task_status(task_id: str, user_id: str) -> dict[str, Any]:
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
