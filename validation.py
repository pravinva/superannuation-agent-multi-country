# validation.py - COMPLETE FIXED VERSION
"""
Multi-Country LLM Judge Validator with Claude Sonnet 4
CRITICAL FIX: JSON parsing errors now default to FAIL (not pass) to trigger retries
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

    def validate_response(self, response_text, member_profile, tool_results, user_query):
        """
        Validate AI response against member profile and tool results

        Args:
            response_text: The AI-generated response
            member_profile: Member data from database
            tool_results: Results from MCP tools
            user_query: Original user question

        Returns:
            Dict with validation results including passed, confidence, violations, reasoning
        """

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

            print(f"⏱️  Judge validation took {elapsed:.2f} seconds")

            # Parse JSON response with improved error handling
            result = self._parse_judge_output(judge_output)

            return result

        except Exception as e:
            print(f"❌ Judge validation error: {e}")
            # CRITICAL FIX: Return FAIL on error (not pass)
            return {
                "passed": False,  # ← FIXED: Was True, now False
                "confidence": 0.0,
                "violations": [{
                    "code": "SYSTEM-ERROR",
                    "severity": "CRITICAL",
                    "detail": f"Judge validation system error: {str(e)}",
                    "evidence": ""
                }],
                "reasoning": f"Judge LLM encountered error: {str(e)}"
            }

    def _parse_judge_output(self, judge_output):
        """
        Parse judge output with IMPROVED error handling

        CRITICAL FIX: If parsing fails, return FAIL (not pass) to trigger retry
        """

        # Try to extract JSON from response
        try:
            # First attempt: direct JSON parse
            result = json.loads(judge_output)
            print("✓ Successfully parsed judge JSON directly")

        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse judge JSON directly: {e}")
            print(f"Raw output (first 500 chars): {judge_output[:500]}")

            # Second attempt: Extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', judge_output, re.DOTALL)

            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                    print("✓ Extracted JSON from markdown code block")
                except json.JSONDecodeError as e2:
                    print(f"❌ JSON extraction from markdown failed: {e2}")
                    # CRITICAL FIX: Default to FAIL (not pass)
                    return {
                        "passed": False,  # ← FIXED: Was True, now False
                        "confidence": 0.0,
                        "violations": [{
                            "code": "PARSE-ERROR",
                            "severity": "CRITICAL",
                            "detail": "Failed to parse judge output JSON - triggering retry for safety",
                            "evidence": judge_output[:200]
                        }],
                        "reasoning": "JSON parsing failed in both direct and markdown extraction - defaulting to fail"
                    }
            else:
                # CRITICAL FIX: No JSON found, default to FAIL
                print("❌ No JSON structure found in judge output")
                lines = judge_output.split('\n')[:5]
                potential_issues = [line for line in lines if 'violation' in line.lower() or 'critical' in line.lower()]
                print(f"⚠️ Found potential issues in unparseable output: {potential_issues}")

                return {
                    "passed": False,  # ← FIXED: Was True, now False
                    "confidence": 0.0,
                    "violations": [{
                        "code": "NO-JSON",
                        "severity": "CRITICAL",
                        "detail": "Judge output did not contain parseable JSON structure",
                        "evidence": judge_output[:200]
                    }],
                    "reasoning": "No JSON structure found in judge output - defaulting to fail for safety"
                }

        # Validate result structure
        if not isinstance(result, dict):
            print(f"❌ Judge result is not a dictionary: {type(result)}")
            return {
                "passed": False,
                "confidence": 0.0,
                "violations": [{
                    "code": "INVALID-STRUCTURE",
                    "severity": "CRITICAL",
                    "detail": f"Judge output is {type(result)} not dict",
                    "evidence": str(result)[:200]
                }],
                "reasoning": "Invalid result structure from judge"
            }

        # Ensure required fields exist with safe defaults
        if "passed" not in result:
            print("⚠️ 'passed' field missing from judge output - defaulting to False")
            result["passed"] = False  # Default to fail if missing

        if "confidence" not in result:
            result["confidence"] = 0.0

        if "violations" not in result:
            result["violations"] = []

        if "reasoning" not in result:
            result["reasoning"] = "No reasoning provided by judge"

        return result

    def _build_validation_prompt(self, response_text, member_profile, tool_results, user_query):
        """Build comprehensive validation prompt for judge LLM"""

        # Extract key member data
        age = member_profile.get('age', 'Unknown')
        preservation_age = member_profile.get('preservation_age', 60)
        balance = member_profile.get('super_balance', 0)

        # Calculate age comparison explicitly
        age_comparison = "Cannot determine"
        if isinstance(age, int) and isinstance(preservation_age, int):
            age_comparison = f"{age} >= {preservation_age} = {age >= preservation_age}"

        prompt = f"""You are an expert retirement compliance validator. Your job is to verify that AI-generated retirement advice is accurate, factually correct, and compliant with regulations.

MEMBER PROFILE:
- Name: {member_profile.get('name')}
- Age: {age} years old
- Preservation Age: {preservation_age} years old
- Balance: {balance}
- Employment: {member_profile.get('employment_status')}
- Marital Status: {member_profile.get('marital_status')}

USER QUESTION:
{user_query}

CALCULATOR/TOOL RESULTS:
{json.dumps(tool_results, indent=2, default=str)[:1500]}

AI RESPONSE TO VALIDATE:
{response_text}

CRITICAL VALIDATION CHECKS:

1. AGE LOGIC ACCURACY:
   - Member's actual age: {age} years old
   - Preservation age threshold: {preservation_age}
   - Mathematical check: {age_comparison}
   - If age >= preservation age → member HAS REACHED preservation age
   - If age < preservation age → member is BELOW preservation age
   - VIOLATION: Any statement that contradicts the above logic

2. MATHEMATICAL ACCURACY:
   - Verify all numbers match tool results exactly
   - Check percentage calculations are correct
   - Verify withdrawal amounts and tax calculations
   - VIOLATION: Any incorrect math or mismatched numbers

3. DATA CONSISTENCY:
   - Response must use member's actual age ({age}) and balance ({balance})
   - No contradictions between different parts of response
   - VIOLATION: Any internal contradictions or wrong member data

4. REGULATORY COMPLIANCE:
   - Advice must match country-specific rules from tool results
   - Tax implications must be accurate for member's age
   - VIOLATION: Any non-compliant advice

5. FORMATTING:
   - Check for proper spacing and punctuation
   - Currency should be formatted consistently
   - VIOLATION: Minor formatting issues (severity: LOW)

RESPONSE FORMAT:

Provide your validation in VALID JSON format (no markdown code blocks):

{{
  "passed": true or false,
  "confidence": 0.0 to 1.0,
  "violations": [
    {{
      "code": "LOGIC-001",
      "severity": "CRITICAL" or "MEDIUM" or "LOW",
      "detail": "Clear description of the violation",
      "evidence": "Direct quote from response showing the error"
    }}
  ],
  "reasoning": "Brief explanation of your decision"
}}

IMPORTANT: 
- Return ONLY valid JSON (no markdown, no code blocks)
- Be strict on age/math logic errors (CRITICAL severity)
- Be lenient on minor formatting issues (LOW severity)
- If passed=false, list ALL violations found
"""

        return prompt


class DeterministicValidator:
    """Fast rules-based validator for common errors"""

    @staticmethod
    def validate_response(response_text, member_profile, tool_results):
        """
        Run deterministic validation checks using pattern matching

        Returns:
            Dict with validation results
        """

        violations = []

        # Check 1: Age accuracy
        age = member_profile.get('age')
        preservation_age = member_profile.get('preservation_age', 60)

        if age and isinstance(age, int) and isinstance(preservation_age, int):
            # Check for incorrect age logic
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

        # Check 2: Balance mentions
        balance = member_profile.get('super_balance')
        if balance and isinstance(balance, (int, float)):
            balance_str = str(int(balance))
            # Lenient check - just warn if balance not mentioned
            if balance_str not in response_text.replace(',', '').replace(' ', ''):
                violations.append({
                    "code": "BALANCE-MISSING",
                    "severity": "LOW",
                    "detail": f"Could not find exact balance {balance} mentioned in response",
                    "evidence": ""
                })

        # Check 3: Currency format issues
        if ',$' in response_text or '$,' in response_text:
            violations.append({
                "code": "FORMAT-CURRENCY",
                "severity": "LOW",
                "detail": "Incorrect currency formatting detected",
                "evidence": "Found malformed currency format"
            })

        # Determine pass/fail
        critical_violations = [v for v in violations if v.get('severity') == 'CRITICAL']

        return {
            "passed": len(critical_violations) == 0,
            "confidence": 1.0 if len(violations) == 0 else 0.7,
            "violations": violations,
            "reasoning": f"Deterministic validation found {len(violations)} issue(s), {len(critical_violations)} critical"
        }
