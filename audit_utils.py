# audit/audit_utils.py
"""Audit utilities - Uses Databricks SDK with auto warehouse discovery"""

import uuid
import datetime
import pandas as pd
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from config import get_governance_table_path

w = WorkspaceClient()

def get_serverless_warehouse():
    """Automatically find a serverless SQL warehouse"""
    warehouses = w.warehouses.list()
    for warehouse in warehouses:
        if warehouse.enable_serverless_compute and warehouse.state in ['RUNNING', 'STOPPED']:
            return warehouse.id
    for warehouse in warehouses:
        if warehouse.state in ['RUNNING', 'STOPPED']:
            return warehouse.id
    raise ValueError("No SQL warehouse available")

def execute_query(query):
    """Execute SQL query"""
    try:
        warehouse_id = get_serverless_warehouse()

        statement = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query,
            wait_timeout="30s"
        )

        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)

        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                columns = [col.name for col in statement.manifest.schema.columns]
                df = pd.DataFrame(statement.result.data_array, columns=columns)
                return df

        return pd.DataFrame()
    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame()

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
    """Log a query event to Unity Catalog GOVERNANCE table"""
    event_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat()

    try:
        table_path = get_governance_table_path()

        # Escape single quotes for SQL
        def escape(s):
            return str(s).replace("'", "''") if s else ""

        # Convert citations list to string
        citations_str = str(citations) if citations else "[]"

        query = f"""
        INSERT INTO {table_path} (
            event_id, timestamp, user_id, session_id, country, query_string,
            agent_response, result_preview, cost, citations, tool_used,
            judge_response, judge_verdict, error_info
        ) VALUES (
            '{event_id}',
            '{timestamp}',
            '{escape(user_id)}',
            '{escape(session_id)}',
            '{escape(country)}',
            '{escape(query_string)}',
            '{escape(agent_response)}',
            '{escape(result_preview)}',
            {cost},
            '{escape(citations_str)}',
            '{escape(tool_used)}',
            '{escape(judge_response)}',
            '{escape(judge_verdict)}',
            '{escape(error_info)}'
        )
        """

        execute_query(query)
        print(f"✓ Logged event {event_id[:8]}... to governance table")
    except Exception as e:
        print(f"Error logging to governance table: {e}")

def get_audit_log(session_id=None, user_id=None, country=None):
    """Retrieve audit logs from Unity Catalog GOVERNANCE table"""
    try:
        table_path = get_governance_table_path()
        query = f"SELECT * FROM {table_path}"

        conditions = []
        if session_id:
            conditions.append(f"session_id = '{session_id}'")
        if user_id:
            conditions.append(f"user_id = '{user_id}'")
        if country:
            conditions.append(f"country = '{country}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT 100"

        return execute_query(query)
    except Exception as e:
        print(f"Error retrieving audit log: {e}")
        return pd.DataFrame()

def get_query_cost(event_row):
    """Get cost for a specific query event"""
    return event_row.get("cost", 0.0) if isinstance(event_row, dict) else 0.0
