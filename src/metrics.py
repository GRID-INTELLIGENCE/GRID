"""Unified metrics collection for GRID system."""

from typing import Any

# Import components
try:
    from vection.core.stream_context import StreamContext
except ImportError:
    StreamContext = None

try:
    from tools.rag.rag_engine import RAGEngine
except ImportError:
    RAGEngine = None


def get_system_metrics() -> dict[str, Any]:
    """Get comprehensive system metrics.
    
    Returns:
        Dictionary with all available metrics
    """
    metrics = {}
    
    # StreamContext metrics
    if StreamContext is not None:
        try:
            stream_ctx = StreamContext.get_instance()
            metrics["stream_context"] = stream_ctx.get_stats()
        except Exception:
            metrics["stream_context"] = {"error": "StreamContext unavailable"}
    
    # RAG Engine metrics
    if RAGEngine is not None:
        try:
            # Create a temporary engine instance to get config-based metrics
            from tools.rag.config import RAGConfig
            config = RAGConfig.from_env()
            
            # Cache metrics (if cache enabled in config)
            if config.cache_enabled:
                engine = RAGEngine(config=config)
                metrics["rag_cache"] = engine.get_cache_stats()
                metrics["working_memory"] = engine.get_working_memory_stats()
            else:
                metrics["rag_cache"] = {"disabled": True}
                metrics["working_memory"] = {"disabled": True}
                
        except Exception as e:
            metrics["rag_cache"] = {"error": str(e)}
            metrics["working_memory"] = {"error": str(e)}
    
    # Basic system info
    metrics["system"] = {
        "components": {
            "stream_context": StreamContext is not None,
            "rag_engine": RAGEngine is not None,
        }
    }
    
    return metrics


def get_metrics_summary() -> dict[str, Any]:
    """Get simplified metrics summary for monitoring.
    
    Returns:
        Dictionary with key metrics for health checks
    """
    full_metrics = get_system_metrics()
    summary = {}
    
    # StreamContext health
    if "stream_context" in full_metrics:
        sc = full_metrics["stream_context"]
        if "error" not in sc:
            summary["sessions"] = {
                "active": sc.get("active_sessions", 0),
                "max": sc.get("max_sessions", 0),
                "utilization": sc.get("active_sessions", 0) / max(sc.get("max_sessions", 1), 1)
            }
    
    # Cache health
    if "rag_cache" in full_metrics:
        cache = full_metrics["rag_cache"]
        if "error" not in cache and "disabled" not in cache:
            summary["cache"] = {
                "hit_rate": cache.get("hit_rate_percent", 0),
                "utilization": cache.get("size", 0) / max(cache.get("max_size", 1), 1),
                "hits": cache.get("hits", 0),
                "misses": cache.get("misses", 0)
            }
    
    # Memory health
    if "working_memory" in full_metrics:
        memory = full_metrics["working_memory"]
        if "error" not in memory and "disabled" not in memory:
            summary["memory"] = {
                "utilization": memory.get("utilization", 0),
                "tokens_used": memory.get("tokens_used", 0),
                "tokens_limit": memory.get("tokens_limit", 0)
            }
    
    return summary
