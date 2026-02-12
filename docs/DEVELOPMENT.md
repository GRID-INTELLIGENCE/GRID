# Development Guide

## Overview

This guide provides comprehensive information for developers working on the GRID AI security and privacy platform.

## Development Environment Setup

### Prerequisites
- Python 3.13+
- Redis server (recommended for full testing)
- Node.js 18+ (for frontend development)
- Git

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd grid

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev,test]"
```

### Environment Configuration

Create `.env.development`:
```env
# Development settings
DEBUG=true
GRID_ENV=development

# Database (development)
POSTGRES_SERVER=localhost
POSTGRES_USER=grid_dev
POSTGRES_PASSWORD=grid_dev
POSTGRES_DB=grid_dev

# Redis (development)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# Security (development - NOT FOR PRODUCTION)
SECRET_KEY=dev-secret-key-change-in-production
RATE_LIMIT_SECRET=dev-rate-limit-secret

# External Services
OLLAMA_BASE_URL=http://localhost:11434
```

## Project Structure

### Backend Structure
```
src/grid/
├── api/
│   ├── main.py              # FastAPI application
│   └── routers/
│       ├── auth.py          # Authentication endpoints
│       ├── inference.py     # Inference endpoints
│       └── privacy.py        # Privacy endpoints
├── core/
│   ├── config.py            # Application configuration
│   └── security.py          # Authentication utilities
├── models/
│   ├── user.py              # User models
│   └── inference.py         # Inference models
├── services/
│   └── inference.py         # Business logic
└── security/
    ├── __init__.py          # Security module init
    └── environment.py       # Environment settings
```

### Test Structure
```
tests/
├── unit/                   # Unit tests
│   ├── test_inference.py
│   └── test_models.py
├── integration/            # Integration tests
│   └── test_api.py
├── security/               # Security tests
│   └── test_security_suite.py
├── e2e/                    # End-to-end tests
│   └── test_workflow.py
└── conftest.py             # Test configuration
```

## Development Workflow

### 1. Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run tests to ensure nothing breaks
python -m pytest tests/unit/ tests/integration/ tests/security/ -v

# Add new tests for new functionality
# ... write tests ...

# Run full test suite
python -m pytest tests/ -v
```

### 2. Code Quality

#### Type Hints
All functions should have proper type hints:
```python
from typing import Optional, Dict, Any
from pydantic import BaseModel

def process_inference(
    request: InferenceRequest,
    user_id: str,
    settings: Optional[Dict[str, Any]] = None
) -> InferenceResponse:
    """Process inference request with security validation."""
    pass
```

#### Error Handling
Use proper exception handling:
```python
try:
    result = await process_request(request)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### Logging
Use structured logging:
```python
import logging

logger = logging.getLogger(__name__)

def process_request(request: Request):
    logger.info(
        "Processing request",
        extra={
            "user_id": request.user_id,
            "request_type": request.type,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 3. Testing

#### Writing Tests

**Unit Tests**:
```python
import pytest
from grid.services.inference import InferenceService

class TestInferenceService:
    def setup_method(self):
        self.service = InferenceService()

    def test_validation(self):
        """Test request validation."""
        valid_request = InferenceRequest(prompt="Valid prompt")
        assert self.service._validate_request(valid_request) is True

        invalid_request = InferenceRequest(prompt="")
        assert self.service._validate_request(invalid_request) is False
```

**Integration Tests**:
```python
from fastapi.testclient import TestClient
from grid.api.main import app

def test_inference_endpoint():
    """Test inference API endpoint."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/inference",
        json={"prompt": "Test prompt"}
    )
    assert response.status_code == 200
    assert "result" in response.json()
```

#### Test Configuration

The test suite uses `conftest.py` for configuration:
- Path resolution for dual codebase
- Environment setup
- Common fixtures

#### Running Tests

```bash
# Quick development test
python -m pytest tests/unit/ -v

# Full test suite
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=grid --cov-report=html

# Specific test file
python -m pytest tests/security/test_security_suite.py -v

# Skip slow tests
python -m pytest tests/ -v -m "not slow"
```

## Code Standards

### Python Standards
- Follow PEP 8
- Use Black for code formatting
- Use isort for import sorting
- Use mypy for type checking

### Configuration Files

**pyproject.toml** (relevant sections):
```toml
[tool.black]
line-length = 88
target-version = ['py313']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
```

### Git Hooks

Set up pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## Debugging

### Common Issues

#### Import Path Problems
If you encounter import errors:
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify conftest.py configuration
python -m pytest tests/unit/ -v --collect-only
```

#### Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Test Redis connection
python -c "import redis; r=redis.Redis(); r.ping()"
```

#### Database Issues
```bash
# Test database connection
python -c "from grid.core.config import settings; print(settings.DATABASE_URI)"
```

### Debugging Tools

#### Logging Configuration
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add debug output
logger.debug(f"Processing request: {request}")
```

#### Performance Profiling
```python
import cProfile
import pstats

def profile_function():
    pr = cProfile.Profile()
    pr.enable()
    # Your code here
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

## Security Development

### Security Best Practices
1. Never commit secrets
2. Use environment variables for sensitive data
3. Validate all inputs
4. Use parameterized queries
5. Implement proper error handling

### Security Testing
```bash
# Run security tests
python -m pytest tests/security/ -v

# Check for common security issues
pip install bandit
bandit -r src/

# Check dependencies for vulnerabilities
pip install safety
safety check
```

## Frontend Development

### Setup
```bash
cd frontend
npm install
npm run dev
```

### Testing
```bash
# Frontend unit tests
npm test

# E2E tests (requires backend running)
npm run test:e2e
```

## Deployment

### Development Deployment
```bash
# Build for development
uvicorn grid.api.main:app --reload --host 0.0.0.0 --port 8000

# With environment file
uvicorn grid.api.main:app --reload --env-file .env.development
```

### Production Considerations
- Use production environment variables
- Enable proper logging
- Set up monitoring
- Configure reverse proxy
- Use HTTPS

## Contributing

### Pull Request Process
1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

### Code Review Checklist
- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance impact considered

## Troubleshooting

### Development Issues

#### Module Import Errors
```bash
# Verify package installation
pip list | grep grid

# Reinstall if needed
pip install -e .
```

#### Test Failures
```bash
# Run with verbose output
python -m pytest tests/ -v -s

# Run specific failing test
python -m pytest tests/unit/test_inference.py::test_name -v -s
```

#### Performance Issues
```bash
# Profile test execution
python -m pytest tests/ --profile

# Check for memory leaks
python -m pytest tests/ --memprof
```

## Resources

### Documentation
- [API Reference](docs/API_REFERENCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Test Status](docs/TEST_STATUS.md)

### Tools
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [pytest Documentation](https://docs.pytest.org/)

### Community
- GitHub Issues
- Discussion Forums
- Stack Overflow

---

**Happy Coding!** 🚀
