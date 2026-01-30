# Databricks Credential Configuration Guide

## Overview
This guide helps you configure real Databricks credentials **securely** via environment variables. **No secrets will be hardcoded.**

## Step 1: Obtain Your Databricks Credentials

You need three pieces of information from your Databricks workspace:

1. **Server Hostname**: Find in Databricks → SQL Warehouses → Connection Details
   - Example: `adb-1234567890123456.7.azuredatabricks.net`

2. **HTTP Path**: Same location as hostname
   - Example: `/sql/1.0/warehouses/abc123def456`

3. **Access Token**: User Settings → Developer → Access Tokens → Generate New Token
   - Example: `dapi1234567890abcdef1234567890ab` (replace with your token)

## Step 2: Set Environment Variables

### Option A: Using `.env` File (Recommended)

Create or update `e:\grid\.env`:

```env
USE_DATABRICKS=true
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_ACCESS_TOKEN=dapi_your_actual_token_here
```

**Security**: The `.env` file is already in `.gitignore` - it will NOT be committed to version control.

### Option B: Using PowerShell (Current Session Only)

```powershell
$env:USE_DATABRICKS="true"
$env:DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
$env:DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
$env:DATABRICKS_ACCESS_TOKEN="dapi_your_actual_token_here"
```

**Note**: These variables only persist for the current terminal session.

### Option C: Using Windows System Environment Variables (Permanent)

1. Open System Properties → Advanced → Environment Variables
2. Add User Variables:
   - `USE_DATABRICKS` = `true`
   - `DATABRICKS_SERVER_HOSTNAME` = your workspace URL
   - `DATABRICKS_HTTP_PATH` = your warehouse path
   - `DATABRICKS_ACCESS_TOKEN` = your token

3. **Restart your terminal** for changes to take effect

## Step 3: Verify Configuration

Run the configuration check:

```bash
python scripts/check_databricks_config.py
```

Expected output:
```
✅ SUCCESS: All required credentials are set
✅ STRICT MODE: Credentials validated
```

## Step 4: Test Connection

Run the health check:

```bash
python -c "from vinci_code.database.health import detailed_health_check; import json; print(json.dumps(detailed_health_check(), indent=2))"
```

Expected output:
```json
{
  "status": "healthy",
  "latency_ms": 234.56,
  ...
}
```

## Step 5: Initialize Database

Create tables in Databricks:

```bash
python scripts/migrate_to_databricks.py --create
```

## Security Notes

✅ **Safe Practices** (What we're doing):
- Loading credentials from environment variables
- Using `.env` file (ignored by git)
- Validating at startup (Strict Mode)
- Redacting tokens from logs

❌ **Prohibited** (What we avoid):
- Hardcoding credentials in `.py` files
- Committing `.env` to git
- Logging credentials
- Using default/placeholder values in production

## Troubleshooting

### "Credentials not found"
- **Cause**: Environment variables not set
- **Fix**: Use Option A, B, or C above

### "Cannot connect to Databricks"
- **Cause**: Invalid credentials or network issue
- **Fix**: Verify credentials in Databricks console

### "Strict mode validation failed"
- **Cause**: Using placeholder values
- **Fix**: Replace with real credentials

## Next Steps

Once credentials are configured and verified:

1. Create tables: `python scripts/migrate_to_databricks.py --create`
2. Run the demo: `python demos/dataset_lifecycle.py`
3. Deploy your application

**All credentials are managed systematically through environment variables - never hardcoded.**
