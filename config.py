# config.py
"""Configuration for multi-country retirement advisory application"""

# Brand Configuration
BRANDCONFIG = {
    "brand_name": "Global Retirement Advisory",
    "subtitle": "Enterprise-Grade Agentic AI on Databricks",
    "logo_url": "logo.png",
    "support_email": "support@globalpensionfund.com"
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
MAIN_LLM_TEMPERATURE = 0.3
MAIN_LLM_MAX_TOKENS = 750 

# Judge LLM for validation (Claude Sonnet 4)
JUDGE_LLM_ENDPOINT = "databricks-claude-sonnet-4"
JUDGE_LLM_TEMPERATURE = 0.1
JUDGE_LLM_MAX_TOKENS = 300

# ============================================================================
# MLflow Configuration
# ============================================================================

MLFLOW_PROD_EXPERIMENT_PATH = "/Workspace/Users/pravin.varma@databricks.com/prodretirement-advisory"
MLFLOW_OFFLINE_EVAL_PATH = "/Workspace/Users/pravin.varma@databricks.com/retirement-eval"

# ============================================================================
# Architecture and infrastructure details
# ============================================================================

ARCHITECTURECONTENT = {
    "description": "This system supports superannuation and pension queries across Australia, USA, UK, and India with full governance and tool validation.",
    "infra_details": "Leveraging Databricks, Unity Catalog, and proprietary calculators. All queries and LLM validation interactions are logged for compliance."
}

# ============================================================================
# Unity Catalog configuration
# ============================================================================

UNITY_CATALOG = "super_advisory_demo"
UNITY_SCHEMA = "member_data"
GOVERNANCE_TABLE = "governance"
MEMBER_PROFILES_TABLE = "member_profiles"
SQL_WAREHOUSE_ID = "4b9b953939869799"

# Helper functions
def get_table_path(table_name):
    """Get fully qualified table path"""
    return f"{UNITY_CATALOG}.{UNITY_SCHEMA}.{table_name}"

def get_governance_table_path():
    """Get governance table full path"""
    return get_table_path(GOVERNANCE_TABLE)

def get_member_profiles_table_path():
    """Get member profiles table full path"""
    return get_table_path(MEMBER_PROFILES_TABLE)

