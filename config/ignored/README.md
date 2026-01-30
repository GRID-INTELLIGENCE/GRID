# Ignored Directories Organization

**Purpose**: Centralized storage for dotfolders and ignored directories to keep root directory clean and simple.

## Structure

```
config/ignored/
├── dotfolders/          # IDE, cache, and temporary dotfolders
│   ├── case_memory/     # Case memory (from .case_memory)
│   ├── case_references/ # Case references (from .case_references)
│   ├── claude/          # Claude AI context (from .claude)
│   ├── context/         # Project context (from .context)
│   ├── cursor/          # Cursor IDE config (from .cursor)
│   ├── hypothesis/      # Hypothesis test cache (from .hypothesis)
│   ├── memos/           # Memos (from .memos)
│   ├── private/         # Private files (from .private)
│   ├── pytest_cache/    # Pytest cache (from .pytest_cache)
│   ├── rag_db/          # RAG database (from .rag_db)
│   ├── rag_logs/        # RAG logs (from .rag_logs)
│   ├── ruff_cache/      # Ruff cache (from .ruff_cache)
│   ├── tmp/             # Temporary files (from .tmp)
│   ├── vscode/          # VS Code config (from .vscode)
│   ├── welcome/         # Welcome docs (from .welcome)
│   ├── windsurf/        # Windsurf config (from .windsurf)
│   └── zed/             # Zed editor config (from .zed)
│
└── build-artifacts/     # Build output and artifacts
    ├── dist/            # Distribution packages
    └── build/           # Build artifacts
```

## What Gets Moved Here

### Dotfolders (IDE, Cache, Temporary)
These dotfolders are **moved** from root to `config/ignored/dotfolders/`:
- IDE configurations (`.cursor/`, `.vscode/`, `.windsurf/`, `.zed/`)
- Cache directories (`.pytest_cache/`, `.ruff_cache/`, `.hypothesis/`)
- Temporary directories (`.tmp/`, `.rag_db/`, `.rag_logs/`)
- AI context directories (`.claude/`, `.context/`, `.case_memory/`, `.case_references/`)
- Private directories (`.private/`, `.memos/`, `.welcome/`)

**Note**: When moved, the leading dot is removed (e.g., `.cursor/` → `cursor/`) for easier navigation.

### Build Artifacts
Build output and generated artifacts:
- `dist/` - Distribution packages (wheels, tarballs)
- `build/` - Build artifacts and intermediate files

## Essential Dotfolders (Stay at Root)

These dotfolders **MUST remain at root** because tools require them there:
- `.git/` - Git repository (required by Git)
- `.github/` - GitHub workflows and configs (required by GitHub Actions)
- `.venv/` - Active virtual environment (required for Python runtime)

**Note**: These are essential for tool operation and cannot be moved.

## Benefits

### Clean Root Directory
✅ **Fewer dotfolders**: Only 3 essential ones remain at root
✅ **Less clutter**: IDE and cache folders organized away
✅ **Faster navigation**: Find what you need quickly
✅ **Clear focus**: Focus on code, not configuration clutter

### Organized Storage
✅ **Centralized**: All ignored directories in one place
✅ **Categorized**: Organized by type (dotfolders vs build-artifacts)
✅ **Easy cleanup**: Remove all at once if needed
✅ **Version control**: Can be excluded from Git easily

### Tool Compatibility
✅ **Tools work**: Essential dotfolders remain where tools expect them
✅ **Cache isolated**: Cache and temporary files don't clutter root
✅ **IDE configs organized**: IDE settings available but not in way

## Usage

### Accessing Moved Directories

**IDE Configs:**
```bash
# Cursor config
ls config/ignored/dotfolders/cursor/

# VS Code config
ls config/ignored/dotfolders/vscode/
```

**Cache Directories:**
```bash
# Pytest cache
ls config/ignored/dotfolders/pytest_cache/

# Ruff cache
ls config/ignored/dotfolders/ruff_cache/
```

**Build Artifacts:**
```bash
# Distribution packages
ls config/ignored/build-artifacts/dist/

# Build artifacts
ls config/ignored/build-artifacts/build/
```

### Cleaning Up

**Remove all cache directories:**
```bash
rm -rf config/ignored/dotfolders/*_cache/
```

**Remove all build artifacts:**
```bash
rm -rf config/ignored/build-artifacts/*
```

**Remove all ignored directories:**
```bash
rm -rf config/ignored/*
```

## Maintenance

### Adding New Ignored Directories

When new dotfolders or ignored directories are created:
1. Identify if essential (must stay at root) or can be moved
2. If moveable, add to appropriate category in `scripts/organize_ignored.py`
3. Run `python scripts/organize_ignored.py` to move them

### Regenerating Cache/Artifacts

Cache and build artifacts can be regenerated:
- **Cache**: Tools will recreate when needed
- **Build artifacts**: Rebuilt with `make build` or `uv build`

## Git Configuration

To exclude `config/ignored/` from version control, add to `.gitignore`:

```gitignore
# Ignored directories (cache, artifacts, IDE configs)
config/ignored/
```

**Note**: Essential dotfolders (`.git/`, `.github/`, `.venv/`) are already handled by Git.

## Conclusion

This organization ensures:
- ✅ **Clean root**: Only essential dotfolders visible
- ✅ **Organized storage**: All ignored directories in one place
- ✅ **Easy navigation**: Find what you need quickly
- ✅ **Tool compatibility**: Tools still work as expected

When you start a work session, you see **only the essentials** at root, while everything else is **properly organized and easily accessible** when needed.
