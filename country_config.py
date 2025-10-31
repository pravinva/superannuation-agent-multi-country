#!/usr/bin/env python3
"""
Country-Specific Configuration Module
Centralized country configurations for easy multi-country support
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class CountryConfig:
    """
    Configuration for a specific country.
    
    All country-specific logic should be defined here,
    making it easy to add new countries.
    """
    # Basic Info
    code: str                          # "AU", "US", "UK", "IN"
    name: str                          # "Australia"
    currency: str                      # "AUD"
    currency_symbol: str               # "$"
    
    # Terminology
    retirement_account_term: str       # "superannuation", "401k", "pension", "EPF"
    balance_term: str                  # "super balance", "retirement balance", "pension pot"
    
    # Regulatory
    authorities: List[str]             # ["ATO", "Centrelink", "ASIC"]
    key_regulations: List[str]         # ["Superannuation Act 1992", ...]
    regulatory_urls: List[str]         # [https://www.ato.gov.au/...]
    
    # Advisory Context
    advisor_title: str                 # "Australian Superannuation Advisor"
    regulatory_context: str            # "Follow ATO tax rules..."
    
    # Special Instructions (country-specific)
    special_instructions: Optional[str] = None  # e.g., India balance split
    
    # Prompt Customization
    greeting_style: str = "formal"     # "formal", "casual", "neutral"
    
    # Tools
    available_tools: List[str] = None  # ["tax", "benefit", "projection"]
    
    def __post_init__(self):
        if self.available_tools is None:
            self.available_tools = ["tax", "benefit", "projection"]


# ============================================================================
# COUNTRY CONFIGURATIONS
# ============================================================================

COUNTRY_CONFIGS = {
    "AU": CountryConfig(
        code="AU",
        name="Australia",
        currency="AUD",
        currency_symbol="$",
        
        retirement_account_term="superannuation",
        balance_term="super balance",
        
        authorities=[
            "Australian Taxation Office (ATO)",
            "Department of Social Services (DSS)",
            "Australian Securities and Investments Commission (ASIC)"
        ],
        
        key_regulations=[
            "Superannuation Industry (Supervision) Act 1993",
            "Income Tax Assessment Act 1997",
            "Age Pension eligibility rules"
        ],
        
        regulatory_urls=[
            "https://www.ato.gov.au/super/",
            "https://www.dss.gov.au/"
        ],
        
        advisor_title="Australian Superannuation Advisor",
        
        regulatory_context="""Follow Australian superannuation regulations including:
- ATO tax rules on withdrawal
- Preservation age (typically 60) - CRITICAL: Unrestricted access begins at preservation age (60) upon retirement, NOT age 65
- Age 65 is the "unrestricted non-preserved age" where access is available regardless of employment status
- Age 60 (preservation age) + retirement = unrestricted access (this is the answer to "when can I access without restrictions?")
- Age Pension eligibility (age 67)
- Transition to Retirement (TTR) rules
Discuss all monetary values in AUD.""",
        
        special_instructions="""CRITICAL FOR AUSTRALIA MEMBERS:
When answering questions about "unrestricted access" or "access without restrictions":
- The answer is preservation age (typically 60) UPON RETIREMENT, NOT age 65
- Age 65 is the "unrestricted non-preserved age" where access is available regardless of employment status
- But unrestricted access upon retirement happens at preservation age (60)
- Always clarify: "At preservation age (60) upon retirement" for unrestricted access
- If asked "at what age can I access without restrictions?", answer: "preservation age (60) upon retirement"
- Do NOT say "age 65" as the answer to unrestricted access questions""",
        
        greeting_style="formal",
        available_tools=["tax", "benefit", "projection"]
    ),
    
    "US": CountryConfig(
        code="US",
        name="USA",
        currency="USD",
        currency_symbol="$",
        
        retirement_account_term="401(k) or IRA",
        balance_term="retirement balance",
        
        authorities=[
            "Internal Revenue Service (IRS)",
            "Social Security Administration (SSA)",
            "U.S. Department of Labor (DOL)"
        ],
        
        key_regulations=[
            "Internal Revenue Code Section 401(k)",
            "Internal Revenue Code Section 408 (IRA)",
            "SECURE 2.0 Act (2022)",
            "Required Minimum Distribution (RMD) rules"
        ],
        
        regulatory_urls=[
            "https://www.irs.gov/retirement-plans",
            "https://www.ssa.gov/"
        ],
        
        advisor_title="U.S. Retirement Advisor",
        
        regulatory_context="""Follow IRS regulations including:
- 401(k) and IRA withdrawal rules
- Early withdrawal penalties (10% before age 59½)
- Required Minimum Distributions (RMD) starting age 73
- Social Security benefit calculations
Discuss all monetary values in USD.""",
        
        special_instructions=None,
        
        greeting_style="neutral",
        available_tools=["tax", "benefit", "projection"]
    ),
    
    "UK": CountryConfig(
        code="UK",
        name="United Kingdom",
        currency="GBP",
        currency_symbol="£",
        
        retirement_account_term="pension",
        balance_term="pension pot",
        
        authorities=[
            "Her Majesty's Revenue and Customs (HMRC)",
            "UK Pensions Regulator (TPR)",
            "Financial Conduct Authority (FCA)"
        ],
        
        key_regulations=[
            "Pensions Act 2014",
            "Finance Act (pension tax relief)",
            "State Pension rules",
            "Pension freedoms (age 55)"
        ],
        
        regulatory_urls=[
            "https://www.gov.uk/pension-schemes",
            "https://www.gov.uk/tax-on-your-private-pension"
        ],
        
        advisor_title="UK Pension Advisor",
        
        regulatory_context="""Follow UK pension regulations including:
- HMRC pension drawdown rules
- 25% tax-free lump sum allowance
- State Pension eligibility (based on NI contributions)
- Normal Minimum Pension Age (NMPA) - typically age 55
Discuss all monetary values in GBP.""",
        
        special_instructions=None,
        
        greeting_style="formal",
        available_tools=["tax", "benefit", "projection"]
    ),
    
    "IN": CountryConfig(
        code="IN",
        name="India",
        currency="INR",
        currency_symbol="₹",
        
        retirement_account_term="EPF and NPS",
        balance_term="retirement corpus",
        
        authorities=[
            "Income Tax Department",
            "Pension Fund Regulatory and Development Authority (PFRDA)",
            "Employees' Provident Fund Organisation (EPFO)"
        ],
        
        key_regulations=[
            "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
            "PFRDA Act, 2013",
            "Income Tax Act, 1961 (Section 10(12), 80C)"
        ],
        
        regulatory_urls=[
            "https://www.epfindia.gov.in/",
            "https://www.npstrust.org.in/"
        ],
        
        advisor_title="Indian Provident Fund Advisor",
        
        regulatory_context="""Follow Indian retirement regulations including:
- EPF withdrawal rules (EPFO)
- NPS annuity requirements (PFRDA)
- Income Tax Act provisions (Section 10(12), 80C)
- EPS (Employees' Pension Scheme) benefits
Discuss all monetary values in INR.""",
        
        special_instructions="""CRITICAL FOR INDIA MEMBERS:
The member's retirement corpus is split into TWO schemes:
- EPF (Employees' Provident Fund): 75% of total - mandatory provident fund
- NPS (National Pension System): 25% of total - voluntary pension scheme

When discussing EPF, ONLY reference the EPF balance (75%), NOT the total.
When discussing NPS, ONLY reference the NPS balance (25%), NOT the total.
The tool results show the exact balances used for each calculation.
ALWAYS use the balance amounts shown in the tool calculation notes.""",
        
        greeting_style="formal",
        available_tools=["tax", "eps_benefit", "projection"]  # Note: eps_benefit instead of benefit
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_country_config(country_code: str) -> CountryConfig:
    """
    Get configuration for a specific country.
    
    Args:
        country_code: Two-letter country code (AU, US, UK, IN)
        
    Returns:
        CountryConfig object
        
    Raises:
        ValueError: If country code not supported
    """
    country_code = country_code.upper()
    
    if country_code not in COUNTRY_CONFIGS:
        raise ValueError(
            f"Country '{country_code}' not supported. "
            f"Available countries: {', '.join(COUNTRY_CONFIGS.keys())}"
        )
    
    return COUNTRY_CONFIGS[country_code]


def get_supported_countries() -> List[str]:
    """Get list of supported country codes."""
    return list(COUNTRY_CONFIGS.keys())


def get_country_name(country_code: str) -> str:
    """Get full country name from code."""
    try:
        config = get_country_config(country_code)
        return config.name
    except ValueError:
        return country_code  # fallback


def get_currency_info(country_code: str) -> Dict[str, str]:
    """Get currency information for a country."""
    config = get_country_config(country_code)
    return {
        "code": config.currency,
        "symbol": config.currency_symbol
    }


def get_special_instructions(country_code: str) -> Optional[str]:
    """
    Get special instructions for a country (if any).
    
    This is the key function that replaces hardcoded India logic!
    """
    config = get_country_config(country_code)
    return config.special_instructions


def get_balance_terminology(country_code: str) -> str:
    """
    Get the appropriate term for retirement balance in a country.
    
    Examples:
    - AU: "super balance"
    - US: "retirement balance"
    - UK: "pension pot"
    - IN: "retirement corpus"
    """
    config = get_country_config(country_code)
    return config.balance_term


# ============================================================================
# TEMPLATE FOR ADDING NEW COUNTRIES
# ============================================================================

"""
To add a new country (e.g., Canada):

1. Add to COUNTRY_CONFIGS:

COUNTRY_CONFIGS["CA"] = CountryConfig(
    code="CA",
    name="Canada",
    currency="CAD",
    currency_symbol="$",
    
    retirement_account_term="RRSP/RRIF",
    balance_term="retirement savings",
    
    authorities=[
        "Canada Revenue Agency (CRA)",
        "Office of the Superintendent of Financial Institutions (OSFI)"
    ],
    
    key_regulations=[
        "Income Tax Act (RRSP rules)",
        "Canada Pension Plan (CPP)",
        "Old Age Security (OAS)"
    ],
    
    regulatory_urls=[
        "https://www.canada.ca/en/services/benefits/publicpensions.html"
    ],
    
    advisor_title="Canadian Retirement Advisor",
    
    regulatory_context='''Follow Canadian retirement regulations including:
- RRSP contribution limits and withdrawal rules
- RRIF minimum withdrawal requirements
- CPP and OAS eligibility
- Tax implications under Income Tax Act
Discuss all monetary values in CAD.''',
    
    special_instructions=None,  # Add if needed
    
    greeting_style="neutral",
    available_tools=["tax", "benefit", "projection"]
)

2. Create UC functions in sql_ddls/:
   - ca_calculate_tax()
   - ca_check_pension_impact()
   - ca_project_retirement()

3. Add tool wrappers in tools.py (follow existing pattern)

4. That's it! No other files need editing.
"""


if __name__ == "__main__":
    print("=" * 70)
    print("COUNTRY CONFIGURATIONS")
    print("=" * 70)
    
    for code, config in COUNTRY_CONFIGS.items():
        print(f"\n{code} - {config.name}")
        print(f"  Currency: {config.currency_symbol}{config.currency}")
        print(f"  Term: {config.retirement_account_term}")
        print(f"  Balance: {config.balance_term}")
        print(f"  Authorities: {len(config.authorities)}")
        print(f"  Special Instructions: {'Yes' if config.special_instructions else 'No'}")
    
    print("\n" + "=" * 70)
    print(f"Total supported countries: {len(COUNTRY_CONFIGS)}")
    print("=" * 70)

