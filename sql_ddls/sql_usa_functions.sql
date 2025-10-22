
-- ============================================================================
-- USA 401(k) RETIREMENT FUNCTIONS
-- ============================================================================

-- 1. Calculate 401(k) Withdrawal with Tax Implications
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.calculate_401k_withdrawal(
  member_id STRING COMMENT 'Member identifier',
  withdrawal_amount DOUBLE COMMENT 'Proposed withdrawal amount in USD'
)
RETURNS STRUCT<
  withdrawal_amount: DOUBLE,
  tax_rate: STRING,
  tax_amount: DOUBLE,
  penalty: DOUBLE,
  status: STRING,
  member_name: STRING,
  member_age: INT,
  net_withdrawal: DOUBLE
>
LANGUAGE PYTHON
COMMENT 'MCP Server: IRS 401(k) Calculator - Calculates tax and penalties on 401(k) withdrawals. Registered in Unity Catalog for governance.'
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
      "tax_rate": None,
      "tax_amount": None,
      "penalty": None,
      "status": "Member not found",
      "member_name": None,
      "member_age": None,
      "net_withdrawal": None
    }

  profile = profile_df.first()
  age = int(profile.age)

  # IRS rules: no penalty after 59.5, 10% penalty before
  early_withdrawal = age < 59.5
  penalty_rate = 0.10 if early_withdrawal else 0.0
  penalty = withdrawal_amount * penalty_rate

  # Simplified federal tax (marginal rate approximation)
  if withdrawal_amount < 44625:
    tax_rate = 0.12
  elif withdrawal_amount < 95375:
    tax_rate = 0.22
  else:
    tax_rate = 0.24

  tax_amount = withdrawal_amount * tax_rate
  total_deductions = tax_amount + penalty

  status = "Early withdrawal - penalty applies" if early_withdrawal else "Qualified distribution - no penalty"

  return {
    "withdrawal_amount": withdrawal_amount,
    "tax_rate": f"{tax_rate*100:.0f}%",
    "tax_amount": round(tax_amount, 2),
    "penalty": round(penalty, 2),
    "status": status,
    "member_name": profile.name,
    "member_age": age,
    "net_withdrawal": round(withdrawal_amount - total_deductions, 2)
  }
$$;

-- 2. Check Social Security Impact
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.check_social_security_impact(
  member_id STRING COMMENT 'Member identifier',
  proposed_withdrawal DOUBLE COMMENT 'Proposed 401(k) withdrawal'
)
RETURNS STRUCT<
  member_name: STRING,
  current_401k_balance: DOUBLE,
  after_withdrawal_balance: DOUBLE,
  estimated_annual_ss: DOUBLE,
  combined_retirement_income: DOUBLE,
  income_adequacy: STRING
>
LANGUAGE PYTHON
COMMENT 'MCP Server: SSA Calculator - Estimates Social Security and combined retirement income.'
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
      "current_401k_balance": None,
      "after_withdrawal_balance": None,
      "estimated_annual_ss": None,
      "combined_retirement_income": None,
      "income_adequacy": "Member not found"
    }

  profile = profile_df.first()
  balance = int(profile.super_balance)
  age = int(profile.age)

  # Estimate Social Security (avg benefit ~$1,827/month in 2025)
  if age >= 67:
    monthly_ss = 1827
  elif age >= 62:
    monthly_ss = 1400  # Reduced benefit
  else:
    monthly_ss = 0

  annual_ss = monthly_ss * 12
  after_balance = balance - int(proposed_withdrawal)

  # 4% safe withdrawal rule
  annual_401k = after_balance * 0.04
  combined_income = annual_ss + annual_401k

  # Assess adequacy (70-80% of pre-retirement income rule of thumb)
  if combined_income >= 50000:
    adequacy = "Good - meets typical retirement needs"
  elif combined_income >= 30000:
    adequacy = "Adequate - covers basic expenses"
  else:
    adequacy = "Low - may need additional income sources"

  return {
    "member_name": profile.name,
    "current_401k_balance": float(balance),
    "after_withdrawal_balance": float(after_balance),
    "estimated_annual_ss": round(annual_ss, 2),
    "combined_retirement_income": round(combined_income, 2),
    "income_adequacy": adequacy
  }
$$;

-- 3. Project 401(k) Balance
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.project_401k_balance(
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
COMMENT 'MCP Server: 401(k) Projection Tool - Projects retirement account balance over time.'
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

  # Investment return assumptions
  annual_return = 0.06  # 6% average return

  # RMD percentages based on IRS tables
  if age < 72:
    drawdown_pct = 0.04
  elif age < 75:
    drawdown_pct = 0.04
  elif age < 80:
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
    if current_age < 72:
      drawdown_pct = 0.04
    elif current_age < 80:
      drawdown_pct = 0.05
    else:
      drawdown_pct = 0.06

    annual_drawdown = balance * drawdown_pct

  return {
    "member_name": profile.name,
    "current_age": age,
    "current_balance": float(profile.super_balance),
    "annual_return": f"{annual_return*100:.1f}%",
    "projection_summary": f"Balance {'depleted' if balance <= 0 else 'sustained'} after {years} years",
    "balance_depleted": balance <= 0
  }
$$;
