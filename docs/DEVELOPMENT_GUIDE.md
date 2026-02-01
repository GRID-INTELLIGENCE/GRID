# GRID Development Guide

Comprehensive build, test, and deployment commands for GRID workspace projects.

## Quick Start

```bash
# Setup GRID Framework
cd e:\grid
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test

# Verify setup
python -m pytest tests/unit/ -v
ruff check .
```

## Project-Specific Commands

### GRID Framework (Core)

**Environment Setup**

```bash
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test
```

**Development**

```bash
# Run main API server
python -m application.mothership.main

# Run with specific configuration
PYTHONPATH=src python -m application.mothership.main

# Development server with reload
uvicorn application.mothership.main:app --reload --host 0.0.0.0 --port 8000
```

**Testing**

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Security tests
pytest tests/security/ -v

# Exclude slow tests
pytest -m "not slow"

# Critical path tests only
pytest -m "critical"

# Coverage report
pytest --cov=src --cov-report=html
```

**Code Quality**

```bash
# Linting
ruff check .
ruff check --fix .

# Formatting
black .

# Type checking
mypy src/

# Security scanning
bandit -r src/
safety check
```

**RAG System**

```bash
# Query RAG system
python -m tools.rag.cli query "your question"

# Index documents
python -m tools.rag.cli index docs/

# On-demand RAG
python -m tools.rag.cli ondemand "question" --include-codebase

# RAG statistics
python -m tools.rag.cli stats
```

### EUFLE ML/AI Subproject

**Setup**

```bash
cd e:\grid\EUFLE
uv sync --group dev --group training

# Alternative: pip install with extras
pip install -e .[dev,training]
```

**Development**

```bash
# Main entry point
python eufle.py

# Training with specific model
python eufle.py --model mistral-nemo --data-path ./data

# Evaluation
python -m evaluation.evaluate_model --checkpoint ./checkpoints/latest
```

**Testing**

```bash
pytest tests/ -v
pytest -m "not gpu"  # Skip GPU tests
pytest -m "unit"    # Unit tests only
```

### Legacy Pipeline (Archived)

**Setup**

```bash
cd e:\grid\archive\legacy\pipeline
pip install -r requirements.txt

# Alternative with pyproject.toml
pip install -e .
```

**Running**

```bash
# Process documents
python main.py --input ./documents --output ./results

# OCR processing
python -m pipeline.ocr_processor --image-path ./scans/doc.pdf

# Classification
python -m pipeline.classifier --data ./processed --model ./models/classifier.pkl
```


### Build and Run

```bash
# Build main GRID image

# Build with specific commit


# Run specific services
```


```bash
# Build with development dependencies

# Run with mounted source for development

# Debug container
```

## Service Dependencies

### Local Services

```bash
# Start ChromaDB (vector store)
chroma run --host localhost --port 8001 --path ./data/chroma

# Start Ollama (LLM service)
ollama serve
ollama pull mistral
ollama pull nomic-embed-text

# Start Postgres/Redis (Optional - if configured)
# redis-server e:\grid\config\redis.conf
# pg_ctl -D e:\grid\data\postgres start

```

### Service Health Checks

```bash
# Check ChromaDB
curl http://localhost:8001/api/v1/heartbeat

# Check Ollama
curl http://localhost:11434/api/tags

# Check main API
curl http://localhost:8000/health

# Check database connection
python -c "from application.database import engine; print(engine.execute('SELECT 1').scalar())"
```

## Environment Configuration

### Required Environment Variables

```bash
# Database (Local First defaults)
MOTHERSHIP_DATABASE_URL=sqlite:///grid.db
# REDIS_URL=redis://localhost:6379/0 (Optional)

# AI/ML
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Security
MOTHERSHIP_SECRET_KEY=dev-secret-key

```

### Configuration Files

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
notepad .env

# Validate configuration
python -c "from application.config import settings; print(settings.dict())"
```

## Performance Monitoring

### Benchmarking

```bash
# Run performance benchmarks
python -m tools.performance.benchmark

# RAG performance
python -m tools.rag.cli evaluate --benchmark

# API load testing
python -m tools.performance.load_test --concurrent 10 --duration 60
```

### Profiling

```bash
# Profile API endpoints
python -m tools.performance.profile --endpoint "/api/v1/query"

# Memory profiling
python -m memory_profiler tools/rag/cli.py query "test"

# CPU profiling
python -c "
import cProfile
import pstats
cProfile.run('python -m application.mothership.main', 'profile.stats')
pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)
"
```

## Troubleshooting

### Common Issues

**Path Traversal Errors**

```bash
# Check security validation
python -m pytest tests/security/test_path_traversal.py -v

# Validate file operations
python -c "from src.grid.security.path_validator import PathValidator; print(PathValidator.validate_path('test.txt', 'e:\grid'))"
```

**Dependency Conflicts**

```bash
# Check dependency tree
uv pip tree

# Resolve conflicts
uv pip install --force-reload

# Clean reinstall
uv venv --clear
uv sync --group dev --group test
```

**Import Errors**

```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Validate imports
python -c "import src.grid.core; print('OK')"

# Check module structure
python -c "import pkgutil; print([name for _, name, _ in pkgutil.iter_modules('src')])"
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m application.mothership.main

# Memory leak detection
python -m tracemalloc --limit 100
python -m application.mothership.main
python -c "import tracemalloc; snapshot = tracemalloc.take_snapshot(); top_stats = snapshot.statistics('lineno'); print(top_stats[:10])"
```

## Release Process

### Version Management

```bash
# Update version in pyproject.toml
# Update version in __init__.py files
# Update CHANGELOG.md

# Run full test suite
pytest

# Build documentation
mkdocs build

# Create release tag
git tag -a v2.2.1 -m "Release version 2.2.1"
git push origin v2.2.1
```


```bash
# Build production image

# Tag for registry

# Push to registry
```

## Integration with Other Tools

### VS Code Integration

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest",
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Start Development Server",
      "type": "shell",
      "command": "python",
      "args": ["-m", "application.mothership.main"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "dedicated"
      }
    }
  ]
}
```

### Git Hooks

```bash
# Pre-commit hook
#!/bin/sh
ruff check .
black --check .
pytest tests/unit/ -q

# Pre-push hook
#!/bin/sh
pytest
safety check
```

## Cross-References

- **Dependency Versions**: See `DEPENDENCY_MATRIX.md` for complete version matrix
- **Security Guidelines**: See `docs/AGENTS.md` for security patterns
- **Architecture**: See `docs/architecture.md` for system design
- **Patterns**: See `docs/pattern_language.md` for development patterns

## Notes

- Always run commands from `e:\grid` root directory unless specified
- Use `uv` for dependency management, `pip` only as fallback
- Python 3.13.11 is enforced across all projects
- Security validation is mandatory for all file operations
- Check `DEPENDENCY_MATRIX.md` for current dependency versions
