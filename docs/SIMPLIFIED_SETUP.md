# GRID Simplified Development Setup

## Quick Start

**One command to set up your entire development environment:**

```bash
python scripts/setup.py --quick
```

That's it! Your local secrets manager is ready with encrypted storage.

---

## What This Does

The setup script automates the following:

1. **Checks prerequisites** (Python 3.10+, uv package manager)
2. **Creates local directories** (`~/.grid/secrets`, `~/.grid/cache`, `~/.grid/logs`)
3. **Initializes local secrets manager** with AES-256-GCM encryption
4. **Sets default secrets** (MOTHERSHIP_SECRET_KEY, MISTRAL_API_KEY, GRID_API_KEY)
5. **Generates environment configuration** (`.env` file)
6. **Validates the setup** (tests read/write operations)

---

## Usage

### Interactive Mode (recommended for first-time setup)
```bash
python scripts/setup.py
```

### Quick Setup (use defaults)
```bash
python scripts/setup.py --quick
```

### Migrate from Existing .env
```bash
python scripts/setup.py --migrate
```

### Production Setup
```bash
python scripts/setup.py --env production
```

---

## Managing Secrets

### Set a Secret
```bash
python -m grid.secrets set MY_API_KEY "my-secret-value"
```

### Get a Secret
```bash
python -m grid.secrets get MY_API_KEY
```

### List All Secrets
```bash
python -m grid.secrets list
```

### Delete a Secret
```bash
python -m grid.secrets delete MY_API_KEY
```

### Programmatic Usage
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))
from grid.security import get_local_secrets_manager

# Get secrets manager
manager = get_local_secrets_manager()

# Set a secret
manager.set("MY_API_KEY", "my-secret-value")

# Get a secret
api_key = manager.get("MY_API_KEY")
```

---

## Security Features

### Local Encryption
- **Algorithm:** AES-256-GCM (authenticated encryption)
- **Key Derivation:** PBKDF2 with 100,000 iterations
- **Master Key:** Stored in `~/.grid/.master.key` with restricted permissions (600)

### Storage
- **Location:** `~/.grid/secrets/secrets.db`
- **Format:** SQLite with WAL mode for performance
- **Isolation:** Each secret encrypted individually

### Secrets Location
```
~/.grid/
├── .master.key          # Master encryption key (DO NOT SHARE)
├── secrets/
│   └── secrets.db       # Encrypted secrets database
├── cache/               # Application cache
└── logs/                # Application logs
```

---

## Environment Variables

The setup generates a `.env` file with sensible defaults:

```bash
# GRID Environment Configuration
GRID_ENVIRONMENT=development

# For production, you can switch to GCP Secret Manager:
# GRID_SECRETS_PROVIDER=gcp
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## Validation

### Run Security Validation
```bash
python scripts/validate_security.py
```

### Quick Validation
```bash
python scripts/validate_security.py --quick
```

### Generate Report
```bash
python scripts/validate_security.py --report
```

The validation checks:
- ✅ Secrets database exists and works
- ✅ Encryption/decryption operations succeed
- ✅ No hardcoded secrets in code
- ✅ Required dependencies installed
- ✅ .gitignore has secrets patterns

---

## Migration from .env

If you have secrets in a `.env` file, migrate them to the local secrets manager:

```bash
# Backup your .env first
cp .env .env.backup

# Run migration
python scripts/setup.py --migrate
```

This will:
1. Parse your `.env` file
2. Extract API keys, passwords, and secrets
3. Store them in the encrypted local database
4. Backup your `.env` file

---

## Production Deployment

For production, you have two options:

### Option 1: Use Local Secrets Manager
```bash
python scripts/setup.py --env production
```

### Option 2: Use GCP Secret Manager
```bash
# Set environment variables
export GRID_SECRETS_PROVIDER=gcp
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Migrate secrets to GCP
python scripts/migrate_to_gcp.py
```

---

## Troubleshooting

### "Secrets database not found"
Run the setup script:
```bash
python scripts/setup.py --quick
```

### "Permission denied" on master key
The master key file has restricted permissions. Ensure you're the owner:
```bash
ls -la ~/.grid/.master.key
```

### "Module not found" error
Ensure you're in the project directory:
```bash
cd /path/to/grid
```

### Reset Everything
To start fresh:
```bash
# Remove local secrets
rm -rf ~/.grid/secrets ~/.grid/.master.key

# Re-run setup
python scripts/setup.py --quick
```

---

## Architecture

```
Local Secrets Manager
├── Encryption Layer (AES-256-GCM)
│   ├── Master Key (~/.grid/.master.key)
│   ├── PBKDF2 Key Derivation
│   └── Per-secret salt + nonce
├── Storage Layer (SQLite)
│   ├── WAL mode for performance
│   ├── Encrypted values
│   └── Metadata
└── Interface Layer
    ├── CLI (grid.security.local_secrets_manager)
    ├── Python API (get_secret, set_secret)
    └── Optional GCP sync
```

---

## Security Best Practices

1. **Never commit `.env` files** - They're automatically ignored by `.gitignore`
2. **Never share your master key** - `~/.grid/.master.key` is local to your machine
3. **Use unique secrets per environment** - Don't use the same API key in dev and prod
4. **Rotate secrets periodically** - Use the CLI to delete and re-add secrets
5. **Back up your secrets** - Export with `list` and `get` commands before system changes

---

## Comparison

| Feature | Before (30+ steps) | After (1 command) |
|---------|-------------------|-------------------|
| Setup time | 30+ minutes | 30 seconds |
| Commands needed | 30+ | 1 |
| GCP required | Yes | Optional |
| Offline capable | No | Yes |
| Encryption | Manual setup | Automatic |
| Validation | Manual | Automated |

---

## Next Steps

After running `python scripts/setup.py --quick`:

1. **Update your API keys:**
   ```bash
   python -m grid.secrets set MISTRAL_API_KEY "your-actual-api-key"
   ```

2. **Start developing:**
   ```bash
   python -m src.grid
   ```

3. **Validate your setup:**
   ```bash
   python scripts/validate_security.py
   ```

---

**Questions?** See `docs/SECURITY.md` or run `python scripts/validate_security.py --help`
