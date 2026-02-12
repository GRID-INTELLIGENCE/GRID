"""
Databricks Schema Definition
=============================
Database schema for Coinbase platform on Databricks.

Unity Catalog Compliance:
- All table and column names are lowercase with underscores
- No spaces or dots in names
- Managed Delta Lake tables for ACID compliance
- Runtime version: 11.3 LTS or higher required
- Access modes: Standard or dedicated

Focus: Databricks as top priority for artifact creation
"""

# Portfolio positions table
CREATE_PORTFOLIO_POSITIONS = """
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
"""

# Price history table
CREATE_PRICE_HISTORY = """
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
"""

# Trading signals table
CREATE_TRADING_SIGNALS = """
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
"""

# Portfolio events table
CREATE_PORTFOLIO_EVENTS = """
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
"""

# Portfolio summary table
CREATE_PORTFOLIO_SUMMARY = """
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
"""

# Audit events table for portfolio access history
CREATE_AUDIT_EVENTS = """
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
"""

# All schemas
ALL_SCHEMAS = [
    CREATE_PORTFOLIO_POSITIONS,
    CREATE_PRICE_HISTORY,
    CREATE_TRADING_SIGNALS,
    CREATE_PORTFOLIO_EVENTS,
    CREATE_PORTFOLIO_SUMMARY,
    CREATE_AUDIT_EVENTS,
]


def get_schema_ddl() -> str:
    """
    Get complete Databricks schema DDL.

    Returns:
        Complete schema DDL string
    """
    return "\n\n".join(ALL_SCHEMAS)


# MERGE queries for upsert operations
MERGE_PORTFOLIO_POSITION = """
MERGE INTO portfolio_positions target
USING (
    SELECT
        ? as user_id_hash,
        ? as symbol,
        ? as asset_name,
        ? as sector,
        ? as quantity,
        ? as purchase_price,
        ? as current_price,
        ? as purchase_value,
        ? as current_value,
        ? as total_gain_loss,
        ? as gain_loss_percentage,
        ? as purchase_date,
        ? as commission,
        ? as high_limit,
        ? as low_limit,
        ? as comment,
        ? as transaction_type,
        current_timestamp() as created_at,
        current_timestamp() as updated_at
) source
ON target.user_id_hash = source.user_id_hash AND target.symbol = source.symbol
WHEN MATCHED THEN
    UPDATE SET
        asset_name = source.asset_name,
        sector = source.sector,
        quantity = source.quantity,
        purchase_price = source.purchase_price,
        current_price = source.current_price,
        purchase_value = source.purchase_value,
        current_value = source.current_value,
        total_gain_loss = source.total_gain_loss,
        gain_loss_percentage = source.gain_loss_percentage,
        purchase_date = source.purchase_date,
        commission = source.commission,
        high_limit = source.high_limit,
        low_limit = source.low_limit,
        comment = source.comment,
        transaction_type = source.transaction_type,
        updated_at = current_timestamp()
WHEN NOT MATCHED THEN
    INSERT (
        user_id_hash, symbol, asset_name, sector, quantity,
        purchase_price, current_price, purchase_value, current_value,
        total_gain_loss, gain_loss_percentage, purchase_date, commission,
        high_limit, low_limit, comment, transaction_type, created_at, updated_at
    )
    VALUES (
        source.user_id_hash, source.symbol, source.asset_name, source.sector, source.quantity,
        source.purchase_price, source.current_price, source.purchase_value, source.current_value,
        source.total_gain_loss, source.gain_loss_percentage, source.purchase_date, source.commission,
        source.high_limit, source.low_limit, source.comment, source.transaction_type, source.created_at, source.updated_at
    )
"""

MERGE_PORTFOLIO_SUMMARY = """
MERGE INTO portfolio_summary target
USING (
    SELECT
        ? as user_id_hash,
        ? as total_positions,
        ? as total_value,
        ? as total_purchase_value,
        ? as total_commission,
        ? as total_gain_loss,
        ? as gain_loss_percentage,
        current_timestamp() as updated_at
) source
ON target.user_id_hash = source.user_id_hash
WHEN MATCHED THEN
    UPDATE SET
        total_positions = source.total_positions,
        total_value = source.total_value,
        total_purchase_value = source.total_purchase_value,
        total_commission = source.total_commission,
        total_gain_loss = source.total_gain_loss,
        gain_loss_percentage = source.gain_loss_percentage,
        updated_at = current_timestamp()
WHEN NOT MATCHED THEN
    INSERT (user_id_hash, total_positions, total_value, total_purchase_value,
            total_commission, total_gain_loss, gain_loss_percentage, updated_at)
    VALUES (source.user_id_hash, source.total_positions, source.total_value,
            source.total_purchase_value, source.total_commission, source.total_gain_loss,
            source.gain_loss_percentage, source.updated_at)
"""
