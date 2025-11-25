#!/usr/bin/env python3
"""
Generate realistic demo data for Superannuation Agent using Faker
==================================================================

Generates synthetic member profiles, citations, and governance data
matching the existing schema structure but with Faker-generated values.

Usage:
    python generate_demo_data.py --output parquet  # Generate parquet files
    python generate_demo_data.py --output sql      # Generate SQL INSERT statements
    python generate_demo_data.py --preview         # Preview data without saving

Tables generated:
    - member_profiles: Synthetic retirement fund members
    - citation_registry: Regulatory citations (mostly static)
    - governance: Audit logs of agent queries
"""

import argparse
import random
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from faker import Faker

# Initialize Faker instances for different locales
fake_au = Faker('en_AU')
fake_us = Faker('en_US')
fake_uk = Faker('en_GB')
fake_in = Faker('en_IN')

# Country-specific configuration
COUNTRY_CONFIG = {
    'AU': {
        'faker': fake_au,
        'preservation_age': 60,
        'member_prefix': 'AU',
        'count': 20,
        'currency_range': (68000, 1250000),  # AUD
        'income_range': (0, 125000),
        'persona_types': ['Below Average', 'Middle Income', 'Comfortable', 'High Net Worth']
    },
    'US': {
        'faker': fake_us,
        'preservation_age': 59,
        'member_prefix': 'US',
        'count': 3,
        'currency_range': (125000, 580000),  # USD converted estimate
        'income_range': (25000, 95000),
        'persona_types': ['Pre-retirement Planner', 'Wealth Accumulator', 'Retiree Drawdown']
    },
    'UK': {
        'faker': fake_uk,
        'preservation_age': 55,
        'member_prefix': 'UK',
        'count': 2,
        'currency_range': (195000, 280000),  # GBP converted estimate
        'income_range': (60000, 75000),
        'persona_types': ['Pre-retirement Planner', 'Wealth Accumulator']
    },
    'IN': {
        'faker': fake_in,
        'preservation_age': 58,
        'member_prefix': 'IN',
        'count': 3,
        'currency_range': (68000, 220000),  # INR converted estimate (in thousands)
        'income_range': (12000, 45000),
        'persona_types': ['Pre-retirement Planner', 'Wealth Accumulator', 'Retiree Drawdown']
    }
}

# Enum values for categorical fields
EMPLOYMENT_STATUS = ['Full-time', 'Part-time', 'Retired', 'Self-employed', 'Unemployed - Health', 'Employed']
FINANCIAL_LITERACY = ['Low', 'Medium', 'Moderate', 'High']
GENDER = ['Male', 'Female']
HEALTH_STATUS = ['Excellent', 'Good', 'Fair', 'Poor', 'Chronic illness']
HOME_OWNERSHIP = [
    'Owned Outright', 'Homeowner - No Mortgage', 'Homeowner - Mortgage',
    'Owned with Mortgage', 'Renter', 'Renting', 'Owner'
]
RISK_PROFILE = ['Conservative', 'Balanced', 'Moderate', 'Growth', 'Aggressive']
MARITAL_STATUS = ['Single', 'Married', 'Divorced', 'Widowed']


def generate_member_profile(country: str, member_number: int) -> Dict:
    """Generate a single member profile with realistic data"""
    config = COUNTRY_CONFIG[country]
    faker = config['faker']

    # Basic demographics
    age = random.randint(35, 75)
    gender = random.choice(GENDER)

    # Name based on gender and country
    if gender == 'Male':
        name = faker.name_male()
    else:
        name = faker.name_female()

    # Employment and retirement phase logic
    is_retired = age >= 65 or random.random() < 0.2
    employment_status = 'Retired' if is_retired else random.choice([
        'Full-time', 'Part-time', 'Self-employed', 'Employed'
    ])

    # Financial details based on life stage
    super_balance = random.randint(*config['currency_range'])

    # Account-based pension (only if retired and over preservation age)
    if is_retired and age >= config['preservation_age']:
        account_based_pension = random.choice([0, random.randint(25000, 85000)])
    else:
        account_based_pension = 0

    # Income (lower if retired)
    if is_retired:
        annual_income_outside_super = random.choice([0, random.randint(5000, 25000)])
    else:
        annual_income_outside_super = random.randint(*config['income_range'])

    # Debt (higher for younger, lower for retirees)
    if age < 50:
        debt = random.randint(30000, 180000)
    elif age < 60:
        debt = random.randint(20000, 95000)
    else:
        debt = random.choice([0, random.randint(0, 50000)])

    # Dependents (fewer for older members)
    if age < 45:
        dependents = random.randint(0, 3)
    elif age < 60:
        dependents = random.randint(0, 2)
    else:
        dependents = random.choice([0, 0, 0, 1])

    # Other financial attributes
    financial_literacy = random.choice(FINANCIAL_LITERACY)
    health_status = random.choice(HEALTH_STATUS)

    # Home ownership (more likely owned for older)
    if age >= 60:
        home_ownership = random.choice([
            'Owned Outright', 'Homeowner - No Mortgage', 'Owner'
        ])
    else:
        home_ownership = random.choice(HOME_OWNERSHIP)

    # Other assets
    other_assets = random.randint(8000, 450000)

    # Persona type
    persona_type = random.choice(config['persona_types'])

    # Risk profile (more conservative with age)
    if age >= 65:
        risk_profile = random.choice(['Conservative', 'Balanced', 'Moderate'])
    elif age >= 55:
        risk_profile = random.choice(['Balanced', 'Moderate', 'Growth'])
    else:
        risk_profile = random.choice(['Growth', 'Aggressive', 'Balanced'])

    # Marital status
    marital_status = random.choice(MARITAL_STATUS)

    return {
        'account_based_pension': account_based_pension,
        'age': age,
        'annual_income_outside_super': annual_income_outside_super,
        'debt': debt,
        'dependents': dependents,
        'employment_status': employment_status,
        'financial_literacy': financial_literacy,
        'gender': gender,
        'health_status': health_status,
        'home_ownership': home_ownership,
        'member_id': f"{config['member_prefix']}{member_number:03d}",
        'name': name,
        'other_assets': other_assets,
        'persona_type': persona_type,
        'preservation_age': config['preservation_age'],
        'risk_profile': risk_profile,
        'super_balance': super_balance,
        'marital_status': marital_status,
        'country': country
    }


def generate_member_profiles() -> pd.DataFrame:
    """Generate all member profiles across all countries"""
    members = []

    for country, config in COUNTRY_CONFIG.items():
        for i in range(1, config['count'] + 1):
            member = generate_member_profile(country, i)
            members.append(member)

    df = pd.DataFrame(members)

    # Reorder columns to match SQL schema
    column_order = [
        'account_based_pension', 'age', 'annual_income_outside_super', 'debt',
        'dependents', 'employment_status', 'financial_literacy', 'gender',
        'health_status', 'home_ownership', 'member_id', 'name', 'other_assets',
        'persona_type', 'preservation_age', 'risk_profile', 'super_balance',
        'marital_status', 'country'
    ]

    return df[column_order]


def generate_citation_registry() -> pd.DataFrame:
    """
    Generate citation registry data.
    This is mostly static regulatory data - keeping similar to original.
    """
    citations = [
        # Australia
        {
            'citation_id': 'AU-PENSION-001',
            'country': 'AU',
            'authority': 'Department of Social Services (DSS)',
            'regulation_name': 'Social Security Act 1991',
            'regulation_code': 'Part 3.10 - Asset Test',
            'effective_date': '2024-09-20',
            'source_url': 'https://www.dss.gov.au/seniors/age-pension/age-pension-assets-test',
            'description': 'Age Pension asset test thresholds and taper rates for homeowners and non-homeowners',
            'last_verified': datetime.now(),
            'tool_type': 'benefit'
        },
        {
            'citation_id': 'AU-PRESERVATION-001',
            'country': 'AU',
            'authority': 'Australian Taxation Office (ATO)',
            'regulation_name': 'Superannuation Industry (Supervision) Regulations 1994',
            'regulation_code': 'Schedule 1 - Preservation Ages',
            'effective_date': '1994-07-01',
            'source_url': 'https://www.ato.gov.au/individuals/super/withdrawing-and-using-your-super/preservation-age',
            'description': 'Preservation age table based on date of birth - determines when super can be accessed',
            'last_verified': datetime.now(),
            'tool_type': 'benefit'
        },
        {
            'citation_id': 'AU-TAX-001',
            'country': 'AU',
            'authority': 'Australian Taxation Office (ATO)',
            'regulation_name': 'Income Tax Assessment Act 1997',
            'regulation_code': 'Division 301',
            'effective_date': '2024-07-01',
            'source_url': 'https://www.ato.gov.au/law/view/document?docid=PAC/19970038/301-1',
            'description': 'Tax treatment of superannuation benefits - tax-free component rules for withdrawals after preservation age',
            'last_verified': datetime.now(),
            'tool_type': 'tax'
        },
        # United States
        {
            'citation_id': 'US-IRA-001',
            'country': 'US',
            'authority': 'Internal Revenue Service (IRS)',
            'regulation_name': 'Internal Revenue Code',
            'regulation_code': 'Section 408 - Individual Retirement Accounts',
            'effective_date': '2024-01-01',
            'source_url': 'https://www.irs.gov/retirement-plans/individual-retirement-arrangements-iras',
            'description': 'Traditional and Roth IRA rules including contribution limits and withdrawal taxation',
            'last_verified': datetime.now(),
            'tool_type': 'tax'
        },
        {
            'citation_id': 'US-RMD-001',
            'country': 'US',
            'authority': 'Internal Revenue Service (IRS)',
            'regulation_name': 'SECURE 2.0 Act',
            'regulation_code': 'Section 401(a)(9) - Required Minimum Distributions',
            'effective_date': '2023-01-01',
            'source_url': 'https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-required-minimum-distributions-rmds',
            'description': 'Required Minimum Distribution rules starting at age 73 (changed from 72 under SECURE 2.0)',
            'last_verified': datetime.now(),
            'tool_type': 'projection'
        },
        # United Kingdom
        {
            'citation_id': 'UK-PENSION-001',
            'country': 'UK',
            'authority': 'Department for Work and Pensions (DWP)',
            'regulation_name': 'Pensions Act 2014',
            'regulation_code': 'Section 4 - State Pension',
            'effective_date': '2024-04-06',
            'source_url': 'https://www.gov.uk/new-state-pension',
            'description': 'New State Pension eligibility, amounts (£221.20/week), and National Insurance requirements',
            'last_verified': datetime.now(),
            'tool_type': 'benefit'
        },
        {
            'citation_id': 'UK-TAX-001',
            'country': 'UK',
            'authority': 'HM Revenue & Customs (HMRC)',
            'regulation_name': 'Finance Act 2004',
            'regulation_code': 'Part 4 - Pension Schemes',
            'effective_date': '2024-04-06',
            'source_url': 'https://www.gov.uk/tax-on-your-private-pension',
            'description': 'Pension tax relief and 25% tax-free lump sum rules',
            'last_verified': datetime.now(),
            'tool_type': 'tax'
        },
        # India
        {
            'citation_id': 'IN-EPF-001',
            'country': 'IN',
            'authority': 'Employees Provident Fund Organisation (EPFO)',
            'regulation_name': 'Employees Provident Funds Scheme',
            'regulation_code': '1952',
            'effective_date': '2024-04-01',
            'source_url': 'https://www.epfindia.gov.in/',
            'description': 'EPF withdrawal rules - tax-free after 5 years continuous service or at age 58',
            'last_verified': datetime.now(),
            'tool_type': 'tax'
        },
        {
            'citation_id': 'IN-NPS-001',
            'country': 'IN',
            'authority': 'Pension Fund Regulatory and Development Authority (PFRDA)',
            'regulation_name': 'PFRDA Act 2013',
            'regulation_code': 'NPS Exit Regulations',
            'effective_date': '2024-04-01',
            'source_url': 'https://www.npstrust.org.in/content/tax-benefits',
            'description': 'National Pension System exit rules - 40% minimum annuity purchase, 60% lump sum tax-free withdrawal',
            'last_verified': datetime.now(),
            'tool_type': 'benefit'
        }
    ]

    return pd.DataFrame(citations)


def generate_governance_logs(member_profiles: pd.DataFrame, num_logs: int = 154) -> pd.DataFrame:
    """Generate fake governance audit logs"""
    logs = []

    # Sample queries for different topics
    query_templates = [
        "When can I access my super?",
        "How much tax will I pay on withdrawal?",
        "What is my preservation age?",
        "Can I make extra contributions?",
        "What are the Age Pension requirements?",
        "How do I transition to retirement?",
        "What happens to my super if I die?",
        "Can I access my super early due to hardship?",
        "What investment options should I choose?",
        "How much do I need to retire comfortably?"
    ]

    for i in range(num_logs):
        member = member_profiles.sample(1).iloc[0]
        query = random.choice(query_templates)

        # Generate fake response
        response = fake_au.paragraph(nb_sentences=3)

        # Simulate timestamps over the past 6 months
        timestamp = datetime.now() - timedelta(days=random.randint(0, 180),
                                                hours=random.randint(0, 23),
                                                minutes=random.randint(0, 59))

        log = {
            'event_id': f"EVT-{timestamp.strftime('%Y%m%d')}-{i:04d}",
            'timestamp': timestamp.isoformat(),
            'user_id': member['member_id'],
            'session_id': f"SESS-{fake_au.uuid4()[:8]}",
            'country': member['country'],
            'query_string': query,
            'agent_response': response[:1000],  # Truncate to 1000 chars
            'result_preview': f"Answered query about {query.lower()}",
            'cost': round(random.uniform(0.001, 0.05), 6),
            'citations': '["AU-TAX-001", "AU-PRESERVATION-001"]',  # Simplified
            'tool_used': random.choice(['calculate_tax', 'check_preservation_age', 'estimate_pension', None]),
            'judge_response': 'Response appropriate and accurate' if random.random() > 0.1 else 'Review recommended',
            'judge_verdict': random.choice(['Pass', 'Pass', 'Pass', 'Review']),
            'error_info': None if random.random() > 0.05 else 'Minor formatting issue',
            'validation_mode': random.choice(['llm_judge', 'hybrid', 'deterministic']),
            'validation_attempts': random.randint(1, 2),
            'total_time_seconds': round(random.uniform(0.5, 5.0), 2)
        }

        logs.append(log)

    return pd.DataFrame(logs)


def save_as_parquet(member_profiles: pd.DataFrame,
                   citation_registry: pd.DataFrame,
                   governance: pd.DataFrame,
                   output_dir: str = "data/generated"):
    """Save dataframes as parquet files"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    member_profiles.to_parquet(f"{output_dir}/member_profiles.parquet", index=False)
    citation_registry.to_parquet(f"{output_dir}/citation_registry.parquet", index=False)
    governance.to_parquet(f"{output_dir}/governance.parquet", index=False)

    print(f"✓ Saved parquet files to {output_dir}/")
    print(f"  - member_profiles.parquet ({len(member_profiles)} rows)")
    print(f"  - citation_registry.parquet ({len(citation_registry)} rows)")
    print(f"  - governance.parquet ({len(governance)} rows)")


def save_as_sql(member_profiles: pd.DataFrame,
               citation_registry: pd.DataFrame,
               governance: pd.DataFrame,
               output_file: str = "data/generated_data.sql"):
    """Generate SQL INSERT statements"""
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        f.write("-- Generated by generate_demo_data.py\n")
        f.write(f"-- Date: {datetime.now().isoformat()}\n\n")

        # Citation registry
        f.write("-- Citation Registry\n")
        f.write("INSERT INTO super_advisory_demo.member_data.citation_registry\n")
        f.write("  (citation_id, country, authority, regulation_name, regulation_code, ")
        f.write("effective_date, source_url, description, last_verified, tool_type)\n")
        f.write("VALUES\n")

        for idx, row in citation_registry.iterrows():
            values = (
                f"  ('{row['citation_id']}', '{row['country']}', '{row['authority']}', "
                f"'{row['regulation_name']}', '{row['regulation_code']}', '{row['effective_date']}', "
                f"'{row['source_url']}', '{row['description']}', "
                f"'{row['last_verified']}', '{row['tool_type']}')"
            )
            if idx < len(citation_registry) - 1:
                f.write(values + ",\n")
            else:
                f.write(values + ";\n\n")

        # Member profiles
        f.write("-- Member Profiles\n")
        f.write("INSERT INTO super_advisory_demo.member_data.member_profiles\n")
        f.write("  (account_based_pension, age, annual_income_outside_super, debt, dependents, ")
        f.write("employment_status, financial_literacy, gender, health_status, home_ownership, ")
        f.write("member_id, name, other_assets, persona_type, preservation_age, risk_profile, ")
        f.write("super_balance, marital_status, country)\n")
        f.write("VALUES\n")

        for idx, row in member_profiles.iterrows():
            values = (
                f"  ({row['account_based_pension']}, {row['age']}, {row['annual_income_outside_super']}, "
                f"{row['debt']}, {row['dependents']}, '{row['employment_status']}', "
                f"'{row['financial_literacy']}', '{row['gender']}', '{row['health_status']}', "
                f"'{row['home_ownership']}', '{row['member_id']}', '{row['name']}', "
                f"{row['other_assets']}, '{row['persona_type']}', {row['preservation_age']}, "
                f"'{row['risk_profile']}', {row['super_balance']}, '{row['marital_status']}', '{row['country']}')"
            )
            if idx < len(member_profiles) - 1:
                f.write(values + ",\n")
            else:
                f.write(values + ";\n\n")

    print(f"✓ Saved SQL file to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate realistic demo data for Superannuation Agent using Faker"
    )
    parser.add_argument(
        '--output',
        choices=['parquet', 'sql', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview data without saving'
    )
    parser.add_argument(
        '--num-governance-logs',
        type=int,
        default=154,
        help='Number of governance logs to generate (default: 154)'
    )

    args = parser.parse_args()

    print("Generating demo data with Faker...\n")

    # Generate data
    member_profiles = generate_member_profiles()
    citation_registry = generate_citation_registry()
    governance = generate_governance_logs(member_profiles, args.num_governance_logs)

    # Preview
    if args.preview:
        print("\n=== Member Profiles (first 5) ===")
        print(member_profiles.head())
        print(f"\nTotal: {len(member_profiles)} members")
        print(f"By country: {member_profiles['country'].value_counts().to_dict()}")

        print("\n=== Citation Registry (first 3) ===")
        print(citation_registry.head(3))
        print(f"\nTotal: {len(citation_registry)} citations")

        print("\n=== Governance Logs (first 3) ===")
        print(governance.head(3))
        print(f"\nTotal: {len(governance)} logs")
        return

    # Save data
    if args.output in ['parquet', 'both']:
        save_as_parquet(member_profiles, citation_registry, governance)

    if args.output in ['sql', 'both']:
        save_as_sql(member_profiles, citation_registry, governance)

    print("\n✓ Data generation complete!")


if __name__ == "__main__":
    main()
