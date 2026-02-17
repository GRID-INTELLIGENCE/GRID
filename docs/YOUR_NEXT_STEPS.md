## Quick Reference: Your Environment Variables

Based on your screenshot, you have:
- ✅ `DATABRICKS_API_KEY` (will now be recognized as access token)

You still need to add:
- `USE_DATABRICKS=true`
- `DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com`
- `DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-id`

### Example PowerShell Commands:
```powershell
# Set in current session
$env:USE_DATABRICKS="true"
$env:DATABRICKS_SERVER_HOSTNAME="adb-xxxx.azuredatabricks.net"
$env:DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/xxxxx"

# Verify
python scripts/check_databricks_config.py
```

### Or add to Windows Environment Variables:
1. System Properties → Environment Variables
2. Add the three variables above
3. Restart terminal
4. Run: `python scripts/check_databricks_config.py`

**Note**: The config now accepts both `DATABRICKS_ACCESS_TOKEN` and `DATABRICKS_API_KEY` (you're using the latter).
