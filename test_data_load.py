# test_data_load.py
# Simple script to verify Databricks connection and member data loading

from data_utils import get_members_by_country
import pandas as pd

print("=== Databricks Member Data Test ===")

try:
    print("Attempting to query members for Australia (AU)...\n")
    df = get_members_by_country("AU", limit=5)

    if df is None:
        print("❌ Query failed: No DataFrame returned.")
    elif df.empty:
        print("⚠️ Query executed but returned no rows.")
        print("   Possible causes:")
        print("   • Table is empty or filtered country code not found")
        print("   • Incorrect table path in config.get_member_profiles_table_path()")
        print("   • Missing or invalid SQL_WAREHOUSE_ID in config.py")
    else:
        print(f"✅ Loaded {len(df)} member records successfully!\n")
        print(df.head(10).to_string(index=False))

except Exception as e:
    print(f"❌ ERROR: {e}")

