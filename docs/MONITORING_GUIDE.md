# Lakehouse Monitoring Setup Guide

## Overview

The system uses Databricks Lakehouse Monitoring to track agent performance, cost, quality, and operational metrics over time. Monitoring is configured through the `observability.py` module and tracks data stored in the governance table.

## Architecture

Lakehouse Monitoring monitors the `governance` table in Unity Catalog, which stores every query execution record with:
- Query metadata (user, country, session)
- Execution metrics (cost, latency, tokens)
- Classification results (method, confidence)
- Validation results (verdict, confidence, attempts)
- Tool usage and citations
- Error information

## Initial Setup

### Prerequisites

1. Unity Catalog enabled workspace
2. Governance table created (`super_advisory_demo.member_data.governance`)
3. Databricks SQL Warehouse configured
4. Appropriate permissions for creating monitors

### Create Monitor

```python
from observability import create_observability

obs = create_observability(
    enable_mlflow=True,
    enable_lakehouse_monitoring=True
)

monitor = obs.setup_lakehouse_monitoring(
    baseline_table=None,  # Optional baseline for drift detection
    schedule="0 0 * * *"  # Daily at midnight UTC
)
```

### Monitor Configuration

**Schedule Format:** Cron expression (quartz format)
- `"0 0 * * *"` - Daily at midnight UTC
- `"0 */6 * * *"` - Every 6 hours
- `"0 0 * * 0"` - Weekly on Sunday

**Baseline Table:** Optional table for drift detection. If provided, monitoring compares current data distribution against baseline.

## Custom Metrics

The monitor tracks the following custom metrics:

### Classification Metrics

- `avg_classification_confidence`: Average confidence score from classifier
- `classification_method_distribution`: Distribution of classification methods (regex, embedding, llm)

### Cost Metrics

- `avg_cost_per_query`: Average cost per query in USD
- `total_daily_cost`: Total cost aggregated per day

### Validation Metrics

- `validation_pass_rate`: Percentage of queries that passed LLM validation
- `avg_validation_attempts`: Average number of validation attempts per query

### Performance Metrics

- `avg_runtime_sec`: Average query execution time
- `p95_runtime_sec`: 95th percentile runtime

### Error Metrics

- `error_rate`: Percentage of queries with errors

## Monitor Output

The monitor creates the following outputs:

1. **Monitoring Dashboard:** SQL dashboard accessible via Databricks UI
2. **Monitoring Views:** Aggregated views in Unity Catalog schema
3. **Alerts:** Automated alerts based on metric thresholds (if configured)

## Accessing Monitoring Data

### Get Dashboard URL

```python
dashboard_url = obs.get_monitoring_dashboard_url()
print(f"Dashboard: {dashboard_url}")
```

### Get Metrics Summary

```python
metrics = obs.get_monitoring_metrics(days=7)
print(f"Total Queries: {metrics['total_queries']}")
print(f"Avg Cost: ${metrics['avg_cost']:.4f}")
print(f"Pass Rate: {metrics['validation_pass_rate']*100:.1f}%")
```

### Print Summary

```python
obs.print_monitoring_summary(days=7)
```

## Manual Refresh

Trigger a manual refresh of monitoring metrics:

```python
success = obs.refresh_monitoring_metrics()
```

## Monitoring Views

The system creates monitoring views for easy querying:

### Daily Aggregations

```sql
SELECT * FROM super_advisory_demo.member_data.governance_monitoring
WHERE date >= CURRENT_DATE - INTERVAL 7 DAYS
ORDER BY date DESC;
```

### Hourly Aggregations

```sql
SELECT * FROM super_advisory_demo.member_data.governance_monitoring_hourly
WHERE hour >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
ORDER BY hour DESC;
```

## Alert Configuration

Configure alerts in the Databricks UI:

1. Navigate to the monitoring dashboard
2. Click "Add Alert" on any metric
3. Set threshold (e.g., error_rate > 0.05)
4. Configure notification channel (email, Slack, etc.)

**Common Alert Thresholds:**

- Error rate > 5%
- Average cost > $0.01 per query
- Validation pass rate < 90%
- P95 latency > 10 seconds

## Troubleshooting

### Monitor Not Created

**Error:** "Monitor creation failed"

**Solutions:**
- Verify Unity Catalog permissions
- Check governance table exists and is accessible
- Ensure SQL warehouse is available
- Review error message for specific issue

### Metrics Not Updating

**Symptoms:** Dashboard shows stale data

**Solutions:**
- Check monitor schedule is correct
- Manually trigger refresh: `obs.refresh_monitoring_metrics()`
- Verify governance table has recent data
- Check monitor status in Databricks UI

### Dashboard Not Accessible

**Error:** "Dashboard URL not found"

**Solutions:**
- Verify monitor was created successfully
- Check monitor status: `w.quality_monitors.get(table_name=...)`
- Ensure dashboard permissions are configured
- Recreate monitor if necessary

## Integration with Streamlit UI

The monitoring metrics are displayed in the Streamlit governance UI (`ui_monitoring_tabs.py`):

- **Real-Time Metrics:** Current performance indicators
- **Classification Analytics:** Stage distribution and cost savings
- **Quality Monitoring:** Validation pass rates and confidence distributions
- **Cost Analysis:** Detailed cost breakdowns and trends

The UI queries the governance table directly and aggregates metrics client-side for real-time display.

## Best Practices

1. **Baseline Establishment:** Create a baseline table after initial deployment to track drift over time

2. **Schedule Optimization:** Use daily schedules for production, hourly for development/testing

3. **Alert Thresholds:** Set conservative thresholds initially and adjust based on production patterns

4. **Retention:** Monitor governance table size and implement retention policies if needed

5. **Review Regularly:** Review monitoring dashboard weekly to identify trends and anomalies

## Custom Metrics

To add custom metrics, modify `setup_lakehouse_monitoring()` in `observability.py`:

```python
MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
    name="custom_metric_name",
    input_columns=["column_name"],
    definition="AVG(column_name)"  # SQL aggregate expression
)
```

## Monitoring vs MLflow

**Lakehouse Monitoring:**
- Time-series metrics and trends
- Automated alerts and dashboards
- Data quality and drift detection
- Aggregated views for reporting

**MLflow:**
- Per-query execution tracking
- Prompt versioning and model registry
- Detailed artifacts and logs
- Experiment tracking and comparisons

Both systems complement each other: MLflow tracks individual executions, while Lakehouse Monitoring provides aggregated insights over time.

