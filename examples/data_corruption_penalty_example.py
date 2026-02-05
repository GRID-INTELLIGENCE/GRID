"""Example usage of the Data Corruption Penalty System.

This example demonstrates how to use the data corruption penalty system
to track and penalize endpoints that cause data or environment corruption.
"""
import asyncio
import logging
from typing import Any

from fastapi import FastAPI, Request, Response
from grid.resilience.data_corruption_penalty import (
    CorruptionSeverity,
    CorruptionType,
    corruption_tracker,
    record_corruption_event,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Example 1: Basic Usage with Manual Event Recording
# =============================================================================

async def example_manual_corruption_reporting():
    """Example of manually recording a corruption event."""
    
    # Simulate detecting data corruption in an endpoint
    endpoint = "POST /api/v1/data/upload"
    
    # Record a medium severity corruption event
    penalty = record_corruption_event(
        endpoint=endpoint,
        severity=CorruptionSeverity.MEDIUM,
        corruption_type=CorruptionType.DATA_VALIDATION,
        description="Invalid data format detected in upload payload",
        affected_resources=["uploads/users/2024/01/file123.json"],
        metadata={
            "file_size": "2.5MB",
            "content_type": "application/json",
            "validation_errors": ["missing_required_field: user_id"],
        },
    )
    
    logger.info(f"Recorded corruption event. Penalty applied: {penalty}")
    
    # Check endpoint health
    health = corruption_tracker.get_endpoint_health(endpoint)
    logger.info(f"Endpoint health: {health}")
    
    # Record a more severe event
    record_corruption_event(
        endpoint=endpoint,
        severity=CorruptionSeverity.HIGH,
        corruption_type=CorruptionType.REFERENTIAL_INTEGRITY,
        description="Database foreign key constraint violated",
        affected_resources=["database: users", "database: orders"],
        metadata={
            "constraint": "fk_orders_user_id",
            "user_id": "user-456",
            "order_id": "order-789",
        },
    )
    
    # Check if endpoint is now critical
    is_critical = corruption_tracker.is_endpoint_critical(endpoint)
    logger.info(f"Endpoint critical status: {is_critical}")
    
    # Get current penalty score
    current_penalty = corruption_tracker.get_endpoint_penalty(endpoint)
    logger.info(f"Current penalty score: {current_penalty}")


# =============================================================================
# Example 2: Using the Middleware in FastAPI
# =============================================================================

def example_middleware_setup():
    """Example of setting up the middleware in a FastAPI app."""
    from application.mothership.middleware.data_corruption import (
        DataCorruptionDetectionMiddleware,
        DataCorruptionPenaltyTracker,
    )
    
    app = FastAPI()
    
    # Create a custom tracker with specific configuration
    tracker = DataCorruptionPenaltyTracker()
    
    # Add the middleware
    app.add_middleware(
        DataCorruptionDetectionMiddleware,
        tracker=tracker,
        critical_endpoints={
            "/api/v1/data/upload",
            "/api/v1/data/delete",
        },
    )
    
    @app.post("/api/v1/data/upload")
    async def upload_data(request: Request):
        """Example endpoint that handles data uploads."""
        # If this endpoint throws an exception, it will be automatically
        # recorded as a corruption event with appropriate severity
        # ... endpoint logic ...
        return {"status": "success"}
    
    return app


# =============================================================================
# Example 3: Custom Corruption Indicators
# =============================================================================

def example_custom_indicators():
    """Example of adding custom corruption indicators."""
    from application.mothership.middleware.data_corruption import (
        DataCorruptionDetectionMiddleware,
    )
    
    app = FastAPI()
    middleware = DataCorruptionDetectionMiddleware(app=app)
    
    # Add custom indicators for specific business logic
    middleware.add_corruption_indicator(
        name="data_schema_mismatch",
        severity=CorruptionSeverity.HIGH,
        corruption_type=CorruptionType.SCHEMA_VIOLATION,
        description="Data schema version mismatch detected",
    )
    
    middleware.add_corruption_indicator(
        name="permission_denied",
        severity=CorruptionSeverity.MEDIUM,
        corruption_type=CorruptionType.SECURITY,
        description="Unauthorized access attempt detected",
    )
    
    return middleware


# =============================================================================
# Example 4: Monitoring Critical Endpoints
# =============================================================================

async def example_critical_endpoint_monitoring():
    """Example of monitoring critical endpoints."""
    
    # Simulate multiple endpoints with issues
    endpoints = [
        ("POST /api/v1/users", CorruptionSeverity.LOW, CorruptionType.VALIDATION),
        ("POST /api/v1/orders", CorruptionSeverity.MEDIUM, CorruptionType.DATA_VALIDATION),
        ("DELETE /api/v1/data", CorruptionSeverity.HIGH, CorruptionType.ENVIRONMENT),
    ]
    
    for endpoint, severity, corruption_type in endpoints:
        record_corruption_event(
            endpoint=endpoint,
            severity=severity,
            corruption_type=corruption_type,
            description=f"Simulated corruption in {endpoint}",
        )
    
    # Get all critical endpoints
    critical = corruption_tracker.get_critical_endpoints()
    
    if critical:
        logger.warning("Critical endpoints detected:")
        for endpoint, penalty in critical:
            health = corruption_tracker.get_endpoint_health(endpoint)
            logger.warning(f"  - {endpoint}: score={penalty:.2f}, severity={health['severity']}")
            logger.warning(f"    Recommendation: {health['recommendation']}")
    else:
        logger.info("No critical endpoints at this time")


# =============================================================================
# Example 5: Using the API Endpoints
# =============================================================================

async def example_api_usage():
    """Example of using the corruption monitoring API endpoints."""
    import httpx
    
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient() as client:
        # Report a corruption event manually
        response = await client.post(
            f"{base_url}/corruption/report",
            json={
                "endpoint": "POST /api/v1/data/upload",
                "severity": "HIGH",
                "corruption_type": "data_validation",
                "description": "Invalid file format detected",
                "affected_resources": ["uploads/invalid/file.pdf"],
            },
        )
        logger.info(f"Report response: {response.json()}")
        
        # Get endpoint health
        response = await client.get(
            f"{base_url}/corruption/health/POST%20/api/v1/data/upload"
        )
        logger.info(f"Health response: {response.json()}")
        
        # Get critical endpoints
        response = await client.get(f"{base_url}/corruption/critical")
        logger.info(f"Critical endpoints: {response.json()}")
        
        # Get overall stats
        response = await client.get(f"{base_url}/corruption/stats")
        logger.info(f"Stats: {response.json()}")


# =============================================================================
# Example 6: Integration with Existing Monitoring
# =============================================================================

def example_integration_with_monitoring():
    """Example of integrating with existing monitoring infrastructure."""
    from prometheus_client import Counter, Gauge
    from grid.resilience.metrics import MetricsCollector
    
    # Create Prometheus metrics for corruption tracking
    corruption_counter = Counter(
        "data_corruption_events_total",
        "Total number of data corruption events",
        ["endpoint", "severity", "corruption_type"],
    )
    
    corruption_score_gauge = Gauge(
        "endpoint_corruption_penalty",
        "Current corruption penalty score for endpoints",
        ["endpoint"],
    )
    
    # Custom wrapper that integrates with Prometheus
    def track_and_record_prometheus(
        endpoint: str,
        severity: CorruptionSeverity,
        corruption_type: CorruptionType,
        description: str,
    ) -> float:
        """Record corruption and update Prometheus metrics."""
        penalty = record_corruption_event(
            endpoint=endpoint,
            severity=severity,
            corruption_type=corruption_type,
            description=description,
        )
        
        # Update Prometheus metrics
        corruption_counter.labels(
            endpoint=endpoint,
            severity=severity.name,
            corruption_type=corruption_type.value,
        ).inc()
        
        current_score = corruption_tracker.get_endpoint_penalty(endpoint)
        corruption_score_gauge.labels(endpoint=endpoint).set(current_score)
        
        return penalty
    
    return track_and_record_prometheus


# =============================================================================
# Main
# =============================================================================

async def main():
    """Run all examples."""
    logger.info("=" * 60)
    logger.info("Data Corruption Penalty System - Usage Examples")
    logger.info("=" * 60)
    
    # Run examples
    await example_manual_corruption_reporting()
    await example_critical_endpoint_monitoring()
    
    # API usage example requires a running server, so we skip it
    # await example_api_usage()
    
    logger.info("=" * 60)
    logger.info("Examples completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
