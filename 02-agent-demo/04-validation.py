# Databricks notebook source
# MAGIC %md
# MAGIC # Response Validation - LLM-as-a-Judge
# MAGIC
# MAGIC This notebook demonstrates the validation system that ensures agent
# MAGIC responses are accurate, compliant, and high-quality.
# MAGIC
# MAGIC **Validation Approach:**
# MAGIC - LLM-as-a-Judge (Claude Sonnet)
# MAGIC - Confidence scoring
# MAGIC - Automatic retry on low confidence
# MAGIC - Audit logging

# COMMAND ----------

import sys
sys.path.append('..')

from validation import validate_response
from validation.json_parser import JSONParser
from config import JUDGE_LLM_ENDPOINT, LLM_JUDGE_CONFIDENCE_THRESHOLD

print("✓ Validation modules imported")
print(f"  Judge LLM: {JUDGE_LLM_ENDPOINT}")
print(f"  Confidence threshold: {LLM_JUDGE_CONFIDENCE_THRESHOLD}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Prompt Template

# COMMAND ----------

from prompts.template_manager import TemplateManager

tm = TemplateManager()

# Show validation prompt template
validation_template = tm.render_validation_prompt(
    query="How much tax will I pay?",
    response="Based on your age of 65 and withdrawal of $50,000...",
    country="AU",
    member_id="AU001"
)

print("Validation Prompt Structure:")
print(validation_template[:500] + "...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate a Response

# COMMAND ----------

# Example response to validate
query = "When can I access my super without penalties?"
response = """Based on your member profile, you can access your superannuation
without penalties at age 60, which is your preservation age. Since you are currently
62 years old, you are able to withdraw from your super tax-free."""
country = "AU"
member_id = "AU004"

print(f"Query: {query}")
print(f"Response: {response[:100]}...")
print(f"Country: {country}\n")

# Validate the response
validation_result = validate_response(
    query=query,
    response=response,
    country=country,
    member_id=member_id
)

print("Validation Result:")
print(f"  Verdict: {validation_result['verdict']}")
print(f"  Confidence: {validation_result.get('confidence', 0):.2f}")
print(f"  Passed: {validation_result.get('passed', False)}")
print(f"\nFeedback: {validation_result.get('feedback', 'N/A')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Criteria

# COMMAND ----------

# The judge evaluates responses on:
criteria = [
    "Accuracy: Information is factually correct",
    "Completeness: Addresses all parts of the query",
    "Compliance: Follows country-specific regulations",
    "Clarity: Easy to understand",
    "Citations: Proper references included",
    "Tone: Professional and helpful"
]

print("Validation Criteria:")
for criterion in criteria:
    print(f"  ✓ {criterion}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Different Response Quality Levels

# COMMAND ----------

test_cases = [
    {
        "name": "High Quality Response",
        "query": "What is my super balance?",
        "response": "Your current superannuation balance is $450,000 AUD. This information is current as of today.",
        "expected_verdict": "Pass"
    },
    {
        "name": "Incomplete Response",
        "response": "Your balance is good.",
        "expected_verdict": "Fail or Review"
    },
    {
        "name": "Incorrect Information",
        "response": "You can withdraw your super at age 50 without penalties.",
        "expected_verdict": "Fail"
    }
]

# Note: Actual validation requires LLM calls, which we'll simulate
print("Validation Test Cases:")
for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. {test['name']}")
    print(f"   Response: {test.get('response', '')[:60]}...")
    print(f"   Expected: {test['expected_verdict']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Confidence Scoring

# COMMAND ----------

# Confidence threshold determines retry logic
print(f"Confidence Threshold: {LLM_JUDGE_CONFIDENCE_THRESHOLD}")
print("\nRetry Logic:")
print(f"  Confidence < {LLM_JUDGE_CONFIDENCE_THRESHOLD}: Retry synthesis")
print(f"  Confidence >= {LLM_JUDGE_CONFIDENCE_THRESHOLD}: Accept response")
print("\nMax Retry Attempts: 2")

# COMMAND ----------

# MAGIC %md
# MAGIC ## JSON Response Parsing

# COMMAND ----------

# The judge returns JSON which must be parsed reliably
parser = JSONParser()

# Example judge responses (various formats)
test_responses = [
    '{"passed": true, "confidence": 0.95, "feedback": "Accurate response"}',
    '```json\n{"passed": true, "confidence": 0.85}\n```',
    'The response is correct. {"passed": true, "confidence": 0.90}'
]

print("JSON Parser Test:")
for i, response in enumerate(test_responses, 1):
    result = parser.parse_validation_result(response)
    print(f"\n{i}. Input: {response[:50]}...")
    print(f"   Parsed: {result}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Metrics

# COMMAND ----------

# Track validation performance
from config import UNITY_CATALOG, UNITY_SCHEMA

validation_metrics = spark.sql(f"""
SELECT
    country,
    judge_verdict,
    COUNT(*) as query_count,
    AVG(total_time_seconds) as avg_time,
    AVG(validation_attempts) as avg_attempts
FROM {UNITY_CATALOG}.{UNITY_SCHEMA}.governance
WHERE judge_verdict IS NOT NULL
GROUP BY country, judge_verdict
ORDER BY country, judge_verdict
""")

display(validation_metrics)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Pass Rate

# COMMAND ----------

pass_rate = spark.sql(f"""
SELECT
    country,
    COUNT(CASE WHEN judge_verdict = 'Pass' THEN 1 END) * 100.0 / COUNT(*) as pass_rate,
    COUNT(*) as total_queries
FROM {UNITY_CATALOG}.{UNITY_SCHEMA}.governance
WHERE judge_verdict IS NOT NULL
GROUP BY country
ORDER BY country
""")

display(pass_rate)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Complete
# MAGIC
# MAGIC You've learned about:
# MAGIC - LLM-as-a-Judge validation
# MAGIC - Validation criteria
# MAGIC - Confidence scoring
# MAGIC - JSON response parsing
# MAGIC - Validation metrics
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - **03-monitoring-demo/01-mlflow-tracking**: Track validation metrics
# MAGIC - **03-monitoring-demo/03-dashboard**: Visualize validation results

# COMMAND ----------

print("✅ Validation deep dive complete!")
print("   LLM-as-a-Judge: Claude Sonnet")
print("   Confidence threshold: 0.70")
print("   Max retries: 2")
print("   Ready for production use")
