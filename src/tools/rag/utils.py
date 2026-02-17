"""Utility functions for RAG system."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


def check_ollama_connection(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running and accessible.

    Args:
        base_url: Ollama base URL

    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(f"{base_url.rstrip('/')}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


def list_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """List available Ollama models.

    Args:
        base_url: Ollama base URL

    Returns:
        List of model names
    """
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(f"{base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
            data = response.model_dump_json()
            models = [model["name"] for model in data.get("models", [])]
            return models
    except Exception as e:
        raise RuntimeError(f"Failed to list Ollama models: {e}") from e


def find_embedding_model(
    preferred: str = "nomic-embed-text-v2-moe:latest", base_url: str = "http://localhost:11434"
) -> str | None:
    """Find available embedding model, trying alternatives.

    Args:
        preferred: Preferred model name
        base_url: Ollama base URL

    Returns:
        Available model name or None
    """
    try:
        models = list_ollama_models(base_url)

        # Check preferred first
        if preferred in models:
            return preferred

        # Try fuzzy match (without/with :latest)
        if ":" in preferred:
            no_tag = preferred.split(":")[0]
            if no_tag in models:
                return no_tag
        else:
            with_tag = f"{preferred}:latest"
            if with_tag in models:
                return with_tag

        # Try alternatives in order of preference
        alternatives = [
            "nomic-embed-text-v2-moe:latest",
            "nomic-embed-text-v2-moe",
            "nomic-embed-text-v2",
            "nomic-embed-text",
            "nomic-embed-text:latest",
        ]

        for alt in alternatives:
            if alt in models:
                return alt

        # Check for any nomic model
        for model in models:
            if "nomic" in model.lower() and "embed" in model.lower():
                return model

        return None
    except Exception:
        return None


def find_llm_model(preferred: str = "ministral-3:3b", base_url: str = "http://localhost:11434") -> str | None:
    """Find available LLM model, trying alternatives.

    Args:
        preferred: Preferred model name
        base_url: Ollama base URL

    Returns:
        Available model name or None
    """
    try:
        models = list_ollama_models(base_url)

        # Check preferred first
        if preferred in models:
            return preferred

        # Try fuzzy match (without/with :latest)
        if ":" in preferred:
            no_tag = preferred.split(":")[0]
            if no_tag in models:
                return no_tag
        else:
            with_tag = f"{preferred}:latest"
            if with_tag in models:
                return with_tag

        # Try alternatives
        alternatives = [
            "ministral-3:3b",
            "ministral",
            "gpt-oss-safeguard",
            "llama2",
            "mistral",
        ]

        for alt in alternatives:
            if alt in models:
                return alt

        return None
    except Exception:
        return None


def get_agent_ignore_patterns(repo_path: str) -> list[str]:
    """Load ignore patterns from .agentignore file in repo root.

    Args:
        repo_path: Path to the repository root

    Returns:
        List of ignore patterns
    """
    ignore_file = Path(repo_path) / ".agentignore"
    patterns = []

    if ignore_file.exists():
        try:
            with open(ignore_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception:  # noqa: S110 intentional silent handling
            pass

    return patterns


# =============================================================================
# Model Health Check System
# =============================================================================


class ModelHealthStatus(StrEnum):
    """Health status of a model."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DOWNLOADING = "downloading"


@dataclass
class ModelHealthInfo:
    """Health information for a model."""

    model_name: str
    status: ModelHealthStatus
    is_available: bool
    last_checked: datetime
    error_message: str | None = None
    details: dict[str, any] | None = None

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "status": self.status.value,
            "is_available": self.is_available,
            "last_checked": self.last_checked.isoformat(),
            "error_message": self.error_message,
            "details": self.details or {},
        }


@dataclass
class ModelHealthCheck:
    """Health check result for multiple models."""

    ollama_accessible: bool
    models: dict[str, ModelHealthInfo]
    timestamp: datetime

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary."""
        return {
            "ollama_accessible": self.ollama_accessible,
            "models": {name: info.to_dict() for name, info in self.models.items()},
            "timestamp": self.timestamp.isoformat(),
            "total_models": len(self.models),
            "healthy_models": sum(1 for m in self.models.values() if m.status == ModelHealthStatus.HEALTHY),
            "unhealthy_models": sum(1 for m in self.models.values() if m.status == ModelHealthStatus.UNHEALTHY),
        }


def check_model_health(
    model_name: str,
    base_url: str = "http://localhost:11434",
    timeout: float = 5.0,
) -> ModelHealthInfo:
    """
    Check if a specific Ollama model is healthy and available.

    Args:
        model_name: Name of the model to check
        base_url: Ollama base URL
        timeout: Request timeout in seconds

    Returns:
        ModelHealthInfo with status and details
    """
    now = datetime.now(UTC)

    try:
        # First check if Ollama is accessible
        if not check_ollama_connection(base_url):
            return ModelHealthInfo(
                model_name=model_name,
                status=ModelHealthStatus.UNHEALTHY,
                is_available=False,
                last_checked=now,
                error_message="Ollama service not accessible",
            )

        # Check if model exists in available models
        try:
            available_models = list_ollama_models(base_url)

            # Exact match
            if model_name in available_models:
                return ModelHealthInfo(
                    model_name=model_name,
                    status=ModelHealthStatus.HEALTHY,
                    is_available=True,
                    last_checked=now,
                    details={"matched_as": "exact", "total_available": len(available_models)},
                )

            # Try fuzzy match (strip :latest or add it)
            name_without_tag = model_name.split(":")[0] if ":" in model_name else model_name
            name_with_tag = f"{name_without_tag}:latest"

            for model in available_models:
                model_without_tag = model.split(":")[0]
                if model_without_tag == name_without_tag or model == name_with_tag:
                    return ModelHealthInfo(
                        model_name=model_name,
                        status=ModelHealthStatus.HEALTHY,
                        is_available=True,
                        last_checked=now,
                        details={
                            "matched_as": "fuzzy",
                            "available_as": model,
                            "total_available": len(available_models),
                        },
                    )

            # Model not found
            return ModelHealthInfo(
                model_name=model_name,
                status=ModelHealthStatus.UNHEALTHY,
                is_available=False,
                last_checked=now,
                error_message=f"Model '{model_name}' not found in available models",
                details={"available_models": available_models[:10]},  # Limit to first 10
            )

        except Exception as e:
            return ModelHealthInfo(
                model_name=model_name,
                status=ModelHealthStatus.UNHEALTHY,
                is_available=False,
                last_checked=now,
                error_message=f"Failed to list available models: {e}",
            )

    except Exception as e:
        return ModelHealthInfo(
            model_name=model_name,
            status=ModelHealthStatus.UNKNOWN,
            is_available=False,
            last_checked=now,
            error_message=f"Unexpected error during health check: {e}",
        )


def check_models_health(
    model_names: list[str],
    base_url: str = "http://localhost:11434",
    timeout: float = 5.0,
) -> ModelHealthCheck:
    """
    Check health of multiple models.

    Args:
        model_names: List of model names to check
        base_url: Ollama base URL
        timeout: Request timeout in seconds

    Returns:
        ModelHealthCheck with status for all models
    """
    ollama_accessible = check_ollama_connection(base_url)
    now = datetime.now(UTC)
    models: dict[str, ModelHealthInfo] = {}

    for model_name in model_names:
        if not ollama_accessible:
            models[model_name] = ModelHealthInfo(
                model_name=model_name,
                status=ModelHealthStatus.UNHEALTHY,
                is_available=False,
                last_checked=now,
                error_message="Ollama service not accessible",
            )
        else:
            models[model_name] = check_model_health(model_name, base_url, timeout)

    return ModelHealthCheck(
        ollama_accessible=ollama_accessible,
        models=models,
        timestamp=now,
    )


def check_rag_system_health(
    embedding_model: str = "nomic-embed-text:latest",
    llm_model: str = "ministral-3:3b",
    base_url: str = "http://localhost:11434",
) -> dict[str, any]:
    """
    Check health of the RAG system's model dependencies.

    Args:
        embedding_model: Name of embedding model to check
        llm_model: Name of LLM model to check
        base_url: Ollama base URL

    Returns:
        Dictionary with system health status
    """
    logger.info(f"Checking RAG system health (embedding={embedding_model}, llm={llm_model})")

    health_check = check_models_health([embedding_model, llm_model], base_url)

    # Determine overall system status
    embedding_info = health_check.models.get(embedding_model)
    llm_info = health_check.models.get(llm_model)

    if embedding_info and embedding_info.is_available and llm_info and llm_info.is_available:
        overall_status = "healthy"
    elif embedding_info and embedding_info.is_available:
        overall_status = "degraded"
        logger.warning(f"RAG system degraded: LLM model '{llm_model}' not available")
    elif llm_info and llm_info.is_available:
        overall_status = "degraded"
        logger.warning(f"RAG system degraded: Embedding model '{embedding_model}' not available")
    else:
        overall_status = "unhealthy"
        logger.error("RAG system unhealthy: Neither model is available")

    result = {
        "overall_status": overall_status,
        "ollama_accessible": health_check.ollama_accessible,
        "embedding_model": embedding_info.to_dict() if embedding_info else None,
        "llm_model": llm_info.to_dict() if llm_info else None,
        "timestamp": health_check.timestamp.isoformat(),
    }

    if overall_status != "healthy":
        logger.warning(f"RAG system health check result: {overall_status}")
    else:
        logger.info("RAG system health check: all models available")

    return result
