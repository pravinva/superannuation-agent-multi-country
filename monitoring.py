#!/usr/bin/env python3
from shared.logging_config import get_logger

logger = get_logger(__name__)

"""
Observability and Monitoring for SuperAdvisor Agent
Uses native Databricks tools: MLflow and Lakehouse Monitoring
"""

import mlflow
import time
from datetime import datetime
from typing import Dict, Optional, List
from databricks.sdk import WorkspaceClient
from config import (
    MLFLOW_PROD_EXPERIMENT_PATH,
    UNITY_CATALOG,
    UNITY_SCHEMA,
    SQL_WAREHOUSE_ID
)


class AgentMonitor:
    """
    Comprehensive monitoring for SuperAdvisor Agent using MLflow.
    
    Tracks:
    - Query performance (latency, cost, tokens)
    - Classification metrics (accuracy, stage distribution)
    - Validation metrics (pass rate, confidence)
    - Business metrics (queries by country, tool usage)
    - Model performance (synthesis, validation)
    """
    
    def __init__(self, experiment_path: Optional[str] = None):
        """
        Initialize monitoring with MLflow tracking.
        
        Args:
            experiment_path: MLflow experiment path
        """
        self.experiment_path = experiment_path or MLFLOW_PROD_EXPERIMENT_PATH
        self.w = WorkspaceClient()
        
        # Set up MLflow
        try:
            mlflow.set_tracking_uri("databricks")
            mlflow.set_experiment(self.experiment_path)
            logger.info(f"✅ MLflow monitoring initialized: {self.experiment_path}")
        except Exception as e:
            logger.info(f"⚠️ MLflow initialization warning: {e}")
    
    def log_query_execution(self, 
                           session_id: str,
                           user_id: str,
                           country: str,
                           query_string: str,
                           result: Dict,
                           cost_breakdown: Dict,
                           elapsed_time: float):
        """
        Log a complete query execution to MLflow with detailed metrics.
        
        Args:
            session_id: Unique session identifier
            user_id: Member/user identifier
            country: Country code
            query_string: User's query
            result: Query result dictionary
            cost_breakdown: Detailed cost breakdown
            elapsed_time: Total execution time
        """
        try:
            run_name = f"query-{session_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            with mlflow.start_run(run_name=run_name) as run:
                # === PARAMETERS (Query Context) ===
                mlflow.log_param("session_id", session_id)
                mlflow.log_param("user_id", user_id)
                mlflow.log_param("country", country)
                mlflow.log_param("query_length", len(query_string))
                mlflow.log_param("timestamp", datetime.now().isoformat())
                
                # Classification details
                classification = result.get('classification', {})
                mlflow.log_param("classification_method", classification.get('method', 'unknown'))
                mlflow.log_param("classification_result", classification.get('classification', 'unknown'))
                mlflow.log_param("off_topic", result.get('off_topic', False))
                
                # Tools used
                tools_used = result.get('tools_used', [])
                mlflow.log_param("tools_used", ','.join(tools_used) if tools_used else 'none')
                mlflow.log_param("tools_count", len(tools_used))
                
                # Validation details
                validation = result.get('validation', {})
                mlflow.log_param("validation_mode", validation.get('_validator_used', 'unknown'))
                
                # === METRICS (Performance) ===
                
                # Latency metrics
                mlflow.log_metric("total_latency_sec", elapsed_time)
                mlflow.log_metric("response_length", len(result.get('response', '')))
                
                # Cost metrics
                total_cost = cost_breakdown.get('total', {}).get('total_cost', 0)
                mlflow.log_metric("total_cost_usd", total_cost)
                mlflow.log_metric("synthesis_cost_usd", cost_breakdown.get('synthesis', {}).get('cost', 0))
                mlflow.log_metric("validation_cost_usd", cost_breakdown.get('validation', {}).get('cost', 0))
                
                # Token metrics
                mlflow.log_metric("total_tokens", cost_breakdown.get('total', {}).get('total_tokens', 0))
                mlflow.log_metric("synthesis_tokens", cost_breakdown.get('total', {}).get('synthesis_tokens', 0))
                mlflow.log_metric("validation_tokens", cost_breakdown.get('total', {}).get('validation_tokens', 0))
                
                # Classification metrics
                mlflow.log_metric("classification_confidence", classification.get('confidence', 0))
                mlflow.log_metric("classification_latency_ms", classification.get('latency_ms', 0))
                mlflow.log_metric("classification_cost_usd", classification.get('cost_usd', 0))
                
                # Validation metrics
                mlflow.log_metric("validation_confidence", validation.get('confidence', 0))
                mlflow.log_metric("validation_passed", 1 if validation.get('passed', True) else 0)
                mlflow.log_metric("validation_attempts", result.get('attempts', 1))
                violations_count = len(validation.get('violations', []))
                mlflow.log_metric("validation_violations", violations_count)
                
                # Synthesis metrics
                synthesis_results = result.get('synthesis_results', [])
                if synthesis_results:
                    avg_synthesis_latency = sum(s.get('duration', 0) for s in synthesis_results) / len(synthesis_results)
                    mlflow.log_metric("avg_synthesis_latency_sec", avg_synthesis_latency)
                
                # === ARTIFACTS (Detailed Data) ===
                
                # Log query and response
                mlflow.log_text(query_string, "query.txt")
                mlflow.log_text(result.get('response', ''), "response.txt")
                
                # Log cost breakdown as JSON
                mlflow.log_dict(cost_breakdown, "cost_breakdown.json")
                
                # Log classification details
                mlflow.log_dict(classification, "classification.json")
                
                # Log validation details
                mlflow.log_dict(validation, "validation.json")
                
                # Log full result
                mlflow.log_dict(result, "full_result.json")
                
                # === TAGS (Searchable Metadata) ===
                mlflow.set_tag("country", country)
                mlflow.set_tag("off_topic", str(result.get('off_topic', False)))
                mlflow.set_tag("validation_passed", str(validation.get('passed', True)))
                mlflow.set_tag("classification_method", classification.get('method', 'unknown'))
                mlflow.set_tag("environment", "production")
                
                logger.info(f"✅ MLflow logged: {run.info.run_id}")
                return run.info.run_id
                
        except Exception as e:
            logger.info(f"⚠️ MLflow logging error: {e}")
            return None
    
    def log_classifier_metrics(self, classifier_metrics: Dict, batch_size: int = 100):
        """
        Log classifier performance metrics to MLflow.
        
        Args:
            classifier_metrics: Metrics from classifier.get_metrics()
            batch_size: Number of queries in this batch
        """
        try:
            run_name = f"classifier-metrics-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            with mlflow.start_run(run_name=run_name):
                # Stage distribution
                mlflow.log_metric("stage1_percentage", classifier_metrics.get('stage1_percentage', 0))
                mlflow.log_metric("stage2_percentage", classifier_metrics.get('stage2_percentage', 0))
                mlflow.log_metric("stage3_percentage", classifier_metrics.get('stage3_percentage', 0))
                
                # Performance
                mlflow.log_metric("avg_latency_ms", classifier_metrics.get('avg_latency_ms', 0))
                mlflow.log_metric("avg_cost_usd", classifier_metrics.get('avg_cost_usd', 0))
                mlflow.log_metric("cache_hit_rate", classifier_metrics.get('cache_hit_rate', 0))
                
                # Volume
                mlflow.log_metric("total_queries", classifier_metrics.get('total_queries', 0))
                mlflow.log_metric("batch_size", batch_size)
                
                # Log full metrics
                mlflow.log_dict(classifier_metrics, "classifier_metrics.json")
                
                mlflow.set_tag("metric_type", "classifier")
                mlflow.set_tag("timestamp", datetime.now().isoformat())
                
                logger.info(f"✅ Classifier metrics logged to MLflow")
                
        except Exception as e:
            logger.info(f"⚠️ Classifier metrics logging error: {e}")
    
    def log_model_performance(self, 
                             model_type: str,
                             metrics: Dict,
                             period: str = "hourly"):
        """
        Log model performance metrics (synthesis/validation LLMs).
        
        Args:
            model_type: "synthesis" or "validation"
            metrics: Performance metrics dictionary
            period: Time period (hourly, daily, weekly)
        """
        try:
            run_name = f"{model_type}-performance-{period}-{datetime.now().strftime('%Y%m%d-%H')}"
            
            with mlflow.start_run(run_name=run_name):
                mlflow.log_param("model_type", model_type)
                mlflow.log_param("period", period)
                mlflow.log_param("timestamp", datetime.now().isoformat())
                
                # Log all metrics
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)):
                        mlflow.log_metric(metric_name, metric_value)
                
                mlflow.log_dict(metrics, f"{model_type}_metrics.json")
                mlflow.set_tag("metric_type", "model_performance")
                
                logger.info(f"✅ {model_type} model performance logged")
                
        except Exception as e:
            logger.info(f"⚠️ Model performance logging error: {e}")


class LakehouseMonitor:
    """
    Set up and manage Lakehouse Monitoring for governance table.
    
    Monitors:
    - Query volume and patterns
    - Cost trends
    - Validation pass rates
    - Classification accuracy
    - Latency trends
    - Error rates
    """
    
    def __init__(self):
        """Initialize Lakehouse Monitor."""
        self.w = WorkspaceClient()
        self.governance_table = f"{UNITY_CATALOG}.{UNITY_SCHEMA}.governance"
        logger.info(f"✅ Lakehouse Monitor initialized for {self.governance_table}")
    
    def create_monitoring_profile(self, 
                                 profile_name: str = "superadvisor_monitor",
                                 baseline_table: Optional[str] = None):
        """
        Create Lakehouse Monitoring profile for the governance table.
        
        This monitors:
        - Data quality (completeness, validity)
        - Data drift (distribution changes)
        - Custom metrics (cost, latency, accuracy)
        
        Args:
            profile_name: Name for the monitoring profile
            baseline_table: Optional baseline table for drift detection
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Setting up Lakehouse Monitoring Profile: {profile_name}")
        logger.info(f"{'='*70}")
        
        # SQL to create monitoring views
        setup_sql = f"""
-- Create monitoring aggregation view
CREATE OR REPLACE VIEW {UNITY_CATALOG}.{UNITY_SCHEMA}.governance_monitoring AS
SELECT 
  DATE(timestamp) as date,
  country,
  tool_used,
  judge_verdict,
  validation_mode,
  
  -- Volume metrics
  COUNT(*) as query_count,
  COUNT(DISTINCT user_id) as unique_users,
  COUNT(DISTINCT session_id) as unique_sessions,
  
  -- Cost metrics
  AVG(cost) as avg_cost,
  SUM(cost) as total_cost,
  MIN(cost) as min_cost,
  MAX(cost) as max_cost,
  PERCENTILE_APPROX(cost, 0.95) as p95_cost,
  
  -- Validation metrics
  SUM(CASE WHEN judge_verdict = 'Pass' THEN 1 ELSE 0 END) as passed_count,
  AVG(CASE WHEN judge_verdict = 'Pass' THEN 1.0 ELSE 0.0 END) as pass_rate,
  AVG(validation_attempts) as avg_validation_attempts,
  
  -- Latency metrics
  AVG(runtime_sec) as avg_latency_sec,
  PERCENTILE_APPROX(runtime_sec, 0.50) as p50_latency_sec,
  PERCENTILE_APPROX(runtime_sec, 0.95) as p95_latency_sec,
  PERCENTILE_APPROX(runtime_sec, 0.99) as p99_latency_sec,
  
  -- Error metrics
  SUM(CASE WHEN error_info != '' THEN 1 ELSE 0 END) as error_count,
  
  -- Query length metrics
  AVG(LENGTH(query_text)) as avg_query_length,
  AVG(LENGTH(agent_response)) as avg_response_length
  
FROM {self.governance_table}
WHERE timestamp >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY DATE(timestamp), country, tool_used, judge_verdict, validation_mode
ORDER BY date DESC, country;

-- Create hourly metrics view (for real-time monitoring)
CREATE OR REPLACE VIEW {UNITY_CATALOG}.{UNITY_SCHEMA}.governance_monitoring_hourly AS
SELECT 
  DATE_TRUNC('HOUR', timestamp) as hour,
  country,
  
  COUNT(*) as query_count,
  AVG(cost) as avg_cost,
  SUM(cost) as total_cost,
  AVG(CASE WHEN judge_verdict = 'Pass' THEN 1.0 ELSE 0.0 END) as pass_rate,
  AVG(runtime_sec) as avg_latency_sec,
  PERCENTILE_APPROX(runtime_sec, 0.95) as p95_latency_sec,
  SUM(CASE WHEN error_info != '' THEN 1 ELSE 0 END) as error_count
  
FROM {self.governance_table}
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY DATE_TRUNC('HOUR', timestamp), country
ORDER BY hour DESC;

-- Create classification metrics view
CREATE OR REPLACE VIEW {UNITY_CATALOG}.{UNITY_SCHEMA}.classification_monitoring AS
SELECT 
  DATE(timestamp) as date,
  country,
  
  COUNT(*) as total_queries,
  
  -- Tool usage distribution
  SUM(CASE WHEN tool_used = 'tax' THEN 1 ELSE 0 END) as tax_queries,
  SUM(CASE WHEN tool_used = 'benefit' THEN 1 ELSE 0 END) as benefit_queries,
  SUM(CASE WHEN tool_used = 'projection' THEN 1 ELSE 0 END) as projection_queries,
  
  -- Cost efficiency
  AVG(cost) as avg_cost_per_query,
  SUM(cost) as total_daily_cost,
  
  -- Response quality
  AVG(validation_attempts) as avg_attempts,
  AVG(LENGTH(agent_response)) as avg_response_length
  
FROM {self.governance_table}
WHERE timestamp >= CURRENT_DATE - INTERVAL 90 DAYS
GROUP BY DATE(timestamp), country
ORDER BY date DESC;
"""
        
        logger.info("\n📊 Creating monitoring views...")
        logger.info(f"   - {UNITY_CATALOG}.{UNITY_SCHEMA}.governance_monitoring")
        logger.info(f"   - {UNITY_CATALOG}.{UNITY_SCHEMA}.governance_monitoring_hourly")
        logger.info(f"   - {UNITY_CATALOG}.{UNITY_SCHEMA}.classification_monitoring")
        
        return setup_sql
    
    def create_alert_queries(self) -> Dict[str, str]:
        """
        Create SQL queries for alerting on anomalies.
        
        Returns:
            Dictionary of alert queries
        """
        alerts = {
            "high_cost_alert": f"""
-- Alert: Queries with unusually high cost
SELECT 
  timestamp,
  user_id,
  query_text,
  cost,
  tool_used
FROM {self.governance_table}
WHERE 
  timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
  AND cost > (
    SELECT AVG(cost) + 3 * STDDEV(cost)
    FROM {self.governance_table}
    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
  )
ORDER BY cost DESC
LIMIT 10;
""",
            
            "high_error_rate_alert": f"""
-- Alert: High error rate in last hour
SELECT 
  DATE_TRUNC('HOUR', timestamp) as hour,
  country,
  COUNT(*) as total_queries,
  SUM(CASE WHEN error_info != '' THEN 1 ELSE 0 END) as errors,
  SUM(CASE WHEN error_info != '' THEN 1.0 ELSE 0.0 END) / COUNT(*) as error_rate
FROM {self.governance_table}
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
GROUP BY DATE_TRUNC('HOUR', timestamp), country
HAVING error_rate > 0.05  -- Alert if >5% error rate
ORDER BY hour DESC;
""",
            
            "low_pass_rate_alert": f"""
-- Alert: Low validation pass rate
SELECT 
  DATE_TRUNC('HOUR', timestamp) as hour,
  country,
  validation_mode,
  COUNT(*) as total_queries,
  SUM(CASE WHEN judge_verdict = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*) as pass_rate
FROM {self.governance_table}
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
GROUP BY DATE_TRUNC('HOUR', timestamp), country, validation_mode
HAVING pass_rate < 0.70  -- Alert if <70% pass rate
ORDER BY pass_rate ASC;
""",
            
            "high_latency_alert": f"""
-- Alert: Queries with high latency
SELECT 
  timestamp,
  user_id,
  query_text,
  runtime_sec,
  tool_used,
  validation_attempts
FROM {self.governance_table}
WHERE 
  timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
  AND runtime_sec > 30  -- Alert if >30 seconds
ORDER BY runtime_sec DESC
LIMIT 10;
""",
            
            "cost_spike_alert": f"""
-- Alert: Unusual cost spike (hourly)
WITH hourly_costs AS (
  SELECT 
    DATE_TRUNC('HOUR', timestamp) as hour,
    SUM(cost) as total_cost
  FROM {self.governance_table}
  WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
  GROUP BY DATE_TRUNC('HOUR', timestamp)
),
stats AS (
  SELECT 
    AVG(total_cost) as avg_cost,
    STDDEV(total_cost) as stddev_cost
  FROM hourly_costs
)
SELECT 
  h.hour,
  h.total_cost,
  s.avg_cost,
  (h.total_cost - s.avg_cost) / s.stddev_cost as z_score
FROM hourly_costs h, stats s
WHERE 
  h.hour >= CURRENT_TIMESTAMP - INTERVAL 2 HOURS
  AND (h.total_cost - s.avg_cost) / s.stddev_cost > 3  -- 3 sigma
ORDER BY h.hour DESC;
"""
        }
        
        return alerts
    
    def create_dashboard_queries(self) -> Dict[str, str]:
        """
        Create SQL queries for operational dashboards.
        
        Returns:
            Dictionary of dashboard queries
        """
        dashboards = {
            "real_time_metrics": f"""
-- Real-time metrics (last 24 hours)
SELECT 
  'Last 24h' as period,
  COUNT(*) as total_queries,
  COUNT(DISTINCT user_id) as unique_users,
  SUM(cost) as total_cost,
  AVG(cost) as avg_cost,
  AVG(runtime_sec) as avg_latency_sec,
  SUM(CASE WHEN judge_verdict = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*) as pass_rate,
  SUM(CASE WHEN error_info != '' THEN 1 ELSE 0 END) as errors
FROM {self.governance_table}
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS;
""",
            
            "country_breakdown": f"""
-- Metrics by country (last 7 days)
SELECT 
  country,
  COUNT(*) as query_count,
  AVG(cost) as avg_cost,
  SUM(cost) as total_cost,
  AVG(runtime_sec) as avg_latency,
  SUM(CASE WHEN judge_verdict = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*) as pass_rate
FROM {self.governance_table}
WHERE timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY country
ORDER BY query_count DESC;
""",
            
            "tool_usage": f"""
-- Tool usage patterns (last 7 days)
SELECT 
  tool_used,
  COUNT(*) as usage_count,
  AVG(cost) as avg_cost,
  AVG(runtime_sec) as avg_latency,
  SUM(CASE WHEN judge_verdict = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*) as pass_rate
FROM {self.governance_table}
WHERE timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY tool_used
ORDER BY usage_count DESC;
""",
            
            "hourly_trend": f"""
-- Hourly query volume and cost (last 48 hours)
SELECT 
  DATE_TRUNC('HOUR', timestamp) as hour,
  COUNT(*) as query_count,
  SUM(cost) as total_cost,
  AVG(runtime_sec) as avg_latency,
  SUM(CASE WHEN judge_verdict = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*) as pass_rate
FROM {self.governance_table}
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 48 HOURS
GROUP BY DATE_TRUNC('HOUR', timestamp)
ORDER BY hour DESC;
""",
            
            "validation_performance": f"""
-- Validation performance by mode (last 7 days)
SELECT 
  validation_mode,
  COUNT(*) as query_count,
  AVG(validation_attempts) as avg_attempts,
  SUM(CASE WHEN judge_verdict = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*) as pass_rate,
  AVG(runtime_sec) as avg_latency
FROM {self.governance_table}
WHERE timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY validation_mode
ORDER BY query_count DESC;
"""
        }
        
        return dashboards
    
    def setup_monitoring(self):
        """
        Complete monitoring setup including views, alerts, and dashboards.
        """
        logger.info(f"\n{'='*70}")
        logger.info("🔧 LAKEHOUSE MONITORING SETUP")
        logger.info(f"{'='*70}\n")
        
        # 1. Create monitoring views
        monitoring_sql = self.create_monitoring_profile()
        logger.info("✅ Monitoring views SQL generated")
        logger.info("   Run this SQL in Databricks SQL to create views\n")
        
        # 2. Generate alert queries
        alerts = self.create_alert_queries()
        logger.info(f"✅ {len(alerts)} alert queries generated:")
        for alert_name in alerts.keys():
            logger.info(f"   - {alert_name}")

        # 3. Generate dashboard queries
        dashboards = self.create_dashboard_queries()
        logger.info(f"✅ {len(dashboards)} dashboard queries generated:")
        for dashboard_name in dashboards.keys():
            logger.info(f"   - {dashboard_name}")
        
        logger.info(f"{'='*70}")
        logger.info("📊 NEXT STEPS:")
        logger.info(f"{'='*70}")
        logger.info("1. Run the monitoring views SQL in Databricks SQL")
        logger.info("2. Create SQL alerts using the alert queries")
        logger.info("3. Build dashboards using the dashboard queries")
        logger.info("4. Set up scheduled jobs to check alerts")
        logger.info(f"{'='*70}\n")
        
        return {
            "monitoring_sql": monitoring_sql,
            "alerts": alerts,
            "dashboards": dashboards
        }


def create_monitoring_notebook():
    """
    Generate a Databricks notebook for monitoring setup.
    
    Returns:
        Notebook cells as a list
    """
    cells = []
    
    # Cell 1: Setup
    cells.append({
        "cell_type": "markdown",
        "source": """# SuperAdvisor Agent Monitoring Setup

This notebook sets up comprehensive monitoring for the SuperAdvisor Agent using:
- **Lakehouse Monitoring**: Track data quality, drift, and custom metrics
- **MLflow**: Log and track model performance
- **SQL Alerts**: Real-time alerting on anomalies

## Architecture

```
Query Execution → Governance Table → Monitoring Views → Dashboards + Alerts
                ↓
              MLflow → Performance Tracking → Model Registry
```
"""
    })
    
    # Cell 2: Create monitoring views
    cells.append({
        "cell_type": "code",
        "source": """from monitoring import LakehouseMonitor

# Initialize monitor
monitor = LakehouseMonitor()

# Setup monitoring (generates SQL)
setup_result = monitor.setup_monitoring()

# Print monitoring SQL
print(setup_result['monitoring_sql'])"""
    })
    
    # Cell 3: Query real-time metrics
    cells.append({
        "cell_type": "code",
        "source": """# Get dashboard queries
dashboards = monitor.create_dashboard_queries()

# Display real-time metrics
display(spark.sql(dashboards['real_time_metrics']))"""
    })
    
    return cells


# Convenience function to export monitoring setup
def export_monitoring_setup(output_path: str = "monitoring_setup.sql"):
    """
    Export all monitoring SQL to a file.
    
    Args:
        output_path: Path to save SQL file
    """
    monitor = LakehouseMonitor()
    setup = monitor.setup_monitoring()
    
    with open(output_path, 'w') as f:
        f.write("-- SuperAdvisor Agent Monitoring Setup\n")
        f.write("-- Generated: " + datetime.now().isoformat() + "\n\n")
        
        f.write("-- ========================================\n")
        f.write("-- MONITORING VIEWS\n")
        f.write("-- ========================================\n\n")
        f.write(setup['monitoring_sql'])
        f.write("\n\n")
        
        f.write("-- ========================================\n")
        f.write("-- ALERT QUERIES\n")
        f.write("-- ========================================\n\n")
        for alert_name, alert_sql in setup['alerts'].items():
            f.write(f"-- {alert_name}\n")
            f.write(alert_sql)
            f.write("\n\n")
        
        f.write("-- ========================================\n")
        f.write("-- DASHBOARD QUERIES\n")
        f.write("-- ========================================\n\n")
        for dashboard_name, dashboard_sql in setup['dashboards'].items():
            f.write(f"-- {dashboard_name}\n")
            f.write(dashboard_sql)
            f.write("\n\n")
    
    logger.info(f"✅ Monitoring setup exported to {output_path}")


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("SuperAdvisor Agent Monitoring Setup")
    logger.info("=" * 70)
    
    # Setup Lakehouse Monitoring
    monitor = LakehouseMonitor()
    setup = monitor.setup_monitoring()
    
    # Export to file
    export_monitoring_setup()
    
    logger.info("\n✅ Monitoring setup complete!")
    logger.info("\nRun this file to generate monitoring SQL:")
    logger.info("  python monitoring.py")

