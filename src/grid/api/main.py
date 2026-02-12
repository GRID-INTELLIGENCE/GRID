from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routers import auth, inference, privacy
from ..core.config import settings
from ..core.security import get_current_user

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="GRID API - Geometric Resonance Intelligence Driver",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)
app.include_router(
    inference.router,
    prefix="/api/v1/inference",
    tags=["Inference"]
)
app.include_router(
    privacy.router,
    prefix="/api/v1/privacy",
    tags=["Privacy"]
)

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
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )
