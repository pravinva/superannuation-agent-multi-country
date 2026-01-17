# Adding New Countries: Configuration Guide

## Overview

The system uses a country-agnostic architecture where all country-specific logic is centralized in `country_config.py`. Adding a new country requires only configuration changes, no code modifications to the agent logic.

## Architecture

Country-specific data is stored in `CountryConfig` dataclass instances:

```python
@dataclass
class CountryConfig:
    code: str                          # "AU", "US", "UK", "IN"
    name: str                          # "Australia"
    currency: str                      # "AUD"
    currency_symbol: str               # "$"
    retirement_account_term: str       # "superannuation"
    balance_term: str                  # "super balance"
    authorities: List[str]             # Regulatory bodies
    key_regulations: List[str]         # Key regulations
    regulatory_urls: List[str]         # Reference URLs
    advisor_title: str                 # Advisor title
    regulatory_context: str            # Regulatory instructions
    special_instructions: Optional[str] # Country-specific notes
    greeting_style: str                # "formal", "casual", "neutral"
    available_tools: List[str]         # Available tools
```

## Step-by-Step Process

### Step 1: Add Country Configuration

Edit `country_config.py` and add a new entry to `COUNTRY_CONFIGS`:

```python
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
    
    regulatory_context="""Follow Canadian retirement regulations including:
- RRSP contribution limits and withdrawal rules
- RRIF minimum withdrawal requirements
- CPP and OAS eligibility
- Tax implications under Income Tax Act
Discuss all monetary values in CAD.""",
    
    special_instructions=None,  # Add if needed
    
    greeting_style="neutral",
    available_tools=["tax", "benefit", "projection"]
)
```

### Step 2: Create Unity Catalog SQL Functions

Create SQL functions in Unity Catalog for country-specific calculations. These should follow the naming convention: `{COUNTRY_CODE}_{function_name}`.

**Example for Canada:**

```sql
CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.CA_calculate_tax(
    member_id STRING,
    withdrawal_amount DOUBLE,
    age INT
) RETURNS STRUCT<
    tax_amount DOUBLE,
    net_amount DOUBLE,
    marginal_rate DOUBLE,
    authority STRING
> AS $$
    -- Implementation here
    RETURN STRUCT(
        tax_amount AS DOUBLE,
        net_amount AS DOUBLE,
        marginal_rate AS DOUBLE,
        'Canada Revenue Agency (CRA)' AS authority
    )
$$;

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.CA_check_pension_impact(
    member_id STRING,
    withdrawal_amount DOUBLE
) RETURNS STRUCT<
    impact_type STRING,
    impact_amount DOUBLE,
    authority STRING
> AS $$
    -- Implementation here
$$;

CREATE OR REPLACE FUNCTION super_advisory_demo.pension_calculators.CA_project_retirement(
    member_id STRING,
    years INT,
    contribution_rate DOUBLE
) RETURNS STRUCT<
    projected_balance DOUBLE,
    growth_rate DOUBLE,
    authority STRING
> AS $$
    -- Implementation here
$$;
```

**Function Requirements:**

1. **Input Parameters:** Standardized inputs (member_id, withdrawal_amount, age, etc.)
2. **Return Structure:** Consistent return format with `authority` field
3. **Naming:** Must start with country code (e.g., `CA_`)
4. **Schema:** Located in `super_advisory_demo.pension_calculators` schema

### Step 3: Add Tool Wrappers

Add tool wrapper functions in `tools.py`:

```python
def _call_ca_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id):
    """
    Call Canadian retirement calculation tool.
    
    Args:
        tool_id: Tool identifier ('tax', 'benefit', 'projection')
        member_id: Member identifier
        profile: Member profile dictionary
        withdrawal_amount: Optional withdrawal amount
        warehouse_id: SQL warehouse ID
        
    Returns:
        Tool result dictionary
    """
    from utils.lakehouse import execute_sql_query
    from config import SQL_WAREHOUSE_ID
    
    wh_id = warehouse_id or SQL_WAREHOUSE_ID
    country_code = "CA"
    
    if tool_id == "tax":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.CA_calculate_tax(
            '{member_id}',
            {withdrawal_amount or 0.0},
            {profile.get('age', 65)}
        ) as result
        """
    elif tool_id == "benefit":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.CA_check_pension_impact(
            '{member_id}',
            {withdrawal_amount or 0.0}
        ) as result
        """
    elif tool_id == "projection":
        query = f"""
        SELECT super_advisory_demo.pension_calculators.CA_project_retirement(
            '{member_id}',
            10,
            0.10
        ) as result
        """
    else:
        return {"error": f"Unknown tool: {tool_id}"}
    
    try:
        df = execute_sql_query(query, warehouse_id=wh_id)
        if df.empty:
            return {"error": "No result from tool"}
        
        result = df.iloc[0]['result']
        return {
            "tool": f"{country_code}_{tool_id}",
            "result": result,
            "authority": result.get('authority', 'Unknown')
        }
    except Exception as e:
        return {"error": str(e)}
```

### Step 4: Update Tool Router

Update `call_tool()` function in `tools.py` to route to new country:

```python
def call_tool(country_code, tool_id, member_id, profile, withdrawal_amount=None, warehouse_id=None):
    """Route tool call to country-specific implementation."""
    if country_code == "CA":
        return _call_ca_tool(tool_id, member_id, profile, withdrawal_amount, warehouse_id)
    # ... existing country handlers
```

### Step 5: Add Member Data

Add sample member profiles to Unity Catalog `member_profiles` table:

```sql
INSERT INTO super_advisory_demo.member_data.member_profiles VALUES
('ca_member_001', 'CA', 'John', 'Doe', 55, 500000.00, '2024-01-01');
```

## Special Instructions

If the country has unique requirements (like India's balance split), add them to `special_instructions`:

```python
special_instructions="""CRITICAL FOR CANADA MEMBERS:
When discussing RRSP withdrawals:
- Withdrawals are taxable as income
- 10% withholding tax applies to withdrawals over $5,000
- CPP benefits may be affected by large withdrawals
Always reference CRA guidelines for specific scenarios."""
```

These instructions are automatically included in the system prompt via `prompts_registry.py`.

## Testing

### Unit Test Country Config

```python
from country_config import get_country_config, get_currency_info

config = get_country_config("CA")
assert config.name == "Canada"
assert config.currency == "CAD"

currency = get_currency_info("CA")
assert currency["code"] == "CAD"
```

### Test Tool Execution

```python
from tools import call_tool

profile = {"age": 55, "balance": 500000.0}
result = call_tool("CA", "tax", "test_member", profile, withdrawal_amount=10000.0)
assert "result" in result
assert "authority" in result["result"]
```

### End-to-End Test

Run a query through the agent:

```python
from agent_processor import agent_query

result = agent_query(
    user_id="ca_member_001",
    session_id="test_session",
    country="CA",
    query_string="How much tax will I pay on a $10,000 RRSP withdrawal?"
)

assert result["answer"] is not None
assert result["tools_called"] == ["tax"]
```

## Authority Mapping

The `get_authority()` function maps tool types to regulatory authorities:

```python
def get_authority(country_code: str, tool_type: str) -> str:
    config = get_country_config(country_code)
    tool_to_authority_map = {
        "tax": 0,          # First authority in list
        "benefit": 1,      # Second authority in list
        "projection": 2,   # Third authority in list
        "eps_benefit": 1   # Special case for India
    }
    authority_index = tool_to_authority_map.get(tool_type, 0)
    return config.authorities[authority_index]
```

Ensure the country's `authorities` list order matches the tool type mapping.

## Utility Functions

Country configuration is accessed via utility functions:

- `get_country_config(country_code)`: Returns full CountryConfig
- `get_currency_info(country_code)`: Returns currency code and symbol
- `get_special_instructions(country_code)`: Returns special instructions if any
- `get_balance_terminology(country_code)`: Returns country-specific balance term
- `get_authority(country_code, tool_type)`: Returns regulatory authority for tool

These are used throughout the codebase to ensure consistent country-specific behavior.

## Validation Checklist

Before deploying a new country:

1. Country configuration added to `COUNTRY_CONFIGS`
2. SQL functions created in Unity Catalog
3. Tool wrappers added to `tools.py`
4. Tool router updated
5. Sample member data added
6. Special instructions documented (if any)
7. Authority mapping verified
8. Unit tests written
9. End-to-end test passes
10. Documentation updated

## Common Patterns

### Currency Formatting

Currency formatting is handled automatically via `utils/formatting.py`:

```python
from utils.formatting import format_currency_amount

amount = format_currency_amount(1000.50, "CA")  # Returns "$1,000.50"
```

### Regulatory Citations

Citations are automatically formatted with country-specific authorities:

```python
from country_config import get_authority

authority = get_authority("CA", "tax")  # Returns "Canada Revenue Agency (CRA)"
```

### Prompt Integration

Country-specific prompts are automatically generated:

```python
from prompts_registry import PromptsRegistry

registry = PromptsRegistry()
system_prompt = registry.get_system_prompt(country="Canada")
# Includes regulatory_context, special_instructions, currency, etc.
```

## Maintenance

When updating country configurations:

1. Modify `CountryConfig` in `country_config.py`
2. Update SQL functions if regulations change
3. Update special instructions if needed
4. Test thoroughly before deployment
5. Document changes in release notes

No code changes are required in `agent.py`, `react_loop.py`, or other core components.

