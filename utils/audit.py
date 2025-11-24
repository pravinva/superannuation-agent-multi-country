#!/usr/bin/env python3
"""
Audit Utilities - Query Logging & Governance

All audit and governance operations:
- Query event logging to Unity Catalog
- Citation formatting
- Governance result transformation
- Audit log retrieval
- Cost summary queries
"""

import json
import traceback
from typing import Optional, List, Dict, Any
from utils.lakehouse import execute_sql_statement, get_audit_logs as db_get_audit_logs, get_cost_summary as db_get_cost_summary
from shared.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# CORE AUDIT LOGGING
# ============================================================================

def log_query_event(
    user_id: str,
    session_id: str,
    country: str,
    query_string: str,
    response_text: Optional[str] = None,
    agent_response: Optional[str] = None,  # backward compatibility
    result_preview: Optional[str] = None,
    citations: Optional[List] = None,
    tool_used: Optional[str] = None,
    tools_called_count: Optional[int] = None,
    judge_response: Optional[str] = None,
    judge_verdict: Optional[str] = None,
    judge_confidence: Optional[float] = None,
    error_info: Optional[str] = None,
    cost: float = 0.0,
    validation_mode: str = "llm_judge",
    validation_attempts: int = 1,
    total_time_seconds: float = 0.0
):
    """
    Log query event to super_advisory_demo.member_data.governance table.
    
    Includes cost, timing, citations, and validation details.
    
    Args:
        user_id: Member/user identifier
        session_id: Session identifier
        country: Country code
        query_string: User's query
        response_text: Agent's response (preferred)
        agent_response: Agent's response (backward compatibility)
        result_preview: Preview of results
        citations: List of citations
        tool_used: Tools that were used
        tools_called_count: Number of tools called
        judge_response: Validation response
        judge_verdict: Pass/Fail verdict
        judge_confidence: Confidence score (0-1)
        error_info: Error information if any
        cost: Total cost in USD
        validation_mode: Validation strategy used
        validation_attempts: Number of validation attempts
        total_time_seconds: Total execution time
    """
    from config import SQL_WAREHOUSE_ID
    
    try:
        # Handle defaults and backward compatibility
        response_text = response_text or agent_response or ""
        result_preview = result_preview or ""
        tool_used = tool_used or ""
        judge_response = judge_response or ""
        judge_verdict = judge_verdict or ""
        error_info = error_info or ""
        validation_mode = validation_mode or "llm_judge"
        country = country or "Unknown"
        
        # Format citations
        citations_json = build_citation_json(citations)
        
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
            '{_escape_sql(user_id)}',
            '{_escape_sql(session_id)}',
            '{_escape_sql(country)}',
            '{_escape_sql(query_string)}',
            '{_escape_sql(response_text)}',
            '{_escape_sql(result_preview)}',
            {cost},
            '{_escape_sql(citations_json)}',
            '{_escape_sql(tool_used)}',
            '{_escape_sql(judge_response)}',
            '{_escape_sql(judge_verdict)}',
            {judge_confidence if judge_confidence is not None else 0.0},
            '{_escape_sql(error_info)}',
            '{_escape_sql(validation_mode)}',
            {validation_attempts},
            {total_time_seconds}
        )
        """

        execute_sql_statement(insert_sql, SQL_WAREHOUSE_ID)
        logger.info(f"✅ Logged event (country={country}, cost=${cost:.4f}, verdict={judge_verdict})")

    except Exception as e:
        logger.error(f"⚠️ Error logging governance event: {e}")
        traceback.print_exc()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def escape_sql(value: Any) -> str:
    """
    SQL-safe string escaping for use in SQL queries.
    
    Escapes single quotes by doubling them (SQL standard).
    
    Args:
        value: Value to escape (can be str, int, float, None, etc.)
        
    Returns:
        Escaped string (empty string if None)
    """
    if value is None:
        return ""
    return str(value).replace("'", "''")


# Keep _escape_sql for backward compatibility
_escape_sql = escape_sql


def build_citation_json(citations: Optional[List]) -> str:
    """
    Convert citations to JSON string for storage.
    
    Args:
        citations: List of citation dictionaries
        
    Returns:
        JSON string representation
    """
    try:
        if not citations:
            return "[]"
        return json.dumps(citations, ensure_ascii=False)
    except Exception:
        return "[]"


def transform_governance_result(row: Dict) -> Dict:
    """
    Convert raw UC record into summarized dict for display.
    
    Args:
        row: Raw governance table row
        
    Returns:
        Formatted dictionary for display
    """
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
        logger.error(f"⚠️ transform_governance_result error: {e}")
        return {}


# ============================================================================
# AUDIT LOG RETRIEVAL (delegates to database.py)
# ============================================================================

def get_audit_log(limit: int = 50) -> List[Dict]:
    """
    Fetch recent governance table entries.
    
    Wrapper around lakehouse.get_audit_logs() for backward compatibility.
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        List of audit log dictionaries
    """
    return db_get_audit_logs(limit)


def get_query_cost(limit: int = 100) -> List[Dict]:
    """
    Get aggregated cost summary per country or user.
    
    Wrapper around lakehouse.get_cost_summary() for backward compatibility.
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        List of cost summary dictionaries
    """
    return db_get_cost_summary(limit)

