# Coinbase Context & Architecture

## Architecture Overview

The Coinbase platform is built on six fundamental components (Compass, Calendar, Dictionary, Scale, Watch, Vault) with a privacy-first, security-first design.

### Core Components

- **Compass**: Trading direction and signal generation
- **Calendar**: Time-based event tracking and scheduling
- **Dictionary**: Pattern recognition and market terminology
- **Scale**: Position sizing and risk management
- **Watch**: Real-time monitoring and alerts
- **Vault**: Secure storage and access control

### Platform Layers

1. **Data Layer**: Databricks Lakehouse with Unity Catalog governance
2. **Security Layer**: Encryption, access control, audit logging
3. **AI Safety Layer**: Privilege validation and output sanitization
4. **Integration Layer**: Yahoo Finance, MCP servers, external APIs
5. **Application Layer**: Portfolio analytics, trading signals, risk assessment

## Databricks Governance Model

### Unity Catalog Integration

- **Managed Tables**: All portfolio data stored as Delta Lake managed tables
- **Naming Constraints**: Lowercase, no spaces, no dots in table/column names
- **Access Modes**: Standard or dedicated access mode for compute
- **Runtime Version**: 11.3 LTS or higher required
- **Audit Logging**: Full audit trail for all data access and modifications

### Data Classification

| Data Type | Classification | Access Requirements |
|-----------|----------------|---------------------|
| Portfolio Positions | CRITICAL | Encrypted, hashed user IDs, audit logging required |
| Transaction History | CRITICAL | Encrypted, audit logging required |
| Market Data | PUBLIC | No restrictions |
| User Preferences | SENSITIVE | Access control required |
| Analytics Results | RESTRICTED | Sanitized output only |

### Security Controls

1. **Encryption**: AES-256 for data at rest, TLS 1.3 for data in transit
2. **Access Control**: Role-based access with principle of least privilege
3. **Audit Logging**: All access events logged with timestamp, user, action, and metadata
4. **Data Sanitization**: PII and sensitive values redacted before output
5. **AI Safety**: All AI-driven analytics require approval and output sanitization

## Safety Controls

### PortfolioDataSecurity

- User ID hashing (SHA-256) for privacy
- Data encryption/decryption with AES-256
- Access control validation with security levels
- Security context creation and management
- Data sanitization for output

### PortfolioAISafety

- AI safety levels: PERMITTED, RESTRICTED, PROHIBITED
- Data sensitivity: PUBLIC, SENSITIVE, CRITICAL
- AI access validation based on purpose and approval
- Output sanitization for AI responses
- Access logging for all AI interactions

### PortfolioAuditLogger

- Audit event types: READ, WRITE, DELETE, EXPORT, AI_ACCESS
- Comprehensive logging with metadata
- File-based and in-memory storage
- Audit log export functionality
- Singleton instance management

### Sensitive Code Leak Prevention (SCLP)

- Pattern detection for financial data leaks
- Severity weighting and violation tiers
- Escalating penalties (cooldowns, blocks, quarantines)
- Circuit breaker integration for resilience
- Multi-layer safety pipeline

## Scope Boundaries

### Allowed for Analytics

- Aggregated portfolio metrics (total value, gain/loss percentages)
- Risk scores and concentration metrics
- Sector allocation summaries
- Top/worst performer rankings (symbol only, no quantities)
- Trading signals and recommendations

### Not Allowed for Output

- Raw portfolio positions with quantities
- User-identifiable information
- Transaction history details
- Specific purchase prices
- Personal comments or notes
- Unsanitized AI outputs

### AI Access Rules

- AI can only access portfolio data with explicit approval
- AI outputs must be sanitized before display
- AI cannot access user-identifiable data
- AI cannot recommend specific buy/sell actions without approval
- All AI interactions must be logged

## Integration Points

### Databricks Backend

- Schema: `portfolio_positions`, `price_history`, `trading_signals`, `portfolio_events`, `portfolio_summary`
- Persistence: MERGE queries for upserts
- Analytics: Performance analysis, risk assessment, sector allocation
- Audit: Dedicated audit events table

### MCP Servers

- **grid-rag**: Knowledge base and document retrieval
- **grid-enhanced-tools**: Development tools and profiling
- **Portfolio Safety Lens**: Context-aware portfolio analytics (NEW)
- **grid-agentic**: Agent orchestration and workflows

### External Integrations

- Yahoo Finance: Portfolio data import and market data
- Databricks SQL: Database connectivity and queries
- GRID Safety Pipelines: SCLP and circuit breakers

## Security Requirements

### Portfolio Data (CRITICAL)

- Must be encrypted at rest and in transit
- User IDs must be hashed (SHA-256)
- All access must be logged with full metadata
- AI access requires explicit approval
- Output must be sanitized before display

### AI Safety (RESTRICTED)

- AI can only access data with proper authorization
- AI outputs must be sanitized
- AI cannot recommend financial actions without approval
- All AI interactions must be logged

### Audit Logging (MANDATORY)

- All portfolio access events must be logged
- Audit logs must include: timestamp, user, action, data accessed, result
- Audit logs must be exportable and queryable
- Audit logs must be retained for compliance

## Implementation Priorities

1. **Phase 1**: Context consolidation and policy definition
2. **Phase 2**: Local guardrails implementation
3. **Phase 3**: Databricks cloud setup
4. **Phase 4**: Custom MCP server (Portfolio Safety Lens)
5. **Phase 5**: Tests and demos
6. **Phase 6**: Documentation and skills registration

## References

- Databricks Unity Catalog: https://docs.databricks.com/data-governance/unity-catalog/index.html
- Databricks Security: https://docs.databricks.com/security/index.html
- Delta Lake: https://docs.databricks.com/delta/index.html
- GRID AI Safety Framework: `e:/grid/docs/AI safety.md`
- GRID Agent Architecture: `e:/grid/docs/AGENTIC_ARCHITECTURE.md`
