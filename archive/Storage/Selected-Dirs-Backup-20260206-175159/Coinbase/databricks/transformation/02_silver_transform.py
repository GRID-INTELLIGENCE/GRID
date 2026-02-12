# Databricks Notebook: Transformation (Silver Layer)
# Description: Cleaning, normalization, and quality checks on Bronze data

# 1. Read from Bronze
# df = spark.read.table(f"{CATALOG}.{SCHEMA_BRONZE}.raw_coinbase_data")

# 2. Data Cleaning
# Handle missing values, filter duplicates, normalize timestamps
# clean_df = df.filter(col("price").isNotNull()).dropDuplicates(["timestamp", "symbol"])

# 3. Schema Enforcement & Quality Checks
# Validate data types and business rules

# 4. Write to Silver
# clean_df.write.format("delta").mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA_SILVER}.cleaned_coinbase_data")
