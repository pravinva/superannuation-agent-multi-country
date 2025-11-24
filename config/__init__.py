"""
Configuration package for superannuation agent.

This module provides backward-compatible access to configuration loaded from YAML.
All config values are loaded from config/config.yaml instead of root config.py
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Load configuration from YAML
_config_yaml_path = Path(__file__).parent / 'config.yaml'

def _load_yaml_config():
    """Load configuration from YAML file."""
    if not _config_yaml_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {_config_yaml_path}")

    with open(_config_yaml_path, 'r') as f:
        return yaml.safe_load(f)

# Load config once at import time
_config = _load_yaml_config()

# ============================================================================
# LLM Configuration - Main LLM for synthesis
# ============================================================================
MAIN_LLM_ENDPOINT = _config['llm']['endpoint']
MAIN_LLM_TEMPERATURE = _config['llm']['temperature']
MAIN_LLM_MAX_TOKENS = _config['llm']['max_tokens']

# ============================================================================
# LLM Configuration - Judge LLM for validation
# ============================================================================
JUDGE_LLM_ENDPOINT = _config['validation_llm']['endpoint']
JUDGE_LLM_TEMPERATURE = _config['validation_llm']['temperature']
JUDGE_LLM_MAX_TOKENS = _config['validation_llm']['max_tokens']
LLM_JUDGE_CONFIDENCE_THRESHOLD = _config['validation_llm']['confidence_threshold']
MAX_VALIDATION_ATTEMPTS = _config['validation_llm']['max_validation_attempts']

# ============================================================================
# LLM Configuration - Classifier LLM for Stage 3 fallback
# ============================================================================
CLASSIFIER_LLM_ENDPOINT = _config['classifier_llm']['endpoint']

# ============================================================================
# Databricks Configuration
# ============================================================================
SQL_WAREHOUSE_ID = _config['databricks']['sql_warehouse_id']
UNITY_CATALOG = _config['databricks']['unity_catalog']
UNITY_SCHEMA = _config['databricks']['unity_schema']
GOVERNANCE_TABLE = _config['databricks']['governance_table']
MEMBER_PROFILES_TABLE = _config['databricks']['member_profiles_table']

# ============================================================================
# MLflow Configuration
# ============================================================================
MLFLOW_PROD_EXPERIMENT_PATH = _config['mlflow']['prod_experiment_path']
MLFLOW_OFFLINE_EVAL_PATH = _config['mlflow']['offline_eval_path']

# ============================================================================
# Brand Configuration
# ============================================================================
BRANDCONFIG = {
    "brand_name": _config['brand']['brand_name'],
    "subtitle": _config['brand']['subtitle'],
    "logo_url": _config['brand'].get('logo_url', 'logo.png'),
    "support_email": _config['brand'].get('support_email', 'support@example.com')
}

# ============================================================================
# LLM Pricing (from original config.py)
# ============================================================================
LLM_PRICING = {
    "claude-opus-4-1": {
        "input_tokens": 15.00,
        "output_tokens": 75.00
    },
    "claude-sonnet-4": {
        "input_tokens": 3.00,
        "output_tokens": 15.00
    },
    "claude-haiku-4": {
        "input_tokens": 0.25,
        "output_tokens": 1.25
    },
    "gpt-oss-120b": {
        "input_tokens": 0.15,
        "output_tokens": 0.15
    }
}

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
        model_type: Full endpoint name like "databricks-claude-opus-4-1" or "databricks-gpt-oss-120b"

    Returns:
        Total cost in USD
    """
    # Strip "databricks-" prefix if present
    if model_type.startswith("databricks-"):
        model_type = model_type.replace("databricks-", "")

    # Check if model type exists in pricing
    if model_type not in LLM_PRICING:
        model_type = "claude-sonnet-4"  # fallback

    pricing = LLM_PRICING[model_type]

    input_cost = (input_tokens / 1_000_000) * pricing["input_tokens"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_tokens"]

    total_cost = input_cost + output_cost
    return total_cost

def validate_configuration():
    """Validate that required configuration is set"""
    issues = []

    if SQL_WAREHOUSE_ID == "YOUR_WAREHOUSE_ID_HERE":
        issues.append("SQL_WAREHOUSE_ID not configured")

    if "<your-email>" in MLFLOW_PROD_EXPERIMENT_PATH:
        issues.append("MLFLOW_PROD_EXPERIMENT_PATH contains placeholder")

    if BRANDCONFIG["support_email"] == "support@example.com":
        issues.append("Using default support email (optional)")

    if issues:
        import warnings
        warnings.warn(
            "\n".join([
                "Configuration issues found:",
                *issues,
                "",
                "Update config/config.yaml or configure via UI (Governance → Configuration tab)"
            ])
        )

    return len([i for i in issues if "not configured" in i]) == 0

# Export all public symbols for backward compatibility
__all__ = [
    'MAIN_LLM_ENDPOINT',
    'MAIN_LLM_TEMPERATURE',
    'MAIN_LLM_MAX_TOKENS',
    'JUDGE_LLM_ENDPOINT',
    'JUDGE_LLM_TEMPERATURE',
    'JUDGE_LLM_MAX_TOKENS',
    'LLM_JUDGE_CONFIDENCE_THRESHOLD',
    'MAX_VALIDATION_ATTEMPTS',
    'CLASSIFIER_LLM_ENDPOINT',
    'SQL_WAREHOUSE_ID',
    'UNITY_CATALOG',
    'UNITY_SCHEMA',
    'GOVERNANCE_TABLE',
    'MEMBER_PROFILES_TABLE',
    'MLFLOW_PROD_EXPERIMENT_PATH',
    'MLFLOW_OFFLINE_EVAL_PATH',
    'BRANDCONFIG',
    'LLM_PRICING',
    'get_table_path',
    'get_governance_table_path',
    'get_member_profiles_table_path',
    'calculate_llm_cost',
    'validate_configuration',
]
