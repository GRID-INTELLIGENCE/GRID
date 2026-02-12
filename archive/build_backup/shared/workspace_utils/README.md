# Workspace Utilities

Unified package for workspace utility scripts including repository analysis, project comparison, entity classification, and EUFLE verification.

## Features

- **Repository Analysis**: Static analysis of code repositories with dependency mapping
- **Project Comparison**: Cross-project comparison with pattern matching
- **Entity Classification**: Signal vs noise classification patterns
- **EUFLE Verification**: Setup verification for EUFLE projects
- **Cascade Integration**: JSON output format for Cascade parsing and automation
- **Centralized Configuration**: Shared configuration management across all utilities

## Installation

The package is located at `e:\shared\workspace_utils\`. Ensure `e:\` or `e:\shared` is in your Python path (e.g. PYTHONPATH or VS Code settings).

## Usage

### Command Line Interface

```bash
# Analyze a repository
workspace-utils analyze --root ./project --out ./analysis

# Compare two analyzed projects
workspace-utils compare --project1 ./grid_analysis --project2 ./eufle_analysis --out ./comparison

# Verify EUFLE setup
workspace-utils verify

# Manage configuration
workspace-utils config --show
workspace-utils config --get output_dir
workspace-utils config --set output_dir=./custom_output
```

### Python API

```python
from workspace_utils import RepositoryAnalyzer, ProjectComparator, EUFLEVerifier

# Repository analysis
analyzer = RepositoryAnalyzer(root_path="./project", output_dir="./analysis")
candidates = analyzer.analyze_repository()
analyzer.save_outputs(candidates)

# Project comparison
comparator = ProjectComparator(
    project1_analysis_dir="./grid_analysis",
    project2_analysis_dir="./eufle_analysis",
    output_dir="./comparison"
)
comparator.save_comparison_report()

# EUFLE verification
verifier = EUFLEVerifier()
result = verifier.run_all_checks()
```

## Configuration

Configuration is managed via `config.py` and can be customized through:

1. Environment variables
2. Configuration file: `workspace_utils_config.json`
3. CLI commands: `workspace-utils config`

## Cascade Integration

All utilities output JSON for Cascade parsing:

- Analysis results are saved as JSON
- Comparison reports use JSON format
- Verification results include structured JSON output
- Configuration supports Cascade terminal tracking

## Migration from Standalone Scripts

The following scripts have been migrated:

- `analyze_repo.py` → `workspace_utils.repo_analyzer`
- `compare_projects.py` → `workspace_utils.project_comparator`
- `code_local.py` → `workspace_utils.entity_classifier`
- `verify_eufle_setup.py` → `workspace_utils.eufle_verifier`

Original scripts are kept as backward-compatible wrappers.

## Testing

```bash
# From E:\ with PYTHONPATH=e:\shared
python -m pytest shared/workspace_utils/tests/

# Run specific test file
python -m pytest shared/workspace_utils/tests/test_repo_analyzer.py

# Run with coverage
python -m pytest shared/workspace_utils/tests/ --cov=workspace_utils --cov-report=html
```

Test coverage includes:
- Unit tests for individual modules
- Integration tests for CLI commands
- Mock tests for external dependencies
- Validation tests for JSON output format

## Known Issues

### OpenCode Integration

⚠️ **Current Status**: OpenCode has runtime/dependency issues

- OpenCode source cloned to `/mnt/c/Users/irfan/opencode`
- Requires Bun runtime (installed)
- Wrapper scripts created but OpenCode binary fails to run
- **Recommendation**: Use existing Claude/Claude Code integration for now
- **Alternative**: Direct API calls via Anthropic/OpenAI SDKs

See `docs/opencode_usage.md` for more details and alternatives.

## License

Internal workspace utilities package.
