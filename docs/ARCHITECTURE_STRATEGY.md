# Architecture Strategy: Maximizing GRID with Databricks

## 1. The Strategic Shift
Moving to Databricks is not just a database swap; it is a shift to a **Lakehouse Architecture**. This enables GRID to handle massive scale while maintaining the agility of a Python application.

### Core Principles
1.  **Strict Separation**: The application (GRID) holds logic; the Lakehouse (Databricks) holds state.
2.  **Stateless Compute**: GRID nodes should be stateless, relying on the Lakehouse for all persistence.
3.  **Event-Driven**: Every state change in the business domain (e.g., `Order`) must emit a system `Event`.

## 2. Medallion Architecture in GRID

Adopt the "Bronze-Silver-Gold" pattern for data maturity:

| Layer | Concept | GRID Implementation |
|-------|---------|---------------------|
| **Bronze** | Raw Ingestion | `Events` table. Stores raw JSON payloads of every system action. Immutable. |
| **Silver** | Cleaned/Conformed | Domain Tables (`Products`, `Orders`). Structured, typed, and validated via SQLAlchemy models. |
| **Gold** | Aggregated Insights | Analytical Views. Pre-calculated metrics (e.g., `RevenueByCategory`) for dashboards. |

**Actionable Practice**:
- When designing a new feature, define the **Silver** schema first (SQLAlchemy Model).
- Ensure every write to Silver emits a corresponding **Bronze** record (Event).

## 3. Security & Trust Strategy

We have implemented a **"Zero-Trust, Fail-Fast"** security posture.

### The "Strict Mode" Protocol
- **Fail Fast**: The app crashes immediately if secrets are missing. Do not catch these errors; let the deployment fail.
- **No Defaults**: Never fallback to local SQLite in production. It creates "split-brain" data states.
- **Log Redaction**: Trust the `DatabricksConnector` to sanitize logs. Do not manually log tokens.

## 4. Optimization Checklist

Use this checklist to maintain system health:

- [ ] **Connection Pooling**: Rely on SQLAlchemy's pooling. Do not open/close sessions per request.
- [ ] **Lazy Loading**: Use `lazy="select"` (default) for relationships to avoid fetching massive graphs.
- [ ] **Batch Operations**: Use `session.add_all()` for bulk inserts (Ingestion phase).
- [ ] **Push-Down Queries**: Use `select(func.sum(...))` to let Databricks calculate aggregates. Never fetch all rows to Python to sum them.

## 5. Development Workflow

1.  **Simulate Locally**: Use `scripts/simulate_pipeline.py` to verify logic without incurring cloud costs.
2.  **Verify Config**: Use `scripts/check_databricks_config.py` before deploying.
3.  **Deploy & Monitor**: Watch the `Events` table for the heartbeat of the system.
