"""
Test Configuration
==================

Configuration specific to integration tests.
Extends main config.py with test-specific settings.
"""

import os
from config import *

# ============================================================================
# TEST ENVIRONMENT CONFIGURATION
# ============================================================================

# Use separate MLflow experiment for tests to avoid polluting production
MLFLOW_TEST_EXPERIMENT_PATH = "/Users/pravin.varma@databricks.com/retirement-advisory-tests"

# Test members (confirmed to exist in database)
TEST_MEMBERS = {
    "AU": "AU001",  # Australian test member
    "US": "US001",  # US test member
    "UK": "UK001",  # UK test member
    "IN": "IN001"   # Indian test member
}

# Expected values for test assertions
EXPECTED_TEST_DATA = {
    "AU001": {
        "country": "AU",
        "currency_symbol": "A$",
        "currency_code": "AUD",  # ISO code used in responses
        "authority": "APRA",
        "balance_min": 100000.0,  # Minimum expected balance
        "balance_max": 200000.0   # Maximum expected balance
    },
    "US001": {
        "country": "US",
        "currency_symbol": "$",
        "currency_code": "USD",
        "authority": "DOL",
        "balance_min": 50000.0,
        "balance_max": 150000.0
    },
    "UK001": {
        "country": "UK",
        "currency_symbol": "£",
        "currency_code": "GBP",
        "authority": "FCA",
        "balance_min": 50000.0,
        "balance_max": 150000.0
    },
    "IN001": {
        "country": "IN",
        "currency_symbol": "₹",
        "currency_code": "INR",
        "authority": "PFRDA",
        "balance_min": 500000.0,
        "balance_max": 2000000.0
    }
}

# Test queries for different scenarios
TEST_QUERIES = {
    "balance_inquiry": [
        "What's my current balance?",
        "How much do I have saved?",
        "Show me my account balance",
        "What is my superannuation balance?"
    ],
    "contribution_limits": [
        "What are my contribution limits?",
        "How much can I contribute this year?",
        "Tell me about contribution caps"
    ],
    "withdrawal_rules": [
        "When can I access my super?",
        "What are the withdrawal conditions?",
        "Can I withdraw early?"
    ]
}

# Test execution settings
TEST_SETTINGS = {
    "run_real_llm_calls": True,  # Set to False to mock LLM responses
    "max_test_duration_seconds": 30,  # Timeout for individual tests
    "cleanup_test_data": True,  # Clean up governance logs after tests
    "verbose_logging": False  # Enable detailed logging during tests
}

# ============================================================================
# HELPER FUNCTIONS FOR TESTS
# ============================================================================

def get_test_member_id(country_code):
    """Get test member ID for a country."""
    return TEST_MEMBERS.get(country_code.upper())

def get_test_query(query_type, index=0):
    """Get a test query of specified type."""
    queries = TEST_QUERIES.get(query_type, [])
    if queries and index < len(queries):
        return queries[index]
    return None

def get_expected_data(member_id):
    """Get expected test data for a member."""
    return EXPECTED_TEST_DATA.get(member_id, {})

def is_balance_in_expected_range(balance, member_id):
    """Check if balance is in expected range for test member."""
    expected = EXPECTED_TEST_DATA.get(member_id, {})
    min_balance = expected.get("balance_min", 0)
    max_balance = expected.get("balance_max", float('inf'))
    return min_balance <= balance <= max_balance
