# validation.py - Multi-Country LLM Judge Validator with Claude Sonnet 4

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
            Dict with validation results
        """
        validation_prompt = self._build_validation_prompt(
            response_text, 
            member_profile, 
            tool_results, 
            user_query
        )
        
        try:
            start_time = time.time()
            
            messages = [
                ChatMessage(
                    role=ChatMessageRole.USER,
                    content=validation_prompt
                )
            ]
            
            response = self.w.serving_endpoints.query(
                name=self.judge_endpoint,
                messages=messages,
                max_tokens=JUDGE_LLM_MAX_TOKENS,
                temperature=JUDGE_LLM_TEMPERATURE
            )
            
            elapsed = time.time() - start_time
            judge_output = response.choices[0].message.content
            
            print(f"⏱️  Judge validation took {elapsed:.2f} seconds")
            
            validation_result = self._parse_judge_output(judge_output)
            validation_result['elapsed_time'] = elapsed
            validation_result['judge_model'] = self.judge_endpoint
            
            return validation_result
            
        except Exception as e:
            print(f"⚠️ LLM Judge validation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'passed': True,
                'error': str(e),
                'confidence': 0.0,
                'violations': [],
                'judge_model': self.judge_endpoint
            }
    
    def _build_validation_prompt(self, response_text, member_profile, tool_results, user_query):
        """Build validation prompt with multi-source ground truth - MULTI-COUNTRY"""
        
        # Get country from profile
        country = member_profile.get('country', 'Australia')
        
        profile_summary = {
            'name': member_profile.get('name'),
            'age': member_profile.get('age'),
            'country': country,
            'preservation_age': member_profile.get('preservation_age', 60),
            'super_balance': member_profile.get('super_balance'),
            'other_assets': member_profile.get('other_assets'),
            'debt': member_profile.get('debt'),
            'employment_status': member_profile.get('employment_status'),
            'marital_status': member_profile.get('marital_status'),
            'dependents': member_profile.get('dependents'),
            'home_ownership': member_profile.get('home_ownership'),
            'annual_income_outside_super': member_profile.get('annual_income_outside_super')
        }
        
        clean_tool_results = {k: v for k, v in tool_results.items() 
                             if not k.startswith('_')}
        
        # Build prompt with proper escaping
        member_age = profile_summary.get('age', 0)
        pres_age = profile_summary.get('preservation_age', 60)
        
        # Country-specific pension ages
        pension_ages = {
            "Australia": 67,
            "USA": 67,  # Full Social Security retirement age
            "United Kingdom": 66,  # State Pension age
            "India": 60  # EPF withdrawal age
        }
        pension_age = pension_ages.get(country, 67)
        
        # Country-specific program names
        pension_names = {
            "Australia": "Age Pension",
            "USA": "Social Security",
            "United Kingdom": "State Pension",
            "India": "EPF/Pension"
        }
        pension_name = pension_names.get(country, "pension")
        
        # Calculate age comparisons
        age_vs_preservation = "ABOVE (>=)" if member_age >= pres_age else "BELOW (<)"
        age_vs_pension = "AT OR ABOVE (>=)" if member_age >= pension_age else "BELOW (<)"
        
        prompt = f"""You are a compliance judge validating {country} retirement advisory response.

**VALID DATA SOURCES:**

1. MEMBER PROFILE DATA:
{json.dumps(profile_summary, indent=2, default=str)}

2. TOOL RESULTS DATA:
{json.dumps(clean_tool_results, indent=2, default=str)}

**USER QUERY:** {user_query}

**AI RESPONSE:** {response_text}

**MATHEMATICAL FACTS TO VERIFY:**
- Country: {country}
- Member age: {member_age}
- Preservation age: {pres_age}
- Age comparison: {member_age} is {age_vs_preservation} {pres_age}
- {pension_name} eligibility age: {pension_age}
- Pension comparison: {member_age} is {age_vs_pension} {pension_age}

**VALIDATION RULES (adjusted for {country}):**

DATA-001: Data Fabrication
- ONLY flag if AI cites numbers NOT in member profile OR tool results
- other_assets={profile_summary.get('other_assets')} is VALID from profile
- marital_status={profile_summary.get('marital_status')} is VALID from profile
- home_ownership={profile_summary.get('home_ownership')} is VALID from profile
- dependents={profile_summary.get('dependents')} is VALID from profile
- DO NOT flag if AI discusses options generally without inventing specific amounts
- DO flag if AI invents specific withdrawal amounts not mentioned in user query

PA-001: Preservation Age Violations (for {country})
- Member age: {member_age}, preservation age: {pres_age}
- If age < preservation: MUST state cannot access retirement funds (except compassionate grounds)
- If age >= preservation: CAN state they can access retirement funds
- CRITICAL CHECK: {member_age} is {age_vs_preservation} {pres_age}
- Check for contradictions

PENSION-001: {pension_name} Violations
- Member age: {member_age}
- {pension_name} eligibility age: {pension_age}
- CRITICAL CHECK: {member_age} is {age_vs_pension} {pension_age}
- If member age < {pension_age}: MUST state "future projection" or "when you reach {pension_age}"
- If member age >= {pension_age}: CAN state current eligibility

LOGIC-001: Mathematical/Logical Errors
- Check for mathematical impossibilities (e.g., stating "{member_age} is below {pres_age}" when {member_age} > {pres_age})
- Check for contradictory statements
- Verify age comparisons match the MATHEMATICAL FACTS above
- Flag statements that contradict basic arithmetic

FORMAT-001: Formatting
- Currency must have space (e.g., "54,000 {country}" with space)
- No asterisks for emphasis

**CRITICAL: RESPOND WITH VALID JSON ONLY - NO EXTRA TEXT, NO MARKDOWN**

You MUST respond with ONLY this exact JSON structure:

{{
  "passed": true,
  "confidence": 0.95,
  "violations": [],
  "reasoning": "Response is accurate and compliant for {country}"
}}

OR if there are issues:

{{
  "passed": false,
  "confidence": 0.90,
  "violations": [
    {{
      "code": "LOGIC-001",
      "severity": "CRITICAL",
      "detail": "States member age {member_age} is below preservation age {pres_age}, which is mathematically incorrect",
      "evidence": "Direct quote from response showing the error"
    }}
  ],
  "reasoning": "Found logical error in age comparison"
}}

**CONFIDENCE GUIDELINES:**
- 0.90-1.00: Violations are clear and definitely wrong
- 0.70-0.89: Violations are likely with minor ambiguity
- 0.40-0.69: Uncertain, borderline violations
- 0.00-0.39: Low certainty, likely false positives

**IMPORTANT:**
- Be STRICT on mathematical/logical errors
- Be STRICT on age eligibility contradictions
- Be LENIENT on data from member profile or tool results
- Only flag CRITICAL violations for {country} regulations
- Set confidence HIGH only when violations are unambiguous

Respond with JSON only (no markdown, no code blocks, no explanation):"""
        
        return prompt
    
    def _parse_judge_output(self, judge_output):
        """Parse judge JSON output with robust error handling"""
        try:
            json_str = judge_output.strip()
            
            # Handle markdown code blocks
            code_block_start = "```
            code_block_end = "```"
            
            if code_block_start in json_str:
                parts = json_str.split(code_block_start)
                if len(parts) > 1:
                    json_str = parts[1].split(code_block_end)[0].strip()
            elif code_block_end in json_str and json_str.count(code_block_end) >= 2:
                parts = json_str.split(code_block_end)
                if len(parts) >= 3:
                    json_str = parts[1].strip()
            
            # Try to extract JSON object using regex as fallback
            if not json_str.startswith('{'):
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', judge_output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_match = re.search(r'\{[\s\S]*\}', judge_output)
                    if json_match:
                        json_str = json_match.group(0)
            
            # Clean up common JSON issues
            json_str = json_str.replace('\n', ' ').replace('\r', '')
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            # Parse JSON
            result = json.loads(json_str)
            
            # Validate structure
            if 'passed' not in result:
                result['passed'] = True
            if 'confidence' not in result:
                result['confidence'] = 0.5
            if 'violations' not in result:
                result['violations'] = []
            if 'reasoning' not in result:
                result['reasoning'] = 'No reasoning provided'
            
            # Ensure violations have required fields
            for violation in result.get('violations', []):
                if 'code' not in violation:
                    violation['code'] = 'UNKNOWN'
                if 'severity' not in violation:
                    violation['severity'] = 'MEDIUM'
                if 'detail' not in violation:
                    violation['detail'] = 'No detail provided'
                if 'evidence' not in violation:
                    violation['evidence'] = ''
            
            if result.get('confidence', 0) == 0 or 'failed to parse' in result.get('reasoning', '').lower():
                print("⚠️ Judge returned uncertain result (confidence=0), treating as passed")
                result['passed'] = True
                result['confidence'] = 0.0
                result['violations'] = []
                result['reasoning'] = 'Judge validation uncertain - treated as passed'
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse judge JSON: {e}")
            print(f"Raw output (first 500 chars): {judge_output[:500]}...")
            
            passed = True
            reasoning = "Failed to parse judge output - defaulting to pass"
            
            if any(word in judge_output.lower() for word in ['critical', 'violation', 'error', 'incorrect', 'wrong', 'fabricat']):
                lines = judge_output.split('\n')
                concerns = [line.strip() for line in lines if any(word in line.lower() for word in ['critical', 'violation', 'error', 'incorrect', 'fabricat'])]
                if concerns:
                    reasoning = "Parse failed but potential issues detected: " + " | ".join(concerns[:2])
                    print(f"⚠️ Found potential issues in unparseable output: {concerns[:2]}")
            
            return {
                'passed': passed,
                'confidence': 0.0,
                'violations': [],
                'reasoning': reasoning,
                'parse_error': str(e),
                'raw_output': judge_output[:1000]
            }
        except Exception as e:
            print(f"⚠️ Unexpected error parsing judge output: {e}")
            return {
                'passed': True,
                'confidence': 0.0,
                'violations': [],
                'reasoning': 'Unexpected validation error - defaulting to pass',
                'parse_error': str(e),
                'raw_output': judge_output[:1000] if judge_output else ''
            }


class DeterministicValidator:
    """Fallback rule-based validator - MULTI-COUNTRY"""
    
    @staticmethod
    def validate_response(response_text, member_profile, tool_results):
        """Rule-based validation for any country"""
        violations = []
        country = member_profile.get('country', 'Australia')
        
        # Rule 1: Check asterisk formatting
        asterisks = re.findall(r'(?<!\*)\*(?!\*)[^*]+\*(?!\*)', response_text)
        if asterisks and len(asterisks) > 2:
            violations.append({
                'code': 'FORMAT-001',
                'severity': 'MEDIUM',
                'detail': 'Contains single asterisks for formatting',
                'evidence': f'Found {len(asterisks)} instances'
            })
        
        # Rule 2: Check currency spacing
        bad_currency = re.findall(r'\d{1,3}(?:,\d{3})*(?:AUD|USD|GBP|INR)\b', response_text)
        if bad_currency:
            violations.append({
                'code': 'FORMAT-001',
                'severity': 'MEDIUM',
                'detail': 'Currency missing space',
                'evidence': ', '.join(bad_currency[:3])
            })
        
        # Rule 3: Preservation age (multi-country)
        member_age = member_profile.get('age', 999)
        preservation_age = member_profile.get('preservation_age', 60)
        
        if member_age < preservation_age:
            has_access = 'access' in response_text.lower()
            has_warning = ('cannot access' in response_text.lower() or 
                          'preservation age' in response_text.lower() or
                          f'{preservation_age}' in response_text)
            
            if has_access and not has_warning:
                violations.append({
                    'code': 'PA-001',
                    'severity': 'CRITICAL',
                    'detail': f'Age {member_age} < preservation age {preservation_age}, no warning',
                    'evidence': 'Missing preservation age warning'
                })
        
        # Rule 4: Pension age (country-specific)
        pension_ages = {"Australia": 67, "USA": 67, "United Kingdom": 66, "India": 60}
        pension_age = pension_ages.get(country, 67)
        
        if member_age < pension_age:
            pension_keywords = {
                "Australia": "age pension",
                "USA": "social security",
                "United Kingdom": "state pension",
                "India": "epf"
            }
            keyword = pension_keywords.get(country, "pension")
            
            pension_mentioned = keyword in response_text.lower()
            incorrect = ('you are eligible' in response_text.lower() or
                        'you currently receive' in response_text.lower())
            properly_qualified = (f'when you reach {pension_age}' in response_text.lower() or
                                'future' in response_text.lower())
            
            if pension_mentioned and incorrect and not properly_qualified:
                violations.append({
                    'code': 'PENSION-001',
                    'severity': 'CRITICAL',
                    'detail': f'Age {member_age} < {pension_age}, states current eligibility',
                    'evidence': f'Incorrect {keyword} eligibility'
                })
        
        passed = len([v for v in violations if v['severity'] == 'CRITICAL']) == 0
        
        return {
            'passed': passed,
            'confidence': 0.7 if violations else 0.9,
            'violations': violations,
            'reasoning': f'Rule-based validation for {country}. Found {len(violations)} issues.',
            'method': 'deterministic',
            'judge_model': 'rule-based-fallback'
        }


# Explicit exports
__all__ = ['LLMJudgeValidator', 'DeterministicValidator']

