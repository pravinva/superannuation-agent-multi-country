"""
Pytest Fixtures for Integration Tests
======================================

Provides reusable fixtures for all integration tests.
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent import SuperAdvisorAgent
from tools import SuperAdvisorTools
from tests.test_config import *
from utils.lakehouse import execute_sql_statement


@pytest.fixture(scope="session")
def agent():
    """
    Create SuperAdvisorAgent instance for testing.

    Scope: session - created once per test session
    """
    return SuperAdvisorAgent(
        validation_mode="llm_judge",
        enable_mlflow_prompts=False  # Use local prompts for tests
    )


@pytest.fixture(scope="session")
def tools():
    """
    Create SuperAdvisorTools instance for testing.

    Scope: session - created once per test session
    """
    return SuperAdvisorTools()


@pytest.fixture(scope="function")
def test_session_id():
    """
    Generate unique session ID for each test.

    Scope: function - new ID for each test
    """
    return f"test-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"


@pytest.fixture(scope="session")
def test_members():
    """
    Provide test member IDs for all countries.

    Returns dict: {country_code: member_id}
    """
    return TEST_MEMBERS


@pytest.fixture(scope="function")
def cleanup_governance_logs(test_session_id):
    """
    Clean up test governance logs after test completion.

    Scope: function - runs after each test
    """
    yield  # Test runs here

    # Cleanup after test
    if TEST_SETTINGS["cleanup_test_data"]:
        try:
            cleanup_sql = f"""
            DELETE FROM {get_governance_table_path()}
            WHERE session_id = '{test_session_id}'
            """
            execute_sql_statement(cleanup_sql)
        except Exception as e:
            print(f"Warning: Could not clean up test data: {e}")


@pytest.fixture(scope="function")
def mlflow_test_experiment():
    """
    Set up MLflow test experiment.

    Scope: function - separate experiment for each test
    """
    import mlflow

    # Set experiment for tests
    mlflow.set_experiment(MLFLOW_TEST_EXPERIMENT_PATH)

    return MLFLOW_TEST_EXPERIMENT_PATH


@pytest.fixture(scope="session")
def verify_test_members_exist(tools):
    """
    Verify that test member IDs exist in database.

    Scope: session - runs once at start
    Fails fast if test data is missing
    """
    missing_members = []

    for country, member_id in TEST_MEMBERS.items():
        profile = tools.get_member_profile(member_id)
        if not profile or "error" in profile:
            missing_members.append(f"{country}: {member_id}")

    if missing_members:
        pytest.fail(
            f"Test members not found in database:\n" +
            "\n".join(missing_members) +
            "\n\nPlease ensure test data exists before running integration tests."
        )

    return True


@pytest.fixture(scope="function")
def mock_llm_response():
    """
    Provide mock LLM responses for faster testing.

    Only used when TEST_SETTINGS["run_real_llm_calls"] = False
    """
    return {
        "balance_inquiry": {
            "text": "Your current superannuation balance is A$125,450.75.",
            "input_tokens": 500,
            "output_tokens": 100,
            "cost": 0.002
        },
        "contribution_limits": {
            "text": "Your concessional contribution cap is $30,000 per year.",
            "input_tokens": 600,
            "output_tokens": 120,
            "cost": 0.003
        }
    }


@pytest.fixture(scope="function")
def test_timer():
    """
    Track test execution time.

    Yields tuple: (start_time, get_duration_func)
    """
    start_time = datetime.now()

    def get_duration():
        return (datetime.now() - start_time).total_seconds()

    yield start_time, get_duration

    # Log duration after test
    duration = get_duration()
    if TEST_SETTINGS["verbose_logging"]:
        print(f"\n⏱️  Test duration: {duration:.2f}s")
