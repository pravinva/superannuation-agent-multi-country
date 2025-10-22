# config.py

BRANDCONFIG = {
    "brand_name": "Global Retirement Advisory",
    "logo_url": "static/logo.svg",
    "support_email": "support@example.com"
}

# National colors for UI theming
NATIONAL_COLORS = {
    "Australia": ["#00843D", "#FFD700"],
    "USA": ["#3C3B6E", "#B22234", "#FFFFFF"],
    "UK": ["#012169", "#C8102E", "#FFFFFF"],
    "India": ["#FF9933", "#138808", "#FFFFFF"]
}

# MLflow experiment configuration
MLFLOW_PROD_EXPERIMENT_PATH = "/Workspace/Users/pravin.varma@databricks.com/experiments/prod/retirement-advisory"
MLFLOW_OFFLINE_EVAL_PATH = "/Workspace/Users/pravin.varma@databricks.com/offline/retirement-eval"

# Architecture and infrastructure details
ARCHITECTURECONTENT = {
    "description": "This system supports superannuation and pension queries across Australia, USA, UK, and India with full governance and tool validation.",
    "infra_details": "Leveraging Databricks, Unity Catalog, and proprietary calculators. All queries and LLM validation interactions are logged for compliance."
}

# Unity Catalog configuration
UNITY_CATALOG = "super_advisory_demo"
UNITY_SCHEMA = "member_data"
GOVERNANCE_TABLE = "governance"
MEMBER_PROFILES_TABLE = "member_profiles"

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
