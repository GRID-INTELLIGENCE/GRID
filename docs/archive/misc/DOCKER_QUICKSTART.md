

## Quick Start

### Prerequisites
- 4GB+ RAM, 2GB+ disk space for images and volumes

### Local Development


**Option A: Run API on host (recommended for development)**

1. **Start infrastructure services**:
   ```bash
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


1. **Start all services including API**:
   ```bash
   ```

   This adds:
   - **Mothership API**: http://localhost:8080

2. **Check service status**:
   ```bash
   ```

   All services should show `healthy` in the STATUS column.

3. **View API logs**:
   ```bash
   ```

4. **Access the API**:
   ```bash
   curl http://localhost:8080/health
   ```

5. **Stop services**:
   ```bash
   ```

   To also remove data volumes:
   ```bash
   ```

---

## Service Configuration

### Environment Variables


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


---

## Local Development Workflow

### Running Tests

Test the API inside the container:

```bash
# Run tests

# Run with coverage
```

### Database Migrations

Apply Alembic migrations (if using):

```bash
```

### RAG Operations

Query the local RAG system:

```bash
```

Index documentation:

```bash
```

### Shell Access

Debug a service by opening a shell:

```bash
# Access API container

# Access PostgreSQL
```

---

## Building Custom Images

### Build for Local Testing

```bash
```

### Build with BuildKit Cache

```bash
```

### Build Specific Stages

```bash
# Build only the builder stage for inspection
```

---

## Production Deployment


1. **Create a `.env.production` file**:
   ```env
   POSTGRES_PASSWORD=<strong-random-password>
   CORS_ORIGINS=https://yourdomain.com
   DEBUG=false
   ```

2. **Run with production config**:
   ```bash
   ```

### Using Kubernetes (Enterprise)

1. **Push image to registry**:
   ```bash
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

# Check container health
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running and accepting connections

# Check DATABASE_URL is correct in mothership-api service
```

### ChromaDB Not Responding

```bash
# Check ChromaDB is healthy
curl http://localhost:8000/api/v1/heartbeat

# View ChromaDB logs
```

### Ollama Models Not Available

```bash
# Access Ollama and pull required models

# List available models
```

### Port Conflicts


```yaml
services:
  mothership-api:
    ports:
      - "8081:8080"  # Change host port from 8080 to 8081
```

Then access API at `http://localhost:8081`.

### Out of Disk Space

```bash

# Remove specific volumes (data will be lost)
```

---

## Performance Tuning

### Resource Limits


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


```bash
# Use named volumes (recommended)

# Or bind mount to host directory
```

---

## Integration with GitHub Actions

- Builds images on push to `main` and PR branches
- Scans for vulnerabilities with Trivy
- Pushes to GitHub Container Registry (for main/tags)
- Caches layers for faster builds

Push images to your registry:

```bash
```

---

## Next Steps

- **Configure CI/CD** to automatically deploy on merge to main
- **Monitor containers** with tools like Prometheus + Grafana
- **Set up container logging** with ELK stack or cloud providers
- **Use secrets management** (Vault, AWS Secrets Manager) for sensitive data

---

## References

