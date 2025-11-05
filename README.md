# Multi-Country Pension Advisor

**Maintainer:** [Pravin Varma](https://github.com/pravinva)

Enterprise-grade agentic AI reference implementation for pension advisory using Agent Framework, MLflow, and Unity Catalog.

## Overview

Demonstrates production-ready agentic AI patterns for Financial Services:
- Cost reduction (pennies vs. $150/hour advisors)
- Regulatory compliance with full audit trail
- Hyper-personalized member responses
- Multi-geography support (AU, US, UK, IN)

### Key Features

- **8-phase agentic pipeline** with Agent Framework orchestration
- **Privacy protection** via PII anonymization and restoration
- **Off-topic detection** using ai_classify SQL function
- **LLM-as-a-Judge validation** for response accuracy
- **Complete governance** with Unity Catalog audit trail
- **MLflow experiment tracking** for cost and performance metrics
- **Real-time cost transparency** per query

## Architecture

### 8-Phase Agent Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI (app.py)                    │
│  ┌────────────┬────────────┬────────────┬────────────┐      │
│  │ Australia  │    USA     │     UK     │   India    │      │
│  └────────────┴────────────┴────────────┴────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Agent Processor (agent_processor.py)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Phase 1: Profile Retrieval    (Unity Catalog)        │  │
│  │ Phase 2: Name Anonymization   (PII Protection)       │  │
│  │ Phase 3: Query Classification (ai_classify)          │  │
│  │ Phase 4: Tool Planning        (Claude Opus 4.1)      │  │
│  │ Phase 5: Tool Execution       (UC Functions)         │  │
│  │ Phase 6: Response Synthesis   (Claude Opus 4.1)      │  │
│  │ Phase 7: Validation           (LLM Judge)            │  │
│  │ Phase 8: Audit Logging        (MLflow + Governance)  │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Unity     │     │   Claude 4   │     │   MLflow    │
│  Catalog    │     │  Foundation  │     │ Experiment  │
│             │     │    Models    │     │  Tracking   │
│ • Functions │     │              │     │             │
│ • Tables    │     │ • Opus 4.1   │     │ • Traces    │
│ • Registry  │     │ • Sonnet 4   │     │ • Metrics   │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Technology Stack

- **Agent Framework**: Agent Bricks for tool orchestration
- **LLM Models**: Claude Opus 4.1 (planning/synthesis), Claude Sonnet 4 (validation)
- **Data Platform**: Databricks Unity Catalog
- **Experiment Tracking**: MLflow
- **UI Framework**: Streamlit
- **SQL Functions**: 18 country-specific calculators

## Quick Start

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- Access to Databricks Foundation Model API (Claude Opus 4.1 and Sonnet 4)
- SQL warehouse access
- Unity Catalog privileges (CREATE FUNCTION, SELECT on tables)
- Python 3.9+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pravinva/multi-country-pension-advisor.git
   cd multi-country-pension-advisor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Unity Catalog** (run in this order)
   ```sql
   -- Step 1: Create schema and tables
   -- Run: sql_ddls/super_advisory_demo_schema.sql
   
   -- Step 2: Create calculator functions
   -- Run: sql_ddls/super_advisory_demo_functions.sql
   ```

4. **Configure environment**
   
   Update `config.py` with your workspace settings:
   ```python
   CATALOG_NAME = "super_advisory_demo"
   SCHEMA_NAME = "pension_calculators"
   WAREHOUSE_ID = "your_warehouse_id"
   
   # Databricks-hosted Claude Foundation Model endpoints
   CLAUDE_OPUS_ENDPOINT = "databricks-claude-opus-4-1"
   CLAUDE_SONNET_ENDPOINT = "databricks-claude-sonnet-4"
   ```
   
   **Note**: No API keys needed - uses Databricks workspace authentication and Databricks-hosted Claude models.

5. **Run the application**
   ```bash
   # In Databricks workspace (recommended)
   streamlit run app.py
   
   # Or locally with Databricks CLI authentication
   databricks auth login
   streamlit run app.py
   ```
   
   **Authentication**: Uses Databricks workspace identity or CLI token - no separate API keys required.

## Unity Catalog Functions

### 18 Country-Specific Calculators

The system uses specialized SQL functions stored in Unity Catalog for country-specific pension calculations.

#### Australia (3 functions)
- `au_calculate_tax` - Superannuation withdrawal tax based on preservation age rules (ATO Division 301)
- `au_check_pension_impact` - Age Pension eligibility and asset test calculations (Social Security Act 1991)
- `au_project_balance` - Future superannuation balance projections (ASFA/APRA standards)

#### USA (6 functions)
- `us_calculate_tax` - General retirement account taxation
- `us_calculate_401k_tax` - 401(k) early withdrawal penalties (IRC Section 401(k))
- `us_check_social_security` - Social Security benefit estimation (SSA rules)
- `us_project_401k` - 401(k) balance projection
- `us_project_401k_balance` - Detailed 401(k) growth with RMD considerations
- `us_project_retirement_balance` - Comprehensive retirement account projections (SECURE 2.0 Act)

#### United Kingdom (3 functions)
- `uk_calculate_pension_tax` - Pension withdrawal tax including 25% tax-free lump sum (Finance Act 2004)
- `uk_check_state_pension` - State Pension eligibility based on NI contributions (Pensions Act 2014)
- `uk_project_pension_balance` - Pension drawdown and balance projections

#### India (6 functions)
- `in_calculate_epf_tax` - EPF withdrawal tax calculations (Section 10(12) exemptions)
- `in_calculate_eps_benefits` - Employee Pension Scheme benefits (Pension = Salary × Service / 70)
- `in_calculate_nps` - National Pension System calculations
- `in_calculate_nps_benefits` - NPS annuity and lump sum calculations (PFRDA Act 2013)
- `in_project_retirement` - General retirement corpus projection
- `in_project_retirement_corpus` - Detailed EPF interest rate projections (EPF Act 1952)

**Note**: India system automatically splits member balances 75% EPF / 25% NPS for accurate calculations.

### Function Structure

All Unity Catalog functions follow this pattern:

```sql
CREATE FUNCTION super_advisory_demo.pension_calculators.{country}_{operation}(
    member_id STRING,
    current_balance DOUBLE,
    age INT,
    withdrawal_amount DOUBLE
) RETURNS STRUCT<...>
```

## Key Capabilities

### Off-Topic Detection with ai_classify

The system uses Databricks `ai_classify` SQL function to filter non-retirement queries:

```sql
SELECT ai_classify(
    'What is my superannuation balance?',
    ARRAY('retirement_planning', 'general_question', 'off_topic')
) as topic;
```

Queries classified as `off_topic` are politely redirected without consuming LLM resources.

### Privacy Protection

**Name Anonymization Pipeline**:
1. Extract member name from Unity Catalog profile
2. Replace with token (e.g., `[MEMBER_NAME_1]`) during LLM processing
3. Restore real name in final response for personalization
4. Log only anonymized versions to MLflow

This ensures PII protection while maintaining conversational quality.

### LLM Judge Validation

Every response is validated against regulatory standards:

```python
# LLM Judge evaluates:
- Regulatory accuracy (country-specific laws cited correctly)
- Safety (no harmful financial advice)
- Completeness (all query aspects addressed)
- Citation quality (proper regulatory references)

# Returns:
{
    "verdict": "APPROVED",
    "confidence": 0.95,
    "issues": []
}
```

**Validation Modes**:
- **LLM Judge**: Comprehensive semantic validation (Claude Sonnet 4)
- **Deterministic**: Fast rule-based checks for critical violations
- **Hybrid**: Deterministic first, LLM fallback for edge cases

### Governance & Audit Trail

Every query is logged to `super_advisory_demo.member_data.governance`:

```sql
CREATE TABLE governance (
    event_id STRING,
    timestamp TIMESTAMP,
    user_id STRING,
    session_id STRING,
    country STRING,
    query_string STRING,
    agent_response STRING,
    cost DOUBLE,
    citations STRING,
    judge_verdict STRING,
    judge_confidence DOUBLE,
    validation_mode STRING,
    total_time_seconds DOUBLE
);
```

**Regulatory References** stored in `citation_registry`:

```sql
SELECT citation_id, authority, regulation_name, source_url
FROM super_advisory_demo.member_data.citation_registry
WHERE country = 'AU';

-- Example results:
-- AU-TAX-001    | Australian Taxation Office | Income Tax Assessment Act 1997
-- AU-PENSION-001| Dept of Social Services    | Social Security Act 1991
```

## Cost Analysis

### Pricing Model

```python
# From config.py
LLM_PRICING = {
    "claude-opus-4-1": {
        "input_tokens": 15.00,   # $15 per 1M tokens
        "output_tokens": 75.00   # $75 per 1M tokens
    },
    "claude-sonnet-4": {
        "input_tokens": 3.00,    # $3 per 1M tokens
        "output_tokens": 15.00   # $15 per 1M tokens
    }
}
```

### Typical Query Cost

| Operation | Model | Tokens | Cost |
|-----------|-------|--------|------|
| Planning & Synthesis | Opus 4.1 | ~2,000 | $0.0029 |
| Validation | Sonnet 4 | ~500 | $0.0004 |
| **Total per Query** | - | - | **~$0.003** |

**Cost Comparison**:
- Traditional financial advisor: $150-300/hour
- This system: $0.003/query (~50,000 queries = $150)

### Real-Time Cost Display

Each response shows:
```
Total Cost: $0.003245
├─ Main LLM (Opus 4.1): $0.002891
└─ Judge LLM (Sonnet 4): $0.000354
```

## Development

### Project Structure

```
multi-country-pension-advisor/
│
├── app.py                   # Streamlit UI application
├── app.yaml                 # Databricks app configuration
├── requirements.txt         # Python dependencies
│
├── agent.py                 # SuperAdvisorAgent (8-phase pipeline)
├── agent_processor.py       # Agent orchestration & MLflow
├── tools.py                 # Unity Catalog function wrappers
├── validation.py            # LLM Judge & Deterministic validators
│
├── config.py                # Configuration (endpoints, pricing, catalog)
├── data_utils.py            # Unity Catalog data access
├── progress_utils.py        # Real-time pipeline progress tracking
├── ui_components.py         # Streamlit UI components
│
├── audit/
│   └── audit_utils.py       # Governance logging
│
├── country_content/
│   ├── disclaimers.py       # Country-specific legal disclaimers
│   ├── prompts.py           # Welcome messages per country
│   └── regulations.py       # Regulatory reference links
│
├── prompts/
│   └── country_prompts.py   # Country-specific advisor personas
│
├── sql_ddls/
│   ├── super_advisory_demo_schema.sql      # Run FIRST
│   └── super_advisory_demo_functions.sql   # Run SECOND
│
└── README.md
```

### Adding a New Country

1. **Create 3 UC functions** in `sql_ddls/super_advisory_demo_functions.sql`:
   ```sql
   CREATE FUNCTION {country}_calculate_tax(...) RETURNS STRUCT<...>;
   CREATE FUNCTION {country}_check_benefit(...) RETURNS STRUCT<...>;
   CREATE FUNCTION {country}_project_balance(...) RETURNS STRUCT<...>;
   ```

2. **Add tool wrapper** in `tools.py`:
   ```python
   def _call_{country}_tool(tool_id, member_id, profile, withdrawal, warehouse_id):
       # Implementation
   ```

3. **Add country content** in `country_content/`:
   - `prompts.py` - Welcome message
   - `disclaimers.py` - Legal disclaimers
   - `regulations.py` - Regulatory references

4. **Update config** in `config.py`:
   ```python
   COUNTRY_CODES = ['AU', 'US', 'UK', 'IN', 'NEW_COUNTRY']
   ```

### Testing

```bash
# Single query test
python -c "
from agent_processor import agent_query
result = agent_query(
    user_id='TEST001',
    session_id='test-session',
    country='AU',
    query_string='Can I access my super at age 55?',
    validation_mode='llm_judge'
)
print(result)
"
```

### Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Key debug points:
- Tool execution in `tools.py`
- Validation logic in `validation.py`
- Agent phases in `agent_processor.py`

## Usage Examples

### Australia
```
Query: "What's the maximum I can withdraw from my super this year?"
Functions Used: au_calculate_tax, au_check_pension_impact
Regulatory Citations: ATO Division 301, Social Security Act 1991
```

### USA
```
Query: "What are my required minimum distributions at age 73?"
Functions Used: us_calculate_401k_tax, us_project_retirement_balance
Regulatory Citations: IRC Section 401(a)(9), SECURE 2.0 Act
```

### United Kingdom
```
Query: "How much of my pension can I take tax-free?"
Functions Used: uk_calculate_pension_tax
Regulatory Citations: Finance Act 2004 Section 164
```

### India
```
Query: "Can I withdraw my EPF for housing?"
Functions Used: in_calculate_epf_tax, in_project_retirement_corpus
Regulatory Citations: EPF Act 1952 Section 68B
```

## License

MIT License

Copyright (c) 2025 Pravin Varma

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Contributing

Issues and pull requests welcome! Please open an issue first to discuss proposed changes.

Maintained by [@pravinva](https://github.com/pravinva)

## Maintainer

**Pravin Varma**  
GitHub: [@pravinva](https://github.com/pravinva)

Questions? Open an issue or reach out via GitHub.

---

Built with Databricks Platform | MIT License
