# Databricks Setup - Python 3.14 Workaround

## ✅ Installation Successful!

We successfully installed `databricks-sql-connector` on Python 3.14 by bypassing the strict dependency checks.

### The Solution Used
```bash
pip install databricks-sql-connector --no-deps
```

This works because your environment already has a compatible (newer) version of pandas installed, even though the connector's metadata didn't explicitly allow it.

## 🚀 Next Steps

### 1. Configure Credentials
Open `.env` and fill in your real Databricks details:

```bash
USE_DATABRICKS=true
DATABRICKS_SERVER_HOSTNAME=adb-xxxxxxxx.xx.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/xxxxxxxx
DATABRICKS_ACCESS_TOKEN=dapi_xxxxxxxxxxxxxxxx
```

### 2. Verify Connection
Run the test script again:
```bash
python scripts/test_databricks_connection.py
```

### 3. Setup Dataset
Once connected, you can run the SQL setup script in Databricks (or via code) to create the GFashion tables:
- Script location: `scripts/setup_gfashion_databricks.sql`

## ⚠️ Note on Dependencies
Since we installed with `--no-deps`, some optional features might be missing dependencies (like `lz4` for compression or `oauthlib` for OAuth).
If you see `ImportError` in the future, install the missing package manually:
```bash
pip install lz4 oauthlib openpyxl
```
