#!/usr/bin/env python3
"""
Simple test script for GPT OSS 120B classifier endpoint
Tests if the endpoint is working correctly for classification
"""

import json
import re
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

def test_gpt_oss_endpoint():
    """Test GPT OSS endpoint directly"""
    print("=" * 70)
    print("🧪 Testing GPT OSS 120B Endpoint")
    print("=" * 70)
    print()
    
    w = WorkspaceClient()
    endpoint_name = "databricks-gpt-oss-120b"
    
    # Test query
    test_query = "What's the maximum amount I can withdraw from my superannuation this year?"
    
    classification_prompt = f"""You are a retirement advisory classifier.

Determine if this query is about retirement/pensions/superannuation OR off-topic.

USER QUERY: "{test_query}"

RETIREMENT TOPICS:
- Retirement accounts: 401k, IRA, Superannuation, EPF, NPS, SIPP, pension
- Withdrawals, early access, hardship
- Tax on retirement withdrawals
- Benefits, projections, contributions
- Retirement planning advice

OFF-TOPIC EXAMPLES:
- General finance (loans, mortgages, credit cards, savings accounts)
- Investments (stocks, crypto, real estate - unless retirement-specific)
- General questions (weather, cooking, sports, entertainment)
- Technical support (login, password reset)

IMPORTANT: "Retirement party" or "retirement gift" = OFF-TOPIC (social events, not financial)

Respond in JSON:
{{
    "classification": "retirement_query" or "off_topic",
    "confidence": 0.0 to 1.0,
    "reasoning": "one sentence"
}}"""
    
    try:
        print(f"📡 Calling endpoint: {endpoint_name}")
        print(f"📝 Query: {test_query}")
        print()
        
        response = w.serving_endpoints.query(
            name=endpoint_name,
            messages=[
                ChatMessage(role=ChatMessageRole.USER, content=classification_prompt)
            ],
            max_tokens=150,
            temperature=0.0
        )
        
        print("✅ Endpoint responded!")
        print()
        
        # Check response structure
        print("📊 Response Structure:")
        print(f"   Type: {type(response)}")
        print(f"   Has 'choices': {hasattr(response, 'choices')}")
        
        if hasattr(response, 'choices') and len(response.choices) > 0:
            message = response.choices[0].message
            print(f"   Message type: {type(message)}")
            print(f"   Has 'content': {hasattr(message, 'content')}")
            
            if hasattr(message, 'content'):
                content = message.content
                print(f"   Content type: {type(content)}")
                print(f"   Content value: {repr(content)}")
                print()
                
                # Handle different content types
                if isinstance(content, list):
                    print("⚠️  Content is a LIST - extracting text chunks")
                    # Extract only 'text' type chunks
                    text_chunks = []
                    for chunk in content:
                        if isinstance(chunk, dict):
                            if chunk.get('type') == 'text' and 'text' in chunk:
                                print(f"   Found 'text' chunk: {chunk['text'][:50]}...")
                                text_chunks.append(chunk['text'])
                            elif 'text' in chunk:
                                print(f"   Found chunk with 'text' key: {chunk['text'][:50]}...")
                                text_chunks.append(chunk['text'])
                            else:
                                print(f"   Skipping chunk type: {chunk.get('type', 'unknown')}")
                        else:
                            text_chunks.append(str(chunk))
                    response_text = ' '.join(text_chunks)
                elif isinstance(content, str):
                    print("✅ Content is a STRING")
                    response_text = content
                else:
                    print(f"⚠️  Content is {type(content)} - converting to string")
                    response_text = str(content)
                
                print()
                print("📄 Response Text:")
                print("-" * 70)
                print(response_text)
                print("-" * 70)
                print()
                
                # Try to extract JSON
                try:
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                        print("✅ Successfully parsed JSON!")
                        print(f"   Classification: {result.get('classification')}")
                        print(f"   Confidence: {result.get('confidence')}")
                        print(f"   Reasoning: {result.get('reasoning')}")
                    else:
                        print("❌ No JSON found in response")
                        print("   Trying to parse entire response as JSON...")
                        result = json.loads(response_text)
                        print("✅ Successfully parsed entire response as JSON!")
                        print(f"   Result: {result}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print("   Response might not be valid JSON")
            else:
                print("❌ Message has no 'content' attribute")
                print(f"   Available attributes: {dir(message)}")
        else:
            print("❌ No choices in response")
            print(f"   Response: {response}")
            
    except Exception as e:
        print(f"❌ Error calling endpoint: {e}")
        print()
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False
    
    print()
    print("=" * 70)
    print("✅ Test completed!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    test_gpt_oss_endpoint()

