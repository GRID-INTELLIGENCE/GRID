# Databricks Notebook: Feature Engineering
# Description: Generating technical indicators and features for ML modeling

# 1. Load Silver Data
# df = spark.read.table(f"{CATALOG}.{SCHEMA_SILVER}.cleaned_coinbase_data")

# 2. Technical Indicators
# Calculate RSI, MACD, Moving Averages, Volatility
# from pyspark.sql.window import Window
# w = Window.partitionBy("symbol").orderBy("timestamp")
# ...

# 3. Feature Selection & Engineering
# Lag features, rolling windows

# 4. Save to Gold Schema (Feature Store)
# feature_df.write.format("delta").mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA_GOLD}.coinbase_features")
