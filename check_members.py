#!/usr/bin/env python3
"""Quick script to check member_profiles table data."""

from databricks.sdk import WorkspaceClient
from config import SQL_WAREHOUSE_ID

w = WorkspaceClient()

sample_query = '''
SELECT member_id, name, age, country, super_balance
FROM super_advisory_demo.member_data.member_profiles
LIMIT 10
'''

try:
    statement = w.statement_execution.execute_statement(
        warehouse_id=SQL_WAREHOUSE_ID,
        statement=sample_query,
        wait_timeout='30s'
    )

    if statement.result and statement.result.data_array:
        print('\nSample members from member_profiles:')
        print('-' * 80)
        print(f'{"Member ID":<15} | {"Name":<20} | {"Age":<5} | {"Country":<5} | {"Balance":<15}')
        print('-' * 80)
        for row in statement.result.data_array:
            balance = int(row[4]) if row[4] else 0
            print(f'{row[0]:<15} | {row[1]:<20} | {row[2]:<5} | {row[3]:<5} | ${balance:>12,}')
        print()
    else:
        print('No sample data returned')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
