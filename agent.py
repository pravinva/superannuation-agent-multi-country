# agent.py - UPDATED FOR UC FUNCTIONS (12 FUNCTIONS)
"""
Multi-Country Retirement Advisor Agent
- Supports 4 countries: Australia, USA, UK, India
- Calls UC Functions (3 per country = 12 total)
- Configurable validation modes: llm_judge, hybrid, deterministic
- Logs to Unity Catalog and MLflow
- Implements retry logic with judge feedback
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from tools import calculate_retirement_advice  # UPDATED IMPORT
from validation import LLMJudgeValidator, DeterministicValidator
from country_content import COUNTRY_PROMPTS, COUNTRY_REGULATIONS, POST_ANSWER_DISCLAIMERS
from config import MAIN_LLM_ENDPOINT, JUDGE_LLM_ENDPOINT, MAIN_LLM_TEMPERATURE, SQL_WAREHOUSE_ID
from data_utils import get_member_by_id
import json
import time
import uuid
from datetime import datetime


class MultiCountryAdvisorAgent:
    """Multi-country retirement advisor with UC Functions integration"""

    def __init__(self, country="Australia"):
        self.w = WorkspaceClient()
        self.country = country
        self.main_endpoint = MAIN_LLM_ENDPOINT
        self.judge_endpoint = JUDGE_LLM_ENDPOINT
        self.session_id = str(uuid.uuid4())
        self.warehouse_id = SQL_WAREHOUSE_ID  # ADDED

        self.validator = LLMJudgeValidator(judge_endpoint=self.judge_endpoint)

        print(f"✓ Multi-Country Advisor Agent initialized")
        print(f"  Country: {country}")
        print(f"  Main LLM: {self.main_endpoint}")
        print(f"  Judge LLM: {self.judge_endpoint}")
        print(f"  Warehouse: {self.warehouse_id}")  # ADDED

    def call_claude(self, messages, max_tokens=2000, temperature=None, endpoint=None):
        """Call Claude endpoint via Databricks SDK"""
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
        """Safely convert value to integer"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _log_query_audit(self, member_id, user_query, response_text, total_time, 
                         tools_count, validation_mode="llm_judge", validation_attempts=1,
                         validation_result=None):
        """
        Log query to BOTH Unity Catalog AND MLflow
        """

        # 1. Log to Unity Catalog
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
                citations=[f"{self.country} Tax Authority", f"{self.country} Pension Authority"],
                tool_used=f"{self.country}_calculator",
                judge_response="",
                judge_verdict="Pass" if validation_result and validation_result.get('passed') else "Review",
                error_info="",
                cost=0.0,
                validation_mode=validation_mode,
                validation_attempts=validation_attempts,
                total_time_seconds=total_time
            )
            print(f"✓ Logged to Unity Catalog: session {self.session_id[:8]}")
        except Exception as e:
            print(f"❌ UC audit logging failed: {e}")

        # 2. Log to MLflow
        try:
            from mlflow_utils import log_mlflow_run
            from config import MLFLOW_PROD_EXPERIMENT_PATH

            params = {
                "country": self.country,
                "member_id": member_id,
                "session_id": self.session_id,
                "main_llm": self.main_endpoint,
                "judge_llm": self.judge_endpoint,
                "validation_mode": validation_mode,
                "query": user_query[:200]
            }

            metrics = {
                "total_time_seconds": total_time,
                "tools_called": tools_count,
                "response_length": len(response_text),
                "validation_attempts": validation_attempts,
                "validation_passed": 1 if (validation_result and validation_result.get('passed')) else 0,
                "validation_confidence": validation_result.get('confidence', 0.0) if validation_result else 0.0,
                "validation_violations": len(validation_result.get('violations', [])) if validation_result else 0
            }

            artifacts = {
                "query": user_query,
                "response": response_text,
                "validation_result": str(validation_result) if validation_result else "None"
            }

            log_mlflow_run(
                experiment_path=MLFLOW_PROD_EXPERIMENT_PATH,
                params=params,
                metrics=metrics,
                artifacts=artifacts
            )

            print(f"✓ Logged to MLflow: {MLFLOW_PROD_EXPERIMENT_PATH}")

        except Exception as e:
            print(f"❌ MLflow logging failed: {e}")


    def process_query(self, member_id, user_query, status_callback=None,
                      temperature=None, anonymize=False, enable_validation=True,
                      validation_mode="llm_judge"):
        """
        Main agentic workflow with UC Functions integration

        Args:
            member_id: Member identifier
            user_query: User's retirement question
            status_callback: Optional callback for real-time updates
            temperature: LLM temperature (None = use default)
            anonymize: Whether to anonymize member name (default: False)
            enable_validation: Whether to run validation
            validation_mode: "llm_judge", "hybrid", or "deterministic"

        Returns:
            Tuple: (response_text, tool_results_dict)
        """

        overall_start = time.time()
        temp = temperature if temperature is not None else MAIN_LLM_TEMPERATURE

        print(f"\n{'='*70}")
        print(f"AGENT: Processing query for {self.country}")
        print(f"Member: {member_id}")
        print(f"Query: {user_query}")
        print(f"Validation Mode: {validation_mode}")
        print(f"{'='*70}\n")

        timings = {}
        tools_called = []

        # Get member profile from database
        profile_df = get_member_by_id(member_id)
        if profile_df is None or profile_df.empty:
            return "Member profile not found", {"error": "Member not found"}

        profile = profile_df.to_dict('records')[0]

        # Convert numeric fields to integers
        numeric_fields = ['age', 'super_balance', 'other_assets', 'debt',
                         'preservation_age', 'annual_income_outside_super',
                         'dependents', 'account_based_pension']

        for field in numeric_fields:
            if field in profile:
                profile[field] = self._convert_to_int(profile[field])

        # Extract first name for personalization
        member_full_name = profile['name']
        member_first_name = member_full_name.split()[0] if member_full_name else 'Member'

        # Currency code based on country
        currency_codes = {
            "Australia": "AUD",
            "USA": "USD",
            "United Kingdom": "GBP",
            "India": "INR"
        }
        currency_code = currency_codes.get(self.country, "AUD")

        # Anonymization
        real_name = profile['name']
        if anonymize:
            member_token = f"Member {member_id[-4:]}"
            profile['name'] = member_token
            print(f"🔒 Anonymized: '{real_name}' → '{member_token}'")
        else:
            member_token = None
            print(f"✅ Using real name: '{real_name}'")

        # STEP 1: Call UC Functions (3 functions per country)
        if status_callback:
            status_callback("tool_start", f"Calling {self.country} UC Functions...")

        tool_start = time.time()
        
        # UPDATED: Call calculate_retirement_advice which calls 3 UC functions
        tool_result = calculate_retirement_advice(
            member_id=member_id,
            withdrawal_amount=100000,  # Default withdrawal amount
            country=self.country,
            warehouse_id=self.warehouse_id  # ADDED warehouse_id
        )
        
        tool_duration = time.time() - tool_start

        # Extract tools_called from result (includes all 3 UC functions)
        if 'tools_called' in tool_result:
            tools_called = tool_result['tools_called']
        else:
            tools_called = [{
                "name": f"{self.country} Calculator",
                "duration": tool_duration,
                "status": "completed"
            }]

        print(f"✓ UC Functions executed in {tool_duration:.2f}s")
        print(f"  → {len(tools_called)} functions called")

        if status_callback:
            status_callback("tool_complete", None)

        # STEP 2: Multi-stage synthesis with validation retry loop
        regulations = COUNTRY_REGULATIONS.get(self.country, {})

        context = f"""MEMBER PROFILE:
Name: {profile['name']}
First Name: {member_first_name}
Age: {profile.get('age')}
Preservation Age: {profile.get('preservation_age', 60)}
Balance: {currency_code} {profile.get('super_balance', 0)}
Employment: {profile.get('employment_status')}
Marital Status: {profile.get('marital_status')}
Country: {self.country}

REGULATORY CONTEXT:
{json.dumps(regulations, indent=2)}

UC FUNCTION RESULTS (3 calculations):
{json.dumps(tool_result, indent=2, default=str)}

USER QUESTION:
{user_query}"""

        if status_callback:
            status_callback("synthesis_start", None)

        synthesis_start = time.time()

        # Retry loop configuration
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
                print(f"RETRY REASON: Validation failed")
            print(f"{'='*70}\n")

            # Stage 1: Situation Analysis
            if status_callback:
                status_callback("synthesis_stage", {"stage": 1, "task": "Analyzing Situation"})

            situation_prompt = f"""You are a {self.country} retirement advisor. Analyze this member's situation based on the data provided.

{context}

{"IMPORTANT - CORRECTION NEEDED: " + validation_feedback if validation_feedback else ""}

Write a 2-3 sentence situation summary that:
- Uses the member's FIRST NAME ({member_first_name})
- States their ACTUAL age ({profile.get('age')}) and balance
- Mentions their specific question

RESPONSE FORMAT:
[Your analysis here - 2-3 sentences only]"""

            situation, _ = self.call_claude([
                {"role": "user", "content": situation_prompt}
            ], max_tokens=300, temperature=temp)

            print(f"✓ Stage 1 (Situation): {len(situation)} chars")

            # Stage 2: Insights from UC Functions
            if status_callback:
                status_callback("synthesis_stage", {"stage": 2, "task": "Generating Insights"})

            insights_prompt = f"""Based on the UC Function results, provide 3-4 key insights.

{context}

SITUATION ANALYSIS:
{situation}

{"CORRECTION NEEDED: " + validation_feedback if validation_feedback else ""}

Generate 3-4 insights as bullet points:
• [Insight 1 from tax calculation]
• [Insight 2 from government benefit]
• [Insight 3 from projection]
• [Insight 4 - optional]

CRITICAL: Use EXACT numbers from UC Function results. Double-check all ages and amounts."""

            insights, _ = self.call_claude([
                {"role": "user", "content": insights_prompt}
            ], max_tokens=600, temperature=temp)

            print(f"✓ Stage 2 (Insights): {len(insights)} chars")

            # Stage 3: Recommendations
            if status_callback:
                status_callback("synthesis_stage", {"stage": 3, "task": "Creating Recommendations"})

            recommendations_prompt = f"""Based on the analysis and UC Function results, provide 3 specific recommendations.

{context}

SITUATION:
{situation}

INSIGHTS:
{insights}

{"FIX THESE ISSUES: " + validation_feedback if validation_feedback else ""}

Provide exactly 3 numbered recommendations:
1. [Specific actionable recommendation]
2. [Second specific recommendation]
3. [Third specific recommendation]

Use member's first name ({member_first_name}). Be specific and actionable."""

            recommendations, _ = self.call_claude([
                {"role": "user", "content": recommendations_prompt}
            ], max_tokens=600, temperature=temp)

            print(f"✓ Stage 3 (Recommendations): {len(recommendations)} chars")

            # Combine stages
            final_response = f"""## Your Situation

{situation}

---

## Key Insights

{insights}

---

## Recommendations

{recommendations}

---

*Based on {len(tools_called)} regulatory calculations for {self.country}*"""

            synthesis_duration = time.time() - synthesis_start
            print(f"✓ Synthesis complete: {synthesis_duration:.2f}s")

            # STEP 3: Validation
            if enable_validation:
                if status_callback:
                    status_callback("validation_start", None)

                validation_start = time.time()

                if validation_mode == "llm_judge":
                    validation_result = self.validator.validate_response(
                        final_response, profile, tool_result, user_query
                    )
                elif validation_mode == "deterministic":
                    validation_result = DeterministicValidator.validate_response(
                        final_response, profile, tool_result
                    )
                elif validation_mode == "hybrid":
                    det_result = DeterministicValidator.validate_response(
                        final_response, profile, tool_result
                    )
                    if det_result['passed']:
                        validation_result = det_result
                    else:
                        validation_result = self.validator.validate_response(
                            final_response, profile, tool_result, user_query
                        )
                else:
                    validation_result = {"passed": True, "violations": [], "reasoning": "Validation disabled"}

                validation_duration = time.time() - validation_start
                validation_passed = validation_result.get('passed', False)

                print(f"✓ Validation ({validation_mode}): {validation_duration:.2f}s")
                print(f"  Result: {'PASSED' if validation_passed else 'FAILED'}")
                print(f"  Violations: {len(validation_result.get('violations', []))}")

                if status_callback:
                    status_callback("validation_complete", {
                        "passed": validation_passed,
                        "violations": len(validation_result.get('violations', []))
                    })

                if not validation_passed and attempt < MAX_RETRIES:
                    # Prepare feedback for retry
                    violations = validation_result.get('violations', [])
                    critical = [v for v in violations if v.get('severity') == 'CRITICAL']
                    
                    if critical:
                        validation_feedback = "; ".join([
                            f"{v['code']}: {v['detail']}" for v in critical
                        ])
                    else:
                        validation_feedback = validation_result.get('reasoning', 'Please correct errors')

                    if status_callback:
                        status_callback("retry", {
                            "attempt": attempt + 2,
                            "violations": len(critical)
                        })

                    attempt += 1
                    continue
                else:
                    break
            else:
                validation_result = {"passed": True, "violations": [], "reasoning": "Validation disabled"}
                validation_passed = True
                break

        if status_callback:
            status_callback("synthesis_complete", {"attempts": attempt + 1})

        # STEP 4: Log to audit
        total_duration = time.time() - overall_start
        
        self._log_query_audit(
            member_id=member_id,
            user_query=user_query,
            response_text=final_response,
            total_time=total_duration,
            tools_count=len(tools_called),
            validation_mode=validation_mode,
            validation_attempts=attempt + 1,
            validation_result=validation_result
        )

        # Build result dict with all metadata
        result_dict = {
            "_tools_called": tools_called,
            "_validation": validation_result,
            "citations": tool_result.get('citations', []),
            "member_data": profile,
            "timings": {
                "total": total_duration,
                "tool": tool_duration,
                "synthesis": synthesis_duration
            }
        }

        # Add tool results
        result_dict.update(tool_result)

        print(f"\n{'='*70}")
        print(f"COMPLETED: {total_duration:.2f}s total")
        print(f"  Tool: {tool_duration:.2f}s ({len(tools_called)} UC functions)")
        print(f"  Synthesis: {synthesis_duration:.2f}s (attempt {attempt + 1})")
        print(f"  Validation: {validation_result.get('confidence', 0.0):.0%} confidence")
        print(f"{'='*70}\n")

        return final_response, result_dict
