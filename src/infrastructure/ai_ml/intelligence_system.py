"""
Frontier Intelligence System for Southeast Asia Region
====================================================

AI/ML infrastructure component providing intelligent capabilities
for the modernized arena architecture with safety-first approach.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..event_bus.event_system import (  # type: ignore[import-not-found]
    Event,
    EventBus,
    EventHandler,
    EventResult,
    EventStatus,
)


class AISafetyLevel(Enum):
    """AI safety levels."""

    PERMITTED = "permitted"
    RESTRICTED = "restricted"
    PROHIBITED = "prohibited"


class DataSensitivity(Enum):
    """Data sensitivity levels."""

    PUBLIC = "public"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"


class ModelType(Enum):
    """Model types."""

    PREDICTIVE = "predictive"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    GENERATIVE = "generative"
    REINFORCEMENT = "reinforcement"


@dataclass
class AIRequest:
    """AI inference request."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = ""
    model_type: ModelType = ModelType.PREDICTIVE
    input_data: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    safety_level: AISafetyLevel = AISafetyLevel.PERMITTED
    data_sensitivity: DataSensitivity = DataSensitivity.PUBLIC
    user_context: str | None = None
    timestamp: float = field(default_factory=time.time)
    timeout: float = 30.0


@dataclass
class AIResponse:
    """AI inference response."""

    request_id: str
    model_name: str
    predictions: dict[str, Any] | None = None
    confidence: float = 0.0
    explanation: str | None = None
    safety_assessment: AISafetyLevel = AISafetyLevel.PERMITTED
    processing_time: float = 0.0
    model_version: str = ""
    timestamp: float = field(default_factory=time.time)
    error: str | None = None


@dataclass
class ModelMetadata:
    """Model metadata."""

    name: str
    version: str
    type: ModelType
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    safety_level: AISafetyLevel
    data_requirements: list[str]
    performance_metrics: dict[str, float]
    created_at: datetime
    updated_at: datetime
    tags: list[str] = field(default_factory=list)


class AISafetyGuard:
    """AI safety guard for input validation and output filtering."""

    def __init__(self):
        self.blocked_patterns = [
            r"\b(password|token|secret|key)\b",
            r"\b(social_security|ssn)\b",
            r"\b(credit_card|card_number)\b",
            r"\b(bank_account|account_number)\b",
        ]
        self.max_input_size = 10000  # characters
        self.max_output_size = 5000  # characters

    def validate_input(self, request: AIRequest) -> tuple[bool, str]:
        """Validate AI request input."""
        import re

        # Check data sensitivity vs safety level
        if request.data_sensitivity == DataSensitivity.CRITICAL:
            if request.safety_level != AISafetyLevel.PROHIBITED:
                return False, "Critical data requires PROHIBITED safety level"

        # Check input size
        input_str = json.dumps(request.input_data)
        if len(input_str) > self.max_input_size:
            return False, f"Input too large: {len(input_str)} > {self.max_input_size}"

        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return False, f"Input contains blocked pattern: {pattern}"

        return True, "Input validated"

    def sanitize_output(self, response: AIResponse) -> AIResponse:
        """Sanitize AI response output."""
        if response.predictions:
            # Remove any potential sensitive data
            predictions_str = json.dumps(response.predictions)

            # Truncate if too large
            if len(predictions_str) > self.max_output_size:
                response.predictions = {"error": "Output truncated due to size limit"}
                response.confidence = 0.0

            # Add safety disclaimer
            if response.safety_level != AISafetyLevel.PROHIBITED:
                response.explanation = (
                    f"{response.explanation or ''}\n" "[AI Safety: This response has been filtered and sanitized]"
                )

        return response


class ModelRegistry:
    """Registry for AI models."""

    def __init__(self):
        self.models: dict[str, ModelMetadata] = {}
        self.model_instances: dict[str, Any] = {}

    def register_model(self, metadata: ModelMetadata, model_instance: Any):
        """Register a model."""
        self.models[metadata.name] = metadata
        self.model_instances[metadata.name] = model_instance
        logging.info(f"Model registered: {metadata.name} v{metadata.version}")

    def get_model(self, model_name: str) -> Any | None:
        """Get model instance."""
        return self.model_instances.get(model_name)

    def get_metadata(self, model_name: str) -> ModelMetadata | None:
        """Get model metadata."""
        return self.models.get(model_name)

    def list_models(self, model_type: ModelType | None = None) -> list[ModelMetadata]:
        """List all models or models of specific type."""
        models = list(self.models.values())

        if model_type:
            models = [m for m in models if m.type == model_type]

        return models


class FeatureStore:
    """Feature store for ML features."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Any | None = None
        self.feature_definitions: dict[str, dict[str, Any]] = {}

    async def start(self):
        """Start feature store."""
        try:
            import redis.asyncio as redis

            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logging.info("Feature store connected to Redis")
        except Exception as e:
            logging.error(f"Failed to connect feature store: {e}")

    async def stop(self):
        """Stop feature store."""
        if self.redis_client:
            await self.redis_client.close()

    def register_feature(self, name: str, definition: dict[str, Any]):
        """Register a feature definition."""
        self.feature_definitions[name] = definition
        logging.info(f"Feature registered: {name}")

    async def get_features(self, entity_id: str, feature_names: list[str]) -> dict[str, Any]:
        """Get features for an entity."""
        if not self.redis_client:
            return {}

        features = {}
        for feature_name in feature_names:
            try:
                key = f"features:{entity_id}:{feature_name}"
                value = await self.redis_client.get(key)
                if value:
                    features[feature_name] = json.loads(value)
            except Exception as e:
                logging.error(f"Failed to get feature {feature_name}: {e}")

        return features

    async def set_features(self, entity_id: str, features: dict[str, Any], ttl: int = 3600):
        """Set features for an entity."""
        if not self.redis_client:
            return

        for feature_name, value in features.items():
            try:
                key = f"features:{entity_id}:{feature_name}"
                await self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logging.error(f"Failed to set feature {feature_name}: {e}")


class ExperimentTracker:
    """Experiment tracking for ML experiments."""

    def __init__(self, storage_path: str = "experiments"):
        self.storage_path = storage_path
        self.experiments: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def log_experiment(
        self,
        experiment_name: str,
        model_name: str,
        parameters: dict[str, Any],
        metrics: dict[str, float],
        tags: list[str] | None = None,
    ):
        """Log an experiment."""
        async with self._lock:
            experiment_id = str(uuid.uuid4())

            experiment = {
                "id": experiment_id,
                "name": experiment_name,
                "model_name": model_name,
                "parameters": parameters,
                "metrics": metrics,
                "tags": tags or [],
                "timestamp": time.time(),
            }

            self.experiments[experiment_id] = experiment
            await self._persist_experiment(experiment)

            logging.info(f"Experiment logged: {experiment_name} ({experiment_id})")
            return experiment_id

    async def get_best_model(self, experiment_name: str, metric: str = "accuracy") -> str | None:
        """Get best model for an experiment."""
        experiments = [
            exp for exp in self.experiments.values() if exp["name"] == experiment_name and metric in exp["metrics"]
        ]

        if not experiments:
            return None

        best_experiment = max(experiments, key=lambda x: x["metrics"][metric])
        return best_experiment["model_name"]

    async def _persist_experiment(self, experiment: dict[str, Any]):
        """Persist experiment to disk."""
        import os

        import aiofiles  # type: ignore[import-untyped]

        os.makedirs(self.storage_path, exist_ok=True)

        filename = f"{self.storage_path}/{experiment['id']}.json"
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(experiment, indent=2))


class FrontierIntelligenceSystem:
    """
    Main AI/ML system for the frontier intelligence infrastructure.
    """

    def __init__(
        self,
        region: str = "southeast_asia",
        redis_url: str = "redis://localhost:6379",
        event_bus: EventBus | None = None,
    ):
        self.region = region
        self.event_bus = event_bus

        self.model_registry = ModelRegistry()
        self.feature_store = FeatureStore(redis_url)
        self.experiment_tracker = ExperimentTracker()
        self.safety_guard = AISafetyGuard()

        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.response_cache: dict[str, AIResponse] = {}
        self.processing = False

        # Metrics
        self.requests_processed = 0
        self.requests_failed = 0
        self.average_processing_time = 0.0

        # Regional configuration
        self.regional_config = self._load_regional_config(region)

    def _load_regional_config(self, region: str) -> dict[str, Any]:
        """Load regional configuration."""
        configs = {
            "southeast_asia": {
                "timezone": "UTC+8",
                "languages": ["en", "zh", "ms", "th", "vi", "id", "tl"],
                "currencies": ["USD", "SGD", "MYR", "THB", "VND", "IDR", "PHP"],
                "regulations": ["PDPA", "PDPO", "PDPA"],
                "data_residency": True,
                "model_bias_protection": True,
            }
        }
        return configs.get(region, configs["southeast_asia"])

    async def start(self):
        """Start the intelligence system."""
        await self.feature_store.start()

        # Start processing loop
        self.processing = True
        asyncio.create_task(self._processing_loop())

        # Register event handlers if event bus provided
        if self.event_bus:
            self.event_bus.register_handler(AIRequestHandler(self))

        logging.info(f"Frontier Intelligence System started for {self.region}")

    async def stop(self):
        """Stop the intelligence system."""
        self.processing = False
        await self.feature_store.stop()
        logging.info("Frontier Intelligence System stopped")

    async def predict(
        self,
        model_name: str,
        input_data: dict[str, Any],
        safety_level: AISafetyLevel = AISafetyLevel.PERMITTED,
        data_sensitivity: DataSensitivity = DataSensitivity.PUBLIC,
        **kwargs,
    ) -> AIResponse:
        """Make a prediction."""
        request = AIRequest(
            model_name=model_name,
            input_data=input_data,
            safety_level=safety_level,
            data_sensitivity=data_sensitivity,
            parameters=kwargs,
        )

        # Add to queue
        await self.request_queue.put(request)

        # Wait for response (with timeout)
        start_time = time.time()
        while request.id not in self.response_cache:
            await asyncio.sleep(0.01)
            if time.time() - start_time > request.timeout:
                return AIResponse(request_id=request.id, model_name=model_name, error="Request timeout")

        response = self.response_cache.pop(request.id)
        return response

    async def _processing_loop(self):
        """Main processing loop for AI requests."""
        while self.processing:
            try:
                # Get request from queue
                request = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)

                # Process request
                response = await self._process_request(request)

                # Cache response
                self.response_cache[request.id] = response

                # Update metrics
                if response.error:
                    self.requests_failed += 1
                else:
                    self.requests_processed += 1

            except TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Processing loop error: {e}")

    async def _process_request(self, request: AIRequest) -> AIResponse:
        """Process an AI request."""
        start_time = time.time()

        try:
            # Safety validation
            is_valid, error_msg = self.safety_guard.validate_input(request)
            if not is_valid:
                return AIResponse(
                    request_id=request.id,
                    model_name=request.model_name,
                    error=f"Safety validation failed: {error_msg}",
                    safety_assessment=AISafetyLevel.PROHIBITED,
                )

            # Get model
            model = self.model_registry.get_model(request.model_name)
            if not model:
                return AIResponse(
                    request_id=request.id, model_name=request.model_name, error=f"Model not found: {request.model_name}"
                )

            # Get model metadata
            metadata = self.model_registry.get_metadata(request.model_name)

            # Check safety level compatibility
            if metadata.safety_level.value > request.safety_level.value:
                return AIResponse(
                    request_id=request.id,
                    model_name=request.model_name,
                    error=f"Insufficient safety level for model: {request.model_name}",
                )

            # Get features if needed
            features = {}
            if metadata.data_requirements:
                entity_id = request.input_data.get("entity_id", "default")
                features = await self.feature_store.get_features(entity_id, metadata.data_requirements)

            # Prepare input
            model_input = {**request.input_data, **features, **request.parameters}

            # Make prediction
            predictions = await self._predict_with_model(model, model_input)

            # Create response
            response = AIResponse(
                request_id=request.id,
                model_name=request.model_name,
                predictions=predictions.get("predictions"),
                confidence=predictions.get("confidence", 0.0),
                explanation=predictions.get("explanation"),
                safety_assessment=metadata.safety_level,
                model_version=metadata.version,
                processing_time=time.time() - start_time,
            )

            # Sanitize output
            response = self.safety_guard.sanitize_output(response)

            return response

        except Exception as e:
            return AIResponse(
                request_id=request.id,
                model_name=request.model_name,
                error=str(e),
                processing_time=time.time() - start_time,
            )

    async def _predict_with_model(self, model: Any, input_data: dict[str, Any]) -> dict[str, Any]:
        """Make prediction with model."""
        # This is a placeholder for actual model inference
        # In a real implementation, this would call the specific model

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Mock prediction
        return {
            "predictions": {"result": "mock_prediction"},
            "confidence": 0.85,
            "explanation": "Mock model prediction",
        }

    async def get_metrics(self) -> dict[str, Any]:
        """Get system metrics."""
        return {
            "region": self.region,
            "requests_processed": self.requests_processed,
            "requests_failed": self.requests_failed,
            "success_rate": (
                self.requests_processed / (self.requests_processed + self.requests_failed)
                if (self.requests_processed + self.requests_failed) > 0
                else 0
            ),
            "models_registered": len(self.model_registry.models),
            "queue_size": self.request_queue.qsize(),
            "regional_config": self.regional_config,
        }


class AIRequestHandler(EventHandler):
    """Event handler for AI requests."""

    def __init__(self, intelligence_system: FrontierIntelligenceSystem):
        self.intelligence_system = intelligence_system

    @property
    def event_types(self) -> list[str]:
        return ["ai.request", "ai.model.update"]

    async def handle(self, event: Event) -> EventResult:
        """Handle AI-related events."""
        start_time = time.time()

        try:
            if event.type == "ai.request":
                # Process AI request from event
                request_data = event.data

                response = await self.intelligence_system.predict(
                    model_name=request_data["model_name"],
                    input_data=request_data["input_data"],
                    safety_level=AISafetyLevel(request_data.get("safety_level", "permitted")),
                    data_sensitivity=DataSensitivity(request_data.get("data_sensitivity", "public")),
                )

                # Publish response event
                if self.intelligence_system.event_bus:
                    await self.intelligence_system.event_bus.publish(
                        "ai.response",
                        {
                            "request_id": response.request_id,
                            "predictions": response.predictions,
                            "confidence": response.confidence,
                            "error": response.error,
                        },
                        source="intelligence_system",
                    )

                return EventResult(
                    event_id=event.id,
                    status=EventStatus.COMPLETED,
                    result={"response_id": response.request_id},
                    processing_time=time.time() - start_time,
                )

            elif event.type == "ai.model.update":
                # Handle model update
                # This would trigger model reloading, etc.
                return EventResult(
                    event_id=event.id,
                    status=EventStatus.COMPLETED,
                    result={"model_updated": True},
                    processing_time=time.time() - start_time,
                )

        except Exception as e:
            return EventResult(
                event_id=event.id, status=EventStatus.FAILED, error=str(e), processing_time=time.time() - start_time
            )


# ============================================================================
# Example Usage
# ============================================================================


async def example_intelligence_setup():
    """Example setup of intelligence system."""
    # Create event bus
    event_bus = EventBus()
    await event_bus.start()

    # Create intelligence system
    intelligence = FrontierIntelligenceSystem(region="southeast_asia", event_bus=event_bus)
    await intelligence.start()

    # Register a mock model
    from unittest.mock import Mock

    mock_model = Mock()
    mock_model.predict.return_value = {"result": 0.85}

    metadata = ModelMetadata(
        name="risk_assessment",
        version="1.0.0",
        type=ModelType.CLASSIFICATION,
        description="Risk assessment model",
        input_schema={"features": "dict"},
        output_schema={"risk_score": "float"},
        safety_level=AISafetyLevel.PERMITTED,
        data_requirements=["credit_score", "income"],
        performance_metrics={"accuracy": 0.92},
        created_at=datetime.now(),
        updated_at=datetime.now(),
        tags=["risk", "finance"],
    )

    intelligence.model_registry.register_model(metadata, mock_model)

    # Make a prediction
    response = await intelligence.predict(
        model_name="risk_assessment",
        input_data={"entity_id": "user123", "income": 50000},
        safety_level=AISafetyLevel.PERMITTED,
    )

    print(f"Prediction response: {response}")

    # Get metrics
    metrics = await intelligence.get_metrics()
    print(f"Intelligence system metrics: {metrics}")

    return intelligence


if __name__ == "__main__":

    async def main():
        intelligence = await example_intelligence_setup()

        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await intelligence.stop()

    asyncio.run(main())
