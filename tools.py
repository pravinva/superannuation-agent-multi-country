# tools.py
"""
Pension Calculator Tools - Complete Implementation
Calls UC Functions in pension_calculators schema
Fetches data from Unity Catalog tables
Adds authoritative citations from registry
Returns enriched responses for all 4 countries
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
# AUSTRALIA CALCULATORS (3 functions)
# ============================================================================

def calculate_super_australia(member_id, withdrawal_amount, warehouse_id):
    """
    Australia Superannuation Calculator - Calls 3 UC Functions
    
    Functions called:
    1. au_calculate_tax - ATO tax calculation
    2. au_check_pension_impact - Centrelink Age Pension
    3. au_project_balance - Retirement projection
    
    Args:
        member_id: Member identifier
        withdrawal_amount: Proposed withdrawal in AUD
        warehouse_id: SQL Warehouse ID
    
    Returns:
        dict with calculations, citations, and metadata
    """
    
    overall_start = time.time()
    
    # Step 1: Fetch member profile
    profile = get_member_profile(member_id, warehouse_id)
    
    if not profile:
        return {
            "error": "Member not found",
            "country": "Australia",
            "member_id": member_id
        }
    
    tools_called = []
    
    # Step 2: Call UC Function - ATO Tax Calculator
    tax_start = time.time()
    tax_query = f"""
        SELECT super_advisory_demo.pension_calculators.au_calculate_tax(
            '{member_id}',
            {profile['age']},
            {profile['preservation_age']},
            {profile['super_balance']},
            {withdrawal_amount}
        ) as result
    """
    
    tax_result_raw = execute_query(warehouse_id, tax_query)
    tax_duration = time.time() - tax_start
    
    if tax_result_raw and len(tax_result_raw) > 0:
        tax_result = tax_result_raw[0][0]
        
        tools_called.append({
            "name": "ATO Tax Calculator",
            "authority": "Australian Taxation Office",
            "uc_function": "super_advisory_demo.pension_calculators.au_calculate_tax",
            "status": "completed",
            "duration": round(tax_duration, 2)
        })
    else:
        tax_result = None
    
    # Step 3: Call UC Function - Centrelink Age Pension
    pension_start = time.time()
    pension_query = f"""
        SELECT super_advisory_demo.pension_calculators.au_check_pension_impact(
            '{member_id}',
            {profile['age']},
            '{profile['marital_status']}',
            {profile['super_balance']},
            {profile['other_assets']},
            {withdrawal_amount}
        ) as result
    """
    
    pension_result_raw = execute_query(warehouse_id, pension_query)
    pension_duration = time.time() - pension_start
    
    if pension_result_raw and len(pension_result_raw) > 0:
        pension_result = pension_result_raw[0][0]
        
        tools_called.append({
            "name": "Centrelink Age Pension Calculator",
            "authority": "Department of Social Services",
            "uc_function": "super_advisory_demo.pension_calculators.au_check_pension_impact",
            "status": "completed",
            "duration": round(pension_duration, 2)
        })
    else:
        pension_result = None
    
    # Step 4: Call UC Function - Retirement Projection
    projection_start = time.time()
    projection_query = f"""
        SELECT super_advisory_demo.pension_calculators.au_project_balance(
            '{member_id}',
            {profile['age']},
            {profile['preservation_age']},
            {profile['super_balance']},
            20
        ) as result
    """
    
    projection_result_raw = execute_query(warehouse_id, projection_query)
    projection_duration = time.time() - projection_start
    
    if projection_result_raw and len(projection_result_raw) > 0:
        projection_result = projection_result_raw[0][0]
        
        tools_called.append({
            "name": "Superannuation Projection Engine",
            "authority": "ASFA / APRA",
            "uc_function": "super_advisory_demo.pension_calculators.au_project_balance",
            "status": "completed",
            "duration": round(projection_duration, 2)
        })
    else:
        projection_result = None
    
    # Step 5: Fetch authoritative citations
    citations = get_citations(['AU-TAX-001', 'AU-PENSION-001', 'AU-STANDARD-001'], warehouse_id)
    
    total_duration = time.time() - overall_start
    
    # Step 6: Build enriched response
    return {
        "country": "Australia",
        "member_id": member_id,
        "member_name": profile['name'],
        "member_age": profile['age'],
        "withdrawal_amount": withdrawal_amount,
        
        # Tax calculation results
        "tax_calculation": tax_result,
        
        # Pension impact results
        "pension_impact": pension_result,
        
        # Projection results
        "retirement_projection": projection_result,
        
        # Citations (never made up!)
        "citations": citations,
        
        # Metadata for progress tracking
        "tools_called": tools_called,
        "data_source": "super_advisory_demo.member_data.member_profiles",
        "citation_source": "super_advisory_demo.member_data.citation_registry",
        "total_duration": round(total_duration, 2)
    }


# ============================================================================
# USA CALCULATORS (3 functions)
# ============================================================================

def calculate_401k_usa(member_id, withdrawal_amount, warehouse_id):
    """
    USA 401(k) Calculator - Calls 3 UC Functions
    
    Functions called:
    1. us_calculate_401k_tax - 401(k)/IRA tax with penalties
    2. us_check_social_security - Social Security benefits
    3. us_project_retirement_balance - Balance projection with RMD
    
    Args:
        member_id: Member identifier
        withdrawal_amount: Proposed withdrawal in USD
        warehouse_id: SQL Warehouse ID
    
    Returns:
        dict with calculations, citations, and metadata
    """
    
    overall_start = time.time()
    
    # Fetch member profile
    profile = get_member_profile(member_id, warehouse_id)
    
    if not profile:
        return {
            "error": "Member not found",
            "country": "USA",
            "member_id": member_id
        }
    
    tools_called = []
    
    # Function 1: 401(k) Tax Calculator
    tax_start = time.time()
    # Assume 401k as default account type - could be parameter
    tax_query = f"""
        SELECT super_advisory_demo.pension_calculators.us_calculate_401k_tax(
            '{member_id}',
            {profile['age']},
            {profile['super_balance']},
            {withdrawal_amount},
            '401k'
        ) as result
    """
    
    tax_result_raw = execute_query(warehouse_id, tax_query)
    tax_duration = time.time() - tax_start
    
    if tax_result_raw and len(tax_result_raw) > 0:
        tax_result = tax_result_raw[0][0]
        tools_called.append({
            "name": "401(k) Tax Calculator",
            "authority": "Internal Revenue Service",
            "uc_function": "super_advisory_demo.pension_calculators.us_calculate_401k_tax",
            "status": "completed",
            "duration": round(tax_duration, 2)
        })
    else:
        tax_result = None
    
    # Function 2: Social Security Calculator
    ss_start = time.time()
    # Assume average monthly earnings of $3000 and claiming at 67
    ss_query = f"""
        SELECT super_advisory_demo.pension_calculators.us_check_social_security(
            '{member_id}',
            {profile['age']},
            3000.0,
            67,
            {profile['super_balance'] * 0.04}
        ) as result
    """
    
    ss_result_raw = execute_query(warehouse_id, ss_query)
    ss_duration = time.time() - ss_start
    
    if ss_result_raw and len(ss_result_raw) > 0:
        ss_result = ss_result_raw[0][0]
        tools_called.append({
            "name": "Social Security Calculator",
            "authority": "Social Security Administration",
            "uc_function": "super_advisory_demo.pension_calculators.us_check_social_security",
            "status": "completed",
            "duration": round(ss_duration, 2)
        })
    else:
        ss_result = None
    
    # Function 3: Retirement Balance Projection
    proj_start = time.time()
    proj_query = f"""
        SELECT super_advisory_demo.pension_calculators.us_project_retirement_balance(
            '{member_id}',
            {profile['age']},
            {profile['super_balance']},
            0,
            65,
            20
        ) as result
    """
    
    proj_result_raw = execute_query(warehouse_id, proj_query)
    proj_duration = time.time() - proj_start
    
    if proj_result_raw and len(proj_result_raw) > 0:
        proj_result = proj_result_raw[0][0]
        tools_called.append({
            "name": "Retirement Balance Projection",
            "authority": "IRS (SECURE 2.0 Act)",
            "uc_function": "super_advisory_demo.pension_calculators.us_project_retirement_balance",
            "status": "completed",
            "duration": round(proj_duration, 2)
        })
    else:
        proj_result = None
    
    # Fetch citations
    citations = get_citations(['US-TAX-001', 'US-PENALTY-001', 'US-SS-001', 'US-RMD-001'], warehouse_id)
    
    return {
        "country": "USA",
        "member_id": member_id,
        "member_name": profile['name'],
        "member_age": profile['age'],
        "withdrawal_amount": withdrawal_amount,
        "tax_calculation": tax_result,
        "social_security": ss_result,
        "retirement_projection": proj_result,
        "citations": citations,
        "tools_called": tools_called,
        "data_source": "super_advisory_demo.member_data.member_profiles",
        "total_duration": round(time.time() - overall_start, 2)
    }


# ============================================================================
# UK CALCULATORS (3 functions)
# ============================================================================

def calculate_uk_pension(member_id, withdrawal_amount, warehouse_id):
    """
    UK Pension Calculator - Calls 3 UC Functions
    
    Functions called:
    1. uk_calculate_pension_tax - Pension tax with 25% tax-free
    2. uk_check_state_pension - State Pension eligibility
    3. uk_project_pension_balance - Drawdown projection
    
    Args:
        member_id: Member identifier
        withdrawal_amount: Proposed withdrawal in GBP
        warehouse_id: SQL Warehouse ID
    
    Returns:
        dict with calculations, citations, and metadata
    """
    
    overall_start = time.time()
    
    # Fetch member profile
    profile = get_member_profile(member_id, warehouse_id)
    
    if not profile:
        return {
            "error": "Member not found",
            "country": "United Kingdom",
            "member_id": member_id
        }
    
    tools_called = []
    
    # Function 1: Pension Tax Calculator
    tax_start = time.time()
    # Assume Lump_Sum as default withdrawal type
    tax_query = f"""
        SELECT super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
            '{member_id}',
            {profile['age']},
            {profile['super_balance']},
            {withdrawal_amount},
            'Lump_Sum'
        ) as result
    """
    
    tax_result_raw = execute_query(warehouse_id, tax_query)
    tax_duration = time.time() - tax_start
    
    if tax_result_raw and len(tax_result_raw) > 0:
        tax_result = tax_result_raw[0][0]
        tools_called.append({
            "name": "UK Pension Tax Calculator",
            "authority": "HM Revenue & Customs",
            "uc_function": "super_advisory_demo.pension_calculators.uk_calculate_pension_tax",
            "status": "completed",
            "duration": round(tax_duration, 2)
        })
    else:
        tax_result = None
    
    # Function 2: State Pension Calculator
    sp_start = time.time()
    # Assume 35 NI qualifying years for full pension
    sp_query = f"""
        SELECT super_advisory_demo.pension_calculators.uk_check_state_pension(
            '{member_id}',
            {profile['age']},
            35,
            {profile['super_balance'] * 0.04}
        ) as result
    """
    
    sp_result_raw = execute_query(warehouse_id, sp_query)
    sp_duration = time.time() - sp_start
    
    if sp_result_raw and len(sp_result_raw) > 0:
        sp_result = sp_result_raw[0][0]
        tools_called.append({
            "name": "State Pension Calculator",
            "authority": "Department for Work and Pensions",
            "uc_function": "super_advisory_demo.pension_calculators.uk_check_state_pension",
            "status": "completed",
            "duration": round(sp_duration, 2)
        })
    else:
        sp_result = None
    
    # Function 3: Pension Drawdown Projection
    proj_start = time.time()
    # Assume 4% annual drawdown
    annual_drawdown = profile['super_balance'] * 0.04
    proj_query = f"""
        SELECT super_advisory_demo.pension_calculators.uk_project_pension_balance(
            '{member_id}',
            {profile['age']},
            {profile['super_balance']},
            {annual_drawdown},
            20
        ) as result
    """
    
    proj_result_raw = execute_query(warehouse_id, proj_query)
    proj_duration = time.time() - proj_start
    
    if proj_result_raw and len(proj_result_raw) > 0:
        proj_result = proj_result_raw[0][0]
        tools_called.append({
            "name": "Pension Drawdown Projection",
            "authority": "Financial Conduct Authority",
            "uc_function": "super_advisory_demo.pension_calculators.uk_project_pension_balance",
            "status": "completed",
            "duration": round(proj_duration, 2)
        })
    else:
        proj_result = None
    
    # Fetch citations
    citations = get_citations(['UK-TAX-001', 'UK-PENSION-001', 'UK-AGE-001', 'UK-DRAWDOWN-001'], warehouse_id)
    
    return {
        "country": "United Kingdom",
        "member_id": member_id,
        "member_name": profile['name'],
        "member_age": profile['age'],
        "withdrawal_amount": withdrawal_amount,
        "tax_calculation": tax_result,
        "state_pension": sp_result,
        "drawdown_projection": proj_result,
        "citations": citations,
        "tools_called": tools_called,
        "data_source": "super_advisory_demo.member_data.member_profiles",
        "total_duration": round(time.time() - overall_start, 2)
    }


# ============================================================================
# INDIA CALCULATORS (3 functions)
# ============================================================================

def calculate_india_epf(member_id, withdrawal_amount, warehouse_id):
    """
    India EPF Calculator - Calls 3 UC Functions
    
    Functions called:
    1. in_calculate_epf_tax - EPF tax with 5-year exemption
    2. in_calculate_nps_benefits - NPS lump sum and annuity
    3. in_project_retirement_corpus - EPF + NPS projection
    
    Args:
        member_id: Member identifier
        withdrawal_amount: Proposed withdrawal in INR
        warehouse_id: SQL Warehouse ID
    
    Returns:
        dict with calculations, citations, and metadata
    """
    
    overall_start = time.time()
    
    # Fetch member profile
    profile = get_member_profile(member_id, warehouse_id)
    
    if not profile:
        return {
            "error": "Member not found",
            "country": "India",
            "member_id": member_id
        }
    
    tools_called = []
    
    # Function 1: EPF Tax Calculator
    tax_start = time.time()
    # Assume 8 years of service and Full withdrawal
    tax_query = f"""
        SELECT super_advisory_demo.pension_calculators.in_calculate_epf_tax(
            '{member_id}',
            {profile['age']},
            8,
            {profile['super_balance']},
            {withdrawal_amount},
            'Full'
        ) as result
    """
    
    tax_result_raw = execute_query(warehouse_id, tax_query)
    tax_duration = time.time() - tax_start
    
    if tax_result_raw and len(tax_result_raw) > 0:
        tax_result = tax_result_raw[0][0]
        tools_called.append({
            "name": "EPF Tax Calculator",
            "authority": "Employees Provident Fund Organisation",
            "uc_function": "super_advisory_demo.pension_calculators.in_calculate_epf_tax",
            "status": "completed",
            "duration": round(tax_duration, 2)
        })
    else:
        tax_result = None
    
    # Function 2: NPS Benefits Calculator
    nps_start = time.time()
    # Assume member has NPS corpus equal to 50% of EPF
    nps_corpus = profile['super_balance'] * 0.5
    nps_query = f"""
        SELECT super_advisory_demo.pension_calculators.in_calculate_nps_benefits(
            '{member_id}',
            {profile['age']},
            {nps_corpus},
            40.0,
            7.5
        ) as result
    """
    
    nps_result_raw = execute_query(warehouse_id, nps_query)
    nps_duration = time.time() - nps_start
    
    if nps_result_raw and len(nps_result_raw) > 0:
        nps_result = nps_result_raw[0][0]
        tools_called.append({
            "name": "NPS Benefits Calculator",
            "authority": "Pension Fund Regulatory Authority",
            "uc_function": "super_advisory_demo.pension_calculators.in_calculate_nps_benefits",
            "status": "completed",
            "duration": round(nps_duration, 2)
        })
    else:
        nps_result = None
    
    # Function 3: Retirement Corpus Projection
    proj_start = time.time()
    proj_query = f"""
        SELECT super_advisory_demo.pension_calculators.in_project_retirement_corpus(
            '{member_id}',
            {profile['age']},
            {profile['super_balance']},
            {profile['super_balance'] * 0.5},
            5000,
            3000,
            60,
            20
        ) as result
    """
    
    proj_result_raw = execute_query(warehouse_id, proj_query)
    proj_duration = time.time() - proj_start
    
    if proj_result_raw and len(proj_result_raw) > 0:
        proj_result = proj_result_raw[0][0]
        tools_called.append({
            "name": "Retirement Corpus Projection",
            "authority": "EPFO & PFRDA",
            "uc_function": "super_advisory_demo.pension_calculators.in_project_retirement_corpus",
            "status": "completed",
            "duration": round(proj_duration, 2)
        })
    else:
        proj_result = None
    
    # Fetch citations
    citations = get_citations(['IN-EPF-001', 'IN-TAX-001', 'IN-NPS-001', 'IN-INTEREST-001'], warehouse_id)
    
    return {
        "country": "India",
        "member_id": member_id,
        "member_name": profile['name'],
        "member_age": profile['age'],
        "withdrawal_amount": withdrawal_amount,
        "epf_tax_calculation": tax_result,
        "nps_benefits": nps_result,
        "retirement_projection": proj_result,
        "citations": citations,
        "tools_called": tools_called,
        "data_source": "super_advisory_demo.member_data.member_profiles",
        "total_duration": round(time.time() - overall_start, 2)
    }


# ============================================================================
# ROUTER FUNCTION
# ============================================================================

def get_pension_calculator(country):
    """
    Get the appropriate calculator function for a country
    
    Args:
        country: Country name (Australia, USA, United Kingdom, India)
    
    Returns:
        Calculator function
    """
    calculators = {
        "Australia": calculate_super_australia,
        "USA": calculate_401k_usa,
        "United Kingdom": calculate_uk_pension,
        "India": calculate_india_epf
    }
    
    return calculators.get(country, calculate_super_australia)


# ============================================================================
# CONVENIENCE FUNCTION FOR AGENT
# ============================================================================

def calculate_retirement_advice(member_id, withdrawal_amount, country, warehouse_id=None):
    """
    Main entry point for retirement advice calculation
    
    Args:
        member_id: Member identifier
        withdrawal_amount: Proposed withdrawal amount
        country: Country name (Australia, USA, United Kingdom, India)
        warehouse_id: Optional SQL Warehouse ID (uses config default if not provided)
    
    Returns:
        dict with calculations, citations, and metadata for all 3 functions
    """
    
    if warehouse_id is None:
        warehouse_id = SQL_WAREHOUSE_ID
    
    # Get the appropriate calculator for the country
    calculator = get_pension_calculator(country)
    
    # Call the calculator
    result = calculator(member_id, withdrawal_amount, warehouse_id)
    
    return result
