# audit_utils.py – Backward Compatible | Updated for UC logging

from databricks.sdk import WorkspaceClient
from config import SQL_WAREHOUSE_ID
import json
import traceback

w = WorkspaceClient()

# =====================================================
# CORE AUDIT LOGGING
# =====================================================

def log_query_event(
    user_id,
    session_id,
    country,
    query_string,
    response_text=None,          # ✅ preferred version
    agent_response=None,         # ✅ backward compatibility
    result_preview=None,
    citations=None,
    tool_used=None,
    tools_called_count=None,
    judge_response=None,
    judge_verdict=None,
    judge_confidence=None,
    error_info=None,
    cost=0.0,                    # ✅ ensures cost passed in from agent.py
    validation_mode="llm_judge",
    validation_attempts=1,
    total_time_seconds=0.0
):
    """
    Log each query to super_advisory_demo.member_data.governance (UC table).
    Includes cost, timing, citations, and validation details.
    Compatible with existing schema and prior imports.
    """
    try:
        response_text = response_text or agent_response or ""
        result_preview = result_preview or ""
        tool_used = tool_used or ""
        judge_response = judge_response or ""
        judge_verdict = judge_verdict or ""
        error_info = error_info or ""
        validation_mode = validation_mode or "llm_judge"
        country = country or "Unknown"

        citations_json = json.dumps(citations) if citations else "[]"

        # Simple SQL-safe escaping
        def escape_sql(value):
            if value is None:
                return ""
            return str(value).replace("'", "''")

        # Build the SQL
        insert_sql = f"""
        INSERT INTO super_advisory_demo.member_data.governance (
            event_id, timestamp, user_id, session_id, country, query_string,
            agent_response, result_preview, cost, citations, tool_used,
            judge_response, judge_verdict, judge_confidence,
            error_info, validation_mode, validation_attempts, total_time_seconds
        )
        VALUES (
            uuid(),
            current_timestamp(),
            '{escape_sql(user_id)}',
            '{escape_sql(session_id)}',
            '{escape_sql(country)}',
            '{escape_sql(query_string)}',
            '{escape_sql(response_text)}',
            '{escape_sql(result_preview)}',
            {cost},
            '{escape_sql(citations_json)}',
            '{escape_sql(tool_used)}',
            '{escape_sql(judge_response)}',
            '{escape_sql(judge_verdict)}',
            {judge_confidence if judge_confidence is not None else 0.0},
            '{escape_sql(error_info)}',
            '{escape_sql(validation_mode)}',
            {validation_attempts},
            {total_time_seconds}
        )
        """

        w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=insert_sql,
            wait_timeout="30s"
        )
        print(f"✅ Logged event (country={country}, cost=${cost:.4f}, verdict={judge_verdict})")

    except Exception as e:
        print(f"⚠️ Error logging governance event: {e}")
        traceback.print_exc()


# =====================================================
# RESULT + SUMMARY FUNCTIONS
# =====================================================

def build_citation_json(citations):
    """Convert citations to JSON string for storage."""
    try:
        if not citations:
            return "[]"
        return json.dumps(citations, ensure_ascii=False)
    except Exception:
        return "[]"


def transform_governance_result(row):
    """Convert raw UC record into summarized dict for display."""
    try:
        return {
            "event_id": row.get("event_id"),
            "timestamp": row.get("timestamp"),
            "user_id": row.get("user_id"),
            "country": row.get("country"),
            "query": row.get("query_string", "")[:500],
            "cost": round(float(row.get("cost", 0.0)), 6),
            "citations": json.loads(row.get("citations") or "[]"),
            "verdict": row.get("judge_verdict"),
            "time_seconds": float(row.get("total_time_seconds", 0)),
        }
    except Exception as e:
        print(f"⚠️ transform_governance_result error: {e}")
        return {}


def get_audit_log(limit: int = 50):
    """
    Compatibility alias for old get_audit_log.
    Fetches recent governance table entries.
    """
    try:
        sql = f"""
        SELECT *
        FROM super_advisory_demo.member_data.governance
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        statement = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=sql,
            wait_timeout="30s"
        )
        result = statement.result.data_array
        keys = [c.name for c in statement.manifest.schema.columns]
        formatted = [dict(zip(keys, r)) for r in result]
        return formatted
    except Exception as e:
        print(f"⚠️ get_audit_log() could not fetch governance logs: {e}")
        return []


def get_query_cost(limit: int = 100):
    """
    Compatibility alias for old get_query_cost.
    Returns aggregated compute costs per country or user.
    """
    try:
        sql = f"""
        SELECT
            country,
            user_id,
            ROUND(SUM(cost), 4) AS total_cost,
            COUNT(*) AS query_count,
            ROUND(AVG(cost), 6) AS avg_cost
        FROM super_advisory_demo.member_data.governance
        GROUP BY country, user_id
        ORDER BY total_cost DESC
        LIMIT {limit}
        """
        statement = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=sql,
            wait_timeout="30s"
        )
        result = statement.result.data_array
        keys = [c.name for c in statement.manifest.schema.columns]
        formatted = [dict(zip(keys, r)) for r in result]
        return formatted
    except Exception as e:
        print(f"⚠️ get_query_cost() could not compute cost summary: {e}")
        return []

