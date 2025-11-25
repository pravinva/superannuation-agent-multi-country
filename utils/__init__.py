#!/usr/bin/env python3
"""
Utils Module - Consolidated Utilities

Clean, organized utilities for the SuperAdvisor Agent:

- lakehouse.py: Unity Catalog / Lakehouse operations
- progress.py: Beautiful progress tracking UI
- audit.py: Audit logging and governance

Usage:
    from utils.lakehouse import execute_sql_query, get_members_by_country
    from utils.progress import initialize_progress_tracker, mark_phase_complete
    from utils.audit import log_query_event
"""

# Lakehouse operations
from utils.lakehouse import (
    execute_sql_query,
    execute_sql_statement,
    get_member_by_id,
    get_members_by_country,
    get_citations,
    get_audit_logs,
    get_cost_summary
)

# Progress tracking
from utils.progress import (
    initialize_progress_tracker,
    reset_progress_tracker,
    mark_phase_running,
    mark_phase_complete,
    mark_phase_error
)

# Audit operations
from utils.audit import (
    log_query_event,
    build_citation_json,
    transform_governance_result,
    get_audit_log,
    get_query_cost
)

__all__ = [
    # Lakehouse
    'execute_sql_query',
    'execute_sql_statement',
    'get_member_by_id',
    'get_members_by_country',
    'get_citations',
    'get_audit_logs',
    'get_cost_summary',
    # Progress
    'initialize_progress_tracker',
    'reset_progress_tracker',
    'mark_phase_running',
    'mark_phase_complete',
    'mark_phase_error',
    # Audit
    'log_query_event',
    'build_citation_json',
    'transform_governance_result',
    'get_audit_log',
    'get_query_cost',
]

