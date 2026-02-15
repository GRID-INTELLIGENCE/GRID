from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ...core.config import settings
from ...models.user import User
from ...models.inference import InferenceRequest, InferenceResponse
from ...core.security import get_current_active_user
from ...services.inference import InferenceService

router = APIRouter()

@router.post("/", response_model=InferenceResponse)
async def create_inference(
    request: InferenceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new inference request"""
    try:
        inference_service = InferenceService()
        result = await inference_service.process(request)

        # Log the request for auditing
        background_tasks.add_task(
            log_inference_request,
            user_id=current_user.username,
            request=request,
            response=result
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

@router.post("/async")
async def create_async_inference(
    request: InferenceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Create an asynchronous inference request"""
    try:
        # Queue the request for processing
        task_id = await queue_inference_task(request, current_user.username)

        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Inference request queued for processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue inference: {str(e)}")

@router.get("/status/{task_id}")
async def get_inference_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get the status of an asynchronous inference request"""
    try:
        status = await get_task_status(task_id, current_user.username)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail="Task not found")

@router.get("/models")
async def list_available_models(
    current_user: User = Depends(get_current_active_user)
):
    """List available inference models"""
    return {
        "models": ["gpt-3.5-turbo", "gpt-4", "claude-2", "local-model"],
        "default": "gpt-3.5-turbo"
    }

# Helper functions
async def log_inference_request(user_id: str, request: InferenceRequest, response: InferenceResponse):
    """Log inference request for auditing"""
    # Implementation would log to database/audit system
    pass

async def queue_inference_task(request: InferenceRequest, user_id: str) -> str:
    """Queue inference task for async processing"""
    # Implementation would add to task queue
    return "task_123"

async def get_task_status(task_id: str, user_id: str):
    """Get status of async task"""
    # Implementation would check task status
    return {"status": "completed", "result": "Sample result"}
