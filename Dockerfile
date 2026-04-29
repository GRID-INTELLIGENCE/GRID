FROM python:3.13-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM base AS dev
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --group dev --group test
EXPOSE 8080
CMD ["uv", "run", "uvicorn", "application.mothership.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

FROM base AS prod
RUN useradd -r -s /bin/false grid_user
USER grid_user
EXPOSE 8080
CMD ["uv", "run", "uvicorn", "application.mothership.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
