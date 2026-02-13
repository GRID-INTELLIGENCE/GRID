import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.config import settings
from .routers import auth, inference, privacy

logger = logging.getLogger(__name__)


def validate_environment_variables() -> None:
    """Validate critical environment variables.

    Raises RuntimeError instead of calling sys.exit so tests can catch it.
    Skipped when TESTING=true.
    """
    if os.getenv("TESTING") == "true":
        return

    required_vars = {
        "MOTHERSHIP_SECRET_KEY": os.getenv("MOTHERSHIP_SECRET_KEY"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
    }

    missing_vars: list[str] = []
    invalid_vars: list[str] = []

    for var_name, var_value in required_vars.items():
        if var_value is None:
            missing_vars.append(var_name)
        elif var_name == "MOTHERSHIP_SECRET_KEY" and len(var_value) < 32:
            invalid_vars.append(f"{var_name} must be at least 32 characters long")

    if missing_vars or invalid_vars:
        error_msg = "Application startup failed due to environment configuration:\n"
        if missing_vars:
            error_msg += f"Missing required environment variables: {', '.join(missing_vars)}\n"
        if invalid_vars:
            error_msg += f"Invalid environment variables: {'; '.join(invalid_vars)}\n"
        raise RuntimeError(error_msg)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: validate env vars on startup."""
    validate_environment_variables()
    logger.info("GRID API started")
    yield
    logger.info("GRID API shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="GRID API - Geometric Resonance Intelligence Driver",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(inference.router, prefix="/api/v1/inference", tags=["Inference"])
app.include_router(privacy.router, prefix="/api/v1/privacy", tags=["Privacy"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "GRID API", "version": "1.0.0", "docs": "/docs"}


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "status_code": exc.status_code})
