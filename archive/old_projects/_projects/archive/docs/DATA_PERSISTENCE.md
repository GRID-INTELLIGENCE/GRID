# Data Persistence & Large File Management

## Overview
Echoes uses a file-based persistence model with Git LFS for efficient handling of large binary files. This document outlines the architecture and best practices for data management.

## File-Based Storage

### Data Directories
- `data/`: Root directory for all persistent data
  - `cache/`: Temporary cache files (excluded from Git)
  - `models/`: Local model weights and artifacts
  - `outputs/`: Generated outputs and exports
  - `sessions/`: User/agent session data

### Configuration
- Storage paths are configured via environment variables in `.env`
- Default paths are relative to the project root
- All data directories are created automatically if they don't exist

## Git LFS Configuration

### Tracked File Types
```
# .gitattributes
*.dll filter=lfs diff=lfs merge=lfs -text
*.exe filter=lfs diff=lfs merge=lfs -text
*.so filter=lfs diff=lfs merge=lfs -text
*.dylib filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
```

### Excluded Directories
```
# .gitignore
actions-runner/
OPENAI scaffolds/ffmpeg-*/
```

## Best Practices

### For Developers
1. **Large Files**: Always add new binary file types to `.gitattributes`
2. **Local Artifacts**: Keep local development artifacts out of version control
3. **Environment**: Use `.env` for local configuration overrides

### For CI/CD
1. **LFS**: Ensure Git LFS is installed in your CI environment
2. **Cache**: Configure appropriate caching for large model files
3. **Cleanup**: Remove temporary files after build/test phases

## Migration from Database Storage

### Changes from Previous Versions
- Removed PostgreSQL/Redis dependencies
- Simplified deployment with file-based storage
- Improved performance for read-heavy workloads

### Data Migration
If migrating from a previous version with database storage, use the provided migration scripts in `scripts/migrate/`.
