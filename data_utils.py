"""
Data utilities with enhanced error handling
"""
import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from config import get_member_profiles_table_path, SQL_WAREHOUSE_ID

w = WorkspaceClient()

def execute_query(query):
    """Execute SQL query and return DataFrame."""
    try:
        # ✅ ENHANCED CHECK: Catch placeholder values
        if not SQL_WAREHOUSE_ID or \
           SQL_WAREHOUSE_ID in ["YOUR_WAREHOUSE_ID_HERE", "<Your SQL Warehouse ID>", "None", ""]:
            raise ValueError("SQL Warehouse ID not configured. Please set it in Configuration.")
        
        statement = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=query,
            wait_timeout="30s"
        )
        
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                columns = [col.name for col in statement.manifest.schema.columns]
                df = pd.DataFrame(statement.result.data_array, columns=columns)
                return df
            else:
                return pd.DataFrame()
        else:
            raise Exception(f"Query failed with state: {statement.status.state}")
    
    except Exception as e:
        st.error(f"Query execution error: {str(e)}")
        raise


def get_members_by_country(country_code, default_return=None):
    """Get all members for a specific country."""
    if default_return is None:
        default_return = pd.DataFrame()
    
    try:
        # ✅ CHECK SQL WAREHOUSE ID
        if not SQL_WAREHOUSE_ID or \
           SQL_WAREHOUSE_ID in ["YOUR_WAREHOUSE_ID_HERE", "<Your SQL Warehouse ID>", "None", "", "null"]:
            st.error("⚠️ **SQL Warehouse Not Configured**")
            st.markdown("""
            **Please configure your SQL Warehouse ID:**
            
            1. Click **"Governance"** in the left sidebar
            2. Select the **Configuration** tab
            3. Enter your SQL Warehouse ID
            4. Click **Save Configuration**
            5. Return to the Advisory page
            
            **Where to find your SQL Warehouse ID:**
            - Go to Databricks SQL → SQL Warehouses
            - Click on your warehouse
            - Copy the **Warehouse ID** from the Connection Details
            
            👈 **Click "Governance" in the sidebar to get started**
            """)
            return default_return
        
        table_path = get_member_profiles_table_path()
        query = f"SELECT * FROM {table_path} WHERE country = '{country_code}'"
        
        df = execute_query(query)
        
        if df.empty:
            print(f"⚠️ No members found for country: {country_code}")
            st.warning(f"""
            **No members found for {country_code}**
            
            Please ensure:
            - The database schema is set up (`super_advisory_demo.member_data`)
            - Member profiles exist in the `member_profiles` table for country '{country_code}'
            - You have SELECT permissions on the table
            
            **To set up the database:**
            1. Run: `super_advisory_demo_schema_export.sql`
            2. Run: `super_advisory_demo_functions_WITH_GRANTS.sql`
            """)
            return default_return
        
        print(f"✅ Found {len(df)} members for {country_code}")
        return df
        
    except Exception as e:
        error_msg = str(e)
        
        # ✅ CATCH SQL WAREHOUSE ERRORS
        if "not a valid endpoint id" in error_msg.lower():
            st.error("⚠️ **Invalid SQL Warehouse ID**")
            st.markdown(f"""
            The SQL Warehouse ID in your configuration is invalid:
            
            **Current Value:** `{SQL_WAREHOUSE_ID}`
            
            **To fix:**
            1. Click **"Governance"** in the left sidebar 👈
            2. Select the **Configuration** tab
            3. Enter a valid SQL Warehouse ID (format: `abc123def456`)
            4. Click **Save Configuration**
            5. Return to the Advisory page
            """)
        else:
            st.error(f"❌ Error loading members for {country_code}: {error_msg}")
        
        return default_return


def get_member_by_id(member_id):
    """Get a specific member by ID."""
    try:
        # ✅ CHECK SQL WAREHOUSE ID
        if not SQL_WAREHOUSE_ID or \
           SQL_WAREHOUSE_ID in ["YOUR_WAREHOUSE_ID_HERE", "<Your SQL Warehouse ID>", "None", ""]:
            st.error("⚠️ SQL Warehouse Not Configured")
            return None
        
        table_path = get_member_profiles_table_path()
        query = f"SELECT * FROM {table_path} WHERE member_id = '{member_id}'"
        
        df = execute_query(query)
        
        if df.empty:
            print(f"⚠️ Member not found: {member_id}")
            return None
        
        return df.iloc[0].to_dict()
        
    except Exception as e:
        st.error(f"❌ Error loading member {member_id}: {str(e)}")
        return None

