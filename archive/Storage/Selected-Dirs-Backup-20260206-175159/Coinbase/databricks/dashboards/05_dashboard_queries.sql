# Databricks SQL: Dashboard Queries
# Description: SQL queries for visualization in Databricks SQL Dashboards

# -- 1. Daily Volume by Asset
# SELECT symbol, date(timestamp) as date, sum(volume) as total_volume
# FROM silver.cleaned_coinbase_data
# GROUP BY 1, 2
# ORDER BY 2 DESC, 3 DESC;

# -- 2. Price Volatility (Moving Average)
# SELECT timestamp, symbol, price, 
#        avg(price) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) as ma_24h
# FROM silver.cleaned_coinbase_data;

# -- 3. Feature Distribution
# SELECT rsi, count(*) as count
# FROM gold.coinbase_features
# GROUP BY 1;
