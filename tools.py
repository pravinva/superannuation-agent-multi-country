# tools.py - WITH INTELLIGENT INDIVIDUAL TOOL CALLING AND CITATIONS

"""
Pension Calculator Tools - Intelligent Implementation

✅ NEW: Individual tool calling - Call tools one at a time
✅ NEW: Tools metadata - Describes each tool for planning
✅ Calls UC Functions in pension_calculators schema
✅ Fetches data from Unity Catalog tables
✅ Adds authoritative citations from registry
✅ Returns enriched responses for all 4 countries
✅ FIXED: Citation IDs match citation registry exactly

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
        
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                columns = [col.name for col in statement.manifest.schema.columns]
                rows = []
                for row_data in statement.result.data_array:
                    row = {}
                    for i, col_name in enumerate(columns):
                        row[col_name] = row_data[i]
                    rows.append(row)
                
                # Return as list of tuples for backward compatibility
                result_tuples = []
                for row in rows:
                    result_tuples.append(tuple(row.values()))
                return result_tuples
            return []
        else:
            print(f"Query failed: {statement.status.state}")
            return []
    except Exception as e:
        print(f"Error executing query: {e}")
        return []


def get_citations(citation_ids, warehouse_id):
    """
    Fetch detailed citations from citation registry by IDs
    ✅ FIXED: Properly query citation registry for specific IDs
    """
    if not citation_ids:
        return []
    
    # Build IN clause for SQL query
    ids_str = "', '".join(citation_ids)
    
    query = f"""
    SELECT 
        citation_id,
        authority,
        regulation_name,
        regulation_code,
        source_url,
        description
    FROM super_advisory_demo.member_data.citation_registry
    WHERE citation_id IN ('{ids_str}')
    ORDER BY citation_id
    """
    
    try:
        result = execute_query(warehouse_id, query)
        citations = []
        for row in result:
            citations.append({
                'citation_id': row[0],
                'authority': row[1],
                'regulation': f"{row[2]} ({row[3]})",
                'source_url': row[4],
                'description': row[5]
            })
        return citations
    except Exception as e:
        print(f"⚠️  Error fetching citations: {e}")
        return []


# ============================================================================
# COUNTRY-SPECIFIC TOOL IMPLEMENTATIONS
# ============================================================================

def _call_australia_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call individual Australia UC function"""
    start_time = time.time()
    
    if tool_id == "tax":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.au_calculate_tax(
          '{member_id}',
          {profile['age']},
          {profile.get('preservation_age', 60)},
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
                "citations": get_citations(['AU-TAX-001', 'AU-PRESERVATION-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "benefit":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.au_check_pension_impact(
          '{member_id}',
          {profile['age']},
          {profile['super_balance']},
          {profile.get('other_assets', 0)},
          '{profile.get('marital_status', 'Single')}',
          '{profile.get('home_ownership', 'Homeowner')}'
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
                "citations": get_citations(['AU-PENSION-001', 'AU-STANDARD-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "projection":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.au_project_balance(
          '{member_id}',
          {profile['age']},
          {profile['super_balance']},
          {profile.get('preservation_age', 60)},
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
                "citations": get_citations(['AU-STANDARD-001', 'AU-PRESERVATION-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    return {"error": f"Unknown tool_id: {tool_id}"}


def _call_usa_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call individual USA UC function - ✅ UPDATED WITH CORRECT CITATIONS"""
    start_time = time.time()
    
    if tool_id == "tax":
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
                "citations": get_citations(['US-TAX-001', 'US-PENALTY-001', 'US-IRA-001'], warehouse_id),  # ✅ UPDATED
                "duration": round(duration, 2)
            }
    
    elif tool_id == "benefit":
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
                "citations": get_citations(['US-SS-001'], warehouse_id),  # ✅ UPDATED
                "duration": round(duration, 2)
            }
    
    elif tool_id == "projection":
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
                "citations": get_citations(['US-TAX-001', 'US-RMD-001'], warehouse_id),  # ✅ UPDATED
                "duration": round(duration, 2)
            }
    
    return {"error": f"Unknown tool_id: {tool_id}"}


def _call_uk_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call individual UK UC function"""
    start_time = time.time()
    
    if tool_id == "tax":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
          '{member_id}',
          {profile['age']},
          {profile['super_balance']},
          {withdrawal_amount},
          'UFPLS'
        ) as result
        """
        result_raw = execute_query(warehouse_id, query)
        duration = time.time() - start_time
        
        if result_raw and len(result_raw) > 0:
            return {
                "tool_name": "HMRC Pension Tax Calculator",
                "tool_id": "tax",
                "uc_function": "super_advisory_demo.pension_calculators.uk_calculate_pension_tax",
                "authority": "HM Revenue & Customs",
                "calculation": result_raw[0][0],
                "citations": get_citations(['UK-TAX-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "benefit":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.uk_check_state_pension(
          '{member_id}',
          {profile['age']},
          35
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
                "citations": get_citations(['UK-PENSION-001', 'UK-AGE-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    elif tool_id == "projection":
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
                "citations": get_citations(['UK-DRAWDOWN-001', 'UK-TAX-001'], warehouse_id),
                "duration": round(duration, 2)
            }
    
    return {"error": f"Unknown tool_id: {tool_id}"}


def _call_india_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """Call individual India UC function - ✅ UPDATED WITH CORRECT CITATIONS"""
    start_time = time.time()
    
    if tool_id == "tax":
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
                "citations": get_citations(['IN-EPF-001', 'IN-TAX-001'], warehouse_id),  # ✅ UPDATED
                "duration": round(duration, 2)
            }
    
    elif tool_id == "benefit":
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
                "citations": get_citations(['IN-NPS-001', 'IN-NPS-RETURN-001'], warehouse_id),  # ✅ UPDATED
                "duration": round(duration, 2)
            }
    
    elif tool_id == "projection":
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
                "citations": get_citations(['IN-EPF-001', 'IN-INTEREST-001', 'IN-NPS-RETURN-001'], warehouse_id),  # ✅ UPDATED
                "duration": round(duration, 2)
            }
    
    return {"error": f"Unknown tool_id: {tool_id}"}


# ============================================================================
# PUBLIC API
# ============================================================================

def call_individual_tool(tool_id, member_id, withdrawal_amount, country, warehouse_id):
    """
    Call a single UC function based on tool_id and country
    
    Args:
        tool_id: "tax", "benefit", or "projection"
        member_id: Member identifier
        withdrawal_amount: Amount to calculate (for tax tools)
        country: Country name
        warehouse_id: SQL warehouse ID
        
    Returns:
        dict: Tool result with calculation, citations, and metadata
    """
    from data_utils import get_member_by_id
    
    profile = get_member_by_id(member_id)
    if not profile:
        return {"error": f"Member {member_id} not found"}
    
    country_dispatch = {
        "Australia": _call_australia_tool,
        "USA": _call_usa_tool,
        "United Kingdom": _call_uk_tool,
        "India": _call_india_tool
    }
    
    tool_func = country_dispatch.get(country)
    if not tool_func:
        return {"error": f"Unsupported country: {country}"}
    
    return tool_func(tool_id, member_id, profile, withdrawal_amount, warehouse_id)


def get_all_tools_metadata(country):
    """
    Get metadata for all available tools in a country
    Used by agent's planning phase to decide which tools to call
    ✅ UPDATED: Citation IDs now match citation registry
    """
    metadata_by_country = {
        "Australia": [
            {
                "id": "tax",
                "name": "ATO Tax Calculator",
                "description": "Calculates withdrawal tax based on age and preservation age",
                "uc_function": "super_advisory_demo.pension_calculators.au_calculate_tax",
                "authority": "Australian Taxation Office",
                "citation_ids": ["AU-TAX-001", "AU-PRESERVATION-001"]
            },
            {
                "id": "benefit",
                "name": "Centrelink Age Pension Calculator",
                "description": "Checks government pension eligibility and impact",
                "uc_function": "super_advisory_demo.pension_calculators.au_check_pension_impact",
                "authority": "Department of Social Services",
                "citation_ids": ["AU-PENSION-001", "AU-STANDARD-001"]
            },
            {
                "id": "projection",
                "name": "Superannuation Projection Engine",
                "description": "Projects future balance over time",
                "uc_function": "super_advisory_demo.pension_calculators.au_project_balance",
                "authority": "ASFA / APRA",
                "citation_ids": ["AU-STANDARD-001", "AU-PRESERVATION-001"]
            }
        ],
        "USA": [
            {
                "id": "tax",
                "name": "IRS 401(k) Tax Calculator",
                "description": "Calculates federal tax on 401(k) withdrawals",
                "uc_function": "super_advisory_demo.pension_calculators.us_calculate_tax",
                "authority": "Internal Revenue Service",
                "citation_ids": ["US-TAX-001", "US-PENALTY-001", "US-IRA-001"]  # ✅ UPDATED
            },
            {
                "id": "benefit",
                "name": "Social Security Benefits Calculator",
                "description": "Checks Social Security eligibility and amounts",
                "uc_function": "super_advisory_demo.pension_calculators.us_check_social_security",
                "authority": "Social Security Administration",
                "citation_ids": ["US-SS-001"]  # ✅ UPDATED
            },
            {
                "id": "projection",
                "name": "401(k) Projection Engine",
                "description": "Projects 401(k) growth and RMDs",
                "uc_function": "super_advisory_demo.pension_calculators.us_project_401k",
                "authority": "Department of Labor / IRS",
                "citation_ids": ["US-TAX-001", "US-RMD-001"]  # ✅ UPDATED
            }
        ],
        "United Kingdom": [
            {
                "id": "tax",
                "name": "HMRC Pension Tax Calculator",
                "description": "Calculates UK pension tax and tax-free lump sum",
                "uc_function": "super_advisory_demo.pension_calculators.uk_calculate_pension_tax",
                "authority": "HM Revenue & Customs",
                "citation_ids": ["UK-TAX-001"]
            },
            {
                "id": "benefit",
                "name": "State Pension Calculator",
                "description": "Checks State Pension eligibility and amounts",
                "uc_function": "super_advisory_demo.pension_calculators.uk_check_state_pension",
                "authority": "Department for Work and Pensions",
                "citation_ids": ["UK-PENSION-001", "UK-AGE-001"]
            },
            {
                "id": "projection",
                "name": "UK Pension Projection Engine",
                "description": "Projects pension growth and drawdown",
                "uc_function": "super_advisory_demo.pension_calculators.uk_project_pension",
                "authority": "Pensions Regulator / FCA",
                "citation_ids": ["UK-DRAWDOWN-001", "UK-TAX-001"]
            }
        ],
        "India": [
            {
                "id": "tax",
                "name": "EPF Tax Calculator",
                "description": "Calculates tax on EPF withdrawals",
                "uc_function": "super_advisory_demo.pension_calculators.in_calculate_epf_tax",
                "authority": "Income Tax Department",
                "citation_ids": ["IN-EPF-001", "IN-TAX-001"]  # ✅ UPDATED
            },
            {
                "id": "benefit",
                "name": "NPS Benefits Calculator",
                "description": "Calculates NPS benefits and annuity",
                "uc_function": "super_advisory_demo.pension_calculators.in_calculate_nps",
                "authority": "Pension Fund Regulatory Authority",
                "citation_ids": ["IN-NPS-001", "IN-NPS-RETURN-001"]  # ✅ UPDATED
            },
            {
                "id": "projection",
                "name": "EPF/NPS Projection Engine",
                "description": "Projects EPF/NPS growth to retirement",
                "uc_function": "super_advisory_demo.pension_calculators.in_project_retirement",
                "authority": "EPFO / PFRDA",
                "citation_ids": ["IN-EPF-001", "IN-INTEREST-001", "IN-NPS-RETURN-001"]  # ✅ UPDATED
            }
        ]
    }
    
    return metadata_by_country.get(country, metadata_by_country["Australia"])
