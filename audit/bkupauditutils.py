# audit/audit_utils.py - COMPLETE FIXED VERSION
"""
Audit logging with proper parameter handling
✅ FIXED: Added limit parameter to get_audit_log()
"""

import uuid
import datetime
import pandas as pd
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from config import get_governance_table_path, SQL_WAREHOUSE_ID

w = WorkspaceClient()

def get_warehouse_id():
    """Get warehouse ID from config"""
    if not SQL_WAREHOUSE_ID or SQL_WAREHOUSE_ID == "YOUR_WAREHOUSE_ID_HERE":
        raise ValueError("Please set SQL_WAREHOUSE_ID in config.py")
    return SQL_WAREHOUSE_ID

def execute_query(query):
    """Execute SQL query"""
    try:
        warehouse_id = get_warehouse_id()
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
    session_id,
    country,
    query_string,
    agent_response,
    result_preview,
    citations,
    tool_used,
    judge_response,
    judge_verdict,
    error_info,
    cost=0.0,
    validation_mode="llm_judge",
    validation_attempts=1,
    total_time_seconds=0.0
):
    """
    Log query event to governance table
    
    Args:
        user_id: User identifier
        session_id: Session UUID
        country: Country name (Australia, USA, United Kingdom, India)
        query_string: User's query
        agent_response: Full LLM response
        result_preview: Summary/preview of result
        citations: List of citations
        tool_used: Name of tool/calculator used
        judge_response: Judge LLM response
        judge_verdict: Pass/Reject/Review/ERROR
        error_info: Error details if any
        cost: Cost of query (default 0.0)
        validation_mode: Validation strategy used (llm_judge/hybrid/deterministic)
        validation_attempts: Number of retry attempts
        total_time_seconds: Total processing time in seconds
    """
    
    event_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat()
    
    try:
        table_path = get_governance_table_path()
        
        def escape(s):
            """Escape single quotes for SQL"""
            if s is None:
                return ""
            return str(s).replace("'", "''").replace("\\", "\\\\")
        
        # Convert citations to string
        if isinstance(citations, list):
            citations_str = str(citations)
        else:
            citations_str = str(citations) if citations else "[]"
        
        # Truncate long responses
        if agent_response and len(agent_response) > 15000:
            agent_response = agent_response[:15000] + "... [truncated]"
        
        query = f"""
INSERT INTO {table_path} (
    event_id, timestamp, user_id, session_id, country, query_string,
    agent_response, result_preview, cost, citations, tool_used,
    judge_response, judge_verdict, error_info,
    validation_mode, validation_attempts, total_time_seconds
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
    '{escape(error_info)}',
    '{escape(validation_mode)}',
    {validation_attempts},
    {total_time_seconds}
)
"""
        
        execute_query(query)
        print(f"✓ Logged event {event_id[:8]} to governance table")
        print(f"  Mode: {validation_mode}, Attempts: {validation_attempts}, Time: {total_time_seconds:.2f}s")
        
    except Exception as e:
        print(f"❌ Error logging to governance table: {e}")
        import traceback
        traceback.print_exc()


def get_audit_log(session_id=None, user_id=None, country=None, limit=100):
    """
    ✅ FIXED: Added limit parameter with default value
    
    Retrieve audit logs with optional filters
    
    Args:
        session_id: Filter by session ID
        user_id: Filter by user ID
        country: Filter by country
        limit: Maximum number of records to return (default: 100)
    
    Returns:
        DataFrame with audit records
    """
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
        
        # ✅ FIXED: Use limit parameter instead of hardcoded value
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        return execute_query(query)
    
    except Exception as e:
        print(f"Error retrieving audit log: {e}")
        return pd.DataFrame()


def get_query_cost(event_row):
    """Get cost for a specific query event"""
    return event_row.get("cost", 0.0) if isinstance(event_row, dict) else 0.0
