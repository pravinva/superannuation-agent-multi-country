# Databricks notebook source
# MAGIC %md
# MAGIC # Build Multi-Country Retirement Advisory Agent
# MAGIC
# MAGIC This notebook demonstrates how to use the production agent framework to build
# MAGIC a multi-country retirement advisory agent with:
# MAGIC - LLM-based query classification
# MAGIC - Tool calling for retirement calculations
# MAGIC - Country-specific responses
# MAGIC - Validation and quality checks
# MAGIC
# MAGIC **Agent Architecture:**
# MAGIC ```
# MAGIC User Query → Classifier → Orchestrator → Tools → Response Builder → Validated Response
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Production Modules
# MAGIC
# MAGIC Import from root-level production code

# COMMAND ----------

import sys
sys.path.append('..')  # Add parent to import from root

# Import agent components
from agent_processor import agent_query
from classifier import classify_query
from agent import AgentOrchestrator
from config import MAIN_LLM_ENDPOINT, UNITY_CATALOG, UNITY_SCHEMA
from country_config import get_country_config, get_currency_symbol

print("✓ Agent modules imported")
print(f"  LLM Endpoint: {MAIN_LLM_ENDPOINT}")
print(f"  Unity Catalog: {UNITY_CATALOG}.{UNITY_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Query Classification
# MAGIC
# MAGIC The classifier determines query type and whether tools are needed

# COMMAND ----------

# Example query
query = "I'm 62 years old and want to know when I can access my super without penalties"
country = "AU"
member_id = "AU001"

print(f"Query: {query}")
print(f"Country: {country}")
print(f"Member: {member_id}\n")

# Classify the query
classification = classify_query(query, country, member_id)

print("Classification result:")
print(f"  Type: {classification.get('type', 'Unknown')}")
print(f"  Requires tools: {classification.get('requires_tools', False)}")
print(f"  Confidence: {classification.get('confidence', 0.0):.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Execute Agent Query
# MAGIC
# MAGIC Use the agent processor to handle the query end-to-end

# COMMAND ----------

# Execute full agent query
result = agent_query(
    query=query,
    member_id=member_id,
    country=country
)

print("Agent Response:")
print(f"{result['response']}\n")

print("Metadata:")
print(f"  Tools used: {result.get('tools_used', [])}")
print(f"  Processing time: {result.get('processing_time', 0):.2f}s")
print(f"  Cost: ${result.get('cost', 0):.6f}")
print(f"  Validation: {result.get('validation_status', 'N/A')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Multi-Country Support
# MAGIC
# MAGIC Test the agent with different countries

# COMMAND ----------

# Test queries for different countries
test_cases = [
    {
        "query": "How much tax will I pay on my retirement withdrawal?",
        "country": "AU",
        "member_id": "AU004"
    },
    {
        "query": "When can I start taking distributions from my 401(k)?",
        "country": "US",
        "member_id": "US001"
    },
    {
        "query": "What is my State Pension age?",
        "country": "UK",
        "member_id": "UK001"
    },
    {
        "query": "Can I withdraw from my EPF before age 58?",
        "country": "IN",
        "member_id": "IN001"
    }
]

# Run all test cases
for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*70}")
    print(f"Test Case {i}: {test['country']}")
    print(f"{'='*70}")
    print(f"Query: {test['query']}")
    print(f"Member: {test['member_id']}\n")

    result = agent_query(
        query=test['query'],
        member_id=test['member_id'],
        country=test['country']
    )

    currency = get_currency_symbol(test['country'])
    print(f"Response ({currency}):")
    print(f"{result['response'][:300]}...")  # Truncate for display
    print(f"\nTools used: {result.get('tools_used', [])}")
    print(f"Cost: ${result.get('cost', 0):.6f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Tool Integration
# MAGIC
# MAGIC The agent can call Unity Catalog functions as tools

# COMMAND ----------

# Example: Tax calculation tool
from tools import execute_tool

# Tool call example
tool_result = execute_tool(
    tool_name="calculate_tax",
    parameters={
        "country": "AU",
        "member_id": "AU004",
        "withdrawal_amount": 50000,
        "age": 65
    }
)

print("Tool Result:")
print(tool_result)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Response Validation
# MAGIC
# MAGIC All responses go through LLM-as-a-Judge validation

# COMMAND ----------

from validation import validate_response

# Validate a response
validation_result = validate_response(
    query=query,
    response=result['response'],
    country=country,
    member_id=member_id
)

print("Validation Result:")
print(f"  Verdict: {validation_result['verdict']}")
print(f"  Confidence: {validation_result.get('confidence', 0):.2f}")
print(f"  Feedback: {validation_result.get('feedback', 'N/A')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Country-Specific Configuration
# MAGIC
# MAGIC Each country has specific regulations and terminology

# COMMAND ----------

import pandas as pd

# Show country configurations
countries = ['AU', 'US', 'UK', 'IN']
config_data = []

for country_code in countries:
    config = get_country_config(country_code)
    config_data.append({
        'Country': config.name,
        'Currency': f"{config.currency_symbol} {config.currency}",
        'Retirement Account': config.retirement_account_term,
        'Balance Term': config.balance_term,
        'Preservation Age Term': config.preservation_age_term
    })

config_df = pd.DataFrame(config_data)
display(config_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Complete Example: Interactive Query

# COMMAND ----------

# Interactive query example
def ask_agent(query_text, country_code, member_id):
    """Helper function to query the agent"""
    print(f"\n{'='*70}")
    print(f"QUERY ({country_code})")
    print(f"{'='*70}")
    print(f"{query_text}\n")

    result = agent_query(
        query=query_text,
        member_id=member_id,
        country=country_code
    )

    print("RESPONSE:")
    print(f"{result['response']}\n")

    if result.get('citations'):
        print("CITATIONS:")
        for citation in result['citations']:
            print(f"  - {citation}")

    print(f"\nProcessing time: {result.get('processing_time', 0):.2f}s")
    print(f"Cost: ${result.get('cost', 0):.6f}")

    return result

# Example usage
result = ask_agent(
    query_text="I want to retire early. What are my options and tax implications?",
    country_code="AU",
    member_id="AU015"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Agent Demo Complete
# MAGIC
# MAGIC You've seen how the production agent handles:
# MAGIC - Multi-country queries
# MAGIC - Tool integration
# MAGIC - Response validation
# MAGIC - Country-specific configurations
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - **03-tool-integration**: Deep dive into Unity Catalog function tools
# MAGIC - **04-validation**: LLM-as-a-Judge validation details
# MAGIC - **03-monitoring-demo/01-mlflow-tracking**: Track agent performance

# COMMAND ----------

print("✅ Agent demo complete!")
print("   Multi-country support: AU, US, UK, IN")
print("   Tool calling: Unity Catalog functions")
print("   Validation: LLM-as-a-Judge")
print("   Ready for production use")
