# Databricks Integration - Setup Guide

## Overview
GRID now supports Databricks SQL as the database backend, replacing SQLite for production deployments.

## What Was Implemented

### 1. Core Configuration (`vinci_code/core/config.py`)
- Extended `DatabaseSettings` with Databricks-specific fields:
  - `databricks_server_hostname`
  - `databricks_http_path`
  - `databricks_access_token`
  - `databricks_profile`
  - `use_databricks` (toggle flag)
- Added environment variable loading for all Databricks settings

### 2. Databricks Connector (`vinci_code/database/databricks_connector.py`)
- `DatabricksConnector` class for managing connections
- `create_databricks_engine()` - Creates SQLAlchemy engine
- `validate_databricks_connection()` - Tests connection health
- Support for both token-based and profile-based authentication
- Connection pooling and error handling

### 3. Session Management (`vinci_code/database/session.py`)
- Conditional database selection based on `use_databricks` flag
- Automatic fallback to SQLite if Databricks connection fails
- Maintains backward compatibility with existing code

### 4. Environment Configuration (`.env.example`)
- Complete Databricks configuration template
- Examples for both authentication methods
- Clear instructions for setup

### 5. Testing & Validation
- **Test Script**: `scripts/test_databricks_connection.py`
  - Validates configuration
  - Tests connection
  - Provides detailed status output

- **Unit Tests**: `tests/unit/test_databricks_config.py`
  - Configuration loading tests
  - Environment variable parsing tests
  - Boolean value handling tests

### 6. Documentation (`README.md`)
- Comprehensive setup instructions
- Authentication method comparison
- Credential acquisition guide
- Troubleshooting tips

## Installation Steps

### 1. Install Dependencies

**Note**: The `databricks-sql-connector` package requires pandas, which may have build issues on some systems. If you encounter errors:

```bash
# Option 1: Install pandas first (may require build tools)
pip install pandas
pip install databricks-sql-connector

# Option 2: Use pre-built wheels (recommended for Windows)
pip install --only-binary :all: pandas
pip install databricks-sql-connector

# Option 3: Install from requirements file
pip install -e .
```

### 2. Configure Environment Variables

Create or update your `.env` file:

```bash
# Enable Databricks
USE_DATABRICKS=true

# Connection details (get from Databricks workspace)
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id

# Choose authentication method:

# Method 1: Personal Access Token
DATABRICKS_ACCESS_TOKEN=YOUR_TOKEN_HERE

# Method 2: Profile-based (leave token empty)
# DATABRICKS_PROFILE=DEFAULT
```

### 3. Get Databricks Credentials

#### Server Hostname
- Go to your Databricks workspace
- Copy the URL (e.g., `adb-1234567890123456.7.azuredatabricks.net`)
- Remove `https://` prefix

#### HTTP Path
1. Navigate to **SQL Warehouses** in Databricks
2. Select your warehouse
3. Click **Connection Details** tab
4. Copy the **HTTP Path** (e.g., `/sql/1.0/warehouses/abc123def456`)

#### Access Token (if using token auth)
1. Click your profile icon → **User Settings**
2. Go to **Access Tokens** tab
3. Click **Generate New Token**
4. Copy the token (save it securely - it won't be shown again)

### 4. Test Connection

Run the test script to verify your setup:

```bash
python scripts/test_databricks_connection.py
```

Expected output:
```
╔══════════════════════════════════════════════════════════╗
║          DATABRICKS CONNECTION TEST SCRIPT              ║
╚══════════════════════════════════════════════════════════╝

DATABRICKS CONFIGURATION STATUS
============================================================
Use Databricks: True
Server Hostname: your-workspace.cloud.databricks.com
HTTP Path: /sql/1.0/warehouses/your-warehouse-id
Access Token: ***5678
Profile: DEFAULT
============================================================

TESTING DATABRICKS CONNECTION
------------------------------------------------------------
Attempting to connect to Databricks...
✓ Connection successful!
Your Databricks database is ready to use.
------------------------------------------------------------

✓ ALL CHECKS PASSED
Your GRID application is ready to use Databricks!
```

### 5. Run Unit Tests

```bash
# Test configuration loading
pytest tests/unit/test_databricks_config.py -v

# Run all tests
pytest tests/ -v
```

## Usage

Once configured, the application automatically uses Databricks:

```python
from vinci_code.database.session import SessionLocal
from vinci_code.database.models import Event

# Create a session (automatically uses Databricks if configured)
session = SessionLocal()

try:
    # Query data
    events = session.query(Event).limit(10).all()
    print(f"Retrieved {len(events)} events from Databricks")
finally:
    session.close()
```

## Troubleshooting

### Issue: "databricks-sql-connector installation failed"
**Solution**: Install pandas separately first:
```bash
pip install pandas
pip install databricks-sql-connector
```

### Issue: "Connection validation failed"
**Possible causes**:
1. Incorrect hostname or HTTP path
2. Invalid or expired access token
3. Network connectivity issues
4. Warehouse is stopped (start it in Databricks)

**Solution**:
- Verify credentials in Databricks workspace
- Check warehouse status
- Test network connectivity

### Issue: "Failed to create Databricks engine"
**Solution**: Check logs for detailed error. Common issues:
- Missing required environment variables
- Malformed connection string
- Authentication failure

### Issue: "Application falls back to SQLite"
**Cause**: Databricks connection failed, automatic fallback activated

**Solution**:
- Check `USE_DATABRICKS` is set to `true`
- Verify all required credentials are configured
- Run test script to diagnose issue

## Architecture Notes

### Backward Compatibility
- Existing code continues to work without changes
- SQLite remains available as fallback
- Session interface unchanged

### Connection Pooling
- Databricks manages connection pooling server-side
- Uses `NullPool` to avoid client-side pooling conflicts

### Error Handling
- Automatic fallback to SQLite on connection failure
- Detailed logging for debugging
- Graceful degradation

## Next Steps

1. **Create Tables**: Run Alembic migrations to create tables in Databricks
   ```bash
   alembic upgrade head
   ```

2. **Migrate Data**: If migrating from SQLite, export and import data

3. **Monitor Performance**: Use Databricks query history to monitor performance

4. **Optimize Queries**: Leverage Databricks-specific features (Delta Lake, caching)

## Additional Resources

- [Databricks SQL Connector Documentation](https://docs.databricks.com/dev-tools/python-sql-connector.html)
- [SQLAlchemy Databricks Dialect](https://github.com/databricks/databricks-sql-python)
- [Databricks Authentication Guide](https://docs.databricks.com/dev-tools/auth.html)
