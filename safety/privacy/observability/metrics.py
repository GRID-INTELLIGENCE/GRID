from prometheus_client import Histogram, Counter, REGISTRY

def _get_or_create_metric(metric_class, name, documentation, **kwargs):
    try:
        # Check standard registry to avoid duplicates on re-import
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        return metric_class(name, documentation, **kwargs)
    except Exception:
        # Fallback if internal access changes
        try:
             return metric_class(name, documentation, **kwargs)
        except ValueError:
             # Last resort: try to find it in registry manually if above check failed
             for collector in REGISTRY._collector_to_names:
                 if name in REGISTRY._collector_to_names[collector]:
                     return collector
             raise

DETECTION_LATENCY = _get_or_create_metric(
    Histogram,
    "privacy_detection_latency_seconds",
    "PII detection latency",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25),
)

DETECTION_CACHE_HITS = _get_or_create_metric(
    Counter,
    "privacy_detection_cache_hits_total",
    "Cache hits for detection results",
)

DETECTION_CACHE_MISSES = _get_or_create_metric(
    Counter,
    "privacy_detection_cache_misses_total",
    "Cache misses for detection results",
)

SAFETY_ENGINE_CACHE_HITS = _get_or_create_metric(
    Counter,
    "safety_engine_cache_hits_total",
    "Cache hits for safety engine instances",
)

SAFETY_ENGINE_CACHE_MISSES = _get_or_create_metric(
    Counter,
    "safety_engine_cache_misses_total",
    "Cache misses for safety engine instances",
)

SAFETY_ENGINE_CACHE_SIZE = _get_or_create_metric(
    Histogram,
    "safety_engine_cache_size",
    "Number of active safety engines in cache",
    buckets=(10, 100, 1000, 5000, 10000),
)
