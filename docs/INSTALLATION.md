# Installation Guide

Complete installation instructions for Grid project across different platforms and use cases.

---

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Detailed Installation](#detailed-installation)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Troubleshooting](#troubleshooting)

---

## 💻 System Requirements

### Minimum Requirements

- **Python**: 3.10 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for installation
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)

### Optional Requirements

- **Docker**: 20.10+ (for containerized deployment)
- **Git**: 2.30+ (for development)
- **Make**: For using Makefile commands

---

## 🚀 Quick Installation

### For End Users

```bash
# Install from PyPI (when published)
pip install grid
```

### For Developers

```bash
# Clone repository
git clone https://github.com/your-org/grid.git
cd grid

# Install in editable mode with all dependencies
pip install -e ".[dev,api,ml]"
```

---

## 📦 Detailed Installation

### Step 1: Install Python

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer, **check "Add Python to PATH"**
3. Verify: `python --version`

#### macOS
```bash
# Using Homebrew
brew install python@3.11

# Verify
python3 --version
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip

# Verify
python3 --version
```

### Step 2: Clone Repository

```bash
# Clone via HTTPS
git clone https://github.com/your-org/grid.git

# Or via SSH
git clone git@github.com:your-org/grid.git

# Navigate to project
cd grid
```

### Step 3: Create Virtual Environment

#### Windows (PowerShell)
```powershell
# Create virtual environment
python -m venv .venv

# Activate
.\.venv\Scripts\Activate.ps1

# If execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Unix/macOS
```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate
```

### Step 4: Install Dependencies

```bash
# Install core dependencies only
pip install -e .

# Install with development tools
pip install -e ".[dev]"

# Install all features
pip install -e ".[dev,api,ml]"
```

### Step 5: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use your preferred editor)
# Windows
notepad .env

# Unix/macOS
nano .env
# or
vim .env
```

**Required Configuration**:
```env
# Minimum required settings
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-this-to-random-string
API_HOST=0.0.0.0
API_PORT=8000
```

### Step 6: Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify
python -c "from src.database import engine; print('Database OK')"
```

### Step 7: Verify Installation

```bash
# Check package installation
python -c "import grid; print(grid.__version__)"

# Expected output: 0.1.0
```

---

## 🖥️ Platform-Specific Instructions

### Windows-Specific Setup

#### Using Windows Terminal
```powershell
# Install Windows Terminal from Microsoft Store
# Recommended for better experience

# Set PowerShell as default shell
# Settings → Startup → Default Profile → PowerShell
```

#### Common Windows Issues

**Problem**: `python` not found
```powershell
# Solution: Add Python to PATH manually
# System Properties → Environment Variables
# Add: C:\Users\YourName\AppData\Local\Programs\Python\Python311
```

**Problem**: Execution policy restricts scripts
```powershell
# Solution: Allow local scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### macOS-Specific Setup

#### Using Homebrew
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install additional tools
brew install git make
```

### Linux-Specific Setup

#### Ubuntu/Debian
```bash
# Install all required packages
sudo apt update
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    make \
    build-essential

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

#### CentOS/RHEL
```bash
# Install Python 3.11
sudo yum install -y python3.11 python3.11-pip git make gcc

# Or using dnf
sudo dnf install -y python3.11 python3.11-pip git make gcc
```

---

## 🐳 Docker Installation

### Install Docker

#### Windows
1. Download [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Run installer
3. Restart computer
4. Verify: `docker --version`

#### macOS
```bash
# Using Homebrew
brew install --cask docker

# Or download from Docker website
```

#### Linux
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Run with Docker

```bash
# Build image
docker build -t grid:latest .

# Run container
docker run -p 8000:8000 --env-file .env grid:latest

# Or use docker-compose
docker-compose up -d
```

---

## 🔧 Development Setup

### Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

### Install Optional Tools

```bash
# Database tools
pip install pgcli  # PostgreSQL CLI

# Testing tools
pip install pytest-xdist  # Parallel testing
pip install pytest-benchmark  # Performance testing

# Documentation tools
pip install mkdocs mkdocs-material  # Documentation site
```

### IDE Setup

#### Visual Studio Code
1. Install Python extension
2. Install recommended extensions:
   - Python
   - Pylance
   - Black Formatter
   - isort
   - Docker

#### PyCharm
1. Open project folder
2. Configure Python interpreter:
   - File → Settings → Project → Python Interpreter
   - Add interpreter → Existing environment
   - Select `.venv/Scripts/python.exe` (Windows)
3. Enable Django support (if needed)

---

## 🔍 Troubleshooting

### Common Issues

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'grid'`

**Solution**:
```bash
# Reinstall in editable mode
pip install -e .

# Verify PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"
```

#### Database Errors

**Problem**: `OperationalError: no such table`

**Solution**:
```bash
# Run migrations
alembic upgrade head

# Or reset database
rm app.db
alembic upgrade head
```

#### Port Already in Use

**Problem**: `Address already in use: 8000`

**Solution**:
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Unix/macOS: Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn src.api.main:app --port 8001
```

#### Permission Errors (Docker)

**Problem**: `Permission denied` when running Docker

**Solution**:
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended)
sudo docker-compose up
```

### Getting Help

If you encounter issues not covered here:

1. **Check existing issues**: [GitHub Issues](https://github.com/your-org/grid/issues)
2. **Ask in discussions**: [GitHub Discussions](https://github.com/your-org/grid/discussions)
3. **Contact support**: your.email@example.com

---

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] Python version is 3.10+: `python --version`
- [ ] Virtual environment is activated
- [ ] Package is installed: `python -c "import grid; print(grid.__version__)"`
- [ ] Environment file exists: `.env`
- [ ] Database is initialized: `app.db` exists
- [ ] API starts: `uvicorn src.api.main:app`
- [ ] Tests run: `pytest`
- [ ] Pre-commit hooks work: `pre-commit run --all-files`

---

## 🎉 Next Steps

Once installed:

1. **Read the documentation**: [README.md](README.md)
2. **Explore the API**: Visit http://localhost:8000/docs
3. **Run tests**: `pytest` or `make test`
4. **Start developing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

Welcome to Grid! 🚀
