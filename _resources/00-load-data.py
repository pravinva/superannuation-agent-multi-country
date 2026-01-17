# Databricks notebook source
# MAGIC %md
# MAGIC # Generate Demo Data with Faker
# MAGIC
# MAGIC This notebook generates synthetic member profiles, citations, and governance data
# MAGIC using the Faker library. Data is country-specific (AU, US, UK, IN) and matches
# MAGIC the production schema exactly.
# MAGIC
# MAGIC **What this notebook does:**
# MAGIC - Generates 28 member profiles (20 AU, 3 US, 2 UK, 3 IN)
# MAGIC - Generates 9 regulatory citations
# MAGIC - Generates 154 governance audit logs
# MAGIC - Loads data into Unity Catalog tables

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Get configuration from previous notebook
catalog = spark.conf.get("demo.catalog", "super_advisory_demo")
schema = spark.conf.get("demo.schema", "member_data")

print(f"Loading data into:")
print(f"  Catalog: {catalog}")
print(f"  Schema: {schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Data Generation Functions
# MAGIC
# MAGIC Import from the root generate_demo_data.py module

# COMMAND ----------

import sys
sys.path.append('..')  # Add parent directory to import from root

# Import data generation functions
from generate_demo_data import (
    generate_member_profiles,
    generate_citation_registry,
    generate_governance_logs
)

print("✓ Data generation functions imported")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Member Profiles
# MAGIC
# MAGIC Generate synthetic member data for all 4 countries

# COMMAND ----------

# Generate member profiles
member_profiles_df = generate_member_profiles()

print(f"Generated {len(member_profiles_df)} member profiles:")
print(f"  AU: {len(member_profiles_df[member_profiles_df['country'] == 'AU'])}")
print(f"  US: {len(member_profiles_df[member_profiles_df['country'] == 'US'])}")
print(f"  UK: {len(member_profiles_df[member_profiles_df['country'] == 'UK'])}")
print(f"  IN: {len(member_profiles_df[member_profiles_df['country'] == 'IN'])}")

# Preview
display(member_profiles_df.head(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Citation Registry
# MAGIC
# MAGIC Regulatory citations for all countries

# COMMAND ----------

citation_registry_df = generate_citation_registry()

print(f"Generated {len(citation_registry_df)} citations")
display(citation_registry_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Governance Logs
# MAGIC
# MAGIC Synthetic audit logs of agent queries

# COMMAND ----------

governance_df = generate_governance_logs(member_profiles_df, num_logs=154)

print(f"Generated {len(governance_df)} governance logs")
display(governance_df.head(3))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Convert to Spark DataFrames

# COMMAND ----------

# Convert pandas DataFrames to Spark
spark_member_profiles = spark.createDataFrame(member_profiles_df)
spark_citation_registry = spark.createDataFrame(citation_registry_df)
spark_governance = spark.createDataFrame(governance_df)

print("✓ Converted to Spark DataFrames")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load to Unity Catalog Tables
# MAGIC
# MAGIC Write data to Delta tables in Unity Catalog

# COMMAND ----------

# Member profiles
table_name = f"{catalog}.{schema}.member_profiles"
print(f"Writing to {table_name}...")

spark_member_profiles.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(table_name)

print(f"✓ Loaded {spark_member_profiles.count()} member profiles")

# COMMAND ----------

# Citation registry
table_name = f"{catalog}.{schema}.citation_registry"
print(f"Writing to {table_name}...")

spark_citation_registry.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(table_name)

print(f"✓ Loaded {spark_citation_registry.count()} citations")

# COMMAND ----------

# Governance logs
table_name = f"{catalog}.{schema}.governance"
print(f"Writing to {table_name}...")

spark_governance.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .partitionBy("country") \
    .saveAsTable(table_name)

print(f"✓ Loaded {spark_governance.count()} governance logs")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Data Loaded

# COMMAND ----------

print("Verifying data loaded successfully...\n")

# Member profiles
mp_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {catalog}.{schema}.member_profiles").collect()[0].cnt
print(f"✓ member_profiles: {mp_count} rows")

# Citation registry
cr_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {catalog}.{schema}.citation_registry").collect()[0].cnt
print(f"✓ citation_registry: {cr_count} rows")

# Governance
gov_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {catalog}.{schema}.governance").collect()[0].cnt
print(f"✓ governance: {gov_count} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample Queries

# COMMAND ----------

# MAGIC %md
# MAGIC ### Member Profiles by Country

# COMMAND ----------

display(spark.sql(f"""
SELECT
    country,
    COUNT(*) as member_count,
    AVG(age) as avg_age,
    AVG(super_balance) as avg_balance,
    AVG(annual_income_outside_super) as avg_income
FROM {catalog}.{schema}.member_profiles
GROUP BY country
ORDER BY country
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Sample Member Profiles

# COMMAND ----------

display(spark.sql(f"""
SELECT
    member_id,
    name,
    country,
    age,
    employment_status,
    super_balance,
    persona_type
FROM {catalog}.{schema}.member_profiles
ORDER BY country, member_id
LIMIT 10
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Loading Complete
# MAGIC
# MAGIC All tables loaded successfully. Proceed to the next notebook:
# MAGIC - **01-setup/01-unity-catalog-setup**: Set up UC functions and governance

# COMMAND ----------

print("✅ Data loading complete!")
print(f"   {mp_count} member profiles")
print(f"   {cr_count} citations")
print(f"   {gov_count} governance logs")
print(f"   Ready for agent demo")
