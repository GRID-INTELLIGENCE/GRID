FROM python:3.13-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY safety/ safety/
RUN uv sync --frozen --no-dev
COPY src/ src/
COPY security/ security/
COPY boundaries/ boundaries/
COPY knowledge_base/ knowledge_base/

FROM base AS dev
RUN uv sync --frozen --group dev --group test
COPY tests/ tests/
COPY scripts/ scripts/
EXPOSE 8080 8000
CMD ["uv", "run", "uvicorn", "application.mothership.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

FROM base AS prod
RUN useradd -r -s /bin/false grid
USER grid
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8080/health || exit 1
CMD ["uv", "run", "uvicorn", "application.mothership.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
