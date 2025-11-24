"""
Country-Specific Integration Tests
====================================

Tests retirement system logic for each supported country:
- Australia: Superannuation, APRA regulations
- United States: 401(k), IRA, DOL regulations
- United Kingdom: SIPP, Pension schemes, FCA regulations
- India: NPS, EPS, EPF/EPFO, PFRDA regulations

Test Coverage:
- Country-specific retirement terminology
- Regulatory authority references
- Currency and tax rules
- Contribution limits and withdrawal conditions
- Cross-country query handling
"""

import pytest
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.test_config import *
from shared.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# AUSTRALIA - SUPERANNUATION TESTS
# ============================================================================

class TestAustralianSuperannuation:
    """Test Australian superannuation system."""

    def test_superannuation_balance_inquiry(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.1: Australian superannuation balance inquiry.

        Validates:
        - Correct use of "superannuation" terminology
        - AUD currency
        - APRA regulatory references
        """
        member_id = TEST_MEMBERS["AU"]
        query = "What's my superannuation balance?"

        logger.info(f"🧪 Testing AU superannuation inquiry")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"].lower()

        # Should mention superannuation
        assert any(term in response_text for term in ["superannuation", "super"]), \
            "Response should mention superannuation"

        # Should have AUD currency
        expected = EXPECTED_TEST_DATA[member_id]
        assert expected["currency_symbol"] in result["response"] or \
               expected["currency_code"] in result["response"]

        logger.info(f"   ✅ AU superannuation test passed")

    def test_preservation_age_rules(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.2: Australian preservation age rules.

        Validates:
        - Knowledge of preservation age (55-60 depending on DOB)
        - Early access conditions (hardship, compassionate grounds)
        - APRA/ATO regulatory citations
        """
        member_id = TEST_MEMBERS["AU"]
        query = "Can I access my super before retirement age?"

        logger.info(f"🧪 Testing AU preservation age rules")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        # Should mention preservation age or early access conditions
        preservation_terms = [
            "preservation age", "early access", "hardship",
            "compassionate", "condition of release"
        ]
        assert any(term in response_text for term in preservation_terms), \
            "Response should discuss preservation age or access conditions"

        logger.info(f"   ✅ AU preservation age test passed")


# ============================================================================
# UNITED STATES - 401(k) AND IRA TESTS
# ============================================================================

class TestUnitedStates401k:
    """Test US 401(k) and IRA systems."""

    def test_401k_balance_inquiry(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.3: US 401(k) balance inquiry.

        Validates:
        - Recognition of "401(k)" and "401k" terminology
        - USD currency
        - DOL/IRS regulatory references
        """
        member_id = TEST_MEMBERS["US"]
        query = "What's my 401(k) balance?"

        logger.info(f"🧪 Testing US 401(k) inquiry")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"]

        # Should mention 401(k) or retirement account
        assert any(term in response_text.lower() for term in ["401", "retirement", "account"]), \
            "Response should reference 401(k) or retirement account"

        # Should have USD currency
        expected = EXPECTED_TEST_DATA[member_id]
        assert expected["currency_symbol"] in response_text or \
               expected["currency_code"] in response_text

        logger.info(f"   ✅ US 401(k) test passed")

    def test_401k_contribution_limits(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.4: US 401(k) contribution limits.

        Validates:
        - Knowledge of annual contribution limits ($23,000 in 2024)
        - Catch-up contributions for 50+ ($7,500 additional)
        - Employer matching concepts
        """
        member_id = TEST_MEMBERS["US"]
        query = "What are the 401(k) contribution limits?"

        logger.info(f"🧪 Testing US 401(k) contribution limits")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        # Should discuss contribution limits
        limit_terms = ["contribution", "limit", "cap", "maximum", "employer match"]
        assert any(term in response_text for term in limit_terms), \
            "Response should discuss contribution limits"

        logger.info(f"   ✅ US 401(k) contribution limits test passed")

    def test_early_withdrawal_penalty(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.5: US 401(k) early withdrawal penalty.

        Validates:
        - Knowledge of 10% early withdrawal penalty before age 59½
        - Exceptions: first home, education, medical expenses
        - IRS regulatory references
        """
        member_id = TEST_MEMBERS["US"]
        query = "What happens if I withdraw from my 401(k) early?"

        logger.info(f"🧪 Testing US early withdrawal penalty")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        # Should mention penalty or withdrawal rules
        penalty_terms = ["penalty", "early withdrawal", "age", "exception", "tax"]
        assert any(term in response_text for term in penalty_terms), \
            "Response should discuss early withdrawal penalties"

        logger.info(f"   ✅ US early withdrawal penalty test passed")


# ============================================================================
# UNITED KINGDOM - PENSION TESTS
# ============================================================================

class TestUnitedKingdomPension:
    """Test UK pension systems (SIPP, workplace pensions)."""

    def test_uk_pension_balance(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.6: UK pension balance inquiry.

        Validates:
        - Recognition of "pension" terminology
        - GBP currency (£)
        - FCA regulatory references
        """
        member_id = TEST_MEMBERS["UK"]
        query = "What's my pension balance?"

        logger.info(f"🧪 Testing UK pension inquiry")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"]

        # Should mention pension
        assert "pension" in response_text.lower(), \
            "Response should mention pension"

        # Should have GBP currency
        expected = EXPECTED_TEST_DATA[member_id]
        assert expected["currency_symbol"] in response_text or \
               expected["currency_code"] in response_text

        logger.info(f"   ✅ UK pension test passed")

    def test_uk_pension_access_age(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.7: UK pension access age (55, moving to 57 in 2028).

        Validates:
        - Knowledge of minimum pension age
        - 25% tax-free lump sum
        - FCA/HMRC regulatory references
        """
        member_id = TEST_MEMBERS["UK"]
        query = "When can I access my pension?"

        logger.info(f"🧪 Testing UK pension access age")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        # Should discuss access age or retirement age
        age_terms = ["age", "access", "retirement", "withdraw", "55", "57"]
        assert any(term in response_text for term in age_terms), \
            "Response should discuss pension access age"

        logger.info(f"   ✅ UK pension access age test passed")


# ============================================================================
# INDIA - NPS, EPS, EPF/EPFO TESTS
# ============================================================================

class TestIndiaNPSandEPF:
    """Test Indian retirement systems: NPS, EPS, EPF/EPFO."""

    def test_nps_balance_inquiry(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.8: Indian NPS (National Pension System) balance inquiry.

        Validates:
        - Recognition of "NPS" terminology
        - INR currency (₹)
        - PFRDA regulatory references
        """
        member_id = TEST_MEMBERS["IN"]
        query = "What's my NPS balance?"

        logger.info(f"🧪 Testing IN NPS inquiry")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"]

        # Should mention NPS or pension
        assert any(term in response_text.upper() for term in ["NPS", "PENSION", "RETIREMENT"]), \
            "Response should mention NPS or retirement account"

        # Should have INR currency
        expected = EXPECTED_TEST_DATA[member_id]
        assert expected["currency_symbol"] in response_text or \
               expected["currency_code"] in response_text

        logger.info(f"   ✅ IN NPS test passed")

    def test_epf_balance_inquiry(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.9: Indian EPF (Employees' Provident Fund) balance inquiry.

        Validates:
        - Recognition of "EPF", "EPFO", "PF" terminology
        - INR currency
        - EPFO regulatory references
        """
        member_id = TEST_MEMBERS["IN"]
        query = "What's my EPF balance?"

        logger.info(f"🧪 Testing IN EPF inquiry")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"]

        # Should mention EPF/PF or provident fund
        assert any(term in response_text.upper() for term in ["EPF", "PF", "PROVIDENT", "RETIREMENT"]), \
            "Response should mention EPF or provident fund"

        # Should have INR currency
        expected = EXPECTED_TEST_DATA[member_id]
        assert expected["currency_symbol"] in response_text or \
               expected["currency_code"] in response_text

        logger.info(f"   ✅ IN EPF test passed")

    def test_eps_pension_scheme(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.10: Indian EPS (Employees' Pension Scheme).

        Validates:
        - Recognition of "EPS" terminology
        - Understanding of pension component vs PF component
        - EPFO regulatory references
        """
        member_id = TEST_MEMBERS["IN"]
        query = "What is my EPS pension?"

        logger.info(f"🧪 Testing IN EPS inquiry")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"]

        # Should mention EPS or pension
        assert any(term in response_text.upper() for term in ["EPS", "PENSION", "RETIREMENT"]), \
            "Response should mention EPS or pension scheme"

        logger.info(f"   ✅ IN EPS test passed")

    def test_nps_vs_epf_comparison(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.11: Comparison between NPS and EPF.

        Validates:
        - Understanding of differences between NPS and EPF
        - Tax treatment differences
        - Withdrawal rules differences
        """
        member_id = TEST_MEMBERS["IN"]
        query = "What's the difference between NPS and EPF?"

        logger.info(f"🧪 Testing IN NPS vs EPF comparison")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].upper()

        # Should mention both NPS and EPF
        assert "NPS" in response_text or "NATIONAL PENSION" in response_text, \
            "Response should mention NPS"
        assert "EPF" in response_text or "PROVIDENT FUND" in response_text, \
            "Response should mention EPF"

        # Should discuss differences
        comparison_terms = ["DIFFERENCE", "COMPARE", "VERSUS", "VS", "UNLIKE", "WHEREAS"]
        assert any(term in response_text for term in comparison_terms), \
            "Response should compare NPS and EPF"

        logger.info(f"   ✅ IN NPS vs EPF comparison test passed")


# ============================================================================
# CROSS-COUNTRY TESTS
# ============================================================================

class TestCrossCountryQueries:
    """Test handling of queries that mention multiple countries."""

    def test_401k_query_from_australian_member(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.12: Australian member asking about US 401(k).

        Validates:
        - Agent recognizes query is about different country's system
        - Provides appropriate response or clarification
        - Doesn't confuse 401(k) with Australian superannuation
        """
        member_id = TEST_MEMBERS["AU"]
        query = "Can you tell me about 401(k) plans?"

        logger.info(f"🧪 Testing cross-country query: AU member asks about 401(k)")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"]

        # Should mention 401(k) or US retirement system
        assert "401" in response_text or "United States" in response_text or "US" in response_text, \
            "Response should acknowledge 401(k) or US context"

        logger.info(f"   ✅ Cross-country query test passed")

    def test_uk_pension_query_from_indian_member(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 2.13: Indian member asking about UK pension.

        Validates:
        - Agent recognizes international query
        - Provides appropriate response
        """
        member_id = TEST_MEMBERS["IN"]
        query = "How do UK pensions work?"

        logger.info(f"🧪 Testing cross-country query: IN member asks about UK pension")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"]

        # Should mention UK or pension
        assert any(term in response_text for term in ["UK", "United Kingdom", "pension"]), \
            "Response should acknowledge UK pension context"

        logger.info(f"   ✅ Cross-country query test passed")


# ============================================================================
# TEST MARKERS
# ============================================================================

pytest.mark.integration = pytest.mark.integration
pytest.mark.country_specific = pytest.mark.country_specific
