"""MLflow integration for RAG engine tracking."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_MLFLOW_ENABLED = False
_EXPERIMENT_ID = None


def _try_enable_mlflow() -> None:
    """Enable MLflow autologging if available and configured."""
    global _MLFLOW_ENABLED, _EXPERIMENT_ID

    if _MLFLOW_ENABLED:
        return

    try:
        import mlflow
    except ImportError:
        logger.debug("MLflow not installed. Skipping autologging.")
        return

    # Check if MLflow is configured
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    registry_uri = os.getenv("MLFLOW_REGISTRY_URI")
    experiment_id = os.getenv("MLFLOW_EXPERIMENT_ID")

    if not tracking_uri or not experiment_id:
        logger.debug("MLflow not configured. Set MLFLOW_TRACKING_URI and MLFLOW_EXPERIMENT_ID.")
        return

    try:
        mlflow.set_tracking_uri(tracking_uri)
        if registry_uri:
            mlflow.set_registry_uri(registry_uri)

        # Set experiment
        if experiment_id:
            mlflow.set_experiment(experiment_id=experiment_id)
            _EXPERIMENT_ID = experiment_id

        # Enable autologging for supported frameworks
        try:
            mlflow.openai.autolog()
            logger.info("MLflow OpenAI autologging enabled")
        except Exception:
            pass

        try:
            mlflow.langchain.autolog()
            logger.info("MLflow LangChain autologging enabled")
        except Exception:
            pass

        _MLFLOW_ENABLED = True
        logger.info(f"MLflow autologging enabled (experiment: {experiment_id})")
    except Exception as e:
        logger.warning(f"Failed to enable MLflow autologging: {e}")


def mlflow_enabled() -> bool:
    """Check if MLflow autologging is enabled."""
    if not _MLFLOW_ENABLED:
        _try_enable_mlflow()
    return _MLFLOW_ENABLED


@contextmanager
def track_indexing(
    repo_path: str,
    chunk_size: int,
    overlap: int,
    embedding_model: str,
    embedding_provider: str,
):
    """Context manager for tracking indexing operations with MLflow.

    Args:
        repo_path: Path to repository being indexed
        chunk_size: Chunk size used
        overlap: Chunk overlap used
        embedding_model: Embedding model name
        embedding_provider: Embedding provider name

    Yields:
        None
    """
    if not mlflow_enabled():
        yield
        return

    import mlflow

    run_name = f"rag_index_{repo_path.replace('/', '_')[-50:]}"
    with mlflow.start_run(run_name=run_name, nested=True):
        mlflow.log_params(
            {
                "repo_path": repo_path,
                "chunk_size": chunk_size,
                "overlap": overlap,
                "embedding_model": embedding_model,
                "embedding_provider": embedding_provider,
                "operation": "indexing",
            }
        )
        try:
            yield
        except Exception as e:
            mlflow.log_param("error", str(e))
            raise


@contextmanager
def track_query(
    query_text: str,
    top_k: int,
    embedding_model: str,
    llm_model: str,
    temperature: float,
):
    """Context manager for tracking query operations with MLflow.

    Args:
        query_text: Query text
        top_k: Number of results retrieved
        embedding_model: Embedding model name
        llm_model: LLM model name
        temperature: Temperature used

    Yields:
        None
    """
    if not mlflow_enabled():
        yield
        return

    import mlflow

    run_name = f"rag_query_{query_text[:40].replace(' ', '_')}"
    with mlflow.start_run(run_name=run_name, nested=True):
        mlflow.log_params(
            {
                "query": query_text,
                "top_k": top_k,
                "embedding_model": embedding_model,
                "llm_model": llm_model,
                "temperature": temperature,
                "operation": "query",
            }
        )
        try:
            yield
        except Exception as e:
            mlflow.log_param("error", str(e))
            raise


def log_model_routing(
    query: str,
    embedding_provider: str,
    embedding_model: str,
    llm_provider: str,
    llm_model: str,
    reason: str,
):
    """Log model routing decision to MLflow.

    Args:
        query: Query text
        embedding_provider: Chosen embedding provider
        embedding_model: Chosen embedding model
        llm_provider: Chosen LLM provider
        llm_model: Chosen LLM model
        reason: Reason for routing decision
    """
    if not mlflow_enabled():
        return

    import mlflow

    mlflow.log_params(
        {
            "routing_query": query[:100],
            "routing_embedding_provider": embedding_provider,
            "routing_embedding_model": embedding_model,
            "routing_llm_provider": llm_provider,
            "routing_llm_model": llm_model,
            "routing_reason": reason,
        }
    )


def log_retrieval_metrics(
    num_retrieved: int,
    avg_distance: float,
    min_distance: float,
    max_distance: float,
):
    """Log retrieval metrics to MLflow.

    Args:
        num_retrieved: Number of documents retrieved
        avg_distance: Average distance score
        min_distance: Minimum distance score
        max_distance: Maximum distance score
    """
    if not mlflow_enabled():
        return

    import mlflow

    mlflow.log_metrics(
        {
            "retrieval_count": num_retrieved,
            "retrieval_avg_distance": avg_distance,
            "retrieval_min_distance": min_distance,
            "retrieval_max_distance": max_distance,
        }
    )


def log_answer_metrics(answer_length: int, generation_time_seconds: float):
    """Log answer generation metrics to MLflow.

    Args:
        answer_length: Length of generated answer
        generation_time_seconds: Time taken to generate answer
    """
    if not mlflow_enabled():
        return

    import mlflow

    mlflow.log_metrics(
        {
            "answer_length": answer_length,
            "generation_time_seconds": generation_time_seconds,
        }
    )
