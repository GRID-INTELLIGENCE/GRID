#!/bin/sh
set -e

# This script runs before the main application to validate configuration and dependencies

echo "=========================================="
echo "GRID Mothership API - Starting Container"
echo "=========================================="

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service_name at $host:$port..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✓ $service_name is ready!"
            return 0
        fi
        echo "  Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "✗ ERROR: $service_name did not become ready within timeout"
    exit 1
}

# Validate required environment variables
echo "Validating environment configuration..."

required_vars=("CHROMA_HOST" "OLLAMA_HOST")
missing_vars=()

db_url="${DATABASE_URL:-${MOTHERSHIP_DATABASE_URL:-}}"
redis_url="${REDIS_URL:-${MOTHERSHIP_REDIS_URL:-}}"

for var in "${required_vars[@]}"; do
    if [ -z "$(eval echo \$$var)" ]; then
        missing_vars+=("$var")
    fi
done

if [ -z "$db_url" ]; then
    missing_vars+=("DATABASE_URL|MOTHERSHIP_DATABASE_URL")
fi

if [ -z "$redis_url" ]; then
    missing_vars+=("REDIS_URL|MOTHERSHIP_REDIS_URL")
fi

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "✗ ERROR: Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

echo "✓ All required environment variables are set"

# Wait for dependencies if not in skip mode
if [ "$SKIP_DEPENDENCY_CHECK" != "true" ]; then
    echo ""
    echo "Checking service dependencies..."

    # Wait for PostgreSQL
    if [ -n "$POSTGRES_HOST" ]; then
        wait_for_service "$POSTGRES_HOST" 5432 "PostgreSQL"
    fi

    # Wait for ChromaDB
    if [ -n "$CHROMA_HOST" ]; then
        wait_for_service "$CHROMA_HOST" 8000 "ChromaDB"
    fi

    # Wait for Ollama
    if [ -n "$OLLAMA_HOST" ]; then
        # Extract host and port from OLLAMA_HOST URL
        ollama_host=$(echo "$OLLAMA_HOST" | sed -n 's|http://\([^:]*\):.*|\1|p')
        ollama_port=$(echo "$OLLAMA_HOST" | sed -n 's|http://[^:]*:\([0-9]*\).*|\1|p')
        if [ -n "$ollama_host" ] && [ -n "$ollama_port" ]; then
            wait_for_service "$ollama_host" "$ollama_port" "Ollama"
        fi
    fi

    # Wait for Redis
    if [ -n "$REDIS_URL" ]; then
        redis_host=$(echo "$REDIS_URL" | sed -n 's|redis://\([^:]*\):.*|\1|p')
        redis_port=$(echo "$REDIS_URL" | sed -n 's|redis://[^:]*:\([0-9]*\).*|\1|p')
        if [ -n "$redis_host" ] && [ -n "$redis_port" ]; then
            wait_for_service "$redis_host" "$redis_port" "Redis"
        fi
    fi
else
    echo "Skipping dependency checks (SKIP_DEPENDENCY_CHECK=true)"
fi

# Run database migrations if enabled
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo ""
    echo "Running database migrations..."
    python -m alembic upgrade head || {
        echo "✗ ERROR: Database migration failed"
        exit 1
    }
    echo "✓ Database migrations completed"
fi

# Create necessary directories
echo ""
echo "Ensuring data directories exist..."
mkdir -p /data/chroma /data/sessions /data/conversations /data/logs
echo "✓ Data directories ready"

# Display configuration summary
echo ""
echo "=========================================="
echo "Configuration Summary"
echo "=========================================="
echo "GRID_HOME: ${GRID_HOME:-/app}"
echo "GRID_LOG_LEVEL: ${GRID_LOG_LEVEL:-INFO}"
echo "DEBUG: ${DEBUG:-false}"
echo "MOTHERSHIP_PORT: ${MOTHERSHIP_PORT:-8080}"
echo "=========================================="
echo ""

# Start the application
echo "Starting Mothership API..."
exec "$@"
