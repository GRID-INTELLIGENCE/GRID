# GRID Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development)
3. [Production Deployment](#production-deployment)
4. [Testing](#testing)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

## Prerequisites
- Python 3.13
- Node.js 18+
- Docker
- Terraform
- Kubernetes CLI
- AWS CLI (for cloud deployment)

## Local Development

### Backend Setup
```bash
cd grid
uv venv --python 3.13

uv sync --group dev --group test
alembic upgrade head
uvicorn application.mothership.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Production Deployment

### Terraform Setup
```bash
cd infrastructure/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Kubernetes Deployment
```bash
kubectl apply -f infrastructure/kubernetes
```

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific tests:
```bash
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

## Monitoring
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- Logs: `kubectl logs -f <pod-name>`

## Troubleshooting
### Common Issues
1. **Database Connection Issues**
   - Check environment variables
   - Verify database is running
   - Test connection with `psql`

2. **CORS Errors**
   - Ensure correct origins in `BACKEND_CORS_ORIGINS`
   - Check frontend URL matches configured origins

3. **Rate Limiting**
   - Verify Redis connection
   - Check trust tier settings
```
