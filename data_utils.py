# data_utils.py
"""Utilities for retrieving member data - Uses Databricks SDK with auto warehouse discovery"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import pandas as pd
import time
from config import get_member_profiles_table_path

w = WorkspaceClient()

def get_serverless_warehouse():
    """Automatically find a serverless SQL warehouse"""
    warehouses = w.warehouses.list()
    for warehouse in warehouses:
        if warehouse.enable_serverless_compute and warehouse.state in ['RUNNING', 'STOPPED']:
            return warehouse.id
    for warehouse in warehouses:
        if warehouse.state in ['RUNNING', 'STOPPED']:
            return warehouse.id
    raise ValueError("No SQL warehouse available")

def execute_query(query):
    """Execute SQL query and return results as DataFrame"""
    try:
        warehouse_id = get_serverless_warehouse()

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

def get_members_by_country(country):
    """Retrieve member profiles for a specific country"""
    table_path = get_member_profiles_table_path()
    query = f"SELECT * FROM {table_path} WHERE country = '{country}'"
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
