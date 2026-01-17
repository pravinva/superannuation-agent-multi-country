#!/usr/bin/env python3
"""Test Unity Catalog SQL functions with real member data."""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from config import SQL_WAREHOUSE_ID

w = WorkspaceClient()

print("\n" + "="*80)
print("TESTING UNITY CATALOG SQL FUNCTIONS")
print("="*80)

# Test 1: au_check_pension_impact for David Kim
print("\n1. Testing au_check_pension_impact for David Kim (AU015)")
print("-" * 80)

query1 = """
SELECT super_advisory_demo.pension_calculators.au_check_pension_impact('AU015')
"""

try:
    statement = w.statement_execution.execute_statement(
        warehouse_id=SQL_WAREHOUSE_ID,
        statement=query1,
        wait_timeout='30s'
    )

    print(f"Statement State: {statement.status.state}")

    if statement.status.state == StatementState.SUCCEEDED:
        if statement.result and statement.result.data_array:
            result = statement.result.data_array[0][0]
            print(f"✅ Function returned result:")
            print(f"   Result: {result}")
        else:
            print("⚠️  Function succeeded but returned no data")
    else:
        print(f"❌ Function failed: {statement.status.state}")
        if statement.status.error:
            print(f"   Error: {statement.status.error.message}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: au_calculate_tax for Michelle Brown
print("\n2. Testing au_calculate_tax for Michelle Brown (AU008)")
print("-" * 80)

query2 = """
SELECT super_advisory_demo.pension_calculators.au_calculate_tax()
"""

try:
    statement = w.statement_execution.execute_statement(
        warehouse_id=SQL_WAREHOUSE_ID,
        statement=query2,
        wait_timeout='30s'
    )

    print(f"Statement State: {statement.status.state}")

    if statement.status.state == StatementState.SUCCEEDED:
        if statement.result and statement.result.data_array:
            result = statement.result.data_array[0][0]
            print(f"✅ Function returned result:")
            print(f"   Result: {result}")
        else:
            print("⚠️  Function succeeded but returned no data")
    else:
        print(f"❌ Function failed: {statement.status.state}")
        if statement.status.error:
            print(f"   Error: {statement.status.error.message}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
