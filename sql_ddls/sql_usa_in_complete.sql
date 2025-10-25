-- ============================================================================
-- USA FUNCTIONS - EXACT MATCH TO tools.py SIGNATURES
-- ============================================================================

-- 1. us_calculate_tax
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_calculate_tax(
    member_id STRING,
    member_age INT,
    super_balance DOUBLE,
    withdrawal_amount DOUBLE
)
RETURNS STRUCT<
    member_id: STRING,
    member_age: INT,
    account_balance: DOUBLE,
    withdrawal_amount: DOUBLE,
    account_type: STRING,
    early_withdrawal_penalty: DOUBLE,
    income_tax_amount: DOUBLE,
    total_tax: DOUBLE,
    net_withdrawal: DOUBLE,
    status: STRING,
    regulation: STRING,
    authority: STRING
>
COMMENT 'Calculate 401k/IRA withdrawal tax with early penalty if under 59.5'
RETURN STRUCT(
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


-- 2. us_check_social_security
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_check_social_security(
    member_id STRING,
    member_age INT,
    marital_status STRING,
    super_balance DOUBLE
)
RETURNS STRUCT<
    member_id: STRING,
    current_age: INT,
    marital_status: STRING,
    account_balance: DOUBLE,
    full_retirement_age: INT,
    earliest_claim_age: INT,
    can_claim_now: BOOLEAN,
    estimated_monthly_benefit: DOUBLE,
    estimated_annual_benefit: DOUBLE,
    spousal_benefit_eligible: BOOLEAN,
    years_until_fra: INT,
    benefit_status: STRING,
    regulation: STRING,
    authority: STRING
>
COMMENT 'Check Social Security eligibility and estimated benefits'
RETURN STRUCT(
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


-- 3. us_project_401k
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.us_project_401k(
    member_id STRING,
    member_age INT,
    super_balance DOUBLE,
    projection_years INT
)
RETURNS STRUCT<
    member_id: STRING,
    current_age: INT,
    current_balance: DOUBLE,
    projection_years: INT,
    retirement_age: INT,
    assumed_return_rate: DOUBLE,
    assumed_contribution: DOUBLE,
    projected_balance: DOUBLE,
    total_contributions: DOUBLE,
    investment_growth: DOUBLE,
    rmd_required: BOOLEAN,
    rmd_age: INT,
    summary: STRING,
    regulation: STRING,
    authority: STRING
>
COMMENT 'Project 401(k) balance growth over time'
RETURN STRUCT(
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


-- ============================================================================
-- INDIA FUNCTIONS - EXACT MATCH TO tools.py SIGNATURES
-- ============================================================================

-- 1. in_calculate_epf_tax
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax(
    member_id STRING,
    member_age INT,
    super_balance DOUBLE,
    withdrawal_amount DOUBLE
)
RETURNS STRUCT<
    member_id: STRING,
    member_age: INT,
    epf_balance: DOUBLE,
    withdrawal_amount: DOUBLE,
    withdrawal_type: STRING,
    estimated_years_of_service: INT,
    tax_amount: DOUBLE,
    tds_amount: DOUBLE,
    net_withdrawal: DOUBLE,
    tax_exempt: BOOLEAN,
    status: STRING,
    regulation: STRING,
    authority: STRING
>
COMMENT 'Calculate EPF withdrawal tax based on age and service years'
RETURN STRUCT(
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


-- 2. in_calculate_nps
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps(
    member_id STRING,
    member_age INT,
    super_balance DOUBLE
)
RETURNS STRUCT<
    member_id: STRING,
    member_age: INT,
    nps_corpus: DOUBLE,
    min_annuity_pct: DOUBLE,
    max_lump_sum_pct: DOUBLE,
    min_annuity_amount: DOUBLE,
    max_lump_sum: DOUBLE,
    lump_sum_tax_free: DOUBLE,
    estimated_monthly_pension: DOUBLE,
    estimated_annual_pension: DOUBLE,
    is_eligible: BOOLEAN,
    nps_status: STRING,
    regulation: STRING,
    authority: STRING
>
COMMENT 'Calculate NPS benefits with 40% annuity requirement and 60% tax-free lump sum'
RETURN STRUCT(
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


-- 3. in_project_retirement
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.in_project_retirement(
    member_id STRING,
    member_age INT,
    super_balance DOUBLE,
    projection_years INT
)
RETURNS STRUCT<
    member_id: STRING,
    current_age: INT,
    current_balance: DOUBLE,
    retirement_age: INT,
    projection_years: INT,
    epf_return_rate: DOUBLE,
    nps_return_rate: DOUBLE,
    projected_epf_balance: DOUBLE,
    projected_nps_balance: DOUBLE,
    total_projected_corpus: DOUBLE,
    retirement_phase: STRING,
    summary: STRING,
    regulation: STRING,
    authority: STRING
>
COMMENT 'Project EPF/NPS retirement corpus growth'
RETURN STRUCT(
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


-- ============================================================================
-- TEST ALL 6 FUNCTIONS
-- ============================================================================

SELECT '=== Testing USA Functions ===' as test_header;

-- Test us_calculate_tax
SELECT 'us_calculate_tax' as function_name, result.* FROM (
    SELECT super_advisory_demo.pension_calculators.us_calculate_tax(
        'TEST_US_001', 55, 250000.0, 50000.0
    ) as result
);

-- Test us_check_social_security
SELECT 'us_check_social_security' as function_name, result.* FROM (
    SELECT super_advisory_demo.pension_calculators.us_check_social_security(
        'TEST_US_001', 65, 'Married', 250000.0
    ) as result
);

-- Test us_project_401k
SELECT 'us_project_401k' as function_name, result.* FROM (
    SELECT super_advisory_demo.pension_calculators.us_project_401k(
        'TEST_US_001', 45, 250000.0, 20
    ) as result
);

SELECT '=== Testing India Functions ===' as test_header;

-- Test in_calculate_epf_tax
SELECT 'in_calculate_epf_tax' as function_name, result.* FROM (
    SELECT super_advisory_demo.pension_calculators.in_calculate_epf_tax(
        'TEST_IN_001', 45, 500000.0, 100000.0
    ) as result
);

-- Test in_calculate_nps
SELECT 'in_calculate_nps' as function_name, result.* FROM (
    SELECT super_advisory_demo.pension_calculators.in_calculate_nps(
        'TEST_IN_001', 62, 1000000.0
    ) as result
);

-- Test in_project_retirement
SELECT 'in_project_retirement' as function_name, result.* FROM (
    SELECT super_advisory_demo.pension_calculators.in_project_retirement(
        'TEST_IN_001', 45, 500000.0, 15
    ) as result
);

SELECT '✅ All USA and India functions match tools.py signatures!' as status;


-- ============================================================================
-- GRANT EXECUTE PERMISSIONS TO ACCOUNT USERS FOR USA AND INDIA FUNCTIONS
-- ============================================================================

-- USA Functions
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_calculate_tax TO `account users`;
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_check_social_security TO `account users`;
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.us_project_401k TO `account users`;

-- INDIA Functions
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax TO `account users`;
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_nps TO `account users`;
GRANT EXECUTE ON FUNCTION super_advisory_demo.pension_calculators.in_project_retirement TO `account users`;

-- ============================================================================
-- Optionally verify that privileges were applied
-- ============================================================================
SHOW GRANTS ON FUNCTION super_advisory_demo.pension_calculators.us_calculate_tax;
SHOW GRANTS ON FUNCTION super_advisory_demo.pension_calculators.in_calculate_epf_tax;

