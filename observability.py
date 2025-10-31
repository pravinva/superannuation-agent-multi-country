#!/usr/bin/env python3
"""
Observability & Monitoring for SuperAdvisor Agent
Using Databricks native tools: MLflow + Lakehouse Monitoring
"""

import mlflow
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import MonitorInfoStatus
from config import (
    UNITY_CATALOG, 
    UNITY_SCHEMA, 
    MLFLOW_PROD_EXPERIMENT_PATH,
    SQL_WAREHOUSE_ID
)


class AgentObservability:
    """
    Comprehensive observability for SuperAdvisor Agent using:
    - MLflow: Experiment tracking, metrics, model registry
    - Lakehouse Monitoring: Data quality, drift detection, alerts
    """
    
    def __init__(self, 
                 experiment_path: str = None,
                 enable_mlflow: bool = True,
                 enable_lakehouse_monitoring: bool = True):
        """
        Initialize observability module.
        
        Args:
            experiment_path: MLflow experiment path
            enable_mlflow: Enable MLflow tracking
            enable_lakehouse_monitoring: Enable Lakehouse Monitoring
        """
        self.w = WorkspaceClient()
        self.experiment_path = experiment_path or MLFLOW_PROD_EXPERIMENT_PATH
        self.enable_mlflow = enable_mlflow
        self.enable_lakehouse_monitoring = enable_lakehouse_monitoring
        
        # Governance table for monitoring
        self.governance_table = f"{UNITY_CATALOG}.{UNITY_SCHEMA}.governance"
        
        # Current MLflow run context
        self.current_run = None
        self.run_metrics = {}
        
        if self.enable_mlflow:
            self._setup_mlflow()
        
        print(f"✅ AgentObservability initialized")
        print(f"   MLflow: {'Enabled' if enable_mlflow else 'Disabled'}")
        print(f"   Lakehouse Monitoring: {'Enabled' if enable_lakehouse_monitoring else 'Disabled'}")
    
    def _setup_mlflow(self):
        """Setup MLflow experiment and tracking."""
        try:
            mlflow.set_tracking_uri("databricks")
            mlflow.set_experiment(self.experiment_path)
            print(f"✅ MLflow experiment: {self.experiment_path}")
        except Exception as e:
            print(f"⚠️ MLflow setup warning: {e}")
            self.enable_mlflow = False
    
    # ========== MLFLOW TRACKING ==========
    
    def start_agent_run(self, 
                       session_id: str,
                       user_id: str,
                       country: str,
                       query: str,
                       tags: Optional[Dict] = None) -> str:
        """
        Start a new MLflow run for an agent query.
        
        Args:
            session_id: Session identifier
            user_id: User/member identifier
            country: Country code
            query: User query
            tags: Additional tags
            
        Returns:
            Run ID
        """
        if not self.enable_mlflow:
            return None
        
        try:
            # ✅ SAFETY: Close any active run first (prevents "run already active" error)
            try:
                active_run = mlflow.active_run()
                if active_run:
                    print(f"⚠️ Closing stale MLflow run: {active_run.info.run_id}")
                    mlflow.end_run()
            except Exception as cleanup_error:
                print(f"⚠️ Error cleaning up stale run: {cleanup_error}")
            
            run_name = f"agent-query-{session_id[:8]}"
            
            # Start MLflow run
            self.current_run = mlflow.start_run(run_name=run_name)
            
            # Log parameters
            mlflow.log_param("session_id", session_id)
            mlflow.log_param("user_id", user_id)
            mlflow.log_param("country", country)
            mlflow.log_param("query_length", len(query))
            mlflow.log_param("timestamp", datetime.utcnow().isoformat())
            
            # Log tags
            mlflow.set_tag("component", "superadvisor_agent")
            mlflow.set_tag("country", country)
            if tags:
                for key, value in tags.items():
                    mlflow.set_tag(key, str(value))
            
            # Initialize metrics tracking
            self.run_metrics = {
                'start_time': time.time(),
                'classification': {},
                'tools': {},
                'synthesis': {},
                'validation': {},
                'total': {}
            }
            
            return self.current_run.info.run_id
            
        except Exception as e:
            print(f"⚠️ Error starting MLflow run: {e}")
            return None
    
    def log_classification(self, result: Dict):
        """
        Log classification metrics.
        
        Args:
            result: Classification result from cascade classifier
        """
        if not self.enable_mlflow or not self.current_run:
            return
        
        try:
            self.run_metrics['classification'] = result
            
            mlflow.log_metric("classification.is_on_topic", 1.0 if result.get('is_on_topic') else 0.0)
            mlflow.log_metric("classification.confidence", result.get('confidence', 0.0))
            mlflow.log_metric("classification.latency_ms", result.get('latency_ms', 0.0))
            mlflow.log_metric("classification.cost_usd", result.get('cost_usd', 0.0))
            
            mlflow.log_param("classification.method", result.get('method', 'unknown'))
            mlflow.log_param("classification.result", result.get('classification', 'unknown'))
            
            # Log stage used (for monitoring stage distribution)
            method = result.get('method', 'unknown')
            if 'regex' in method:
                mlflow.log_metric("classification.stage", 1)
            elif 'embedding' in method:
                mlflow.log_metric("classification.stage", 2)
            elif 'llm' in method:
                mlflow.log_metric("classification.stage", 3)
            
        except Exception as e:
            print(f"⚠️ Error logging classification: {e}")
    
    def log_tool_execution(self, tools_used: List[str], tool_results: Dict):
        """
        Log tool execution metrics.
        
        Args:
            tools_used: List of tools called
            tool_results: Dictionary of tool results
        """
        if not self.enable_mlflow or not self.current_run:
            return
        
        try:
            self.run_metrics['tools'] = {
                'tools_used': tools_used,
                'tools_count': len(tools_used)
            }
            
            mlflow.log_metric("tools.count", len(tools_used))
            mlflow.log_param("tools.used", ",".join(tools_used) if tools_used else "none")
            
            # Log tool success/failure
            failed_tools = [
                name for name, result in tool_results.items()
                if isinstance(result, dict) and 'error' in result
            ]
            
            mlflow.log_metric("tools.failed_count", len(failed_tools))
            mlflow.log_metric("tools.success_rate", 
                            (len(tools_used) - len(failed_tools)) / len(tools_used) if tools_used else 1.0)
            
            if failed_tools:
                mlflow.log_param("tools.failures", ",".join(failed_tools))
            
        except Exception as e:
            print(f"⚠️ Error logging tool execution: {e}")
    
    def log_synthesis(self, synthesis_results: List[Dict]):
        """
        Log synthesis (response generation) metrics.
        
        Args:
            synthesis_results: List of synthesis attempt results
        """
        if not self.enable_mlflow or not self.current_run:
            return
        
        try:
            total_input_tokens = sum(s.get('input_tokens', 0) for s in synthesis_results)
            total_output_tokens = sum(s.get('output_tokens', 0) for s in synthesis_results)
            total_cost = sum(s.get('cost', 0.0) for s in synthesis_results)
            total_duration = sum(s.get('duration', 0.0) for s in synthesis_results)
            
            self.run_metrics['synthesis'] = {
                'attempts': len(synthesis_results),
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'total_tokens': total_input_tokens + total_output_tokens,
                'cost': total_cost,
                'duration': total_duration
            }
            
            mlflow.log_metric("synthesis.attempts", len(synthesis_results))
            mlflow.log_metric("synthesis.input_tokens", total_input_tokens)
            mlflow.log_metric("synthesis.output_tokens", total_output_tokens)
            mlflow.log_metric("synthesis.total_tokens", total_input_tokens + total_output_tokens)
            mlflow.log_metric("synthesis.cost_usd", total_cost)
            mlflow.log_metric("synthesis.duration_sec", total_duration)
            
            if synthesis_results:
                mlflow.log_param("synthesis.model", synthesis_results[0].get('model', 'unknown'))
            
        except Exception as e:
            print(f"⚠️ Error logging synthesis: {e}")
    
    def log_validation(self, validation_results: List[Dict]):
        """
        Log validation metrics.
        
        Args:
            validation_results: List of validation attempt results
        """
        if not self.enable_mlflow or not self.current_run:
            return
        
        try:
            if not validation_results:
                return
            
            final_validation = validation_results[-1]
            
            total_input_tokens = sum(v.get('input_tokens', 0) for v in validation_results)
            total_output_tokens = sum(v.get('output_tokens', 0) for v in validation_results)
            total_cost = sum(v.get('cost', 0.0) for v in validation_results)
            total_duration = sum(v.get('duration', 0.0) for v in validation_results)
            
            self.run_metrics['validation'] = {
                'attempts': len(validation_results),
                'passed': final_validation.get('passed', False),
                'confidence': final_validation.get('confidence', 0.0),
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'total_tokens': total_input_tokens + total_output_tokens,
                'cost': total_cost,
                'duration': total_duration
            }
            
            mlflow.log_metric("validation.attempts", len(validation_results))
            mlflow.log_metric("validation.passed", 1.0 if final_validation.get('passed') else 0.0)
            mlflow.log_metric("validation.confidence", final_validation.get('confidence', 0.0))
            mlflow.log_metric("validation.input_tokens", total_input_tokens)
            mlflow.log_metric("validation.output_tokens", total_output_tokens)
            mlflow.log_metric("validation.total_tokens", total_input_tokens + total_output_tokens)
            mlflow.log_metric("validation.cost_usd", total_cost)
            mlflow.log_metric("validation.duration_sec", total_duration)
            
            # Log violations
            violations = final_validation.get('violations', [])
            mlflow.log_metric("validation.violations_count", len(violations))
            
            if validation_results:
                mlflow.log_param("validation.model", validation_results[0].get('model', 'unknown'))
            
            # Log validation details as artifact
            mlflow.log_dict(final_validation, "validation_result.json")
            
        except Exception as e:
            print(f"⚠️ Error logging validation: {e}")
    
    def end_agent_run(self, 
                     response: str,
                     success: bool = True,
                     error: Optional[str] = None):
        """
        End the current MLflow run and log final metrics.
        
        Args:
            response: Final response text
            success: Whether the query was successful
            error: Error message if failed
        """
        if not self.enable_mlflow:
            return
        
        # ✅ SAFETY: Check if there's actually an active run
        if not mlflow.active_run():
            print("⚠️ No active MLflow run to end")
            self.current_run = None
            return
        
        try:
            # Calculate total metrics
            elapsed = time.time() - self.run_metrics.get('start_time', time.time())
            
            # Total cost
            total_cost = (
                self.run_metrics.get('classification', {}).get('cost_usd', 0.0) +
                self.run_metrics.get('synthesis', {}).get('cost', 0.0) +
                self.run_metrics.get('validation', {}).get('cost', 0.0)
            )
            
            # Total tokens
            total_tokens = (
                self.run_metrics.get('synthesis', {}).get('total_tokens', 0) +
                self.run_metrics.get('validation', {}).get('total_tokens', 0)
            )
            
            # Log totals
            mlflow.log_metric("total.duration_sec", elapsed)
            mlflow.log_metric("total.cost_usd", total_cost)
            mlflow.log_metric("total.tokens", total_tokens)
            mlflow.log_metric("total.success", 1.0 if success else 0.0)
            mlflow.log_metric("response.length", len(response))
            
            # Log status
            mlflow.set_tag("status", "success" if success else "failed")
            if error:
                mlflow.set_tag("error", error)
            
            # Log response as artifact (truncated)
            response_truncated = response[:5000] if len(response) > 5000 else response
            mlflow.log_text(response_truncated, "response.txt")
            
            # Log full metrics as JSON
            mlflow.log_dict(self.run_metrics, "metrics_summary.json")
            
            # End run
            mlflow.end_run()
            self.current_run = None
            
            print(f"✅ MLflow run completed: ${total_cost:.6f}, {elapsed:.2f}s, {total_tokens} tokens")
            
        except Exception as e:
            print(f"⚠️ Error ending MLflow run: {e}")
            try:
                mlflow.end_run(status="FAILED")
            except:
                pass
    
    # ========== LAKEHOUSE MONITORING ==========
    
    def setup_lakehouse_monitoring(self, 
                                   baseline_table: Optional[str] = None,
                                   schedule: str = "0 0 * * *"):  # Daily at midnight
        """
        Setup Lakehouse Monitoring on the governance table.
        
        Args:
            baseline_table: Optional baseline table for comparison
            schedule: Cron schedule for monitoring (default: daily)
            
        Returns:
            Monitor info or None if failed
        """
        if not self.enable_lakehouse_monitoring:
            print("⚠️ Lakehouse Monitoring disabled")
            return None
        
        try:
            print(f"\n🔍 Setting up Lakehouse Monitoring on {self.governance_table}...")
            
            # Check if monitor already exists
            try:
                existing_monitor = self.w.quality_monitors.get(table_name=self.governance_table)
                print(f"✅ Monitor already exists: {existing_monitor.monitor_version}")
                return existing_monitor
            except Exception:
                print("📊 Creating new monitor...")
            
            # Create monitor configuration
            from databricks.sdk.service.catalog import (
                MonitorInferenceLog,
                MonitorInferenceLogProblemType,
                MonitorMetric,
                MonitorMetricType
            )
            
            # Define custom metrics to track
            custom_metrics = [
                # Classification metrics
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="avg_classification_confidence",
                    input_columns=["classification_confidence"],
                    definition="AVG(classification_confidence)"
                ),
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="classification_method_distribution",
                    input_columns=["classification_method"],
                    definition="COUNT(*) GROUP BY classification_method"
                ),
                
                # Cost metrics
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="avg_cost_per_query",
                    input_columns=["cost"],
                    definition="AVG(cost)"
                ),
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="total_daily_cost",
                    input_columns=["cost"],
                    definition="SUM(cost)"
                ),
                
                # Validation metrics
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="validation_pass_rate",
                    input_columns=["judge_verdict"],
                    definition="SUM(CASE WHEN judge_verdict = 'Pass' THEN 1 ELSE 0 END) / COUNT(*)"
                ),
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="avg_validation_attempts",
                    input_columns=["validation_attempts"],
                    definition="AVG(validation_attempts)"
                ),
                
                # Performance metrics
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="avg_runtime_sec",
                    input_columns=["runtime_sec"],
                    definition="AVG(runtime_sec)"
                ),
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="p95_runtime_sec",
                    input_columns=["runtime_sec"],
                    definition="PERCENTILE(runtime_sec, 0.95)"
                ),
                
                # Error metrics
                MonitorMetric(
                    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
                    name="error_rate",
                    input_columns=["error_text"],
                    definition="SUM(CASE WHEN error_text IS NOT NULL AND error_text != '' THEN 1 ELSE 0 END) / COUNT(*)"
                ),
            ]
            
            # Create inference log config
            inference_log = MonitorInferenceLog(
                granularities=["1 day", "1 hour"],
                timestamp_col="event_timestamp",
                model_id_col="session_id",
                prediction_col="agent_response",
                problem_type=MonitorInferenceLogProblemType.PROBLEM_TYPE_CLASSIFICATION,
                label_col="judge_verdict"
            )
            
            # Create the monitor
            monitor = self.w.quality_monitors.create(
                table_name=self.governance_table,
                assets_dir=f"/Workspace/Users/{self.w.current_user.me().user_name}/superadvisor_monitoring",
                output_schema_name=UNITY_SCHEMA,
                schedule={"quartz_cron_expression": schedule, "timezone_id": "UTC"},
                inference_log=inference_log,
                custom_metrics=custom_metrics,
                baseline_table_name=baseline_table
            )
            
            print(f"✅ Lakehouse Monitor created successfully!")
            print(f"   Table: {self.governance_table}")
            print(f"   Version: {monitor.monitor_version}")
            print(f"   Schedule: {schedule}")
            print(f"   Metrics: {len(custom_metrics)} custom metrics")
            
            return monitor
            
        except Exception as e:
            print(f"❌ Error setting up Lakehouse Monitoring: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_monitoring_dashboard_url(self) -> Optional[str]:
        """
        Get the URL for the Lakehouse Monitoring dashboard.
        
        Returns:
            Dashboard URL or None
        """
        try:
            monitor = self.w.quality_monitors.get(table_name=self.governance_table)
            if monitor and monitor.dashboard_id:
                workspace_url = self.w.config.host
                return f"{workspace_url}/sql/dashboards/{monitor.dashboard_id}"
            return None
        except Exception as e:
            print(f"⚠️ Error getting dashboard URL: {e}")
            return None
    
    def refresh_monitoring_metrics(self) -> bool:
        """
        Manually trigger a refresh of monitoring metrics.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"🔄 Refreshing monitoring metrics for {self.governance_table}...")
            
            self.w.quality_monitors.run_refresh(table_name=self.governance_table)
            
            print("✅ Monitoring refresh triggered")
            return True
            
        except Exception as e:
            print(f"❌ Error refreshing monitoring: {e}")
            return False
    
    def get_monitoring_metrics(self, days: int = 7) -> Optional[Dict]:
        """
        Get monitoring metrics for the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary of metrics or None
        """
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_queries,
                AVG(cost) as avg_cost,
                SUM(cost) as total_cost,
                AVG(runtime_sec) as avg_runtime,
                PERCENTILE(runtime_sec, 0.95) as p95_runtime,
                SUM(CASE WHEN judge_verdict = 'Pass' THEN 1 ELSE 0 END) / COUNT(*) as validation_pass_rate,
                AVG(validation_attempts) as avg_validation_attempts,
                SUM(CASE WHEN error_text IS NOT NULL AND error_text != '' THEN 1 ELSE 0 END) / COUNT(*) as error_rate,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT country) as countries_served
            FROM {self.governance_table}
            WHERE event_timestamp >= CURRENT_DATE() - INTERVAL {days} DAYS
            """
            
            result = self.w.statement_execution.execute_statement(
                warehouse_id=SQL_WAREHOUSE_ID,
                statement=query,
                wait_timeout="30s"
            )
            
            if result.result and result.result.data_array:
                row = result.result.data_array[0]
                return {
                    'total_queries': row[0],
                    'avg_cost': float(row[1]) if row[1] else 0.0,
                    'total_cost': float(row[2]) if row[2] else 0.0,
                    'avg_runtime': float(row[3]) if row[3] else 0.0,
                    'p95_runtime': float(row[4]) if row[4] else 0.0,
                    'validation_pass_rate': float(row[5]) if row[5] else 0.0,
                    'avg_validation_attempts': float(row[6]) if row[6] else 0.0,
                    'error_rate': float(row[7]) if row[7] else 0.0,
                    'unique_users': row[8],
                    'countries_served': row[9]
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting monitoring metrics: {e}")
            return None
    
    def print_monitoring_summary(self, days: int = 7):
        """
        Print a summary of monitoring metrics.
        
        Args:
            days: Number of days to look back
        """
        metrics = self.get_monitoring_metrics(days)
        
        if not metrics:
            print("⚠️ No monitoring metrics available")
            return
        
        print("\n" + "=" * 70)
        print(f"📊 MONITORING SUMMARY (Last {days} Days)")
        print("=" * 70)
        print(f"\n📈 Volume:")
        print(f"  Total Queries: {metrics['total_queries']:,}")
        print(f"  Unique Users: {metrics['unique_users']:,}")
        print(f"  Countries Served: {metrics['countries_served']}")
        print(f"\n💰 Cost:")
        print(f"  Total Cost: ${metrics['total_cost']:.2f}")
        print(f"  Avg Cost/Query: ${metrics['avg_cost']:.4f}")
        print(f"\n⚡ Performance:")
        print(f"  Avg Runtime: {metrics['avg_runtime']:.2f}s")
        print(f"  P95 Runtime: {metrics['p95_runtime']:.2f}s")
        print(f"\n✅ Quality:")
        print(f"  Validation Pass Rate: {metrics['validation_pass_rate']*100:.1f}%")
        print(f"  Avg Validation Attempts: {metrics['avg_validation_attempts']:.2f}")
        print(f"  Error Rate: {metrics['error_rate']*100:.2f}%")
        print("=" * 70 + "\n")


# Convenience function for easy integration
def create_observability(enable_mlflow: bool = True, 
                        enable_lakehouse: bool = True) -> AgentObservability:
    """
    Create and return an AgentObservability instance.
    
    Args:
        enable_mlflow: Enable MLflow tracking
        enable_lakehouse: Enable Lakehouse Monitoring
        
    Returns:
        AgentObservability instance
    """
    return AgentObservability(
        enable_mlflow=enable_mlflow,
        enable_lakehouse_monitoring=enable_lakehouse
    )

