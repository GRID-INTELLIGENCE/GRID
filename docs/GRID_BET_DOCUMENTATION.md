# GRID-BET: Comprehensive Technical Documentation

**Version**: 1.0.0
**Status**: Production / Exclusive
**Last Updated**: December 2025

---

## 1. Executive Summary

**GRID-BET** is an exclusive, proprietary financial intelligence module for the GRID system. It serves as an expert-level financial advisor, data analyst, and risk manager. Unlike standard open-source GRID components, GRID-BET is designed for high-stakes financial decision-making and is protected by strict access controls.

**Core Capabilities:**
- **Risk First**: Advanced multi-factor risk assessment (VaR, CVaR, Sharpe).
- **Decision Intelligence**: Evidence-based investment scoring and confidence modeling.
- **Simulation**: Monte Carlo and historical stress testing for portfolios.
- **Optimization**: Tax-loss harvesting and fee minimization strategies.
- **Market Scouting**: NER-driven entity extraction and strategic alliance detection.

---

## 2. Security & Licensing (Exclusive Module)

This module is **NOT** open source. It is protected by multiple layers of security to ensure exclusive access.

### 2.1 Access Guard (`access_guard.py`)
Runtime protection that enforces authorization before any `bet` module code can be executed.
- **Production Mode**: Requires a valid, cryptographically signed access token or a formal license file.
- **Development Mode**: Can be bypassed internally via `GRID_BET_DEV_MODE=1` (logs a warning).
- **Audit Logging**: All access attempts are logged to `~/.grid/logs/bet-access.log`.

### 2.2 Source Protection
- **Git Exclusion**: The entire `circuits/bet/` directory, tests, and fixtures are in `.gitignore`.
- **Pre-Commit Hook**: `scripts/hooks/pre-commit-bet-guard` prevents accidental commits of proprietary code to public repositories.
- **License**: Covered by `LICENSE_PROPRIETARY.md`.

---

## 3. Architecture & Modules

The system is composed of six interoperating services located in `circuits/bet/`:

### 3.1 Risk Engine (`risk.py`)
The foundation of the system.
- **Input**: Portfolio positions, historical returns.
- **Metrics**: Value at Risk (VaR 95/99), CVaR, Max Drawdown, Beta, Volatility, Sharpe/Sortino Ratios.
- **Logic**: Calculates concentration risk by sector/asset class and determines an overall `RiskLevel` (LOW to CRITICAL).

### 3.2 Financial Decision Engine (`decision.py`)
The "Brain" that recommends actions.
- **Input**: Investment opportunities, user constraints, market context.
- **Scoring**: Weighted evaluation of Risk/Reward, Expected Return, Catalyst Strength, and Constraint Fit.
- **Output**: `InvestmentDecision` (BUY/SELL/HOLD) with a confidence score (0.0-1.0) and detailed rationale.

### 3.3 Cost Optimizer (`optimizer.py`)
Focuses on efficiency.
- **Fee Analysis**: Identifies high-expense ratio funds.
- **Tax Optimization**: Scans for tax-loss harvesting candidates ($3k rule logic).
- **Rebalancing**: Projects costs for portfolio adjustments.

### 3.4 IO Simulator (`simulator.py`)
Stress-testing and future projection.
- **Modes**: Monte Carlo, Historical Replay, Stress Test (e.g., "2008 Crash").
- **Output**: Probability distributions of returns, worst-case scenarios.

### 3.5 Financial NER Service (`ner.py`)
Specialized Natural Language Processing.
- **Extraction**: Tickers ($AAPL), Amounts ($5B), Fiscal Dates (Q4 2025).
- **Logic**: Extends standard GRID NER to understand financial context and relationships.

### 3.6 Alliance Scout (`scout.py`)
Strategic intelligence.
- **Purpose**: Detects M&A targets, strategic partnerships, and competitive threats.
- **Logic**: Analyzes news and relationships to find synergy between entities.

---

## 4. CLI Reference

Access via `python -m grid bet [COMMAND]`. Requires authorization.

### `risk`
Assess portfolio risk metrics.
```bash
python -m grid bet risk --symbols AAPL,MSFT,JPM --horizon 30
python -m grid bet risk --portfolio portfolio.json --format json
```

### `evaluate`
Evaluate a specific investment opportunity.
```bash
python -m grid bet evaluate --symbol AMD --entry 95 --target 140 --stop 85
```

### `simulate`
Run simulations on a portfolio.
```bash
python -m grid bet simulate --scenario bear_market --iterations 1000
python -m grid bet simulate --scenario crash_2008 --portfolio my_holdings.json
```

### `optimize`
Find cost/tax optimizations.
```bash
python -m grid bet optimize --portfolio portfolio.json --objective minimize_taxes
```

### `ingest` / `extract` / `scout`
Data ingestion and intelligence gathering commands.

---

## 5. Python API Reference

### Risk Assessment
```python
from grid.bet.risk import RiskEngine, Position

positions = [Position("AAPL", 100, 150.0)]
engine = RiskEngine()
assessment = engine.assess(positions)
print(assessment.metrics.risk_level)
```

### Decision Making
```python
from grid.bet.decision import FinancialDecisionEngine, InvestmentOpportunity

opp = InvestmentOpportunity(symbol="TSLA", entry_price=200, target_price=250)
engine = FinancialDecisionEngine()
decision = engine.evaluate(opp)
if decision.recommendation == "BUY":
    print(f"Buy with {decision.confidence:.1%} confidence")
```

---

## 6. Data Models & Fixtures

Testing uses offline, realistic JSON fixtures located in `tests/fixtures/bet/`.

| Fixture | Description |
|---------|-------------|
| `portfolio_tech_growth.json` | A high-beta, tech-concentrated portfolio. |
| `market_scenario_bear.json` | Parameters defining a bearish market (high vol, negative drift). |
| `financial_news_sample.json` | Sample news articles for NER/Scout testing. |
| `historical_returns.json` | Synthetic daily return series for benchmarks. |

**Example Portfolio Structure:**
```json
{
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "current_price": 175.50,
      "cost_basis": 150.00,
      "sector": "Technology"
    }
  ]
}
```

---

## 7. Testing & Validation

### Running Tests
All tests are properly scoped and pass.
```bash
# Run full suite
python -m pytest tests/unit/test_bet_*.py

# Run specific module tests
python -m pytest tests/unit/test_bet_risk.py
```

### Benchmarks
Performance benchmarks are integrated into the main evaluation script.
```bash
python scripts/performance_evaluation.py --full
```
*Current benchmark*: ~0.33ms for a 30-position risk assessment.

---

## 8. Development Workflow

1.  **Activate Dev Mode**: `export GRID_BET_DEV_MODE=1`
2.  **Make Changes**: Edit files in `circuits/bet/`.
3.  **Run Tests**: Verify with `pytest`.
4.  **Commit**: **STOP.** Do not commit to public branches. Use internal repo or override hook if authorized (`GRID_BET_COMMIT_OVERRIDE=1`).

---
**Confidentiality Notice**: This documentation describes proprietary functionality. Do not distribute outside of authorized channels.
