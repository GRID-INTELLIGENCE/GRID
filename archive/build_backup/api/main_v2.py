"""GRID Sovereign API Gateway with Rights-Preserving Boundary Enforcement.

Unified FastAPI application with:
- Human rights guardrails and boundary enforcement
- Real-time WebSocket communication
- Comprehensive audit logging
- Prohibited domain blocking
- Live monitoring and alerting
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import boundary enforcement components
from api.middleware.rights_boundary import RightsPreservingBoundaryMiddleware
from api.monitoring.boundary_logger import RightsPreservingLogger, boundary_logger
from api.schema.rights_boundary import (
    BoundarySchema,
    HumanRightCategory,
    MonitoringMetrics,
    RiskLevel,
)
from api.websocket.rights_gateway import websocket_endpoint, websocket_manager


def get_project_root() -> Path:
    """Get project root from env or default."""
    import os
    if root := os.getenv("PROJECT_ROOT"):
        return Path(root)
    return Path(__file__).parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🛡️  GRID Sovereign API Gateway starting...")
    print("🔒 Rights-Preserving Boundary Enforcement: ENABLED")
    print("🚫 Prohibited Domains: 10 categories blocked")
    print("📡 WebSocket Gateway: READY")
    print("📊 Audit Logging: ACTIVE")
    print("⚖️  Human Rights Protection: ENFORCED")
    
    # Initialize monitoring loop
    monitor_task = asyncio.create_task(_monitoring_loop())
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down GRID Sovereign API Gateway...")
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    print("✅ Shutdown complete")


async def _monitoring_loop() -> None:
    """Background monitoring loop."""
    while True:
        try:
            await asyncio.sleep(60)  # Update every minute
            metrics = boundary_logger.get_metrics()
            
            # Alert on concerning patterns
            if metrics.rights_violations_detected > 0:
                print(f"⚠️  ALERT: {metrics.rights_violations_detected} rights violations detected")
                
            if metrics.high_risk_requests > 10:
                print(f"⚠️  ALERT: High volume of high-risk requests ({metrics.high_risk_requests})")
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Monitoring error: {e}")


# Create FastAPI app
app = FastAPI(
    title="GRID Sovereign API",
    description="""
    Unified API gateway for GRID intelligence capabilities with **Human Rights Protection**.
    
    ## Rights-Preserving Features
    
    - **Human Rights Guardrails**: All requests analyzed for potential rights violations
    - **Prohibited Domain Blocking**: Automatic blocking of harmful research areas
    - **Real-time Monitoring**: Live tracking of boundary enforcement
    - **Audit Trail**: Immutable logging for accountability
    - **WebSocket Gateway**: Real-time communication with rights validation
    
    ## Protected Rights
    
    Based on the Universal Declaration of Human Rights (UDHR):
    - Right to Life, Liberty and Security (Article 3)
    - Freedom from Torture (Article 5)
    - Right to Privacy (Article 12)
    - Freedom of Expression (Article 19)
    - Freedom from Discrimination (Article 2)
    - And 6 additional protected rights
    
    ## Prohibited Research Domains
    
    The following research/applications are **automatically blocked**:
    - Mass surveillance technology
    - Discriminatory profiling systems
    - Autonomous weapons
    - Forced behavior modification
    - Exploitative data collection
    - Coercive psychological manipulation
    - Non-consensual biometric tracking
    - Social credit scoring systems
    - Predictive policing without oversight
    - Algorithmic discrimination enforcement
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rights-preserving boundary middleware
app.add_middleware(RightsPreservingBoundaryMiddleware)


@app.get("/", tags=["root"])
async def root() -> dict[str, Any]:
    """API root with rights notice."""
    return {
        "service": "GRID Sovereign API",
        "version": "1.0.0",
        "rights_protection": {
            "status": "active",
            "protected_rights_count": len(HumanRightCategory),
            "prohibited_domains_count": 10,
            "enforcement_mode": "strict",
        },
        "message": (
            "This API enforces human rights protections. "
            "All requests are analyzed for potential violations. "
            "Prohibited research domains are automatically blocked."
        ),
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "websocket": "/ws/{client_id}",
            "schema": "/schema",
            "prohibited_domains": "/prohibited-domains",
        },
        "documentation": {
            "api_docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, Any]:
    """API health check with rights system status."""
    metrics = boundary_logger.get_metrics()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": "1.0.0",
        "service": "grid-sovereign-api",
        "rights_protection": {
            "status": "active",
            "audit_integrity": True,
            "total_requests_processed": metrics.total_requests,
            "violations_blocked": metrics.rights_violations_detected,
        },
    }


@app.get("/metrics", tags=["monitoring"])
async def get_metrics() -> MonitoringMetrics:
    """Get current monitoring metrics."""
    return boundary_logger.get_metrics()


@app.get("/schema", tags=["schema"])
async def get_schema() -> BoundarySchema:
    """Get boundary enforcement schema configuration."""
    return BoundarySchema()


@app.get("/prohibited-domains", tags=["boundaries"])
async def get_prohibited_domains() -> dict[str, Any]:
    """List prohibited research domains."""
    schema = BoundarySchema()
    return {
        "domains": schema.prohibited_domains,
        "count": len(schema.prohibited_domains),
        "description": "These research domains are prohibited to protect human rights",
        "basis": "Universal Declaration of Human Rights (UDHR)",
        "enforcement": "Automatic denial with audit logging",
    }


@app.get("/protected-rights", tags=["boundaries"])
async def get_protected_rights() -> dict[str, Any]:
    """List human rights protected by the system."""
    rights_info = {
        HumanRightCategory.RIGHT_TO_LIFE: {
            "udhr_article": "Article 3",
            "description": "Everyone has the right to life, liberty and security of person",
        },
        HumanRightCategory.FREEDOM_FROM_TORTURE: {
            "udhr_article": "Article 5",
            "description": "No one shall be subjected to torture or cruel treatment",
        },
        HumanRightCategory.RIGHT_TO_PRIVACY: {
            "udhr_article": "Article 12",
            "description": "No arbitrary interference with privacy, family, home or correspondence",
        },
        HumanRightCategory.FREEDOM_OF_EXPRESSION: {
            "udhr_article": "Article 19",
            "description": "Everyone has the right to freedom of opinion and expression",
        },
        HumanRightCategory.FREEDOM_FROM_DISCRIMINATION: {
            "udhr_article": "Article 2",
            "description": "Everyone is entitled to rights without discrimination",
        },
        HumanRightCategory.RIGHT_TO_WORK: {
            "udhr_article": "Article 23",
            "description": "Everyone has the right to work and free choice of employment",
        },
        HumanRightCategory.RIGHT_TO_HEALTH: {
            "udhr_article": "Article 25",
            "description": "Everyone has the right to a standard of living adequate for health",
        },
        HumanRightCategory.RIGHT_TO_EDUCATION: {
            "udhr_article": "Article 26",
            "description": "Everyone has the right to education",
        },
        HumanRightCategory.FREEDOM_OF_THOUGHT: {
            "udhr_article": "Article 18",
            "description": "Everyone has the right to freedom of thought, conscience and religion",
        },
        HumanRightCategory.RIGHT_TO_ASYLUM: {
            "udhr_article": "Article 14",
            "description": "Everyone has the right to seek and enjoy asylum from persecution",
        },
        HumanRightCategory.RIGHT_TO_NATIONALITY: {
            "udhr_article": "Article 15",
            "description": "Everyone has the right to a nationality",
        },
        HumanRightCategory.RIGHT_TO_MARRIAGE: {
            "udhr_article": "Article 16",
            "description": "Men and women of full age have the right to marry",
        },
        HumanRightCategory.RIGHT_TO_PROPERTY: {
            "udhr_article": "Article 17",
            "description": "Everyone has the right to own property",
        },
        HumanRightCategory.RIGHT_TO_POLITICAL_PARTICIPATION: {
            "udhr_article": "Article 21",
            "description": "Everyone has the right to take part in government",
        },
    }
    
    return {
        "rights": [
            {
                "category": right.value,
                "udhr_article": info["udhr_article"],
                "description": info["description"],
            }
            for right, info in rights_info.items()
        ],
        "total_count": len(rights_info),
        "source": "Universal Declaration of Human Rights",
        "adopted": "1948",
    }


@app.post("/validate", tags=["validation"])
async def validate_request(request_data: dict[str, Any]) -> dict[str, Any]:
    """Validate a request without executing it."""
    from api.schema.rights_boundary import RightsPreservingRequest, HumanRightsImpact
    from api.middleware.rights_boundary import RightsPreservingBoundaryMiddleware
    
    # Create mock request for validation
    test_request = RightsPreservingRequest(
        request_type=request_data.get("request_type", "research_query"),
        content=request_data.get("content", ""),
        declared_purpose=request_data.get("purpose"),
        correlation_id=str(uuid4())[:12],
    )
    
    # Run rights assessment
    middleware = RightsPreservingBoundaryMiddleware(app)
    impact = await middleware._assess_human_rights_impact(test_request)
    
    return {
        "validation_id": str(uuid4())[:8],
        "is_valid": impact.risk_level != RiskLevel.VIOLATION,
        "risk_level": impact.risk_level,
        "rights_impact": impact.dict(),
        "would_be_blocked": impact.risk_level == RiskLevel.VIOLATION,
        "requires_human_review": impact.requires_human_review,
    }


# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_rights_gateway(websocket: WebSocket, client_id: str) -> None:
    """
    WebSocket endpoint for real-time rights-preserving communication.
    
    All messages are validated against human rights guardrails.
    Violations are blocked in real-time with immediate notification.
    """
    await websocket_endpoint.handle_websocket(websocket, client_id)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """Global exception handler with rights metadata."""
    correlation_id = getattr(request.state, "rights_metadata", {}).get(
        "correlation_id", str(uuid4())[:12]
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "correlation_id": correlation_id,
            "message": str(exc) if app.debug else "An error occurred",
            "rights_validated": True,
        },
        headers={"X-Correlation-ID": correlation_id},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
