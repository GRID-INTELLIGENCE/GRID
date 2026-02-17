# GRID Global Dev Programs Configuration

**Version**: 1.0  
**Created**: February 5, 2026  
**Purpose**: Configure global rules, skills, and workflows for different dev programs

**Core principles (adamantly maintained):** Transparency and openness. Policy is visible and version-controlled; access to AI providers worldwide is a design goal. External API and network tools are not blocked by default so that RAG, agents, and services can use providers (OpenAI, Anthropic, etc.) where intended. See [docs/PRINCIPLES.md](../../docs/PRINCIPLES.md).

---

## Supported Dev Programs

This system provides program-specific configurations for:

| Dev Program | Focus | Primary Stack | Complexity |
|-------------|-------|----------------|------------|
| **analytics-data** | Data analysis, visualization | Python, Pandas, NumPy | Low |
| **ml-audio** | Audio ML, speech processing | PyTorch, TensorFlow | High |
| **ml-image** | Computer vision, image processing | PyTorch, OpenCV | High |
| **ml-nlp** | NLP, text analysis | HuggingFace, Transformers | High |
| **web-fastapi** | Python web APIs | FastAPI, SQLAlchemy | Medium |
| **web-react** | Frontend applications | React, TypeScript | Medium |
| **data-science** | Data science pipelines | Scikit-learn, XGBoost | Medium |
| **devops-infra** | Infrastructure, CI/CD | Docker, Kubernetes | High |
| **security** | Security research, audits | Python, Radare2 | High |
| **ai-research** | AI research, experiments | JAX, PyTorch | High |

---

## Global Configuration Variables

These are applied across all dev programs unless overridden program-specific:

```yaml
# Global defaults
global:
  python_version: "3.13"
  timeout_seconds: 60
  max_tokens: 4096
  memory_limit_mb: 512
  strict_mode: true
  audit_enabled: true
  
  # Allowed MCP tools
  allowed_tools:
    - filesystem
    - git
    - python-repl
    - ollama
    - bash
    - database
    
  # Blocked tools (external_api and network allowed so RAG and services can use OpenAI/Anthropic/etc.)
  blocked_tools:
    - system_access
    
  # Model preferences
  models:
    embedding: "nomic-embed-text"
    general: "ministral"
    safety: "gpt-oss-safeguard"
    
  # Code quality
  code_quality:
    linting: ["ruff"]
    formatting: ["ruff"]
    type_checking: ["mypy"]
    max_line_length: 120
    
  # Testing
  testing:
    framework: "pytest"
    coverage_threshold: 80
    async_tests: true
```

---

## Dev Program Configurations

### 1. Analytics Data Program

```yaml
program: analytics-data
location: src/analytics/
model: "ministral"
timeout_seconds: 30
strict_mode: false

allowed_tools:
  - filesystem
  - git
  - python-repl
  - ollama
  - bash
  
blocked_tools: []
  
frameworks:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - plotly
  
workflows:
  - data_ingestion
  - data_cleaning
  - data_visualization
  - report_generation
  
skills:
  - transform.pivot_table
  - context.data_analysis
  - compress.summarize
```

### 2. ML Audio Program

```yaml
program: ml-audio
location: src/ml/audio/
model: "ministral"
timeout_seconds: 120
strict_mode: true

allowed_tools:
  - filesystem
  - git
  - python-repl
  - ollama
  - bash
  
blocked_tools: []
  
frameworks:
  - pytorch
  - torch_audio
  - librosa
  - audiomentations
  - torchaudio
  
workflows:
  - audio_preprocessing
  - feature_extraction
  - model_training
  - audio_generation
  
skills:
  - context.audio_analysis
  - transform.audio_features
  - compress.signal_data
  - safety.audio_anomaly_detection
```

### 3. Web FastAPI Program

```yaml
program: web-fastapi
location: src/web/fastapi/
model: "ministral"
timeout_seconds: 45
strict_mode: true

allowed_tools:
  - filesystem
  - git
  - python-repl
  - ollama
  - bash
  - database
  
blocked_tools: []
  
frameworks:
  - fastapi
  - sqlalchemy
  - pydantic
  - uvicorn
  - alembic
  
workflows:
  - api_design
  - endpoint_creation
  - database_migration
  - api_documentation
  
skills:
  - transform.api_spec
  - security.rest_validation
  - compress.response_data
  - intelligence.performance_profiling
```

### 4. Web React Program

```yaml
program: web-react
location: src/web/react/
model: "ministral"
timeout_seconds: 45
strict_mode: false

allowed_tools:
  - filesystem
  - git
  - python-repl
  - ollama
  - bash
  
blocked_tools: []
  
frameworks:
  - react
  - typescript
  - vite
  - tailwindcss
  - zustand
  
workflows:
  - component_creation
  - state_management
  - api_integration
  - testing
  
skills:
  - transform.jsx_tsx
  - context.react_patterns
  - diagnostics.component_audit
```

### 5. Security Research Program

```yaml
program: security
location: src/security/
model: "ministral"
timeout_seconds: 180
strict_mode: true

allowed_tools:
  - filesystem
  - git
  - python-repl
  - ollama
  - bash
  
blocked_tools: []
  
frameworks:
  - radare2
  - frida
  - pwntools
  - scapy
  
workflows:
  - vulnerability_analysis
  - exploit_detection
  - security_audit
  - threat_report
  
skills:
  - security.scan_codebase
  - ai_safety.threat_analysis
  - intelligence.analyze_malware
  - compress.vulnerability_report
```

---

## Workflows by Dev Program

### Analytics Data Workflows

1. **data_ingestion**
   - Read CSV/JSON/Parquet files
   - Validate data schema
   - Handle missing values
   - Store in DuckDB/SQLite

2. **data_cleaning**
   - Remove duplicates
   - Handle outliers
   - Normalize data
   - Create cleaned dataset

3. **data_visualization**
   - Generate plots (matplotlib/seaborn)
   - Create dashboards (plotly)
   - Export to HTML/PNG

4. **report_generation**
   - Generate PDF reports
   - Create Jupyter notebooks
   - Export to markdown

---

### ML Audio Workflows

1. **audio_preprocessing**
   - Load audio files
   - Convert to spectrograms
   - Apply noise reduction
   - Segment audio

2. **feature_extraction**
   - Extract MFCCs
   - Extract Mel-spectrograms
   - Pitch tracking
   - Rhythm analysis

3. **model_training**
   - Train CNN for classification
   - Train RNN for sequence modeling
   - Hyperparameter tuning

4. **audio_generation**
   - Generate audio samples
   - Apply post-processing
   - Export to WAV/MP3

---

### Web FastAPI Workflows

1. **api_design**
   - Create OpenAPI spec
   - Define Pydantic models
   - Design endpoints
   - Plan database schema

2. **endpoint_creation**
   - Create routes
   - Add middleware
   - Implement business logic
   - Add error handling

3. **database_migration**
   - Create migrations
   - Apply schema changes
   - Seed initial data
   - Rollback support

4. **api_documentation**
   - Generate OpenAPI docs
   - Create API examples
   - Write test documentation
   - Export Swagger UI

---

### Security Research Workflows

1. **vulnerability_analysis**
   - Scan code with bandit
   - Check dependencies
   - Analyze entry points
   - Identify attack vectors

2. **exploit_detection**
   - Pattern match exploit code
   - Analyze shellcode
   - Identify persistence mechanisms
   - Detect privilege escalation

3. **security_audit**
   - Review authentication
   - Check authorization
   - Audit logging
   - Verify encryption

4. **threat_report**
   - Generate CVSS scores
   - Document vulnerabilities
   - Create remediation plan
   - Export to audit format

---

## Skill Registries by Program

### Global Skills (All Programs)

```python
# Transform Skills
transform.schema_map
transform.api_schema
transform.jsx_tsx

# Context Skills
context.refine
context.pattern_match
context.compression

# Compression Skills
compress.summarize
compress.articulate
compress.extract_essence

# Security Skills
security.scan_codebase
security.rate_limiter
security.path_validator
```

### Program-Specific Skills

#### Analytics Data
```python
skills.analytics:
  - transform.pivot_table
  - transform.aggregate_data
  - context.data_insights
  - compress.metric_summary
```

#### ML Programs
```python
skills.ml_common:
  - context.ml_experiments
  - compress.model_artifacts
  - security.model_bias_check
  
skills.ml_audio:
  - context.audio_analysis
  - transform.audio_features
  
skills.ml_image:
  - context.image_analysis
  - transform.image_features
```

#### Web Programs
```python
skills.web:
  - transform.api_spec
  - transform.component_prop
  - context.state_management
  - security.rest_validation
```

---

## Dev Program Detection

Automatic detection based on directory structure:

```python
def detect_program(directory: str) -> str:
    """Detect which dev program directory belongs to"""
    
    program_signatures = {
        "analytics-data": ["pandas", "numpy", "matplotlib"],
        "ml-audio": ["librosa", "torchaudio", "audio"],
        "ml-image": ["cv2", "torchvision", "image"],
        "ml-nlp": ["transformers", "huggingface", "nlp"],
        "web-fastapi": ["fastapi", "uvicorn", "api"],
        "web-react": ["react", "vite", "tsx", "jsx"],
        "data-science": ["sklearn", "xgboost", "pipeline"],
        "security": ["radare2", "frida", "vulnerability"],
        "ai-research": ["jax", "research", "experiment"]
    }
    
    for program, signatures in program_signatures.items():
        if any(sig in directory.lower() for sig in signatures):
            return program
    
    return "default"
```

---

## CLI Usage

```bash
# List all dev programs
python -m grid devprograms list

# Set active program
python -m grid devprograms set web-fastapi

# Get current program config
python -m grid devprograms get

# Validate program configuration
python -m grid devprograms validate

# Generate program-specific code
python -m grid devprograms generate --program ml-audio --workflow audio_preprocessing

# Check program compatibility
python -m grid devprograms check --target program1 --source program2
```

---

## File Structure

```
.grid/
├── devprograms/
│   ├── programs/
│   │   ├── analytics-data.yml
│   │   ├── ml-audio.yml
│   │   ├── web-fastapi.yml
│   │   └── security.yml
│   ├── workflows/
│   │   ├── analytics-data/
│   │   │   ├── data_ingestion.json
│   │   │   └── data_visualization.json
│   │   ├── ml-audio/
│   │   │   └── audio_preprocessing.json
│   │   └── web-fastapi/
│   │       └── api_design.json
│   └── skills/
│       ├── global/
│       ├── analytics-data/
│       └── security/
```

---

## Migration from Config

To migrate from single config to dev programs:

```bash
# Export current config to default program
python -m grid devprograms export --from .cursorrules

# Import program-specific config
python -m grid devprograms import --target workspace --program web-fastapi

# Compare configs
python -m grid devprograms diff --program web-fastapi --ref .cursorrules
```

---

## Best Practices

1. **Always detect program first**: Use `detect_program()` to identify context
2. **Apply global defaults first**: Start with global config, then program overrides
3. **Validate program config**: Use `validate_program()` before applying
4. **Use program-specific workflows**: Leverage standardized workflows
5. **Audit skill usage**: Track which skills are used per program
6. **Maintain compatibility**: Ensure skills work across programs

---

## Troubleshooting

### Program Not Detected

```bash
# Debug detection
python -m grid devprograms debug-detect --directory /path/to/code

# Use explicit program
python -m grid devprograms set --program ml-audio --directory /path/to/code
```

### Workflow Not Found

```bash
# Use fallback workflow
python -m grid devpackages workflows list --program analytics-data

# Use template workflow
python -m grid devpackages generate --program analytics-data --workflow code_review
```

### Skill Missing

```bash
# Use global skill
python -m grid skills run transform.schema_map

# Use program skill
python -m grid skills run context.data_analysis --program analytics-data
```

---

## Future Enhancements

- [ ] Program-specific caching
- [ ] Cross-program workflow orchestration
- [ ] Skill dependency resolution
- [ ] Automatic program switching
- [ ] Program compatibility matrix
- [ ] Dev program marketplace

---

**Document Status**: Production Ready ✅  
**Last Updated**: February 5, 2026