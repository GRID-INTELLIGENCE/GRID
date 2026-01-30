# Environment Configuration Files

**Purpose**: Centralized storage for environment-specific configuration files.

## Organization

Environment files are organized here by **environment type** for easy management and deployment.

## Files

### Development
- `.env.development` - Development environment configuration

### Staging
- `.env.staging` - Staging environment configuration

### Production
- `.env.production` - Production environment configuration

### Docker
- `.env.docker` - Docker container environment configuration

### Virtual Environment
- `.env.venv` - Virtual environment specific configuration

## Usage

### Loading Environment Files

**Development:**
```bash
cp config/env/.env.development .env
# or
source config/env/.env.development
```

**Staging:**
```bash
cp config/env/.env.staging .env
```

**Production:**
```bash
cp config/env/.env.production .env
```

**Docker:**
```bash
# Docker Compose will use .env.docker automatically
docker-compose --env-file config/env/.env.docker up
```

## Root-Level Files

The following environment files remain at root for convenience:
- `.env` - Active runtime environment (local development)
- `.env.example` - Template file (visible for reference)

## Security

⚠️ **Important**:
- Environment files contain sensitive configuration
- Never commit `.env` files with secrets to version control
- Use `.env.example` as a template without secrets
- Use environment variables or secrets management in production

## Benefits

✅ **Organized**: All environment configs in one place
✅ **Clear**: Easy to identify environment-specific settings
✅ **Secure**: Centralized management of sensitive configs
✅ **Deployable**: Easy to select and deploy correct config
