"""
GRID Main Entry Point.

This module serves as the primary entry point for the GRID system's API services.
It defaults to running the API Gateway, which routes requests to specialized
sub-services like the Mothership Cockpit.
"""

import os
import sys
from pathlib import Path

# Add paths using SecurePathManager for secure path management
current_dir = Path(__file__).parent.absolute()
root_dir = current_dir.parent.absolute()

try:
    from grid.security.path_manager import SecurePathManager

    manager = SecurePathManager(base_dir=root_dir)
    if str(current_dir) not in sys.path:
        manager.add_path(current_dir, validate=True)
    if str(root_dir) not in sys.path:
        manager.add_path(root_dir, validate=True)
except ImportError:
    # Fallback to direct sys.path manipulation if SecurePathManager unavailable
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

try:
    # Attempt to load the API Gateway as the primary entry point
    from infrastructure.api_gateway.gateway import RouteConfig, ServiceEndpoint, create_gateway_app

    app, gateway = create_gateway_app()

    # Register default services
    # The Mothership Cockpit runs on 8080 by default
    mothership_url = os.environ.get("MOTHERSHIP_URL", "http://localhost:8080")

    gateway.register_service(
        ServiceEndpoint(name="grid-service", url=mothership_url, weight=1, health_check_path="/health/live")
    )

    # Route all API requests to the Mothership for now
    gateway.register_route(
        RouteConfig(
            path="/api/v1",
            service_name="grid-service",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        )
    )

    # Route health checks
    gateway.register_route(
        RouteConfig(path="/health", service_name="grid-service", methods=["GET"], auth_required=False)
    )

except ImportError as e:
    # If gateway is not available, try to fall back to the Mothership app directly
    # This ensures resiliency if parts of the infrastructure are missing.
    try:
        from application.mothership.main import app
    except ImportError:
        # If both fail, we have a serious configuration issue
        raise ImportError(f"Could not initialize GRID entry point. Error loading gateway: {e}") from e

if __name__ == "__main__":
    import uvicorn

    # If run directly, start the app on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
