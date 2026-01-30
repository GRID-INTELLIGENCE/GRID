# Quick Start: Databricks Database Setup

## 1. Install Dependencies

```bash
# Install pandas first (may take a few minutes)
pip install pandas

# Then install Databricks connector
pip install databricks-sql-connector
```

**If installation fails**, try:
```bash
pip install --only-binary :all: pandas databricks-sql-connector
```

## 2. Configure Environment

Create `.env` file in project root:

```bash
# Enable Databricks
USE_DATABRICKS=true

# Your Databricks details (get from workspace)
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id

# Authentication (choose one):
DATABRICKS_ACCESS_TOKEN=your-token-here
# OR
# DATABRICKS_PROFILE=DEFAULT
```

## 3. Test Connection

```bash
python scripts/test_databricks_connection.py
```

Expected output:
```
✓ Connection successful!
Your Databricks database is ready to use.
```

## 4. Verify Setup

```bash
# Run configuration tests
pytest tests/unit/test_databricks_config.py -v

# All 7 tests should pass
```

## 5. Use in Your Code

```python
from vinci_code.database.session import SessionLocal

# Automatically uses Databricks when configured
session = SessionLocal()
# ... your database operations ...
session.close()
```

## Need Help?

- **Full documentation**: `docs/databricks_setup.md`
- **Implementation details**: `DATABRICKS_INTEGRATION.md`
- **Configuration reference**: `.env.example`

## Where to Get Credentials

1. **Hostname**: Your Databricks workspace URL
2. **HTTP Path**: SQL Warehouses → Your Warehouse → Connection Details
3. **Token**: User Settings → Access Tokens → Generate New Token
