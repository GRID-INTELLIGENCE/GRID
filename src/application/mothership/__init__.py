"""
Mothership Cockpit - Local Integration Backend

A comprehensive FastAPI backend implementing the Mothership Cockpit
local integration logic using Pythonic best practices.

Features:
    - Session management with TTL and activity tracking
    - Operation/task lifecycle management with progress tracking
    - Component health monitoring and registration
    - Alert system with severity levels and acknowledgment
    - Real-time WebSocket support for live updates
    - Cloud integration with Gemini Studio
    - Repository pattern for data access
    - Dependency injection via FastAPI

Usage:
    # Run the server
    uvicorn application.mothership.main:app --reload --port 8080

    # Import components
    from application.mothership import create_app, CockpitService
    from application.mothership.config import get_settings
    from application.mothership.models import Session, Operation, Alert

Architecture:
    - config.py: Configuration management with environment variable support
    - exceptions.py: Hierarchical exception classes
    - models/: Domain models (Session, Operation, Component, Alert)
    - schemas/: Pydantic request/response schemas
    - repositories/: Data access layer with Unit of Work pattern
    - services/: Business logic layer
    - routers/: FastAPI API endpoints
    - dependencies.py: FastAPI dependency injection
    - main.py: Application factory and entry point
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Grid Team"

# Graceful imports with fallbacks (Grid Core pattern)
# Initialize all to None before conditional imports
create_app = app = None  # type: ignore
MothershipSettings = get_settings = None  # type: ignore
CockpitService = SessionService = OperationService = ComponentService = AlertService = None  # type: ignore
Session = Operation = Component = Alert = CockpitState = None  # type: ignore
UnitOfWork = StateStore = None  # type: ignore
MothershipError = AuthenticationError = AuthorizationError = ResourceNotFoundError = ValidationError = None  # type: ignore

# Try to import application factory
try:
    from .main import app, create_app
except ImportError:  # pragma: no cover
    pass

# Try to import configuration
try:
    from .config import MothershipSettings, get_settings
except ImportError:  # pragma: no cover
    pass

# Try to import services
try:
    from .services import (
        AlertService,
        CockpitService,
        ComponentService,
        OperationService,
        SessionService,
    )
except ImportError:  # pragma: no cover
    pass

# Try to import models
try:
    from . import models

    Session = getattr(models, "Session", None)
    Operation = getattr(models, "Operation", None)
    Component = getattr(models, "Component", None)
    Alert = getattr(models, "Alert", None)
    CockpitState = getattr(models, "CockpitState", None)
except ImportError:  # pragma: no cover
    pass

# Try to import repositories
try:
    from .repositories import StateStore, UnitOfWork
except ImportError:  # pragma: no cover
    pass

# Try to import exceptions
try:
    from . import exceptions

    MothershipError = getattr(exceptions, "MothershipError", None)
    AuthenticationError = getattr(exceptions, "AuthenticationError", None)
    AuthorizationError = getattr(exceptions, "AuthorizationError", None)
    ResourceNotFoundError = getattr(exceptions, "ResourceNotFoundError", None)
    ValidationError = getattr(exceptions, "ValidationError", None)
except ImportError:  # pragma: no cover
    pass

__all__ = [
    # Application
    *(["create_app"] if create_app is not None else []),
    *(["app"] if app is not None else []),
    # Configuration
    *(["MothershipSettings"] if MothershipSettings is not None else []),
    *(["get_settings"] if get_settings is not None else []),
    # Services
    *(["CockpitService"] if CockpitService is not None else []),
    *(["SessionService"] if SessionService is not None else []),
    *(["OperationService"] if OperationService is not None else []),
    *(["ComponentService"] if ComponentService is not None else []),
    *(["AlertService"] if AlertService is not None else []),
    # Models
    *(["Session"] if Session is not None else []),
    *(["Operation"] if Operation is not None else []),
    *(["Component"] if Component is not None else []),
    *(["Alert"] if Alert is not None else []),
    *(["CockpitState"] if CockpitState is not None else []),
    # Repositories
    *(["UnitOfWork"] if UnitOfWork is not None else []),
    *(["StateStore"] if StateStore is not None else []),
    # Exceptions
    *(["MothershipError"] if MothershipError is not None else []),
    *(["AuthenticationError"] if AuthenticationError is not None else []),
    *(["AuthorizationError"] if AuthorizationError is not None else []),
    *(["ResourceNotFoundError"] if ResourceNotFoundError is not None else []),
    *(["ValidationError"] if ValidationError is not None else []),
]


# Lazy imports to avoid circular dependencies (fallback if module-level imports fail)
def __getattr__(name: str):
    """Lazy import module components."""
    if name == "create_app":
        from .main import create_app

        return create_app
    elif name == "app":
        from .main import app

        return app
    elif name in ("MothershipSettings", "get_settings"):
        from .config import MothershipSettings, get_settings

        if name == "MothershipSettings":
            return MothershipSettings
        return get_settings
    elif name == "CockpitService":
        from .services import CockpitService

        return CockpitService
    elif name == "SessionService":
        from .services import SessionService

        return SessionService
    elif name == "OperationService":
        from .services import OperationService

        return OperationService
    elif name == "ComponentService":
        from .services import ComponentService

        return ComponentService
    elif name == "AlertService":
        from .services import AlertService

        return AlertService
    elif name in ("Session", "Operation", "Component", "Alert", "CockpitState"):
        from . import models

        return getattr(models, name)
    elif name in ("UnitOfWork", "StateStore"):
        from .repositories import StateStore, UnitOfWork

        if name == "UnitOfWork":
            return UnitOfWork
        return StateStore
    elif name in (
        "MothershipError",
        "AuthenticationError",
        "AuthorizationError",
        "ResourceNotFoundError",
        "ValidationError",
    ):
        from . import exceptions

        return getattr(exceptions, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
