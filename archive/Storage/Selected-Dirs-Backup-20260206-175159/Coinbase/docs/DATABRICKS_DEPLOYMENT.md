# Databricks Deployment Guide
# ===========================
# Complete deployment instructions for Coinbase Portfolio Safety Lens on Databricks

## Prerequisites

### Databricks Account
- Databricks workspace (Standard or Premium)
- SQL Warehouse (Standard or Dedicated)
- Runtime 11.3 LTS or higher
- Unity Catalog enabled

### Local Setup
```bash
# Install dependencies
uv venv --python 3.13
.venv\Scripts\Activate.ps1
uv sync --group dev --group test
```

### Environment Variables
```bash
export DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your_warehouse_id"
export DATABRICKS_TOKEN="your_personal_access_token"
```

## Database Artifacts Created

### 1. Managed Delta Tables

#### portfolio_positions
```sql
CREATE TABLE IF NOT EXISTS portfolio_positions (
    user_id_hash STRING,
    symbol STRING,
    asset_name STRING,
    sector STRING,
    quantity DECIMAL(18, 8),
    purchase_price DECIMAL(18, 8),
    current_price DECIMAL(18, 8),
    purchase_value DECIMAL(18, 8),
    current_value DECIMAL(18, 8),
    total_gain_loss DECIMAL(18, 8),
    gain_loss_percentage DECIMAL(10, 4),
    purchase_date STRING,
    commission DECIMAL(18, 8),
    high_limit DECIMAL(18, 8),
    low_limit DECIMAL(18, 8),
    comment STRING,
    transaction_type STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY (user_id_hash, symbol)
)
```

**Purpose**: Stores portfolio positions with hashed user IDs
**Features**: ACID transactions, Time Travel (7 days), Auto-optimize

#### price_history
```sql
CREATE TABLE IF NOT EXISTS price_history (
    symbol STRING,
    price DECIMAL(18, 8),
    volume BIGINT,
    open_price DECIMAL(18, 8),
    high_price DECIMAL(18, 8),
    low_price DECIMAL(18, 8),
    change_amount DECIMAL(18, 8),
    change_percentage DECIMAL(10, 4),
    timestamp TIMESTAMP,
    source STRING,
    PRIMARY KEY (symbol, timestamp)
)
```

**Purpose**: Historical price data for analytics
**Features**: Time series data, optimized for range queries

#### trading_signals
```sql
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id STRING,
    user_id_hash STRING,
    symbol STRING,
    direction STRING,
    confidence DECIMAL(10, 4),
    reasoning STRING,
    target_price DECIMAL(18, 8),
    stop_loss DECIMAL(18, 8),
    sentiment DECIMAL(10, 4),
    momentum DECIMAL(18, 8),
    current_price DECIMAL(18, 8),
    created_at TIMESTAMP,
    PRIMARY KEY (signal_id)
)
```

**Purpose**: AI-generated trading signals
**Features**: Sanitized AI outputs, audit logging

#### portfolio_events
```sql
CREATE TABLE IF NOT EXISTS portfolio_events (
    event_id STRING,
    user_id_hash STRING,
    symbol STRING,
    event_type STRING,
    quantity DECIMAL(18, 8),
    price DECIMAL(18, 8),
    purpose STRING,
    metadata STRING,
    created_at TIMESTAMP,
    PRIMARY KEY (event_id)
)
```

**Purpose**: Portfolio transaction events
**Features**: Full audit trail, metadata capture

#### portfolio_summary
```sql
CREATE TABLE IF NOT EXISTS portfolio_summary (
    user_id_hash STRING,
    total_positions INT,
    total_value DECIMAL(18, 8),
    total_purchase_value DECIMAL(18, 8),
    total_commission DECIMAL(18, 8),
    total_gain_loss DECIMAL(18, 8),
    gain_loss_percentage DECIMAL(10, 4),
    updated_at TIMESTAMP,
    PRIMARY KEY (user_id_hash)
)
```

**Purpose**: Aggregated portfolio metrics
**Features**: Pre-computed summaries for fast queries

#### audit_events
```sql
CREATE TABLE IF NOT EXISTS audit_events (
    event_id STRING,
    user_id_hash STRING,
    event_type STRING,
    action STRING,
    details STRING,
    source_ip STRING,
    user_agent STRING,
    created_at TIMESTAMP,
    PRIMARY KEY (event_id)
)
```

**Purpose**: Comprehensive audit logging
**Features**: All access logged, exportable for compliance

### 2. Unity Catalog Structure

```
coinbase (catalog)
└── portfolio (schema)
    ├── portfolio_positions (table)
    ├── price_history (table)
    ├── trading_signals (table)
    ├── portfolio_events (table)
    ├── portfolio_summary (table)
    └── audit_events (table)
```

**Naming Constraints**:
- Lowercase with underscores
- No spaces or dots
- Unity Catalog compliant

### 3. Views and Presets

#### Portfolio Summary View
```sql
CREATE OR REPLACE VIEW coinbase.portfolio.v_portfolio_summary AS
SELECT 
    user_id_hash,
    total_positions,
    total_value,
    total_gain_loss,
    gain_loss_percentage,
    updated_at
FROM coinbase.portfolio.portfolio_summary
WHERE total_value > 0;
```

#### Risk Analysis View
```sql
CREATE OR REPLACE VIEW coinbase.portfolio.v_risk_analysis AS
SELECT 
    user_id_hash,
    symbol,
    quantity,
    current_value,
    (quantity * current_price) / total_value as concentration_percentage
FROM coinbase.portfolio.portfolio_positions
WHERE current_value > 0;
```

## Deployment Steps

### Step 1: Initialize Database Schema

```python
from coinbase.database.databricks_persistence import DatabricksPortfolioPersistence

# Initialize persistence
persistence = DatabricksPortfolioPersistence()

# Create all tables
persistence.initialize_schema()

print("✅ Database schema initialized")
```

### Step 2: Load Portfolio Data

```python
import pandas as pd
from coinbase.database.databricks_persistence import DatabricksPortfolioPersistence

# Load CSV
df = pd.read_csv("portfolios/yahoo_portfolio.csv")

# Initialize persistence
persistence = DatabricksPortfolioPersistence()

# Hash user ID
user_id = "user123"
user_id_hash = persistence.security.hash_user_id(user_id)

# Load positions
for _, row in df.iterrows():
    position = PortfolioPosition(
        symbol=row['Symbol'],
        asset_name=row['Symbol'],  # Would need mapping
        sector="Technology",  # Would need mapping
        quantity=row['Quantity'],
        purchase_price=row['Purchase Price'],
        current_price=row['Current Price'],
        purchase_value=row['Quantity'] * row['Purchase Price'],
        current_value=row['Quantity'] * row['Current Price'],
        total_gain_loss=row['Quantity'] * (row['Current Price'] - row['Purchase Price']),
        gain_loss_percentage=((row['Current Price'] - row['Purchase Price']) / row['Purchase Price']) * 100,
        purchase_date=row['Trade Date'],
        commission=row['Commission'],
        high_limit=row.get('High Limit'),
        low_limit=row.get('Low Limit'),
        comment=row.get('Comment'),
        transaction_type=row.get('Transaction Type')
    )
    
    persistence.save_position(user_id, position)

print(f"✅ Loaded {len(df)} positions")
```

### Step 3: Start Portfolio Safety Lens MCP Server

```bash
# From GRID root
python mcp-setup/server/portfolio_safety_mcp_server.py
```

Server will start on port 8005 with health check at `/health`.

### Step 4: Test Portfolio Safety Lens

```python
from mcp.client import Client

# Connect to Portfolio Safety Lens
client = Client("portfolio-safety-lens")

# Get safe portfolio summary
summary = client.call_tool("portfolio_summary_safe", {"user_id": "user123"})
print(f"Portfolio Value: ${summary['total_value']:,.2f}")
print(f"Gain/Loss: {summary['gain_loss_percentage']:.2f}%")

# Get risk signals
risk = client.call_tool("portfolio_risk_signal", {"user_id": "user123"})
print(f"Risk Level: {risk['risk_level']}")

# View audit logs
logs = client.call_tool("audit_log_tail", {"limit": 5})
for log in logs:
    print(f"{log['timestamp']} - {log['action']}")

# Check governance compliance
compliance = client.call_tool("governance_lint", {"user_id": "user123"})
print(f"Policy Compliant: {compliance['policy_compliant']}")
```

### Step 5: Run Fast Verify

```python
from coinbase.verification.fast_verify import fast_verify_portfolio, fast_verify_summary

# Run verification
result = fast_verify_portfolio("user123")

# Get summary
summary = fast_verify_summary(result)

print(f"Success Rate: {summary['success_rate']:.1f}%")
print(f"Passed: {summary['passed']}")
print(f"Failed: {summary['failed']}")
print(f"Duration: {summary['duration_ms']:.2f}ms")
```

## Databricks Notebook Presets

### Preset 1: Portfolio Overview

```python
# Portfolio Overview Notebook
%sql

-- Get portfolio summary
SELECT 
    user_id_hash,
    total_positions,
    total_value,
    total_gain_loss,
    gain_loss_percentage,
    updated_at
FROM coinbase.portfolio.portfolio_summary
ORDER BY total_value DESC
LIMIT 10;
```

### Preset 2: Risk Analysis

```python
# Risk Analysis Notebook
%sql

-- Analyze concentration risk
WITH portfolio_concentration AS (
    SELECT 
        user_id_hash,
        symbol,
        current_value,
        SUM(current_value) OVER (PARTITION BY user_id_hash) as total_value,
        (current_value / SUM(current_value) OVER (PARTITION BY user_id_hash)) * 100 as concentration_pct
    FROM coinbase.portfolio.portfolio_positions
)
SELECT 
    user_id_hash,
    symbol,
    current_value,
    concentration_pct,
    CASE 
        WHEN concentration_pct > 50 THEN 'HIGH'
        WHEN concentration_pct > 25 THEN 'MEDIUM'
        ELSE 'LOW'
    END as risk_level
FROM portfolio_concentration
WHERE concentration_pct > 10
ORDER BY concentration_pct DESC;
```

### Preset 3: Audit Trail

```python
# Audit Trail Notebook
%sql

-- Recent audit events
SELECT 
    event_id,
    user_id_hash,
    event_type,
    action,
    created_at
FROM coinbase.portfolio.audit_events
ORDER BY created_at DESC
LIMIT 50;
```

## Monitoring and Maintenance

### Performance Monitoring

```python
# Monitor query performance
from coinbase.database.databricks_persistence import DatabricksPortfolioPersistence

persistence = DatabricksPortfolioPersistence()

# Check connection
if persistence.test_connection():
    print("✅ Database connection healthy")
else:
    print("❌ Database connection failed")
```

### Data Quality Checks

```python
# Run data quality checks
from coinbase.database.data_quality import get_data_quality_checker

checker = get_data_quality_checker()

# Check positions
positions = persistence.get_positions("user123")
result = checker.check_positions_batch(positions)

print(f"Total Positions: {result['total_positions']}")
print(f"Passed: {result['passed']}")
print(f"Failed: {result['failed']}")
print(f"Total Issues: {result['total_issues']}")
```

### Audit Log Export

```python
# Export audit logs for compliance
from coinbase.security.audit_logger import get_audit_logger

logger = get_audit_logger()

# Export to CSV
export = logger.export_logs()
export.to_csv("audit_export.csv")

print(f"✅ Exported {len(export)} audit events")
```

## Security Best Practices

### 1. Token Management
- Rotate PATs every 90 days
- Store tokens in environment variables
- Use secret management for production

### 2. Access Control
- Grant least privilege access
- Use Unity Catalog for fine-grained permissions
- Enable IP access lists

### 3. Data Encryption
- At rest: Managed by Databricks (AES-256)
- In transit: TLS 1.3
- Customer-managed keys available for enterprise

### 4. Audit Logging
- Enable audit logging for all access
- Monitor for suspicious activity
- Export logs regularly for compliance

## Troubleshooting

### Connection Issues
```python
# Test connection
import os
from databricks import sql

connection = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=os.getenv("DATABRICKS_HTTP_PATH"),
    access_token=os.getenv("DATABRICKS_TOKEN")
)

cursor = connection.cursor()
cursor.execute("SELECT 1")
print("✅ Connection successful")
```

### Schema Issues
```python
# Recreate schema if needed
from coinbase.database.databricks_schema import get_schema_ddl

ddl = get_schema_ddl()
print(ddl)
```

### Performance Issues
```python
# Optimize tables
cursor.execute("OPTIMIZE portfolio_positions ZORDER BY (symbol)")
cursor.execute("VACUUM portfolio_positions RETAIN 7 HOURS")
```

## Next Steps

1. **Test Deployment**: Run all tests with `uv run pytest tests/ -v`
2. **Load Sample Data**: Use `portfolios/yahoo_portfolio.csv`
3. **Start MCP Server**: Launch Portfolio Safety Lens
4. **Run Demo**: Execute `examples/portfolio_safety_lens_demo.py`
5. **Monitor**: Check Databricks cluster metrics
6. **Scale**: Add more workers for production

## References

- [Databricks SQL Connector](https://docs.databricks.com/en/sql/connect.html)
- [Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- [Delta Lake](https://docs.databricks.com/en/delta/index.html)
- [Portfolio Safety Lens](docs/PORTFOLIO_SAFETY_LENS.md)
- [Fast Verify](coinbase/verification/fast_verify.py)
