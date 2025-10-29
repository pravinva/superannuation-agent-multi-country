#!/usr/bin/env python3

# validation.py - COMPLETE WITH TOOL FAILURE DETECTION + SCOPE ADHERENCE

# ✅ Judge sees FULL context including member_profile AND tool_output
# ✅ No more "invented data" false positives
# ✅ Understands that using member data is CORRECT
# ✅ Fixed indentation issues
# ✅ Added detailed violation debugging
# ✅ NOW TRACKS TOKENS AND CALCULATES COSTS!
# ✅ NEW: Detects and fails validation when tools error
# ✅ NEW: Recognizes that politely declining off-topic queries is CORRECT

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from config import JUDGE_LLM_ENDPOINT, JUDGE_LLM_TEMPERATURE, JUDGE_LLM_MAX_TOKENS, calculate_llm_cost
import json
import time
import re

class LLMJudgeValidator:
    """LLM-as-a-Judge validator using Claude for fair validation"""
    
    def __init__(self, judge_endpoint=None):
        self.w = WorkspaceClient()
        self.judge_endpoint = judge_endpoint or JUDGE_LLM_ENDPOINT
        
        # Determine model type from endpoint name for cost calculation
        if "opus" in self.judge_endpoint.lower():
            self.model_type = "claude-opus-4-1"
        elif "sonnet" in self.judge_endpoint.lower():
            self.model_type = "claude-sonnet-4"
        elif "haiku" in self.judge_endpoint.lower():
            self.model_type = "claude-haiku-4"
        else:
            self.model_type = "claude-sonnet-4"  # default
        
        print(f"✓ LLM Judge initialized: {self.judge_endpoint} (model: {self.model_type})")
    
    def validate(self, response_text, user_query, context, member_profile=None, tool_output=None):
        """Validate response - NOW RECEIVES MEMBER PROFILE AND TOOL OUTPUT"""
        
        # 🆕 NEW: Check for tool failures FIRST (deterministic check)
        if tool_output:
            failed_tools = [
                tool_name for tool_name, result in tool_output.items() 
                if isinstance(result, dict) and "error" in result
            ]
            
            if failed_tools:
                print(f"❌ TOOL FAILURE DETECTED: {', '.join(failed_tools)}")
                error_details = []
                for tool_name in failed_tools:
                    error_msg = tool_output[tool_name].get('error', 'Unknown error')
                    error_details.append(f"{tool_name}: {error_msg}")
                
                return {
                    "passed": False,
                    "confidence": 1.0,  # High confidence - deterministic check
                    "violations": [{
                        "code": "TOOL-EXECUTION-FAILED",
                        "severity": "CRITICAL",
                        "detail": f"Required calculation tools failed: {', '.join(failed_tools)}",
                        "evidence": error_details[0][:200] if error_details else "Tool execution error"
                    }],
                    "_validator_used": "DETERMINISTIC-TOOL-CHECK",
                    "reasoning": "Cannot validate response when underlying calculations failed",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0.0,
                    "model": "deterministic",
                    "duration": 0.0
                }
        
        try:
            print(f"\n📊 VALIDATION DEBUG:")
            print(f"📊 Full response length: {len(response_text)} chars")
            print(f"📊 Response starts with: {response_text[:150]}...")
            
            validation_prompt = self._build_validation_prompt(
                response_text, user_query, context, member_profile, tool_output
            )
            
            print(f"🧠 Calling judge LLM: {self.judge_endpoint}")
            
            messages = [
                ChatMessage(
                    role=ChatMessageRole.USER,
                    content=validation_prompt
                )
            ]
            
            start_time = time.time()
            response = self.w.serving_endpoints.query(
                name=self.judge_endpoint,
                messages=messages,
                max_tokens=JUDGE_LLM_MAX_TOKENS,
                temperature=JUDGE_LLM_TEMPERATURE
            )
            
            elapsed = time.time() - start_time
            
            # 🆕 EXTRACT TOKEN USAGE FROM RESPONSE
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'prompt_tokens', 0)
                output_tokens = getattr(response.usage, 'completion_tokens', 0)
                print(f"📊 Token usage: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} total")
            else:
                # Fallback: estimate tokens from character counts
                input_tokens = len(validation_prompt) // 4  # rough estimate: 4 chars per token
                output_tokens = 100  # conservative estimate for JSON output
                print(f"⚠️ Token usage not available, estimated: {input_tokens} input + {output_tokens} output")
            
            # 🆕 CALCULATE COST
            validation_cost = calculate_llm_cost(input_tokens, output_tokens, self.model_type)
            print(f"💰 Validation cost: ${validation_cost:.6f} ({self.model_type})")
            
            if hasattr(response, 'choices') and response.choices:
                judge_output = response.choices[0].message.content
            else:
                judge_output = str(response)
            
            print(f"⏱️ Judge validation took {elapsed:.2f} seconds")
            print(f"📝 Judge output length: {len(judge_output)} chars")
            
            # Try to parse JSON
            validation_result = self._parse_validation_response(judge_output)
            
            if validation_result:
                print(f"✅ USING LLM JUDGE RESULT - Passed: {validation_result['passed']}")
                
                # 🆕 ADD TOKEN COUNTS AND COST TO RESULT
                validation_result['input_tokens'] = input_tokens
                validation_result['output_tokens'] = output_tokens
                validation_result['total_tokens'] = input_tokens + output_tokens
                validation_result['cost'] = validation_cost
                validation_result['model'] = self.model_type
                validation_result['duration'] = elapsed
                
                # Print violations if any
                violations = validation_result.get('violations', [])
                if violations:
                    print(f"⚠️ VIOLATIONS FOUND ({len(violations)}):")
                    for i, v in enumerate(violations, 1):
                        print(f"  {i}. [{v.get('severity', 'UNKNOWN')}] {v.get('code', 'NO-CODE')}: {v.get('detail', 'No detail')}")
                        if v.get('evidence'):
                            print(f"     Evidence: {v.get('evidence', '')[:100]}")
                else:
                    print(f"✅ No violations found")
                
                return validation_result
            else:
                print(f"⚠️ LLM Judge JSON parsing FAILED - Falling back to keyword analysis")
                result = self._keyword_based_validation(response_text, user_query)
                result['_validator_used'] = 'KEYWORD_FALLBACK'
                
                # Add token/cost info even for fallback
                result['input_tokens'] = input_tokens
                result['output_tokens'] = output_tokens
                result['total_tokens'] = input_tokens + output_tokens
                result['cost'] = validation_cost
                result['model'] = self.model_type
                result['duration'] = elapsed
                
                return result
                
        except Exception as e:
            print(f"❌ Validation error: {e}")
            print(f"⚠️ FALLING BACK: Exception during LLM Judge")
            result = self._keyword_based_validation(response_text, user_query)
            result['_validator_used'] = 'FALLBACK_EXCEPTION'
            
            # Add zero cost for exception fallback
            result['input_tokens'] = 0
            result['output_tokens'] = 0
            result['total_tokens'] = 0
            result['cost'] = 0.0
            result['model'] = 'none'
            result['duration'] = 0.0
            
            return result
    
    def _build_validation_prompt(self, response_text, user_query, context, member_profile=None, tool_output=None):
        """Build validation prompt - NOW INCLUDES MEMBER PROFILE AND TOOL OUTPUT"""
        
        # Format member profile for clarity
        member_info = "NO MEMBER PROFILE PROVIDED"
        if member_profile:
            member_info = f"""
MEMBER PROFILE (for reference):
- Member ID: {member_profile.get('member_id', 'N/A')}
- Name: {member_profile.get('name', 'N/A')} (anonymized during processing)
- Age: {member_profile.get('age', 'N/A')}
- Country: {member_profile.get('country', 'N/A')}
- Preservation Age: {member_profile.get('preservation_age', 'N/A')}
- Employment Status: {member_profile.get('employment_status', 'N/A')}
- Super Balance: {member_profile.get('super_balance', 'N/A')}
- Other Assets: {member_profile.get('other_assets', 'N/A')}
- Dependents: {member_profile.get('dependents', 'N/A')}
"""
        
        # 🆕 NEW: Format tool output and detect failures
        tool_info = "NO TOOL CALCULATIONS PERFORMED"
        tool_failures = []
        if tool_output:
            tool_lines = ["TOOL CALCULATIONS & RESULTS (what the planning LLM received):"]
            for tool_name, tool_result in tool_output.items():
                if "error" in tool_result:
                    tool_lines.append(f"\n❌ Tool '{tool_name}' failed: {tool_result['error']}")
                    tool_failures.append(f"- {tool_name}: {tool_result['error']}")
                else:
                    tool_lines.append(f"\n✓ Tool: {tool_result.get('tool_name', tool_name)}")
                    tool_lines.append(f"  UC Function: {tool_result.get('uc_function', 'N/A')}")
                    tool_lines.append(f"  Authority: {tool_result.get('authority', 'N/A')}")
                    tool_lines.append(f"  Calculation Result: {tool_result.get('calculation', 'N/A')}")
                    if tool_result.get('citations'):
                        tool_lines.append(f"  Citations: {len(tool_result['citations'])} regulatory references")
            tool_info = "\n".join(tool_lines)
        
        # 🆕 NEW: Add tool status indicator
        tool_status = "✅ All tools executed successfully"
        if tool_failures:
            tool_status = f"❌ TOOL FAILURES DETECTED:\n" + "\n".join(tool_failures)
        
        prompt = f"""FAIR VALIDATION TASK: Analyze this retirement advice response thoroughly.

USER'S EXACT QUESTION: "{user_query}"

{member_info}

{tool_info}

{tool_status}

AI GENERATED RESPONSE (FULL {len(response_text)} CHARACTERS - REVIEW ENTIRE RESPONSE BELOW):
{response_text}

SYSTEM NOTE:
- Off-topic queries (vacation, food, general life advice) are filtered BEFORE reaching validation using ai_classify
- If you see a polite decline for non-retirement topics, this is CORRECT behavior and should PASS
- Only retirement-related queries should have tool calculations and detailed answers

VALIDATION CRITERIA (BE FAIR - REVIEW ENTIRE RESPONSE):

0. **TOOL EXECUTION**: If ANY tools failed (see above), response MUST fail validation with CRITICAL severity

0.5. **SCOPE ADHERENCE**: 
   - If question is about retirement/pensions/superannuation → response must answer it
   - If question is OFF-TOPIC (vacation, food, general advice) → politely declining is CORRECT
   - A polite decline that redirects to retirement topics should PASS validation
   - Only fail if response answers off-topic questions OR ignores in-scope retirement questions

1. **QUESTION ANSWERING**: Does the response adequately address the user's retirement question (IF in scope)?

2. **SPECIFICITY**: Does it provide specific numbers where appropriate?

3. **DATA USAGE**: Does it reference member data appropriately? (IMPORTANT: Using member's profile data is CORRECT, not an error)

4. **COMPLETENESS**: Does it address main aspects of the question?

5. **ACCURACY**: Are statements consistent with retirement rules?

IMPORTANT CLARIFICATIONS:
- The member profile ABOVE contains the member's actual data (age, balance, country, etc)
- The tool calculations ABOVE show the actual results from regulatory calculators
- Using this data in the response is CORRECT and EXPECTED
- If response says "you are age 52" and profile shows age=52, that's DATA USAGE, NOT INVENTION
- If response says "your balance is $X" and profile shows balance=$X, that's CORRECT, NOT MADE UP
- If response uses numbers from tool calculations, that's CORRECT, NOT INVENTED
- Only flag as "invented data" if response contains numbers/facts NOT in the member profile OR tool results

SEVERITY GUIDELINES - BE FAIR:
- CRITICAL: Only if major factual error that contradicts member's actual data OR if tools failed
- HIGH: If main retirement question completely unanswered (when it should be)
- MODERATE: If some details missing but main answer is there
- LOW: Minor style or formatting issues

RESPONSE PASSES if:
✓ All tools executed successfully (no errors)
✓ Answers the main retirement question asked (if in scope) OR politely declines if off-topic
✓ Uses member's provided profile data appropriately
✓ Uses tool calculation results appropriately
✓ Provides accurate information about retirement rules
✓ References member's age/balance when relevant
✓ Stays within retirement advisory scope

RESPONSE FAILS only if:
✗ Any calculation tools failed to execute
✗ Completely misses answering an IN-SCOPE retirement question
✗ Answers off-topic questions outside the retirement domain
✗ Contains major factual errors about retirement rules
✗ Uses data that contradicts the provided member profile or tool results

CRITICAL: If the response passes all criteria, the "violations" array MUST be empty [].
Only include violations if the response actually FAILS validation.
Keep violations to a MAXIMUM of 2-3 significant issues.

JSON FORMAT REQUIREMENTS - KEEP CONCISE:
- Each violation "detail" must be ONE SENTENCE MAX
- Each violation "evidence" must be ONE SHORT QUOTE MAX
- "reasoning" must be ONE SENTENCE MAX
- If passed=true, violations MUST be an empty array []

Respond with ONLY VALID, COMPLETE JSON (no other text):
{{
  "passed": true/false,
  "confidence": 0.0-1.0,
  "violations": [
    {{
      "code": "SHORTCODE",
      "severity": "CRITICAL/HIGH/MODERATE/LOW",
      "detail": "One sentence.",
      "evidence": "Short quote."
    }}
  ],
  "reasoning": "One sentence explanation."
}}"""
        
        return prompt
    
    def _parse_validation_response(self, judge_output):
        """Parse validation response - ROBUST WITH MALFORMED JSON HANDLING"""
        
        print(f"\n🔍 PARSING LLM JUDGE OUTPUT ({len(judge_output)} chars)...")
        
        # Strategy 1: Direct JSON (clean parse)
        try:
            result = json.loads(judge_output)
            if "passed" in result and "confidence" in result:
                print("✅ Strategy 1: Direct JSON parse succeeded - LLM JUDGE WORKING")
                result['_validator_used'] = 'LLM_JUDGE'
                print(f"✅ Validation result from LLM: passed={result['passed']}, confidence={result['confidence']}")
                return result
        except json.JSONDecodeError as e:
            print(f"⚠️ Strategy 1 failed: {str(e)[:100]}")
        
        # Strategy 2: Fix malformed JSON
        try:
            fixed_output = self._fix_malformed_json(judge_output)
            result = json.loads(fixed_output)
            if "passed" in result and "confidence" in result:
                print("✅ Strategy 2: Fixed malformed JSON - LLM JUDGE WORKING")
                result['_validator_used'] = 'LLM_JUDGE'
                print(f"✅ Validation result from LLM: passed={result['passed']}, confidence={result['confidence']}")
                return result
        except Exception as e:
            print(f"⚠️ Strategy 2 failed: {str(e)[:100]}")
        
        # Strategy 3: Extract from markdown code block
        try:
            json_match = re.search(r'``````', judge_output, re.MULTILINE)
            if json_match:
                json_str = json_match.group(1).strip()
                json_str = re.sub(r'^json\s*', '', json_str, flags=re.IGNORECASE | re.MULTILINE)
                json_str = self._fix_malformed_json(json_str)
                result = json.loads(json_str)
                if "passed" in result and "confidence" in result:
                    print("✅ Strategy 3: Markdown + fixed - LLM JUDGE WORKING")
                    result['_validator_used'] = 'LLM_JUDGE'
                    print(f"✅ Validation result from LLM: passed={result['passed']}, confidence={result['confidence']}")
                    return result
        except Exception as e:
            print(f"⚠️ Strategy 3 failed: {str(e)[:100]}")
        
        # Strategy 4: Extract between braces and fix
        try:
            first_brace = judge_output.find('{')
            last_brace = judge_output.rfind('}')
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                json_str = judge_output[first_brace:last_brace+1]
                json_str = self._fix_malformed_json(json_str)
                result = json.loads(json_str)
                if "passed" in result and "confidence" in result:
                    print("✅ Strategy 4: Brace extraction + fixed - LLM JUDGE WORKING")
                    result['_validator_used'] = 'LLM_JUDGE'
                    print(f"✅ Validation result from LLM: passed={result['passed']}, confidence={result['confidence']}")
                    return result
        except Exception as e:
            print(f"⚠️ Strategy 4 failed: {str(e)[:100]}")
        
        print("\n❌ ALL LLM JUDGE JSON STRATEGIES FAILED")
        print(f"🔍 Judge output (first 500 chars):")
        print(judge_output[:500])
        print(f"\n⚠️ Falling back to keyword-based validation")
        return None
    
    def _fix_malformed_json(self, json_str):
        """Fix common malformed JSON issues"""
        
        # Remove trailing commas
        json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)
        
        # Fix unclosed strings
        if json_str.rstrip().endswith('"') == False:
            if json_str.count('"') % 2 == 1:
                json_str = json_str + '"'
        
        # Fix unclosed objects
        json_str = json_str.rstrip()
        if not json_str.endswith('}'):
            last_brace = json_str.rfind('}')
            if last_brace != -1:
                json_str = json_str[:last_brace+1]
            else:
                json_str = json_str + '}'
        
        return json_str
    
    def _keyword_based_validation(self, response_text, user_query):
        """Fallback validation using keyword analysis"""
        
        print(f"\n📊 USING FALLBACK: Keyword-based validation")
        
        response_lower = response_text.lower()
        
        positive_keywords = ['can', 'you can', 'yes', 'will', 'should', 'recommend', 'withdraw', 'access']
        negative_keywords = ['cannot', "can't", 'no', 'not possible', 'unable', 'forbidden']
        
        positive_count = sum(1 for kw in positive_keywords if kw in response_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in response_lower)
        
        has_explicit_pass = any(phrase in response_lower for phrase in ['you can', 'yes you', 'absolutely'])
        has_explicit_fail = any(phrase in response_lower for phrase in ['cannot', "can't access"])
        
        has_numbers = bool(re.search(r'\d{1,}(?:,\d{3})*(?:\.\d{2})?', response_text))
        
        if len(response_text) > 200:
            confidence = 0.75
        else:
            confidence = 0.6
        
        if has_explicit_fail and "cannot" in response_lower:
            passed = False
            confidence = 0.7
        elif has_explicit_pass and has_numbers:
            passed = True
            confidence = 0.8
        elif positive_count > negative_count and len(response_text) > 150:
            passed = True
            confidence = 0.75
        else:
            passed = True
            confidence = 0.65
        
        print(f"📊 Keyword analysis: positive={positive_count}, negative={negative_count}")
        print(f"📊 Explicit: pass={has_explicit_pass}, fail={has_explicit_fail}")
        
        result = {
            "passed": passed,
            "confidence": confidence,
            "violations": [] if passed else [{
                "code": "KEYWORD-ANALYSIS",
                "severity": "MODERATE",
                "detail": "Based on keyword analysis",
                "evidence": "Response analysis"
            }],
            "reasoning": "Keyword-based validation (fallback)",
            "_validator_used": 'KEYWORD_FALLBACK'
        }
        
        print(f"⚠️ FALLBACK RESULT: {'Pass' if passed else 'Fail'} (confidence: {int(confidence*100)}%)")
        return result


class DeterministicValidator:
    """Simple deterministic validation - no LLM costs"""
    
    def validate(self, response_text, user_query, context, member_profile=None, tool_output=None):
        """Deterministic validation - quick checks"""
        
        # 🆕 NEW: Check for tool failures FIRST
        if tool_output:
            failed_tools = [
                tool_name for tool_name, result in tool_output.items()
                if isinstance(result, dict) and "error" in result
            ]
            
            if failed_tools:
                print(f"❌ DETERMINISTIC CHECK: Tool failures detected: {', '.join(failed_tools)}")
                error_details = []
                for tool_name in failed_tools:
                    error_msg = tool_output[tool_name].get('error', 'Unknown error')
                    error_details.append(f"{tool_name}: {error_msg}")
                
                return {
                    "passed": False,
                    "confidence": 1.0,
                    "violations": [{
                        "code": "TOOL-FAILED",
                        "severity": "CRITICAL",
                        "detail": f"Calculation tools failed: {', '.join(failed_tools)}",
                        "evidence": error_details[0][:200] if error_details else "Tool execution error"
                    }],
                    "_validator_used": "DETERMINISTIC",
                    "reasoning": "Tool execution failed",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0.0,
                    "model": "deterministic",
                    "duration": 0.0
                }
        
        # Existing deterministic checks
        if len(response_text) < 50:
            return {
                "passed": False,
                "confidence": 0.9,
                "violations": [{
                    "code": "TOO-SHORT",
                    "severity": "HIGH",
                    "detail": "Response too brief"
                }],
                "_validator_used": 'DETERMINISTIC',
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "model": "deterministic",
                "duration": 0.0
            }
        
        has_numbers = bool(re.search(r'\$?\d{1,}(?:,\d{3})*', response_text))
        
        return {
            "passed": True,
            "confidence": 0.8 if has_numbers else 0.65,
            "violations": [],
            "_validator_used": 'DETERMINISTIC',
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0,
            "model": "deterministic",
            "duration": 0.0
        }

