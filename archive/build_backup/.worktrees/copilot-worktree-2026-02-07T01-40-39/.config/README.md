# GRID Configuration Hub

**Central configuration management for E:\ workspace**  
Version: 1.0.0 | Last Updated: 2026-01-24 | Status: ✅ Active

---

## Structure

```
E:\.config/
├── schema/
│   ├── toolset-contract.json     ← Machine-readable tool definitions & validation rules
│   ├── repos.json.schema         ← JSON Schema for Apps/backend/config/repos.json
│   └── architecture.json         ← Dependency graph (future)
├── runtime/
│   ├── repos.json                ← Enabled repositories registry (Apps backend)
│   ├── .env.grid                 ← Grid service environment
│   └── .env.pipeline             ← Pipeline service environment
├── secrets/
│   ├── .env.apps.template        ← Frontend secrets (DO NOT CHECK IN)
│   ├── .env.eufle.template       ← EUFLE model keys (DO NOT CHECK IN)
│   ├── .env.github.template      ← GitHub SDK token (DO NOT CHECK IN)
│   └── .env.editor               ← VS Code / Windsurf integration (DO NOT CHECK IN)
└── README.md                      ← This file
```

---

## Purpose

**Single Source of Truth** for all workspace configuration:
- ✅ Toolset definitions (10 GRID toolsets with entry points, dependencies, capabilities)
- ✅ Environment variables (standardized naming across 5 projects)
- ✅ Schema validation (JSON Schema, Pydantic models)
- ✅ Integration matrix (tool dependencies)
- ✅ Global settings (paths, performance tuning)

---

## Usage

### For Development

**Load configuration**:
```python
# Python
import json
with open('E:/.config/schema/toolset-contract.json') as f:
    config = json.load(f)

# Access toolset
tools = config['toolsetContract']['toolsets']['coreIntelligence']
```

**Validate runtime config**:
```python
from pathlib import Path
import json

schema = json.load(open('E:/.config/schema/repos.json.schema'))
runtime = json.load(open('E:/.config/runtime/repos.json'))

# Validate against schema (use jsonschema library)
import jsonschema
jsonschema.validate(runtime, schema)
```

### For VS Code Integration

**Windsurf / VS Code auto-discover tools**:
```
1. VS Code reads: $APPDATA/Code/User/prompts/toolkit.toolsets.jsonc
2. toolkit.toolsets.jsonc imports from: E:\.config\schema\toolset-contract.json
3. All 10 toolsets available in VS Code chat + commands
```

### For Deployment

**Bootstrap environment**:
```powershell
# Copy secrets template
copy E:\.config\secrets\.env.apps.template E:\.config\secrets\.env.apps
edit E:\.config\secrets\.env.apps  # Add actual secrets

# Load runtime config
$repos = Get-Content E:\.config\runtime\repos.json | ConvertFrom-Json
```

---

## Configuration Categories

### Schema/ — Definitions & Validation

| File | Purpose | Updated By |
|------|---------|-----------|
| `toolset-contract.json` | GRID toolset definitions (10 toolsets) | Manually (part of plan) |
| `repos.json.schema` | JSON Schema for repos registry | Manually (part of plan) |
| `architecture.json` | Machine-readable dependency graph | Generated (part of Stage 4) |

### Runtime/ — Services & Environment

| File | Purpose | Use Case |
|------|---------|----------|
| `repos.json` | Enabled repositories for Apps harness | Apps backend `config_service.py` |
| `.env.grid` | Grid service configuration | `grid/.env` (symlink or copy) |
| `.env.pipeline` | Pipeline service configuration | `pipeline/.env` (symlink or copy) |

### Secrets/ — API Keys & Tokens (DO NOT CHECK IN)

| File | Purpose | How to Populate |
|------|---------|-----------------|
| `.env.apps.template` | Frontend API keys (GEMINI_API_KEY, etc.) | Copy from `Apps/.env.local` |
| `.env.eufle.template` | Model provider keys (OpenAI, HuggingFace) | Copy from `EUFLE/config/.env.example` |
| `.env.github.template` | GitHub SDK token | Generate at https://github.com/settings/tokens |
| `.env.editor` | VS Code / Windsurf integration | Create from `.editor-config/.env.editor.template` |

**Important**: Add `secrets/` to `.gitignore` — never commit API keys.

---

## Validation

### At Startup

Apps backend validates on startup:
```python
# backend/main.py (startup event)
@app.on_event("startup")
async def validate_config():
    config_service = get_config_service()
    repos = config_service.get_enabled_repos()
    # Validates repos.json against schema
    # Checks all repo paths exist
    # Reports any misconfigurations
```

### Manual Validation

```powershell
# Validate JSON syntax
$contract = Get-Content E:\.config\schema\toolset-contract.json | ConvertFrom-Json
Write-Host "✓ Toolset schema valid"

# Validate repos registry
$repos = Get-Content E:\.config\runtime\repos.json | ConvertFrom-Json
Write-Host "✓ Repos registry valid ($($repos.repos.Count) repos)"
```

---

## Environment Variables

### Global (all projects)

```
GRID_SESSIONS=logs/sessions
GRID_CONVERSATIONS=logs/conversations
GRID_ROOT=${workspaceFolder}
PYTHONPATH=${workspaceFolder}/src
```

### Project-Specific

**Grid** (`E:\.config\runtime\.env.grid`):
```
OLLAMA_BASE_URL=http://localhost:11434
CHROMADB_PATH=.rag_db/
```

**Pipeline** (`E:\.config\runtime\.env.pipeline`):
```
AWS_S3_BUCKET=my-bucket
OCR_ENGINE=tesseract
```

**Apps Frontend** (`E:\.config\secrets\.env.apps`):
```
VITE_API_URL=http://localhost:8000
VITE_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
GEMINI_API_KEY=...
```

---

## Integration Matrix

**Tool dependencies** (from `toolsetContract.integrationMatrix`):

```
coreIntelligence ──→ ragSystem, aiCollaboration
ragSystem ──────────→ coreIntelligence, developmentAutomation
architecturalTools ─→ codeQuality, workspaceUtils
codeQuality ───────→ systemMonitoring, architecturalTools
systemMonitoring ──→ developmentAutomation
llmOperations ─────→ dataPipeline, codeQuality
dataPipeline ──────→ llmOperations, workspaceUtils
workspaceUtils ────→ architecturalTools, dataPipeline
developmentAutomation ──→ systemMonitoring, aiCollaboration
aiCollaboration ───→ coreIntelligence, ragSystem, developmentAutomation
```

Use this to understand tool initialization order and dependencies.

---

## Next Steps

1. **[Stage 1]** Populate `secrets/` with actual API keys (from `.template` files)
2. **[Stage 2]** Add `repos.json.schema` validation to Apps startup
3. **[Stage 3]** Generate `architecture.json` from workspace analysis
4. **[Stage 4]** Export configuration as API endpoint (`GET /api/config/repos`)
5. **[Ongoing]** Keep `toolset-contract.json` in sync with codebase changes

---

## Support

**Questions?** Check:
- [E:\.editor-config\IMPLEMENTATION_GUIDE.md](E:/.editor-config/IMPLEMENTATION_GUIDE.md) — Quick start
- [E:\ARCHITECTURE_EXECUTIVE_SUMMARY.md](E:/ARCHITECTURE_EXECUTIVE_SUMMARY.md) — System design
- [E:\analysis_outputs\COMPREHENSIVE_ANALYSIS_REPORT.md](E:/analysis_outputs/COMPREHENSIVE_ANALYSIS_REPORT.md) — Detailed findings
