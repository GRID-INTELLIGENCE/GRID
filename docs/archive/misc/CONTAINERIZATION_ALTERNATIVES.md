# Alternative Containerization Solutions




```bash
# Build and test

# Run application
```


Podman is a daemonless container engine that works well on Windows:

### Installation:
1. Download from: https://github.com/containers/podman/releases
2. Install Podman for Windows
3. Run: `podman machine init` then `podman machine start`

### Usage:
```bash
podman build -t grid:latest .

# Run tests
podman run --rm grid:latest pytest tests/ -v --cov=src

# Run application
podman run -p 8000:8000 grid:latest
```

## Option 3: Virtual Environment + Process Isolation

For development without containers:

```bash
# Create isolated environment
python -m venv .grid_env
.grid_env\Scripts\activate  # Windows
# source .grid_env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r Python/requirements.txt

# Run tests
pytest tests/ -v --cov=src --cov-report=html

# Run application
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

## Option 4: GitHub Actions CI/CD

Use GitHub Actions for containerized testing:

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: pip install -r Python/requirements.txt
    - name: Run tests
      run: pytest tests/ -v --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Current Status

- ✅ Containerization configuration files created
- ✅ Alternative solutions available

## Quick Fix Attempts

Try these in order:

   ```powershell

   ```

   ```powershell
   ```

3. **Use Podman instead:**
   - Install Podman

4. **Use virtual environment:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r Python/requirements.txt
   pytest tests/unit/test_nl_dev.py -k triage -v
   ```

The containerization infrastructure is ready - we just need a working container runtime!
