"""
Arena AI Service
================

This is an example AI service that demonstrates how to integrate with the
Arena API Gateway architecture. It includes safety checks, monitoring,
and service discovery integration.

The service provides AI-powered text generation with built-in safety
and compliance features.
"""

import asyncio
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ...ai_safety.safety import AISafetyManager

# Import Arena components
from ...api_gateway.authentication.auth import AuthManager
from ...monitoring.monitor import MonitoringManager
from ...service_mesh.discovery import ServiceDiscovery

logger = logging.getLogger(__name__)


class TextGenerationRequest(BaseModel):
    """Request model for text generation."""

    prompt: str = Field(..., min_length=1, max_length=1000, description="Text prompt for generation")
    max_tokens: int = Field(100, ge=10, le=500, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.1, le=2.0, description="Sampling temperature")
    model: str = Field("arena-gpt", description="Model to use for generation")


class TextGenerationResponse(BaseModel):
    """Response model for text generation."""

    generated_text: str
    model_used: str
    tokens_used: int
    safety_score: float
    processing_time: float
    timestamp: datetime


class ArenaAIService:
    """
    Example AI service for the Arena architecture.
    """

    def __init__(self) -> None:
        self.app: FastAPI = FastAPI(
            title="Arena AI Service",
            description="AI-powered text generation with safety and compliance",
            version="1.0.0",
        )

        # Initialize components
        self.auth_manager: AuthManager = AuthManager()
        self.monitoring: MonitoringManager = MonitoringManager()
        self.ai_safety: AISafetyManager = AISafetyManager()
        self.service_discovery: ServiceDiscovery = ServiceDiscovery()

        # Service configuration
        self.service_name: str = "ai_service"
        self.service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
        self.health_url: str = f"{self.service_url}/health"

        # Mock AI model (replace with actual model in production)
        self.mock_responses: list[str] = [
            "The Arena architecture provides dynamic API routing with built-in safety mechanisms.",
            "Service discovery enables automatic registration and health monitoring of microservices.",
            "AI safety checks prevent harmful content generation and ensure compliance.",
            "The monitoring system provides real-time metrics and alerting capabilities.",
        ]

        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Setup API routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": self.service_name,
                "timestamp": datetime.now(UTC).isoformat(),
                "version": "1.0.0",
            }

        @self.app.post("/generate", response_model=TextGenerationResponse)
        async def generate_text(
            request: TextGenerationRequest, req: Request, authenticated: bool = Depends(self._authenticate_request)
        ):
            """Generate text using AI model with safety checks."""
            start_time = asyncio.get_event_loop().time()

            try:
                # 1. AI Safety check
                safety_result = await self.ai_safety.check_request(req)
                if not safety_result["safe"]:
                    raise HTTPException(status_code=403, detail="Request flagged by AI safety system")

                # 2. Content safety analysis
                content_check = await self.ai_safety._analyze_content_safety(req)
                if not content_check.passed and content_check.severity.name == "CRITICAL":
                    raise HTTPException(status_code=403, detail="Content safety violation")

                # 3. Generate text (mock implementation)
                generated_text = await self._generate_text_mock(request)

                # 4. Post-generation safety check
                output_safety = await self._check_output_safety(generated_text)
                if not output_safety["safe"]:
                    logger.warning(f"Unsafe output detected: {output_safety['issues']}")
                    # In production, you might want to filter or reject unsafe outputs

                # 5. Calculate processing time
                processing_time = asyncio.get_event_loop().time() - start_time

                # 6. Record metrics
                await self.monitoring.record_request(req, {"status_code": 200}, processing_time, authenticated)

                # 7. Create response
                response = TextGenerationResponse(
                    generated_text=generated_text,
                    model_used=request.model,
                    tokens_used=len(generated_text.split()),
                    safety_score=output_safety.get("score", 0.8),
                    processing_time=round(processing_time, 3),
                    timestamp=datetime.now(UTC),
                )

                return response

            except HTTPException:
                raise
            except Exception as e:
                processing_time = asyncio.get_event_loop().time() - start_time
                await self.monitoring.record_error(req, str(e), processing_time)
                raise HTTPException(status_code=500, detail="Internal service error") from e

        @self.app.get("/models")
        async def list_models():
            """List available AI models."""
            return {
                "models": [
                    {
                        "name": "arena-gpt",
                        "description": "Arena-optimized GPT model with safety features",
                        "max_tokens": 500,
                        "safety_enabled": True,
                    }
                ]
            }

        @self.app.get("/metrics")
        async def get_metrics():
            """Get service metrics."""
            return self.monitoring.get_metrics_summary()

    async def _authenticate_request(self, request: Request) -> bool:
        """Authenticate the incoming request."""
        auth_result = await self.auth_manager.authenticate(request)
        return auth_result["authenticated"]

    async def _generate_text_mock(self, request: TextGenerationRequest) -> str:
        """
        Mock text generation - replace with actual AI model in production.
        """
        # Simulate processing time
        await asyncio.sleep(0.1)

        # Simple mock response based on prompt keywords
        prompt_lower = request.prompt.lower()

        if "arena" in prompt_lower:
            base_response = self.mock_responses[0]
        elif "service" in prompt_lower or "discovery" in prompt_lower:
            base_response = self.mock_responses[1]
        elif "safety" in prompt_lower or "compliance" in prompt_lower:
            base_response = self.mock_responses[2]
        elif "monitoring" in prompt_lower or "metrics" in prompt_lower:
            base_response = self.mock_responses[3]
        else:
            base_response = self.mock_responses[0]

        # Add some variation based on temperature
        if request.temperature > 1.0:
            base_response += " This response includes additional creative elements."
        elif request.temperature < 0.5:
            base_response = base_response.split(".")[0] + "."

        # Limit by max tokens
        words = base_response.split()
        if len(words) > request.max_tokens:
            base_response = " ".join(words[: request.max_tokens])

        return base_response

    async def _check_output_safety(self, text: str) -> dict[str, Any]:
        """
        Check the safety of generated output.
        """
        # Simple safety checks - replace with more sophisticated analysis
        unsafe_patterns = [r"(?i)(kill|harm|violence)", r"(?i)(illegal|criminal)", r"(?i)(hate|discrimination)"]

        issues = []
        for pattern in unsafe_patterns:
            if re.search(pattern, text):
                issues.append(f"Matched unsafe pattern: {pattern}")

        safety_score = 1.0 - (len(issues) * 0.2)  # Deduct 0.2 per issue
        safety_score = max(0.0, min(1.0, safety_score))

        return {"safe": len(issues) == 0, "score": safety_score, "issues": issues}

    async def register_with_discovery(self) -> None:
        """Register this service with the service discovery system."""
        try:
            _registration_data = {
                "service_name": self.service_name,
                "url": self.service_url,
                "health_url": self.health_url,
                "metadata": {
                    "version": "1.0.0",
                    "capabilities": ["text_generation", "safety_checks"],
                    "models": ["arena-gpt"],
                    "rate_limits": {"requests_per_minute": 60, "tokens_per_minute": 10000},
                },
                "tags": ["ai", "generation", "safety"],
            }

            # Register with service discovery (this would typically call the discovery API)
            logger.info(f"Registering service {self.service_name} with discovery")

            # In a real implementation, you would make an HTTP call to the discovery service
            # await self._register_with_discovery_api(registration_data)

        except Exception as e:
            logger.error(f"Failed to register with discovery: {str(e)}")

    async def start_background_tasks(self) -> None:
        """Start background tasks for the service."""
        # Start monitoring
        await self.monitoring.start()

        # Start AI safety monitoring
        asyncio.create_task(self.ai_safety.monitor_safety())

        # Register with service discovery
        await self.register_with_discovery()

        # Send heartbeats
        asyncio.create_task(self._send_heartbeats())

    async def _send_heartbeats(self) -> None:
        """Send periodic heartbeats to service discovery."""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds

                # This would typically call the discovery API
                # await self.service_discovery.update_heartbeat(self.service_name, self.instance_id)

                logger.debug("Sent heartbeat")

            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
                await asyncio.sleep(10)

    async def shutdown(self) -> None:
        """Shutdown the service."""
        await self.monitoring.stop()
        logger.info("AI service shutdown complete")


# Global service instance
service = ArenaAIService()

# Export the FastAPI app
app = service.app

if __name__ == "__main__":

    async def startup():
        await service.start_background_tasks()

    async def shutdown():
        await service.shutdown()

    # Add startup and shutdown events
    app.add_event_handler("startup", startup)
    app.add_event_handler("shutdown", shutdown)

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("AI_SERVICE_PORT", "8001")), reload=True)
