
-- ============================================================================
-- INDIA PROVIDENT FUND (EPF/PPF) FUNCTIONS
-- ============================================================================

-- 1. Calculate EPF Withdrawal with Tax
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.calculate_epf_withdrawal(
  member_id STRING COMMENT 'Member identifier',
  withdrawal_amount DOUBLE COMMENT 'Proposed withdrawal amount in INR'
)
RETURNS STRUCT<
  withdrawal_amount: DOUBLE,
  tax_status: STRING,
  tax_amount: DOUBLE,
  tds_applicable: BOOLEAN,
  member_name: STRING,
  member_age: INT,
  years_of_service: INT,
  net_withdrawal: DOUBLE
>
LANGUAGE PYTHON
COMMENT 'MCP Server: EPFO Calculator - Calculates EPF withdrawal tax per Indian income tax rules. Registered in Unity Catalog.'
AS $$
  from pyspark.sql import SparkSession

  spark = SparkSession.builder.getOrCreate()

  profile_df = spark.sql(f"""
    SELECT name, age
    FROM super_advisory_demo.member_data.member_profiles
    WHERE member_id = '{member_id}'
  """)

  if profile_df.count() == 0:
    return {
      "withdrawal_amount": withdrawal_amount,
      "tax_status": "Member not found",
      "tax_amount": None,
      "tds_applicable": None,
      "member_name": None,
      "member_age": None,
      "years_of_service": None,
      "net_withdrawal": None
    }

  profile = profile_df.first()
  age = int(profile.age)

  # Estimate years of service (assuming started at 25)
  years_of_service = max(0, age - 25)

  # EPF withdrawal is tax-free if:
  # 1. Continuous service of 5 years or more, OR
  # 2. Withdrawal after retirement/resignation

  if years_of_service >= 5 or age >= 58:
    tax_free = True
    tax_amount = 0
    tds_applicable = False
    status = "Tax-free withdrawal (5+ years service or age 58+)"
  else:
    # Taxable as per income tax slab
    # Simplified: assuming 20% tax for early withdrawal
    tax_free = False
    tax_rate = 0.20
    tax_amount = withdrawal_amount * tax_rate
    tds_applicable = True
    status = f"Taxable at {tax_rate*100:.0f}% (early withdrawal, <5 years service)"

  return {
    "withdrawal_amount": withdrawal_amount,
    "tax_status": status,
    "tax_amount": round(tax_amount, 2),
    "tds_applicable": tds_applicable,
    "member_name": profile.name,
    "member_age": age,
    "years_of_service": years_of_service,
    "net_withdrawal": round(withdrawal_amount - tax_amount, 2)
  }
$$;

-- 2. Check NPS and Pension Impact
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.check_india_pension_impact(
  member_id STRING COMMENT 'Member identifier',
  proposed_withdrawal DOUBLE COMMENT 'Proposed EPF/PPF withdrawal in INR'
)
RETURNS STRUCT<
  member_name: STRING,
  current_pf_balance: DOUBLE,
  after_withdrawal_balance: DOUBLE,
  estimated_monthly_pension: DOUBLE,
  annual_pension_income: DOUBLE,
  income_adequacy: STRING
>
LANGUAGE PYTHON
COMMENT 'MCP Server: NPS/Pension Calculator - Estimates post-retirement income in India.'
AS $$
  from pyspark.sql import SparkSession

  spark = SparkSession.builder.getOrCreate()

  profile_df = spark.sql(f"""
    SELECT name, super_balance, age
    FROM super_advisory_demo.member_data.member_profiles
    WHERE member_id = '{member_id}'
  """)

  if profile_df.count() == 0:
    return {
      "member_name": None,
      "current_pf_balance": None,
      "after_withdrawal_balance": None,
      "estimated_monthly_pension": None,
      "annual_pension_income": None,
      "income_adequacy": "Member not found"
    }

  profile = profile_df.first()
  balance = int(profile.super_balance)
  age = int(profile.age)

  after_balance = balance - int(proposed_withdrawal)

  # If age >= 60, eligible for pension (40% compulsory annuity under NPS)
  # Or can take lump sum from EPF and invest for returns

  if age >= 60:
    # Assume 40% goes to annuity (NPS rule)
    annuity_amount = after_balance * 0.40
    # Annuity rate ~6% per year
    annual_pension = annuity_amount * 0.06
    monthly_pension = annual_pension / 12
  else:
    # Not yet eligible for pension
    # But can estimate based on 5% withdrawal rate
    annual_pension = after_balance * 0.05
    monthly_pension = annual_pension / 12

  # Indian average retirement need: ₹25,000-40,000/month
  if monthly_pension >= 40000:
    adequacy = "Comfortable - exceeds typical retirement needs"
  elif monthly_pension >= 25000:
    adequacy = "Adequate - meets average retirement expenses"
  else:
    adequacy = "Modest - may need additional income sources"

  return {
    "member_name": profile.name,
    "current_pf_balance": float(balance),
    "after_withdrawal_balance": float(after_balance),
    "estimated_monthly_pension": round(monthly_pension, 2),
    "annual_pension_income": round(annual_pension, 2),
    "income_adequacy": adequacy
  }
$$;

-- 3. Project EPF/PPF Balance
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.project_india_pf_balance(
  member_id STRING COMMENT 'Member identifier',
  years INT COMMENT 'Number of years to project'
)
RETURNS STRUCT<
  member_name: STRING,
  current_age: INT,
  current_balance: DOUBLE,
  annual_return: STRING,
  projection_summary: STRING,
  balance_depleted: BOOLEAN
>
LANGUAGE PYTHON
COMMENT 'MCP Server: EPF/PPF Projection Tool - Projects provident fund balance over retirement.'
AS $$
  from pyspark.sql import SparkSession

  spark = SparkSession.builder.getOrCreate()

  profile_df = spark.sql(f"""
    SELECT name, age, super_balance
    FROM super_advisory_demo.member_data.member_profiles
    WHERE member_id = '{member_id}'
  """)

  if profile_df.count() == 0:
    return {
      "member_name": None,
      "current_age": None,
      "current_balance": None,
      "annual_return": None,
      "projection_summary": "Member not found",
      "balance_depleted": None
    }

  profile = profile_df.first()
  age = int(profile.age)
  balance = float(profile.super_balance)

  # EPF interest rate ~8-8.5% (but post-retirement ~6-7%)
  if age < 60:
    annual_return = 0.08
  else:
    annual_return = 0.06

  # Withdrawal rates
  if age < 60:
    drawdown_pct = 0.04
  elif age < 70:
    drawdown_pct = 0.05
  else:
    drawdown_pct = 0.06

  annual_drawdown = balance * drawdown_pct

  # Project forward
  for year in range(min(years, 20)):
    balance = balance * (1 + annual_return) - annual_drawdown
    if balance <= 0:
      break

    current_age = age + year
    if current_age < 60:
      annual_return = 0.08
      drawdown_pct = 0.04
    elif current_age < 70:
      annual_return = 0.06
      drawdown_pct = 0.05
    else:
      annual_return = 0.06
      drawdown_pct = 0.06

    annual_drawdown = balance * drawdown_pct

  return {
    "member_name": profile.name,
    "current_age": age,
    "current_balance": float(profile.super_balance),
    "annual_return": f"{annual_return*100:.1f}%",
    "projection_summary": f"PF balance {'depleted' if balance <= 0 else 'sustained'} after {years} years",
    "balance_depleted": balance <= 0
  }
$$;
