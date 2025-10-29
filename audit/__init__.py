# audit/__init__.py
from .audit_utils import log_query_event, get_audit_log, get_query_cost

__all__ = ['log_query_event', 'get_audit_log', 'get_query_cost']

