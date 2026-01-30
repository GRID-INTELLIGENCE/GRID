# Docker Integration for GRID

This guide helps you set up and run GRID using Docker for both local development and production deployment.

## Quick Start

### Prerequisites
- Docker Engine 20.10+ or Docker Desktop 4.0+
- Docker Compose 2.0+ (included with Docker Desktop)
- 4GB+ RAM, 2GB+ disk space for images and volumes

### Local Development

> **Note**: The base `docker-compose.yml` provides **infrastructure services only** (PostgreSQL, ChromaDB, Ollama, Redis). The Mothership API service is defined in `docker-compose.prod.yml` and requires explicit profile activation or can be run directly on the host.

**Option A: Run API on host (recommended for development)**

1. **Start infrastructure services**:
   ```bash
   docker-compose up -d
   ```

   This starts:
   - **PostgreSQL**: localhost:5432
   - **ChromaDB**: http://localhost:8000
   - **Ollama**: http://localhost:11435 (mapped from 11434)
   - **Redis**: localhost:6379

2. **Run API locally**:
   ```powershell
   # PowerShell
   .\.venv\Scripts\python.exe -m application.mothership.main
   ```

   API will be available at: http://localhost:8080

**Option B: Run API in Docker (production-like)**

1. **Start all services including API**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile api up -d
   ```

   This adds:
   - **Mothership API**: http://localhost:8080

2. **Check service status**:
   ```bash
   docker-compose ps
   ```

   All services should show `healthy` in the STATUS column.

3. **View API logs**:
   ```bash
   docker-compose - docker-compose.prod.yml logs -f mothership-api
   ```

4. **Access the API**:
   ```bash
   curl http://localhost:8080/health
   ```

5. **Stop services**:
   ```bash
   docker-compose down
   ```

   To also remove data volumes:
   ```bash
   docker-compose down -v
   ```

---

## Service Configuration

### Environment Variables

Each service uses environment variables for configuration. Modify `docker-compose.yml` to override defaults:

#### Mothership API
- `MOTHERSHIP_HOST`: API bind address (default: `0.0.0.0`)
- `MOTHERSHIP_PORT`: API port (default: `8080`)
- `DATABASE_URL`: PostgreSQL connection string
- `CHROMA_HOST`: ChromaDB host (default: `chroma`)
- `CHROMA_PORT`: ChromaDB port (default: `8000`)
- `OLLAMA_HOST`: Ollama service URL (default: `http://ollama:11434`)
- `RAG_ALLOW_REMOTE_LLM`: Use only local Ollama (default: `false`)
- `REDIS_URL`: Redis connection string (default: `redis://redis:6379/0`)
- `GRID_LOG_LEVEL`: Logging level (default: `INFO`)
- `CORS_ORIGINS`: Comma-separated allowed origins

#### Database (PostgreSQL)
- `POSTGRES_USER`: Username (default: `grid`)
- `POSTGRES_PASSWORD`: Password (default: `grid_dev_password` — **change in production**)
- `POSTGRES_DB`: Database name (default: `grid_db`)

#### ChromaDB
- `CHROMA_API_IMPL`: API implementation (default: `rest`)
- `CHROMA_SERVER_HOST`: Bind address (default: `0.0.0.0`)
- `CHROMA_SERVER_PORT`: Port (default: `8000`)

#### Ollama
- `OLLAMA_HOST`: Bind address (default: `0.0.0.0:11434`)

### Service Dependencies

The Mothership API depends on PostgreSQL, ChromaDB, and Ollama being healthy before starting. Use `docker-compose logs` to debug startup issues.

---

## Local Development Workflow

### Running Tests

Test the API inside the container:

```bash
# Run tests
docker-compose exec mothership-api pytest tests/ -v --tb=short

# Run with coverage
docker-compose exec mothership-api pytest tests/ --cov=grid --cov-report=html
```

### Database Migrations

Apply Alembic migrations (if using):

```bash
docker-compose exec mothership-api alembic upgrade head
```

### RAG Operations

Query the local RAG system:

```bash
docker-compose exec mothership-api python -m tools.rag.cli query "How does pattern recognition work?"
```

Index documentation:

```bash
docker-compose exec mothership-api python -m tools.rag.cli index docs/ --rebuild --curate
```

### Shell Access

Debug a service by opening a shell:

```bash
# Access API container
docker-compose exec mothership-api /bin/bash

# Access PostgreSQL
docker-compose exec postgres psql -U grid -d grid_db
```

---

## Building Custom Images

### Build for Local Testing

```bash
docker build -t grid-mothership:latest .
```

### Build with BuildKit Cache

```bash
DOCKER_BUILDKIT=1 docker build -t grid-mothership:latest .
```

### Build Specific Stages

```bash
# Build only the builder stage for inspection
docker build --target builder -t grid-builder:latest .
```

---

## Production Deployment

### Using Docker Compose (Small Deployments)

1. **Create a `.env.production` file**:
   ```env
   POSTGRES_PASSWORD=<strong-random-password>
   CORS_ORIGINS=https://yourdomain.com
   DEBUG=false
   ```

2. **Run with production config**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Using Kubernetes (Enterprise)

1. **Push image to registry**:
   ```bash
   docker tag grid-mothership:latest ghcr.io/your-org/grid:latest
   docker push ghcr.io/your-org/grid:latest
   ```

2. **Use Kubernetes manifests** (create in `k8s/`):
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: grid-mothership
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: grid-mothership
     template:
       metadata:
         labels:
           app: grid-mothership
       spec:
         containers:
         - name: mothership-api
           image: ghcr.io/your-org/grid:latest
           ports:
           - containerPort: 8080
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: grid-secrets
                 key: database-url
   ```

---

## Troubleshooting

### Services Not Starting

```bash
# View detailed logs
docker-compose logs mothership-api
docker-compose logs postgres
docker-compose logs chroma
docker-compose logs ollama

# Check container health
docker-compose ps
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running and accepting connections
docker-compose exec postgres psql -U grid -d grid_db -c "SELECT 1"

# Check DATABASE_URL is correct in mothership-api service
docker-compose exec mothership-api env | grep DATABASE_URL
```

### ChromaDB Not Responding

```bash
# Check ChromaDB is healthy
curl http://localhost:8000/api/v1/heartbeat

# View ChromaDB logs
docker-compose logs chroma
```

### Ollama Models Not Available

```bash
# Access Ollama and pull required models
docker-compose exec ollama ollama pull nomic-embed-text-v2-moe:latest
docker-compose exec ollama ollama pull ministral:latest

# List available models
docker-compose exec ollama ollama list
```

### Port Conflicts

If ports are already in use, modify `docker-compose.yml`:

```yaml
services:
  mothership-api:
    ports:
      - "8081:8080"  # Change host port from 8080 to 8081
```

Then access API at `http://localhost:8081`.

### Out of Disk Space

```bash
# Clean up unused Docker resources
docker system prune -a

# Remove specific volumes (data will be lost)
docker-compose down -v
```

---

## Performance Tuning

### Resource Limits

Set resource constraints in `docker-compose.yml`:

```yaml
mothership-api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

### GPU Support (NVIDIA)

Enable GPU for Ollama:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Requires NVIDIA Container Toolkit installed.

### Persistent Storage

By default, volumes are created in Docker's data directory. For better control:

```bash
# Use named volumes (recommended)
docker volume ls
docker volume inspect grid-postgres_data

# Or bind mount to host directory
docker-compose -f docker-compose.volumes.yml up
```

---

## Integration with GitHub Actions

The project includes a Docker build workflow (`.github/workflows/docker-build.yml`) that:
- Builds images on push to `main` and PR branches
- Scans for vulnerabilities with Trivy
- Pushes to GitHub Container Registry (for main/tags)
- Caches layers for faster builds

Push images to your registry:

```bash
docker tag grid-mothership:latest ghcr.io/your-org/grid:latest
docker push ghcr.io/your-org/grid:latest
```

---

## Next Steps

- **Add docker-compose.prod.yml** for production overrides (scaled services, external DB, etc.)
- **Configure CI/CD** to automatically deploy on merge to main
- **Monitor containers** with tools like Prometheus + Grafana
- **Set up container logging** with ELK stack or cloud providers
- **Use secrets management** (Vault, AWS Secrets Manager) for sensitive data

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [ChromaDB Docker Deployment](https://docs.trychroma.com/deployment)
- [Ollama Docker Setup](https://ollama.ai/blog/ollama-is-running-in-docker)
