# tools.py - Tool Execution Logic (NOT a utility!)

# ✅ REFACTORED: Eliminated 90% duplication for AU/US/UK
# ✅ Uses UnifiedToolExecutor for AU/US/UK (config-driven)
# ✅ India (IN) preserved with special EPF/NPS handling
# ✅ Integrated with centralized logging
# ✅ Error handling for failed UC functions
# ✅ Now uses utils.lakehouse for SQL execution

from config import SQL_WAREHOUSE_ID
from utils.lakehouse import execute_sql_statement, get_citations
from tools.tool_executor import UnifiedToolExecutor, ToolExecutionError, ToolConfigurationError
from shared.logging_config import get_logger
import time

# ============================================================================
# NOTE: This file contains DOMAIN LOGIC for tool execution
# It is NOT a utility file - it implements business logic for
# retirement calculations across different countries
# ============================================================================

# Initialize logger
logger = get_logger(__name__)

# Initialize unified executor for AU/US/UK
_unified_executor = None

def _get_unified_executor(warehouse_id: str) -> UnifiedToolExecutor:
    """
    Get or create unified tool executor instance.

    Args:
        warehouse_id: SQL warehouse ID

    Returns:
        UnifiedToolExecutor instance
    """
    global _unified_executor
    if _unified_executor is None or _unified_executor.warehouse_id != warehouse_id:
        _unified_executor = UnifiedToolExecutor(warehouse_id=warehouse_id, logger=logger)
        logger.debug("Initialized UnifiedToolExecutor")
    return _unified_executor

# ============================================================================
# AUSTRALIA, USA, UK TOOLS - UNIFIED IMPLEMENTATION
# ============================================================================

def _call_au_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """
    Call Australia UC functions using unified executor.

    Delegated to UnifiedToolExecutor for configuration-driven execution.
    """
    executor = _get_unified_executor(warehouse_id)
    try:
        return executor.execute_tool(
            country="AU",
            tool_id=tool_id,
            member_id=member_id,
            profile=profile,
            withdrawal_amount=withdrawal_amount
        )
    except (ToolExecutionError, ToolConfigurationError) as e:
        logger.error(f"AU tool execution failed: {e}")
        return {"error": str(e)}


def _call_us_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """
    Call USA UC functions using unified executor.

    Delegated to UnifiedToolExecutor for configuration-driven execution.
    """
    executor = _get_unified_executor(warehouse_id)
    try:
        return executor.execute_tool(
            country="US",
            tool_id=tool_id,
            member_id=member_id,
            profile=profile,
            withdrawal_amount=withdrawal_amount
        )
    except (ToolExecutionError, ToolConfigurationError) as e:
        logger.error(f"US tool execution failed: {e}")
        return {"error": str(e)}


def _call_uk_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """
    Call UK UC functions using unified executor.

    Delegated to UnifiedToolExecutor for configuration-driven execution.
    """
    executor = _get_unified_executor(warehouse_id)
    try:
        return executor.execute_tool(
            country="UK",
            tool_id=tool_id,
            member_id=member_id,
            profile=profile,
            withdrawal_amount=withdrawal_amount
        )
    except (ToolExecutionError, ToolConfigurationError) as e:
        logger.error(f"UK tool execution failed: {e}")
        return {"error": str(e)}

# ============================================================================
# INDIA TOOLS - WITH EPF/NPS SPLIT TRANSPARENCY
# ============================================================================

def _call_in_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call India UC functions - WITH EXPLICIT EPF/NPS SPLIT REPORTING"""
    start_time = time.time()
    
    # 🆕 CRITICAL FIX: Convert ALL strings to numbers FIRST
    try:
        age = int(float(str(profile.get('age', 0))))
        total_balance = float(str(profile.get('super_balance', 0)).replace(',', ''))
        withdrawal_amount_num = float(str(withdrawal_amount).replace(',', '')) if withdrawal_amount else 0.0

        years_of_service_raw = profile.get('years_of_service')
        if years_of_service_raw:
            years_of_service = int(float(str(years_of_service_raw)))
        else:
            years_of_service = max(age - 25, 0)

    except (ValueError, TypeError) as e:
        logger.error(f"Type conversion error in _call_in_tool: {e}")
        return {"error": f"Invalid data types: {e}"}
    
    # ✅ SPLIT: 75% EPF (mandatory) / 25% NPS (voluntary)
    epf_balance = total_balance * 0.75
    nps_balance = total_balance * 0.25
    
    # 🆕 NEW: Add split information to ALL India tool results
    balance_split_info = {
        "total_balance": total_balance,
        "epf_balance": epf_balance,
        "nps_balance": nps_balance,
        "split_note": "India retirement corpus is split: 75% EPF (mandatory provident fund) + 25% NPS (voluntary pension scheme)"
    }
    
    if tool_id == "tax":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.in_calculate_epf_tax(
            '{member_id}', {age}, {epf_balance}, {withdrawal_amount_num}
        ) as result
        """
        tool_config = ('EPF Tax Calculator', 'in_calculate_epf_tax',
                      'Income Tax Department', ['IN-EPF-001', 'IN-TAX-001'])
        calculation_note = f"Tax calculated on EPF portion: {epf_balance:,.2f} INR (75% of total)"
    
    elif tool_id == "benefit":
        annuity_pct = max(profile.get("annuity_purchase_pct", 40), 40)
        pension_rate = profile.get("monthly_pension_rate", 6)
        query = f"""
        SELECT super_advisory_demo.pension_calculators.in_calculate_nps_benefits(
            '{member_id}',
            {nps_balance},
            {annuity_pct},
            {pension_rate},
            {age}
        ) AS result
        """
        tool_config = ('NPS Benefits Calculator', 'in_calculate_nps_benefits',
                      'PFRDA', ['IN-NPS-001'])
        calculation_note = f"NPS benefits calculated on: {nps_balance:,.2f} INR (25% of total)"
    
    elif tool_id == "eps_benefit":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.in_calculate_eps_benefits(
            '{member_id}',
            {age},
            {epf_balance},
            {years_of_service}
        ) AS result
        """
        tool_config = ('EPS Benefits Calculator', 'in_calculate_eps_benefits',
                      "Employees' Provident Fund Organisation (EPFO)", ['IN-EPS-001'])
        calculation_note = f"EPS pension calculated on EPF portion: {epf_balance:,.2f} INR (75% of total)"
    
    elif tool_id == "projection":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.in_project_retirement_corpus(
            '{member_id}', {age}, {total_balance}, {withdrawal_amount_num}, 20
        ) as result
        """
        tool_config = ('Retirement Corpus Projection', 'in_project_retirement_corpus',
                      'EPFO', ['IN-INTEREST-001'])
        calculation_note = f"Projection based on total balance: {total_balance:,.2f} INR"
    
    else:
        return {"error": f"Unknown tool_id: {tool_id}"}
    
    result = execute_sql_statement(query, warehouse_id)
    duration = time.time() - start_time
    
    if not result or not result.result or not result.result.data_array:
        return {"error": f"No result from in_{tool_id}"}
    
    calculation = result.result.data_array[0][0]
    name, func, auth, citations_ids = tool_config
    
    # 🆕 NEW: Return enhanced result with balance split transparency
    return {
        "tool_name": name,
        "tool_id": tool_id,
        "uc_function": func,
        "authority": auth,
        "calculation": str(calculation),
        "calculation_note": calculation_note,  # NEW: Explains which balance was used
        "balance_split": balance_split_info,   # NEW: Full split breakdown
        "citations": get_citations(citations_ids, warehouse_id),
        "duration": round(duration, 2)
    }

# ============================================================================
# PUBLIC API
# ============================================================================

def call_individual_tool(tool_id, member_id, withdrawal_amount, country, warehouse_id):
    """Call a single UC function - FIXED for all countries"""
    from utils.lakehouse import get_member_by_id
    
    profile = get_member_by_id(member_id)
    if not profile or "error" in profile:
        return {"error": f"Member {member_id} not found"}
    
    country_dispatch = {
        "AU": _call_au_tool,
        "US": _call_us_tool,
        "UK": _call_uk_tool,
        "IN": _call_in_tool,
        "Australia": _call_au_tool,
        "USA": _call_us_tool,
        "United Kingdom": _call_uk_tool,
        "India": _call_in_tool
    }
    
    country_upper = country.upper() if isinstance(country, str) else country
    tool_func = country_dispatch.get(country_upper) or country_dispatch.get(country)
    
    if not tool_func:
        return {"error": f"Unsupported country: {country}"}
    
    return tool_func(tool_id, member_id, profile, withdrawal_amount, warehouse_id)

# ============================================================================
# SUPER ADVISOR TOOLS CLASS (FOR AGENT.PY COMPATIBILITY)
# ============================================================================

class SuperAdvisorTools:
    """Tool wrapper for agent.py compatibility"""

    def __init__(self, warehouse_id=None):
        self.warehouse_id = warehouse_id or SQL_WAREHOUSE_ID
        logger.info("SuperAdvisorTools initialized")

    def get_member_profile(self, member_id):
        """Get member profile"""
        from utils.lakehouse import get_member_by_id
        return get_member_by_id(member_id)

    def call_tool(self, tool_id, member_id, withdrawal_amount, country):
        """Call a tool - PRIMARY METHOD FOR AGENTS"""
        result = call_individual_tool(tool_id, member_id, withdrawal_amount, country, self.warehouse_id)

        if "error" in result:
            logger.error(f"Tool '{tool_id}' error: {result['error']}")
        else:
            logger.info(f"Tool '{tool_id}' executed successfully")

        return result

