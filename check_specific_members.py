#!/usr/bin/env python3
"""Check specific members in member_profiles table."""

from databricks.sdk import WorkspaceClient
from config import SQL_WAREHOUSE_ID

w = WorkspaceClient()

# Query for David Kim and Michelle Brown
query = """
SELECT
    member_id,
    name,
    age,
    country,
    super_balance,
    preservation_age,
    employment_status,
    marital_status
FROM super_advisory_demo.member_data.member_profiles
WHERE name IN ('David Kim', 'Michelle Brown')
ORDER BY name
"""

try:
    statement = w.statement_execution.execute_statement(
        warehouse_id=SQL_WAREHOUSE_ID,
        statement=query,
        wait_timeout='30s'
    )

    if statement.result and statement.result.data_array:
        print('\nMember data found:')
        print('=' * 100)
        for row in statement.result.data_array:
            print(f"\nMember ID:         {row[0]}")
            print(f"Name:              {row[1]}")
            print(f"Age:               {row[2]}")
            print(f"Country:           {row[3]}")
            print(f"Super Balance:     ${int(row[4]):,}" if row[4] else "Super Balance:     N/A")
            print(f"Preservation Age:  {row[5]}")
            print(f"Employment:        {row[6]}")
            print(f"Marital Status:    {row[7]}")
            print('-' * 100)
    else:
        print('❌ No data found for David Kim or Michelle Brown')

    # Also count total members with these names
    count_query = """
    SELECT COUNT(*) as count
    FROM super_advisory_demo.member_data.member_profiles
    WHERE name IN ('David Kim', 'Michelle Brown')
    """

    statement2 = w.statement_execution.execute_statement(
        warehouse_id=SQL_WAREHOUSE_ID,
        statement=count_query,
        wait_timeout='30s'
    )

    if statement2.result and statement2.result.data_array:
        count = statement2.result.data_array[0][0]
        print(f"\n✅ Found {count} member(s) matching these names")

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
