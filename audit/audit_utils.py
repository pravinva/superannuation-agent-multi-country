# audit/audit_utils.py
import uuid
import datetime
import pandas as pd
from pyspark.sql import SparkSession

# Unity Catalog configuration
CATALOG = "super_advisory_demo"
SCHEMA = "member_data"
TABLE = "governance"

def get_spark():
    """Get or create Spark session"""
    return SparkSession.builder.getOrCreate()

def log_query_event(
    user_id,
    country,
    query_string,
    cost,
    agent_response,
    result_preview,
    citations,
    tool_used,
    judge_response,
    judge_verdict,
    error_info,
    session_id=None
):
    """Log a query event to Unity Catalog governance table"""
    event_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow()

    # Create record
    record = {
        "event_id": event_id,
        "timestamp": timestamp,
        "user_id": user_id,
        "session_id": session_id or "",
        "country": country,
        "query_string": query_string,
        "agent_response": agent_response,
        "result_preview": result_preview,
        "cost": cost,
        "citations": citations if isinstance(citations, list) else [],
        "tool_used": tool_used,
        "judge_response": judge_response,
        "judge_verdict": judge_verdict,
        "error_info": error_info
    }

    try:
        spark = get_spark()
        df = spark.createDataFrame([record])
        df.write.format("delta").mode("append").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
    except Exception as e:
        print(f"Error logging to Unity Catalog: {e}")

def get_audit_log(session_id=None, user_id=None, country=None):
    """Retrieve audit logs from Unity Catalog"""
    try:
        spark = get_spark()
        query = f"SELECT * FROM {CATALOG}.{SCHEMA}.{TABLE}"

        conditions = []
        if session_id:
            conditions.append(f"session_id = '{session_id}'")
        if user_id:
            conditions.append(f"user_id = '{user_id}'")
        if country:
            conditions.append(f"country = '{country}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC"

        df = spark.sql(query)
        return df.toPandas()
    except Exception as e:
        print(f"Error retrieving audit log: {e}")
        return pd.DataFrame()

def get_query_cost(event_row):
    """Get cost for a specific query event"""
    return event_row.get("cost", 0.0) if isinstance(event_row, dict) else 0.0
