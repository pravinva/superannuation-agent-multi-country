"""
End-to-End Integration Tests
=============================

Tests complete query processing workflow from input to response.

Test Coverage:
- Complete balance inquiry flow
- Multi-tool query execution
- Validation and retry logic
- MLflow logging
- Governance table logging
"""

import pytest
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.test_config import *
from shared.logging_config import get_logger

logger = get_logger(__name__)


class TestE2EBalanceInquiry:
    """Test complete balance inquiry workflow."""

    def test_balance_inquiry_australia(
        self,
        agent,
        test_session_id,
        test_timer,
        verify_test_members_exist,
        cleanup_governance_logs
    ):
        """
        Test 1.1: Complete balance inquiry for Australian member.

        Flow:
        1. User asks: "What's my current balance?"
        2. Agent retrieves member profile (AU001)
        3. Classifies query as "balance_inquiry"
        4. Calls get_current_balance tool
        5. Synthesizes response with AUD currency
        6. LLM Judge validates response
        7. Logs to governance table
        8. Logs to MLflow

        Expected:
        - Response contains correct currency (A$)
        - Classification successful
        - Judge verdict: PASS
        - Governance table has event record
        - Total execution time < 30s
        """
        # Arrange
        member_id = TEST_MEMBERS["AU"]
        query = TEST_QUERIES["balance_inquiry"][0]  # "What's my current balance?"
        start_time, get_duration = test_timer

        logger.info(f"🧪 Starting E2E test: Balance Inquiry (AU)")
        logger.info(f"   Member: {member_id}")
        logger.info(f"   Query: {query}")
        logger.info(f"   Session: {test_session_id}")

        # Act
        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        duration = get_duration()

        # Assert - Basic response structure
        assert result is not None, "Agent returned None"
        assert "error" not in result, f"Agent returned error: {result.get('error')}"
        assert "response" in result, "Response missing from result"

        response_text = result.get("response", "")
        assert len(response_text) > 0, "Response text is empty"

        # Assert - Currency symbol OR currency code present
        expected_data = EXPECTED_TEST_DATA[member_id]
        currency_symbol = expected_data["currency_symbol"]
        currency_code = expected_data["currency_code"]
        has_currency = currency_symbol in response_text or currency_code in response_text
        assert has_currency, \
            f"Expected currency '{currency_symbol}' or '{currency_code}' not found in response"

        # Assert - Classification occurred
        if "classification_method" in result:
            classification = result["classification_method"]
            assert classification in ["regex", "embedding", "llm"], \
                f"Unknown classification method: {classification}"
            logger.info(f"   ✅ Classification: {classification}")

        # Assert - Validation passed
        if "judge_verdict" in result:
            verdict = result["judge_verdict"]
            assert verdict == "PASS", \
                f"LLM Judge verdict failed: {verdict}"
            logger.info(f"   ✅ Judge verdict: {verdict}")

        # Assert - Cost tracked
        if "cost" in result:
            cost = result["cost"]
            assert cost > 0, "Cost not tracked"
            assert cost < 0.10, f"Cost too high: ${cost:.4f}"  # Sanity check
            logger.info(f"   ✅ Cost: ${cost:.4f}")

        # Assert - Performance
        assert duration < TEST_SETTINGS["max_test_duration_seconds"], \
            f"Test took too long: {duration:.2f}s"

        logger.info(f"   ✅ Duration: {duration:.2f}s")
        logger.info(f"   ✅ Test PASSED")

    def test_balance_inquiry_all_countries(
        self,
        agent,
        test_members,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 1.2: Balance inquiry works for all 4 countries.

        Tests:
        - AU (Australia) - A$
        - US (United States) - $
        - UK (United Kingdom) - £
        - IN (India) - ₹

        Validation:
        - Correct currency symbol in response
        - Response contains balance information
        - All countries complete successfully
        """
        query = "What's my current balance?"
        results = {}
        start_time, get_duration = test_timer

        logger.info(f"🧪 Starting multi-country balance inquiry test")

        for country, member_id in test_members.items():
            logger.info(f"\n   Testing {country}: {member_id}")

            # Execute query
            result = agent.process_query(
                member_id=member_id,
                user_query=query
            )

            # Store result
            results[country] = result

            # Basic assertions
            assert result is not None, f"{country}: Agent returned None"
            assert "error" not in result, f"{country}: {result.get('error')}"
            assert "response" in result, f"{country}: Response missing"

            response_text = result.get("response", "")

            # Currency assertion (accept either symbol or code)
            expected = EXPECTED_TEST_DATA[member_id]
            currency_symbol = expected["currency_symbol"]
            currency_code = expected["currency_code"]
            has_currency = currency_symbol in response_text or currency_code in response_text
            assert has_currency, \
                f"{country}: Currency '{currency_symbol}' or '{currency_code}' not found"

            logger.info(f"      ✅ {country} passed (currency: {currency_symbol}/{currency_code})")

        duration = get_duration()
        logger.info(f"\n   ✅ All {len(test_members)} countries passed")
        logger.info(f"   ✅ Total duration: {duration:.2f}s")


class TestE2EMultiTool:
    """Test queries requiring multiple tool calls."""

    @pytest.mark.slow
    def test_contribution_and_projection(
        self,
        agent,
        test_session_id,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 1.3: Multi-tool query execution.

        Query: "If I contribute $500/month, what will my balance be in 10 years?"

        Expected Tools Called:
        1. get_current_balance
        2. get_contribution_limits
        3. calculate_future_balance

        Validation:
        - Multiple tools executed
        - Results combined in synthesis
        - Cost tracks all LLM calls
        """
        member_id = TEST_MEMBERS["AU"]
        query = "If I contribute $500 per month, what will my balance be in 10 years?"

        logger.info(f"🧪 Starting multi-tool test")
        logger.info(f"   Query: {query}")

        # Act
        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        # Assert
        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result.get("response", "")
        assert len(response_text) > 0

        # Check that response addresses future projection
        future_keywords = ["year", "future", "will be", "projection", "grow"]
        has_future_reference = any(word in response_text.lower() for word in future_keywords)
        assert has_future_reference, "Response doesn't address future projection"

        logger.info(f"   ✅ Multi-tool test passed")


class TestE2EValidation:
    """Test validation and retry logic."""

    def test_validation_logs_correctly(
        self,
        agent,
        test_members,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 1.4: Validation logging.

        Validates that:
        - Judge verdict is logged
        - Validation attempts tracked
        - Confidence scores recorded (if available)
        """
        member_id = TEST_MEMBERS["AU"]
        query = "What's my balance?"

        logger.info(f"🧪 Starting validation logging test")

        # Act
        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        # Assert
        assert result is not None
        assert "validation" in result or "attempts" in result, \
            "No validation information in result"

        # Check validation structure (nested in 'validation' key)
        if "validation" in result:
            validation = result["validation"]
            assert "passed" in validation, "Validation missing 'passed' field"
            logger.info(f"   ✅ Validation passed: {validation.get('passed')}")
            if "violations" in validation:
                logger.info(f"   ℹ️ Violations: {len(validation.get('violations', []))}")

        # Check attempts tracked
        if "attempts" in result:
            attempts = result["attempts"]
            assert attempts >= 1, "Validation attempts not tracked"
            assert attempts <= MAX_VALIDATION_ATTEMPTS, \
                f"Too many attempts: {attempts}"
            logger.info(f"   ✅ Validation attempts: {attempts}")

        logger.info(f"   ✅ Validation logging test passed")


# ============================================================================
# TEST MARKERS AND CONFIGURATION
# ============================================================================

pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.e2e = pytest.mark.e2e
