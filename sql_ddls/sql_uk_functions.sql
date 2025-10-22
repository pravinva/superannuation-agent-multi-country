
-- ============================================================================
-- UK PENSION FUNCTIONS
-- ============================================================================

-- 1. Calculate UK Pension Withdrawal with Tax
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.calculate_uk_pension_withdrawal(
  member_id STRING COMMENT 'Member identifier',
  withdrawal_amount DOUBLE COMMENT 'Proposed withdrawal amount in GBP'
)
RETURNS STRUCT<
  withdrawal_amount: DOUBLE,
  tax_free_portion: DOUBLE,
  taxable_portion: DOUBLE,
  tax_amount: DOUBLE,
  status: STRING,
  member_name: STRING,
  member_age: INT,
  net_withdrawal: DOUBLE
>
LANGUAGE PYTHON
COMMENT 'MCP Server: HMRC Pension Calculator - Calculates UK pension withdrawal tax. Registered in Unity Catalog for governance.'
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
      "withdrawal_amount": withdrawal_amount,
      "tax_free_portion": None,
      "taxable_portion": None,
      "tax_amount": None,
      "status": "Member not found",
      "member_name": None,
      "member_age": None,
      "net_withdrawal": None
    }

  profile = profile_df.first()
  age = int(profile.age)
  total_pension = int(profile.super_balance)

  # UK allows 25% tax-free lump sum
  tax_free_allowance = total_pension * 0.25

  if withdrawal_amount <= tax_free_allowance:
    tax_free = withdrawal_amount
    taxable = 0
    tax_amount = 0
    status = "Tax-free withdrawal (within 25% allowance)"
  else:
    tax_free = tax_free_allowance
    taxable = withdrawal_amount - tax_free_allowance

    # UK income tax bands (2024-25)
    if taxable <= 12570:
      tax_rate = 0.0  # Personal allowance
    elif taxable <= 50270:
      tax_rate = 0.20  # Basic rate
    elif taxable <= 125140:
      tax_rate = 0.40  # Higher rate
    else:
      tax_rate = 0.45  # Additional rate

    tax_amount = taxable * tax_rate
    status = f"Partial tax at {tax_rate*100:.0f}% (over 25% allowance)"

  return {
    "withdrawal_amount": withdrawal_amount,
    "tax_free_portion": round(tax_free, 2),
    "taxable_portion": round(taxable, 2),
    "tax_amount": round(tax_amount, 2),
    "status": status,
    "member_name": profile.name,
    "member_age": age,
    "net_withdrawal": round(withdrawal_amount - tax_amount, 2)
  }
$$;

-- 2. Check State Pension Impact
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.check_uk_state_pension(
  member_id STRING COMMENT 'Member identifier',
  proposed_withdrawal DOUBLE COMMENT 'Proposed private pension withdrawal'
)
RETURNS STRUCT<
  member_name: STRING,
  current_pension_balance: DOUBLE,
  after_withdrawal_balance: DOUBLE,
  state_pension_age: INT,
  eligible_for_state_pension: BOOLEAN,
  annual_state_pension: DOUBLE,
  combined_annual_income: DOUBLE,
  income_assessment: STRING
>
LANGUAGE PYTHON
COMMENT 'MCP Server: DWP State Pension Calculator - Estimates UK state and private pension income.'
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
      "current_pension_balance": None,
      "after_withdrawal_balance": None,
      "state_pension_age": None,
      "eligible_for_state_pension": None,
      "annual_state_pension": None,
      "combined_annual_income": None,
      "income_assessment": "Member not found"
    }

  profile = profile_df.first()
  balance = int(profile.super_balance)
  age = int(profile.age)

  # UK State Pension Age is 66-67 (gradually increasing)
  state_pension_age = 67
  eligible = age >= state_pension_age

  # Full new State Pension: £221.20/week (2024-25)
  annual_state_pension = 11502.40 if eligible else 0

  after_balance = balance - int(proposed_withdrawal)

  # 4% safe withdrawal from private pension
  annual_private_pension = after_balance * 0.04
  combined_income = annual_state_pension + annual_private_pension

  # UK average retirement income ~£15,000-20,000
  if combined_income >= 25000:
    assessment = "Comfortable - above average retirement income"
  elif combined_income >= 15000:
    assessment = "Adequate - meets typical UK retirement needs"
  else:
    assessment = "Modest - covers basic living expenses"

  return {
    "member_name": profile.name,
    "current_pension_balance": float(balance),
    "after_withdrawal_balance": float(after_balance),
    "state_pension_age": state_pension_age,
    "eligible_for_state_pension": eligible,
    "annual_state_pension": round(annual_state_pension, 2),
    "combined_annual_income": round(combined_income, 2),
    "income_assessment": assessment
  }
$$;

-- 3. Project UK Pension Balance
CREATE OR REPLACE FUNCTION super_advisory_demo.mcp_tools.project_uk_pension_balance(
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
COMMENT 'MCP Server: UK Pension Projection Tool - Projects pension pot over retirement.'
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

  # Conservative UK investment return
  annual_return = 0.05  # 5% average

  # Drawdown rates by age
  if age < 65:
    drawdown_pct = 0.03
  elif age < 75:
    drawdown_pct = 0.04
  else:
    drawdown_pct = 0.05

  annual_drawdown = balance * drawdown_pct

  # Project forward
  for year in range(min(years, 20)):
    balance = balance * (1 + annual_return) - annual_drawdown
    if balance <= 0:
      break

    current_age = age + year
    if current_age < 65:
      drawdown_pct = 0.03
    elif current_age < 75:
      drawdown_pct = 0.04
    else:
      drawdown_pct = 0.05

    annual_drawdown = balance * drawdown_pct

  return {
    "member_name": profile.name,
    "current_age": age,
    "current_balance": float(profile.super_balance),
    "annual_return": f"{annual_return*100:.1f}%",
    "projection_summary": f"Pension pot {'depleted' if balance <= 0 else 'sustained'} after {years} years",
    "balance_depleted": balance <= 0
  }
$$;
