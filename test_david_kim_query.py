#!/usr/bin/env python3
"""Test query for David Kim: Early super access question."""

from agent_processor import agent_query
import uuid

# Test parameters
member_id = "AU015"  # David Kim
session_id = str(uuid.uuid4())
country = "AU"
query = "Can I access my super early for medical reasons or financial hardship?"

print("\n" + "="*80)
print("TESTING AGENT QUERY")
print("="*80)
print(f"Member ID: {member_id} (David Kim)")
print(f"Session ID: {session_id}")
print(f"Country: {country}")
print(f"Query: {query}")
print("="*80 + "\n")

try:
    result = agent_query(
        user_id=member_id,
        session_id=session_id,
        country=country,
        query_string=query,
        validation_mode="llm",
        enable_observability=False
    )

    print("\n" + "="*80)
    print("RESULT")
    print("="*80)

    if result.get('error'):
        print(f"\n❌ ERROR: {result['error']}")
    else:
        print(f"\n✅ Response received:")
        print("-" * 80)
        print(result['answer'])
        print("-" * 80)

        print(f"\n📊 Metadata:")
        print(f"   Tools called: {', '.join(result['tools_called']) if result['tools_called'] else 'None'}")
        print(f"   Cost: ${result['cost']:.6f}")
        print(f"   Validation: {result['judge_verdict']['verdict']} ({result['judge_verdict']['confidence']:.0%} confidence)")

        if result.get('citations'):
            print(f"\n📚 Citations: {len(result['citations'])} citation(s)")

    print("\n" + "="*80)

except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
