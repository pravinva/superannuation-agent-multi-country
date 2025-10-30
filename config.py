# config.py - Configuration for Multi-Country Pension Advisor
# 
# This file contains configuration for the enterprise-grade agentic AI demo.
# Update the placeholders below with your Databricks workspace details.

# ============================================================================
# Brand Configuration
# ============================================================================

BRANDCONFIG = {
    "brand_name": "Global Retirement Advisory",
    "subtitle": "Enterprise-Grade Agentic AI on Databricks",
    "logo_url": "logo.png",
    "support_email": "support@example.com"  # Update with your support email
}

# National colors for UI theming
NATIONAL_COLORS = {
    "Australia": ["#00843D", "#FFD700"],
    "USA": ["#3C3B6E", "#B22234", "#FFFFFF"],
    "UK": ["#012169", "#C8102E", "#FFFFFF"],
    "India": ["#FF9933", "#138808", "#FFFFFF"]
}

# ============================================================================
# LLM CONFIGURATION - Foundation Model API Endpoints
# ============================================================================

# Main LLM for synthesis and planning (Claude Opus 4.1)
MAIN_LLM_ENDPOINT = "databricks-claude-opus-4-1"
MAIN_LLM_TEMPERATURE = 0.2
MAIN_LLM_MAX_TOKENS = 750
MAX_VALIDATION_ATTEMPTS = 2

# Judge LLM for validation (Claude Sonnet 4)
JUDGE_LLM_ENDPOINT = "databricks-claude-sonnet-4"
JUDGE_LLM_TEMPERATURE = 0.1
JUDGE_LLM_MAX_TOKENS = 300
LLM_JUDGE_CONFIDENCE_THRESHOLD = 0.70

# ============================================================================
# DATABRICKS GENAI PRICING (per 1M tokens) - Official rates
# ============================================================================

# Source: https://www.databricks.com/product/pricing/genai-pricing-calculator
LLM_PRICING = {
    "claude-opus-4-1": {
        "input_tokens": 15.00,  # $15 per 1M input tokens
        "output_tokens": 75.00  # $75 per 1M output tokens
    },
    "claude-sonnet-4": {
        "input_tokens": 3.00,   # $3 per 1M input tokens
        "output_tokens": 15.00  # $15 per 1M output tokens
    },
    "claude-haiku-4": {
        "input_tokens": 0.25,   # $0.25 per 1M input tokens
        "output_tokens": 1.25   # $1.25 per 1M output tokens
    }
}

# ============================================================================
# MLflow Configuration
# ============================================================================

# Update with your Databricks username/email
MLFLOW_PROD_EXPERIMENT_PATH = "/Users/<your-email>/prodretirement-advisory"
MLFLOW_OFFLINE_EVAL_PATH = "/Users/<your-email>/retirement-eval"

# ============================================================================
# Architecture and infrastructure details
# ============================================================================

ARCHITECTURECONTENT = {
    "description": "This system supports superannuation and pension queries across Australia, USA, UK, and India with full governance and tool validation.",
    "infra_details": "Leveraging Databricks, Unity Catalog, and proprietary calculators. All queries and LLM validation interactions are logged for compliance."
}

# ============================================================================
# Unity Catalog Configuration
# ============================================================================

UNITY_CATALOG = "super_advisory_demo"
UNITY_SCHEMA = "member_data"
GOVERNANCE_TABLE = "governance"
MEMBER_PROFILES_TABLE = "member_profiles"

# SQL Warehouse ID - Update with your warehouse ID or configure in UI
# Find your warehouse ID: SQL → SQL Warehouses → Select warehouse → Copy ID
# Can also be configured via UI: Governance → Configuration tab
SQL_WAREHOUSE_ID = "Your SQL Warehouse ID here"

# ============================================================================
# Helper Functions
# ============================================================================

def get_table_path(table_name):
    """Get fully qualified table path"""
    return f"{UNITY_CATALOG}.{UNITY_SCHEMA}.{table_name}"

def get_governance_table_path():
    """Get governance table full path"""
    return get_table_path(GOVERNANCE_TABLE)

def get_member_profiles_table_path():
    """Get member profiles table full path"""
    return get_table_path(MEMBER_PROFILES_TABLE)

def calculate_llm_cost(input_tokens, output_tokens, model_type):
    """
    Calculate cost based on official Databricks GenAI pricing.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens  
        model_type: "claude-opus-4-1", "claude-sonnet-4", or "claude-haiku-4"
    
    Returns:
        Total cost in USD
    """
    if model_type not in LLM_PRICING:
        model_type = "claude-sonnet-4"  # fallback
    
    pricing = LLM_PRICING[model_type]
    
    input_cost = (input_tokens / 1_000_000) * pricing["input_tokens"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_tokens"]
    
    total_cost = input_cost + output_cost
    return total_cost

# ============================================================================
# Configuration Validation
# ============================================================================

def validate_configuration():
    """Validate that required configuration is set"""
    issues = []
    
    if SQL_WAREHOUSE_ID == "YOUR_WAREHOUSE_ID_HERE":
        issues.append("⚠️  SQL_WAREHOUSE_ID not configured")
    
    if "<your-email>" in MLFLOW_PROD_EXPERIMENT_PATH:
        issues.append("⚠️  MLFLOW_PROD_EXPERIMENT_PATH contains placeholder")
    
    if BRANDCONFIG["support_email"] == "support@example.com":
        issues.append("ℹ️  Using default support email (optional)")
    
    if issues:
        import warnings
        warnings.warn(
            "\n".join([
                "Configuration issues found:",
                *issues,
                "",
                "Update config.py or configure via UI (Governance → Configuration tab)"
            ])
        )
    
    return len([i for i in issues if i.startswith("⚠️")]) == 0

# Run validation on import (optional - comment out if not desired)
# validate_configuration()
