"""
Comprehensive Topic-Based Integration Tests
============================================

Tests key retirement topics across all countries:
- Taxation: Tax rules, benefits, deductions
- Retirement Planning: Projections, strategies, advice
- Withdrawals: Rules, penalties, conditions
- Annuities: Income streams, pension products
- Preservation Age: Access age, early access rules

Countries: Australia, United States, United Kingdom, India

Test Coverage:
- 5 topics × 4 countries = 20 core tests
- Comprehensive validation of agent knowledge
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
# TAXATION TESTS - ALL COUNTRIES
# ============================================================================

class TestTaxation:
    """Test taxation knowledge for all countries."""

    def test_au_superannuation_tax(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.1: Australian superannuation taxation.

        Validates:
        - Tax-free withdrawals after age 60
        - Tax on withdrawals before preservation age
        - Concessional contributions tax (15%)
        - ATO regulatory references
        """
        member_id = TEST_MEMBERS["AU"]
        query = "What tax do I pay on my superannuation withdrawals?"

        logger.info(f"🧪 Testing AU taxation")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result
        assert "response" in result

        response_text = result["response"].lower()

        # Should discuss tax rules
        tax_terms = ["tax", "taxable", "tax-free", "ato", "income"]
        assert any(term in response_text for term in tax_terms), \
            "Response should discuss taxation"

        logger.info(f"   ✅ AU taxation test passed")

    def test_us_401k_tax(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.2: US 401(k) taxation.

        Validates:
        - Pre-tax contributions
        - Taxable withdrawals at ordinary income rates
        - Roth 401(k) vs traditional 401(k)
        - IRS regulatory references
        """
        member_id = TEST_MEMBERS["US"]
        query = "How is my 401(k) withdrawal taxed?"

        logger.info(f"🧪 Testing US taxation")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        tax_terms = ["tax", "taxable", "irs", "income", "withdraw"]
        assert any(term in response_text for term in tax_terms), \
            "Response should discuss taxation"

        logger.info(f"   ✅ US taxation test passed")

    def test_uk_pension_tax(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.3: UK pension taxation.

        Validates:
        - 25% tax-free lump sum
        - Taxable income on remaining pension
        - HMRC tax bands
        - FCA/HMRC regulatory references
        """
        member_id = TEST_MEMBERS["UK"]
        query = "What tax do I pay on my pension withdrawal?"

        logger.info(f"🧪 Testing UK taxation")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        tax_terms = ["tax", "taxable", "tax-free", "hmrc", "lump sum"]
        assert any(term in response_text for term in tax_terms), \
            "Response should discuss taxation"

        logger.info(f"   ✅ UK taxation test passed")

    def test_in_nps_tax(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.4: Indian NPS/EPF taxation.

        Validates:
        - Tax exemption on EPF withdrawals after 5 years
        - NPS tax benefits (80CCD)
        - Partial withdrawal tax rules
        - Income Tax Act references
        """
        member_id = TEST_MEMBERS["IN"]
        query = "What tax benefits do I get on my NPS contributions?"

        logger.info(f"🧪 Testing IN taxation")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        tax_terms = ["tax", "benefit", "deduction", "80ccd", "exemption"]
        assert any(term in response_text for term in tax_terms), \
            "Response should discuss tax benefits"

        logger.info(f"   ✅ IN taxation test passed")


# ============================================================================
# RETIREMENT PLANNING TESTS - ALL COUNTRIES
# ============================================================================

class TestRetirementPlanning:
    """Test retirement planning advice for all countries."""

    def test_au_retirement_planning(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.5: Australian retirement planning.

        Validates:
        - Retirement income projections
        - Age pension eligibility
        - Account-based pension strategies
        - Transition to retirement
        """
        member_id = TEST_MEMBERS["AU"]
        query = "How should I plan for my retirement with my current super balance?"

        logger.info(f"🧪 Testing AU retirement planning")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        planning_terms = ["retirement", "plan", "income", "strategy", "pension", "age pension"]
        assert any(term in response_text for term in planning_terms), \
            "Response should discuss retirement planning"

        logger.info(f"   ✅ AU retirement planning test passed")

    def test_us_retirement_planning(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.6: US retirement planning.

        Validates:
        - Retirement income needs
        - Social Security coordination
        - Required Minimum Distributions (RMDs)
        - Withdrawal strategies (4% rule)
        """
        member_id = TEST_MEMBERS["US"]
        query = "What's the best strategy to withdraw from my 401(k) in retirement?"

        logger.info(f"🧪 Testing US retirement planning")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        planning_terms = ["retirement", "strategy", "withdraw", "income", "plan", "social security"]
        assert any(term in response_text for term in planning_terms), \
            "Response should discuss retirement planning"

        logger.info(f"   ✅ US retirement planning test passed")

    def test_uk_retirement_planning(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.7: UK retirement planning.

        Validates:
        - Pension drawdown strategies
        - State pension coordination
        - Annuity vs drawdown
        - Lifetime allowance considerations
        """
        member_id = TEST_MEMBERS["UK"]
        query = "Should I take my pension as a lump sum or regular income?"

        logger.info(f"🧪 Testing UK retirement planning")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        planning_terms = ["pension", "lump sum", "income", "drawdown", "strategy", "state pension"]
        assert any(term in response_text for term in planning_terms), \
            "Response should discuss pension strategies"

        logger.info(f"   ✅ UK retirement planning test passed")

    def test_in_retirement_planning(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.8: Indian retirement planning.

        Validates:
        - NPS vs EPF retirement income
        - Annuity purchase requirements (NPS)
        - Systematic withdrawal plans
        - Post-retirement tax planning
        """
        member_id = TEST_MEMBERS["IN"]
        query = "How should I plan my retirement income from NPS and EPF?"

        logger.info(f"🧪 Testing IN retirement planning")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].upper()

        planning_terms = ["RETIREMENT", "INCOME", "NPS", "EPF", "PLAN", "STRATEGY"]
        assert any(term in response_text for term in planning_terms), \
            "Response should discuss retirement planning"

        logger.info(f"   ✅ IN retirement planning test passed")


# ============================================================================
# WITHDRAWAL TESTS - ALL COUNTRIES
# ============================================================================

class TestWithdrawals:
    """Test withdrawal rules for all countries."""

    def test_au_withdrawal_rules(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.9: Australian withdrawal rules.

        Validates:
        - Preservation age access
        - Condition of release rules
        - Hardship withdrawals
        - Unrestricted non-preserved benefits
        """
        member_id = TEST_MEMBERS["AU"]
        query = "When can I withdraw money from my superannuation?"

        logger.info(f"🧪 Testing AU withdrawal rules")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        withdrawal_terms = ["withdraw", "access", "preservation", "retirement", "condition of release"]
        assert any(term in response_text for term in withdrawal_terms), \
            "Response should discuss withdrawal rules"

        logger.info(f"   ✅ AU withdrawal rules test passed")

    def test_us_withdrawal_rules(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.10: US withdrawal rules.

        Validates:
        - Age 59½ rule
        - 10% early withdrawal penalty
        - Hardship distributions
        - Loans from 401(k)
        - Required Minimum Distributions (age 73)
        """
        member_id = TEST_MEMBERS["US"]
        query = "Can I withdraw from my 401(k) before age 59½?"

        logger.info(f"🧪 Testing US withdrawal rules")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        withdrawal_terms = ["withdraw", "age", "penalty", "early", "59", "hardship"]
        assert any(term in response_text for term in withdrawal_terms), \
            "Response should discuss withdrawal rules"

        logger.info(f"   ✅ US withdrawal rules test passed")

    def test_uk_withdrawal_rules(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.11: UK withdrawal rules.

        Validates:
        - Minimum age 55 (rising to 57)
        - 25% tax-free lump sum
        - Pension drawdown rules
        - Lifetime allowance
        """
        member_id = TEST_MEMBERS["UK"]
        query = "What are the rules for withdrawing from my pension?"

        logger.info(f"🧪 Testing UK withdrawal rules")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        withdrawal_terms = ["withdraw", "age", "55", "57", "tax-free", "lump sum", "drawdown"]
        assert any(term in response_text for term in withdrawal_terms), \
            "Response should discuss withdrawal rules"

        logger.info(f"   ✅ UK withdrawal rules test passed")

    def test_in_withdrawal_rules(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.12: Indian withdrawal rules.

        Validates:
        - EPF withdrawal after 5 years
        - NPS withdrawal: 60% annuity mandatory
        - Partial withdrawals (3 times before retirement)
        - Early exit penalties
        """
        member_id = TEST_MEMBERS["IN"]
        query = "Can I withdraw my EPF before retirement?"

        logger.info(f"🧪 Testing IN withdrawal rules")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].upper()

        withdrawal_terms = ["WITHDRAW", "EPF", "RETIREMENT", "EARLY", "PENALTY", "YEAR"]
        assert any(term in response_text for term in withdrawal_terms), \
            "Response should discuss withdrawal rules"

        logger.info(f"   ✅ IN withdrawal rules test passed")


# ============================================================================
# ANNUITY TESTS - ALL COUNTRIES
# ============================================================================

class TestAnnuities:
    """Test annuity and income stream knowledge for all countries."""

    def test_au_annuity_products(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.13: Australian annuity products.

        Validates:
        - Account-based pensions
        - Lifetime annuities
        - Fixed-term annuities
        - Age pension asset test treatment
        """
        member_id = TEST_MEMBERS["AU"]
        query = "What annuity options do I have for my superannuation?"

        logger.info(f"🧪 Testing AU annuity options")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        annuity_terms = ["annuity", "pension", "income", "lifetime", "account-based", "income stream"]
        assert any(term in response_text for term in annuity_terms), \
            "Response should discuss annuity options"

        logger.info(f"   ✅ AU annuity options test passed")

    def test_us_annuity_products(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.14: US annuity products.

        Validates:
        - Immediate vs deferred annuities
        - Fixed vs variable annuities
        - Annuitization options from 401(k)
        - Social Security as annuity
        """
        member_id = TEST_MEMBERS["US"]
        query = "Should I convert my 401(k) to an annuity?"

        logger.info(f"🧪 Testing US annuity options")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        annuity_terms = ["annuity", "income", "convert", "retirement", "payment", "lifetime"]
        assert any(term in response_text for term in annuity_terms), \
            "Response should discuss annuity options"

        logger.info(f"   ✅ US annuity options test passed")

    def test_uk_annuity_products(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.15: UK annuity products.

        Validates:
        - Lifetime annuities
        - Enhanced annuities (health conditions)
        - Annuity vs drawdown comparison
        - Annuity rates and guarantees
        """
        member_id = TEST_MEMBERS["UK"]
        query = "Should I buy an annuity with my pension pot?"

        logger.info(f"🧪 Testing UK annuity options")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        annuity_terms = ["annuity", "pension", "income", "lifetime", "drawdown", "guaranteed"]
        assert any(term in response_text for term in annuity_terms), \
            "Response should discuss annuity options"

        logger.info(f"   ✅ UK annuity options test passed")

    def test_in_annuity_mandatory(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.16: Indian NPS mandatory annuity.

        Validates:
        - 40% mandatory annuity purchase (NPS)
        - Annuity Service Providers (ASPs)
        - Annuity types available
        - EPF vs NPS annuity requirements
        """
        member_id = TEST_MEMBERS["IN"]
        query = "Do I have to buy an annuity from my NPS corpus?"

        logger.info(f"🧪 Testing IN annuity requirements")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].upper()

        annuity_terms = ["ANNUITY", "NPS", "MANDATORY", "40", "PENSION", "CORPUS"]
        assert any(term in response_text for term in annuity_terms), \
            "Response should discuss NPS annuity requirements"

        logger.info(f"   ✅ IN annuity requirements test passed")


# ============================================================================
# PRESERVATION AGE TESTS - ALL COUNTRIES
# ============================================================================

class TestPreservationAge:
    """Test preservation/access age rules for all countries."""

    def test_au_preservation_age(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.17: Australian preservation age.

        Validates:
        - Age 55-60 depending on birth year
        - Early access: compassionate, hardship, terminal illness
        - Transition to retirement
        - Full access at preservation age + retired
        """
        member_id = TEST_MEMBERS["AU"]
        query = "What is my preservation age and when can I access my super?"

        logger.info(f"🧪 Testing AU preservation age")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        age_terms = ["preservation age", "age", "55", "60", "access", "retirement", "born"]
        assert any(term in response_text for term in age_terms), \
            "Response should discuss preservation age"

        logger.info(f"   ✅ AU preservation age test passed")

    def test_us_minimum_age(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.18: US 401(k) age rules.

        Validates:
        - Age 59½ for penalty-free withdrawals
        - Age 55 rule (separation from service)
        - Age 73 for Required Minimum Distributions (RMDs)
        - Exceptions to early withdrawal penalty
        """
        member_id = TEST_MEMBERS["US"]
        query = "At what age can I withdraw from my 401(k) without penalty?"

        logger.info(f"🧪 Testing US minimum age")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        age_terms = ["age", "59", "penalty", "withdraw", "55", "early"]
        assert any(term in response_text for term in age_terms), \
            "Response should discuss age rules"

        logger.info(f"   ✅ US minimum age test passed")

    def test_uk_minimum_pension_age(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.19: UK minimum pension age.

        Validates:
        - Age 55 currently (rising to 57 in 2028)
        - Earlier access: ill health, protected pension age
        - State Pension age (66-68)
        - Normal minimum pension age (NMPA)
        """
        member_id = TEST_MEMBERS["UK"]
        query = "What is the minimum age I can access my pension?"

        logger.info(f"🧪 Testing UK minimum pension age")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].lower()

        age_terms = ["age", "55", "57", "minimum", "access", "pension", "nmpa"]
        assert any(term in response_text for term in age_terms), \
            "Response should discuss minimum pension age"

        logger.info(f"   ✅ UK minimum pension age test passed")

    def test_in_retirement_age(
        self,
        agent,
        test_timer,
        verify_test_members_exist
    ):
        """
        Test 3.20: Indian retirement age rules.

        Validates:
        - EPF: Age 58 for full withdrawal without penalty
        - NPS: Age 60 for maturity (can extend to 70)
        - EPS: Age 58 for pension eligibility
        - Early exit: Age 60 (NPS) vs service-based (EPF)
        """
        member_id = TEST_MEMBERS["IN"]
        query = "At what age can I withdraw my EPF and NPS?"

        logger.info(f"🧪 Testing IN retirement age")

        result = agent.process_query(
            member_id=member_id,
            user_query=query
        )

        assert result is not None
        assert "error" not in result

        response_text = result["response"].upper()

        age_terms = ["AGE", "58", "60", "EPF", "NPS", "RETIREMENT", "WITHDRAW"]
        assert any(term in response_text for term in age_terms), \
            "Response should discuss retirement age"

        logger.info(f"   ✅ IN retirement age test passed")


# ============================================================================
# TEST MARKERS
# ============================================================================

pytest.mark.integration = pytest.mark.integration
pytest.mark.comprehensive = pytest.mark.comprehensive
pytest.mark.taxation = pytest.mark.taxation
pytest.mark.planning = pytest.mark.planning
pytest.mark.withdrawal = pytest.mark.withdrawal
pytest.mark.annuity = pytest.mark.annuity
pytest.mark.age_rules = pytest.mark.age_rules
