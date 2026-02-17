"""
API Versioning Middleware for Mothership Cockpit.

Injects version-specific headers into responses and handles deprecation signaling.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from ..api.versioning import get_version_metadata

logger = logging.getLogger(__name__)


class VersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle API versioning headers and deprecation signaling.
    """

    def __init__(
        self,
        app: ASGIApp,
        default_version: str = "v1",
    ):
        super().__init__(app)
        self.default_version = default_version

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Determine version from path (e.g., /api/v1/...)
        path = request.url.path
        version_str = self.default_version

        if "/api/v2" in path:
            version_str = "v2"
        elif "/api/v1" in path:
            version_str = "v1"
        elif "/api/experimental" in path:
            version_str = "experimental"

        # Process request
        response = await call_next(request)

        # Inject versioning headers
        version_meta = get_version_metadata(version_str)
        if version_meta:
            version_meta.inject_headers(response)
        
        return response
