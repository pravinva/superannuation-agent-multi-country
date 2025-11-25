# Databricks notebook source
# MAGIC %md
# MAGIC # MLflow Experiment Tracking
# MAGIC
# MAGIC Track agent performance, costs, and quality metrics using MLflow.

# COMMAND ----------

import sys
sys.path.append('..')

from monitoring import log_agent_metrics, get_experiment_stats
from config import MLFLOW_PROD_EXPERIMENT_PATH
import mlflow

print(f"✓ MLflow experiment: {MLFLOW_PROD_EXPERIMENT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## View Experiment Runs

# COMMAND ----------

# Set experiment
mlflow.set_experiment(MLFLOW_PROD_EXPERIMENT_PATH)

# Get recent runs
runs = mlflow.search_runs(
    experiment_names=[MLFLOW_PROD_EXPERIMENT_PATH],
    max_results=10,
    order_by=["start_time DESC"]
)

display(runs[['run_id', 'start_time', 'status', 'metrics.cost', 'metrics.latency', 'params.country']])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tracked Metrics

# COMMAND ----------

metrics = {
    "Performance": ["query_latency", "tool_execution_time", "total_time"],
    "Cost": ["total_cost", "llm_cost", "token_count"],
    "Quality": ["validation_pass_rate", "confidence_score", "tool_success_rate"]
}

for category, metric_list in metrics.items():
    print(f"\n{category}:")
    for metric in metric_list:
        print(f"  ✓ {metric}")

# COMMAND ----------

print("✅ MLflow tracking active")
