# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog Setup for Multi-Country Advisory
# MAGIC
# MAGIC This notebook sets up Unity Catalog functions and governance for the
# MAGIC retirement advisory agent.
# MAGIC
# MAGIC **What this notebook does:**
# MAGIC - Creates Unity Catalog functions for retirement calculations
# MAGIC - Sets up country-specific calculation functions
# MAGIC - Configures function permissions
# MAGIC - Tests function execution

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import sys
sys.path.append('..')

from config import UNITY_CATALOG, UNITY_SCHEMA

catalog = spark.conf.get("demo.catalog", UNITY_CATALOG)
schema = spark.conf.get("demo.schema", UNITY_SCHEMA)

print(f"Setting up UC functions in:")
print(f"  Catalog: {catalog}")
print(f"  Schema: pension_calculators")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create UC Functions from SQL DDL
# MAGIC
# MAGIC Load and execute the UC functions SQL script

# COMMAND ----------

# Read the UC functions SQL file
import os
sql_file_path = "../sql_ddls/super_advisory_demo_functions.sql"

with open(sql_file_path, 'r') as f:
    sql_content = f.read()

print(f"✓ Loaded UC functions SQL from {sql_file_path}")
print(f"  Size: {len(sql_content):,} characters")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Function Creation
# MAGIC
# MAGIC Split and execute each CREATE FUNCTION statement

# COMMAND ----------

# Split into individual statements (separated by semicolons outside of function bodies)
# This is a simplified approach - for production, use proper SQL parser

statements = []
current_stmt = []
in_function = False

for line in sql_content.split('\n'):
    line_stripped = line.strip()

    if line_stripped.startswith('CREATE OR REPLACE FUNCTION'):
        in_function = True
        if current_stmt:
            statements.append('\n'.join(current_stmt))
            current_stmt = []

    current_stmt.append(line)

    if in_function and line_stripped == ';':
        statements.append('\n'.join(current_stmt))
        current_stmt = []
        in_function = False

if current_stmt:
    statements.append('\n'.join(current_stmt))

print(f"Found {len([s for s in statements if 'CREATE' in s])} CREATE FUNCTION statements")

# COMMAND ----------

# Execute each CREATE FUNCTION statement
success_count = 0
error_count = 0

for i, stmt in enumerate(statements):
    if 'CREATE OR REPLACE FUNCTION' not in stmt:
        continue

    try:
        # Extract function name for logging
        func_name = stmt.split('FUNCTION')[1].split('(')[0].strip()

        spark.sql(stmt)
        print(f"✓ Created function: {func_name}")
        success_count += 1
    except Exception as e:
        print(f"✗ Error creating function: {str(e)[:100]}")
        error_count += 1

print(f"\nSummary:")
print(f"  Success: {success_count}")
print(f"  Errors: {error_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## List Created Functions

# COMMAND ----------

display(spark.sql(f"SHOW FUNCTIONS IN {catalog}.pension_calculators"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Function Execution
# MAGIC
# MAGIC Test key functions for each country

# COMMAND ----------

# MAGIC %md
# MAGIC ### Australia - Tax Calculation

# COMMAND ----------

result_au = spark.sql(f"""
SELECT {catalog}.pension_calculators.au_calculate_tax(
    500000,  -- super_balance
    50000,   -- withdrawal_amount
    67,      -- age
    0        -- annual_income
) as tax_result
""")

display(result_au)

# COMMAND ----------

# MAGIC %md
# MAGIC ### United States - RMD Calculation

# COMMAND ----------

result_us = spark.sql(f"""
SELECT {catalog}.pension_calculators.us_calculate_rmd(
    750000,  -- account_balance
    75       -- age
) as rmd_amount
""")

display(result_us)

# COMMAND ----------

# MAGIC %md
# MAGIC ### United Kingdom - State Pension

# COMMAND ----------

result_uk = spark.sql(f"""
SELECT {catalog}.pension_calculators.uk_calculate_state_pension(
    40,      -- ni_years
    67       -- current_age
) as pension_result
""")

display(result_uk)

# COMMAND ----------

# MAGIC %md
# MAGIC ### India - EPF Calculation

# COMMAND ----------

result_in = spark.sql(f"""
SELECT {catalog}.pension_calculators.in_calculate_epf_maturity(
    250000,  -- epf_balance
    8.25,    -- interest_rate
    10       -- years_to_retirement
) as maturity_value
""")

display(result_in)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Function Permissions
# MAGIC
# MAGIC Grant EXECUTE permission on functions to relevant groups

# COMMAND ----------

# Example: Grant execute to all users (adjust for your security model)
try:
    spark.sql(f"""
    GRANT EXECUTE ON FUNCTION {catalog}.pension_calculators.au_calculate_tax
    TO `account users`
    """)
    print("✓ Granted EXECUTE permission on AU functions")
except Exception as e:
    print(f"Note: {e}")
    print("Permissions may need to be set via Account Console")

# COMMAND ----------

# MAGIC %md
# MAGIC ## UC Functions Setup Complete
# MAGIC
# MAGIC All retirement calculation functions are now available as Unity Catalog functions.
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - **02-governance-setup**: Configure row-level security and audit logging
# MAGIC - **02-agent-demo/02-build-agent**: See these functions in action with the agent

# COMMAND ----------

print("✅ Unity Catalog functions setup complete!")
print(f"   Functions created in: {catalog}.pension_calculators")
print(f"   Tested: AU, US, UK, IN calculation functions")
print(f"   Ready for agent integration")
