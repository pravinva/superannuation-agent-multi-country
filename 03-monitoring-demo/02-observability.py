# Databricks notebook source
# MAGIC %md  
# MAGIC # Agent Observability
# MAGIC
# MAGIC Monitor agent behavior, latency, and tool usage patterns.

# COMMAND ----------

import sys
sys.path.append('..')

from observability import track_query_latency, get_agent_stats
from config import UNITY_CATALOG, UNITY_SCHEMA

print("✓ Observability modules imported")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query Latency Analysis

# COMMAND ----------

latency_stats = spark.sql(f"""
SELECT
    country,
    COUNT(*) as query_count,
    AVG(total_time_seconds) as avg_latency,
    MIN(total_time_seconds) as min_latency,
    MAX(total_time_seconds) as max_latency,
    PERCENTILE(total_time_seconds, 0.95) as p95_latency
FROM {UNITY_CATALOG}.{UNITY_SCHEMA}.governance
GROUP BY country
ORDER BY country
""")

display(latency_stats)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tool Usage Patterns

# COMMAND ----------

tool_usage = spark.sql(f"""
SELECT
    tool_used,
    country,
    COUNT(*) as usage_count,
    AVG(total_time_seconds) as avg_time
FROM {UNITY_CATALOG}.{UNITY_SCHEMA}.governance
WHERE tool_used IS NOT NULL
GROUP BY tool_used, country
ORDER BY usage_count DESC
""")

display(tool_usage)

# COMMAND ----------

print("✅ Observability metrics available")
