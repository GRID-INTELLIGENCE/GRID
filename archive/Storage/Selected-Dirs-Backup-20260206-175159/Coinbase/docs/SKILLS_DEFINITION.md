# Portfolio Safety Skills Definition
# =================================
# Skills for Coinbase Databricks AI Safety implementation

skills:
  portfolio_safety_lens:
    name: Portfolio Safety Lens
    description: Context-aware secure portfolio analytics with full guardrails
    category: security
    capabilities:
      - Sanitized portfolio summary (metrics only, no raw positions)
      - Portfolio risk signals (risk scores, no raw data)
      - Audit log tail (hashed IDs only)
      - Governance lint (policy compliance checks)
    tools:
      - portfolio_summary_safe
      - portfolio_risk_signal
      - audit_log_tail
      - governance_lint
    guardrails:
      - User ID hashing (SHA-256)
      - AES-256 encryption for sensitive data
      - Access control validation
      - AI safety approval required
      - Output sanitization enforced
      - Comprehensive audit logging
    dependencies:
      - PortfolioDataSecurity
      - PortfolioAISafety
      - PortfolioAuditLogger
      - PortfolioDataPolicy
      - AISafePortfolioAnalyzer
    examples:
      - Get safe portfolio metrics
      - Check portfolio risk levels
      - View recent audit logs
      - Verify policy compliance

  databricks_governance_lint:
    name: Databricks Governance Lint
    description: Databricks Unity Catalog governance compliance checks
    category: governance
    capabilities:
      - Managed table validation
      - Naming constraint checks
      - Access mode validation
      - Runtime version verification
      - Data quality checks
    tools:
      - validate_managed_tables
      - check_naming_constraints
      - verify_access_modes
      - check_runtime_version
      - run_data_quality_checks
    guardrails:
      - Unity Catalog compliance
      - Delta Lake format enforcement
      - ACID transaction guarantees
      - Audit trail maintenance
    dependencies:
      - DatabricksConnector
      - PortfolioDataQualityChecker
      - PortfolioAuditLogger
    examples:
      - Validate Databricks schema compliance
      - Check table naming conventions
      - Verify data quality
      - Ensure audit logging enabled

  audit_guardrails:
    name: Audit Guardrails
    description: Comprehensive audit logging and security event tracking
    category: security
    capabilities:
      - Event logging (READ, WRITE, DELETE, EXPORT, AI_ACCESS)
      - Audit log retrieval
      - Audit log export
      - Security event monitoring
      - Compliance reporting
    tools:
      - log_access_event
      - log_write_event
      - log_ai_access_event
      - get_audit_logs
      - export_audit_logs
      - monitor_security_events
    guardrails:
      - All portfolio access logged
      - Full metadata capture
      - Immutable audit trail
      - Exportable for compliance
    dependencies:
      - PortfolioAuditLogger
      - PortfolioDataSecurity
    examples:
      - Log portfolio read access
      - Log AI-driven analytics access
      - Retrieve recent audit events
      - Export audit logs for compliance

# Integration with GRID Agent System
integration:
  agent_system:
    - Skills can be invoked by GRID agents
    - Guardrails enforced at agent level
    - Audit logging for all agent actions
    - AI safety validation for AI-driven agents
  
  safety_pipeline:
    - Input validation (SCLP patterns)
    - Access control checks
    - AI safety approval
    - Output sanitization
    - Audit logging

  circuit_breaker:
    - Failure tracking
    - Penalty tiers for violations
    - Automatic blocking on critical violations
    - Cooldown periods for repeated offenses

# Compliance References
compliance:
  frameworks:
    - EU AI Act
    - NIST AI RMF
    - ISO/IEC 42001
    - GDPR (data protection)
    - SOC 2 (security controls)
  
  data_classification:
    CRITICAL:
      - Portfolio positions
      - Transaction history
      - User identifiers
    SENSITIVE:
      - User preferences
      - Analytics results
    PUBLIC:
      - Market data
      - Symbol information
      - Sector classifications

# Testing Coverage
testing:
  unit_tests:
    - test_portfolio_security_units.py
    - test_data_quality.py
  
  integration_tests:
    - test_portfolio_safety_mcp_integration.py
  
  smoke_tests:
    - test_portfolio_safety_mcp_smoke.py
  
  examples:
    - examples/portfolio_safety_lens_demo.py
    - examples/comprehensive_security.py

# Documentation
documentation:
  architecture:
    - docs/COINBASE_CONTEXT.md
    - docs/PORTFOLIO_SAFETY_LENS.md
    - docs/DATABRICKS_CONFIG.md
  
  code:
    - coinbase/security/portfolio_data_policy.py
    - coinbase/security/ai_safety.py
    - coinbase/security/audit_logger.py
    - coinbase/database/secure_persistence.py
    - coinbase/database/ai_safe_analyzer.py
    - coinbase/database/data_quality.py
    - grid/mcp-setup/server/portfolio_safety_mcp_server.py
