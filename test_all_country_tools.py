#!/usr/bin/env python3
"""
Comprehensive tool invocation tests for all countries.
Tests that tools are actually called and return valid results.
"""

from agent_processor import agent_query
import uuid
import json
from datetime import datetime

# Test cases: (country, member_id, query, expected_tools)
TEST_CASES = [
    # AUSTRALIA TESTS
    {
        "country": "AU",
        "member_id": "AU015",  # David Kim, age 55, $892k
        "name": "David Kim",
        "query": "What tax will I pay if I withdraw $50,000 from my super?",
        "expected_tools": ["tax"],
        "description": "AU tax calculation"
    },
    {
        "country": "AU",
        "member_id": "AU008",  # Michelle Brown, age 62
        "name": "Michelle Brown",
        "query": "Will withdrawing money affect my Centrelink pension?",
        "expected_tools": ["benefit"],
        "description": "AU pension impact"
    },
    {
        "country": "AU",
        "member_id": "AU015",
        "name": "David Kim",
        "query": "How much super will I have when I retire at 65?",
        "expected_tools": ["projection"],
        "description": "AU projection"
    },

    # USA TESTS
    {
        "country": "US",
        "member_id": "US001",
        "name": "Robert Smith",
        "query": "What tax will I pay if I withdraw $30,000 from my 401k?",
        "expected_tools": ["tax"],
        "description": "US 401k tax calculation"
    },
    {
        "country": "US",
        "member_id": "US002",
        "name": "Linda Johnson",
        "query": "What Social Security benefits am I eligible for?",
        "expected_tools": ["benefit"],
        "description": "US Social Security benefits"
    },
    {
        "country": "US",
        "member_id": "US001",
        "name": "Robert Smith",
        "query": "How much will my 401k grow by retirement?",
        "expected_tools": ["projection"],
        "description": "US 401k projection"
    },

    # UK TESTS
    {
        "country": "UK",
        "member_id": "UK001",
        "name": "James Wilson",
        "query": "What tax will I pay on a £25,000 pension withdrawal?",
        "expected_tools": ["tax"],
        "description": "UK pension tax calculation"
    },
    {
        "country": "UK",
        "member_id": "UK002",
        "name": "Emma Thompson",
        "query": "Am I eligible for the State Pension?",
        "expected_tools": ["benefit"],
        "description": "UK State Pension eligibility"
    },
    {
        "country": "UK",
        "member_id": "UK001",
        "name": "James Wilson",
        "query": "How much will my pension be worth at retirement?",
        "expected_tools": ["projection"],
        "description": "UK pension projection"
    },

    # INDIA TESTS
    {
        "country": "IN",
        "member_id": "IN001",
        "name": "Rajesh Kumar",
        "query": "What tax will I pay on EPF withdrawal?",
        "expected_tools": ["tax"],
        "description": "India EPF tax calculation"
    },
    {
        "country": "IN",
        "member_id": "IN002",
        "name": "Priya Sharma",
        "query": "What NPS benefits and pension will I receive?",
        "expected_tools": ["benefit"],
        "description": "India NPS benefits"
    },
    {
        "country": "IN",
        "member_id": "IN001",
        "name": "Rajesh Kumar",
        "query": "What EPS pension am I eligible for?",
        "expected_tools": ["eps_benefit"],
        "description": "India EPS pension"
    },
    {
        "country": "IN",
        "member_id": "IN001",
        "name": "Rajesh Kumar",
        "query": "How much will my EPF and NPS grow by retirement?",
        "expected_tools": ["projection"],
        "description": "India retirement corpus projection"
    },
]


def run_test(test_case):
    """Run a single test case and return results."""
    country = test_case["country"]
    member_id = test_case["member_id"]
    query = test_case["query"]
    expected_tools = test_case["expected_tools"]
    description = test_case["description"]
    name = test_case["name"]

    session_id = str(uuid.uuid4())

    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"Country: {country}")
    print(f"Member: {name} ({member_id})")
    print(f"Query: {query}")
    print(f"Expected Tools: {', '.join(expected_tools)}")
    print(f"{'-'*80}")

    try:
        result = agent_query(
            user_id=member_id,
            session_id=session_id,
            country=country,
            query_string=query,
            validation_mode="llm",
            enable_observability=False
        )

        # Check if error
        if result.get('error'):
            print(f"❌ FAILED: {result['error']}")
            return {
                "test": description,
                "country": country,
                "member": name,
                "status": "FAILED",
                "error": result['error'],
                "tools_called": [],
                "expected_tools": expected_tools
            }

        # Check tools called
        tools_called = result.get('tools_called', [])
        validation = result.get('judge_verdict', {})
        cost = result.get('cost', 0)

        # Check if expected tools were called
        tools_match = set(expected_tools).issubset(set(tools_called))
        validation_passed = validation.get('passed', False)

        if tools_match and validation_passed:
            status = "✅ PASSED"
            test_status = "PASSED"
        elif tools_match and not validation_passed:
            status = "⚠️  PARTIAL (tools called but validation failed)"
            test_status = "PARTIAL"
        else:
            status = "❌ FAILED (wrong tools called)"
            test_status = "FAILED"

        print(f"\nStatus: {status}")
        print(f"Tools Called: {', '.join(tools_called) if tools_called else 'None'}")
        print(f"Validation: {validation.get('verdict', 'N/A')} ({validation.get('confidence', 0):.0%})")
        print(f"Cost: ${cost:.6f}")

        # Show response snippet
        answer = result.get('answer', '')
        if answer:
            snippet = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"\nResponse snippet: {snippet}")

        return {
            "test": description,
            "country": country,
            "member": name,
            "status": test_status,
            "tools_called": tools_called,
            "expected_tools": expected_tools,
            "validation": validation.get('verdict', 'N/A'),
            "confidence": validation.get('confidence', 0),
            "cost": cost
        }

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test": description,
            "country": country,
            "member": name,
            "status": "EXCEPTION",
            "error": str(e),
            "tools_called": [],
            "expected_tools": expected_tools
        }


def main():
    """Run all tests and generate summary report."""
    print("\n" + "="*80)
    print("COMPREHENSIVE TOOL INVOCATION TESTS")
    print("Testing all countries: AU, US, UK, IN")
    print("Testing all tool types: tax, benefit, projection, eps_benefit")
    print("="*80)

    results = []
    start_time = datetime.now()

    for test_case in TEST_CASES:
        result = run_test(test_case)
        results.append(result)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Generate summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r["status"] == "PASSED")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"] in ["FAILED", "EXCEPTION"])
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"⚠️  Partial: {partial}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Total Duration: {duration:.1f}s")

    # Breakdown by country
    print(f"\n{'-'*80}")
    print("BREAKDOWN BY COUNTRY")
    print(f"{'-'*80}")

    for country in ["AU", "US", "UK", "IN"]:
        country_results = [r for r in results if r["country"] == country]
        country_passed = sum(1 for r in country_results if r["status"] == "PASSED")
        country_total = len(country_results)
        print(f"{country}: {country_passed}/{country_total} passed")

    # Failed tests detail
    failed_tests = [r for r in results if r["status"] in ["FAILED", "EXCEPTION"]]
    if failed_tests:
        print(f"\n{'-'*80}")
        print("FAILED TESTS DETAIL")
        print(f"{'-'*80}")
        for test in failed_tests:
            print(f"\n❌ {test['test']} ({test['country']})")
            print(f"   Member: {test['member']}")
            print(f"   Expected tools: {', '.join(test['expected_tools'])}")
            print(f"   Tools called: {', '.join(test['tools_called']) if test['tools_called'] else 'None'}")
            if 'error' in test:
                print(f"   Error: {test['error']}")

    # Tool invocation stats
    print(f"\n{'-'*80}")
    print("TOOL INVOCATION STATISTICS")
    print(f"{'-'*80}")

    all_tools = {}
    for result in results:
        for tool in result['tools_called']:
            country = result['country']
            key = f"{country}:{tool}"
            all_tools[key] = all_tools.get(key, 0) + 1

    for country in ["AU", "US", "UK", "IN"]:
        print(f"\n{country}:")
        country_tools = {k: v for k, v in all_tools.items() if k.startswith(f"{country}:")}
        for tool, count in sorted(country_tools.items()):
            print(f"  {tool}: {count} invocation(s)")

    # Save detailed results
    results_file = "test_results_all_countries.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total": total,
                "passed": passed,
                "partial": partial,
                "failed": failed,
                "success_rate": (passed/total)*100
            },
            "results": results
        }, f, indent=2)

    print(f"\n{'-'*80}")
    print(f"Detailed results saved to: {results_file}")
    print("="*80 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
