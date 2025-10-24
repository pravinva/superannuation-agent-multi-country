-- ============================================================================
-- CITATION REGISTRY TABLE
-- Authoritative source references for all retirement calculators
-- NEVER make up citations - all must be verified and stored here
-- ============================================================================

CREATE TABLE IF NOT EXISTS super_advisory_demo.member_data.citation_registry (
    citation_id STRING PRIMARY KEY COMMENT 'Unique citation identifier (e.g., AU-TAX-001)',
    country STRING COMMENT 'Country code (AU, US, UK, IN)',
    authority STRING COMMENT 'Regulatory authority name',
    regulation_name STRING COMMENT 'Name of regulation or standard',
    regulation_code STRING COMMENT 'Specific code or section reference',
    effective_date DATE COMMENT 'Date regulation became effective',
    source_url STRING COMMENT 'Official URL to regulation',
    description STRING COMMENT 'Brief description of what this regulates',
    last_verified TIMESTAMP COMMENT 'When citation was last verified'
)
USING DELTA
COMMENT 'Verified citation registry - ensures all calculator citations are authoritative and traceable'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true'
);

-- ============================================================================
-- AUSTRALIA CITATIONS
-- ============================================================================

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'AU-TAX-001',
    'AU',
    'Australian Taxation Office (ATO)',
    'Income Tax Assessment Act 1997',
    'Division 301',
    '2024-07-01',
    'https://www.ato.gov.au/law/view/document?docid=PAC/19970038/301-1',
    'Tax treatment of superannuation benefits - tax-free component rules for withdrawals after preservation age',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'AU-PENSION-001',
    'AU',
    'Department of Social Services (DSS)',
    'Social Security Act 1991',
    'Part 3.10 - Asset Test',
    '2024-09-20',
    'https://www.dss.gov.au/seniors/age-pension/age-pension-assets-test',
    'Age Pension asset test thresholds and taper rates for homeowners and non-homeowners',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'AU-STANDARD-001',
    'AU',
    'Association of Superannuation Funds of Australia (ASFA)',
    'ASFA Retirement Standard',
    '2024-25',
    '2024-09-01',
    'https://www.superannuation.asn.au/resources/retirement-standard',
    'Comfortable and modest retirement income benchmarks for singles and couples',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'AU-PRESERVATION-001',
    'AU',
    'Australian Taxation Office (ATO)',
    'Superannuation Industry (Supervision) Regulations 1994',
    'Schedule 1 - Preservation Ages',
    '1994-07-01',
    'https://www.ato.gov.au/individuals/super/withdrawing-and-using-your-super/preservation-age',
    'Preservation age table based on date of birth - determines when super can be accessed',
    CURRENT_TIMESTAMP()
);

-- ============================================================================
-- USA CITATIONS
-- ============================================================================

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'US-TAX-001',
    'US',
    'Internal Revenue Service (IRS)',
    'Internal Revenue Code',
    'Section 401(k)',
    '2024-01-01',
    'https://www.irs.gov/retirement-plans/plan-participant-employee/401k-resource-guide',
    '401(k) plan contribution limits, withdrawal rules, and early withdrawal penalties',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'US-PENALTY-001',
    'US',
    'Internal Revenue Service (IRS)',
    'Internal Revenue Code',
    'Section 72(t)',
    '2024-01-01',
    'https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-tax-on-early-distributions',
    '10% early withdrawal penalty for distributions before age 59½ with exceptions',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'US-SS-001',
    'US',
    'Social Security Administration (SSA)',
    'Social Security Act',
    'Title II',
    '2025-01-01',
    'https://www.ssa.gov/OACT/COLA/Benefits.html',
    'Social Security retirement benefit calculation and full retirement age determination',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'US-RMD-001',
    'US',
    'Internal Revenue Service (IRS)',
    'SECURE 2.0 Act',
    'Section 401(a)(9)',
    '2023-01-01',
    'https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-required-minimum-distributions-rmds',
    'Required Minimum Distribution rules starting at age 73 (changed from 72 in 2023)',
    CURRENT_TIMESTAMP()
);

-- ============================================================================
-- UK CITATIONS
-- ============================================================================

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'UK-TAX-001',
    'UK',
    'HM Revenue & Customs (HMRC)',
    'Finance Act 2004',
    'Part 4 - Pension Schemes',
    '2024-04-06',
    'https://www.gov.uk/tax-on-your-private-pension',
    'Pension tax relief and 25% tax-free lump sum rules',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'UK-PENSION-001',
    'UK',
    'Department for Work and Pensions (DWP)',
    'Pensions Act 2014',
    'Section 4 - State Pension',
    '2024-04-06',
    'https://www.gov.uk/new-state-pension',
    'New State Pension eligibility, amounts (£221.20/week), and National Insurance requirements',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'UK-AGE-001',
    'UK',
    'Department for Work and Pensions (DWP)',
    'Pensions Act 1995',
    'Schedule 4 - State Pension Age',
    '2024-04-06',
    'https://www.gov.uk/state-pension-age',
    'State Pension age timetable - currently 66, rising to 67 by 2028',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'UK-DRAWDOWN-001',
    'UK',
    'Financial Conduct Authority (FCA)',
    'Pension Wise Guidance',
    '2015',
    '2024-04-06',
    'https://www.moneyhelper.org.uk/en/pensions-and-retirement/taking-your-pension',
    'Pension drawdown guidance including sustainable withdrawal rates',
    CURRENT_TIMESTAMP()
);

-- ============================================================================
-- INDIA CITATIONS
-- ============================================================================

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'IN-EPF-001',
    'IN',
    'Employees Provident Fund Organisation (EPFO)',
    'Employees Provident Funds Scheme',
    '1952',
    '2024-04-01',
    'https://www.epfindia.gov.in/site_docs/PDFs/Downloads_PDFs/withdrawalProcess.pdf',
    'EPF withdrawal rules - tax-free after 5 years continuous service',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'IN-TAX-001',
    'IN',
    'Income Tax Department',
    'Income Tax Act 1961',
    'Section 10(12)',
    '2024-04-01',
    'https://www.incometax.gov.in/iec/foportal/',
    'Taxation of EPF withdrawals - conditions for tax exemption',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'IN-NPS-001',
    'IN',
    'Pension Fund Regulatory and Development Authority (PFRDA)',
    'PFRDA Act 2013',
    'NPS Regulations',
    '2024-04-01',
    'https://www.npstrust.org.in/content/tax-benefits',
    'National Pension System regulations - 40% compulsory annuity, 60% lump sum withdrawal',
    CURRENT_TIMESTAMP()
);

INSERT INTO super_advisory_demo.member_data.citation_registry VALUES
(
    'IN-INTEREST-001',
    'IN',
    'Employees Provident Fund Organisation (EPFO)',
    'EPF Interest Rate Declaration',
    '2024-25',
    '2024-04-01',
    'https://www.epfindia.gov.in/',
    'EPF interest rate - currently 8.25% per annum as declared by EPFO',
    CURRENT_TIMESTAMP()
);

-- ============================================================================
-- VERIFY CITATIONS
-- ============================================================================

-- Check total citations by country
SELECT country, COUNT(*) as citation_count
FROM super_advisory_demo.member_data.citation_registry
GROUP BY country
ORDER BY country;

-- View all citations
SELECT 
    citation_id,
    country,
    authority,
    CONCAT(regulation_name, ' (', regulation_code, ')') as regulation,
    source_url
FROM super_advisory_demo.member_data.citation_registry
ORDER BY country, citation_id;

-- Test: Fetch Australian citations
SELECT 
    authority,
    regulation_name,
    regulation_code,
    source_url,
    description
FROM super_advisory_demo.member_data.citation_registry
WHERE citation_id IN ('AU-TAX-001', 'AU-PENSION-001', 'AU-STANDARD-001')
ORDER BY citation_id;
