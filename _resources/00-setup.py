# Databricks notebook source
# MAGIC %md
# MAGIC # Demo Setup
# MAGIC
# MAGIC This notebook initializes the catalog, schemas, and configuration for the
# MAGIC Multi-Country Retirement Advisory demo.
# MAGIC
# MAGIC **What this notebook does:**
# MAGIC - Creates Unity Catalog and schemas if they don't exist
# MAGIC - Sets up configuration variables
# MAGIC - Prepares the environment for data loading

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC These can be overridden via widgets or environment variables

# COMMAND ----------

# Widgets for configuration
dbutils.widgets.text("catalog", "super_advisory_demo", "Catalog Name")
dbutils.widgets.text("schema", "member_data", "Schema Name")
dbutils.widgets.dropdown("reset_all_data", "false", ["true", "false"], "Reset All Data")

# Get widget values
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
reset_all_data = dbutils.widgets.get("reset_all_data") == "true"

print(f"Catalog: {catalog}")
print(f"Schema: {schema}")
print(f"Reset data: {reset_all_data}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Catalog and Schema

# COMMAND ----------

# Create catalog if it doesn't exist
spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
print(f"✓ Catalog '{catalog}' ready")

# Use the catalog
spark.sql(f"USE CATALOG {catalog}")

# Create schema if it doesn't exist
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
print(f"✓ Schema '{schema}' ready")

# Use the schema
spark.sql(f"USE SCHEMA {schema}")

# Create pension_calculators schema for UC functions
spark.sql(f"CREATE SCHEMA IF NOT EXISTS pension_calculators")
print(f"✓ Schema 'pension_calculators' ready (for UC functions)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup Configuration Variables
# MAGIC
# MAGIC These variables will be used by other notebooks

# COMMAND ----------

# Set configuration for other notebooks to use
spark.conf.set("demo.catalog", catalog)
spark.conf.set("demo.schema", schema)
spark.conf.set("demo.reset_data", str(reset_all_data))

# Cloud storage path for streaming checkpoints
cloud_storage_path = f"/tmp/{catalog}/{schema}"
spark.conf.set("demo.storage_path", cloud_storage_path)

print(f"✓ Configuration set:")
print(f"  - Catalog: {catalog}")
print(f"  - Schema: {schema}")
print(f"  - Storage path: {cloud_storage_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reset Data (Optional)
# MAGIC
# MAGIC If reset_all_data is true, drop all tables

# COMMAND ----------

if reset_all_data:
    print("⚠️  Resetting all data...")

    # Get list of tables
    tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()

    for table_row in tables:
        table_name = table_row.tableName
        full_table_name = f"{catalog}.{schema}.{table_name}"
        print(f"  Dropping {full_table_name}...")
        spark.sql(f"DROP TABLE IF EXISTS {full_table_name}")

    print(f"✓ All tables dropped in {catalog}.{schema}")
else:
    print("ℹ️  Keeping existing data (reset_all_data=false)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Setup

# COMMAND ----------

# List schemas in catalog
print("Schemas in catalog:")
display(spark.sql(f"SHOW SCHEMAS IN {catalog}"))

# List tables in schema
print(f"\nTables in {catalog}.{schema}:")
display(spark.sql(f"SHOW TABLES IN {catalog}.{schema}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup Complete
# MAGIC
# MAGIC The environment is ready for data loading. Proceed to the next notebook:
# MAGIC - **00-load-data**: Generate and load synthetic member data

# COMMAND ----------

print("✅ Setup complete!")
print(f"   Catalog: {catalog}")
print(f"   Schema: {schema}")
print(f"   Ready for data loading")
