# Workspaces and Submodules

This workspace uses a hybrid git management strategy to handle multiple related projects while respecting independent repositories.

## Repository Structure

### Primary Active Projects (Independent Repositories)

#### 1. GRID Framework (`grid/`)
- **Repository**: `git@github.com:irfankabir02/GRID.git`
- **Role**: Core cognitive framework with RAG system
- **Dependencies**: FastAPI, ChromaDB, Ollama, scikit-learn
- **Status**: Active development, main framework

#### 2. EUFLE ML Operations (`projects/EUFLE/`)
- **Repository**: Independent (no remotes configured)
- **Role**: LLM fine-tuning and code transformation
- **Dependencies**: PyTorch, Transformers, PEFT, TRL
- **Status**: Active development, ML/AI operations

### Workspace Management Repository (This Repository)

#### Root Workspace (`E:\`)
- **Repository**: Initialize here for workspace coordination
- **Role**: Meta-management of all projects
- **Contains**:
  - Shared configuration (`config/`, `.env.editor.template`)
  - Shared utilities (`shared/`, `scripts/`)
  - Documentation (`AGENTS.md`, `DEPENDENCY_MATRIX.md`)
  - Cross-project automation
  - Development environment setup

## Git Strategy

### 1. Independent Project Repositories
`grid/` and `projects/EUFLE/` maintain their own git histories:
```bash
# GRID Framework
cd grid
git status
git add .
git commit -m "Update framework"
git push origin main

# EUFLE Operations  
cd projects/EUFLE
git status
git add .
git commit -m "Update ML operations"
git push origin master
```

### 2. Workspace Coordination Repository
Initialize root git for workspace-level management:
```bash
# Root workspace (this repository)
cd E:\
git init
git add AGENTS.md DEPENDENCY_MATRIX.md README.md
git add .gitignore scripts/ shared/ config/
git commit -m "Initialize workspace coordination"
```

### 3. Git Ignore Strategy
Root `.gitignore` excludes:
- Project-specific git repos (`grid/.git`, `projects/*/.git`)
- Build artifacts and caches
- Local configuration and data
- Temporary files

## Project Roles and Responsibilities

### GRID Framework (`grid/`)
**Primary Functions:**
- Cognitive architecture and event systems
- Local-first RAG with ChromaDB
- API server and CLI tools
- Pattern recognition and analysis
- Integration with Ollama models

**Key Directories:**
- `src/grid/` - Core framework
- `src/application/` - FastAPI applications
- `src/cognitive/` - AI integration
- `src/tools/` - Utilities and CLI
- `tests/` - Comprehensive test suite

### EUFLE ML Operations (`projects/EUFLE/`)
**Primary Functions:**
- LLM fine-tuning pipeline
- Code transformation operations
- Model routing and selection
- Training and evaluation

**Key Directories:**
- `studio/` - UI components
- `eufle/` - Core ML operations
- `evaluation/` - Testing and validation
- `config/` - Configuration and requirements

### Workspace Coordination (`E:\`)
**Primary Functions:**
- Cross-project documentation
- Shared development tools
- Environment setup scripts
- Dependency matrix management
- Agent development guidelines

## Development Workflow

### 1. Project-Specific Changes
```bash
# Working on GRID framework
cd grid
# Make changes
git add .
git commit -m "Feature: new cognitive pattern"
git push

# Working on EUFLE operations
cd projects/EUFLE
# Make changes
git add .
git commit -m "Update: new fine-tuning method"
git push
```

### 2. Workspace-Level Changes
```bash
# Working on shared documentation or scripts
cd E:\
# Update AGENTS.md, DEPENDENCY_MATRIX.md, etc.
git add AGENTS.md DEPENDENCY_MATRIX.md
git commit -m "Update: agent guidelines for new dependency"
git push
```

### 3. Cross-Project Integration
When changes span multiple projects:
1. Make changes in each project repository
2. Update workspace-level documentation
3. Commit changes in each repository independently
4. Use consistent commit messages across repositories

## Initialization Commands

### Initialize Workspace Repository
```bash
cd E:\
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
git add .gitignore README.md AGENTS.md DEPENDENCY_MATRIX.md
git add scripts/ shared/ config/
git commit -m "Initial commit: workspace coordination setup"
```

### Configure Remote (Optional)
```bash
# If you want to backup workspace coordination
git remote add origin git@github.com:username/workspace-coordination.git
git push -u origin main
```

## Conflict Prevention

### Repository Separation
- Each project maintains independent git history
- No nested git repositories in the same tree
- Workspace git ignores project `.git` directories

### Branch Strategy
- `main`/`master` for stable releases
- `develop` for integration work
- Feature branches for new work
- Consistent naming across projects

### Commit Convention
```
<type>: <description>

feat: Add new cognitive pattern
fix: Resolve RAG query timeout
docs: Update agent setup instructions
chore: Update dependency matrix
```

## Maintenance

### Regular Updates
1. **Weekly**: Update dependency matrix and agent guidelines
2. **Monthly**: Review and update documentation
3. **Quarterly**: Archive old analysis outputs
4. **As needed**: Update shared scripts and configurations

### Backup Strategy
- Each repository backed up independently
- Workspace coordination repository for configuration
- Separate remote repositories for disaster recovery

This structure allows independent development of GRID and EUFLE while providing centralized coordination and shared resources for the entire development ecosystem.
