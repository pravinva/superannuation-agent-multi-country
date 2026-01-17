# Databricks notebook source
# MAGIC %md
# MAGIC # Multi-Country Agent Architecture Overview
# MAGIC
# MAGIC This notebook provides an overview of the retirement advisory agent architecture
# MAGIC and how it handles multi-country queries with LLM orchestration.
# MAGIC
# MAGIC **Agent Architecture:**
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────┐
# MAGIC │                    User Query                               │
# MAGIC └────────────────────┬────────────────────────────────────────┘
# MAGIC                      │
# MAGIC                      ▼
# MAGIC         ┌────────────────────────┐
# MAGIC         │   Query Classifier     │ ← LLM (GPT-oss-120B)
# MAGIC         │  - Determines intent   │
# MAGIC         │  - Identifies tools    │
# MAGIC         └────────┬───────────────┘
# MAGIC                  │
# MAGIC                  ▼
# MAGIC         ┌────────────────────────┐
# MAGIC         │   Agent Orchestrator   │ ← LLM (Claude Opus)
# MAGIC         │  - Manages flow        │
# MAGIC         │  - Calls tools         │
# MAGIC         └────────┬───────────────┘
# MAGIC                  │
# MAGIC     ┌────────────┼────────────┐
# MAGIC     ▼            ▼            ▼
# MAGIC ┌────────┐  ┌────────┐  ┌────────┐
# MAGIC │UC Tool │  │UC Tool │  │UC Tool │
# MAGIC │ Tax    │  │Balance │  │Project │
# MAGIC └────┬───┘  └────┬───┘  └────┬───┘
# MAGIC      └───────────┼───────────┘
# MAGIC                  ▼
# MAGIC         ┌────────────────────────┐
# MAGIC         │  Response Builder      │
# MAGIC         │  - Formats response    │
# MAGIC         │  - Adds citations      │
# MAGIC         └────────┬───────────────┘
# MAGIC                  │
# MAGIC                  ▼
# MAGIC         ┌────────────────────────┐
# MAGIC         │   LLM-as-a-Judge       │ ← LLM (Claude Sonnet)
# MAGIC         │  - Validates response  │
# MAGIC         │  - Quality check       │
# MAGIC         └────────┬───────────────┘
# MAGIC                  │
# MAGIC                  ▼
# MAGIC         ┌────────────────────────┐
# MAGIC         │  Validated Response    │
# MAGIC         └────────────────────────┘
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Agent Components

# COMMAND ----------

import sys
sys.path.append('..')

# Show the agent modules
from agents import orchestrator, context_formatter, response_builder

print("Agent Framework Modules:")
print(f"  ✓ Orchestrator: {orchestrator.__file__}")
print(f"  ✓ Context Formatter: {context_formatter.__file__}")
print(f"  ✓ Response Builder: {response_builder.__file__}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Multi-Country Support

# COMMAND ----------

from country_config import COUNTRY_CONFIGS

import pandas as pd

# Show country configurations
configs = []
for code, config in COUNTRY_CONFIGS.items():
    configs.append({
        'Code': code,
        'Country': config.name,
        'Currency': f"{config.currency_symbol} {config.currency}",
        'Account Type': config.retirement_account_term,
        'Balance Term': config.balance_term
    })

config_df = pd.DataFrame(configs)
display(config_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## LLM Configuration
# MAGIC
# MAGIC The agent uses 3 different LLMs for different purposes

# COMMAND ----------

from config import MAIN_LLM_ENDPOINT, JUDGE_LLM_ENDPOINT, CLASSIFIER_LLM_ENDPOINT

llm_config = pd.DataFrame([
    {
        'Purpose': 'Main Agent',
        'Model': MAIN_LLM_ENDPOINT,
        'Use Case': 'Response synthesis, reasoning, tool orchestration',
        'Temperature': 0.2
    },
    {
        'Purpose': 'Validation',
        'Model': JUDGE_LLM_ENDPOINT,
        'Use Case': 'Response quality validation (LLM-as-a-Judge)',
        'Temperature': 0.1
    },
    {
        'Purpose': 'Classification',
        'Model': CLASSIFIER_LLM_ENDPOINT,
        'Use Case': 'Query classification (Stage 3 fallback)',
        'Temperature': 0.0
    }
])

display(llm_config)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tool Integration
# MAGIC
# MAGIC The agent can call Unity Catalog functions as tools

# COMMAND ----------

from tools import AVAILABLE_TOOLS

# Show available tools
tools_data = []
for tool_name, tool_config in AVAILABLE_TOOLS.items():
    tools_data.append({
        'Tool Name': tool_name,
        'Countries': ', '.join(tool_config.get('countries', [])),
        'Description': tool_config.get('description', '')[:60] + '...'
    })

tools_df = pd.DataFrame(tools_data)
display(tools_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query Flow Example

# COMMAND ----------

# Example query flow
query = "How much tax will I pay if I withdraw $50,000 from my super?"
country = "AU"
member_id = "AU001"

print(f"Query: {query}")
print(f"Country: {country}")
print(f"Member: {member_id}\n")

print("Flow:")
print("1. Classifier identifies this as a 'tax_questions' query")
print("2. Orchestrator determines tool needed: calculate_tax")
print("3. Tool executor calls: au_calculate_tax(member_id, 50000, age)")
print("4. Response builder formats result with citations")
print("5. Validator checks response quality")
print("6. User receives validated, country-specific response")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Processing Pipeline

# COMMAND ----------

from agents.orchestrator import AgentOrchestrator

# Show orchestrator flow
orchestrator = AgentOrchestrator()

print("Orchestrator Pipeline:")
print("  1. build_context() - Prepare query context")
print("  2. classify_query() - Determine query type")
print("  3. execute_tools() - Run required calculations")
print("  4. build_response() - Synthesize response")
print("  5. validate_response() - Quality check")
print("  6. log_to_governance() - Audit log")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitoring & Observability

# COMMAND ----------

from monitoring import get_agent_metrics

# Show tracked metrics
metrics = [
    "Query latency",
    "Tool execution time",
    "LLM token usage",
    "Cost per query",
    "Validation pass rate",
    "Tool success rate"
]

print("Tracked Metrics:")
for metric in metrics:
    print(f"  ✓ {metric}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Agent Overview Complete
# MAGIC
# MAGIC You've learned about:
# MAGIC - Agent architecture and flow
# MAGIC - Multi-country support
# MAGIC - LLM configuration
# MAGIC - Tool integration
# MAGIC - Processing pipeline
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - **02-build-agent**: See the agent in action
# MAGIC - **03-tool-integration**: Deep dive into tool calling
# MAGIC - **04-validation**: Learn about response validation

# COMMAND ----------

print("✅ Agent architecture overview complete!")
