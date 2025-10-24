-- ============================================================================
-- USA PENSION CALCULATOR FUNCTIONS (COMPLETE SET)
-- 3 Functions matching Australia's comprehensive coverage
-- ============================================================================

-- Function 1: 401(k)/IRA Tax Calculator (Enhanced)
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_calculate_401k_tax(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Member age in years',
  account_balance DOUBLE COMMENT 'Current 401(k)/IRA balance in USD',
  withdrawal_amount DOUBLE COMMENT 'Proposed withdrawal amount in USD',
  account_type STRING COMMENT 'Account type: 401k, Traditional_IRA, or Roth_IRA'
)
RETURNS STRUCT<
  member_id: STRING,
  account_type: STRING,
  withdrawal_amount: DOUBLE,
  early_withdrawal_penalty: DOUBLE,
  income_tax_amount: DOUBLE,
  total_tax: DOUBLE,
  net_withdrawal: DOUBLE,
  status: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'USA: 401(k)/IRA Tax Calculator - Withdrawal tax and penalties per IRC Sections 401(k) and 72(t)'
RETURN STRUCT(
  member_id,
  account_type,
  withdrawal_amount,
  
  -- Early withdrawal penalty (10% if under 59.5, except for Roth IRA qualified withdrawals)
  CASE 
    WHEN member_age >= 59 THEN 0.0
    WHEN UPPER(account_type) = 'ROTH_IRA' THEN 0.0  -- Roth contributions can be withdrawn anytime
    ELSE withdrawal_amount * 0.10
  END as early_withdrawal_penalty,
  
  -- Federal income tax (simplified brackets for 2024)
  CASE 
    WHEN UPPER(account_type) = 'ROTH_IRA' THEN 0.0  -- Roth withdrawals are tax-free
    WHEN withdrawal_amount <= 11000 THEN withdrawal_amount * 0.10
    WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
    WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
    WHEN withdrawal_amount <= 182100 THEN withdrawal_amount * 0.24
    ELSE withdrawal_amount * 0.32
  END as income_tax_amount,
  
  -- Total tax
  (CASE 
    WHEN member_age >= 59 THEN 0.0
    WHEN UPPER(account_type) = 'ROTH_IRA' THEN 0.0
    ELSE withdrawal_amount * 0.10
  END) + (CASE 
    WHEN UPPER(account_type) = 'ROTH_IRA' THEN 0.0
    WHEN withdrawal_amount <= 11000 THEN withdrawal_amount * 0.10
    WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
    WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
    WHEN withdrawal_amount <= 182100 THEN withdrawal_amount * 0.24
    ELSE withdrawal_amount * 0.32
  END) as total_tax,
  
  -- Net withdrawal amount
  withdrawal_amount - (
    (CASE 
      WHEN member_age >= 59 THEN 0.0
      WHEN UPPER(account_type) = 'ROTH_IRA' THEN 0.0
      ELSE withdrawal_amount * 0.10
    END) + (CASE 
      WHEN UPPER(account_type) = 'ROTH_IRA' THEN 0.0
      WHEN withdrawal_amount <= 11000 THEN withdrawal_amount * 0.10
      WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
      WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
      WHEN withdrawal_amount <= 182100 THEN withdrawal_amount * 0.24
      ELSE withdrawal_amount * 0.32
    END)
  ) as net_withdrawal,
  
  -- Status message
  CASE 
    WHEN UPPER(account_type) = 'ROTH_IRA' THEN 
      CONCAT('Tax-free withdrawal from Roth IRA (age ', CAST(member_age AS STRING), ')')
    WHEN member_age >= 59 THEN 
      CONCAT('Subject to income tax only (age ', CAST(member_age AS STRING), ' >= 59.5)')
    ELSE 
      CONCAT('Subject to 10% early withdrawal penalty and income tax (age ', 
             CAST(member_age AS STRING), ' < 59.5)')
  END as status,
  
  'Internal Revenue Code, Section 401(k), Section 408 (IRAs), Section 72(t)' as regulation,
  'Internal Revenue Service (IRS)' as authority
);


-- Function 2: Social Security Benefit Calculator
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_check_social_security(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Member age in years',
  monthly_earnings_history DOUBLE COMMENT 'Average indexed monthly earnings in USD',
  claimed_age INT COMMENT 'Age planning to claim SS benefits (62-70)',
  other_retirement_income DOUBLE COMMENT 'Annual income from other retirement sources'
)
RETURNS STRUCT<
  member_id: STRING,
  current_age: INT,
  claim_age: INT,
  full_retirement_age: INT,
  estimated_monthly_benefit: DOUBLE,
  estimated_annual_benefit: DOUBLE,
  reduction_or_increase_pct: DOUBLE,
  combined_annual_income: DOUBLE,
  benefit_status: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'USA: Social Security Benefit Calculator - Estimates SS benefits based on claiming age per SSA rules'
RETURN STRUCT(
  member_id,
  member_age as current_age,
  claimed_age as claim_age,
  
  -- Full Retirement Age (FRA) - for those born 1960 or later, FRA is 67
  67 as full_retirement_age,
  
  -- Calculate Primary Insurance Amount (PIA) - simplified formula
  -- Actual SSA formula has bend points, this is simplified
  -- Base benefit at FRA (assuming average of $3,500/month for 2024)
  CASE 
    WHEN claimed_age < 62 THEN 0.0  -- Can't claim before 62
    WHEN claimed_age = 62 THEN monthly_earnings_history * 0.70  -- 30% reduction
    WHEN claimed_age = 63 THEN monthly_earnings_history * 0.75
    WHEN claimed_age = 64 THEN monthly_earnings_history * 0.80
    WHEN claimed_age = 65 THEN monthly_earnings_history * 0.867
    WHEN claimed_age = 66 THEN monthly_earnings_history * 0.933
    WHEN claimed_age = 67 THEN monthly_earnings_history * 1.0   -- Full benefit at FRA
    WHEN claimed_age = 68 THEN monthly_earnings_history * 1.08  -- 8% increase per year after FRA
    WHEN claimed_age = 69 THEN monthly_earnings_history * 1.16
    WHEN claimed_age >= 70 THEN monthly_earnings_history * 1.24 -- Max at age 70
    ELSE monthly_earnings_history
  END as estimated_monthly_benefit,
  
  -- Annual benefit
  (CASE 
    WHEN claimed_age < 62 THEN 0.0
    WHEN claimed_age = 62 THEN monthly_earnings_history * 0.70
    WHEN claimed_age = 63 THEN monthly_earnings_history * 0.75
    WHEN claimed_age = 64 THEN monthly_earnings_history * 0.80
    WHEN claimed_age = 65 THEN monthly_earnings_history * 0.867
    WHEN claimed_age = 66 THEN monthly_earnings_history * 0.933
    WHEN claimed_age = 67 THEN monthly_earnings_history * 1.0
    WHEN claimed_age = 68 THEN monthly_earnings_history * 1.08
    WHEN claimed_age = 69 THEN monthly_earnings_history * 1.16
    WHEN claimed_age >= 70 THEN monthly_earnings_history * 1.24
    ELSE monthly_earnings_history
  END) * 12.0 as estimated_annual_benefit,
  
  -- Reduction or increase percentage from FRA
  CASE 
    WHEN claimed_age < 62 THEN 0.0
    WHEN claimed_age = 62 THEN -30.0
    WHEN claimed_age = 63 THEN -25.0
    WHEN claimed_age = 64 THEN -20.0
    WHEN claimed_age = 65 THEN -13.3
    WHEN claimed_age = 66 THEN -6.7
    WHEN claimed_age = 67 THEN 0.0
    WHEN claimed_age = 68 THEN 8.0
    WHEN claimed_age = 69 THEN 16.0
    WHEN claimed_age >= 70 THEN 24.0
    ELSE 0.0
  END as reduction_or_increase_pct,
  
  -- Combined retirement income (SS + other sources)
  ((CASE 
    WHEN claimed_age < 62 THEN 0.0
    WHEN claimed_age = 62 THEN monthly_earnings_history * 0.70
    WHEN claimed_age = 63 THEN monthly_earnings_history * 0.75
    WHEN claimed_age = 64 THEN monthly_earnings_history * 0.80
    WHEN claimed_age = 65 THEN monthly_earnings_history * 0.867
    WHEN claimed_age = 66 THEN monthly_earnings_history * 0.933
    WHEN claimed_age = 67 THEN monthly_earnings_history * 1.0
    WHEN claimed_age = 68 THEN monthly_earnings_history * 1.08
    WHEN claimed_age = 69 THEN monthly_earnings_history * 1.16
    WHEN claimed_age >= 70 THEN monthly_earnings_history * 1.24
    ELSE monthly_earnings_history
  END) * 12.0) + other_retirement_income as combined_annual_income,
  
  -- Status message
  CASE 
    WHEN member_age < 62 THEN 
      CONCAT('Not yet eligible - minimum claim age is 62 (currently ', 
             CAST(member_age AS STRING), ')')
    WHEN claimed_age < 62 THEN 
      'Cannot claim before age 62'
    WHEN claimed_age = 67 THEN 
      'Claiming at Full Retirement Age (FRA) - 100% of benefit'
    WHEN claimed_age < 67 THEN 
      CONCAT('Early claiming (age ', CAST(claimed_age AS STRING), 
             ') - reduced benefit by ', 
             CAST(ABS(CASE 
               WHEN claimed_age = 62 THEN -30.0
               WHEN claimed_age = 63 THEN -25.0
               WHEN claimed_age = 64 THEN -20.0
               WHEN claimed_age = 65 THEN -13.3
               WHEN claimed_age = 66 THEN -6.7
               ELSE 0.0
             END) AS STRING), '%')
    WHEN claimed_age > 67 THEN 
      CONCAT('Delayed claiming (age ', CAST(claimed_age AS STRING), 
             ') - increased benefit by ', 
             CAST(CASE 
               WHEN claimed_age = 68 THEN 8.0
               WHEN claimed_age = 69 THEN 16.0
               WHEN claimed_age >= 70 THEN 24.0
               ELSE 0.0
             END AS STRING), '%')
    ELSE 'Standard benefit'
  END as benefit_status,
  
  'Social Security Act, Title II - Old-Age, Survivors, and Disability Insurance' as regulation,
  'Social Security Administration (SSA)' as authority
);


-- Function 3: Retirement Account Projection (401k/IRA)
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_project_retirement_balance(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Current age in years',
  account_balance DOUBLE COMMENT 'Current total retirement account balance in USD',
  annual_contribution DOUBLE COMMENT 'Annual contribution amount in USD',
  retirement_age INT COMMENT 'Planned retirement age',
  projection_years INT COMMENT 'Number of years to project'
)
RETURNS STRUCT<
  member_id: STRING,
  current_age: INT,
  current_balance: DOUBLE,
  retirement_age: INT,
  projection_years: INT,
  retirement_phase: STRING,
  annual_return_rate: DOUBLE,
  annual_withdrawal_rate: DOUBLE,
  estimated_final_balance: DOUBLE,
  rmd_required: BOOLEAN,
  rmd_age: INT,
  balance_depleted: BOOLEAN,
  summary: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'USA: Retirement Account Projection - Projects 401(k)/IRA balance with RMD considerations'
RETURN STRUCT(
  member_id,
  member_age as current_age,
  account_balance as current_balance,
  retirement_age,
  LEAST(projection_years, 30) as projection_years,
  
  -- Determine retirement phase
  CASE 
    WHEN member_age < retirement_age THEN 'Accumulation (Pre-retirement)'
    WHEN member_age < 65 THEN 'Early Retirement (Before Medicare)'
    WHEN member_age < 73 THEN 'Mid Retirement (Before RMD)'
    ELSE 'Late Retirement (RMD Required)'
  END as retirement_phase,
  
  -- Annual return rate by phase (conservative estimates)
  CASE 
    WHEN member_age < retirement_age THEN 0.08  -- 8% growth phase
    WHEN member_age < 65 THEN 0.07              -- 7% early retirement
    WHEN member_age < 73 THEN 0.06              -- 6% mid retirement
    ELSE 0.05                                    -- 5% late retirement (more conservative)
  END as annual_return_rate,
  
  -- Annual withdrawal rate (4% rule standard, higher for RMD phase)
  CASE 
    WHEN member_age < retirement_age THEN 0.0   -- Still contributing
    WHEN member_age < 73 THEN 0.04               -- 4% safe withdrawal rule
    WHEN member_age < 75 THEN 0.0366             -- RMD rate at 73
    WHEN member_age < 80 THEN 0.04               -- RMD rate 75-79
    ELSE 0.05                                     -- Higher RMD rate 80+
  END as annual_withdrawal_rate,
  
  -- Simplified projection
  CASE 
    WHEN member_age < retirement_age THEN
      -- Accumulation phase with contributions
      account_balance * POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (annual_contribution * ((POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.08))
    ELSE
      -- Withdrawal phase
      account_balance * POWER(
        1.0 + CASE 
          WHEN member_age < 65 THEN 0.07
          WHEN member_age < 73 THEN 0.06
          ELSE 0.05
        END,
        CAST(LEAST(projection_years, 30) AS DOUBLE)
      ) - (
        account_balance * 
        CASE 
          WHEN member_age < 73 THEN 0.04
          WHEN member_age < 75 THEN 0.0366
          WHEN member_age < 80 THEN 0.04
          ELSE 0.05
        END * CAST(LEAST(projection_years, 30) AS DOUBLE)
      )
  END as estimated_final_balance,
  
  -- Required Minimum Distribution (RMD) required after age 73
  member_age >= 73 OR (member_age + projection_years) >= 73 as rmd_required,
  
  73 as rmd_age,
  
  -- Check if balance depleted
  CASE 
    WHEN member_age < retirement_age THEN FALSE
    ELSE (account_balance * POWER(
      1.0 + CASE 
        WHEN member_age < 65 THEN 0.07
        WHEN member_age < 73 THEN 0.06
        ELSE 0.05
      END,
      CAST(LEAST(projection_years, 30) AS DOUBLE)
    ) - (
      account_balance * 
      CASE 
        WHEN member_age < 73 THEN 0.04
        WHEN member_age < 75 THEN 0.0366
        WHEN member_age < 80 THEN 0.04
        ELSE 0.05
      END * CAST(LEAST(projection_years, 30) AS DOUBLE)
    )) <= 0
  END as balance_depleted,
  
  -- Summary message
  CASE 
    WHEN member_age < retirement_age THEN
      CONCAT('Accumulation phase: Projected balance USD ', 
             FORMAT_NUMBER(
               account_balance * POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
               (annual_contribution * ((POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.08)),
               0
             ),
             ' at retirement (age ', CAST(retirement_age AS STRING), ')')
    WHEN (account_balance * POWER(
      1.0 + CASE 
        WHEN member_age < 65 THEN 0.07
        WHEN member_age < 73 THEN 0.06
        ELSE 0.05
      END,
      CAST(LEAST(projection_years, 30) AS DOUBLE)
    ) - (
      account_balance * 
      CASE 
        WHEN member_age < 73 THEN 0.04
        WHEN member_age < 75 THEN 0.0366
        WHEN member_age < 80 THEN 0.04
        ELSE 0.05
      END * CAST(LEAST(projection_years, 30) AS DOUBLE)
    )) <= 0 THEN
      CONCAT('Balance depleted within ', CAST(LEAST(projection_years, 30) AS STRING), ' years')
    ELSE
      CONCAT('Projected balance: USD ',
             FORMAT_NUMBER(
               account_balance * POWER(
                 1.0 + CASE 
                   WHEN member_age < 65 THEN 0.07
                   WHEN member_age < 73 THEN 0.06
                   ELSE 0.05
                 END,
                 CAST(LEAST(projection_years, 30) AS DOUBLE)
               ) - (
                 account_balance * 
                 CASE 
                   WHEN member_age < 73 THEN 0.04
                   WHEN member_age < 75 THEN 0.0366
                   WHEN member_age < 80 THEN 0.04
                   ELSE 0.05
                 END * CAST(LEAST(projection_years, 30) AS DOUBLE)
               ),
               0
             ),
             ' after ', CAST(LEAST(projection_years, 30) AS STRING), ' years',
             CASE WHEN member_age >= 73 OR (member_age + projection_years) >= 73 
                  THEN ' (RMD required at age 73)' 
                  ELSE '' 
             END)
  END as summary,
  
  'SECURE 2.0 Act (2023), IRC Section 401(a)(9) - Required Minimum Distributions' as regulation,
  'Internal Revenue Service (IRS)' as authority
);


-- ============================================================================
-- TEST QUERIES FOR USA FUNCTIONS
-- ============================================================================

-- Test 1: 401(k) tax calculation
SELECT super_advisory_demo.pension_calculators.us_calculate_401k_tax(
  'TEST-US-001', 55, 400000, 50000, '401k'
) as result;

-- Test 2: Social Security benefit estimation
SELECT super_advisory_demo.pension_calculators.us_check_social_security(
  'TEST-US-002', 62, 3000, 67, 20000
) as result;

-- Test 3: Retirement balance projection
SELECT super_advisory_demo.pension_calculators.us_project_retirement_balance(
  'TEST-US-003', 55, 500000, 10000, 65, 20
) as result;
