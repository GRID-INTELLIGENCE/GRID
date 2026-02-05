import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from .token_manager import TokenManager

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate Bearer tokens on incoming requests.
    Populates request.state.user with token payload.
    """

    def __init__(self, app: ASGIApp, token_manager: TokenManager, exclude_paths: list[str] | None = None):
        super().__init__(app)
        self.token_manager = token_manager
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/auth/login", "/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Allow OPTIONS for CORS (usually handled by CORSMiddleware before this, but good practice)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Exclustions
        path = request.url.path
        if any(path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})

        token = auth_header.split(" ")[1]
        try:
            payload = await self.token_manager.verify_token(token)
            # request.state is not typed by default, but commonly used
            request.state.user = payload
            request.state.token = token
        except ValueError as e:
            logger.warning(f"Auth failed: {e}")
            return JSONResponse(status_code=401, content={"detail": str(e)})

        return await call_next(request)
