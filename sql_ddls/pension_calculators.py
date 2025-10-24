-- ============================================================================
-- PENSION CALCULATORS - DATABRICKS SQL (FIXED VERSION)
-- Schema: pension_calculators
-- No PySpark, No table references, 100% Databricks compliant
-- ============================================================================

-- Step 1: Create the schema
CREATE SCHEMA IF NOT EXISTS super_advisory_demo.pension_calculators
COMMENT 'Pension calculator functions for retirement advisory - country-specific calculations with regulatory compliance';

-- Verify schema creation
DESCRIBE SCHEMA super_advisory_demo.pension_calculators;

-- ============================================================================
-- AUSTRALIA FUNCTIONS
-- ============================================================================

-- Function 1: ATO Tax Calculator
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.au_calculate_tax(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Member age in years',
  preservation_age INT COMMENT 'Preservation age threshold (typically 60)',
  super_balance DOUBLE COMMENT 'Current superannuation balance in AUD',
  withdrawal_amount DOUBLE COMMENT 'Proposed withdrawal amount in AUD'
)
RETURNS STRUCT<
  member_id: STRING,
  withdrawal_amount: DOUBLE,
  tax_free_component: DOUBLE,
  taxable_component: DOUBLE,
  tax_amount: DOUBLE,
  tax_rate: DOUBLE,
  net_withdrawal: DOUBLE,
  status: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'Australia: ATO Tax Calculator - Superannuation withdrawal tax per Division 301'
RETURN STRUCT(
  member_id,
  withdrawal_amount,
  
  CASE 
    WHEN member_age >= preservation_age THEN withdrawal_amount
    ELSE 0.0
  END as tax_free_component,
  
  CASE 
    WHEN member_age >= preservation_age THEN 0.0
    ELSE withdrawal_amount
  END as taxable_component,
  
  CASE 
    WHEN member_age >= preservation_age THEN 0.0
    WHEN withdrawal_amount <= 45000 THEN withdrawal_amount * 0.19
    WHEN withdrawal_amount <= 120000 THEN withdrawal_amount * 0.325
    ELSE withdrawal_amount * 0.37
  END as tax_amount,
  
  CASE 
    WHEN member_age >= preservation_age THEN 0.0
    WHEN withdrawal_amount <= 45000 THEN 0.19
    WHEN withdrawal_amount <= 120000 THEN 0.325
    ELSE 0.37
  END as tax_rate,
  
  withdrawal_amount - CASE 
    WHEN member_age >= preservation_age THEN 0.0
    WHEN withdrawal_amount <= 45000 THEN withdrawal_amount * 0.19
    WHEN withdrawal_amount <= 120000 THEN withdrawal_amount * 0.325
    ELSE withdrawal_amount * 0.37
  END as net_withdrawal,
  
  CASE 
    WHEN member_age >= preservation_age THEN 
      CONCAT('Tax-free withdrawal (age ', CAST(member_age AS STRING), 
             ' >= preservation age ', CAST(preservation_age AS STRING), ')')
    ELSE 
      CONCAT('Taxable at ', 
             CAST(CASE 
               WHEN withdrawal_amount <= 45000 THEN 19.0
               WHEN withdrawal_amount <= 120000 THEN 32.5
               ELSE 37.0
             END AS STRING),
             '% (age ', CAST(member_age AS STRING), 
             ' < preservation age ', CAST(preservation_age AS STRING), ')')
  END as status,
  
  'Income Tax Assessment Act 1997, Division 301' as regulation,
  'Australian Taxation Office (ATO)' as authority
);


-- Function 2: Centrelink Age Pension Calculator
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.au_check_pension_impact(
  member_id STRING,
  member_age INT,
  marital_status STRING,
  super_balance DOUBLE,
  other_assets DOUBLE,
  proposed_withdrawal DOUBLE
)
RETURNS STRUCT<
  member_id: STRING,
  current_super_balance: DOUBLE,
  after_withdrawal_balance: DOUBLE,
  total_assessable_assets: DOUBLE,
  age_pension_eligible: BOOLEAN,
  estimated_annual_pension: DOUBLE,
  annual_super_income: DOUBLE,
  combined_annual_income: DOUBLE,
  pension_status: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'Australia: Centrelink Age Pension Calculator - Asset test per Part 3.10'
RETURN STRUCT(
  member_id,
  super_balance as current_super_balance,
  super_balance - proposed_withdrawal as after_withdrawal_balance,
  (super_balance - proposed_withdrawal) + other_assets as total_assessable_assets,
  
  member_age >= 67 as age_pension_eligible,
  
  CASE 
    WHEN member_age < 67 THEN 0.0
    WHEN LOWER(marital_status) IN ('married', 'partnered', 'couple') THEN
      CASE 
        WHEN (super_balance - proposed_withdrawal + other_assets) < 470000 THEN 44855.0
        WHEN (super_balance - proposed_withdrawal + other_assets) < 1012500 THEN
          44855.0 * (1.0 - ((super_balance - proposed_withdrawal + other_assets - 470000.0) / (1012500.0 - 470000.0)))
        ELSE 0.0
      END
    ELSE
      CASE 
        WHEN (super_balance - proposed_withdrawal + other_assets) < 314000 THEN 29754.0
        WHEN (super_balance - proposed_withdrawal + other_assets) < 674000 THEN
          29754.0 * (1.0 - ((super_balance - proposed_withdrawal + other_assets - 314000.0) / (674000.0 - 314000.0)))
        ELSE 0.0
      END
  END as estimated_annual_pension,
  
  (super_balance - proposed_withdrawal) * 0.04 as annual_super_income,
  
  (CASE 
    WHEN member_age < 67 THEN 0.0
    WHEN LOWER(marital_status) IN ('married', 'partnered', 'couple') THEN
      CASE 
        WHEN (super_balance - proposed_withdrawal + other_assets) < 470000 THEN 44855.0
        WHEN (super_balance - proposed_withdrawal + other_assets) < 1012500 THEN
          44855.0 * (1.0 - ((super_balance - proposed_withdrawal + other_assets - 470000.0) / (1012500.0 - 470000.0)))
        ELSE 0.0
      END
    ELSE
      CASE 
        WHEN (super_balance - proposed_withdrawal + other_assets) < 314000 THEN 29754.0
        WHEN (super_balance - proposed_withdrawal + other_assets) < 674000 THEN
          29754.0 * (1.0 - ((super_balance - proposed_withdrawal + other_assets - 314000.0) / (674000.0 - 314000.0)))
        ELSE 0.0
      END
  END) + ((super_balance - proposed_withdrawal) * 0.04) as combined_annual_income,
  
  CASE 
    WHEN member_age < 67 THEN
      CONCAT('Not eligible - age ', CAST(member_age AS STRING), ' < 67 years')
    WHEN LOWER(marital_status) IN ('married', 'partnered', 'couple') THEN
      CASE 
        WHEN (super_balance - proposed_withdrawal + other_assets) < 470000 THEN
          'Eligible for Full Age Pension (Couple, Homeowner)'
        WHEN (super_balance - proposed_withdrawal + other_assets) < 1012500 THEN
          'Eligible for Part Age Pension (Couple, Homeowner)'
        ELSE
          CONCAT('No Age Pension - assets (AUD ', 
                 FORMAT_NUMBER((super_balance - proposed_withdrawal + other_assets), 0), 
                 ') exceed AUD 1,012,500')
      END
    ELSE
      CASE 
        WHEN (super_balance - proposed_withdrawal + other_assets) < 314000 THEN
          'Eligible for Full Age Pension (Single, Homeowner)'
        WHEN (super_balance - proposed_withdrawal + other_assets) < 674000 THEN
          'Eligible for Part Age Pension (Single, Homeowner)'
        ELSE
          CONCAT('No Age Pension - assets (AUD ', 
                 FORMAT_NUMBER((super_balance - proposed_withdrawal + other_assets), 0), 
                 ') exceed AUD 674,000')
      END
  END as pension_status,
  
  'Social Security Act 1991, Part 3.10 - Asset Test' as regulation,
  'Department of Social Services (DSS)' as authority
);


-- Function 3: Superannuation Projection Engine
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.au_project_balance(
  member_id STRING,
  member_age INT,
  preservation_age INT,
  super_balance DOUBLE,
  projection_years INT
)
RETURNS STRUCT<
  member_id: STRING,
  current_age: INT,
  current_balance: DOUBLE,
  projection_years: INT,
  retirement_phase: STRING,
  annual_return_rate: DOUBLE,
  annual_withdrawal_rate: DOUBLE,
  estimated_final_balance: DOUBLE,
  balance_depleted: BOOLEAN,
  summary: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'Australia: Superannuation Projection - Balance projection using ASFA/APRA standards'
RETURN STRUCT(
  member_id,
  member_age as current_age,
  super_balance as current_balance,
  LEAST(projection_years, 30) as projection_years,
  
  CASE 
    WHEN member_age < preservation_age THEN 'Accumulation (Pre-retirement)'
    WHEN member_age < 70 THEN 'Early Retirement (60-69)'
    WHEN member_age < 80 THEN 'Mid Retirement (70-79)'
    ELSE 'Late Retirement (80+)'
  END as retirement_phase,
  
  CASE 
    WHEN member_age < preservation_age THEN 0.07
    WHEN member_age < 70 THEN 0.06
    WHEN member_age < 80 THEN 0.05
    ELSE 0.04
  END as annual_return_rate,
  
  CASE 
    WHEN member_age < preservation_age THEN 0.0
    WHEN member_age < 70 THEN 0.04
    WHEN member_age < 80 THEN 0.05
    ELSE 0.06
  END as annual_withdrawal_rate,
  
  super_balance * POWER(
    1.0 + CASE 
      WHEN member_age < preservation_age THEN 0.07
      WHEN member_age < 70 THEN 0.06
      WHEN member_age < 80 THEN 0.05
      ELSE 0.04
    END,
    CAST(LEAST(projection_years, 30) AS DOUBLE)
  ) - (
    super_balance * 
    CASE 
      WHEN member_age < preservation_age THEN 0.0
      WHEN member_age < 70 THEN 0.04
      WHEN member_age < 80 THEN 0.05
      ELSE 0.06
    END * CAST(LEAST(projection_years, 30) AS DOUBLE)
  ) as estimated_final_balance,
  
  (super_balance * POWER(
    1.0 + CASE 
      WHEN member_age < preservation_age THEN 0.07
      WHEN member_age < 70 THEN 0.06
      WHEN member_age < 80 THEN 0.05
      ELSE 0.04
    END,
    CAST(LEAST(projection_years, 30) AS DOUBLE)
  ) - (
    super_balance * 
    CASE 
      WHEN member_age < preservation_age THEN 0.0
      WHEN member_age < 70 THEN 0.04
      WHEN member_age < 80 THEN 0.05
      ELSE 0.06
    END * CAST(LEAST(projection_years, 30) AS DOUBLE)
  )) <= 0 as balance_depleted,
  
  CASE 
    WHEN (super_balance * POWER(
      1.0 + CASE 
        WHEN member_age < preservation_age THEN 0.07
        WHEN member_age < 70 THEN 0.06
        WHEN member_age < 80 THEN 0.05
        ELSE 0.04
      END,
      CAST(LEAST(projection_years, 30) AS DOUBLE)
    ) - (
      super_balance * 
      CASE 
        WHEN member_age < preservation_age THEN 0.0
        WHEN member_age < 70 THEN 0.04
        WHEN member_age < 80 THEN 0.05
        ELSE 0.06
      END * CAST(LEAST(projection_years, 30) AS DOUBLE)
    )) <= 0 THEN
      CONCAT('Balance depleted within ', CAST(LEAST(projection_years, 30) AS STRING), ' years')
    ELSE
      CONCAT('Projected balance: AUD ', 
             FORMAT_NUMBER(
               super_balance * POWER(
                 1.0 + CASE 
                   WHEN member_age < preservation_age THEN 0.07
                   WHEN member_age < 70 THEN 0.06
                   WHEN member_age < 80 THEN 0.05
                   ELSE 0.04
                 END,
                 CAST(LEAST(projection_years, 30) AS DOUBLE)
               ) - (
                 super_balance * 
                 CASE 
                   WHEN member_age < preservation_age THEN 0.0
                   WHEN member_age < 70 THEN 0.04
                   WHEN member_age < 80 THEN 0.05
                   ELSE 0.06
                 END * CAST(LEAST(projection_years, 30) AS DOUBLE)
               ), 0
             ),
             ' after ', CAST(LEAST(projection_years, 30) AS STRING), ' years')
  END as summary,
  
  'ASFA Retirement Standard 2024-25 & APRA Investment Guidelines' as regulation,
  'Association of Superannuation Funds of Australia (ASFA)' as authority
);


-- ============================================================================
-- USA FUNCTIONS
-- ============================================================================

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_calculate_401k_tax(
  member_id STRING,
  member_age INT,
  account_balance DOUBLE,
  withdrawal_amount DOUBLE
)
RETURNS STRUCT<
  member_id: STRING,
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
COMMENT 'USA: 401(k) Tax Calculator - Withdrawal tax and penalties per IRC Section 401(k)'
RETURN STRUCT(
  member_id,
  withdrawal_amount,
  
  CASE 
    WHEN member_age < 59 THEN withdrawal_amount * 0.10
    ELSE 0.0
  END as early_withdrawal_penalty,
  
  CASE 
    WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
    WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
    ELSE withdrawal_amount * 0.24
  END as income_tax_amount,
  
  CASE 
    WHEN member_age < 59 THEN withdrawal_amount * 0.10
    ELSE 0.0
  END + CASE 
    WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
    WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
    ELSE withdrawal_amount * 0.24
  END as total_tax,
  
  withdrawal_amount - (
    CASE 
      WHEN member_age < 59 THEN withdrawal_amount * 0.10
      ELSE 0.0
    END + CASE 
      WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
      WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
      ELSE withdrawal_amount * 0.24
    END
  ) as net_withdrawal,
  
  CASE 
    WHEN member_age < 59 THEN 
      CONCAT('Subject to 10% early withdrawal penalty and income tax (age ', 
             CAST(member_age AS STRING), ' < 59)')
    ELSE 
      CONCAT('Subject to income tax only (age ', CAST(member_age AS STRING), ' >= 59)')
  END as status,
  
  'Internal Revenue Code, Section 401(k) & Section 72(t)' as regulation,
  'Internal Revenue Service (IRS)' as authority
);


-- ============================================================================
-- UK FUNCTIONS
-- ============================================================================

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
  member_id STRING,
  member_age INT,
  pension_pot DOUBLE,
  withdrawal_amount DOUBLE
)
RETURNS STRUCT<
  member_id: STRING,
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
COMMENT 'UK: Pension Tax Calculator - Tax-free lump sum per Finance Act 2004'
RETURN STRUCT(
  member_id,
  withdrawal_amount,
  
  CASE 
    WHEN withdrawal_amount <= pension_pot * 0.25 THEN withdrawal_amount
    ELSE pension_pot * 0.25
  END as tax_free_lump_sum,
  
  CASE 
    WHEN withdrawal_amount <= pension_pot * 0.25 THEN 0.0
    ELSE withdrawal_amount - (pension_pot * 0.25)
  END as taxable_amount,
  
  CASE 
    WHEN withdrawal_amount <= pension_pot * 0.25 THEN 0.0
    ELSE (withdrawal_amount - (pension_pot * 0.25)) * 0.20
  END as tax_amount,
  
  withdrawal_amount - CASE 
    WHEN withdrawal_amount <= pension_pot * 0.25 THEN 0.0
    ELSE (withdrawal_amount - (pension_pot * 0.25)) * 0.20
  END as net_withdrawal,
  
  CASE 
    WHEN withdrawal_amount <= pension_pot * 0.25 THEN 
      'Tax-free withdrawal (within 25% tax-free allowance)'
    ELSE 
      'Partially taxable (25% tax-free, remainder subject to income tax)'
  END as status,
  
  'Finance Act 2004, Part 4 - Pension Schemes' as regulation,
  'HM Revenue & Customs (HMRC)' as authority
);


-- ============================================================================
-- INDIA FUNCTIONS
-- ============================================================================

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax(
  member_id STRING,
  member_age INT,
  years_of_service INT,
  epf_balance DOUBLE,
  withdrawal_amount DOUBLE
)
RETURNS STRUCT<
  member_id: STRING,
  withdrawal_amount: DOUBLE,
  tax_amount: DOUBLE,
  net_withdrawal: DOUBLE,
  tax_exempt: BOOLEAN,
  status: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'India: EPF Tax Calculator - Tax exemption per EPF Scheme 1952 and Income Tax Act Section 10(12)'
RETURN STRUCT(
  member_id,
  withdrawal_amount,
  
  CASE 
    WHEN years_of_service >= 5 THEN 0.0
    ELSE withdrawal_amount * 0.10
  END as tax_amount,
  
  withdrawal_amount - CASE 
    WHEN years_of_service >= 5 THEN 0.0
    ELSE withdrawal_amount * 0.10
  END as net_withdrawal,
  
  years_of_service >= 5 as tax_exempt,
  
  CASE 
    WHEN years_of_service >= 5 THEN 
      CONCAT('Tax-exempt withdrawal (', CAST(years_of_service AS STRING), 
             ' years service >= 5 years)')
    ELSE 
      CONCAT('Taxable at 10% (', CAST(years_of_service AS STRING), 
             ' years service < 5 years)')
  END as status,
  
  'Employees Provident Funds Scheme 1952 & Income Tax Act 1961, Section 10(12)' as regulation,
  'Employees Provident Fund Organisation (EPFO)' as authority
);


-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- List all functions in the schema
SHOW FUNCTIONS IN super_advisory_demo.pension_calculators;

-- Describe a specific function (example)
DESCRIBE FUNCTION super_advisory_demo.pension_calculators.au_calculate_tax;


-- ============================================================================
-- TEST QUERIES
-- ============================================================================

-- Test 1: Australia - Tax calculation (over preservation age)
SELECT super_advisory_demo.pension_calculators.au_calculate_tax(
  'TEST-AU-001', 65, 60, 500000, 100000
) as result;

-- Test 2: Australia - Pension impact
SELECT super_advisory_demo.pension_calculators.au_check_pension_impact(
  'TEST-AU-002', 70, 'Single', 250000, 50000, 0
) as result;

-- Test 3: Australia - Balance projection
SELECT super_advisory_demo.pension_calculators.au_project_balance(
  'TEST-AU-003', 65, 60, 600000, 20
) as result;

-- Test 4: USA - 401(k) tax
SELECT super_advisory_demo.pension_calculators.us_calculate_401k_tax(
  'TEST-US-001', 55, 400000, 50000
) as result;

-- Test 5: UK - Pension tax
SELECT super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
  'TEST-UK-001', 60, 300000, 100000
) as result;

-- Test 6: India - EPF tax
SELECT super_advisory_demo.pension_calculators.in_calculate_epf_tax(
  'TEST-IN-001', 55, 8, 500000, 100000
) as result;
