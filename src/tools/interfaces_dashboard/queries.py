"""SQL queries for interfaces metrics dashboard."""

from __future__ import annotations


def get_recent_bridge_metrics(hours: int = 24) -> str:
    """Get recent bridge metrics query.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        SQL query string
    """
    return f"""
    SELECT
        timestamp,
        trace_id,
        transfer_latency_ms,
        compressed_size,
        raw_size,
        compression_ratio,
        coherence_level,
        entanglement_count,
        success
    FROM interfaces_bridge_metrics
    WHERE timestamp >= datetime('now', '-{hours} hours')
    ORDER BY timestamp DESC
    LIMIT 1000
    """


def get_recent_sensory_metrics(hours: int = 24) -> str:
    """Get recent sensory metrics query.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        SQL query string
    """
    return f"""
    SELECT
        timestamp,
        trace_id,
        modality,
        duration_ms,
        coherence,
        raw_size,
        source,
        success,
        error_message
    FROM interfaces_sensory_metrics
    WHERE timestamp >= datetime('now', '-{hours} hours')
    ORDER BY timestamp DESC
    LIMIT 1000
    """


def get_latency_percentiles(hours: int = 24, interface_type: str = "bridge") -> str:
    """Get latency percentiles query.

    Args:
        hours: Number of hours to look back (default: 24)
        interface_type: Interface type ('bridge' or 'sensory')

    Returns:
        SQL query string
    """
    if interface_type == "bridge":
        latency_col = "transfer_latency_ms"
        table = "interfaces_bridge_metrics"
    else:
        latency_col = "duration_ms"
        table = "interfaces_sensory_metrics"

    return f"""
    SELECT
        {latency_col} AS latency_ms
    FROM {table}
    WHERE timestamp >= datetime('now', '-{hours} hours')
        AND {latency_col} IS NOT NULL
        AND {latency_col} > 0
    ORDER BY {latency_col}
    """


def get_throughput_metrics(hours: int = 24) -> str:
    """Get throughput metrics query.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        SQL query string
    """
    return f"""
    SELECT
        strftime('%Y-%m-%d %H:00:00', timestamp) AS hour_bucket,
        COUNT(*) AS operation_count,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) AS success_count,
        AVG(CASE WHEN interface_type = 'bridge' THEN transfer_latency_ms ELSE duration_ms END) AS avg_latency_ms
    FROM (
        SELECT timestamp, success, 'bridge' AS interface_type, transfer_latency_ms, NULL AS duration_ms
        FROM interfaces_bridge_metrics
        WHERE timestamp >= datetime('now', '-{hours} hours')
        UNION ALL
        SELECT timestamp, success, 'sensory' AS interface_type, NULL AS transfer_latency_ms, duration_ms
        FROM interfaces_sensory_metrics
        WHERE timestamp >= datetime('now', '-{hours} hours')
    )
    GROUP BY hour_bucket
    ORDER BY hour_bucket DESC
    """


def get_coherence_trends(hours: int = 24) -> str:
    """Get coherence trends query.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        SQL query string
    """
    return f"""
    SELECT
        strftime('%Y-%m-%d %H:00:00', timestamp) AS hour_bucket,
        AVG(coherence) AS avg_coherence
    FROM (
        SELECT timestamp, coherence_level AS coherence
        FROM interfaces_bridge_metrics
        WHERE timestamp >= datetime('now', '-{hours} hours')
            AND coherence_level IS NOT NULL
        UNION ALL
        SELECT timestamp, coherence
        FROM interfaces_sensory_metrics
        WHERE timestamp >= datetime('now', '-{hours} hours')
            AND coherence IS NOT NULL
    )
    GROUP BY hour_bucket
    ORDER BY hour_bucket DESC
    """


def get_modality_distribution(hours: int = 24) -> str:
    """Get modality distribution query.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        SQL query string
    """
    return f"""
    SELECT
        modality,
        COUNT(*) AS operation_count,
        AVG(duration_ms) AS avg_duration_ms,
        AVG(coherence) AS avg_coherence,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) AS success_count,
        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failure_count
    FROM interfaces_sensory_metrics
    WHERE timestamp >= datetime('now', '-{hours} hours')
    GROUP BY modality
    ORDER BY operation_count DESC
    """


def get_error_rates(hours: int = 24) -> str:
    """Get error rates query.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        SQL query string
    """
    return f"""
    SELECT
        strftime('%Y-%m-%d %H:00:00', timestamp) AS hour_bucket,
        'bridge' AS interface_type,
        COUNT(*) AS total_operations,
        SUM(CASE WHEN success THEN 0 ELSE 1 END) AS failure_count,
        CAST(SUM(CASE WHEN success THEN 0 ELSE 1 END) * 100.0 / COUNT(*) AS REAL) AS failure_rate_percentage
    FROM interfaces_bridge_metrics
    WHERE timestamp >= datetime('now', '-{hours} hours')
    GROUP BY hour_bucket
    UNION ALL
    SELECT
        strftime('%Y-%m-%d %H:00:00', timestamp) AS hour_bucket,
        'sensory' AS interface_type,
        COUNT(*) AS total_operations,
        SUM(CASE WHEN success THEN 0 ELSE 1 END) AS failure_count,
        CAST(SUM(CASE WHEN success THEN 0 ELSE 1 END) * 100.0 / COUNT(*) AS REAL) AS failure_rate_percentage
    FROM interfaces_sensory_metrics
    WHERE timestamp >= datetime('now', '-{hours} hours')
    GROUP BY hour_bucket
    ORDER BY hour_bucket DESC
    """


def get_compression_metrics(hours: int = 24) -> str:
    """Get compression metrics query.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        SQL query string
    """
    return f"""
    SELECT
        strftime('%Y-%m-%d %H:00:00', timestamp) AS hour_bucket,
        AVG(compression_ratio) AS avg_compression_ratio,
        AVG(CASE WHEN raw_size > 0 THEN compressed_size * 100.0 / raw_size ELSE 0 END) AS avg_compression_percentage,
        AVG(entanglement_count) AS avg_entanglement_count
    FROM interfaces_bridge_metrics
    WHERE timestamp >= datetime('now', '-{hours} hours')
        AND raw_size > 0
    GROUP BY hour_bucket
    ORDER BY hour_bucket DESC
    """


def get_summary_stats(hours: int = 24) -> str:
    """Get summary statistics query.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        SQL query string
    """
    return f"""
    SELECT
        'bridge' AS interface_type,
        COUNT(*) AS total_operations,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) AS successful_operations,
        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failed_operations,
        AVG(transfer_latency_ms) AS avg_latency_ms,
        AVG(coherence_level) AS avg_coherence
    FROM interfaces_bridge_metrics
    WHERE timestamp >= datetime('now', '-{hours} hours')
    UNION ALL
    SELECT
        'sensory' AS interface_type,
        COUNT(*) AS total_operations,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) AS successful_operations,
        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failed_operations,
        AVG(duration_ms) AS avg_latency_ms,
        AVG(coherence) AS avg_coherence
    FROM interfaces_sensory_metrics
    WHERE timestamp >= datetime('now', '-{hours} hours')
    """
