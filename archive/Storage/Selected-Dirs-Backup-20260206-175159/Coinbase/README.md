# Coinbase Crypto Investment Platform

[![CI/CD Pipeline](https://github.com/your-org/coinbase/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/coinbase/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-org/coinbase/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/coinbase)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![MyPy](https://img.shields.io/badge/mypy-clean-success.svg)](https://mypy-lang.org/)

**Privacy-First, Security-First, Revenue-Focused**

Minimal dependencies, maximum value. Built on GRID patterns for cryptocurrency/investment tracking. **MyPy clean codebase** with comprehensive type annotations.

## Principles

- **Privacy-First**: No PII, encrypted identifiers (SHA-256 hashing)
- **Security-First**: Parameterized queries, SQL injection prevention
- **Cost-Effective**: Minimal dependencies, only revenue-generating features
- **Business-Aligned**: Crypto/investment/stocks revenue generation

## Architecture

```
coinbase/
├── database/
│   └── crypto_db.py          # Databricks-backed database layer
├── features/
│   ├── revenue.py            # Revenue-generating features
│   └── fact_check.py         # Online source verification
└── app.py                    # Main application entry point
```

## Database Schema

**Minimal, Revenue-Focused Tables:**

1. `crypto_assets` - Market data (price, volume, market cap)
2. `price_history` - Historical price data for analysis
3. `portfolio_positions` - User portfolios (hashed IDs)
4. `transactions` - Audit trail
5. `sentiment_analysis` - Trading signals

## Features

### 1. Portfolio Analysis
- Total value and PnL calculation
- Risk assessment (LOW/MEDIUM/HIGH/EXTREME)
- Diversification scoring
- Performance recommendations

### 2. Trading Signals
- Sentiment-based signals (STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL)
- Price momentum analysis
- Target price and stop-loss recommendations
- Confidence scoring

### 3. Fact-Checking
- Multi-source price verification (CoinGecko, Binance, Coinbase)
- Anomaly detection (price spikes, volume anomalies)
- Cross-reference with news (placeholder for API integration)

### 4. Revenue Tracking
- Transaction logging
- Revenue calculation over time periods
- Daily revenue rate tracking

## Setup

```bash
# Create virtual environment
uv venv --python 3.13

# Activate (Windows)
.venv\Scripts\Activate.ps1

# Install dependencies
uv sync --group dev --group test
```

## Environment Variables

```bash
export DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your_warehouse_id"
export DATABRICKS_TOKEN="your_token"
```

## Usage

### Initialize Application

```python
from coinbase.app import create_app

# Create app from environment variables
app = create_app()
```

### Add Crypto Asset

```python
app.add_crypto_asset(
    symbol="BTC",
    name="Bitcoin",
    asset_type="bitcoin",
    current_price=50000.0,
    market_cap=1000000000000.0,
    volume_24h=30000000000.0,
)
```

### Add Portfolio Position

```python
app.add_portfolio_position(
    user_id="user123",
    asset_symbol="BTC",
    quantity=0.5,
    average_cost=45000.0,
)
```

### Analyze Portfolio

```python
analysis = app.analyze_portfolio("user123")

print(f"Portfolio Value: ${analysis['total_value']:,.2f}")
print(f"PnL: {analysis['pnl_percentage']:.2f}%")
print(f"Risk Level: {analysis['risk_level']}")
print(f"Diversification: {analysis['diversification_score']:.1f}%")

print("\nRecommendations:")
for rec in analysis['recommendations']:
    print(f"  - {rec}")
```

### Get Trading Signal

```python
signal = app.get_trading_signal("BTC")

print(f"Trading Signal: {signal.signal.value}")
print(f"Confidence: {signal.confidence:.2f}")
print(f"Reasoning: {signal.reasoning}")

if signal.target_price:
    print(f"Target Price: ${signal.target_price:,.2f}")
if signal.stop_loss:
    print(f"Stop Loss: ${signal.stop_loss:,.2f}")
```

### Verify Price

```python
verification = app.verify_price("BTC", 50000.0, tolerance=0.05)

print(f"Price Verified: {verification['verified']}")
print(f"Consensus Price: ${verification['consensus_price']:,.2f}")
print(f"Sources: {verification['sources_checked']}/{verification['sources_verified']}")

if verification['anomalies']:
    print("\nAnomalies:")
    for anomaly in verification['anomalies']:
        print(f"  - {anomaly}")
```

### Calculate Revenue

```python
revenue = app.calculate_revenue("user123", days=30)

print(f"Revenue (30 days): ${revenue['revenue']:,.2f}")
print(f"Daily Rate: ${revenue['revenue_rate']:,.2f}/day")
```

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ -v --cov=coinbase --cov-report=term-missing

# Run benchmarks
python -m tests.benchmarks.benchmark_runner

# Run benchmarks with JSON output
python -m tests.benchmarks.benchmark_runner --output json --save benchmark_results.json

# Lint
uv run ruff check .

# Format
uv run black .

# Type check
uv run mypy .

# Run example
python coinbase/app.py
```

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Lint**: Code quality checks with Ruff, Black, and MyPy
- **Test**: Runs test suite on Ubuntu, Windows, and macOS
- **Security**: Bandit security linter, Safety, and pip-audit
- **Benchmark**: Performance benchmarks on main branch pushes
- **Build**: Package building and validation

### New Features

#### Custom Exception Hierarchy
Comprehensive exception system with error codes and context tracking:

```python
from coinbase.exceptions import (
    CoinbaseError,
    ValidationError,
    RateLimitError,
    SkillExecutionError,
)

# Exceptions include error codes, severity, and context
try:
    # ... operation
except RateLimitError as e:
    print(f"Rate limited: retry after {e.retry_after}s")
    print(f"Error code: {e.code.name}")  # RATE_LIMITED
```

#### Structured Logging
JSON-formatted logging with correlation IDs and sensitive data masking:

```python
from coinbase.logging_config import setup_logging, get_logger, LogContext

# Setup at application start
setup_logging(level="INFO", json_output=True)

logger = get_logger(__name__)

# Use correlation IDs for request tracking
with LogContext(correlation_id="request-123"):
    logger.info("Processing request", extra={"user_id": "hashed_id"})
```

#### Performance Benchmarks
Run benchmarks to measure and track performance:

```bash
# Run all benchmarks
python -m tests.benchmarks.benchmark_runner

# Compare against baseline
python -m tests.benchmarks.benchmark_runner --baseline baseline.json

# Fail CI if regression detected
python -m tests.benchmarks.benchmark_runner --fail-on-regression
```

## Security & Privacy

### Portfolio Data Classification
**Portfolio data is CRITICAL and treated as personal sensitive information.**

| Data Type | Classification | Access Requirements |
|-----------|----------------|---------------------|
| Portfolio Positions | CRITICAL | Encrypted, hashed user IDs, audit logging required |
| Transaction History | CRITICAL | Encrypted, audit logging required |
| Market Data | PUBLIC | No restrictions |
| User Preferences | SENSITIVE | Access control required |
| Analytics Results | RESTRICTED | Sanitized output only |

### Security Guardrails

#### 1. PortfolioDataSecurity
- User ID hashing (SHA-256) for privacy
- Data encryption/decryption with AES-256
- Access control validation with security levels
- Security context creation and management
- Data sanitization for output

#### 2. PortfolioAISafety
- AI safety levels: PERMITTED, RESTRICTED, PROHIBITED
- Data sensitivity: PUBLIC, SENSITIVE, CRITICAL
- AI access validation based on purpose and approval
- Output sanitization for AI responses
- Access logging for all AI interactions

#### 3. PortfolioAuditLogger
- Audit event types: READ, WRITE, DELETE, EXPORT, AI_ACCESS
- Comprehensive logging with metadata
- File-based and in-memory storage
- Audit log export functionality
- Singleton instance management

#### 4. PortfolioDataPolicy
- Field-level sensitivity classification
- Purpose-based access control
- Output sanitization rules
- Policy compliance validation

### Databricks Guardrails

#### Unity Catalog Integration
- **Managed Tables**: All portfolio data stored as Delta Lake managed tables
- **Naming Constraints**: Lowercase, no spaces, no dots in table/column names
- **Access Modes**: Standard or dedicated access mode for compute
- **Runtime Version**: 11.3 LTS or higher required
- **Audit Logging**: Full audit trail for all data access and modifications

#### Data Quality Checks
- Portfolio position consistency validation
- Quantity and price range checks
- Timestamp validation
- Referential integrity checks

### Privacy-First Design
- User IDs hashed with SHA-256 before storage
- No PII stored in database
- Encrypted identifiers for all user data
- Output sanitization for all portfolio data

### Security-First Architecture
- Parameterized queries throughout (SQL injection prevention)
- Connection timeout enforcement
- Query validation and sanitization
- No raw SQL execution
- Access control validation on all operations
- Comprehensive audit logging

### AI Safety Controls
- AI can only access portfolio data with explicit approval
- AI outputs must be sanitized before display
- AI cannot access user-identifiable data
- AI cannot recommend specific buy/sell actions without approval
- All AI interactions must be logged

### Scope Boundaries

**Allowed for Analytics:**
- Aggregated portfolio metrics (total value, gain/loss percentages)
- Risk scores and concentration metrics
- Sector allocation summaries
- Top/worst performer rankings (symbol only, no quantities)
- Trading signals and recommendations

**Not Allowed for Output:**
- Raw portfolio positions with quantities
- User-identifiable information
- Transaction history details
- Specific purchase prices
- Personal comments or notes
- Unsanitized AI outputs

## Dependencies

**Minimal, Revenue-Focused:**

- `databricks-sdk` - Database backend (reused from GRID)
- `requests` - HTTP client for fact-checking

**No unnecessary dependencies.** Every dependency returns measurable value.

## Cost-Effective

- Uses existing Databricks infrastructure (no new cloud costs)
- Minimal schema (only revenue-generating tables)
- No experimental/unused features
- Focused on ROI

## Business Alignment

All features designed for revenue generation:
- Portfolio optimization → Better returns
- Trading signals → Informed decisions
- Fact-checking → Risk reduction
- Revenue tracking → Performance measurement

## Example Output

```
Portfolio Value: $25,000.00
PnL: 10.00%
Risk Level: medium
Diversification: 60.0%

Recommendations:
  - Strong performance: Consider taking profits on high-gain positions
  - Moderate risk: Monitor portfolio volatility

Trading Signal: BUY
Confidence: 0.70
Reasoning: Positive sentiment (0.45) and upward trend (2.50%)
Target Price: $52,500.00
Stop Loss: $47,500.00

Price Verified: True
Consensus Price: $50,100.00
Sources: 3/3

Revenue (30 days): $25,000.00
Daily Rate: $833.33/day
```

## Production Checklist

- [x] Set DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN
- [x] Configure rate limiting for external APIs
- [x] Set up monitoring and alerting
- [x] Implement backup strategy
- [x] Configure audit logging
- [x] Set up security policies
- [x] Implement user authentication (if needed)
- [x] Configure webhooks for real-time updates

## Project Structure

```
coinbase/
├── __init__.py
├── app.py                    # Main application entry point
├── cli.py                    # Command-line interface
├── exceptions.py             # Custom exception hierarchy
├── logging_config.py         # Structured logging configuration
├── error_recovery.py         # Error recovery with retry logic + circuit breaker
├── skills.py                 # Crypto analysis skills (8 real implementations)
├── agentic_system.py         # GRID agentic system
├── version_scoring.py        # Optimized version scoring
├── tracer.py                 # Runtime behavior tracing
├── events.py                 # Event bus
├── skill_generator.py        # Automatic skill generation
├── learning_coordinator.py   # Learning coordination
├── agent_executor.py         # Agent execution
├── cognitive_engine.py       # Cognitive state tracking
├── database/
│   └── crypto_db.py          # Databricks-backed database layer
├── features/
│   ├── revenue.py            # Revenue-generating features
│   └── fact_check.py         # Online source verification
├── core/                     # Core components
│   ├── attention_allocator.py
│   ├── skill_cache.py        # Skill caching
│   ├── backup_manager.py     # Backup and recovery
│   ├── auth.py               # JWT authentication
│   └── webhook_manager.py    # Real-time webhooks
├── security/                 # Security guardrails
├── integrations/             # External integrations
│   ├── yahoo_finance.py
│   └── coinbase_api.py       # Coinbase API client
└── skills/                   # Crypto analysis skills

tests/
├── benchmarks/               # Performance benchmarks
│   ├── benchmark_runner.py
│   ├── bench_crypto_skills.py
│   └── conftest.py
├── test_integration_workflows.py  # End-to-end integration tests
└── test_*.py                 # Unit tests

.github/
└── workflows/
    ├── ci.yml                # CI/CD pipeline
    ├── release.yml           # Release automation
    └── dependabot.yml        # Dependency updates
```

## License

Proprietary - Revenue-generating business application
