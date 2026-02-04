"""
Arena Service
=============

Modern Arena service that provides cache, rewards, and ADSR envelope
functionality through a REST API. This service integrates Arena/The Chase
concepts into the GRID infrastructure.

ADSR Semantics:
- Attack: Initial resource acquisition (honor growth, cache allocation)
- Decay: Excess reduction (penalty application, priority reduction)
- Sustain: Maintained state during activity (constant resource levels)
- Release: Controlled release (TTL expiration, honor decay)

Features:
- Multi-level cache with TTL and soft-TTL
- Reward system with honor tracking
- ADSR envelope for behavioral feedback
- Honor decay scheduling
- Service mesh integration
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-not-found]
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "Arena", "the_chase", "python", "src"))

from the_chase.core.adsr_envelope import ADSREnvelope, EnvelopePhase  # type: ignore[import-not-found]
from the_chase.overwatch.rewards import Achievement, AchievementType, CharacterRewardState  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class ArenaPhase(str, Enum):
    """Arena phase matching ADSR envelope phases."""

    ATTACK = "attack"
    DECAY = "decay"
    SUSTAIN = "sustains"
    RELEASE = "release"
    IDLE = "idle"


class CacheEntryModel(BaseModel):
    """Model for cache entry."""

    key: str
    value: dict[str, Any]
    priority: float = 0.5
    ttl_seconds: float = 60.0
    soft_ttl_seconds: float | None = None
    reward_level: str = "neutral"
    penalty_level: str = "none"
    created_at: datetime | None = None
    expires_at: datetime | None = None


class CacheResponse(BaseModel):
    """Response model for cache operations."""

    success: bool
    entry: CacheEntryModel | None = None
    phase: ArenaPhase = ArenaPhase.IDLE
    amplitude: float = 0.0


class AchievementModel(BaseModel):
    """Model for achievements."""

    type: str
    points: int
    description: str = ""


class RewardStateModel(BaseModel):
    """Model for character reward state."""

    entity_id: str
    honor: float = 0.0
    level: str = "neutral"
    achievement_count: int = 0
    achievements: list[AchievementModel] = []


class RewardResponse(BaseModel):
    """Response model for reward operations."""

    success: bool
    state: RewardStateModel | None = None
    phase: ArenaPhase = ArenaPhase.IDLE
    amplitude: float = 0.0


class ADSRMetricsModel(BaseModel):
    """Model for ADSR envelope metrics."""

    phase: ArenaPhase
    amplitude: float
    velocity: float
    time_in_phase: float
    total_time: float
    peak_amplitude: float


class HonorDecayConfig(BaseModel):
    """Configuration for honor decay scheduling."""

    enabled: bool = True
    decay_rate: float = 0.01
    decay_interval_seconds: int = 86400
    threshold_honor: float = 10.0


class ArenaService:
    """
    Arena service providing cache, rewards, and ADSR envelope functionality.

    Integrates Arena/The Chase concepts into GRID infrastructure:
    - Cache layer with ADSR-inspired sustain/decay semantics
    - Reward system with honor tracking and decay
    - ADSR envelope for behavioral feedback
    """

    def __init__(self):
        self.app = FastAPI(
            title="Arena Service", description="Arena cache, rewards, and ADSR envelope service", version="1.0.0"
        )

        self.service_name = "arena_service"
        self.service_url = os.getenv("ARENA_SERVICE_URL", "http://localhost:8002")
        self.health_url = f"{self.service_url}/health"

        self.cache: dict[str, Any] = {}
        self.reward_states: dict[str, CharacterRewardState] = {}
        self.adsr_envelopes: dict[str, ADSREnvelope] = {}

        self.scheduler = AsyncIOScheduler()

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _get_or_create_envelope(self, entity_id: str) -> ADSREnvelope:
        """Get or create ADSR envelope for entity."""
        if entity_id not in self.adsr_envelopes:
            self.adsr_envelopes[entity_id] = ADSREnvelope()
        return self.adsr_envelopes[entity_id]

    def _get_envelope_metrics(self, envelope: ADSREnvelope) -> ADSRMetricsModel:
        """Convert envelope metrics to API model."""
        metrics = envelope.get_metrics()
        phase_map = {
            EnvelopePhase.ATTACK: ArenaPhase.ATTACK,
            EnvelopePhase.DECAY: ArenaPhase.DECAY,
            EnvelopePhase.SUSTAIN: ArenaPhase.SUSTAIN,
            EnvelopePhase.RELEASE: ArenaPhase.RELEASE,
            EnvelopePhase.IDLE: ArenaPhase.IDLE,
        }
        return ADSRMetricsModel(
            phase=phase_map.get(metrics.phase, ArenaPhase.IDLE),
            amplitude=metrics.amplitude,
            velocity=metrics.velocity,
            time_in_phase=metrics.time_in_phase,
            total_time=metrics.total_time,
            peak_amplitude=metrics.peak_amplitude,
        )

    def _start_decay_scheduler(self):
        """Start honor decay scheduler."""
        self.scheduler.add_job(self._apply_honor_decay, "interval", seconds=86400, id="honor_decay")
        self.scheduler.start()

    async def _apply_honor_decay(self):
        """Apply honor decay to all reward states."""
        for entity_id, state in list(self.reward_states.items()):
            if state.honor > 10.0:
                state.decay_honor(rate=0.01)
                logger.info(f"Applied honor decay to {entity_id}: {state.honor:.2f}")

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": self.service_name,
                "timestamp": datetime.now(UTC).isoformat(),
                "cache_entries": len(self.cache),
                "reward_states": len(self.reward_states),
                "active_envelopes": len([e for e in self.adsr_envelopes.values() if e.is_active()]),
            }

        @self.app.get("/")
        async def root():
            """Root endpoint with service info."""
            return {
                "service": "Arena Service",
                "version": "1.0.0",
                "description": "Arena cache, rewards, and ADSR envelope service",
                "endpoints": {
                    "cache": "/cache",
                    "rewards": "/rewards",
                    "adsr": "/adsr",
                    "health": "/health",
                },
            }

        @self.app.post("/cache/{entity_id}/trigger")
        async def trigger_cache_envelope(entity_id: str):
            """Trigger ADSR envelope for cache entry (attack phase)."""
            envelope = self._get_or_create_envelope(entity_id)
            envelope.trigger()
            metrics = self._get_envelope_metrics(envelope)
            return {"success": True, "phase": "attack", "metrics": metrics.model_dump()}

        @self.app.post("/cache/{entity_id}/release")
        async def release_cache_envelope(entity_id: str):
            """Release ADSR envelope for cache entry (release phase)."""
            envelope = self._get_or_create_envelope(entity_id)
            envelope.release()
            metrics = self._get_envelope_metrics(envelope)
            return {"success": True, "phase": "release", "metrics": metrics.model_dump()}

        @self.app.get("/cache/{entity_id}/metrics")
        async def get_cache_metrics(entity_id: str):
            """Get ADSR metrics for cache entry."""
            envelope = self._get_or_create_envelope(entity_id)
            envelope.update()
            metrics = self._get_envelope_metrics(envelope)
            return {"success": True, "metrics": metrics.model_dump()}

        @self.app.post("/rewards/{entity_id}/achievement")
        async def add_achievement(entity_id: str, achievement: AchievementModel, request: Request):
            """Add achievement to entity (triggers attack phase)."""
            if entity_id not in self.reward_states:
                self.reward_states[entity_id] = CharacterRewardState(entity_id=entity_id)

            state = self.reward_states[entity_id]
            achievement_type = AchievementType(achievement.type)
            new_achievement = Achievement(
                achievement_type=achievement_type, points=achievement.points, description=achievement.description
            )
            state.add_achievement(new_achievement)

            envelope = self._get_or_create_envelope(entity_id)
            envelope.trigger()

            return RewardResponse(
                success=True,
                state=RewardStateModel(
                    entity_id=state.entity_id,
                    honor=state.honor,
                    level=state.level.value,
                    achievement_count=state.achievement_count,
                    achievements=[
                        AchievementModel(type=a.type.value, points=a.points, description=a.description)
                        for a in state.achievements
                    ],
                ),
                phase=ArenaPhase.ATTACK,
                amplitude=envelope.quality,
            )

        @self.app.get("/rewards/{entity_id}")
        async def get_reward_state(entity_id: str):
            """Get reward state for entity."""
            if entity_id not in self.reward_states:
                self.reward_states[entity_id] = CharacterRewardState(entity_id=entity_id)

            state = self.reward_states[entity_id]
            envelope = self._get_or_create_envelope(entity_id)
            envelope.update()
            metrics = self._get_envelope_metrics(envelope)

            return RewardResponse(
                success=True,
                state=RewardStateModel(
                    entity_id=state.entity_id,
                    honor=state.honor,
                    level=state.level.value,
                    achievement_count=state.achievement_count,
                    achievements=[
                        AchievementModel(type=a.type.value, points=a.points, description=a.description)
                        for a in state.achievements
                    ],
                ),
                phase=metrics.phase,
                amplitude=metrics.amplitude,
            )

        @self.app.post("/rewards/{entity_id}/decay")
        async def decay_honor(entity_id: str, rate: float = 0.01):
            """Apply honor decay to entity."""
            if entity_id not in self.reward_states:
                raise HTTPException(status_code=404, detail="Entity not found")

            state = self.reward_states[entity_id]
            state.decay_honor(rate=rate)
            envelope = self._get_or_create_envelope(entity_id)
            envelope.release()

            return RewardResponse(
                success=True,
                state=RewardStateModel(
                    entity_id=state.entity_id,
                    honor=state.honor,
                    level=state.level.value,
                    achievement_count=state.achievement_count,
                    achievements=[],
                ),
                phase=ArenaPhase.RELEASE,
                amplitude=envelope.quality,
            )

        @self.app.get("/adsr/{entity_id}")
        async def get_adsr_metrics(entity_id: str):
            """Get ADSR envelope metrics for entity."""
            envelope = self._get_or_create_envelope(entity_id)
            envelope.update()
            metrics = self._get_envelope_metrics(envelope)
            return {"success": True, "metrics": metrics.model_dump()}

        @self.app.post("/adsr/{entity_id}/trigger")
        async def trigger_adsr(entity_id: str):
            """Trigger ADSR envelope (start attack phase)."""
            envelope = self._get_or_create_envelope(entity_id)
            envelope.trigger()
            metrics = self._get_envelope_metrics(envelope)
            return {"success": True, "phase": "attack", "metrics": metrics.model_dump()}

        @self.app.post("/adsr/{entity_id}/release")
        async def release_adsr(entity_id: str):
            """Release ADSR envelope (start release phase)."""
            envelope = self._get_or_create_envelope(entity_id)
            envelope.release()
            metrics = self._get_envelope_metrics(envelope)
            return {"success": True, "phase": "release", "metrics": metrics.model_dump()}


app = ArenaService().app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
