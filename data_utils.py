# data_utils.py - Data utilities with enhanced error handling
"""
Data utilities with enhanced error handling
✅ FIXED: Added missing get_member_by_id() function
"""

import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from config import get_member_profiles_table_path, SQL_WAREHOUSE_ID

w = WorkspaceClient()


def execute_query(query):
    """Execute SQL query and return DataFrame"""
    try:
        if not SQL_WAREHOUSE_ID or SQL_WAREHOUSE_ID == "YOUR_WAREHOUSE_ID_HERE":
            raise ValueError("Please set SQL_WAREHOUSE_ID in config.py")
        
        statement = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=query,
            wait_timeout="30s"
        )
        
        # Wait for completion
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                columns = [col.name for col in statement.manifest.schema.columns]
                df = pd.DataFrame(statement.result.data_array, columns=columns)
                return df
        
        return pd.DataFrame()
    
    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame()


def get_member_by_id(member_id, country=None):
    """
    Get member profile by member_id
    
    Args:
        member_id: Member identifier
        country: Optional country filter
    
    Returns:
        Dict with member profile data or None if not found
    """
    try:
        table_path = get_member_profiles_table_path()
        
        # Build query with optional country filter
        query = f"SELECT * FROM {table_path} WHERE member_id = '{member_id}'"
        if country:
            query += f" AND country = '{country}'"
        query += " LIMIT 1"
        
        df = execute_query(query)
        
        if df.empty:
            print(f"⚠️ No member found with ID: {member_id}")
            return None
        
        # Convert DataFrame row to dict
        member_dict = df.iloc[0].to_dict()
        print(f"✅ Found member: {member_dict.get('name', 'Unknown')}")
        return member_dict
        
    except Exception as e:
        st.error(f"Error loading member {member_id}: {str(e)}")
        return None


def get_members_by_country(country_code, default_return=None):
    """
    Get all members for a specific country
    
    Args:
        country_code: Country name ("Australia", "USA", "United Kingdom", "India")
        default_return: Default value if query fails
    
    Returns:
        DataFrame with member profiles
    """
    if default_return is None:
        default_return = pd.DataFrame()
    
    try:
        table_path = get_member_profiles_table_path()
        query = f"SELECT * FROM {table_path} WHERE country = '{country_code}'"
        
        df = execute_query(query)
        
        if df.empty:
            print(f"⚠️ No members found for country: {country_code}")
            return default_return
        
        print(f"✅ Found {len(df)} members for {country_code}")
        return df
        
    except Exception as e:
        st.error(f"Error loading members for {country_code}: {str(e)}")
        return default_return


def get_all_members():
    """
    Get all member profiles across all countries
    
    Returns:
        DataFrame with all member profiles
    """
    try:
        table_path = get_member_profiles_table_path()
        query = f"SELECT * FROM {table_path}"
        
        df = execute_query(query)
        
        if df.empty:
            print("⚠️ No members found in database")
            return pd.DataFrame()
        
        print(f"✅ Found {len(df)} total members")
        return df
        
    except Exception as e:
        st.error(f"Error loading members: {str(e)}")
        return pd.DataFrame()
