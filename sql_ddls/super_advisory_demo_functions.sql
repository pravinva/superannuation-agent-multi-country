-- ============================================================================
-- SuperAdvisory Demo - Complete UC Function Definitions
-- Generated: 2025-10-28 13:53:32.460175
-- EXECUTABLE CREATE OR REPLACE FUNCTION statements
-- ============================================================================

USE CATALOG super_advisory_demo;
USE SCHEMA pension_calculators;


-- Function: au_calculate_tax
-- Australia: ATO Tax Calculator - Superannuation withdrawal tax per Division 301

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.au_calculate_tax(
)
RETURNS STRUCT<member_id: STRING, withdrawal_amount: DOUBLE, tax_free_component: DOUBLE, taxable_component: DOUBLE, tax_amount: DOUBLE, tax_rate: DOUBLE, net_withdrawal: DOUBLE, status: STRING, regulation: STRING, authority: STRING>
COMMENT 'Australia: ATO Tax Calculator - Superannuation withdrawal tax per Division 301'
LANGUAGE SQL
RETURN
    STRUCT(
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

--------------------------------------------------------------------------------

-- Function: au_check_pension_impact
-- Australia: Centrelink Age Pension Calculator - Asset test per Part 3.10

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.au_check_pension_impact(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_super_balance: DOUBLE, after_withdrawal_balance: DOUBLE, total_assessable_assets: DOUBLE, age_pension_eligible: BOOLEAN, estimated_annual_pension: DOUBLE, annual_super_income: DOUBLE, combined_annual_income: DOUBLE, pension_status: STRING, regulation: STRING, authority: STRING>
COMMENT 'Australia: Centrelink Age Pension Calculator - Asset test per Part 3.10'
LANGUAGE SQL
RETURN
    STRUCT(
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

--------------------------------------------------------------------------------

-- Function: au_project_balance
-- Australia: Superannuation Projection - Balance projection using ASFA/APRA standards

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.au_project_balance(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_age: INT, current_balance: DOUBLE, projection_years: INT, retirement_phase: STRING, annual_return_rate: DOUBLE, annual_withdrawal_rate: DOUBLE, estimated_final_balance: DOUBLE, balance_depleted: BOOLEAN, summary: STRING, regulation: STRING, authority: STRING>
COMMENT 'Australia: Superannuation Projection - Balance projection using ASFA/APRA standards'
LANGUAGE SQL
RETURN
    STRUCT(
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

--------------------------------------------------------------------------------

-- Function: in_calculate_epf_tax
-- Calculate EPF withdrawal tax based on age and service years

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, member_age: INT, epf_balance: DOUBLE, withdrawal_amount: DOUBLE, withdrawal_type: STRING, estimated_years_of_service: INT, tax_amount: DOUBLE, tds_amount: DOUBLE, net_withdrawal: DOUBLE, tax_exempt: BOOLEAN, status: STRING, regulation: STRING, authority: STRING>
COMMENT 'Calculate EPF withdrawal tax based on age and service years'
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age,
  CAST(super_balance AS DOUBLE) as epf_balance,
  CAST(withdrawal_amount AS DOUBLE) as withdrawal_amount,
  'FULL' as withdrawal_type,
  
  -- Estimate years of service (assume started at 25)
  GREATEST(0, member_age - 25) as estimated_years_of_service,
  
  -- Tax calculation (tax-exempt if 5+ years service OR age 58+)
  CAST(
    CASE 
      WHEN (member_age - 25) >= 5 THEN 0.0  -- 5+ years service
      WHEN member_age >= 58 THEN 0.0  -- Retirement age
      WHEN withdrawal_amount <= 50000 THEN 0.0  -- Below threshold
      ELSE withdrawal_amount * 0.10  -- 10% tax
    END
  AS DOUBLE) as tax_amount,
  
  -- TDS (same as tax in this case)
  CAST(
    CASE 
      WHEN (member_age - 25) >= 5 THEN 0.0
      WHEN member_age >= 58 THEN 0.0
      WHEN withdrawal_amount <= 50000 THEN 0.0
      ELSE withdrawal_amount * 0.10
    END
  AS DOUBLE) as tds_amount,
  
  -- Net withdrawal
  CAST(
    withdrawal_amount - (CASE 
      WHEN (member_age - 25) >= 5 THEN 0.0
      WHEN member_age >= 58 THEN 0.0
      WHEN withdrawal_amount <= 50000 THEN 0.0
      ELSE withdrawal_amount * 0.10
    END)
  AS DOUBLE) as net_withdrawal,
  
  -- Tax exempt flag
  ((member_age - 25) >= 5) OR (member_age >= 58) OR (withdrawal_amount <= 50000) as tax_exempt,
  
  -- Status
  CASE 
    WHEN (member_age - 25) >= 5 THEN 
      CONCAT('Tax-exempt withdrawal (estimated ', CAST(member_age - 25 AS STRING), 
             ' years service >= 5 years)')
    WHEN member_age >= 58 THEN
      CONCAT('Tax-exempt retirement withdrawal (age ', CAST(member_age AS STRING), ' >= 58)')
    WHEN withdrawal_amount <= 50000 THEN
      'Tax-exempt (withdrawal amount <= INR 50,000)'
    ELSE 
      CONCAT('Taxable at 10% with TDS (estimated ', CAST(member_age - 25 AS STRING), 
             ' years service < 5 years)')
  END as status,
  
  'Employees Provident Funds Scheme 1952; Income Tax Act 1961, Section 10(12)' as regulation,
  'Employees Provident Fund Organisation (EPFO)' as authority
);

--------------------------------------------------------------------------------

-- Function: in_calculate_eps_benefits
-- Calculate EPS (Employee Pension Scheme) benefits for Indian members

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_eps_benefits(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, member_age: INT, epf_balance: DOUBLE, years_of_service: INT, pensionable_salary: DOUBLE, monthly_pension: DOUBLE, annual_pension: DOUBLE, pension_start_age: INT, early_pension_reduction: DOUBLE, min_pension: DOUBLE, max_pension: DOUBLE, calculation_method: STRING, eligibility_status: STRING, pension_commencement: STRING>
COMMENT 'Calculate EPS (Employee Pension Scheme) benefits for Indian members'
LANGUAGE SQL
RETURN
    (SELECT STRUCT(
    member_id,
    member_age,
    epf_balance,
    years_of_service,
    
    -- Estimate pensionable salary from EPF balance
    -- Assuming average salary = EPF balance / (years_of_service * 0.24)
    -- 0.24 = 12% employee + 12% employer contribution rate
    CASE 
      WHEN years_of_service > 0 THEN epf_balance / (years_of_service * 0.24)
      ELSE 15000.0
    END as pensionable_salary,
    
    -- Monthly pension calculation with limits
    -- Formula: (Pensionable Salary × Service Years) / 70
    -- Capped at ₹7,500 and minimum ₹1,000
    CASE 
      WHEN years_of_service < 10 THEN 0.0
      ELSE LEAST(7500.0, GREATEST(1000.0, 
        (CASE 
          WHEN years_of_service > 0 THEN epf_balance / (years_of_service * 0.24)
          ELSE 15000.0
        END * years_of_service) / 70
      ))
    END as monthly_pension,
    
    -- Annual pension
    CASE 
      WHEN years_of_service < 10 THEN 0.0
      ELSE LEAST(7500.0, GREATEST(1000.0, 
        (CASE 
          WHEN years_of_service > 0 THEN epf_balance / (years_of_service * 0.24)
          ELSE 15000.0
        END * years_of_service) / 70
      )) * 12
    END as annual_pension,
    
    -- Pension eligibility age
    58 as pension_start_age,
    
    -- Early pension reduction (4% per year before age 58)
    CASE 
      WHEN member_age < 58 THEN (58 - member_age) * 0.04
      ELSE 0.0
    END as early_pension_reduction,
    
    1000.0 as min_pension,
    7500.0 as max_pension,
    
    'EPS Formula: (Pensionable Salary × Service Years) / 70, capped at ₹7,500/month' as calculation_method,
    
    -- Eligibility status
    CASE 
      WHEN years_of_service < 10 THEN 'Not Eligible (Minimum 10 years service required)'
      WHEN member_age >= 58 THEN 'Eligible for Full Pension'
      WHEN member_age >= 50 THEN 'Eligible with Reduced Pension (Early Exit)'
      ELSE 'Not Yet Eligible (Below Age 50)'
    END as eligibility_status,
    
    -- Pension commencement
    CASE 
      WHEN member_age >= 58 THEN 'Pension can start immediately'
      WHEN member_age >= 50 THEN CONCAT('Pension starts at age 58, or reduced pension now (', 
                                         CAST((58 - member_age) * 4 AS INT), '% reduction)')
      ELSE CONCAT('Pension starts at age 58 (', CAST(58 - member_age AS INT), ' years from now)')
    END as pension_commencement
  ));

--------------------------------------------------------------------------------

-- Function: in_calculate_nps
-- Calculate NPS benefits with 40% annuity requirement and 60% tax-free lump sum

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, member_age: INT, nps_corpus: DOUBLE, min_annuity_pct: DOUBLE, max_lump_sum_pct: DOUBLE, min_annuity_amount: DOUBLE, max_lump_sum: DOUBLE, lump_sum_tax_free: DOUBLE, estimated_monthly_pension: DOUBLE, estimated_annual_pension: DOUBLE, is_eligible: BOOLEAN, nps_status: STRING, regulation: STRING, authority: STRING>
COMMENT 'Calculate NPS benefits with 40% annuity requirement and 60% tax-free lump sum'
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age,
  CAST(super_balance AS DOUBLE) as nps_corpus,
  
  -- Minimum annuity purchase (40%)
  CAST(0.40 AS DOUBLE) as min_annuity_pct,
  
  -- Maximum lump sum (60%)
  CAST(0.60 AS DOUBLE) as max_lump_sum_pct,
  
  -- Minimum annuity amount (40% of corpus)
  CAST(super_balance * 0.40 AS DOUBLE) as min_annuity_amount,
  
  -- Maximum lump sum (60% of corpus)
  CAST(super_balance * 0.60 AS DOUBLE) as max_lump_sum,
  
  -- Lump sum is 100% tax-free up to 60%
  CAST(super_balance * 0.60 AS DOUBLE) as lump_sum_tax_free,
  
  -- Estimated monthly pension (assuming 6% annual return on 40% annuity)
  CAST((super_balance * 0.40 * 0.06) / 12.0 AS DOUBLE) as estimated_monthly_pension,
  
  -- Estimated annual pension
  CAST(super_balance * 0.40 * 0.06 AS DOUBLE) as estimated_annual_pension,
  
  -- Eligible if age 60+
  member_age >= 60 as is_eligible,
  
  -- Status
  CASE 
    WHEN member_age < 60 THEN 
      CONCAT('Cannot withdraw NPS before age 60 (currently age ', CAST(member_age AS STRING), ')')
    ELSE
      CONCAT('Eligible: 60% lump sum (INR ', 
             FORMAT_NUMBER(super_balance * 0.60, 0),
             ', tax-free) + 40% annuity (INR ',
             FORMAT_NUMBER((super_balance * 0.40 * 0.06) / 12.0, 0),
             '/month estimated pension)')
  END as nps_status,
  
  'PFRDA (Pension Fund Regulatory and Development Authority) Act 2013; NPS Exit Regulations' as regulation,
  'Pension Fund Regulatory and Development Authority (PFRDA)' as authority
);

--------------------------------------------------------------------------------

-- Function: in_calculate_nps_benefits
-- India: NPS Benefits Calculator - Calculates lump sum and annuity per PFRDA regulations

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps_benefits(
)
RETURNS STRUCT<member_id: STRING, total_corpus: DOUBLE, min_annuity_amount: DOUBLE, annuity_amount: DOUBLE, lump_sum_withdrawal: DOUBLE, lump_sum_tax_free: DOUBLE, lump_sum_taxable: DOUBLE, estimated_monthly_pension: DOUBLE, estimated_annual_pension: DOUBLE, nps_status: STRING, regulation: STRING, authority: STRING>
COMMENT 'India: NPS Benefits Calculator - Calculates lump sum and annuity per PFRDA regulations'
LANGUAGE SQL
RETURN
    STRUCT(
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

--------------------------------------------------------------------------------

-- Function: in_project_retirement
-- Project EPF/NPS retirement corpus growth

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_project_retirement(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_age: INT, current_balance: DOUBLE, retirement_age: INT, projection_years: INT, epf_return_rate: DOUBLE, nps_return_rate: DOUBLE, projected_epf_balance: DOUBLE, projected_nps_balance: DOUBLE, total_projected_corpus: DOUBLE, retirement_phase: STRING, summary: STRING, regulation: STRING, authority: STRING>
COMMENT 'Project EPF/NPS retirement corpus growth'
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age as current_age,
  CAST(super_balance AS DOUBLE) as current_balance,
  60 as retirement_age,
  LEAST(projection_years, 30) as projection_years,
  
  -- EPF return rate (8.25% as of 2024)
  CAST(0.0825 AS DOUBLE) as epf_return_rate,
  
  -- NPS return rate (assume 10% equity-heavy)
  CAST(0.10 AS DOUBLE) as nps_return_rate,
  
  -- Projected EPF balance (assume 50% in EPF) - ✅ FIX: Handle division by zero
  CAST(
    CASE
      WHEN projection_years <= 0 THEN super_balance * 0.50
      WHEN member_age >= 60 THEN super_balance * 0.50
      ELSE 
        (super_balance * 0.50) * POWER(1.0825, CAST(LEAST(projection_years, 30) AS DOUBLE))
    END
  AS DOUBLE) as projected_epf_balance,
  
  -- Projected NPS balance (assume 50% in NPS)
  CAST(
    CASE
      WHEN projection_years <= 0 THEN super_balance * 0.50
      WHEN member_age >= 60 THEN super_balance * 0.50
      ELSE 
        (super_balance * 0.50) * POWER(1.10, CAST(LEAST(projection_years, 30) AS DOUBLE))
    END
  AS DOUBLE) as projected_nps_balance,
  
  -- Total corpus
  CAST(
    CASE
      WHEN projection_years <= 0 THEN super_balance
      WHEN member_age >= 60 THEN super_balance
      ELSE 
        ((super_balance * 0.50) * POWER(1.0825, CAST(LEAST(projection_years, 30) AS DOUBLE))) +
        ((super_balance * 0.50) * POWER(1.10, CAST(LEAST(projection_years, 30) AS DOUBLE)))
    END
  AS DOUBLE) as total_projected_corpus,
  
  -- Retirement phase
  CASE 
    WHEN member_age < 60 THEN 
      CONCAT('Accumulation phase (', CAST(60 - member_age AS STRING), ' years until retirement)')
    WHEN member_age = 60 THEN 'At retirement age'
    ELSE CONCAT('Post-retirement (age ', CAST(member_age AS STRING), ')')
  END as retirement_phase,
  
  -- Summary
  CASE 
    WHEN member_age >= 60 THEN
      CONCAT('Current retirement corpus: INR ', FORMAT_NUMBER(super_balance, 0))
    WHEN projection_years <= 0 THEN
      CONCAT('Current balance: INR ', FORMAT_NUMBER(super_balance, 0))
    ELSE
      CONCAT('Projected corpus at age 60: INR ',
             FORMAT_NUMBER(
               ((super_balance * 0.50) * POWER(1.0825, CAST(LEAST(60 - member_age, 30) AS DOUBLE))) +
               ((super_balance * 0.50) * POWER(1.10, CAST(LEAST(60 - member_age, 30) AS DOUBLE))),
               0
             ))
  END as summary,
  
  'EPF Scheme 1952; PFRDA Regulations' as regulation,
  'EPFO & PFRDA' as authority
);

--------------------------------------------------------------------------------

-- Function: in_project_retirement_corpus

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_project_retirement_corpus(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_age: INT, retirement_age: INT, projection_years: INT, current_epf_balance: DOUBLE, projected_epf_balance: DOUBLE, current_nps_balance: DOUBLE, projected_nps_balance: DOUBLE, total_projected_corpus: DOUBLE, epf_interest_rate: DOUBLE, nps_return_rate: DOUBLE, retirement_phase: STRING, summary: STRING, regulation: STRING, authority: STRING>
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age as current_age,
  retirement_age,
  LEAST(projection_years, retirement_age - member_age) as projection_years,
  
  current_epf_balance,
  
  -- ✅ FIX: Handle retirement age edge case
  CASE 
    WHEN member_age >= retirement_age THEN current_epf_balance
    WHEN retirement_age - member_age = 0 THEN current_epf_balance
    ELSE 
      current_epf_balance * POWER(1.0825, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (monthly_epf_contribution * 12.0 * 
       ((POWER(1.0825, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.0825))
  END as projected_epf_balance,
  
  current_nps_balance,
  
  CASE 
    WHEN member_age >= retirement_age THEN current_nps_balance
    WHEN retirement_age - member_age = 0 THEN current_nps_balance
    ELSE
      current_nps_balance * POWER(1.10, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (monthly_nps_contribution * 12.0 * 
       ((POWER(1.10, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.10))
  END as projected_nps_balance,
  
  -- Total corpus
  (CASE 
    WHEN member_age >= retirement_age THEN current_epf_balance
    WHEN retirement_age - member_age = 0 THEN current_epf_balance
    ELSE 
      current_epf_balance * POWER(1.0825, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (monthly_epf_contribution * 12.0 * 
       ((POWER(1.0825, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.0825))
  END) + (CASE 
    WHEN member_age >= retirement_age THEN current_nps_balance
    WHEN retirement_age - member_age = 0 THEN current_nps_balance
    ELSE
      current_nps_balance * POWER(1.10, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (monthly_nps_contribution * 12.0 * 
       ((POWER(1.10, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.10))
  END) as total_projected_corpus,
  
  8.25 as epf_interest_rate,
  10.0 as nps_return_rate,
  
  CASE 
    WHEN member_age < retirement_age THEN 
      CONCAT('Accumulation phase (', CAST(retirement_age - member_age AS STRING), ' years until retirement)')
    WHEN member_age = retirement_age THEN 'At retirement age'
    ELSE CONCAT('Post-retirement (age ', CAST(member_age AS STRING), ')')
  END as retirement_phase,
  
  CASE 
    WHEN member_age >= retirement_age THEN
      CONCAT('Current retirement corpus: INR ', 
             FORMAT_NUMBER(current_epf_balance + current_nps_balance, 0))
    ELSE
      CONCAT('Projected corpus at age ', CAST(retirement_age AS STRING), ': INR ',
             FORMAT_NUMBER((current_epf_balance * POWER(1.0825, CAST(retirement_age - member_age AS DOUBLE))) + 
                          (current_nps_balance * POWER(1.10, CAST(retirement_age - member_age AS DOUBLE))), 0))
  END as summary,
  
  'EPF Scheme 1952; PFRDA Regulations' as regulation,
  'EPFO & PFRDA' as authority
);

--------------------------------------------------------------------------------

-- Function: uk_calculate_pension_tax
-- UK: Pension Tax Calculator - Tax-free lump sum and withdrawal tax per Finance Act 2004

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.uk_calculate_pension_tax(
)
RETURNS STRUCT<member_id: STRING, withdrawal_type: STRING, withdrawal_amount: DOUBLE, tax_free_lump_sum: DOUBLE, taxable_amount: DOUBLE, tax_amount: DOUBLE, net_withdrawal: DOUBLE, status: STRING, regulation: STRING, authority: STRING>
COMMENT 'UK: Pension Tax Calculator - Tax-free lump sum and withdrawal tax per Finance Act 2004'
LANGUAGE SQL
RETURN
    STRUCT(
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

--------------------------------------------------------------------------------

-- Function: uk_check_state_pension

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.uk_check_state_pension(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_age: INT, state_pension_age: INT, ni_years: INT, min_qualifying_years: INT, full_state_pension_eligible: BOOLEAN, weekly_state_pension: DOUBLE, annual_state_pension: DOUBLE, combined_annual_income: DOUBLE, pension_status: STRING, regulation: STRING, authority: STRING>
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age AS current_age,

  -- Simplified, static State Pension age logic (current and future threshold)
  CASE 
    WHEN member_age < 66 THEN 66
    ELSE 67
  END AS state_pension_age,

  ni_qualifying_years AS ni_years,
  10 AS min_qualifying_years,
  ni_qualifying_years >= 35 AS full_state_pension_eligible,

  -- Compute base weekly pension — avoid redundant CASE evaluations
  ROUND(
    CASE 
      WHEN ni_qualifying_years < 10 THEN 0.0
      WHEN ni_qualifying_years >= 35 THEN 221.20
      ELSE 221.20 * (ni_qualifying_years / 35.0)
    END,
    2
  ) AS weekly_state_pension,

  -- Annual = weekly × 52
  ROUND(
    CASE 
      WHEN ni_qualifying_years < 10 THEN 0.0
      WHEN ni_qualifying_years >= 35 THEN 221.20 * 52.0
      ELSE (221.20 * (ni_qualifying_years / 35.0)) * 52.0
    END,
    2
  ) AS annual_state_pension,

  -- Combined pension income (state only; placeholders for future expansion)
  ROUND(
    CASE 
      WHEN ni_qualifying_years < 10 THEN 0.0
      WHEN ni_qualifying_years >= 35 THEN 221.20 * 52.0
      ELSE (221.20 * (ni_qualifying_years / 35.0)) * 52.0
    END,
    2
  ) AS combined_annual_income,

  -- Pension status summary
  CASE 
    WHEN member_age < 66 THEN 
      CONCAT('Not yet eligible - State Pension age is 66 (currently age ', member_age, ')')
    WHEN ni_qualifying_years < 10 THEN 
      CONCAT('Not eligible - need minimum 10 qualifying years (currently have ', ni_qualifying_years, ')')
    WHEN ni_qualifying_years >= 35 THEN 
      'Eligible for full New State Pension (£221.20/week or £11,502.40/year)'
    ELSE 
      CONCAT(
        'Eligible for partial pension based on ', ni_qualifying_years, 
        ' years: £',
        ROUND((221.20 * (ni_qualifying_years / 35.0)) * 52.0, 2),
        '/year'
      )
  END AS pension_status,

  'Pensions Act 2014, Section 4 - New State Pension; Pensions Act 2007 - State Pension Age' AS regulation,
  'Department for Work and Pensions (DWP)' AS authority
);

--------------------------------------------------------------------------------

-- Function: uk_project_pension_balance
-- UK: Pension Drawdown Projection - Projects pension pot with flexible drawdown per FCA guidance

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.uk_project_pension_balance(
)
RETURNS STRUCT<member_id: STRING, current_age: INT, current_pension_pot: DOUBLE, annual_drawdown: DOUBLE, projection_years: INT, retirement_phase: STRING, annual_return_rate: DOUBLE, drawdown_rate: DOUBLE, estimated_final_balance: DOUBLE, balance_depleted: BOOLEAN, years_until_depletion: INT, summary: STRING, regulation: STRING, authority: STRING>
COMMENT 'UK: Pension Drawdown Projection - Projects pension pot with flexible drawdown per FCA guidance'
LANGUAGE SQL
RETURN
    STRUCT(
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

--------------------------------------------------------------------------------

-- Function: us_calculate_401k_tax
-- Calculate 401k/IRA withdrawal tax with early penalty if under 59.5

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_calculate_401k_tax(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, account_type: STRING, withdrawal_amount: DOUBLE, early_withdrawal_penalty: DOUBLE, income_tax_amount: DOUBLE, total_tax: DOUBLE, net_withdrawal: DOUBLE, status: STRING, regulation: STRING, authority: STRING>
COMMENT 'Calculate 401k/IRA withdrawal tax with early penalty if under 59.5'
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  account_type,
  CAST(withdrawal_amount AS DOUBLE) as withdrawal_amount,
  
  -- Early withdrawal penalty - CAST AS DOUBLE
  CAST(
    CASE 
      WHEN member_age >= 59 THEN 0.0
      WHEN UPPER(account_type) = 'ROTH_IRA' THEN 0.0
      ELSE withdrawal_amount * 0.10
    END
  AS DOUBLE) as early_withdrawal_penalty,
  
  -- Income tax - CAST AS DOUBLE
  CAST(
    CASE 
      WHEN UPPER(account_type) = 'ROTH_IRA' THEN 0.0
      WHEN withdrawal_amount <= 11000 THEN withdrawal_amount * 0.10
      WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
      WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
      WHEN withdrawal_amount <= 182100 THEN withdrawal_amount * 0.24
      ELSE withdrawal_amount * 0.32
    END
  AS DOUBLE) as income_tax_amount,
  
  -- Total tax - CAST AS DOUBLE
  CAST(
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
  AS DOUBLE) as total_tax,
  
  -- Net withdrawal - CAST AS DOUBLE
  CAST(
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
    )
  AS DOUBLE) as net_withdrawal,
  
  -- Status
  CASE 
    WHEN UPPER(account_type) = 'ROTH_IRA' THEN 
      CONCAT('Tax-free withdrawal from Roth IRA (age ', CAST(member_age AS STRING), ')')
    WHEN member_age >= 59 THEN 
      CONCAT('Subject to income tax only (age ', CAST(member_age AS STRING), ' >= 59.5)')
    ELSE 
      CONCAT('Subject to 10% early withdrawal penalty and income tax (age ', CAST(member_age AS STRING), ' < 59.5)')
  END as status,
  
  'Internal Revenue Code, Section 401(k), Section 408 (IRAs), Section 72(t)' as regulation,
  'Internal Revenue Service (IRS)' as authority
);

--------------------------------------------------------------------------------

-- Function: us_calculate_tax
-- Calculate 401k/IRA withdrawal tax with early penalty if under 59.5

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_calculate_tax(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, member_age: INT, account_balance: DOUBLE, withdrawal_amount: DOUBLE, account_type: STRING, early_withdrawal_penalty: DOUBLE, income_tax_amount: DOUBLE, total_tax: DOUBLE, net_withdrawal: DOUBLE, status: STRING, regulation: STRING, authority: STRING>
COMMENT 'Calculate 401k/IRA withdrawal tax with early penalty if under 59.5'
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age,
  CAST(super_balance AS DOUBLE) as account_balance,
  CAST(withdrawal_amount AS DOUBLE) as withdrawal_amount,
  '401K' as account_type,
  
  -- Early withdrawal penalty (10% if under 59)
  CAST(
    CASE 
      WHEN member_age >= 59 THEN 0.0
      ELSE withdrawal_amount * 0.10
    END
  AS DOUBLE) as early_withdrawal_penalty,
  
  -- Income tax based on 2024 tax brackets
  CAST(
    CASE 
      WHEN withdrawal_amount <= 11000 THEN withdrawal_amount * 0.10
      WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
      WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
      WHEN withdrawal_amount <= 182100 THEN withdrawal_amount * 0.24
      ELSE withdrawal_amount * 0.32
    END
  AS DOUBLE) as income_tax_amount,
  
  -- Total tax (penalty + income tax)
  CAST(
    (CASE 
      WHEN member_age >= 59 THEN 0.0
      ELSE withdrawal_amount * 0.10
    END) + (CASE 
      WHEN withdrawal_amount <= 11000 THEN withdrawal_amount * 0.10
      WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
      WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
      WHEN withdrawal_amount <= 182100 THEN withdrawal_amount * 0.24
      ELSE withdrawal_amount * 0.32
    END)
  AS DOUBLE) as total_tax,
  
  -- Net withdrawal after all taxes
  CAST(
    withdrawal_amount - (
      (CASE 
        WHEN member_age >= 59 THEN 0.0
        ELSE withdrawal_amount * 0.10
      END) + (CASE 
        WHEN withdrawal_amount <= 11000 THEN withdrawal_amount * 0.10
        WHEN withdrawal_amount <= 44625 THEN withdrawal_amount * 0.12
        WHEN withdrawal_amount <= 95375 THEN withdrawal_amount * 0.22
        WHEN withdrawal_amount <= 182100 THEN withdrawal_amount * 0.24
        ELSE withdrawal_amount * 0.32
      END)
    )
  AS DOUBLE) as net_withdrawal,
  
  -- Status message
  CASE 
    WHEN member_age >= 59 THEN 
      CONCAT('Subject to income tax only (age ', CAST(member_age AS STRING), ' >= 59.5)')
    ELSE 
      CONCAT('Subject to 10% early withdrawal penalty and income tax (age ', CAST(member_age AS STRING), ' < 59.5)')
  END as status,
  
  'Internal Revenue Code, Section 401(k), Section 408 (IRAs), Section 72(t)' as regulation,
  'Internal Revenue Service (IRS)' as authority
);

--------------------------------------------------------------------------------

-- Function: us_check_social_security
-- Check Social Security eligibility and estimated benefits

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_check_social_security(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_age: INT, marital_status: STRING, account_balance: DOUBLE, full_retirement_age: INT, earliest_claim_age: INT, can_claim_now: BOOLEAN, estimated_monthly_benefit: DOUBLE, estimated_annual_benefit: DOUBLE, spousal_benefit_eligible: BOOLEAN, years_until_fra: INT, benefit_status: STRING, regulation: STRING, authority: STRING>
COMMENT 'Check Social Security eligibility and estimated benefits'
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age as current_age,
  marital_status,
  CAST(super_balance AS DOUBLE) as account_balance,
  67 as full_retirement_age,
  62 as earliest_claim_age,
  
  -- Can claim now if 62 or older
  member_age >= 62 as can_claim_now,
  
  -- Estimated monthly benefit (simplified - assumes $3000 at FRA)
  CAST(
    CASE 
      WHEN member_age < 62 THEN 0.0
      WHEN member_age >= 67 THEN 3000.0
      WHEN member_age = 62 THEN 2100.0  -- 70% of FRA
      WHEN member_age = 63 THEN 2250.0  -- 75% of FRA
      WHEN member_age = 64 THEN 2400.0  -- 80% of FRA
      WHEN member_age = 65 THEN 2600.0  -- 86.7% of FRA
      WHEN member_age = 66 THEN 2800.0  -- 93.3% of FRA
      ELSE 3000.0
    END
  AS DOUBLE) as estimated_monthly_benefit,
  
  -- Annual benefit
  CAST(
    (CASE 
      WHEN member_age < 62 THEN 0.0
      WHEN member_age >= 67 THEN 3000.0
      WHEN member_age = 62 THEN 2100.0
      WHEN member_age = 63 THEN 2250.0
      WHEN member_age = 64 THEN 2400.0
      WHEN member_age = 65 THEN 2600.0
      WHEN member_age = 66 THEN 2800.0
      ELSE 3000.0
    END) * 12.0
  AS DOUBLE) as estimated_annual_benefit,
  
  -- Spousal benefit eligibility
  UPPER(marital_status) IN ('MARRIED', 'WIDOWED') as spousal_benefit_eligible,
  
  -- Years until FRA
  GREATEST(0, 67 - member_age) as years_until_fra,
  
  -- Status
  CASE 
    WHEN member_age < 62 THEN 
      CONCAT('Not yet eligible - minimum claim age is 62 (currently ', CAST(member_age AS STRING), ')')
    WHEN member_age = 67 THEN 
      'Eligible at Full Retirement Age (FRA) - 100% of benefit'
    WHEN member_age < 67 THEN 
      CONCAT('Eligible for early claim (age ', CAST(member_age AS STRING), ') - reduced benefit')
    ELSE 
      CONCAT('Eligible for delayed claim (age ', CAST(member_age AS STRING), ') - increased benefit up to age 70')
  END as benefit_status,
  
  'Social Security Act, Title II - Old-Age, Survivors, and Disability Insurance' as regulation,
  'Social Security Administration (SSA)' as authority
);

--------------------------------------------------------------------------------

-- Function: us_project_401k
-- Project 401(k) balance growth over time

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_project_401k(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_age: INT, current_balance: DOUBLE, projection_years: INT, retirement_age: INT, assumed_return_rate: DOUBLE, assumed_contribution: DOUBLE, projected_balance: DOUBLE, total_contributions: DOUBLE, investment_growth: DOUBLE, rmd_required: BOOLEAN, rmd_age: INT, summary: STRING, regulation: STRING, authority: STRING>
COMMENT 'Project 401(k) balance growth over time'
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age as current_age,
  CAST(super_balance AS DOUBLE) as current_balance,
  LEAST(projection_years, 30) as projection_years,
  65 as retirement_age,
  
  -- Assumed return rate
  CAST(
    CASE 
      WHEN member_age < 50 THEN 0.08
      WHEN member_age < 60 THEN 0.07
      ELSE 0.06
    END
  AS DOUBLE) as assumed_return_rate,
  
  -- Assumed annual contribution
  CAST(10000.0 AS DOUBLE) as assumed_contribution,
  
  -- Projected balance - ✅ FIX: Handle division by zero
  CAST(
    CASE
      WHEN projection_years <= 0 THEN super_balance
      WHEN member_age >= 65 THEN super_balance  -- Already retired
      ELSE 
        super_balance * POWER(
          1.0 + CASE 
            WHEN member_age < 50 THEN 0.08
            WHEN member_age < 60 THEN 0.07
            ELSE 0.06
          END,
          CAST(LEAST(projection_years, 30) AS DOUBLE)
        ) + (
          10000.0 * (
            (POWER(
              1.0 + CASE 
                WHEN member_age < 50 THEN 0.08
                WHEN member_age < 60 THEN 0.07
                ELSE 0.06
              END,
              CAST(LEAST(projection_years, 30) AS DOUBLE)
            ) - 1.0) / NULLIF(CASE 
              WHEN member_age < 50 THEN 0.08
              WHEN member_age < 60 THEN 0.07
              ELSE 0.06
            END, 0)
          )
        )
    END
  AS DOUBLE) as projected_balance,
  
  -- Total contributions
  CAST(
    CASE
      WHEN projection_years <= 0 THEN 0.0
      WHEN member_age >= 65 THEN 0.0
      ELSE 10000.0 * CAST(LEAST(projection_years, 30) AS DOUBLE)
    END
  AS DOUBLE) as total_contributions,
  
  -- Investment growth
  CAST(
    CASE
      WHEN projection_years <= 0 THEN 0.0
      WHEN member_age >= 65 THEN 0.0
      ELSE (
        super_balance * POWER(
          1.0 + CASE 
            WHEN member_age < 50 THEN 0.08
            WHEN member_age < 60 THEN 0.07
            ELSE 0.06
          END,
          CAST(LEAST(projection_years, 30) AS DOUBLE)
        ) + (
          10000.0 * (
            (POWER(
              1.0 + CASE 
                WHEN member_age < 50 THEN 0.08
                WHEN member_age < 60 THEN 0.07
                ELSE 0.06
              END,
              CAST(LEAST(projection_years, 30) AS DOUBLE)
            ) - 1.0) / NULLIF(CASE 
              WHEN member_age < 50 THEN 0.08
              WHEN member_age < 60 THEN 0.07
              ELSE 0.06
            END, 0)
          )
        )
      ) - super_balance - (10000.0 * CAST(LEAST(projection_years, 30) AS DOUBLE))
    END
  AS DOUBLE) as investment_growth,
  
  -- RMD required at age 73
  member_age >= 73 OR (member_age + projection_years) >= 73 as rmd_required,
  73 as rmd_age,
  
  -- Summary
  CASE 
    WHEN member_age >= 65 THEN
      CONCAT('At retirement age - Current balance: USD ', FORMAT_NUMBER(super_balance, 0))
    WHEN projection_years <= 0 THEN
      CONCAT('Current balance: USD ', FORMAT_NUMBER(super_balance, 0))
    ELSE
      CONCAT('Projected balance in ', CAST(LEAST(projection_years, 30) AS STRING), 
             ' years: USD ',
             FORMAT_NUMBER(
               super_balance * POWER(
                 1.0 + CASE 
                   WHEN member_age < 50 THEN 0.08
                   WHEN member_age < 60 THEN 0.07
                   ELSE 0.06
                 END,
                 CAST(LEAST(projection_years, 30) AS DOUBLE)
               ),
               0
             ),
             CASE WHEN member_age + projection_years >= 73 
                  THEN ' (RMD required at age 73)' 
                  ELSE '' 
             END)
  END as summary,
  
  'Internal Revenue Code, Section 401(k); ERISA 1974' as regulation,
  'Department of Labor / IRS' as authority
);

--------------------------------------------------------------------------------

-- Function: us_project_401k_balance

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_project_401k_balance(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_age: INT, retirement_age: INT, projection_years: INT, current_balance: DOUBLE, projected_balance: DOUBLE, total_contributions: DOUBLE, investment_growth: DOUBLE, summary: STRING, regulation: STRING, authority: STRING>
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age as current_age,
  retirement_age,
  LEAST(projection_years, retirement_age - member_age) as projection_years,
  account_balance as current_balance,
  
  -- ✅ FIX: Handle case where already at retirement age
  CASE 
    WHEN member_age >= retirement_age THEN account_balance
    WHEN retirement_age - member_age = 0 THEN account_balance  -- Safety check
    ELSE 
      account_balance * POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
      (annual_contribution * ((POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.08))
  END as projected_balance,
  
  -- Total contributions
  CASE
    WHEN member_age >= retirement_age THEN 0.0
    ELSE annual_contribution * CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)
  END as total_contributions,
  
  -- Investment growth
  CASE 
    WHEN member_age >= retirement_age THEN 0.0
    WHEN retirement_age - member_age = 0 THEN 0.0
    ELSE (account_balance * POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
          (annual_contribution * ((POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.08))) - 
          account_balance - (annual_contribution * CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE))
  END as investment_growth,
  
  CASE 
    WHEN member_age >= retirement_age THEN
      CONCAT('At retirement age - Current balance: USD ', FORMAT_NUMBER(account_balance, 0))
    ELSE
      CONCAT('Projected balance at age ', CAST(retirement_age AS STRING), ': USD ',
             FORMAT_NUMBER(
               account_balance * POWER(1.08, CAST(retirement_age - member_age AS DOUBLE)) +
               (annual_contribution * ((POWER(1.08, CAST(retirement_age - member_age AS DOUBLE)) - 1) / 0.08)),
               0
             ))
  END as summary,
  
  'Internal Revenue Code, Section 401(k); ERISA 1974' as regulation,
  'Department of Labor / IRS' as authority
);

--------------------------------------------------------------------------------

-- Function: us_project_retirement_balance
-- Project retirement account balance with growth, contributions, and withdrawals

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_project_retirement_balance(
    member_id STRING
)
RETURNS STRUCT<member_id: STRING, current_age: INT, current_balance: DOUBLE, retirement_age: INT, projection_years: INT, retirement_phase: STRING, annual_return_rate: DOUBLE, annual_withdrawal_rate: DOUBLE, estimated_final_balance: DOUBLE, rmd_required: BOOLEAN, rmd_age: INT, balance_depleted: BOOLEAN, summary: STRING, regulation: STRING, authority: STRING>
COMMENT 'Project retirement account balance with growth, contributions, and withdrawals'
LANGUAGE SQL
RETURN
    STRUCT(
  member_id,
  member_age as current_age,
  CAST(account_balance AS DOUBLE) as current_balance,
  retirement_age,
  LEAST(projection_years, 30) as projection_years,
  
  -- Retirement phase
  CASE 
    WHEN member_age < retirement_age THEN 'Accumulation (Pre-retirement)'
    WHEN member_age < 65 THEN 'Early Retirement (Before Medicare)'
    WHEN member_age < 73 THEN 'Mid Retirement (Before RMD)'
    ELSE 'Late Retirement (RMD Required)'
  END as retirement_phase,
  
  -- Return rate - CAST AS DOUBLE
  CAST(
    CASE 
      WHEN member_age < retirement_age THEN 0.08
      WHEN member_age < 65 THEN 0.07
      WHEN member_age < 73 THEN 0.06
      ELSE 0.05
    END
  AS DOUBLE) as annual_return_rate,
  
  -- Withdrawal rate - CAST AS DOUBLE
  CAST(
    CASE 
      WHEN member_age < retirement_age THEN 0.0
      WHEN member_age < 73 THEN 0.04
      WHEN member_age < 75 THEN 0.0366
      WHEN member_age < 80 THEN 0.04
      ELSE 0.05
    END
  AS DOUBLE) as annual_withdrawal_rate,
  
  -- Estimated final balance - CAST AS DOUBLE
  CAST(
    CASE 
      WHEN member_age < retirement_age THEN
        account_balance * POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) +
        (annual_contribution * ((POWER(1.08, CAST(LEAST(projection_years, retirement_age - member_age) AS DOUBLE)) - 1) / 0.08))
      ELSE
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
    END
  AS DOUBLE) as estimated_final_balance,
  
  -- RMD required
  member_age >= 73 OR (member_age + projection_years) >= 73 as rmd_required,
  73 as rmd_age,
  
  -- Balance depleted
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
  
  -- Summary
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

--------------------------------------------------------------------------------

-- ============================================================================
-- FUNCTION PERMISSIONS
-- ============================================================================
-- Apply these grants after creating all functions

-- au_calculate_tax
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.au_calculate_tax TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.au_calculate_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.au_calculate_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- au_check_pension_impact
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.au_check_pension_impact TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.au_check_pension_impact TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.au_check_pension_impact TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- au_project_balance
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.au_project_balance TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.au_project_balance TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.au_project_balance TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- in_calculate_epf_tax
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- in_calculate_eps_benefits
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_eps_benefits TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_eps_benefits TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_eps_benefits TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- in_calculate_nps
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- in_calculate_nps_benefits
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps_benefits TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps_benefits TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps_benefits TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- in_project_retirement
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_project_retirement TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.in_project_retirement TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.in_project_retirement TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- in_project_retirement_corpus
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_project_retirement_corpus TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.in_project_retirement_corpus TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.in_project_retirement_corpus TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- uk_calculate_pension_tax
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.uk_calculate_pension_tax TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.uk_calculate_pension_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.uk_calculate_pension_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- uk_check_state_pension
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.uk_check_state_pension TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.uk_check_state_pension TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.uk_check_state_pension TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- uk_project_pension_balance
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.uk_project_pension_balance TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.uk_project_pension_balance TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.uk_project_pension_balance TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- us_calculate_401k_tax
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_calculate_401k_tax TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.us_calculate_401k_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.us_calculate_401k_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- us_calculate_tax
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_calculate_tax TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.us_calculate_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.us_calculate_tax TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- us_check_social_security
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_check_social_security TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.us_check_social_security TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.us_check_social_security TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- us_project_401k
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_project_401k TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.us_project_401k TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.us_project_401k TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- us_project_401k_balance
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_project_401k_balance TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.us_project_401k_balance TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.us_project_401k_balance TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;

-- us_project_retirement_balance
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_project_retirement_balance TO `account users`;
GRANT ALL PRIVILEGES ON FUNCTION super_advisory_demo.pension_calculators.us_project_retirement_balance TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
GRANT MANAGE ON FUNCTION super_advisory_demo.pension_calculators.us_project_retirement_balance TO `57e7dc57-63b9-4114-a2ad-0a6226794a22`;
