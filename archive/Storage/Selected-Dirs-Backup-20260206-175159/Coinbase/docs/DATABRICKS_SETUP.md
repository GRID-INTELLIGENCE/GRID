# Databricks Integration - Setup and Usage Guide

## Overview

This guide provides comprehensive instructions for integrating Databricks into the Coinbase GRID agentic system, including setup instructions, configuration consolidation, and a tailored usage routine.

## Setup Instructions

### 1. Prerequisites

- Python 3.13 or higher
- Databricks workspace access
- Personal access token (PAT) from Databricks

### 2. Install Dependencies

```bash
# Install databricks SDK
uv sync --group databricks

# Or install manually
pip install databricks-sdk>=0.20.0
```

### 3. Environment Variables Configuration

Set the following environment variables (user-level or system-level):

```bash
# Required
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_personal_access_token

# Optional
DATABRICKS_CLUSTER_ID=your-cluster-id
DATABRICKS_WAREHOUSE_ID=your-warehouse-id
DATABRICKS_ACCOUNT_ID=your-account-id
```

**Windows PowerShell:**
```powershell
$env:DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
$env:DATABRICKS_TOKEN="your_personal_access_token"
$env:DATABRICKS_CLUSTER_ID="your-cluster-id"
$env:DATABRICKS_WAREHOUSE_ID="your-warehouse-id"
```

**Linux/Mac:**
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your_personal_access_token"
export DATABRICKS_CLUSTER_ID="your-cluster-id"
export DATABRICKS_WAREHOUSE_ID="your-warehouse-id"
```

### 4. Verify Installation

```bash
# Run basic usage example
uv run python examples/databricks_basic_usage.py

# Run tests
uv run pytest tests/test_databricks_config.py -v
```

## Configuration Consolidation

The Databricks integration uses a centralized configuration approach:

### Configuration Module (`coinbase/databricks_config.py`)

```python
from coinbase import DatabricksConfig, DatabricksClient

# Load from environment variables
config = DatabricksConfig.from_env()

# Validate configuration
if config.validate():
    print("Configuration is valid")
    
# Create client
client = DatabricksClient(config)
```

### Configuration Fields

| Field | Environment Variable | Required | Description |
|-------|---------------------|----------|-------------|
| host | DATABRICKS_HOST | Yes | Databricks workspace URL |
| token | DATABRICKS_TOKEN | Yes | Personal access token |
| cluster_id | DATABRICKS_CLUSTER_ID | No | Cluster ID for compute |
| warehouse_id | DATABRICKS_WAREHOUSE_ID | No | SQL warehouse ID |
| account_id | DATABRICKS_ACCOUNT_ID | No | Account ID |

## Tailored Usage Routine

### Basic Usage Pattern

```python
from coinbase import DatabricksClient

# Initialize client (loads from env vars)
client = DatabricksClient()

# Test connection
result = client.test_connection()
print(f"Status: {result['status']}")

# List clusters
clusters = client.list_clusters()
print(f"Found {len(clusters)} clusters")

# List warehouses
warehouses = client.list_warehouses()
print(f"Found {len(warehouses)} warehouses")

# Execute SQL query
result = client.run_sql_query("SELECT * FROM table")
```

### Advanced Usage Pattern

```python
from coinbase import DatabricksClient, AgenticSystem

# Create agentic system
system = AgenticSystem()

# Create Databricks client
client = DatabricksClient()

# Register Databricks handler
def databricks_handler(case_id, reference, agent_role):
    """Handler for Databricks operations."""
    # Execute analysis query
    result = client.run_sql_query(
        "SELECT * FROM crypto_data WHERE symbol = 'BTC'"
    )
    return result

system.register_handler("databricks_query", databricks_handler)

# Execute case
result = system.execute_case(
    case_id="crypto-analysis-001",
    task="databricks_query",
    agent_role="CryptoAnalyst"
)
```

## Testing Everything Implemented

### Test Suite

Run the comprehensive test suite:

```bash
# Run all Databricks tests
uv run pytest tests/test_databricks_config.py -v

# Run with coverage
uv run pytest tests/test_databricks_config.py --cov=coinbase.databricks_config
```

### Test Coverage

- Configuration loading from environment variables
- Configuration validation
- Client initialization
- Connection testing
- Cluster listing
- Warehouse listing
- SQL query execution

### Manual Testing

```bash
# Run basic usage example
uv run python examples/databricks_basic_usage.py
```

This will:
1. Load configuration from environment variables
2. Validate configuration
3. Create Databricks client
4. Test connection
5. List available clusters
6. List available warehouses

## Insights

### Key Insights

1. **Environment Variable Approach**: Using environment variables provides a secure and flexible configuration method that separates credentials from code.

2. **Lazy Loading**: The Databricks client uses lazy loading, only creating the SDK client when first accessed, improving startup performance.

3. **Validation First**: Configuration validation happens before client creation, preventing runtime errors.

4. **Modular Design**: The integration is modular and can be used independently or integrated with the GRID agentic system.

5. **Comprehensive Testing**: Full test coverage ensures reliability and prevents regressions.

### Integration Benefits

- **Security**: Credentials stored in environment variables, not in code
- **Flexibility**: Easy to switch between workspaces by changing env vars
- **Maintainability**: Centralized configuration management
- **Testability**: Mocked tests for CI/CD pipelines
- **Scalability**: Can be extended with additional Databricks features

### Best Practices

1. **Never hardcode credentials**: Always use environment variables
2. **Validate early**: Check configuration before attempting operations
3. **Handle errors gracefully**: Provide clear error messages
4. **Test thoroughly**: Use mocks for unit tests
5. **Document clearly**: Provide examples and usage patterns

## Concise Basic Usage Exercise

### Exercise: Query Crypto Data from Databricks

**Objective**: Create a simple script that queries cryptocurrency data from Databricks.

**Steps**:

1. Set environment variables:
   ```bash
   $env:DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
   $env:DATABRICKS_TOKEN="your_token"
   $env:DATABRICKS_WAREHOUSE_ID="your_warehouse_id"
   ```

2. Create script `query_crypto.py`:
   ```python
   from coinbase import DatabricksClient
   
   # Initialize client
   client = DatabricksClient()
   
   # Test connection
   result = client.test_connection()
   print(f"Connection status: {result['status']}")
   
   # Execute query
   query = """
   SELECT 
       symbol,
       price,
       volume,
       timestamp
   FROM crypto_prices 
   WHERE symbol = 'BTC'
   ORDER BY timestamp DESC
   LIMIT 10
   """
   
   data = client.run_sql_query(query)
   print(f"Query result: {data}")
   ```

3. Run the script:
   ```bash
   uv run python query_crypto.py
   ```

**Expected Output**:
```
Connection status: connected
Query result: {...}
```

## Troubleshooting

### Common Issues

**Issue**: `ImportError: databricks-sdk package not installed`

**Solution**: Install the SDK:
```bash
uv sync --group databricks
```

**Issue**: `ValueError: Invalid Databricks configuration`

**Solution**: Verify environment variables are set:
```bash
echo $DATABRICKS_HOST
echo $DATABRICKS_TOKEN
```

**Issue**: Connection timeout

**Solution**: Check network connectivity and workspace URL

## Next Steps

1. Integrate with GRID agentic system for automated crypto analysis
2. Add advanced features (Delta Lake, MLflow, etc.)
3. Implement real-time data streaming
4. Create custom visualizations
5. Deploy to production

## References

- [Databricks SDK for Python](https://docs.databricks.com/aws/en/dev-tools/sdk-python)
- [Databricks Authentication](https://docs.databricks.com/aws/en/dev-tools/auth/env-vars)
- [Databricks Connect](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/)

---

**Last Updated**: January 26, 2026
**Version**: 1.0
