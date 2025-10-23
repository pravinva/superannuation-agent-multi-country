# agent.py - Multi-Country Retirement Advisor with Hyper-Personalization
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from tools import get_country_tool
from validation import LLMJudgeValidator, DeterministicValidator
from country_content import COUNTRY_PROMPTS, COUNTRY_REGULATIONS, POST_ANSWER_DISCLAIMERS
from config import MAIN_LLM_ENDPOINT, JUDGE_LLM_ENDPOINT, MAIN_LLM_TEMPERATURE
from data_utils import get_member_by_id
import json
import time
import uuid
from datetime import datetime


class MultiCountryAdvisorAgent:
    """Multi-country retirement advisor with hyper-personalization"""

    def __init__(self, country="Australia"):
        self.w = WorkspaceClient()
        self.country = country
        self.main_endpoint = MAIN_LLM_ENDPOINT
        self.judge_endpoint = JUDGE_LLM_ENDPOINT
        self.session_id = str(uuid.uuid4())

        self.validator = LLMJudgeValidator(judge_endpoint=self.judge_endpoint)

        print(f"✓ Multi-Country Advisor Agent initialized")
        print(f"  Country: {country}")
        print(f"  Main LLM: {self.main_endpoint}")
        print(f"  Judge LLM: {self.judge_endpoint}")

    def call_claude(self, messages, max_tokens=2000, temperature=None, endpoint=None):
        """Call Claude endpoint via SDK"""
        start_time = time.time()

        temp = temperature if temperature is not None else MAIN_LLM_TEMPERATURE
        endpoint_name = endpoint if endpoint else self.main_endpoint

        chat_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                if msg['role'] == 'system':
                    role = ChatMessageRole.SYSTEM
                elif msg['role'] == 'user':
                    role = ChatMessageRole.USER
                else:
                    role = ChatMessageRole.ASSISTANT
                chat_messages.append(ChatMessage(role=role, content=msg['content']))
            else:
                chat_messages.append(msg)

        response = self.w.serving_endpoints.query(
            name=endpoint_name,
            messages=chat_messages,
            max_tokens=max_tokens,
            temperature=temp
        )

        elapsed = time.time() - start_time
        print(f"⏱️  Claude call: {elapsed:.2f}s (tokens={max_tokens}, temp={temp})")

        return response.choices[0].message.content, elapsed

    def _convert_to_int(self, value, default=0):
        """Safely convert to int"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _log_query_audit(self, member_id, user_query, response_text, total_time, tools_count):
        """Log to Unity Catalog audit table"""
        try:
            from audit.audit_utils import log_query_event

            truncated = response_text[:15000] if len(response_text) > 15000 else response_text

            log_query_event(
                user_id=member_id,
                session_id=self.session_id,
                country=self.country,
                query_string=user_query,
                agent_response=truncated,
                result_preview=f"Completed in {total_time:.2f}s",
                citations=[],
                tool_used=f"{self.country}_calculator",
                judge_response="",
                judge_verdict="N/A",
                error_info="",
                cost=0.0
            )
            print(f"✓ Audit logged: session {self.session_id[:8]}")
        except Exception as e:
            print(f"❌ Audit logging failed: {e}")

    def process_query(self, member_id, user_query, status_callback=None,
                      temperature=None, anonymize=True, enable_validation=True):
        """Main agentic workflow with hybrid validation and retry loop"""

        overall_start = time.time()
        temp = temperature if temperature is not None else MAIN_LLM_TEMPERATURE

        print(f"\n{'='*70}")
        print(f"AGENT: Processing query for {self.country}")
        print(f"Member: {member_id}")
        print(f"Query: {user_query}")
        print(f"{'='*70}\n")

        timings = {}
        tools_called = []

        # Get member profile
        profile_df = get_member_by_id(member_id)
        if profile_df is None or profile_df.empty:
            return "Member profile not found", {"error": "Member not found"}

        profile = profile_df.to_dict('records')[0]

        # Convert numeric fields
        numeric_fields = ['age', 'super_balance', 'other_assets', 'debt',
                         'preservation_age', 'annual_income_outside_super',
                         'dependents', 'account_based_pension']

        for field in numeric_fields:
            if field in profile:
                profile[field] = self._convert_to_int(profile[field])

        # Extract first name for personalization
        member_full_name = profile['name']
        member_first_name = member_full_name.split()[0] if member_full_name else 'Member'

        # Anonymization (kept for backwards compatibility, but disabled by default for personalization)
        real_name = profile['name']
        if anonymize:
            member_token = f"Member {member_id[-4:]}"
            profile['name'] = member_token
            print(f"🔒 Anonymized: '{real_name}' → '{member_token}'")
        else:
            member_token = None
            print(f"✅ Using real name for hyper-personalization: '{real_name}'")

        # STEP 1: Call country-specific calculator
        if status_callback:
            status_callback("tool_start", f"Calling {self.country} calculator...")

        tool_start = time.time()
        country_tool = get_country_tool(self.country)
        tool_result = country_tool(member_id, withdrawal_amount=100000)
        tool_duration = time.time() - tool_start

        tools_called.append({
            "name": f"{self.country} Calculator",
            "duration": tool_duration,
            "status": "completed"
        })

        print(f"✓ Tool executed in {tool_duration:.2f}s")

        if status_callback:
            status_callback("tool_complete", None)

        # STEP 2: Multi-stage synthesis with validation retry loop
        regulations = COUNTRY_REGULATIONS.get(self.country, {})

        context = f"""MEMBER PROFILE:
Name: {profile['name']}
First Name: {member_first_name}
Age: {profile.get('age')}
Balance: ${profile.get('super_balance', 0):,}
Employment: {profile.get('employment_status')}
Marital Status: {profile.get('marital_status')}
Country: {self.country}

REGULATORY CONTEXT:
{json.dumps(regulations, indent=2)}

CALCULATOR RESULTS:
{json.dumps(tool_result, indent=2, default=str)}

USER QUESTION:
{user_query}"""

        if status_callback:
            status_callback("synthesis_start", None)

        synthesis_start = time.time()

        # ===================================================================
        # RETRY LOOP: Try up to 3 times (1 initial + 2 retries)
        # ===================================================================
        MAX_RETRIES = 2
        attempt = 0
        validation_passed = False
        validation_feedback = None
        validation_result = None

        while attempt <= MAX_RETRIES and not validation_passed:

            attempt_label = f"Attempt {attempt + 1}/{MAX_RETRIES + 1}"
            print(f"\n{'='*70}")
            print(f"SYNTHESIS {attempt_label}")
            if validation_feedback:
                print(f"RETRY REASON: Judge found violations")
            print(f"{'='*70}\n")

            # Stage 1: Situation (HYPER-PERSONALIZED)
            if status_callback:
                status_callback("synthesis_stage", {"stage": 1, "task": f"Situation ({attempt_label})"})

            situation_prompt = f"""CONTEXT:
{context}

Write EXACTLY 2 sentences addressing {member_first_name} DIRECTLY by their first name.

CRITICAL PERSONALIZATION RULES:
- Start with: "{member_first_name}, you are {profile.get('age')} years old..."
- Use DIRECT address throughout (you/your not they/their)
- Reference their ACTUAL balance: ${profile.get('super_balance', 0):,}
- Make it conversational and personal
- Example: "John, you are 56 years old with a superannuation balance of $450,000. You are currently employed full-time and approaching your preservation age of 60."

FORMATTING RULES:
- EXACTLY 2 sentences, max 40 words each
- NO asterisks or special characters
- ALWAYS use spaces: "$100,000 tax-free" NOT "$100,000tax-free"
- ALWAYS use commas: "100,000" NOT "100000"
- ALWAYS spaces around math: "$ 32,500 - $ 37,000" NOT "$32,500-$37,000"

{validation_feedback if validation_feedback else ''}

Write directly (no headers)."""

            situation, sit_time = self.call_claude(
                [{"role": "user", "content": situation_prompt}],
                max_tokens=250,
                temperature=temp
            )
            timings[f'situation_attempt_{attempt}'] = sit_time

            # Stage 2: Insights
            if status_callback:
                status_callback("synthesis_stage", {"stage": 2, "task": f"Insights ({attempt_label})"})

            insights_prompt = f"""CONTEXT:
{context}

Write EXACTLY 3 key insights for {member_first_name}'s {self.country} retirement planning.

RULES:
- EXACTLY 3 bullet points
- Max 30 words per bullet
- Use actual numbers from tool results
- Use "you/your" language (continue personalization)
- ALWAYS use spaces: "$100,000 tax-free" NOT "$100,000tax-free"
- ALWAYS use commas: "100,000" NOT "100000"

{validation_feedback if validation_feedback else ''}

Write directly (no headers)."""

            insights, ins_time = self.call_claude(
                [{"role": "user", "content": insights_prompt}],
                max_tokens=450,
                temperature=temp
            )
            timings[f'insights_attempt_{attempt}'] = ins_time

            # Stage 3: Recommendations
            if status_callback:
                status_callback("synthesis_stage", {"stage": 3, "task": f"Recommendations ({attempt_label})"})

            recommendations_prompt = f"""CONTEXT:
{context}

PREVIOUS:
{situation}
{insights}

Write EXACTLY 2 actionable recommendations for {member_first_name}.

RULES:
- EXACTLY 2 numbered items
- ONE sentence each, max 35 words
- Continue using "you/your" personalization
- ALWAYS use spaces: "$100,000 tax-free" NOT "$100,000tax-free"
- ALWAYS use commas: "100,000" NOT "100000"

{validation_feedback if validation_feedback else ''}

Write directly (no headers)."""

            recommendations, rec_time = self.call_claude(
                [{"role": "user", "content": recommendations_prompt}],
                max_tokens=300,
                temperature=temp
            )
            timings[f'recommendations_attempt_{attempt}'] = rec_time

            # ===================================================================
            # VALIDATION: Deterministic (fast) → LLM Judge (accurate)
            # ===================================================================

            if enable_validation:
                if status_callback:
                    status_callback("validation_start", f"Validating ({attempt_label})...")

                full_response = f"{situation}\n\n{insights}\n\n{recommendations}"

                # Phase 1: Fast deterministic check
                print("🔧 Running deterministic pre-check...")
                det_result = DeterministicValidator.validate_response(
                    response_text=full_response,
                    member_profile=profile,
                    tool_results=tool_result
                )

                critical_violations = [v for v in det_result.get('violations', []) 
                                     if v.get('severity') == 'CRITICAL']

                if critical_violations:
                    print(f"❌ Deterministic check failed: {len(critical_violations)} critical issues")
                    validation_result = det_result
                    validation_result['fast_fail'] = True
                    validation_passed = False
                else:
                    # Phase 2: LLM Judge validation
                    print("⚖️  Running LLM Judge validation...")
                    try:
                        validation_result = self.validator.validate_response(
                            response_text=full_response,
                            member_profile=profile,
                            tool_results=tool_result,
                            user_query=user_query
                        )
                        validation_passed = validation_result.get('passed', True)

                    except Exception as e:
                        print(f"⚠️  LLM Judge failed: {e}")
                        validation_result = det_result
                        validation_passed = det_result.get('passed', True)

                tool_result[f'_validation_attempt_{attempt}'] = validation_result

                print(f"⚖️  Validation: {validation_result.get('passed')} (confidence: {validation_result.get('confidence', 0):.2f})")

                if not validation_passed and attempt < MAX_RETRIES:
                    print(f"\n⚠️  Validation failed. Preparing retry {attempt + 2}/{MAX_RETRIES + 1}...")

                    violations = validation_result.get('violations', [])
                    reasoning = validation_result.get('reasoning', '')

                    validation_feedback = f"""
⚠️ CRITICAL: Your previous response had compliance issues. Fix these:

"""
                    for i, violation in enumerate(violations, 1):
                        validation_feedback += f"{i}. **{violation.get('code')}** ({violation.get('severity')}): {violation.get('detail')}\n"
                        if violation.get('evidence'):
                            validation_feedback += f"   Evidence: {violation.get('evidence')[:150]}\n"

                    validation_feedback += f"""
Judge's reasoning: {reasoning}

CRITICAL INSTRUCTIONS FOR THIS RETRY:
1. Fix ALL violations listed above
2. Use ONLY data from member profile and tool results
3. Maintain hyper-personalization: Address {member_first_name} directly
4. Always use proper spacing: "$100,000 tax-free" NOT "$100,000tax-free"
5. Be precise about eligibility thresholds
"""

                    attempt += 1

                    if status_callback:
                        status_callback("retry", {"attempt": attempt + 1, "violations": len(violations)})

                else:
                    break
            else:
                validation_passed = True
                validation_result = {'passed': True, 'confidence': 1.0, 'violations': []}
                break

        # End of retry loop
        total_synthesis_time = time.time() - synthesis_start
        timings['synthesis_total'] = total_synthesis_time
        timings['synthesis_attempts'] = attempt + 1

        tool_result['_validation'] = validation_result
        tool_result['_validation_attempts'] = attempt + 1
        tool_result['_validation_passed'] = validation_passed

        if status_callback:
            status_callback("synthesis_complete", {"attempts": attempt + 1, "passed": validation_passed})

        print(f"\n{'='*70}")
        print(f"SYNTHESIS COMPLETE: {attempt + 1} attempt(s), Validation: {validation_passed}")
        print(f"Total synthesis time: {total_synthesis_time:.2f}s")
        print(f"{'='*70}\n")

        # Build final response
        disclaimer = POST_ANSWER_DISCLAIMERS.get(self.country, "")

        response = f"""## Your Current Situation

{situation}

## Analysis & Insights

{insights}

## Our Recommendation

{recommendations}

---

## Important Disclaimer

{disclaimer}

*Response for {self.country} | Session: {self.session_id[:8]} | Validated: {attempt + 1} attempt(s)*"""

        # De-anonymize (only if anonymization was enabled)
        if anonymize and member_token:
            response = response.replace(member_token, real_name)
            print(f"🔓 Restored: '{member_token}' → '{real_name}'")

        tool_result['_timings'] = timings
        tool_result['_tools_called'] = tools_called

        total_elapsed = time.time() - overall_start
        timings['total'] = total_elapsed

        self._log_query_audit(member_id, user_query, response, total_elapsed, len(tools_called))

        print(f"\n✅ Completed in {total_elapsed:.2f}s")
        print(f"{'='*70}\n")

        return response, tool_result
