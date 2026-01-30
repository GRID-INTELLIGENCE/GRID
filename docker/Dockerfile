# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/app/.venv/bin:$PATH"

# Build arguments for versioning
ARG COMMIT_SHA
ARG BUILD_TIME
ENV COMMIT_SHA=${COMMIT_SHA} \
    BUILD_TIME=${BUILD_TIME}

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Builder stage: install dependencies in a venv using uv
FROM base AS builder

# Copy only requirements files first for better caching
COPY requirements.txt pyproject.toml uv.lock ./

# Create venv and install dependencies using uv with caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv .venv && \
    uv pip install -r requirements.txt

# Copy application code
COPY --link . ./

# Final stage: minimal image with venv and app code, non-root user
FROM base AS final

# Create non-root user and group
RUN addgroup --system grid && adduser --system --ingroup grid grid

WORKDIR /app

# Copy venv and app code from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/ /app/

# Create data directories for persistence
RUN mkdir -p /data/chroma /data/sessions /data/conversations /data/logs && \
    chown -R grid:grid /app /data

# Health check for API (using Python instead of curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=5)" || exit 1

# Switch to non-root user
USER grid

# Expose API port
EXPOSE 8080

# Default command: run Mothership API
CMD ["python", "-m", "application.mothership.main"]
