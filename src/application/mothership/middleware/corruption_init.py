"""Initialization utility for the data corruption penalty system.

This module provides a simple way to set up the complete data corruption penalty
system with the Mothership API.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from .middleware.data_corruption import (
    DataCorruptionDetectionMiddleware,
    DataCorruptionPenaltyTracker,
)
from .routers import corruption_monitoring

logger = logging.getLogger(__name__)


class DataCorruptionPenaltyInitializer:
    """Helper class to initialize the data corruption penalty system."""

    def __init__(
        self,
        app: FastAPI,
        tracker: DataCorruptionPenaltyTracker | None = None,
        critical_endpoints: set[str] | None = None,
    ):
        self.app = app
        self.tracker = tracker or DataCorruptionPenaltyTracker()
        self.critical_endpoints = critical_endpoints or set()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the data corruption penalty system.

        This method:
        1. Adds the corruption detection middleware to the app
        2. Registers the corruption monitoring API endpoints
        3. Sets up critical endpoint monitoring
        """
        if self._initialized:
            logger.warning("Data corruption penalty system already initialized")
            return

        try:
            # Add the middleware
            self.app.add_middleware(
                DataCorruptionDetectionMiddleware,
                tracker=self.tracker,
                critical_endpoints=self.critical_endpoints,
            )
            logger.info("Data corruption detection middleware added")

            # Register the API router
            self.app.include_router(corruption_monitoring.router)
            logger.info("Corruption monitoring API endpoints registered")

            # Log critical endpoints being monitored
            if self.critical_endpoints:
                logger.info(
                    "Monitoring %d critical endpoints: %s",
                    len(self.critical_endpoints),
                    ", ".join(self.critical_endpoints),
                )

            self._initialized = True
            logger.info("Data corruption penalty system initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize data corruption penalty system: %s", e)
            raise

    def add_critical_endpoint(self, endpoint: str) -> None:
        """Add an endpoint to the critical monitoring list."""
        self.critical_endpoints.add(endpoint)
        if self._initialized:
            logger.info("Added critical endpoint: %s", endpoint)


def init_data_corruption_system(
    app: FastAPI,
    critical_endpoints: set[str] | None = None,
    tracker: DataCorruptionPenaltyTracker | None = None,
) -> DataCorruptionPenaltyInitializer:
    """Initialize the data corruption penalty system for a FastAPI app.

    This is the main entry point for setting up the data corruption penalty system.
    It should be called after creating your FastAPI app but before starting the server.

    Example:
        from fastapi import FastAPI
        from mothership.middleware.data_corruption import init_data_corruption_system

        app = FastAPI()

        # Initialize with critical endpoints that handle sensitive data
        corruption_init = init_data_corruption_system(
            app,
            critical_endpoints={
                "/api/v1/data/upload",
                "/api/v1/data/delete",
                "/api/v1/config/update",
            }
        )

        # The system is now active and will monitor all requests

    Args:
        app: The FastAPI application instance
        critical_endpoints: Optional set of endpoint patterns to always monitor closely
        tracker: Optional custom DataCorruptionPenaltyTracker instance

    Returns:
        The initializer instance for further configuration
    """
    initializer = DataCorruptionPenaltyInitializer(
        app=app,
        tracker=tracker,
        critical_endpoints=critical_endpoints,
    )
    initializer.initialize()
    return initializer
