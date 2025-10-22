# data_utils.py
"""Member data retrieval - Uses hardcoded SQL Warehouse ID"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import pandas as pd
import time
from config import get_member_profiles_table_path, SQL_WAREHOUSE_ID

w = WorkspaceClient()

def get_warehouse_id():
    """Get warehouse ID from config"""
    if not SQL_WAREHOUSE_ID or SQL_WAREHOUSE_ID == "YOUR_WAREHOUSE_ID_HERE":
        raise ValueError("Please set SQL_WAREHOUSE_ID in config.py")
    return SQL_WAREHOUSE_ID

def execute_query(query):
    """Execute SQL query and return results as DataFrame"""
    try:
        warehouse_id = get_warehouse_id()
        
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
                df = pd.DataFrame(statement.result.data_array, columns=columns)
                return df
        
        return pd.DataFrame()
    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame()

def get_members_by_country(country, limit=3):
    """Retrieve random member profiles for a specific country"""
    table_path = get_member_profiles_table_path()
    query = f"SELECT * FROM {table_path} WHERE country = '{country}' ORDER BY RAND() LIMIT {limit}"
    return execute_query(query)


def get_member_by_id(member_id):
    """Retrieve a specific member by ID"""
    table_path = get_member_profiles_table_path()
    query = f"SELECT * FROM {table_path} WHERE member_id = '{member_id}'"
    df = execute_query(query)
    if not df.empty:
        return df.to_dict('records')[0]
    return None

def get_all_members():
    """Retrieve all member profiles"""
    table_path = get_member_profiles_table_path()
    query = f"SELECT * FROM {table_path}"
    return execute_query(query)

