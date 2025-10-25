# validation.py - ULTRA-ROBUST VERSION
"""
Multi-Country LLM Judge Validator with Claude Sonnet 4
✅ ULTRA-ROBUST: Handles ANY judge output format
✅ FIXED: Extracts JSON from ANY response (markdown, plain text, etc.)
✅ FALLBACK: Uses keyword analysis if JSON fails completely
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from config import JUDGE_LLM_ENDPOINT, JUDGE_LLM_TEMPERATURE, JUDGE_LLM_MAX_TOKENS
import json
import time
import re


class LLMJudgeValidator:
    """LLM-as-a-Judge validator using Claude Sonnet 4 for multi-country validation"""

    def __init__(self, judge_endpoint=None):
        self.w = WorkspaceClient()
        self.judge_endpoint = judge_endpoint or JUDGE_LLM_ENDPOINT
        print(f"✓ LLM Judge initialized: {self.judge_endpoint}")

    def validate(self, response_text, user_query, context):
        """
        ✅ ULTRA-ROBUST: Validate AI response with multiple fallback strategies
        
        Args:
            response_text: The AI-generated response
            user_query: Original user question
            context: Full context including member profile and tool results

        Returns:
            Dict with validation results
        """
        
        # Parse context to extract member profile and tool results
        member_profile = self._extract_member_profile(context)
        tool_results = self._extract_tool_results(context)

        validation_prompt = self._build_validation_prompt(
            response_text, member_profile, tool_results, user_query
        )

        start_time = time.time()

        try:
            # Call judge LLM endpoint
            chat_messages = [
                ChatMessage(role=ChatMessageRole.USER, content=validation_prompt)
            ]

            response = self.w.serving_endpoints.query(
                name=self.judge_endpoint,
                messages=chat_messages,
                max_tokens=JUDGE_LLM_MAX_TOKENS,
                temperature=JUDGE_LLM_TEMPERATURE
            )

            judge_output = response.choices[0].message.content
            elapsed = time.time() - start_time

            # ✅ NEW: Extract token usage from response
            usage = getattr(response, 'usage', None)
            if usage:
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
            else:
                input_tokens = 0
                output_tokens = 0

            print(f"⏱️  Judge validation took {elapsed:.2f} seconds")
            print(f"📊 Tokens: {input_tokens:,} input + {output_tokens:,} output = {input_tokens + output_tokens:,} total")
            print(f"📝 Judge output (first 300 chars): {judge_output[:300]}")

            # Parse JSON response with ULTRA-ROBUST error handling
            result = self._parse_judge_output_ultra_robust(judge_output, response_text, member_profile)
            
            # ✅ NEW: Add token information to result
            result['input_tokens'] = input_tokens
            result['output_tokens'] = output_tokens
            result['duration'] = elapsed
            
            # Add verdict for compatibility
            if "verdict" not in result:
                result["verdict"] = "Pass" if result.get("passed", False) else "Fail"

            print(f"✅ Validation result: {result.get('verdict')} (confidence: {result.get('confidence', 0):.0%})")
            return result

        except Exception as e:
            print(f"❌ Judge validation error: {e}")
            import traceback
            traceback.print_exc()
            
            # FALLBACK: Use simple rule-based validation
            print("⚠️  Using fallback rule-based validation...")
            result = self._fallback_validation(response_text, member_profile)
            
            # Add zero tokens for fallback (no LLM call)
            result['input_tokens'] = 0
            result['output_tokens'] = 0
            result['duration'] = 0.0
            
            return result

    def _parse_judge_output_ultra_robust(self, judge_output, response_text, member_profile):
        """
        ✅ ULTRA-ROBUST: Parse judge output with multiple strategies
        
        Strategy 1: Direct JSON parse
        Strategy 2: Extract from markdown code block
        Strategy 3: Extract from any {...} pattern
        Strategy 4: Keyword-based analysis
        Strategy 5: Simple rule-based fallback
        """
        
        # STRATEGY 1: Direct JSON parse
        try:
            result = json.loads(judge_output)
            print("✅ Strategy 1: Direct JSON parse succeeded")
            return self._validate_result_structure(result)
        except json.JSONDecodeError:
            print("⚠️  Strategy 1 failed: Not direct JSON")
            pass

        # STRATEGY 2: Extract from markdown code block
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', judge_output, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                print("✅ Strategy 2: Markdown code block extraction succeeded")
                return self._validate_result_structure(result)
        except (json.JSONDecodeError, AttributeError):
            print("⚠️  Strategy 2 failed: No valid JSON in markdown")
            pass

        # STRATEGY 3: Extract ANY {...} pattern (greedy)
        try:
            # Find all JSON-like patterns
            json_patterns = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', judge_output, re.DOTALL)
            
            for pattern in json_patterns:
                try:
                    result = json.loads(pattern)
                    if isinstance(result, dict) and 'passed' in result:
                        print("✅ Strategy 3: Pattern extraction succeeded")
                        return self._validate_result_structure(result)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"⚠️  Strategy 3 failed: {e}")
            pass

        # STRATEGY 4: Keyword-based analysis of judge output
        print("⚠️  All JSON strategies failed, using keyword analysis...")
        return self._keyword_based_validation(judge_output, response_text, member_profile)

    def _keyword_based_validation(self, judge_output, response_text, member_profile):
        """
        ✅ STRATEGY 4: Analyze judge output using keywords
        """
        judge_lower = judge_output.lower()
        
        # Count positive indicators
        positive_keywords = ['pass', 'correct', 'accurate', 'valid', 'compliant', 'appropriate']
        positive_count = sum(1 for kw in positive_keywords if kw in judge_lower)
        
        # Count negative indicators
        negative_keywords = ['fail', 'incorrect', 'inaccurate', 'invalid', 'violation', 'error', 'wrong', 'issue']
        negative_count = sum(1 for kw in negative_keywords if kw in judge_lower)
        
        # Look for explicit pass/fail statements
        has_explicit_pass = bool(re.search(r'\bpass(?:ed)?\b', judge_lower))
        has_explicit_fail = bool(re.search(r'\bfail(?:ed)?\b', judge_lower))
        
        print(f"📊 Keyword analysis: positive={positive_count}, negative={negative_count}")
        print(f"📊 Explicit: pass={has_explicit_pass}, fail={has_explicit_fail}")
        
        # Determine pass/fail
        if has_explicit_pass and not has_explicit_fail:
            passed = True
            confidence = 0.8
            reasoning = "Judge indicated PASS based on keyword analysis"
        elif has_explicit_fail:
            passed = False
            confidence = 0.8
            reasoning = "Judge indicated FAIL based on keyword analysis"
        elif positive_count > negative_count * 2:
            passed = True
            confidence = 0.6
            reasoning = f"Positive indicators ({positive_count}) significantly outweigh negative ({negative_count})"
        elif negative_count > positive_count:
            passed = False
            confidence = 0.6
            reasoning = f"Negative indicators ({negative_count}) outweigh positive ({positive_count})"
        else:
            # Tie or unclear - use fallback rule-based validation
            print("⚠️  Keyword analysis inconclusive, using rule-based fallback...")
            return self._fallback_validation(response_text, member_profile)
        
        # Extract any violations mentioned
        violations = []
        if not passed:
            # Look for common violation patterns
            violation_patterns = [
                r'violation[:\s]+([^.]+)',
                r'error[:\s]+([^.]+)',
                r'incorrect[:\s]+([^.]+)',
                r'issue[:\s]+([^.]+)'
            ]
            
            for pattern in violation_patterns:
                matches = re.findall(pattern, judge_output, re.IGNORECASE)
                for match in matches[:3]:  # Limit to 3 violations
                    violations.append({
                        "code": "KEYWORD-DETECTED",
                        "severity": "MEDIUM",
                        "detail": match.strip(),
                        "evidence": ""
                    })
        
        return {
            "passed": passed,
            "confidence": confidence,
            "verdict": "Pass" if passed else "Fail",
            "violations": violations,
            "reasoning": f"{reasoning}. Judge output analyzed via keyword detection."
        }

    def _fallback_validation(self, response_text, member_profile):
        """
        ✅ STRATEGY 5: Simple rule-based validation as last resort
        """
        print("🔧 Using rule-based fallback validation...")
        
        violations = []
        
        # Check 1: Age logic
        age = member_profile.get('age')
        preservation_age = member_profile.get('preservation_age', 60)
        
        if age and isinstance(age, int) and isinstance(preservation_age, int):
            if age >= preservation_age:
                # Member HAS reached preservation age
                incorrect_patterns = [
                    r'below.*preservation.*age',
                    r'under.*preservation.*age',
                    r'not.*reached.*preservation',
                    r'haven.*t.*reached.*preservation'
                ]
                
                for pattern in incorrect_patterns:
                    if re.search(pattern, response_text, re.IGNORECASE):
                        violations.append({
                            "code": "AGE-LOGIC-ERROR",
                            "severity": "CRITICAL",
                            "detail": f"Response says member hasn't reached preservation age, but {age} >= {preservation_age}",
                            "evidence": pattern
                        })
                        break
        
        # Check 2: Balance mentions (lenient)
        balance = member_profile.get('super_balance')
        if balance and isinstance(balance, (int, float)):
            balance_str = str(int(balance))
            if balance_str not in response_text.replace(',', '').replace(' ', ''):
                violations.append({
                    "code": "BALANCE-MISSING",
                    "severity": "LOW",
                    "detail": f"Could not find exact balance {balance} in response",
                    "evidence": ""
                })
        
        # Determine pass/fail
        critical_violations = [v for v in violations if v.get('severity') == 'CRITICAL']
        passed = len(critical_violations) == 0
        
        return {
            "passed": passed,
            "confidence": 0.7,
            "verdict": "Pass" if passed else "Fail",
            "violations": violations,
            "reasoning": f"Rule-based validation found {len(violations)} issue(s), {len(critical_violations)} critical. Judge LLM output was unparseable."
        }

    def _validate_result_structure(self, result):
        """Ensure result has all required fields with safe defaults"""
        if not isinstance(result, dict):
            raise ValueError(f"Result is not a dictionary: {type(result)}")
        
        # Ensure required fields
        if "passed" not in result:
            result["passed"] = False
        
        if "confidence" not in result:
            result["confidence"] = 0.0
        
        if "violations" not in result:
            result["violations"] = []
        
        if "reasoning" not in result:
            result["reasoning"] = "No reasoning provided by judge"
        
        return result

    def _extract_member_profile(self, context):
        """Extract member profile from context string - ENHANCED to extract ALL fields"""
        profile = {}
        try:
            lines = context.split('\n')
            for line in lines:
                # Age
                if 'Age:' in line and 'Preservation Age' not in line:
                    try:
                        age_str = line.split('Age:')[1].strip()
                        profile['age'] = int(age_str.split()[0])
                    except:
                        pass
                
                # Preservation Age
                elif 'Preservation Age:' in line:
                    try:
                        pres_str = line.split('Preservation Age:')[1].strip()
                        profile['preservation_age'] = int(pres_str.split()[0])
                    except:
                        pass
                
                # Balance
                elif 'Balance:' in line:
                    try:
                        bal_str = line.split('Balance:')[1].strip()
                        bal_clean = ''.join(c for c in bal_str if c.isdigit() or c == '.')
                        profile['super_balance'] = float(bal_clean)
                    except:
                        pass
                
                # Name
                elif 'Name:' in line and 'First Name' not in line:
                    profile['name'] = line.split('Name:')[1].strip()
                
                # First Name
                elif 'First Name:' in line:
                    profile['first_name'] = line.split('First Name:')[1].strip()
                
                # Employment
                elif 'Employment:' in line:
                    profile['employment_status'] = line.split('Employment:')[1].strip()
                
                # Marital Status ← CRITICAL!
                elif 'Marital Status:' in line:
                    profile['marital_status'] = line.split('Marital Status:')[1].strip()
                
                # Dependents ← CRITICAL!
                elif 'Dependents:' in line:
                    try:
                        deps_str = line.split('Dependents:')[1].strip()
                        profile['dependents'] = int(deps_str.split()[0])
                    except:
                        profile['dependents'] = 0
                
                # Other Assets ← CRITICAL!
                elif 'Other Assets:' in line:
                    try:
                        assets_str = line.split('Other Assets:')[1].strip()
                        assets_clean = ''.join(c for c in assets_str if c.isdigit() or c == '.')
                        profile['other_assets'] = float(assets_clean) if assets_clean else 0
                    except:
                        profile['other_assets'] = 0
                
                # Country
                elif 'Country:' in line:
                    profile['country'] = line.split('Country:')[1].strip()
                
                # Member ID
                elif 'Member ID:' in line:
                    profile['member_id'] = line.split('Member ID:')[1].strip()
        
        except Exception as e:
            print(f"⚠️ Error extracting member profile: {e}")
        
        # Debug: Show what was extracted
        print(f"📋 Extracted member profile: {list(profile.keys())}")
        if 'marital_status' in profile:
            print(f"   ✅ Marital Status: {profile['marital_status']}")
        if 'dependents' in profile:
            print(f"   ✅ Dependents: {profile['dependents']}")
        if 'other_assets' in profile:
            print(f"   ✅ Other Assets: {profile['other_assets']}")
        
        return profile

    def _extract_tool_results(self, context):
        """Extract tool results from context string"""
        try:
            if 'UC FUNCTION RESULTS' in context:
                results_section = context.split('UC FUNCTION RESULTS')[1]
                if 'USER QUESTION:' in results_section:
                    results_section = results_section.split('USER QUESTION:')[0]
                
                try:
                    json_start = results_section.find('{')
                    if json_start != -1:
                        json_str = results_section[json_start:]
                        brace_count = 0
                        json_end = -1
                        for i, char in enumerate(json_str):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                        
                        if json_end != -1:
                            return json.loads(json_str[:json_end])
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Error extracting tool results: {e}")
        
        return {}

    def _build_validation_prompt(self, response_text, member_profile, tool_results, user_query):
        """Build comprehensive validation prompt for judge LLM"""

        age = member_profile.get('age', 'Unknown')
        preservation_age = member_profile.get('preservation_age', 60)
        balance = member_profile.get('super_balance', 0)

        age_comparison = "Cannot determine"
        if isinstance(age, int) and isinstance(preservation_age, int):
            age_comparison = f"{age} >= {preservation_age} = {age >= preservation_age}"

        prompt = f"""You are an expert retirement compliance validator. Analyze this AI response for accuracy.

MEMBER PROFILE:
- Name: {member_profile.get('name')}
- Age: {age} years old
- Preservation Age: {preservation_age} years old
- Balance: {balance}
- Employment: {member_profile.get('employment_status')}
- Marital Status: {member_profile.get('marital_status', 'Unknown')}
- Dependents: {member_profile.get('dependents', 0)}
- Other Assets: {member_profile.get('other_assets', 0)}
- Country: {member_profile.get('country', 'Unknown')}

USER QUESTION:
{user_query}

CALCULATOR RESULTS:
{json.dumps(tool_results, indent=2, default=str)[:1000]}

AI RESPONSE TO VALIDATE:
{response_text}

CRITICAL CHECKS:
1. AGE LOGIC: Age {age}, Preservation {preservation_age}. Check: {age_comparison}
2. MATH ACCURACY: Numbers match calculator results?
3. DATA CONSISTENCY: Uses correct member data?
   - Marital Status: {member_profile.get('marital_status', 'Unknown')}
   - Dependents: {member_profile.get('dependents', 0)}
   - Do NOT flag as "assumption" if response uses these facts!

RESPOND WITH VALID JSON ONLY (no markdown, no explanation):

{{
  "passed": true,
  "confidence": 0.95,
  "violations": [],
  "reasoning": "All checks passed"
}}

OR if issues found:

{{
  "passed": false,
  "confidence": 0.90,
  "violations": [
    {{
      "code": "AGE-LOGIC-001",
      "severity": "CRITICAL",
      "detail": "Age logic error detected",
      "evidence": "quote from response"
    }}
  ],
  "reasoning": "Found age logic error"
}}

RESPOND WITH JSON ONLY. NO OTHER TEXT."""

        return prompt


class DeterministicValidator:
    """Fast rules-based validator for common errors"""

    @staticmethod
    def validate(response_text, user_query, context):
        """Run deterministic validation checks"""
        
        violations = []
        
        # Extract member profile
        member_profile = {}
        try:
            lines = context.split('\n')
            for line in lines:
                if 'Age:' in line and 'Preservation' not in line:
                    try:
                        age_str = line.split('Age:')[1].strip()
                        member_profile['age'] = int(age_str.split()[0])
                    except:
                        pass
                elif 'Preservation Age:' in line:
                    try:
                        pres_str = line.split('Preservation Age:')[1].strip()
                        member_profile['preservation_age'] = int(pres_str.split()[0])
                    except:
                        pass
                elif 'Balance:' in line:
                    try:
                        bal_str = line.split('Balance:')[1].strip()
                        bal_clean = ''.join(c for c in bal_str if c.isdigit() or c == '.')
                        member_profile['super_balance'] = float(bal_clean)
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Error parsing context: {e}")

        # Check age logic
        age = member_profile.get('age')
        preservation_age = member_profile.get('preservation_age', 60)

        if age and isinstance(age, int) and isinstance(preservation_age, int):
            if age >= preservation_age:
                incorrect_patterns = [
                    r'below.*preservation.*age',
                    r'under.*preservation.*age',
                    r'not.*reached.*preservation',
                    r'haven.*t.*reached.*preservation'
                ]

                for pattern in incorrect_patterns:
                    if re.search(pattern, response_text, re.IGNORECASE):
                        violations.append({
                            "code": "AGE-LOGIC-ERROR",
                            "severity": "CRITICAL",
                            "detail": f"Incorrect age logic: says under preservation age but {age} >= {preservation_age}",
                            "evidence": pattern
                        })
                        break

        critical_violations = [v for v in violations if v.get('severity') == 'CRITICAL']

        return {
            "passed": len(critical_violations) == 0,
            "confidence": 1.0 if len(violations) == 0 else 0.7,
            "verdict": "Pass" if len(critical_violations) == 0 else "Fail",
            "violations": violations,
            "reasoning": f"Deterministic validation: {len(violations)} issue(s), {len(critical_violations)} critical"
        }
