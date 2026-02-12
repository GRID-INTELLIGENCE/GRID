# Databricks Notebook: Ingestion (Bronze Layer)
# Description: Raw data ingestion from various sources (Yahoo Finance, Exchange APIs)

# 1. Initialization
# Define variables and import libraries
# spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# 2. Extract
# Fetch raw data using APIs or load from mount point
# raw_df = spark.read.json(BRONZE_PATH)

# 3. Transform (Minimal)
# Add metadata columns (ingestion_timestamp, source_file)
# bronze_df = raw_df.withColumn("_ingested_at", current_timestamp())

# 4. Load
# Write to Delta table in Bronze schema
# bronze_df.write.format("delta").mode("append").saveAsTable(f"{CATALOG}.{SCHEMA_BRONZE}.raw_coinbase_data")
