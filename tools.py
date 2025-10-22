# tools.py
"""
Country-specific retirement calculator tools
Uses hardcoded SQL Warehouse ID from config
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
# AUSTRALIA
# ============================================================================

def calculate_super_australia(user_data):
    """Australian superannuation calculator"""
    member_id = user_data.get('member_id')
    
    # Convert to float to handle string values from database
    try:
        super_balance = float(user_data.get('super_balance', 0))
        age = float(user_data.get('age', 65))
    except (ValueError, TypeError):
        super_balance = 0
        age = 65
    
    withdrawal_pct = 0.05 if age >= 65 else 0.04
    withdrawal_amount = super_balance * withdrawal_pct
    
    tax_info = call_uc_function('calculate_tax_implications', member_id, withdrawal_amount)
    pension_impact = call_uc_function('check_age_pension_impact', member_id, withdrawal_amount)
    projection = call_uc_function('project_retirement_income', member_id, 10)
    
    if tax_info and pension_impact:
        summary = f"""Based on your Australian super profile:

💰 Recommended Annual Withdrawal: ${withdrawal_amount:,.2f}
   • Tax status: {tax_info.get('status', 'Unknown')}
   • Tax amount: ${tax_info.get('tax_amount', 0):,.2f}
   • Net withdrawal: ${tax_info.get('net_withdrawal', withdrawal_amount):,.2f}

🏛️ Age Pension Impact:
   • Current eligibility: {'Yes' if pension_impact.get('currently_eligible') else 'No'}
   • Current annual pension: ${pension_impact.get('current_annual_pension', 0):,.2f}
   • After withdrawal pension: ${pension_impact.get('future_annual_pension', 0):,.2f}

📊 10-Year Projection: {projection.get('projection_summary', 'N/A') if projection else 'N/A'}
"""
        amount = tax_info.get('net_withdrawal', withdrawal_amount)
    else:
        summary = f"Estimated annual withdrawal: ${withdrawal_amount:,.2f}"
        amount = withdrawal_amount
    
    return {
        "amount": amount,
        "summary": summary,
        "tool_used": "UC_MCP_AU_Super_v1",
        "citations": [
            COUNTRY_REGULATIONS["Australia"][0],
            "Unity Catalog MCP Tools"
        ]
    }

# ============================================================================
# USA
# ============================================================================

def calculate_401k_usa(user_data):
    """USA 401(k) calculator"""
    member_id = user_data.get('member_id')
    
    # Convert to float to handle string values
    try:
        balance = float(user_data.get('super_balance', 0))
        age = float(user_data.get('age', 65))
    except (ValueError, TypeError):
        balance = 0
        age = 65
    
    withdrawal_pct = 0.04 if age >= 59.5 else 0.03
    withdrawal_amount = balance * withdrawal_pct
    
    tax_info = call_uc_function('calculate_401k_withdrawal', member_id, withdrawal_amount)
    ss_impact = call_uc_function('check_social_security_impact', member_id, withdrawal_amount)
    projection = call_uc_function('project_401k_balance', member_id, 10)
    
    if tax_info and ss_impact:
        summary = f"""Based on your US 401(k) profile:

💰 Recommended Annual Withdrawal: ${withdrawal_amount:,.2f}
   • Status: {tax_info.get('status', 'Unknown')}
   • Tax rate: {tax_info.get('tax_rate', 'N/A')}
   • Penalty: ${tax_info.get('penalty', 0):,.2f}
   • Net withdrawal: ${tax_info.get('net_withdrawal', withdrawal_amount):,.2f}

🇺🇸 Social Security Impact:
   • Combined retirement income: ${ss_impact.get('combined_retirement_income', 0):,.2f}

📊 10-Year Projection: {projection.get('projection_summary', 'N/A') if projection else 'N/A'}
"""
        amount = tax_info.get('net_withdrawal', withdrawal_amount)
    else:
        summary = f"Estimated annual 401(k) withdrawal: ${withdrawal_amount:,.2f}"
        amount = withdrawal_amount
    
    return {
        "amount": amount,
        "summary": summary,
        "tool_used": "UC_MCP_US_401k_v1",
        "citations": [COUNTRY_REGULATIONS["USA"][0], "Unity Catalog MCP Tools"]
    }

# ============================================================================
# UK
# ============================================================================

def calculate_uk_pension(user_data):
    """UK pension calculator"""
    member_id = user_data.get('member_id')
    
    # Convert to float to handle string values
    try:
        balance = float(user_data.get('super_balance', 0))
        age = float(user_data.get('age', 65))
    except (ValueError, TypeError):
        balance = 0
        age = 65
    
    withdrawal_pct = 0.04 if age >= 55 else 0.03
    withdrawal_amount = balance * withdrawal_pct
    
    tax_info = call_uc_function('calculate_uk_pension_withdrawal', member_id, withdrawal_amount)
    state_pension = call_uc_function('check_uk_state_pension', member_id, withdrawal_amount)
    projection = call_uc_function('project_uk_pension_balance', member_id, 10)
    
    if tax_info and state_pension:
        summary = f"""Based on your UK pension profile:

💰 Recommended Annual Withdrawal: £{withdrawal_amount:,.2f}
   • Status: {tax_info.get('status', 'Unknown')}
   • Tax-free portion: £{tax_info.get('tax_free_portion', 0):,.2f}
   • Net withdrawal: £{tax_info.get('net_withdrawal', withdrawal_amount):,.2f}

🇬🇧 State Pension: £{state_pension.get('annual_state_pension', 0):,.2f}

📊 10-Year Projection: {projection.get('projection_summary', 'N/A') if projection else 'N/A'}
"""
        amount = tax_info.get('net_withdrawal', withdrawal_amount)
    else:
        summary = f"Estimated annual pension withdrawal: £{withdrawal_amount:,.2f}"
        amount = withdrawal_amount
    
    return {
        "amount": amount,
        "summary": summary,
        "tool_used": "UC_MCP_UK_Pension_v1",
        "citations": [COUNTRY_REGULATIONS["UK"][0], "Unity Catalog MCP Tools"]
    }

# ============================================================================
# INDIA
# ============================================================================

def calculate_india_pf(user_data):
    """India Provident Fund calculator"""
    member_id = user_data.get('member_id')
    
    # Convert to float to handle string values
    try:
        balance = float(user_data.get('super_balance', 0))
        age = float(user_data.get('age', 65))
    except (ValueError, TypeError):
        balance = 0
        age = 65
    
    withdrawal_pct = 0.05 if age >= 58 else 0.03
    withdrawal_amount = balance * withdrawal_pct
    
    tax_info = call_uc_function('calculate_epf_withdrawal', member_id, withdrawal_amount)
    pension_impact = call_uc_function('check_india_pension_impact', member_id, withdrawal_amount)
    projection = call_uc_function('project_india_pf_balance', member_id, 10)
    
    if tax_info and pension_impact:
        summary = f"""Based on your India PF profile:

�� Recommended Annual Withdrawal: ₹{withdrawal_amount:,.2f}
   • Tax status: {tax_info.get('tax_status', 'Unknown')}
   • Net withdrawal: ₹{tax_info.get('net_withdrawal', withdrawal_amount):,.2f}

🇮🇳 Annual pension income: ₹{pension_impact.get('annual_pension_income', 0):,.2f}

📊 10-Year Projection: {projection.get('projection_summary', 'N/A') if projection else 'N/A'}
"""
        amount = tax_info.get('net_withdrawal', withdrawal_amount)
    else:
        summary = f"Estimated annual PF withdrawal: ₹{withdrawal_amount:,.2f}"
        amount = withdrawal_amount
    
    return {
        "amount": amount,
        "summary": summary,
        "tool_used": "UC_MCP_India_PF_v1",
        "citations": [COUNTRY_REGULATIONS["India"][0], "Unity Catalog MCP Tools"]
    }

def get_country_tool(country):
    """Get the appropriate calculator tool for a country"""
    tools = {
        "Australia": calculate_super_australia,
        "USA": calculate_401k_usa,
        "United Kingdom": calculate_uk_pension,
        "India": calculate_india_pf
    }
    return tools.get(country, calculate_super_australia)

