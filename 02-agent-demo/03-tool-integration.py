# Databricks notebook source
# MAGIC %md
# MAGIC # Tool Integration Deep Dive
# MAGIC
# MAGIC This notebook explores how the agent integrates with Unity Catalog functions
# MAGIC as tools for retirement calculations.
# MAGIC
# MAGIC **Topics Covered:**
# MAGIC - Tool configuration
# MAGIC - Tool executor implementation
# MAGIC - UC function calling
# MAGIC - Error handling
# MAGIC - Result formatting

# COMMAND ----------

import sys
sys.path.append('..')

from tools.tool_executor import ToolExecutor
from tools import AVAILABLE_TOOLS
import pandas as pd

print("✓ Tool modules imported")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Available Tools

# COMMAND ----------

# Display all available tools
tools_data = []
for tool_name, tool_config in AVAILABLE_TOOLS.items():
    tools_data.append({
        'Tool': tool_name,
        'Countries': ', '.join(tool_config.get('countries', [])),
        'UC Function': tool_config.get('uc_function', ''),
        'Description': tool_config.get('description', '')[:80] + '...'
    })

tools_df = pd.DataFrame(tools_data)
display(tools_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tool Configuration
# MAGIC
# MAGIC Tools are defined in `tools/tool_config.yaml`

# COMMAND ----------

import yaml

with open('../tools/tool_config.yaml', 'r') as f:
    tool_config = yaml.safe_load(f)

print("Tool Configuration Structure:")
print(f"  Total tools: {len(tool_config.get('tools', []))}")

# Show one example
example_tool = tool_config['tools'][0]
print(f"\nExample Tool: {example_tool['name']}")
print(f"  UC Function: {example_tool['uc_function']}")
print(f"  Parameters: {example_tool['parameters']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tool Executor

# COMMAND ----------

# Create tool executor instance
executor = ToolExecutor()

print(f"Tool Executor initialized")
print(f"  Available tools: {len(executor.tools)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute a Tool
# MAGIC
# MAGIC Call a UC function via the tool executor

# COMMAND ----------

# Example: Calculate tax for Australian member
result = executor.execute_tool(
    tool_name="calculate_tax",
    parameters={
        "country": "AU",
        "member_id": "AU004",
        "withdrawal_amount": 50000,
        "age": 65
    }
)

print("Tool Execution Result:")
print(f"  Success: {result['success']}")
print(f"  Tool: {result['tool']}")
print(f"  Duration: {result['duration']:.3f}s")
print(f"\nResult:")
print(result['result'])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Multi-Country Tool Execution

# COMMAND ----------

# Test tools across all countries
test_cases = [
    {
        "tool": "check_balance",
        "country": "AU",
        "member_id": "AU001",
        "description": "AU Balance Check"
    },
    {
        "tool": "calculate_tax",
        "country": "US",
        "member_id": "US001",
        "description": "US Tax Calculation",
        "withdrawal_amount": 30000,
        "age": 68
    },
    {
        "tool": "check_preservation_age",
        "country": "UK",
        "member_id": "UK001",
        "description": "UK Preservation Age"
    },
    {
        "tool": "check_balance",
        "country": "IN",
        "member_id": "IN001",
        "description": "IN Balance Check"
    }
]

# Execute all test cases
results = []
for test in test_cases:
    params = {k: v for k, v in test.items() if k not in ['tool', 'description']}

    result = executor.execute_tool(
        tool_name=test['tool'],
        parameters=params
    )

    results.append({
        'Test': test['description'],
        'Tool': test['tool'],
        'Success': result['success'],
        'Duration': f"{result['duration']:.3f}s",
        'Result Preview': str(result.get('result', ''))[:50] + '...'
    })

results_df = pd.DataFrame(results)
display(results_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Error Handling

# COMMAND ----------

# Test error handling with invalid parameters
error_result = executor.execute_tool(
    tool_name="calculate_tax",
    parameters={
        "country": "AU",
        "member_id": "INVALID_ID",  # Invalid member
        "withdrawal_amount": 50000,
        "age": 65
    }
)

print("Error Handling:")
print(f"  Success: {error_result['success']}")
if not error_result['success']:
    print(f"  Error: {error_result.get('error', 'Unknown error')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tool Result Formatting

# COMMAND ----------

from agents.response_builder import ResponseBuilder

# Create response builder
builder = ResponseBuilder()

# Format tool results for LLM consumption
tool_results = [
    {
        "tool": "check_balance",
        "result": {"super_balance": 450000, "currency": "AUD"},
        "success": True
    },
    {
        "tool": "calculate_tax",
        "result": {"tax_amount": 5250, "tax_rate": 0.15, "currency": "AUD"},
        "success": True
    }
]

formatted = builder.format_tool_results(tool_results)
print("Formatted Tool Results for LLM:")
print(formatted)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tool Calling Flow

# COMMAND ----------

# Demonstrate the full tool calling flow
def demonstrate_tool_flow(query, country, member_id):
    """Show the complete tool calling flow"""

    print(f"Query: {query}")
    print(f"Country: {country}, Member: {member_id}\n")

    # 1. Classifier determines tools needed
    print("1. Classifier: Identifies required tools")
    required_tools = ["check_balance", "calculate_tax"]
    print(f"   Tools needed: {required_tools}\n")

    # 2. Execute tools
    print("2. Tool Executor: Calls UC functions")
    results = []
    for tool in required_tools:
        if tool == "check_balance":
            result = executor.execute_tool(tool, {"country": country, "member_id": member_id})
        elif tool == "calculate_tax":
            result = executor.execute_tool(tool, {
                "country": country,
                "member_id": member_id,
                "withdrawal_amount": 50000,
                "age": 65
            })
        results.append(result)
        print(f"   ✓ {tool}: {result['duration']:.3f}s")

    print("\n3. Response Builder: Formats results")
    print("   Creates natural language response with tool data\n")

    return results

# Run demonstration
demo_results = demonstrate_tool_flow(
    "How much tax will I pay on a $50,000 withdrawal?",
    "AU",
    "AU004"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tool Performance Metrics

# COMMAND ----------

# Analyze tool performance
import time

# Benchmark tool execution
benchmark_results = []

for i in range(5):
    start = time.time()

    result = executor.execute_tool(
        "check_balance",
        {"country": "AU", "member_id": "AU001"}
    )

    duration = time.time() - start
    benchmark_results.append(duration)

avg_duration = sum(benchmark_results) / len(benchmark_results)
min_duration = min(benchmark_results)
max_duration = max(benchmark_results)

print(f"Tool Performance (check_balance, n=5):")
print(f"  Average: {avg_duration:.3f}s")
print(f"  Min: {min_duration:.3f}s")
print(f"  Max: {max_duration:.3f}s")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tool Integration Complete
# MAGIC
# MAGIC You've learned about:
# MAGIC - Tool configuration and executor
# MAGIC - UC function integration
# MAGIC - Multi-country tool execution
# MAGIC - Error handling
# MAGIC - Result formatting
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - **04-validation**: LLM-as-a-Judge validation
# MAGIC - **03-monitoring-demo/01-mlflow-tracking**: Track tool performance

# COMMAND ----------

print("✅ Tool integration complete!")
print("   Tools tested across 4 countries")
print("   Error handling verified")
print("   Ready for agent orchestration")
