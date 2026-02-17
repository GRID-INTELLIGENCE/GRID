"""
Tuning API Router for Resonance Parameters.

Provides endpoints for real-time parameter tuning, presets, and arena status.
"""

from typing import Any

from fastapi import APIRouter, WebSocket

from .arena_integration import ArenaIntegration
from .parameter_presets import ParameterPresetSystem

router = APIRouter(prefix="/tuning", tags=["tuning"])

preset_system = ParameterPresetSystem()
# Dummy rules and goal for Arena
rules = [{"condition": "'REWARD' in context['action']", "action": "REWARD", "target": "Sample Reward"}]
goal = {"name": "Test Goal", "target_score": 100}
arena = ArenaIntegration(rules, goal)


@router.get("/parameters")
def get_parameters() -> dict[str, Any]:
    """Get all tunable parameters."""
    return {"status": "ok", "parameters": []}


@router.put("/parameters/{name}")
def update_parameter(name: str, value: float) -> dict[str, Any]:
    """Update a specific parameter value."""
    return {"status": "ok", "parameter": name, "new_value": value}


@router.post("/presets/{preset}")
def apply_preset(preset: str) -> dict[str, Any]:
    """Apply a parameter preset."""
    selected_preset = preset_system.get_preset(preset)
    if selected_preset:
        return {"status": "ok", "preset_applied": selected_preset}
    return {"status": "error", "message": "Preset not found"}


@router.get("/arena/status")
def get_arena_status() -> dict[str, Any]:
    """Get current arena status including score and achievements."""
    return {
        "score": arena.reward_system.score,
        "achievements": arena.reward_system.achievements,
        "violations": arena.penalty_system.violations,
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time parameter updates."""
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
