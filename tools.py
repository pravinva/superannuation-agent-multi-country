# tools.py - PRODUCTION READY WITH EPF/NPS SPLIT TRANSPARENCY

# ✅ Fixed: All type conversion errors resolved
# ✅ All 4 countries: AU, US, UK, IN
# ✅ NEW: India tools explicitly show EPF/NPS balance split
# ✅ All citations loaded from registry
# ✅ Error handling for failed UC functions

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from config import SQL_WAREHOUSE_ID
import time

w = WorkspaceClient()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def execute_query(warehouse_id, query):
    """Execute SQL query via Databricks SDK"""
    try:
        statement = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query,
            wait_timeout="30s"
        )
        
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            return statement
        else:
            print(f"Query failed: {statement.status.state}")
            return None
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def get_citations(citation_ids, warehouse_id):
    """Fetch citations from registry"""
    if not citation_ids:
        return []
    
    ids_str = "', '".join(citation_ids)
    query = f"""
    SELECT 
        citation_id, authority, regulation_name, regulation_code,
        source_url, description
    FROM super_advisory_demo.member_data.citation_registry
    WHERE citation_id IN ('{ids_str}')
    ORDER BY citation_id
    """
    
    try:
        result = execute_query(warehouse_id, query)
        if not result or not result.result or not result.result.data_array:
            return []
        
        citations = []
        for row in result.result.data_array:
            citations.append({
                'citation_id': row[0],
                'authority': row[1],
                'regulation': f"{row[2]} ({row[3]})",
                'source_url': row[4],
                'description': row[5]
            })
        return citations
    except Exception as e:
        print(f"⚠️ Error fetching citations: {e}")
        return []

# ============================================================================
# AUSTRALIA TOOLS
# ============================================================================

def _call_au_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call Australia UC functions"""
    start_time = time.time()
    
    if tool_id == "tax":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.au_calculate_tax(
            '{member_id}', {profile['age']}, {profile.get('preservation_age', 60)},
            {profile['super_balance']}, {withdrawal_amount}
        ) as result
        """
    
    elif tool_id == "benefit":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.au_check_pension_impact(
            '{member_id}', {profile['age']}, {profile['super_balance']},
            {profile.get('other_assets', 0)}, '{profile.get('marital_status', 'Single')}',
            'Homeowner'
        ) as result
        """
    
    elif tool_id == "projection":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.au_project_balance(
            '{member_id}', {profile['age']}, {profile['super_balance']},
            {profile.get('preservation_age', 60)}, 20
        ) as result
        """
    
    else:
        return {"error": f"Unknown tool_id: {tool_id}"}
    
    result = execute_query(warehouse_id, query)
    duration = time.time() - start_time
    
    if not result or not result.result or not result.result.data_array:
        return {"error": f"No result from au_{tool_id}"}
    
    calculation = result.result.data_array[0][0]
    
    tool_config = {
        'tax': ('ATO Tax Calculator', 'au_calculate_tax', 'Australian Taxation Office', ['AU-TAX-001']),
        'benefit': ('Centrelink Calculator', 'au_check_pension_impact', 'Department of Social Services', ['AU-PENSION-001']),
        'projection': ('Superannuation Projection', 'au_project_balance', 'ASFA', ['AU-STANDARD-001'])
    }
    
    name, func, auth, citations_ids = tool_config[tool_id]
    
    return {
        "tool_name": name,
        "tool_id": tool_id,
        "uc_function": func,
        "authority": auth,
        "calculation": str(calculation),
        "citations": get_citations(citations_ids, warehouse_id),
        "duration": round(duration, 2)
    }

# ============================================================================
# USA TOOLS
# ============================================================================

def _call_us_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call USA UC functions"""
    start_time = time.time()
    
    if tool_id == "tax":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.us_calculate_401k_tax(
            '{member_id}', '401k', {withdrawal_amount}, {profile['age']}
        ) as result
        """
    
    elif tool_id == "benefit":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.us_check_social_security(
            '{member_id}', {profile['age']}, '{profile.get('marital_status', 'Single')}',
            {profile['super_balance']}
        ) as result
        """
    
    elif tool_id == "projection":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.us_project_401k_balance(
            '{member_id}', {profile['age']}, 67, {profile['super_balance']}, 10000, 20
        ) as result
        """
    
    else:
        return {"error": f"Unknown tool_id: {tool_id}"}
    
    result = execute_query(warehouse_id, query)
    duration = time.time() - start_time
    
    if not result or not result.result or not result.result.data_array:
        return {"error": f"No result from us_{tool_id}"}
    
    calculation = result.result.data_array[0][0]
    
    tool_config = {
        'tax': ('IRS 401(k) Tax Calculator', 'us_calculate_401k_tax', 'Internal Revenue Service', ['US-TAX-001', 'US-PENALTY-001']),
        'benefit': ('Social Security Calculator', 'us_check_social_security', 'Social Security Administration', ['US-SS-001']),
        'projection': ('401(k) Projection', 'us_project_401k_balance', 'Department of Labor', ['US-RMD-001'])
    }
    
    name, func, auth, citations_ids = tool_config[tool_id]
    
    return {
        "tool_name": name,
        "tool_id": tool_id,
        "uc_function": func,
        "authority": auth,
        "calculation": str(calculation),
        "citations": get_citations(citations_ids, warehouse_id),
        "duration": round(duration, 2)
    }

# ============================================================================
# UK TOOLS
# ============================================================================

def _call_uk_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call UK UC functions"""
    start_time = time.time()
    
    if tool_id == "tax":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
            '{member_id}', {profile['age']}, {profile['super_balance']}, {withdrawal_amount}, 'standard'
        ) as result
        """
    
    elif tool_id == "benefit":
        ni_years = profile.get("ni_qualifying_years", 35)
        marital_status = profile.get("marital_status", "married")
        query = f"""
        SELECT super_advisory_demo.pension_calculators.uk_check_state_pension(
            '{member_id}',
            {profile['age']},
            {ni_years},
            '{marital_status}'
        ) AS result
        """
    
    elif tool_id == "projection":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.uk_project_pension_balance(
            '{member_id}', {profile['age']}, {profile['super_balance']}, {withdrawal_amount}, 20
        ) as result
        """
    
    else:
        return {"error": f"Unknown tool_id: {tool_id}"}
    
    result = execute_query(warehouse_id, query)
    duration = time.time() - start_time
    
    if not result or not result.result or not result.result.data_array:
        return {"error": f"No result from uk_{tool_id}"}
    
    calculation = result.result.data_array[0][0]
    
    tool_config = {
        'tax': ('HMRC Pension Tax Calculator', 'uk_calculate_pension_tax', 'HM Revenue & Customs', ['UK-TAX-001']),
        'benefit': ('State Pension Calculator', 'uk_check_state_pension', 'Department for Work and Pensions', ['UK-PENSION-001']),
        'projection': ('UK Pension Projection', 'uk_project_pension_balance', 'FCA', ['UK-DRAWDOWN-001'])
    }
    
    name, func, auth, citations_ids = tool_config[tool_id]
    
    return {
        "tool_name": name,
        "tool_id": tool_id,
        "uc_function": func,
        "authority": auth,
        "calculation": str(calculation),
        "citations": get_citations(citations_ids, warehouse_id),
        "duration": round(duration, 2)
    }

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
        print(f"❌ Type conversion error in _call_in_tool: {e}")
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
    
    result = execute_query(warehouse_id, query)
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
    from data_utils import get_member_by_id
    
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
        print(f"✓ SuperAdvisorTools initialized")
    
    def get_member_profile(self, member_id):
        """Get member profile"""
        from data_utils import get_member_by_id
        return get_member_by_id(member_id)
    
    def call_tool(self, tool_id, member_id, withdrawal_amount, country):
        """Call a tool - PRIMARY METHOD FOR AGENTS"""
        result = call_individual_tool(tool_id, member_id, withdrawal_amount, country, self.warehouse_id)
        
        if "error" in result:
            print(f"❌ Tool '{tool_id}' error: {result['error']}")
        else:
            print(f"✓ Tool '{tool_id}' executed successfully")
        
        return result

