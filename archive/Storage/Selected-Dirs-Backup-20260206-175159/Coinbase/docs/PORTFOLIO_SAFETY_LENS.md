# Portfolio Safety Lens Feature

## Overview

**Portfolio Safety Lens** is a context-aware MCP (Model Context Protocol) server that provides secure portfolio analytics with full guardrails. It returns only sanitized portfolio insights and maintains a complete audit trail.

## Key Features

### 1. Sanitized Portfolio Summary
- Returns only aggregated metrics (total value, gain/loss percentages)
- No raw positions or quantities exposed
- User IDs are hashed and truncated
- Full audit logging for all access

### 2. Portfolio Risk Signals
- Risk level assessment (LOW/MEDIUM/HIGH)
- Concentration risk metrics
- Diversification scoring
- No raw position data exposed

### 3. Audit Log Tail
- Recent security events with hashed IDs only
- Truncated user identifiers
- No sensitive details exposed
- Full audit trail available internally

### 4. Governance Lint
- Policy compliance checks
- Guardrail validation
- Security control verification
- AI safety enforcement confirmation

## Security Architecture

### Multi-Layer Protection

```
┌─────────────────────────────────────────┐
│   Portfolio Safety Lens MCP Server      │
├─────────────────────────────────────────┤
│  1. PortfolioDataSecurity               │
│     - User ID hashing (SHA-256)         │
│     - AES-256 encryption                │
│     - Access control validation         │
├─────────────────────────────────────────┤
│  2. PortfolioAISafety                  │
│     - AI access approval                │
│     - Output sanitization               │
│     - Access logging                    │
├─────────────────────────────────────────┤
│  3. PortfolioDataPolicy                │
│     - Field-level sensitivity           │
│     - Purpose-based access control      │
│     - Output sanitization rules         │
├─────────────────────────────────────────┤
│  4. PortfolioAuditLogger               │
│     - Comprehensive event logging       │
│     - Metadata capture                  │
│     - Export functionality              │
└─────────────────────────────────────────┘
```

### Data Classification

| Data Type | Classification | Output Rules |
|-----------|----------------|--------------|
| User ID | CRITICAL | Hashed + Truncated |
| Quantity | CRITICAL | Aggregated only |
| Purchase Price | CRITICAL | Aggregated only |
| Symbol | PUBLIC | Raw allowed |
| Current Price | PUBLIC | Raw allowed |
| Sector | PUBLIC | Raw allowed |

## MCP Tools

### portfolio_summary_safe
Get sanitized portfolio metrics only.

**Input:**
```json
{
  "user_id": "string"
}
```

**Output:**
```json
{
  "total_positions": 5,
  "total_value": 50000.0,
  "total_gain_loss": 2500.0,
  "gain_loss_percentage": 5.0,
  "positions_count": 5,
  "timestamp": "2024-01-15T10:30:00"
}
```

### portfolio_risk_signal
Get portfolio risk scores and signals.

**Input:**
```json
{
  "user_id": "string"
}
```

**Output:**
```json
{
  "risk_level": "MEDIUM",
  "concentration_risk": {
    "top_position_percentage": 35.0,
    "top_3_percentage": 65.0
  },
  "diversification": {
    "total_positions": 5,
    "sectors": ["Technology", "Finance", "Healthcare"]
  },
  "recommendation": "Consider diversifying portfolio to reduce concentration risk",
  "timestamp": "2024-01-15T10:30:00"
}
```

### audit_log_tail
Get recent security events (hashed IDs only).

**Input:**
```json
{
  "limit": 10
}
```

**Output:**
```json
[
  {
    "timestamp": "2024-01-15T10:30:00",
    "event_type": "READ",
    "user_id_hash": "a1b2c3d4e5f6...",
    "action": "portfolio_summary_safe",
    "details_count": 2
  }
]
```

### governance_lint
Check portfolio data policy compliance.

**Input:**
```json
{
  "user_id": "string"
}
```

**Output:**
```json
{
  "user_id_hashed": true,
  "critical_data_protected": true,
  "audit_logging_enabled": true,
  "ai_safety_enforced": true,
  "output_sanitization": true,
  "policy_compliant": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

## Usage

### Running the MCP Server

```bash
# From GRID root
python mcp-setup/server/portfolio_safety_mcp_server.py
```

### Demo Script

```bash
# From Coinbase root
python examples/portfolio_safety_lens_demo.py
```

### Example Workflow

```python
from mcp.client import Client

# Connect to Portfolio Safety Lens
client = Client("portfolio-safety-lens")

# Get safe portfolio summary
summary = client.call_tool("portfolio_summary_safe", {"user_id": "user123"})
print(f"Portfolio Value: ${summary['total_value']:,.2f}")

# Get risk signals
risk = client.call_tool("portfolio_risk_signal", {"user_id": "user123"})
print(f"Risk Level: {risk['risk_level']}")

# View recent audit logs
logs = client.call_tool("audit_log_tail", {"limit": 10})
for log in logs:
    print(f"{log['timestamp']} - {log['action']}")

# Check governance compliance
compliance = client.call_tool("governance_lint", {"user_id": "user123"})
print(f"Policy Compliant: {compliance['policy_compliant']}")
```

## Integration with Coinbase

The Portfolio Safety Lens integrates with Coinbase's security modules:

```python
from coinbase.database.ai_safe_analyzer import get_ai_safe_analyzer

# Get AI-safe analyzer
analyzer = get_ai_safe_analyzer()

# Analyze portfolio with full guardrails
analysis = analyzer.analyze_portfolio("user123")

# Get risk signals
risk = analyzer.get_concentration_risk("user123")

# Get safe recommendations
recommendations = analyzer.get_safe_recommendations("user123")
```

## Audit Trail

All portfolio access is logged with full metadata:

```python
from coinbase.security.audit_logger import get_audit_logger

logger = get_audit_logger()

# Log access event
logger.log_event(
    event_type="READ",
    user_id="user123",
    action="get_positions",
    details={"symbol": "AAPL", "quantity": 100}
)

# Get recent logs
logs = logger.get_logs(limit=10)

# Export logs
export = logger.export_logs()
```

## Compliance

### Data Protection
- User IDs hashed with SHA-256
- AES-256 encryption for sensitive data
- No PII stored in database
- Output sanitization for all portfolio data

### Access Control
- Role-based access with principle of least privilege
- Purpose-based access validation
- AI access requires explicit approval
- All access logged with full metadata

### Audit Logging
- Comprehensive event logging
- Metadata capture for all operations
- Export functionality for compliance
- Retention policies configurable

### AI Safety
- AI can only access data with approval
- AI outputs must be sanitized
- AI cannot access user-identifiable data
- All AI interactions logged

## Testing

### Unit Tests
```bash
uv run pytest tests/test_portfolio_security_units.py -v
```

### Integration Tests
```bash
uv run pytest tests/test_portfolio_safety_mcp_integration.py -v
```

### Smoke Tests
```bash
uv run pytest tests/test_portfolio_safety_mcp_smoke.py -v
```

## Configuration

The Portfolio Safety Lens server is configured in `grid/mcp-setup/mcp_config.json`:

```json
{
  "name": "portfolio-safety-lens",
  "description": "Portfolio Safety Lens - Context-aware secure portfolio analytics with full guardrails",
  "enabled": true,
  "command": "python",
  "args": ["mcp-setup/server/portfolio_safety_mcp_server.py"],
  "cwd": "e:\\grid",
  "env": {
    "PYTHONPATH": "e:\\grid\\src;e:\\grid;e:\\Coinbase"
  },
  "port": 8005,
  "health_check": {
    "endpoint": "/health",
    "interval_seconds": 30,
    "timeout_seconds": 5
  }
}
```

## Benefits

1. **Security-First**: Full guardrails for portfolio data protection
2. **Privacy-First**: User IDs hashed, no PII stored
3. **Audit-First**: Complete audit trail for all access
4. **AI-Safe**: AI access controlled and outputs sanitized
5. **Compliance-Ready**: Meets regulatory requirements for financial data

## Future Enhancements

- Real-time portfolio monitoring alerts
- Advanced risk scoring models
- Portfolio rebalancing recommendations
- Integration with trading platforms
- Multi-user support with role-based access

## References

- Coinbase Context: `docs/COINBASE_CONTEXT.md`
- Databricks Integration: `grid/docs/DATABRICKS_INTEGRATION.md`
- AI Safety Framework: `grid/docs/AI safety.md`
- Agent Architecture: `grid/docs/AGENTIC_ARCHITECTURE.md`
