# Usage Instructions & Use Case Scenarios

## Table of Contents

1. [Workspace Root (E:\)](#workspace-root-e)
2. [Grid Repository (E:\grid)](#grid-repository-egrid)
3. [EUFLE Repository (E:\EUFLE)](#eufle-repository-eeufle)
4. [Common Workflows](#common-workflows)

---

## Workspace Root (E:\)

### Overview

The workspace root (`E:\`) serves as the **coordination layer** for the multi-repository system. It contains:

- **`Apps/`** - Central orchestrator and UI
- **`grid/`** - AI/ML framework
- **`EUFLE/`** - HuggingFace chat scaffold
- **`pipeline/`** - Testing and benchmarking
- **`analysis_outputs/`** - Shared analysis artifacts
- **`analyze_repo.py`** - Deep analysis tool
- **`generate_artifacts.py`** - Artifact generation tool

### Recommended Settings

**Environment Variables:**
```bash
# Base path for all repositories
REPO_BASE_PATH=E:\

# Individual repo paths (optional, defaults from config)
REPO_GRID_PATH=grid
REPO_EUFLE_PATH=EUFLE
REPO_PIPELINE_PATH=pipeline
REPO_APPS_PATH=Apps

# Analysis configuration
REFRESH_THRESHOLD_HOURS=24

# Run retention
RUN_RETENTION_DAYS=90
RUN_RETENTION_COUNT=30
```

**Configuration File:**
- `Apps/backend/config/repos.json` - Repository registry

### Use Case: Initial System Setup

**Scenario**: Setting up the workspace for the first time

**Step 1: Verify Repository Structure**
```bash
# Check that all repos exist
cd E:\
dir grid
dir EUFLE
dir pipeline
dir Apps
dir analysis_outputs
```

**Step 2: Configure Repository Paths**
```bash
# Edit Apps/backend/config/repos.json
{
  "base_path": "E:\\",
  "repos": {
    "grid": { "path": "grid", "enabled": true },
    "eufle": { "path": "EUFLE", "enabled": true },
    "pipeline": { "path": "pipeline", "enabled": true },
    "apps": { "path": "Apps", "enabled": true }
  }
}
```

**Step 3: Set Environment Variables**
```powershell
# PowerShell
$env:REPO_BASE_PATH = "E:\"
$env:REFRESH_THRESHOLD_HOURS = "24"
```

**Step 4: Initialize Database**
```bash
cd Apps/backend
python -m uvicorn main:app --reload
# Database will be auto-created on first request
```

### Use Case: Running Deep Analysis on All Repos

**Scenario**: Generate comprehensive analysis artifacts for all repositories

**Step 1: Run Analysis Script**
```bash
cd E:\
python analyze_repo.py grid
python analyze_repo.py EUFLE
python analyze_repo.py pipeline
```

**Step 2: Generate Artifacts**
```bash
python generate_artifacts.py grid
python generate_artifacts.py EUFLE
```

**Step 3: Verify Artifacts**
```bash
dir analysis_outputs\grid
dir analysis_outputs\EUFLE
# Should contain: module_graph.json, entry_points.json, candidates.json, etc.
```

### Use Case: Creating a Harness Run

**Scenario**: Create an immutable snapshot for stakeholder demo

**Step 1: Start Backend**
```bash
cd Apps/backend
python -m uvicorn main:app --reload --port 8000
```

**Step 2: Create Run via API**
```bash
curl -X POST http://localhost:8000/api/harness/runs \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Q1 2026 Stakeholder Demo",
    "tags": ["demo", "stakeholder", "q1-2026"],
    "visibility": "shared"
  }'
```

**Response:**
```json
{
  "run_id": "20260114-143022Z_a3f2b1c4",
  "display_name": "Q1 2026 Stakeholder Demo",
  "tags": ["demo", "stakeholder", "q1-2026"],
  "status": "pending",
  "created_at": "2026-01-14T14:30:22Z"
}
```

**Step 3: Harvest All Repos**
```bash
curl -X POST "http://localhost:8000/api/harness/harvest?run_id=20260114-143022Z_a3f2b1c4&refresh=false"
```

**Step 4: Generate Packs**
```bash
curl -X POST http://localhost:8000/api/harness/runs/20260114-143022Z_a3f2b1c4/packs/generate
```

**Step 5: Retrieve Stakeholder Pack**
```bash
curl http://localhost:8000/api/harness/runs/20260114-143022Z_a3f2b1c4/packs/stakeholder
```

---

## Grid Repository (E:\grid)

### Overview

**Grid** is the **Geometric Resonance Intelligence Driver** - a comprehensive AI/ML framework featuring:

- Geometric Resonance Patterns (9 cognition patterns)
- Light of the Seven cognitive architecture
- Local-First RAG (ChromaDB + Ollama)
- Intelligent Skills Framework
- Resonance API for real-time activity processing
- Agentic System with event-driven case management

### Recommended Settings

**Python Environment:**
```bash
cd E:\grid
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt  # If exists
# or
pip install -e .  # If pyproject.toml exists
```

**Configuration Files:**
- `config/api_routes.yaml` - API route definitions
- `config/arena_config.yaml` - Arena configuration
- `config/qualityGates.json` - Quality gates
- `config/eufle_models.yaml` - EUFLE model integration

**Environment Variables:**
```bash
# Database
GRID_DATABASE_URL=sqlite:///./mothership.db

# RAG Configuration
CHROMA_DB_PATH=./data/chroma
OLLAMA_BASE_URL=http://localhost:11434

# API Configuration
GRID_API_HOST=0.0.0.0
GRID_API_PORT=8001
```

### Use Case: Setting Up Grid for Local Development

**Scenario**: Developer wants to run Grid locally for development

**Step 1: Clone/Verify Repository**
```bash
cd E:\grid
git status  # Verify repository state
```

**Step 2: Install Dependencies**
```bash
# Using uv (if available)
uv sync

# Or using pip
pip install -e .
```

**Step 3: Initialize Database**
```bash
# Grid uses SQLite by default
python -c "from grid.src import init_db; init_db()"
# Or run migrations if using Alembic
alembic upgrade head
```

**Step 4: Start Local Services**
```bash
# Start Ollama (if using local models)
ollama serve

# Start Grid API
python -m grid.src.api.main
# Or using uvicorn
uvicorn grid.src.api.main:app --host 0.0.0.0 --port 8001
```

**Step 5: Verify Installation**
```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy"}
```

### Use Case: Running Grid Analysis via Harness

**Scenario**: Analyze Grid codebase through the Apps harness

**Step 1: Ensure Grid is Configured**
```bash
# Verify Apps/backend/config/repos.json includes grid
{
  "repos": {
    "grid": { "path": "grid", "enabled": true }
  }
}
```

**Step 2: Create Analysis Run**
```bash
curl -X POST http://localhost:8000/api/harness/runs \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Grid Architecture Analysis",
    "tags": ["grid", "analysis"]
  }'
```

**Step 3: Harvest Grid Repository**
```bash
# Get run_id from previous response
RUN_ID="20260114-143022Z_a3f2b1c4"

curl -X POST "http://localhost:8000/api/harness/harvest/grid?run_id=$RUN_ID&refresh=true"
```

**Step 4: Access Normalized Graph**
```bash
curl http://localhost:8000/api/harness/runs/$RUN_ID/artifacts/grid/normalized.json
```

**Step 5: Generate Profile/Resume**
```bash
curl -X POST "http://localhost:8000/api/harness/runs/$RUN_ID/packs/generate-profile?repo_name=grid"
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/profile
```

### Use Case: Integrating Grid with EUFLE

**Scenario**: Use Grid's cognitive architecture with EUFLE models

**Step 1: Configure EUFLE Models in Grid**
```yaml
# config/eufle_models.yaml
models:
  - name: "ministral-14b"
    path: "../EUFLE/hf-models/ministral-14b"
    type: "gguf"
    context_size: 16384
```

**Step 2: Update Grid Config**
```bash
# Edit config/api_routes.yaml to include EUFLE endpoints
```

**Step 3: Test Integration**
```bash
# Start Grid
python -m grid.src.api.main

# Test EUFLE model access
curl -X POST http://localhost:8001/api/eufle/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "model": "ministral-14b"}'
```

---

## EUFLE Repository (E:\EUFLE)

### Overview

**EUFLE** is the **HuggingFace Chat & Discussions** scaffold - a minimal open-source framework for:

- Interactive terminal interface
- Default model routing (local Transformers)
- GGUF fallback support
- Ollama integration
- Model hierarchy (small/medium/large)
- RAG system integration

### Recommended Settings

**Python Environment:**
```bash
cd E:\EUFLE
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**Configuration Files:**
- `configs/eufle_defaults.json` - Default configuration
- `configs/model_specs.json` - Model specifications
- `configs/qualityGates.json` - Quality gates
- `configs/budget_rules.json` - Budget rules

**Environment Variables:**
```bash
# Model Paths
EUFLE_MODEL_PATH=./hf-models
EUFLE_GGUF_PATH=./models

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama2

# RAG Configuration
EUFLE_RAG_ENABLED=true
EUFLE_RAG_DB_PATH=./rag/chroma_db
```

### Use Case: Setting Up EUFLE for Local Development

**Scenario**: Developer wants to run EUFLE locally

**Step 1: Verify Repository**
```bash
cd E:\EUFLE
git status
```

**Step 2: Install Dependencies**
```bash
pip install -r requirements.txt
# Or if using pyproject.toml
pip install -e .
```

**Step 3: Download Models (Optional)**
```bash
# Models are in hf-models/ directory
# If needed, download additional models
python scripts/download_model.py --model ministral-14b
```

**Step 4: Configure EUFLE**
```bash
# Edit configs/eufle_defaults.json
{
  "default_model": "ministral-14b",
  "ollama_enabled": true,
  "rag_enabled": true
}
```

**Step 5: Start EUFLE**
```bash
python eufle.py
# Or for API mode
python -m eufle.api.main --port 8002
```

### Use Case: Running EUFLE Analysis via Harness

**Scenario**: Analyze EUFLE codebase through the Apps harness

**Step 1: Verify Configuration**
```bash
# Check Apps/backend/config/repos.json
{
  "repos": {
    "eufle": { "path": "EUFLE", "enabled": true }
  }
}
```

**Step 2: Create Run**
```bash
curl -X POST http://localhost:8000/api/harness/runs \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "EUFLE Model Analysis",
    "tags": ["eufle", "models", "rag"]
  }'
```

**Step 3: Harvest EUFLE**
```bash
RUN_ID="20260114-143022Z_a3f2b1c4"
curl -X POST "http://localhost:8000/api/harness/harvest/eufle?run_id=$RUN_ID"
```

**Step 4: Check AI Safety Analysis**
```bash
# The normalized graph includes AI safety metadata
curl http://localhost:8000/api/harness/runs/$RUN_ID/artifacts/eufle/normalized.json | \
  jq '.ai_safety'
```

**Expected Output:**
```json
{
  "model_usage": ["ollama", "huggingface"],
  "prompt_security_score": 0.85,
  "data_privacy_score": 0.9,
  "safety_patterns": ["local-first"],
  "risk_level": "low",
  "recommendations": []
}
```

### Use Case: EUFLE RAG System Integration

**Scenario**: Set up EUFLE's RAG system for document retrieval

**Step 1: Initialize RAG Database**
```bash
cd E:\EUFLE
python -c "from rag import init_rag; init_rag()"
```

**Step 2: Add Documents**
```bash
python scripts/add_documents.py --path ./docs --db-path ./rag/chroma_db
```

**Step 3: Test RAG Query**
```bash
python -c "
from rag import query_rag
result = query_rag('What is EUFLE?', top_k=3)
print(result)
"
```

**Step 4: Integrate with Harness**
```bash
# The harness will detect RAG patterns during analysis
curl -X POST "http://localhost:8000/api/harness/harvest/eufle?run_id=$RUN_ID&refresh=true"
```

---

## Common Workflows

### Workflow 1: Daily Development Cycle

**Morning Setup:**
```bash
# 1. Start all services
cd E:\Apps\backend
python -m uvicorn main:app --reload &

cd E:\grid
python -m grid.src.api.main &

cd E:\EUFLE
python eufle.py &
```

**During Development:**
```bash
# Make changes to grid or EUFLE
# Test locally
# Commit changes
```

**End of Day:**
```bash
# Create analysis run
curl -X POST http://localhost:8000/api/harness/runs \
  -d '{"display_name": "Daily Dev Run", "tags": ["daily"]}'

# Harvest changes
curl -X POST "http://localhost:8000/api/harness/harvest?refresh=true"

# Generate packs
curl -X POST http://localhost:8000/api/harness/runs/{run_id}/packs/generate
```

### Workflow 2: Stakeholder Demo Preparation

**Step 1: Create Stable Run**
```bash
curl -X POST http://localhost:8000/api/harness/runs \
  -d '{
    "display_name": "Stakeholder Demo - Q1 2026",
    "tags": ["demo", "stakeholder"],
    "visibility": "shared"
  }'
```

**Step 2: Harvest All Repos**
```bash
RUN_ID="..."
curl -X POST "http://localhost:8000/api/harness/harvest?run_id=$RUN_ID&refresh=false"
```

**Step 3: Mark as Stable**
```bash
curl -X POST http://localhost:8000/api/harness/runs/$RUN_ID/stable?is_stable=true
```

**Step 4: Generate All Packs**
```bash
curl -X POST http://localhost:8000/api/harness/runs/$RUN_ID/packs/generate
```

**Step 5: Retrieve Demo Materials**
```bash
# Stakeholder update
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/stakeholder

# Demo script
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/demo

# Compliance packet
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/compliance

# Monetization pack
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/monetization
```

### Workflow 3: AI Safety Audit

**Step 1: Create Safety-Focused Run**
```bash
curl -X POST http://localhost:8000/api/harness/runs \
  -d '{
    "display_name": "AI Safety Audit - January 2026",
    "tags": ["safety", "audit", "compliance"]
  }'
```

**Step 2: Harvest with AI Safety Analysis**
```bash
RUN_ID="..."
curl -X POST "http://localhost:8000/api/harness/harvest?run_id=$RUN_ID&refresh=true"
```

**Step 3: Generate Profile with AI Safety**
```bash
curl -X POST "http://localhost:8000/api/harness/runs/$RUN_ID/packs/generate-profile"
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/profile | jq '.ai_safety_analysis'
```

**Step 4: Review Safety Recommendations**
```bash
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/profile | \
  jq '.ai_safety_analysis.recommendations'
```

### Workflow 4: Monetization Health Check

**Step 1: Generate Monetization Pack**
```bash
RUN_ID="..."
curl -X POST http://localhost:8000/api/harness/runs/$RUN_ID/packs/generate-monetization
```

**Step 2: Check Stripe Health**
```bash
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/monetization?format=json | \
  jq '.stripe_health'
```

**Step 3: Review Subscription Metrics**
```bash
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/monetization?format=json | \
  jq '.subscription_metrics'
```

**Step 4: Assess Readiness**
```bash
curl http://localhost:8000/api/harness/runs/$RUN_ID/packs/monetization?format=json | \
  jq '.monetization_readiness'
```

---

## Troubleshooting

### Issue: Repository Not Found

**Solution:**
```bash
# Check configuration
cat Apps/backend/config/repos.json

# Verify path exists
dir E:\grid
dir E:\EUFLE

# Set environment variable override
$env:REPO_GRID_PATH = "E:\grid"
```

### Issue: Analysis Artifacts Missing

**Solution:**
```bash
# Run analysis manually
cd E:\
python analyze_repo.py grid
python generate_artifacts.py grid

# Verify artifacts created
dir analysis_outputs\grid
```

### Issue: Harness Run Fails

**Solution:**
```bash
# Check run status
curl http://localhost:8000/api/harness/runs/{run_id}

# Check manifest
cat Apps/data/harness/runs/{run_id}/manifest.json

# Check logs
# (Logs should be in backend console or log files)
```

### Issue: AI Safety Analysis Not Working

**Solution:**
```bash
# Verify AI safety analyzer is imported
python -c "from Apps.backend.services.ai_safety_analyzer import analyze_codebase_ai_safety; print('OK')"

# Check repository path is accessible
# AI safety analyzer needs direct file access to repo
```

---

**Last Updated**: 2026-01-14
**Version**: 1.0
