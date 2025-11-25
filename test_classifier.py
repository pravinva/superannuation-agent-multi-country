#!/usr/bin/env python3
"""
Test script for EmbeddingCascadeClassifier
Tests all 3 stages: Regex, Embedding, and LLM fallback
"""

from classifier import EmbeddingCascadeClassifier
from prompts_registry import get_prompts_registry

def test_classifier():
    """Test the cascade classifier with various queries."""
    
    print("=" * 70)
    print("🧪 TESTING EMBEDDING CASCADE CLASSIFIER")
    print("=" * 70)
    
    # Initialize classifier
    prompts_registry = get_prompts_registry(enable_mlflow=False)
    classifier = EmbeddingCascadeClassifier(
        prompts_registry=prompts_registry,
        enable_cache=True
    )
    
    # Test queries - Expected to be caught by different stages
    test_cases = [
        # Stage 1: Should be caught by regex
        {
            "query": "How much can I withdraw from my 401k?",
            "expected_stage": "regex_fast_path",
            "expected_on_topic": True,
            "description": "Clear retirement query - 401k"
        },
        {
            "query": "What's my superannuation balance?",
            "expected_stage": "regex_fast_path",
            "expected_on_topic": True,
            "description": "Clear retirement query - super"
        },
        {
            "query": "Tell me a joke",
            "expected_stage": "regex_fast_path",
            "expected_on_topic": False,
            "description": "Clear off-topic - joke"
        },
        {
            "query": "What's the weather today?",
            "expected_stage": "regex_fast_path",
            "expected_on_topic": False,
            "description": "Clear off-topic - weather"
        },
        
        # Stage 2: Should fall through to embedding
        {
            "query": "Can I access my retirement funds early?",
            "expected_stage": "embedding_similarity",
            "expected_on_topic": True,
            "description": "Retirement query without exact keywords"
        },
        {
            "query": "How much will I get when I stop working?",
            "expected_stage": "embedding_similarity",
            "expected_on_topic": True,
            "description": "Retirement query - natural language"
        },
        
        # Stage 3: Should require LLM
        {
            "query": "Can I use my savings to buy a boat?",
            "expected_stage": "llm_fallback",
            "expected_on_topic": False,
            "description": "Ambiguous - general savings (not retirement)"
        },
        {
            "query": "What should I get for a retirement party?",
            "expected_stage": "llm_fallback",
            "expected_on_topic": False,
            "description": "Tricky - has 'retirement' but is about party planning"
        },
        
        # Edge cases
        {
            "query": "How does EPF work in India?",
            "expected_stage": "regex_fast_path",
            "expected_on_topic": True,
            "description": "India-specific retirement scheme"
        },
        {
            "query": "Should I consolidate my retirement accounts?",
            "expected_stage": "regex_fast_path",
            "expected_on_topic": True,
            "description": "Retirement planning advice"
        },
    ]
    
    print(f"\n📝 Running {len(test_cases)} test cases...\n")
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_stage = test_case["expected_stage"]
        expected_on_topic = test_case["expected_on_topic"]
        description = test_case["description"]
        
        print(f"\n{'=' * 70}")
        print(f"Test {i}/{len(test_cases)}: {description}")
        print(f"Query: \"{query}\"")
        print("-" * 70)
        
        result = classifier.classify(query)
        
        actual_stage = result.get('method', 'unknown')
        actual_on_topic = result.get('is_on_topic', None)
        confidence = result.get('confidence', 0.0)
        latency = result.get('latency_ms', 0.0)
        cost = result.get('cost_usd', 0.0)
        
        print(f"Result:")
        print(f"  Classification: {result.get('classification', 'unknown')}")
        print(f"  On-Topic: {actual_on_topic}")
        print(f"  Method: {actual_stage}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Latency: {latency:.1f}ms")
        print(f"  Cost: ${cost:.6f}")
        
        # Check if test passed
        stage_match = actual_stage == expected_stage
        topic_match = actual_on_topic == expected_on_topic
        
        if topic_match:
            print(f"✅ PASSED - Correctly classified as {'on-topic' if expected_on_topic else 'off-topic'}")
            passed += 1
        else:
            print(f"❌ FAILED - Expected: {expected_on_topic}, Got: {actual_on_topic}")
            failed += 1
        
        if not stage_match:
            print(f"⚠️  Stage mismatch - Expected: {expected_stage}, Got: {actual_stage}")
    
    # Print metrics
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed} ({passed/len(test_cases)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(test_cases)*100:.1f}%)")
    
    # Print classifier metrics
    classifier.print_metrics()
    
    return passed == len(test_cases)


if __name__ == "__main__":
    try:
        success = test_classifier()
        
        if success:
            print("\n✅ ALL TESTS PASSED!")
            exit(0)
        else:
            print("\n⚠️  SOME TESTS FAILED")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

