from fastapi import FastAPI, WebSocket
from typing import List, Dict, Any

from .parameter_presets import ParameterPresetSystem
from .arena_integration import ArenaIntegration

app = FastAPI()

preset_system = ParameterPresetSystem()
# Dummy rules and goal for Arena
rules = [{"condition": "'REWARD' in context['action']", "action": "REWARD", "target": "Sample Reward"}]
goal = {"name": "Test Goal", "target_score": 100}
arena = ArenaIntegration(rules, goal)

@app.get("/api/resonance/parameters")
def get_parameters():
    # Placeholder for parameter listing
    return {"status": "ok", "parameters": []}

@app.put("/api/resonance/parameters/{name}")
def update_parameter(name: str, value: float):
    # Placeholder for parameter update
    return {"status": "ok", "parameter": name, "new_value": value}

@app.post("/api/resonance/presets/{preset}")
def apply_preset(preset: str):
    selected_preset = preset_system.get_preset(preset)
    if selected_preset:
        return {"status": "ok", "preset_applied": selected_preset}
    return {"status": "error", "message": "Preset not found"}

@app.get("/api/arena/status")
def get_arena_status():
    return {
        "score": arena.reward_system.score,
        "achievements": arena.reward_system.achievements,
        "violations": arena.penalty_system.violations
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # Dummy broadcast
        await websocket.send_text(f"Message text was: {data}")
