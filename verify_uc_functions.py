"""
Verify Unity Catalog Functions for Superannuation Agent
========================================================

This script queries the Unity Catalog to verify that all required
pension calculator functions are registered and accessible.

Expected functions:
- AU: au_calculate_tax, au_check_pension_impact, au_project_balance
- US: us_calculate_401k_tax, us_check_social_security, us_project_401k_balance
- UK: uk_calculate_pension_tax, uk_check_state_pension, uk_project_pension_balance
- IN: in_calculate_epf_tax, in_calculate_nps_benefits, in_calculate_eps_benefits, in_project_retirement_corpus
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import config

def list_catalog_functions():
    """List all functions in the pension_calculators schema."""

    print("\n" + "="*80)
    print("UNITY CATALOG FUNCTION VERIFICATION")
    print("="*80)

    # Initialize Databricks client
    w = WorkspaceClient()

    # Query to list all functions in the schema
    query = """
    SELECT
        routine_name,
        routine_schema,
        routine_catalog,
        routine_type,
        data_type as return_type
    FROM
        system.information_schema.routines
    WHERE
        routine_catalog = 'super_advisory_demo'
        AND routine_schema = 'pension_calculators'
    ORDER BY
        routine_name
    """

    print(f"\nQuerying catalog: super_advisory_demo.pension_calculators")
    print(f"Using warehouse: {config.SQL_WAREHOUSE_ID}")
    print("-" * 80)

    try:
        # Execute query
        statement = w.statement_execution.execute_statement(
            warehouse_id=config.SQL_WAREHOUSE_ID,
            statement=query,
            wait_timeout="30s"
        )

        # Check if query succeeded
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                print(f"\n✅ Found {len(statement.result.data_array)} functions:\n")

                # Expected functions
                expected_functions = {
                    'au_calculate_tax',
                    'au_check_pension_impact',
                    'au_project_balance',
                    'us_calculate_401k_tax',
                    'us_check_social_security',
                    'us_project_401k_balance',
                    'uk_calculate_pension_tax',
                    'uk_check_state_pension',
                    'uk_project_pension_balance',
                    'in_calculate_epf_tax',
                    'in_calculate_nps_benefits',
                    'in_calculate_eps_benefits',
                    'in_project_retirement_corpus'
                }

                found_functions = set()

                # Print function details
                for i, row in enumerate(statement.result.data_array, 1):
                    func_name = row[0]
                    schema = row[1]
                    catalog = row[2]
                    routine_type = row[3]
                    return_type = row[4]

                    found_functions.add(func_name)

                    print(f"{i}. {func_name}")
                    print(f"   Full name: {catalog}.{schema}.{func_name}")
                    print(f"   Type: {routine_type}")
                    print(f"   Returns: {return_type}")
                    print()

                # Check for missing functions
                missing = expected_functions - found_functions
                extra = found_functions - expected_functions

                print("\n" + "="*80)
                print("VERIFICATION SUMMARY")
                print("="*80)
                print(f"\n✅ Expected functions: {len(expected_functions)}")
                print(f"✅ Found functions: {len(found_functions)}")

                if missing:
                    print(f"\n❌ MISSING FUNCTIONS ({len(missing)}):")
                    for func in sorted(missing):
                        print(f"   - {func}")
                else:
                    print("\n✅ All expected functions are registered!")

                if extra:
                    print(f"\n⚠️  EXTRA FUNCTIONS ({len(extra)}):")
                    for func in sorted(extra):
                        print(f"   - {func}")

                return found_functions, missing

            else:
                print("⚠️  No functions found in super_advisory_demo.pension_calculators")
                return set(), expected_functions
        else:
            print(f"❌ Query failed with state: {statement.status.state}")
            if statement.status.error:
                print(f"   Error: {statement.status.error.message}")
            return set(), set()

    except Exception as e:
        print(f"❌ Error querying Unity Catalog: {e}")
        return set(), set()

def test_function_invocation():
    """Test invoking one of the functions to verify it works."""

    print("\n" + "="*80)
    print("FUNCTION INVOCATION TEST")
    print("="*80)

    w = WorkspaceClient()

    # Test AU tax calculator with sample data
    test_query = """
    SELECT super_advisory_demo.pension_calculators.au_calculate_tax(
        'TEST001',  -- member_id
        65,         -- age
        60,         -- preservation_age
        500000,     -- balance
        50000       -- withdrawal_amount
    ) as tax_result
    """

    print("\nTesting: au_calculate_tax()")
    print("Parameters: member_id='TEST001', age=65, balance=500000, withdrawal=50000")
    print("-" * 80)

    try:
        statement = w.statement_execution.execute_statement(
            warehouse_id=config.SQL_WAREHOUSE_ID,
            statement=test_query,
            wait_timeout="30s"
        )

        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                result = statement.result.data_array[0][0]
                print(f"\n✅ Function executed successfully!")
                print(f"   Result: {result}")
                print(f"   Type: {type(result)}")
                return True
            else:
                print("⚠️  Function executed but returned no data")
                return False
        else:
            print(f"❌ Function execution failed: {statement.status.state}")
            if statement.status.error:
                print(f"   Error: {statement.status.error.message}")
            return False

    except Exception as e:
        print(f"❌ Error invoking function: {e}")
        return False

if __name__ == "__main__":
    # List all functions
    found, missing = list_catalog_functions()

    # Test function invocation if functions exist
    if found and not missing:
        test_function_invocation()
    elif missing:
        print("\n⚠️  Skipping invocation test due to missing functions")

    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80 + "\n")
