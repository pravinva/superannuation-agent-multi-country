# tools.py
"""
Country-specific retirement calculator tools
Uses real UC functions from super_advisory_demo.mcp_tools
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from country_content import COUNTRY_REGULATIONS
from config import SQL_WAREHOUSE_ID
import time

w = WorkspaceClient()

def get_warehouse_id():
    """Get warehouse ID from config"""
    if not SQL_WAREHOUSE_ID or SQL_WAREHOUSE_ID == "YOUR_WAREHOUSE_ID_HERE":
        raise ValueError("Please set SQL_WAREHOUSE_ID in config.py with your actual warehouse ID")
    return SQL_WAREHOUSE_ID

def call_uc_function(function_name, *args):
    """Generic UC function caller"""
    try:
        warehouse_id = get_warehouse_id()
        
        # Format arguments
        args_str = ", ".join([f"'{arg}'" if isinstance(arg, str) else str(arg) for arg in args])
        query = f"SELECT super_advisory_demo.mcp_tools.{function_name}({args_str}) as result"
        
        # Execute statement
        statement = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query,
            wait_timeout="30s"
        )
        
        # Wait for completion
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                return statement.result.data_array[0][0]
        
        return None
        
    except Exception as e:
        print(f"Error calling UC function {function_name}: {e}")
        return None


# ============================================================================
# AUSTRALIA - Superannuation Functions
# ============================================================================

def calculate_super_australia(member_id, withdrawal_amount=100000):
    """Calculate Australian superannuation using 3 UC functions"""
    
    # 1. Calculate tax implications (ATO)
    tax_result = call_uc_function("calculate_tax_implications", member_id, withdrawal_amount)
    
    # 2. Check Age Pension impact (Centrelink)
    pension_result = call_uc_function("check_age_pension_impact", member_id, withdrawal_amount)
    
    # 3. Project retirement income
    projection_result = call_uc_function("project_retirement_income", member_id, 20)
    
    # Build summary
    summary = f"""Australian Superannuation Analysis:

Tax Calculation (ATO): {tax_result if tax_result else 'Calculation pending'}
Age Pension Impact (Centrelink): {pension_result if pension_result else 'Calculation pending'}
20-Year Projection: {projection_result if projection_result else 'Calculation pending'}
"""
    
    return {
        "country": "Australia",
        "withdrawal_amount": withdrawal_amount,
        "tax_calculation": tax_result,
        "pension_impact": pension_result,
        "retirement_projection": projection_result,
        "summary": summary,
        "citations": [
            "Australian Taxation Office (ATO) - Superannuation Tax Rules",
            "Centrelink - Age Pension Asset Test 2025",
            "Australian Retirement Trust - Income Projection Model"
        ]
    }


# ============================================================================
# USA - 401(k) Functions
# ============================================================================

def calculate_401k_usa(member_id, withdrawal_amount=100000):
    """Calculate USA 401(k) using 3 UC functions"""
    
    # 1. Calculate 401(k) withdrawal tax/penalties (IRS)
    tax_result = call_uc_function("calculate_401k_withdrawal", member_id, withdrawal_amount)
    
    # 2. Check Social Security impact (SSA)
    ss_result = call_uc_function("check_social_security_impact", member_id, withdrawal_amount)
    
    # 3. Project 401(k) balance
    projection_result = call_uc_function("project_401k_balance", member_id, 20)
    
    summary = f"""USA 401(k) Analysis:

Tax & Penalties (IRS): {tax_result if tax_result else 'Calculation pending'}
Social Security Impact (SSA): {ss_result if ss_result else 'Calculation pending'}
20-Year 401(k) Projection: {projection_result if projection_result else 'Calculation pending'}
"""
    
    return {
        "country": "USA",
        "withdrawal_amount": withdrawal_amount,
        "tax_calculation": tax_result,
        "social_security_impact": ss_result,
        "retirement_projection": projection_result,
        "summary": summary,
        "citations": [
            "IRS Publication 590-B - 401(k) Withdrawal Rules",
            "Social Security Administration - Benefit Calculator 2025",
            "Department of Labor - 401(k) Projection Standards"
        ]
    }


# ============================================================================
# UNITED KINGDOM - Pension Functions
# ============================================================================

def calculate_uk_pension(member_id, withdrawal_amount=100000):
    """Calculate UK pension using 3 UC functions"""
    
    # 1. Calculate pension withdrawal tax (HMRC)
    tax_result = call_uc_function("calculate_uk_pension_withdrawal", member_id, withdrawal_amount)
    
    # 2. Check State Pension (DWP)
    state_pension_result = call_uc_function("check_uk_state_pension", member_id, withdrawal_amount)
    
    # 3. Project pension balance
    projection_result = call_uc_function("project_uk_pension_balance", member_id, 20)
    
    summary = f"""UK Pension Analysis:

Withdrawal Tax (HMRC): {tax_result if tax_result else 'Calculation pending'}
State Pension (DWP): {state_pension_result if state_pension_result else 'Calculation pending'}
20-Year Pension Projection: {projection_result if projection_result else 'Calculation pending'}
"""
    
    return {
        "country": "United Kingdom",
        "withdrawal_amount": withdrawal_amount,
        "tax_calculation": tax_result,
        "state_pension": state_pension_result,
        "retirement_projection": projection_result,
        "summary": summary,
        "citations": [
            "HMRC - Pension Tax Rules 2025",
            "DWP - State Pension Forecast Service",
            "Financial Conduct Authority - Pension Projections"
        ]
    }


# ============================================================================
# INDIA - EPF/PF Functions
# ============================================================================

def calculate_india_pf(member_id, withdrawal_amount=100000):
    """Calculate India EPF/PF using 3 UC functions"""
    
    # 1. Calculate EPF withdrawal tax (EPFO)
    tax_result = call_uc_function("calculate_epf_withdrawal", member_id, withdrawal_amount)
    
    # 2. Check pension impact (NPS)
    pension_result = call_uc_function("check_india_pension_impact", member_id, withdrawal_amount)
    
    # 3. Project PF balance
    projection_result = call_uc_function("project_india_pf_balance", member_id, 20)
    
    summary = f"""India EPF/PF Analysis:

EPF Withdrawal Tax (EPFO): {tax_result if tax_result else 'Calculation pending'}
Pension Impact (NPS): {pension_result if pension_result else 'Calculation pending'}
20-Year PF Projection: {projection_result if projection_result else 'Calculation pending'}
"""
    
    return {
        "country": "India",
        "withdrawal_amount": withdrawal_amount,
        "tax_calculation": tax_result,
        "pension_impact": pension_result,
        "retirement_projection": projection_result,
        "summary": summary,
        "citations": [
            "EPFO - EPF Withdrawal Rules",
            "PFRDA - National Pension System Guidelines",
            "Income Tax Department - PF Taxation 2025"
        ]
    }


# ============================================================================
# Country Tool Router
# ============================================================================

def get_country_tool(country):
    """Get the appropriate calculator function for a country"""
    
    country_tools = {
        "Australia": calculate_super_australia,
        "USA": calculate_401k_usa,
        "United Kingdom": calculate_uk_pension,
        "India": calculate_india_pf
    }
    
    tool = country_tools.get(country)
    
    if not tool:
        raise ValueError(f"No tool available for country: {country}")
    
    return tool

