-- ============================================================================
-- INDIA PENSION CALCULATOR FUNCTIONS (COMPLETE SET)
-- 3 Functions matching Australia's comprehensive coverage
-- ============================================================================

-- Function 1: EPF (Employees' Provident Fund) Tax Calculator (Enhanced)
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Member age in years',
  years_of_service INT COMMENT 'Continuous years of service with EPF contributions',
  epf_balance DOUBLE COMMENT 'Current EPF account balance in INR',
  withdrawal_amount DOUBLE COMMENT 'Proposed withdrawal amount in INR',
  withdrawal_type STRING COMMENT 'Withdrawal type: Full or Partial'
)
RETURNS STRUCT<
  member_id: STRING,
  withdrawal_type: STRING,
  withdrawal_amount: DOUBLE,
  tax_amount: DOUBLE,
  tds_amount: DOUBLE,
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
  withdrawal_type,
  withdrawal_amount,
  
  -- Tax calculation based on service years and withdrawal type
  CASE 
    WHEN years_of_service >= 5 THEN 0.0  -- Tax-exempt after 5 years continuous service
    WHEN UPPER(withdrawal_type) = 'FULL' AND member_age >= 58 THEN 0.0  -- Full withdrawal at retirement age
    WHEN withdrawal_amount <= 50000 THEN 0.0  -- No tax if withdrawal <= 50,000 INR
    ELSE withdrawal_amount * 0.10  -- 10% tax if conditions not met
  END as tax_amount,
  
  -- TDS (Tax Deducted at Source) - 10% if PAN provided, 30% if no PAN
  CASE 
    WHEN years_of_service >= 5 THEN 0.0
    WHEN UPPER(withdrawal_type) = 'FULL' AND member_age >= 58 THEN 0.0
    WHEN withdrawal_amount <= 50000 THEN 0.0
    ELSE withdrawal_amount * 0.10  -- Assuming PAN provided
  END as tds_amount,
  
  -- Net withdrawal after tax
  withdrawal_amount - (CASE 
    WHEN years_of_service >= 5 THEN 0.0
    WHEN UPPER(withdrawal_type) = 'FULL' AND member_age >= 58 THEN 0.0
    WHEN withdrawal_amount <= 50000 THEN 0.0
    ELSE withdrawal_amount * 0.10
  END) as net_withdrawal,
  
  -- Tax exempt flag
  years_of_service >= 5 OR 
  (UPPER(withdrawal_type) = 'FULL' AND member_age >= 58) OR 
  withdrawal_amount <= 50000 as tax_exempt,
  
  -- Status message
  CASE 
    WHEN years_of_service >= 5 THEN 
      CONCAT('Tax-exempt withdrawal (', CAST(years_of_service AS STRING), 
             ' years continuous service >= 5 years)')
    WHEN UPPER(withdrawal_type) = 'FULL' AND member_age >= 58 THEN
      CONCAT('Tax-exempt retirement withdrawal (age ', CAST(member_age AS STRING), ' >= 58)')
    WHEN withdrawal_amount <= 50000 THEN
      'Tax-exempt (withdrawal amount <= INR 50,000)'
    ELSE 
      CONCAT('Taxable at 10% with TDS (', CAST(years_of_service AS STRING), 
             ' years service < 5 years)')
  END as status,
  
  'Employees Provident Funds Scheme 1952; Income Tax Act 1961, Section 10(12)' as regulation,
  'Employees Provident Fund Organisation (EPFO)' as authority
);


-- Function 2: NPS (National Pension System) Calculator
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps_benefits(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Member age in years',
  nps_corpus DOUBLE COMMENT 'Total NPS corpus at retirement in INR',
  annuity_purchase_pct DOUBLE COMMENT 'Percentage of corpus to purchase annuity (min 40%)',
  monthly_pension_rate DOUBLE COMMENT 'Expected monthly pension rate from annuity (% per annum)'
)
RETURNS STRUCT<
  member_id: STRING,
  total_corpus: DOUBLE,
  min_annuity_amount: DOUBLE,
  annuity_amount: DOUBLE,
  lump_sum_withdrawal: DOUBLE,
  lump_sum_tax_free: DOUBLE,
  lump_sum_taxable: DOUBLE,
  estimated_monthly_pension: DOUBLE,
  estimated_annual_pension: DOUBLE,
  nps_status: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'India: NPS Benefits Calculator - Calculates lump sum and annuity per PFRDA regulations'
RETURN STRUCT(
  member_id,
  nps_corpus as total_corpus,
  
  -- Minimum annuity purchase (40% of corpus)
  nps_corpus * 0.40 as min_annuity_amount,
  
  -- Actual annuity purchase amount
  nps_corpus * (annuity_purchase_pct / 100.0) as annuity_amount,
  
  -- Lump sum withdrawal (remaining after annuity)
  nps_corpus * (1.0 - (annuity_purchase_pct / 100.0)) as lump_sum_withdrawal,
  
  -- Tax-free portion of lump sum (up to 60% of corpus)
  LEAST(nps_corpus * (1.0 - (annuity_purchase_pct / 100.0)), nps_corpus * 0.60) as lump_sum_tax_free,
  
  -- Taxable portion (if lump sum > 60% of corpus)
  CASE 
    WHEN (1.0 - (annuity_purchase_pct / 100.0)) > 0.60 THEN
      nps_corpus * ((1.0 - (annuity_purchase_pct / 100.0)) - 0.60)
    ELSE 0.0
  END as lump_sum_taxable,
  
  -- Estimated monthly pension from annuity
  (nps_corpus * (annuity_purchase_pct / 100.0)) * (monthly_pension_rate / 100.0) / 12.0 as estimated_monthly_pension,
  
  -- Annual pension
  (nps_corpus * (annuity_purchase_pct / 100.0)) * (monthly_pension_rate / 100.0) as estimated_annual_pension,
  
  -- Status message
  CASE 
    WHEN member_age < 60 THEN 
      CONCAT('Cannot withdraw NPS before age 60 (currently age ', CAST(member_age AS STRING), 
             ') except for specific conditions')
    WHEN annuity_purchase_pct < 40 THEN 
      CONCAT('Invalid: Must purchase minimum 40% annuity (attempting ', 
             CAST(annuity_purchase_pct AS STRING), '%)')
    WHEN (1.0 - (annuity_purchase_pct / 100.0)) > 0.60 THEN
      CONCAT('Lump sum withdrawal: INR ', 
             FORMAT_NUMBER(nps_corpus * (1.0 - (annuity_purchase_pct / 100.0)), 0),
             ' (60% tax-free, remaining taxable); Monthly pension: INR ',
             FORMAT_NUMBER((nps_corpus * (annuity_purchase_pct / 100.0)) * (monthly_pension_rate / 100.0) / 12.0, 0))
    ELSE
      CONCAT('Lump sum withdrawal: INR ', 
             FORMAT_NUMBER(nps_corpus * (1.0 - (annuity_purchase_pct / 100.0)), 0),
             ' (100% tax-free); Monthly pension: INR ',
             FORMAT_NUMBER((nps_corpus * (annuity_purchase_pct / 100.0)) * (monthly_pension_rate / 100.0) / 12.0, 0))
  END as nps_status,
  
  'PFRDA (Pension Fund Regulatory and Development Authority) Act 2013; NPS Exit Regulations' as regulation,
  'Pension Fund Regulatory and Development Authority (PFRDA)' as authority
);


-- Function 3: Retirement Corpus Projection (EPF + NPS Combined)
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_project_retirement_corpus(
  member_id STRING COMMENT 'Unique member identifier',
  member_age INT COMMENT 'Current age in years',
  current_epf_balance DOUBLE COMMENT 'Current EPF balance in INR',
  current_nps_balance DOUBLE COMMENT 'Current NPS balance in INR',
  monthly_epf_contribution DOUBLE COMMENT 'Monthly EPF contribution (employee + employer) in INR',
  monthly_nps_contribution DOUBLE COMMENT 'Monthly NPS contribution in INR',
  retirement_age INT COMMENT 'Planned retirement age',
  projection_years INT COMMENT 'Number of years to project'
)
RETURNS STRUCT<
  member_id: STRING,
  current_age: INT,
  retirement_age: INT,
  projection_years: INT,
  current_epf_balance: DOUBLE,
  projected_epf_balance: DOUBLE,
  current_nps_balance: DOUBLE,
  projected_nps_balance: DOUBLE,
  total_projected_corpus: DOUBLE,
  epf_interest_rate: DOUBLE,
  nps_return_rate: DOUBLE,
  retirement_phase: STRING,
  summary: STRING,
  regulation: STRING,
  authority: STRING
>
LANGUAGE SQL
COMMENT 'India: Retirement Corpus Projection - Projects EPF and NPS balances to retirement'
RETURN STRUCT(
  member_id,
  member_age as current_age,
  retirement_age,
  LEAST(projection_years, retirement_age - member_age) as projection_years,
  
  current_epf_balance,
  
  -- EPF projection (8.25% interest for 2024-25)
  CASE 
    WHEN member_age >= retirement_age THEN current_epf_balance
    ELSE 
      -- Future value with monthly contributions
      current_epf_balance * POWER(1.0825, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (monthly_epf_contribution * 12.0 * 
       ((POWER(1.0825, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.0825))
  END as projected_epf_balance,
  
  current_nps_balance,
  
  -- NPS projection (assuming 10% average return based on market-linked instruments)
  CASE 
    WHEN member_age >= retirement_age THEN current_nps_balance
    ELSE
      current_nps_balance * POWER(1.10, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (monthly_nps_contribution * 12.0 * 
       ((POWER(1.10, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.10))
  END as projected_nps_balance,
  
  -- Total corpus at retirement
  (CASE 
    WHEN member_age >= retirement_age THEN current_epf_balance
    ELSE 
      current_epf_balance * POWER(1.0825, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (monthly_epf_contribution * 12.0 * 
       ((POWER(1.0825, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.0825))
  END) + (CASE 
    WHEN member_age >= retirement_age THEN current_nps_balance
    ELSE
      current_nps_balance * POWER(1.10, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (monthly_nps_contribution * 12.0 * 
       ((POWER(1.10, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.10))
  END) as total_projected_corpus,
  
  8.25 as epf_interest_rate,  -- Current EPF rate for 2024-25
  10.0 as nps_return_rate,    -- Assumed NPS return (market-linked)
  
  -- Retirement phase
  CASE 
    WHEN member_age < retirement_age THEN 
      CONCAT('Accumulation phase (', CAST(retirement_age - member_age AS STRING), ' years until retirement)')
    WHEN member_age = retirement_age THEN 'At retirement age'
    ELSE CONCAT('Post-retirement (age ', CAST(member_age AS STRING), ')')
  END as retirement_phase,
  
  -- Summary
  CASE 
    WHEN member_age >= retirement_age THEN
      CONCAT('Current retirement corpus: INR ', 
             FORMAT_NUMBER(current_epf_balance + current_nps_balance, 0),
             ' (EPF: INR ', FORMAT_NUMBER(current_epf_balance, 0),
             ' + NPS: INR ', FORMAT_NUMBER(current_nps_balance, 0), ')')
    ELSE
      CONCAT('Projected retirement corpus at age ', CAST(retirement_age AS STRING), ': INR ',
             FORMAT_NUMBER(
               (current_epf_balance * POWER(1.0825, CAST(retirement_age - member_age AS DOUBLE)) +
                (monthly_epf_contribution * 12.0 * 
                 ((POWER(1.0825, CAST(retirement_age - member_age AS DOUBLE)) - 1) / 0.0825))) +
               (current_nps_balance * POWER(1.10, CAST(retirement_age - member_age AS DOUBLE)) +
                (monthly_nps_contribution * 12.0 * 
                 ((POWER(1.10, CAST(retirement_age - member_age AS DOUBLE)) - 1) / 0.10))),
               0
             ),
             ' (EPF: INR ',
             FORMAT_NUMBER(
               current_epf_balance * POWER(1.0825, CAST(retirement_age - member_age AS DOUBLE)) +
               (monthly_epf_contribution * 12.0 * 
                ((POWER(1.0825, CAST(retirement_age - member_age AS DOUBLE)) - 1) / 0.0825)),
               0
             ),
             ' + NPS: INR ',
             FORMAT_NUMBER(
               current_nps_balance * POWER(1.10, CAST(retirement_age - member_age AS DOUBLE)) +
               (monthly_nps_contribution * 12.0 * 
                ((POWER(1.10, CAST(retirement_age - member_age AS DOUBLE)) - 1) / 0.10)),
               0
             ),
             ')')
  END as summary,
  
  'EPF Scheme 1952 - Interest Rate Declaration; PFRDA Regulations - NPS Returns' as regulation,
  'EPFO & PFRDA' as authority
);


-- ============================================================================
-- TEST QUERIES FOR INDIA FUNCTIONS
-- ============================================================================

-- Test 1: EPF tax calculation (tax-exempt case)
SELECT super_advisory_demo.pension_calculators.in_calculate_epf_tax(
  'TEST-IN-001', 58, 8, 500000, 500000, 'Full'
) as result;

-- Test 2: NPS benefits calculation
SELECT super_advisory_demo.pension_calculators.in_calculate_nps_benefits(
  'TEST-IN-002', 60, 2000000, 40, 7.5
) as result;

-- Test 3: Retirement corpus projection
SELECT super_advisory_demo.pension_calculators.in_project_retirement_corpus(
  'TEST-IN-003', 40, 300000, 150000, 5000, 3000, 60, 20
) as result;
