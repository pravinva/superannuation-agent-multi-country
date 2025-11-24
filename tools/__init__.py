"""Tools package for superannuation agent."""

import sys
import importlib.util
from pathlib import Path

# Import from tools.tool_executor (within this package)
from tools.tool_executor import UnifiedToolExecutor, create_executor

# Also expose SuperAdvisorTools from the root-level tools.py file
# This resolves the naming conflict between tools.py file and tools/ package
_tools_module_path = Path(__file__).parent.parent / 'tools.py'
if _tools_module_path.exists():
    _spec = importlib.util.spec_from_file_location("_root_tools", _tools_module_path)
    if _spec and _spec.loader:
        _root_tools = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_root_tools)
        SuperAdvisorTools = _root_tools.SuperAdvisorTools
        __all__ = ['UnifiedToolExecutor', 'create_executor', 'SuperAdvisorTools']
else:
    __all__ = ['UnifiedToolExecutor', 'create_executor']
