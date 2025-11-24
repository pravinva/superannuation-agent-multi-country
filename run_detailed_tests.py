"""
Detailed Test Runner with LLM Response and Judge Verdict Capture
================================================================

Runs integration tests and captures:
1. Query asked
2. Actual LLM response
3. Judge verdict (PASS/FAIL)
4. Validation details
5. Tool execution results
6. Cost and performance metrics
"""

import sys
import os
import json
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_config import *
from agent import SuperAdvisorAgent
from shared.logging_config import get_logger

logger = get_logger(__name__)

def run_detailed_test(member_id, query, test_name):
    """Run a single test and capture all details."""

    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"Member ID: {member_id}")
    print(f"Query: {query}")
    print(f"{'-'*80}")

    # Initialize agent
    agent = SuperAdvisorAgent()

    # Execute query
    start_time = datetime.now()
    result = agent.process_query(
        member_id=member_id,
        user_query=query
    )
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Extract key information
    response_text = result.get("response", "NO RESPONSE")
    classification = result.get("classification", {})
    validation = result.get("validation", {})
    tools_used = result.get("tools_used", [])
    attempts = result.get("attempts", 0)
    cost = sum([r.get("cost", 0) for r in result.get("synthesis_results", [])])

    # Display results
    print(f"\n📊 CLASSIFICATION:")
    print(f"   Method: {classification.get('method', 'N/A')}")
    print(f"   Classification: {classification.get('classification', 'N/A')}")
    print(f"   Confidence: {classification.get('confidence', 0):.2f}")

    print(f"\n🔧 TOOLS USED: {', '.join(tools_used) if tools_used else 'None'}")

    print(f"\n📝 LLM RESPONSE:")
    print(f"{'-'*80}")
    print(response_text)
    print(f"{'-'*80}")

    print(f"\n⚖️ VALIDATION / JUDGE VERDICT:")
    if validation:
        passed = validation.get("passed", False)
        confidence = validation.get("confidence", 0)
        violations = validation.get("violations", [])
        validator_used = validation.get("_validator_used", "N/A")

        verdict = "✅ PASS" if passed else "❌ FAIL"
        print(f"   Verdict: {verdict}")
        print(f"   Validator: {validator_used}")
        print(f"   Confidence: {confidence:.2f}")

        if violations:
            print(f"   Violations: {len(violations)}")
            for v in violations:
                print(f"      - [{v.get('severity', 'N/A')}] {v.get('code', 'N/A')}: {v.get('detail', 'N/A')}")
        else:
            print(f"   Violations: None")
    else:
        print(f"   No validation information available")

    print(f"\n💰 METRICS:")
    print(f"   Attempts: {attempts}")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Cost: ${cost:.4f}")

    # Return test result
    test_passed = "error" not in result and len(response_text) > 0
    return {
        "test_name": test_name,
        "member_id": member_id,
        "query": query,
        "passed": test_passed,
        "response": response_text,
        "validation": validation,
        "classification": classification,
        "tools_used": tools_used,
        "attempts": attempts,
        "duration": duration,
        "cost": cost
    }

def main():
    """Run all critical tests with detailed output."""

    print(f"\n{'#'*80}")
    print(f"# DETAILED INTEGRATION TEST EXECUTION")
    print(f"# Running tests with REAL LLM calls and REAL judge verdicts")
    print(f"# Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")

    test_results = []

    # Test 1: Australia - Balance Inquiry
    result = run_detailed_test(
        member_id=TEST_MEMBERS["AU"],
        query="What's my current superannuation balance?",
        test_name="1. AU Balance Inquiry"
    )
    test_results.append(result)

    # Test 2: Australia - Taxation
    result = run_detailed_test(
        member_id=TEST_MEMBERS["AU"],
        query="What tax do I pay on my superannuation withdrawals?",
        test_name="2. AU Taxation"
    )
    test_results.append(result)

    # Test 3: United States - 401(k) Balance
    result = run_detailed_test(
        member_id=TEST_MEMBERS["US"],
        query="What's my 401(k) balance?",
        test_name="3. US 401(k) Balance"
    )
    test_results.append(result)

    # Test 4: United States - Early Withdrawal
    result = run_detailed_test(
        member_id=TEST_MEMBERS["US"],
        query="Can I withdraw from my 401(k) before age 59½?",
        test_name="4. US Early Withdrawal"
    )
    test_results.append(result)

    # Test 5: United Kingdom - Pension Balance
    result = run_detailed_test(
        member_id=TEST_MEMBERS["UK"],
        query="What's my pension balance?",
        test_name="5. UK Pension Balance"
    )
    test_results.append(result)

    # Test 6: India - NPS Balance
    result = run_detailed_test(
        member_id=TEST_MEMBERS["IN"],
        query="What's my NPS balance?",
        test_name="6. IN NPS Balance"
    )
    test_results.append(result)

    # Test 7: India - EPF vs NPS
    result = run_detailed_test(
        member_id=TEST_MEMBERS["IN"],
        query="What's the difference between NPS and EPF?",
        test_name="7. IN NPS vs EPF"
    )
    test_results.append(result)

    # Summary
    print(f"\n{'='*80}")
    print(f"TEST EXECUTION SUMMARY")
    print(f"{'='*80}")

    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["passed"])
    total_duration = sum(r["duration"] for r in test_results)
    total_cost = sum(r["cost"] for r in test_results)

    print(f"\nTotal Tests Run: {total_tests}")
    print(f"Tests Passed: {passed_tests}")
    print(f"Tests Failed: {total_tests - passed_tests}")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Pass Rate: {(passed_tests/total_tests)*100:.1f}%")

    print(f"\nDetailed Results:")
    for i, result in enumerate(test_results, 1):
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"  {i}. {result['test_name']}: {status}")

    # Save results to JSON
    output_file = "test_results_detailed.json"
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\n📄 Detailed results saved to: {output_file}")

    print(f"\n{'#'*80}")
    print(f"# TEST EXECUTION COMPLETE")
    print(f"# End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}\n")

    return test_results

if __name__ == "__main__":
    main()
