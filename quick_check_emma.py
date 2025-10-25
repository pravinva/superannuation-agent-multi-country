# quick_check_emma.py
"""
Quick check to see what member_id Emma has in the database
Run this to verify the member_id being passed to the UC function
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

def execute_query(query):
    try:
        statement = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=query,
            wait_timeout="30s"
        )
        
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                return statement.result.data_array
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

print("🔍 Checking Emma Thompson's member data...")
print("=" * 60)

query = """
SELECT 
    member_id,
    name,
    age,
    super_balance,
    country
FROM super_advisory_demo.member_data.member_profiles
WHERE country = 'UK'
ORDER BY name
"""

result = execute_query(query)

if result:
    print(f"✅ Found {len(result)} UK members:\n")
    for row in result:
        member_id = row[0]
        name = row[1]
        age = row[2]
        balance = row[3]
        country = row[4]
        
        print(f"Name: {name}")
        print(f"Member ID: {member_id}")
        print(f"Age: {age}")
        print(f"Balance: £{balance:,.0f}")
        print(f"Country: {country}")
        print("-" * 60)
        
        # If this is Emma, test the function with her ID
        if 'Emma' in name:
            print(f"\n🧪 Testing UC function with Emma's data:")
            print(f"   Member ID: {member_id}")
            print(f"   Pension pot: £{balance:,.0f}")
            print(f"   Withdrawal: £50,000")
            
            test_query = f"""
            SELECT super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
                '{member_id}',
                {balance},
                'LUMP_SUM',
                50000.0
            ) as result
            """
            
            print(f"\n📤 Query:\n{test_query}\n")
            
            test_result = execute_query(test_query)
            
            if test_result:
                print(f"✅ Function returned:")
                print(f"   {test_result[0][0]}")
            else:
                print(f"❌ Function returned no results")
                print(f"\n🔍 Let's check the function signature:")
                
                describe_query = "DESCRIBE FUNCTION super_advisory_demo.pension_calculators.uk_calculate_pension_tax"
                desc_result = execute_query(describe_query)
                
                if desc_result:
                    print("Function signature:")
                    for desc_row in desc_result:
                        print(f"   {desc_row}")
            
            print("-" * 60)
else:
    print("❌ No UK members found in database")
    print("\nTrying to find ANY members...")
    
    all_query = "SELECT member_id, name, country FROM super_advisory_demo.member_data.member_profiles LIMIT 5"
    all_result = execute_query(all_query)
    
    if all_result:
        print(f"Found {len(all_result)} members:")
        for row in all_result:
            print(f"   - {row[1]} ({row[2]}): {row[0]}")

print("\n" + "=" * 60)
print("✅ Check complete")
