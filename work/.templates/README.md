# Python Project Template

Standard structure for new Python projects using src layout.

## Directory Structure

```
project_name/
├── src/package_name/          # Main package code
│   ├── __init__.py
│   └── ...
├── tests/                     # Test files
│   ├── __init__.py
│   └── conftest.py
├── scripts/                   # Utility scripts
├── docs/                      # Documentation
│   ├── api/
│   └── user_guide/
├── examples/                  # Example code
│   ├── basic/
│   └── advanced/
├── .github/                   # GitHub templates & workflows
│   └── workflows/
├── pyproject.toml             # Project configuration
├── README.md                  # Project readme
├── LICENSE                    # License file
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guidelines
└── .gitignore                 # Git ignore rules
```

## Files

### pyproject.toml
Standard configuration using hatchling build system.

### .gitignore
Standard Python gitignore with common patterns.

### README.md
Template with sections for description, installation, usage, etc.
