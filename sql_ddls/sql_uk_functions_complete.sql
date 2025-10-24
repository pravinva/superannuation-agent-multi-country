-- ============================================================================
-- UK PENSION CALCULATOR FUNCTIONS (COMPLETE SET)
-- 3 Functions matching Australia's comprehensive coverage
-- ============================================================================

-- Function 1: UK Pension Tax Calculator (Enhanced)
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Member age in years',
  pension_pot DOUBLE COMMENT 'Total pension pot value in GBP',
  withdrawal_amount DOUBLE COMMENT 'Proposed withdrawal amount in GBP',
  withdrawal_type STRING COMMENT 'Withdrawal type: Lump_Sum, Drawdown, or Annuity'
)
RETURNS STRUCT<
  member_id: STRING,
  withdrawal_type: STRING,
  withdrawal_amount: DOUBLE,
  tax_free_lump_sum: DOUBLE,
  taxable_amount: DOUBLE,
  tax_amount: DOUBLE,
  net_withdrawal: DOUBLE,
  status: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'UK: Pension Tax Calculator - Tax-free lump sum and withdrawal tax per Finance Act 2004'
RETURN STRUCT(
  member_id,
  withdrawal_type,
  withdrawal_amount,
  
  -- 25% tax-free lump sum (up to £268,275 lifetime limit for 2024/25)
  CASE 
    WHEN UPPER(withdrawal_type) = 'LUMP_SUM' THEN
      LEAST(withdrawal_amount, pension_pot * 0.25, 268275.0)
    WHEN UPPER(withdrawal_type) = 'DRAWDOWN' THEN
      -- Each drawdown can take 25% tax-free
      withdrawal_amount * 0.25
    ELSE 0.0  -- Annuity typically not tax-free
  END as tax_free_lump_sum,
  
  -- Taxable amount (above 25% tax-free portion)
  CASE 
    WHEN UPPER(withdrawal_type) = 'LUMP_SUM' THEN
      GREATEST(0.0, withdrawal_amount - LEAST(withdrawal_amount, pension_pot * 0.25, 268275.0))
    WHEN UPPER(withdrawal_type) = 'DRAWDOWN' THEN
      withdrawal_amount * 0.75  -- 75% is taxable
    ELSE withdrawal_amount  -- Annuity fully taxable
  END as taxable_amount,
  
  -- Income tax at basic rate 20% (simplified - actual depends on total income)
  CASE 
    WHEN UPPER(withdrawal_type) = 'LUMP_SUM' THEN
      GREATEST(0.0, withdrawal_amount - LEAST(withdrawal_amount, pension_pot * 0.25, 268275.0)) * 0.20
    WHEN UPPER(withdrawal_type) = 'DRAWDOWN' THEN
      (withdrawal_amount * 0.75) * 0.20
    ELSE withdrawal_amount * 0.20
  END as tax_amount,
  
  -- Net withdrawal amount
  withdrawal_amount - (CASE 
    WHEN UPPER(withdrawal_type) = 'LUMP_SUM' THEN
      GREATEST(0.0, withdrawal_amount - LEAST(withdrawal_amount, pension_pot * 0.25, 268275.0)) * 0.20
    WHEN UPPER(withdrawal_type) = 'DRAWDOWN' THEN
      (withdrawal_amount * 0.75) * 0.20
    ELSE withdrawal_amount * 0.20
  END) as net_withdrawal,
  
  -- Status message
  CASE 
    WHEN UPPER(withdrawal_type) = 'LUMP_SUM' AND withdrawal_amount <= (pension_pot * 0.25) THEN 
      'Tax-free withdrawal (within 25% tax-free allowance)'
    WHEN UPPER(withdrawal_type) = 'LUMP_SUM' THEN
      'Partially taxable (25% tax-free, remainder taxed at 20% basic rate)'
    WHEN UPPER(withdrawal_type) = 'DRAWDOWN' THEN
      '25% of each drawdown is tax-free, 75% taxed as income'
    ELSE
      'Annuity payments fully taxable as income'
  END as status,
  
  'Finance Act 2004, Part 4 - Pension Schemes; Finance Act 2024 - Lump Sum Allowance' as regulation,
  'HM Revenue & Customs (HMRC)' as authority
);


-- Function 2: UK State Pension Calculator
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.uk_check_state_pension(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Member age in years',
  ni_qualifying_years INT COMMENT 'National Insurance qualifying years',
  private_pension_income DOUBLE COMMENT 'Annual income from private pensions in GBP'
)
RETURNS STRUCT<
  member_id: STRING,
  current_age: INT,
  state_pension_age: INT,
  ni_years: INT,
  min_qualifying_years: INT,
  full_state_pension_eligible: BOOLEAN,
  weekly_state_pension: DOUBLE,
  annual_state_pension: DOUBLE,
  combined_annual_income: DOUBLE,
  pension_status: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'UK: State Pension Calculator - New State Pension eligibility and amounts per Pensions Act 2014'
RETURN STRUCT(
  member_id,
  member_age as current_age,
  
  -- State Pension age (currently 66, rising to 67 between 2026-2028)
  CASE 
    WHEN member_age < 66 THEN 66  -- Current State Pension age
    ELSE 67  -- Future State Pension age
  END as state_pension_age,
  
  ni_qualifying_years as ni_years,
  
  10 as min_qualifying_years,  -- Minimum to get any State Pension
  
  -- Full State Pension eligibility (need 35 qualifying years)
  ni_qualifying_years >= 35 as full_state_pension_eligible,
  
  -- Weekly State Pension amount (2024/25 rates)
  CASE 
    WHEN ni_qualifying_years < 10 THEN 0.0  -- Not eligible
    WHEN ni_qualifying_years >= 35 THEN 221.20  -- Full new State Pension
    ELSE 221.20 * (CAST(ni_qualifying_years AS DOUBLE) / 35.0)  -- Prorated
  END as weekly_state_pension,
  
  -- Annual State Pension
  (CASE 
    WHEN ni_qualifying_years < 10 THEN 0.0
    WHEN ni_qualifying_years >= 35 THEN 221.20
    ELSE 221.20 * (CAST(ni_qualifying_years AS DOUBLE) / 35.0)
  END) * 52.0 as annual_state_pension,
  
  -- Combined retirement income (State Pension + private pensions)
  ((CASE 
    WHEN ni_qualifying_years < 10 THEN 0.0
    WHEN ni_qualifying_years >= 35 THEN 221.20
    ELSE 221.20 * (CAST(ni_qualifying_years AS DOUBLE) / 35.0)
  END) * 52.0) + private_pension_income as combined_annual_income,
  
  -- Pension status message
  CASE 
    WHEN member_age < 66 THEN 
      CONCAT('Not yet eligible - State Pension age is 66 (currently age ', 
             CAST(member_age AS STRING), ')')
    WHEN ni_qualifying_years < 10 THEN 
      CONCAT('Not eligible - need minimum 10 qualifying years (currently have ', 
             CAST(ni_qualifying_years AS STRING), ')')
    WHEN ni_qualifying_years >= 35 THEN 
      CONCAT('Eligible for Full New State Pension - £221.20/week (£', 
             FORMAT_NUMBER(221.20 * 52.0, 2), '/year)')
    ELSE 
      CONCAT('Eligible for Partial State Pension based on ', 
             CAST(ni_qualifying_years AS STRING), ' qualifying years - £',
             FORMAT_NUMBER((221.20 * (CAST(ni_qualifying_years AS DOUBLE) / 35.0)) * 52.0, 2),
             '/year')
  END as pension_status,
  
  'Pensions Act 2014, Section 4 - New State Pension; Pensions Act 2007 - State Pension Age' as regulation,
  'Department for Work and Pensions (DWP)' as authority
);


-- Function 3: UK Pension Drawdown Projection
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.uk_project_pension_balance(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Current age in years',
  pension_pot DOUBLE COMMENT 'Current pension pot value in GBP',
  annual_drawdown DOUBLE COMMENT 'Planned annual drawdown amount in GBP',
  projection_years INT COMMENT 'Number of years to project'
)
RETURNS STRUCT<
  member_id: STRING,
  current_age: INT,
  current_pension_pot: DOUBLE,
  annual_drawdown: DOUBLE,
  projection_years: INT,
  retirement_phase: STRING,
  annual_return_rate: DOUBLE,
  drawdown_rate: DOUBLE,
  estimated_final_balance: DOUBLE,
  balance_depleted: BOOLEAN,
  years_until_depletion: INT,
  summary: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'UK: Pension Drawdown Projection - Projects pension pot with flexible drawdown per FCA guidance'
RETURN STRUCT(
  member_id,
  member_age as current_age,
  pension_pot as current_pension_pot,
  annual_drawdown,
  LEAST(projection_years, 30) as projection_years,
  
  -- Retirement phase
  CASE 
    WHEN member_age < 55 THEN 'Pre-Access (Cannot access pension yet)'
    WHEN member_age < 65 THEN 'Early Drawdown (55-64)'
    WHEN member_age < 75 THEN 'Mid Drawdown (65-74)'
    ELSE 'Late Drawdown (75+)'
  END as retirement_phase,
  
  -- Annual return rate (conservative UK pension growth estimates)
  CASE 
    WHEN member_age < 55 THEN 0.05   -- 5% growth pre-access
    WHEN member_age < 65 THEN 0.045  -- 4.5% early drawdown
    WHEN member_age < 75 THEN 0.04   -- 4% mid drawdown
    ELSE 0.035                        -- 3.5% late drawdown (more conservative)
  END as annual_return_rate,
  
  -- Drawdown rate as percentage of pot
  CASE 
    WHEN pension_pot > 0 THEN (annual_drawdown / pension_pot)
    ELSE 0.0
  END as drawdown_rate,
  
  -- Simplified projection of final balance
  CASE 
    WHEN member_age < 55 THEN
      -- Cannot draw down yet, only growth
      pension_pot * POWER(1.05, CAST(LEAST(projection_years, 55 - member_age) AS DOUBLE))
    ELSE
      -- Drawdown phase
      pension_pot * POWER(
        1.0 + CASE 
          WHEN member_age < 65 THEN 0.045
          WHEN member_age < 75 THEN 0.04
          ELSE 0.035
        END,
        CAST(LEAST(projection_years, 30) AS DOUBLE)
      ) - (annual_drawdown * CAST(LEAST(projection_years, 30) AS DOUBLE))
  END as estimated_final_balance,
  
  -- Check if balance depleted
  CASE 
    WHEN member_age < 55 THEN FALSE  -- Not drawing down yet
    WHEN annual_drawdown = 0 THEN FALSE
    ELSE (pension_pot * POWER(
      1.0 + CASE 
        WHEN member_age < 65 THEN 0.045
        WHEN member_age < 75 THEN 0.04
        ELSE 0.035
      END,
      CAST(LEAST(projection_years, 30) AS DOUBLE)
    ) - (annual_drawdown * CAST(LEAST(projection_years, 30) AS DOUBLE))) <= 0
  END as balance_depleted,
  
  -- Estimate years until depletion (simplified)
  CASE 
    WHEN member_age < 55 THEN 0
    WHEN annual_drawdown = 0 THEN 0
    WHEN annual_drawdown > (pension_pot * CASE 
      WHEN member_age < 65 THEN 0.045
      WHEN member_age < 75 THEN 0.04
      ELSE 0.035
    END) THEN
      -- Drawdown exceeds growth, calculate years to depletion
      CAST(pension_pot / (annual_drawdown - (pension_pot * CASE 
        WHEN member_age < 65 THEN 0.045
        WHEN member_age < 75 THEN 0.04
        ELSE 0.035
      END)) AS INT)
    ELSE 0  -- Sustainable drawdown
  END as years_until_depletion,
  
  -- Summary message
  CASE 
    WHEN member_age < 55 THEN
      CONCAT('Cannot access pension until age 55 (currently ', 
             CAST(member_age AS STRING), ')')
    WHEN annual_drawdown = 0 THEN
      CONCAT('No drawdown planned - projected pot: £',
             FORMAT_NUMBER(
               pension_pot * POWER(
                 1.0 + CASE 
                   WHEN member_age < 65 THEN 0.045
                   WHEN member_age < 75 THEN 0.04
                   ELSE 0.035
                 END,
                 CAST(LEAST(projection_years, 30) AS DOUBLE)
               ),
               0
             ),
             ' after ', CAST(LEAST(projection_years, 30) AS STRING), ' years')
    WHEN (pension_pot * POWER(
      1.0 + CASE 
        WHEN member_age < 65 THEN 0.045
        WHEN member_age < 75 THEN 0.04
        ELSE 0.035
      END,
      CAST(LEAST(projection_years, 30) AS DOUBLE)
    ) - (annual_drawdown * CAST(LEAST(projection_years, 30) AS DOUBLE))) <= 0 THEN
      CONCAT('Pension pot depleted within ', 
             CAST(
               CAST(pension_pot / (annual_drawdown - (pension_pot * CASE 
                 WHEN member_age < 65 THEN 0.045
                 WHEN member_age < 75 THEN 0.04
                 ELSE 0.035
               END)) AS INT)
             AS STRING),
             ' years at current drawdown rate')
    ELSE
      CONCAT('Projected balance: £',
             FORMAT_NUMBER(
               pension_pot * POWER(
                 1.0 + CASE 
                   WHEN member_age < 65 THEN 0.045
                   WHEN member_age < 75 THEN 0.04
                   ELSE 0.035
                 END,
                 CAST(LEAST(projection_years, 30) AS DOUBLE)
               ) - (annual_drawdown * CAST(LEAST(projection_years, 30) AS DOUBLE)),
               0
             ),
             ' after ', CAST(LEAST(projection_years, 30) AS STRING), ' years',
             ' (sustainable drawdown)')
  END as summary,
  
  'Pension Schemes Act 2015 - Pension Freedoms; FCA Handbook - Pension Drawdown Rules' as regulation,
  'Financial Conduct Authority (FCA) & Pension Wise' as authority
);


-- ============================================================================
-- TEST QUERIES FOR UK FUNCTIONS
-- ============================================================================

-- Test 1: Pension tax calculation with lump sum
SELECT super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
  'TEST-UK-001', 60, 300000, 75000, 'Lump_Sum'
) as result;

-- Test 2: State Pension eligibility
SELECT super_advisory_demo.pension_calculators.uk_check_state_pension(
  'TEST-UK-002', 66, 35, 15000
) as result;

-- Test 3: Pension drawdown projection
SELECT super_advisory_demo.pension_calculators.uk_project_pension_balance(
  'TEST-UK-003', 60, 400000, 20000, 25
) as result;
