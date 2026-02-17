# Dotfiles Organization

**Purpose**: Centralized storage for all dotfiles and ignore files for easy reference and management.

## Structure

This directory contains organized copies of all dotfiles used in the GRID project. These files are organized here for:
- **Easy Reference**: Find and understand all ignore/configuration files in one place
- **Version Control**: Track changes to configuration files
- **Documentation**: Understand what each file does
- **Organization**: Keep root directory clean while maintaining tool compatibility

## Files Stored Here

### Ignore Files
- `.agentignore` - Excludes from AI agent context (prevents processing)
- `.cascadeignore` - Excludes from AI cascade context
- `.cursorignore` - Excludes from Cursor AI context
- `.gitignore` - Excludes from Git version control

### Configuration Files
- `.cursorrules` - Cursor IDE rules and project guidelines
- `.editorconfig` - Editor configuration for consistent formatting
- `.mypy.ini` - Type checking configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `.python-version` - Python version specification

## Root-Level Files (Required by Tools)

Some files **MUST remain at root** because tools require them there:
- `.gitignore` - Git requires at repository root
- `.cursorignore` - Cursor requires at workspace root
- `.agentignore` - Agent tools require at project root
- `.cursorrules` - Cursor requires at workspace root
- `.env` - Runtime environment (kept at root for convenience)

## Environment Files

Environment files are organized in `config/env/`:
- `.env.example` - Template (stays at root for visibility)
- `.env.development` → `config/env/.env.development`
- `.env.staging` → `config/env/.env.staging`
- `.env.production` → `config/env/.env.production`
- `.env.venv` → `config/env/.env.venv`

**Note**: The main `.env` file stays at root for local development convenience.

## File Categories

### Frequently Used (Stay at Root)
- `.gitignore` - Daily Git operations
- `.env` - Runtime configuration
- `.cursorrules` - IDE behavior

### Reference Only (Stored Here)
- `.agentignore` - Reference when configuring agents
- `.cascadeignore` - Reference when configuring cascade
- `.mypy.ini` - Reference when type checking
- `.pre-commit-config.yaml` - Reference when committing

### Environment-Specific (In `config/env/`)
- `.env.development` - Development environment
- `.env.staging` - Staging environment
- `.env.production` - Production environment
- `.env.venv` - Virtual environment configuration

## Syncing with Root

The files in this directory are **organized copies** for reference. The actual working files remain at root where tools require them.

When updating ignore files:
1. Update the root file (required by tool)
2. Update the copy here for reference
3. Keep them synchronized

## Benefits

✅ **Clean Root**: Only essential files visible at root
✅ **Easy Navigation**: Find all configs in one place
✅ **Clear Organization**: Logical grouping by purpose
✅ **Documentation**: Understand what each file does
✅ **Version Control**: Track configuration changes
✅ **Workspace Focus**: Start session with clean navigation
