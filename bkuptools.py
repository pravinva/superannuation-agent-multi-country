# tools.py - WITH INTELLIGENT INDIVIDUAL TOOL CALLING
"""
Pension Calculator Tools - Intelligent Implementation
✅ NEW: Individual tool calling - Call tools one at a time
✅ NEW: Tools metadata - Describes each tool for planning
✅ Calls UC Functions in pension_calculators schema
✅ Fetches data from Unity Catalog tables
✅ Adds authoritative citations from registry
✅ Returns enriched responses for all 4 countries

KEY IMPROVEMENT: Agent can now call individual tools instead of all 3 at once
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from config import SQL_WAREHOUSE_ID
import time

w = WorkspaceClient()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def execute_query(warehouse_id, query):
    """Execute SQL query via Databricks SDK and return results"""
    try:
        statement = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query,
            wait_timeout="30s"
        )
        
        # Poll for completion
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                return statement.result.data_array
        
        return None
        
    except Exception as e:
        print(f"Error executing query: {e}")
        return None


def get_member_profile(member_id, warehouse_id):
    """Fetch member profile data from Unity Catalog"""
    query = f"""
        SELECT 
            name, 
            age, 
            preservation_age,
            super_balance,
            other_assets,
            marital_status,
            employment_status,
            dependents,
            country
        FROM super_advisory_demo.member_data.member_profiles
        WHERE member_id = '{member_id}'
    """
    
    result = execute_query(warehouse_id, query)
    
    if result and len(result) > 0:
        row = result[0]
        return {
            'name': str(row[0]) if row[0] else 'Unknown',
            'age': int(row[1]) if row[1] else 0,
            'preservation_age': int(row[2]) if row[2] else 60,
            'super_balance': float(row[3]) if row[3] else 0.0,
            'other_assets': float(row[4]) if row[4] else 0.0,
            'marital_status': str(row[5]) if row[5] else 'Single',
            'employment_status': str(row[6]) if row[6] else 'Unknown',
            'dependents': int(row[7]) if row[7] else 0,
            'country': str(row[8]) if row[8] else 'Australia'
        }
    
    return None


def get_citations(citation_ids, warehouse_id):
    """Fetch authoritative citations from registry table"""
    if not citation_ids:
        return []
    
    ids_str = "', '".join(citation_ids)
    query = f"""
        SELECT 
            authority,
            regulation_name,
            regulation_code,
            source_url,
            description
        FROM super_advisory_demo.member_data.citation_registry
        WHERE citation_id IN ('{ids_str}')
        ORDER BY citation_id
    """
    
    result = execute_query(warehouse_id, query)
    
    if result:
        citations = []
        for row in result:
            citation_text = f"{row[0]} - {row[1]}"
            if row[2]:
                citation_text += f" ({row[2]})"
            
            citations.append({
                "text": citation_text,
                "url": row[3] if row[3] else "",
                "description": row[4] if row[4] else ""
            })
        return citations
    
    return []


# ============================================================================
# ✅ NEW: TOOLS METADATA FOR PLANNING
# ============================================================================

def get_all_tools_metadata(country):
    """
    Get metadata for all available tools in a country
    Used by agent's planning phase to decide which tools to call
    
    Args:
        country: Country name
    
    Returns:
        list of dicts with tool metadata
    """
    
    metadata_by_country = {
        "Australia": [
            {
                "id": "tax",
                "name": "ATO Tax Calculator",
                "description": "Calculates withdrawal tax based on age and preservation age. Use for: tax questions, withdrawal amounts, net income.",
                "uc_function": "super_advisory_demo.pension_calculators.au_calculate_tax",
                "authority": "Australian Taxation Office",
                "citation_ids": ["AU-TAX-001"]
            },
            {
                "id": "benefit",
                "name": "Centrelink Age Pension Calculator",
                "description": "Checks government pension eligibility and impact. Use for: Age Pension questions, Centrelink benefits, means testing.",
                "uc_function": "super_advisory_demo.pension_calculators.au_check_pension_impact",
                "authority": "Department of Social Services",
                "citation_ids": ["AU-PENSION-001"]
            },
            {
                "id": "projection",
                "name": "Superannuation Projection Engine",
                "description": "Projects future balance over time. Use for: retirement planning, longevity questions, balance projections.",
                "uc_function": "super_advisory_demo.pension_calculators.au_project_balance",
                "authority": "ASFA / APRA",
                "citation_ids": ["AU-STANDARD-001"]
            }
        ],
        "USA": [
            {
                "id": "tax",
                "name": "IRS 401(k) Tax Calculator",
                "description": "Calculates federal tax on 401(k) withdrawals. Use for: tax questions, withdrawal penalties, early withdrawal.",
                "uc_function": "super_advisory_demo.pension_calculators.us_calculate_tax",
                "authority": "Internal Revenue Service",
                "citation_ids": ["US-TAX-001"]
            },
            {
                "id": "benefit",
                "name": "Social Security Benefits Calculator",
                "description": "Checks Social Security eligibility and amounts. Use for: Social Security questions, benefit calculations, retirement age.",
                "uc_function": "super_advisory_demo.pension_calculators.us_check_social_security",
                "authority": "Social Security Administration",
                "citation_ids": ["US-SSA-001"]
            },
            {
                "id": "projection",
                "name": "401(k) Projection Engine",
                "description": "Projects 401(k) growth and RMDs. Use for: retirement planning, Required Minimum Distributions, future balance.",
                "uc_function": "super_advisory_demo.pension_calculators.us_project_401k",
                "authority": "Department of Labor / IRS",
                "citation_ids": ["US-DOL-001"]
            }
        ],
        "United Kingdom": [
            {
                "id": "tax",
                "name": "HMRC Pension Tax Calculator",
                "description": "Calculates UK pension tax and tax-free lump sum. Use for: tax questions, 25% lump sum, PAYE.",
                "uc_function": "super_advisory_demo.pension_calculators.uk_calculate_tax",
                "authority": "HM Revenue & Customs",
                "citation_ids": ["UK-TAX-001"]
            },
            {
                "id": "benefit",
                "name": "State Pension Calculator",
                "description": "Checks State Pension eligibility and amounts. Use for: State Pension questions, National Insurance, eligibility.",
                "uc_function": "super_advisory_demo.pension_calculators.uk_check_state_pension",
                "authority": "Department for Work and Pensions",
                "citation_ids": ["UK-DWP-001"]
            },
            {
                "id": "projection",
                "name": "UK Pension Projection Engine",
                "description": "Projects pension growth and drawdown. Use for: retirement planning, pension pot projections, drawdown strategies.",
                "uc_function": "super_advisory_demo.pension_calculators.uk_project_pension",
                "authority": "Pensions Regulator / FCA",
                "citation_ids": ["UK-TPR-001"]
            }
        ],
        "India": [
            {
                "id": "tax",
                "name": "EPF Tax Calculator",
                "description": "Calculates tax on EPF withdrawals. Use for: EPF tax questions, premature withdrawal, Form 15G/15H.",
                "uc_function": "super_advisory_demo.pension_calculators.in_calculate_epf_tax",
                "authority": "Income Tax Department",
                "citation_ids": ["IN-TAX-001"]
            },
            {
                "id": "benefit",
                "name": "NPS Benefits Calculator",
                "description": "Calculates NPS benefits and annuity. Use for: NPS questions, pension calculations, Tier I/II accounts.",
                "uc_function": "super_advisory_demo.pension_calculators.in_calculate_nps",
                "authority": "Pension Fund Regulatory Authority",
                "citation_ids": ["IN-PFRDA-001"]
            },
            {
                "id": "projection",
                "name": "EPF/NPS Projection Engine",
                "description": "Projects EPF/NPS growth to retirement. Use for: retirement planning, corpus projections, retirement age.",
                "uc_function": "super_advisory_demo.pension_calculators.in_project_retirement",
                "authority": "EPFO / PFRDA",
                "citation_ids": ["IN-EPFO-001"]
            }
        ]
    }
    
    return metadata_by_country.get(country, metadata_by_country["Australia"])


# ============================================================================
# ✅ NEW: INDIVIDUAL TOOL CALLING FUNCTIONS
# ============================================================================

def call_individual_tool(tool_id, member_id, withdrawal_amount, country, warehouse_id):
    """
    Call a single UC function tool
    
    Args:
        tool_id: "tax", "benefit", or "projection"
        member_id: Member identifier
        withdrawal_amount: Withdrawal amount
        country: Country name
        warehouse_id: SQL Warehouse ID
    
    Returns:
        dict with calculation result, duration, and metadata
    """
    
    # Get member profile
    profile = get_member_profile(member_id, warehouse_id)
    
    if not profile:
        return {"error": "Member not found"}
    
    # Route to country-specific function
    country_functions = {
        "Australia": _call_australia_tool,
        "USA": _call_usa_tool,
        "United Kingdom": _call_uk_tool,
        "India": _call_india_tool
    }
    
    func = country_functions.get(country)
    if not func:
        return {"error": f"Country {country} not supported"}
    
    return func(tool_id, member_id, profile, withdrawal_amount, warehouse_id)


# ============================================================================
# AUSTRALIA INDIVIDUAL TOOLS
# ============================================================================

def _call_australia_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call individual Australia UC function"""
    
    start_time = time.time()
    
    if tool_id == "tax":
        # ATO Tax Calculator
        query = f"""
            SELECT super_advisory_demo.pension_calculators.au_calculate_tax(
                '{member_id}',
                {profile['age']},
                {profile['preservation_age']},
                {profile['super_balance']},
                {withdrawal_amount}
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "ATO Tax Calculator",
                "tool_id": "tax",
                "uc_function": "super_advisory_demo.pension_calculators.au_calculate_tax",
                "authority": "Australian Taxation Office",
                "calculation": result_raw[0][0],
                "citations": get_citations(['AU-TAX-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "benefit":
        # Centrelink Age Pension
        query = f"""
            SELECT super_advisory_demo.pension_calculators.au_check_pension_impact(
                '{member_id}',
                {profile['age']},
                '{profile['marital_status']}',
                {profile['super_balance']},
                {profile['other_assets']},
                {withdrawal_amount}
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "Centrelink Age Pension Calculator",
                "tool_id": "benefit",
                "uc_function": "super_advisory_demo.pension_calculators.au_check_pension_impact",
                "authority": "Department of Social Services",
                "calculation": result_raw[0][0],
                "citations": get_citations(['AU-PENSION-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "projection":
        # Retirement Projection
        query = f"""
            SELECT super_advisory_demo.pension_calculators.au_project_balance(
                '{member_id}',
                {profile['age']},
                {profile['preservation_age']},
                {profile['super_balance']},
                20
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "Superannuation Projection Engine",
                "tool_id": "projection",
                "uc_function": "super_advisory_demo.pension_calculators.au_project_balance",
                "authority": "ASFA / APRA",
                "calculation": result_raw[0][0],
                "citations": get_citations(['AU-STANDARD-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    return {"error": f"Unknown tool_id: {tool_id}"}
# tools_INTELLIGENT_part2.py - USA, UK, India individual tools
# This is part 2 - append to part 1

# ============================================================================
# USA INDIVIDUAL TOOLS
# ============================================================================

def _call_usa_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call individual USA UC function"""
    
    start_time = time.time()
    
    if tool_id == "tax":
        # IRS 401(k) Tax
        query = f"""
            SELECT super_advisory_demo.pension_calculators.us_calculate_tax(
                '{member_id}',
                {profile['age']},
                {profile['super_balance']},
                {withdrawal_amount}
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "IRS 401(k) Tax Calculator",
                "tool_id": "tax",
                "uc_function": "super_advisory_demo.pension_calculators.us_calculate_tax",
                "authority": "Internal Revenue Service",
                "calculation": result_raw[0][0],
                "citations": get_citations(['US-TAX-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "benefit":
        # Social Security
        query = f"""
            SELECT super_advisory_demo.pension_calculators.us_check_social_security(
                '{member_id}',
                {profile['age']},
                '{profile['marital_status']}',
                {profile['super_balance']}
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "Social Security Benefits Calculator",
                "tool_id": "benefit",
                "uc_function": "super_advisory_demo.pension_calculators.us_check_social_security",
                "authority": "Social Security Administration",
                "calculation": result_raw[0][0],
                "citations": get_citations(['US-SSA-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "projection":
        # 401(k) Projection
        query = f"""
            SELECT super_advisory_demo.pension_calculators.us_project_401k(
                '{member_id}',
                {profile['age']},
                {profile['super_balance']},
                20
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "401(k) Projection Engine",
                "tool_id": "projection",
                "uc_function": "super_advisory_demo.pension_calculators.us_project_401k",
                "authority": "Department of Labor / IRS",
                "calculation": result_raw[0][0],
                "citations": get_citations(['US-DOL-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    return {"error": f"Unknown tool_id: {tool_id}"}


# ============================================================================
# UK INDIVIDUAL TOOLS
# ============================================================================

def _call_uk_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call individual UK UC function"""
    
    start_time = time.time()
    
    if tool_id == "tax":
        # HMRC Tax
        query = f"""
            SELECT super_advisory_demo.pension_calculators.uk_calculate_tax(
                '{member_id}',
                {profile['age']},
                {profile['super_balance']},
                {withdrawal_amount}
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "HMRC Pension Tax Calculator",
                "tool_id": "tax",
                "uc_function": "super_advisory_demo.pension_calculators.uk_calculate_tax",
                "authority": "HM Revenue & Customs",
                "calculation": result_raw[0][0],
                "citations": get_citations(['UK-TAX-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "benefit":
        # State Pension
        query = f"""
            SELECT super_advisory_demo.pension_calculators.uk_check_state_pension(
                '{member_id}',
                {profile['age']},
                '{profile['marital_status']}',
                {profile['super_balance']}
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "State Pension Calculator",
                "tool_id": "benefit",
                "uc_function": "super_advisory_demo.pension_calculators.uk_check_state_pension",
                "authority": "Department for Work and Pensions",
                "calculation": result_raw[0][0],
                "citations": get_citations(['UK-DWP-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "projection":
        # Pension Projection
        query = f"""
            SELECT super_advisory_demo.pension_calculators.uk_project_pension(
                '{member_id}',
                {profile['age']},
                {profile['super_balance']},
                20
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "UK Pension Projection Engine",
                "tool_id": "projection",
                "uc_function": "super_advisory_demo.pension_calculators.uk_project_pension",
                "authority": "Pensions Regulator / FCA",
                "calculation": result_raw[0][0],
                "citations": get_citations(['UK-TPR-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    return {"error": f"Unknown tool_id: {tool_id}"}


# ============================================================================
# INDIA INDIVIDUAL TOOLS
# ============================================================================

def _call_india_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call individual India UC function"""
    
    start_time = time.time()
    
    if tool_id == "tax":
        # EPF Tax
        query = f"""
            SELECT super_advisory_demo.pension_calculators.in_calculate_epf_tax(
                '{member_id}',
                {profile['age']},
                {profile['super_balance']},
                {withdrawal_amount}
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "EPF Tax Calculator",
                "tool_id": "tax",
                "uc_function": "super_advisory_demo.pension_calculators.in_calculate_epf_tax",
                "authority": "Income Tax Department",
                "calculation": result_raw[0][0],
                "citations": get_citations(['IN-TAX-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "benefit":
        # NPS Benefits
        query = f"""
            SELECT super_advisory_demo.pension_calculators.in_calculate_nps(
                '{member_id}',
                {profile['age']},
                {profile['super_balance']}
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "NPS Benefits Calculator",
                "tool_id": "benefit",
                "uc_function": "super_advisory_demo.pension_calculators.in_calculate_nps",
                "authority": "Pension Fund Regulatory Authority",
                "calculation": result_raw[0][0],
                "citations": get_citations(['IN-PFRDA-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "projection":
        # Retirement Projection
        query = f"""
            SELECT super_advisory_demo.pension_calculators.in_project_retirement(
                '{member_id}',
                {profile['age']},
                {profile['super_balance']},
                20
            ) as result
        """
        
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "EPF/NPS Projection Engine",
                "tool_id": "projection",
                "uc_function": "super_advisory_demo.pension_calculators.in_project_retirement",
                "authority": "EPFO / PFRDA",
                "calculation": result_raw[0][0],
                "citations": get_citations(['IN-EPFO-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    return {"error": f"Unknown tool_id: {tool_id}"}


# ============================================================================
# ✅ BACKWARD COMPATIBILITY: Full calculator functions (if needed)
# ============================================================================

def calculate_retirement_advice(member_id, withdrawal_amount, country, warehouse_id=None):
    """
    Backward compatible function - calls all 3 tools
    
    Use call_individual_tool() for intelligent selection instead
    
    Args:
        member_id: Member identifier
        withdrawal_amount: Proposed withdrawal amount
        country: Country name
        warehouse_id: Optional SQL Warehouse ID
    
    Returns:
        dict with all 3 calculations
    """
    
    if warehouse_id is None:
        warehouse_id = SQL_WAREHOUSE_ID
    
    # Call all 3 tools
    results = {}
    tools_called = []
    all_citations = []
    
    for tool_id in ["tax", "benefit", "projection"]:
        result = call_individual_tool(
            tool_id=tool_id,
            member_id=member_id,
            withdrawal_amount=withdrawal_amount,
            country=country,
            warehouse_id=warehouse_id
        )
        
        if result and "error" not in result:
            results[tool_id] = result["calculation"]
            tools_called.append({
                "name": result["tool_name"],
                "authority": result.get("authority", ""),
                "uc_function": result["uc_function"],
                "status": "completed",
                "duration": result["duration"]
            })
            if "citations" in result:
                all_citations.extend(result["citations"])
    
    return {
        "country": country,
        "member_id": member_id,
        "calculations": results,
        "tools_called": tools_called,
        "citations": all_citations
    }


# ============================================================================
# ROUTER FUNCTION (backward compatibility)
# ============================================================================

def get_pension_calculator(country):
    """
    Backward compatibility - returns function that calls all 3 tools
    
    For new intelligent approach, use call_individual_tool() instead
    """
    def full_calculator(member_id, withdrawal_amount, warehouse_id):
        return calculate_retirement_advice(member_id, withdrawal_amount, country, warehouse_id)
    
    return full_calculator
