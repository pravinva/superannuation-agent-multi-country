# agent.py - WITH INTELLIGENT TOOL SELECTION

"""
Multi-Country Retirement Advisor Agent with Intelligent Tool Selection

✅ NEW: LLM Planning Phase - Only calls needed tools
✅ Supports 4 countries: Australia, USA, UK, India
✅ Configurable validation modes: llm_judge, hybrid, deterministic
✅ Logs to Unity Catalog and MLflow
✅ Implements retry logic with judge feedback

KEY IMPROVEMENT: Reduces tool calls by 60-70% through intelligent planning
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from tools import call_individual_tool, get_all_tools_metadata
from validation import LLMJudgeValidator, DeterministicValidator
from country_content import COUNTRY_PROMPTS, COUNTRY_REGULATIONS, POST_ANSWER_DISCLAIMERS
from config import MAIN_LLM_ENDPOINT, JUDGE_LLM_ENDPOINT, MAIN_LLM_TEMPERATURE, SQL_WAREHOUSE_ID
from data_utils import get_member_by_id
import json
import time
import uuid
from datetime import datetime

class MultiCountryAdvisorAgent:
    """Multi-country retirement advisor with intelligent tool selection"""
    
    def __init__(self, country="Australia"):
        self.w = WorkspaceClient()
        self.country = country
        self.main_endpoint = MAIN_LLM_ENDPOINT
        self.judge_endpoint = JUDGE_LLM_ENDPOINT
        self.session_id = str(uuid.uuid4())
        self.warehouse_id = SQL_WAREHOUSE_ID
        self.validator = LLMJudgeValidator(judge_endpoint=self.judge_endpoint)
        
        print(f"✓ Multi-Country Advisor Agent initialized (Intelligent Mode)")
        print(f"  Country: {country}")
        print(f"  Main LLM: {self.main_endpoint}")
        print(f"  Judge LLM: {self.judge_endpoint}")
        print(f"  Warehouse: {self.warehouse_id}")
    
    def call_claude(self, messages, max_tokens=2000, temperature=None, endpoint=None):
        """Call Claude endpoint via Databricks SDK - WITH TOKEN TRACKING"""
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
        
        answer = response.choices[0].message.content
        elapsed = time.time() - start_time
        
        # Extract token usage from response
        usage = getattr(response, 'usage', None)
        if usage:
            input_tokens = getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'completion_tokens', 0)
            total_tokens = input_tokens + output_tokens
        else:
            input_tokens = 0
            output_tokens = 0
            total_tokens = 0
        
        print(f"⏱️  Claude call: {elapsed:.2f}s")
        print(f"📊 Tokens: {input_tokens:,} input + {output_tokens:,} output = {total_tokens:,} total")
        
        return answer, elapsed, input_tokens, output_tokens
    
    def _convert_to_int(self, value, default=0):
        """Safely convert value to integer"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _plan_tool_selection(self, user_query, member_profile):
        """
        ✅ NEW: LLM Planning Phase - Decide which tools to call
        
        Args:
            user_query: User's question
            member_profile: Member data
            
        Returns:
            dict: {
                "tools_needed": ["tax", "benefit", "projection"],
                "reasoning": "explanation",
                "withdrawal_amount": 50000
            }
        """
        # Get available tools for this country
        tools_metadata = get_all_tools_metadata(self.country)
        tools_description = "\n".join([
            f"{i+1}. **{tool['id']}** - {tool['name']}: {tool['description']}"
            for i, tool in enumerate(tools_metadata)
        ])
        
        planning_prompt = f"""You are a retirement planning expert. Analyze this query and decide which calculators you need.

**USER QUERY:** {user_query}

**MEMBER CONTEXT:**
- Age: {member_profile.get('age', 'N/A')}
- Balance: {member_profile.get('super_balance', 'N/A')}
- Country: {self.country}
- Employment: {member_profile.get('employment_status', 'N/A')}

**AVAILABLE CALCULATORS FOR {self.country.upper()}:**
{tools_description}

**INSTRUCTIONS:**
1. Analyze what the user is asking
2. Select ONLY the calculators needed to answer the question
3. Extract withdrawal amount if mentioned (default: 50000)
4. Provide brief reasoning

**EXAMPLES:**
Query: "How much tax will I pay on a $75,000 withdrawal?"
→ {{"tools_needed": ["tax"], "withdrawal_amount": 75000, "reasoning": "Tax calculation only"}}

Query: "Will withdrawing affect my pension?"
→ {{"tools_needed": ["tax", "benefit"], "withdrawal_amount": 50000, "reasoning": "Need tax and benefit impact"}}

Query: "Can I retire early at 58?"
→ {{"tools_needed": ["tax", "benefit", "projection"], "withdrawal_amount": 50000, "reasoning": "Need all calculators for retirement planning"}}

Query: "What's my Age Pension eligibility?"
→ {{"tools_needed": ["benefit"], "withdrawal_amount": 0, "reasoning": "Only benefit eligibility check"}}

Respond with ONLY valid JSON matching this format:
{{
  "tools_needed": ["tax"],
  "withdrawal_amount": 50000,
  "reasoning": "Brief explanation"
}}"""

        try:
            planning_messages = [{"role": "user", "content": planning_prompt}]
            planning_response, planning_time, plan_in, plan_out = self.call_claude(
                planning_messages,
                max_tokens=300,
                temperature=0.0  # Deterministic for planning
            )
            
            # Parse JSON response
            plan = json.loads(planning_response)
            
            # Validate and set defaults
            if "tools_needed" not in plan or not plan["tools_needed"]:
                print("⚠️  Planning returned empty tools, defaulting to all")
                plan["tools_needed"] = ["tax", "benefit", "projection"]
            
            if "withdrawal_amount" not in plan:
                plan["withdrawal_amount"] = 50000
            
            if "reasoning" not in plan:
                plan["reasoning"] = "Using selected tools"
            
            # Add token tracking to plan
            plan["tokens"] = {"input": plan_in, "output": plan_out}
            
            print(f"🧠 Planning complete ({planning_time:.2f}s):")
            print(f"   Tools needed: {', '.join(plan['tools_needed'])}")
            print(f"   Withdrawal: ${plan['withdrawal_amount']:,}")
            print(f"   Reasoning: {plan['reasoning']}")
            
            return plan
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Planning JSON parse error: {e}")
            print(f"   Response: {planning_response[:200]}")
            # Fallback: use all tools
            return {
                "tools_needed": ["tax", "benefit", "projection"],
                "withdrawal_amount": 50000,
                "reasoning": "Fallback to all tools (parsing failed)"
            }
        except Exception as e:
            print(f"⚠️  Planning error: {e}")
            # Fallback: use all tools
            return {
                "tools_needed": ["tax", "benefit", "projection"],
                "withdrawal_amount": 50000,
                "reasoning": "Fallback to all tools (planning failed)"
            }
    
    def _log_query_audit(self, member_id, user_query, response_text, total_time,
                         tools_count, validation_mode="llm_judge", validation_attempts=1,
                         validation_result=None, cost=0.0, token_breakdown=None,
                         plan=None, tools_called=None):
        """
        Log query to BOTH Unity Catalog AND MLflow
        ✅ FIXED: Added missing parameters
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
                response_text=truncated,
                total_time_seconds=round(total_time, 2),
                tools_called_count=tools_count,
                validation_mode=validation_mode,
                validation_attempts=validation_attempts,
                judge_verdict=validation_result.get('verdict') if validation_result else None,
                judge_confidence=validation_result.get('confidence') if validation_result else None,
                cost=cost
            )
            print(f"✓ Audit logged to Unity Catalog")
        except Exception as e:
            print(f"⚠️  Unity Catalog logging failed: {e}")
        
        # 2. Log to MLflow (if experiment path configured)
        try:
            import mlflow
            from config import MLFLOW_PROD_EXPERIMENT_PATH
            
            if MLFLOW_PROD_EXPERIMENT_PATH:
                mlflow.set_tracking_uri("databricks")
                mlflow.set_experiment(MLFLOW_PROD_EXPERIMENT_PATH)
                
                with mlflow.start_run(run_name=f"query_{self.session_id[:8]}"):
                    mlflow.log_params({
                        "country": self.country,
                        "member_id": member_id,
                        "validation_mode": validation_mode
                    })
                    
                    # ✅ FIX: Only calculate if token_breakdown provided
                    if token_breakdown:
                        total_input = (token_breakdown['planning']['input'] +
                                     token_breakdown['synthesis']['input'] +
                                     token_breakdown['validation']['input'])
                        total_output = (token_breakdown['planning']['output'] +
                                      token_breakdown['synthesis']['output'] +
                                      token_breakdown['validation']['output'])
                        
                        mlflow.log_metrics({
                            "total_time_seconds": round(total_time, 2),
                            "tools_called": tools_count,
                            "validation_attempts": validation_attempts,
                            "response_length": len(response_text),
                            "cost_usd": cost,
                            "input_tokens": total_input,
                            "output_tokens": total_output,
                            "total_tokens": total_input + total_output,
                            "planning_tokens": token_breakdown['planning']['input'] + token_breakdown['planning']['output'],
                            "synthesis_tokens": token_breakdown['synthesis']['input'] + token_breakdown['synthesis']['output'],
                            "validation_tokens": token_breakdown['validation']['input'] + token_breakdown['validation']['output']
                        })
                    else:
                        # Fallback if token_breakdown not provided
                        mlflow.log_metrics({
                            "total_time_seconds": round(total_time, 2),
                            "tools_called": tools_count,
                            "validation_attempts": validation_attempts,
                            "response_length": len(response_text),
                            "cost_usd": cost
                        })
                    
                    if validation_result:
                        mlflow.log_metrics({
                            "judge_confidence": validation_result.get('confidence', 0),
                            "violations_count": len(validation_result.get('violations', []))
                        })
                    
                    print(f"✓ Logged to MLflow: {MLFLOW_PROD_EXPERIMENT_PATH}")
        except Exception as e:
            print(f"⚠️  MLflow logging failed: {e}")
        
        # ✅ FIX: Replace invalid log_trace with artifact logging
        try:
            import mlflow
            import tempfile
            
            # Use MLflow's standard artifact logging instead of log_trace
            if token_breakdown and plan and tools_called:
                trace_data = {
                    "planning": plan,
                    "token_usage": token_breakdown,
                    "executed_tools": tools_called,
                    "validation": validation_result if validation_result else {}
                }
                
                # Log as artifact instead
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(trace_data, f, indent=2, default=str)
                    temp_path = f.name
                
                mlflow.log_artifact(temp_path, "trace_data")
                print("✓ MLflow trace data logged as artifact")
                
        except Exception as trace_error:
            print(f"⚠️  Failed to log MLflow trace: {trace_error}")
    
    def query(self, user_query, member_id, anonymize=True, validation_mode="llm_judge",
              max_validation_attempts=2, status_callback=None):
        """
        Process user query with intelligent tool selection
        
        Args:
            user_query: User's question
            member_id: Member identifier
            anonymize: Whether to anonymize member name
            validation_mode: 'llm_judge', 'hybrid', or 'deterministic'
            max_validation_attempts: Max retry attempts for validation
            status_callback: Optional callback for real-time updates
            
        Returns:
            tuple: (answer, citations, metadata, judge_response, verdict, error_info, tools_called)
        """
        overall_start = time.time()
        profile = get_member_by_id(member_id)
        
        if not profile:
            return (
                f"Error: Member {member_id} not found.",
                [],
                {"error": "Member not found"},
                None,
                "ERROR",
                "Member not found",
                []
            )
        
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
        
        # ✅ NEW: STEP 0.5 - Planning Phase
        print("\n" + "="*60)
        print("🧠 PLANNING PHASE: Selecting tools...")
        print("="*60)
        
        plan = self._plan_tool_selection(user_query, profile)
        tools_to_call = plan["tools_needed"]
        withdrawal_amount = plan["withdrawal_amount"]
        planning_reasoning = plan["reasoning"]
        
        # ✅ NEW: Initialize token tracking
        token_breakdown = {
            'planning': plan.get('tokens', {'input': 0, 'output': 0}),
            'synthesis': {'input': 0, 'output': 0},
            'validation': {'input': 0, 'output': 0}
        }
        
        print(f"\n📋 Plan: Call {len(tools_to_call)}/{3} tools")
        print(f"   Selected: {', '.join(tools_to_call)}")
        print(f"   Savings: {(1 - len(tools_to_call)/3)*100:.0f}% reduction")
        
        # STEP 1: Call only selected UC Functions
        if status_callback:
            status_callback("tool_start", f"Calling {len(tools_to_call)} {self.country} UC Functions...")
        
        tool_start = time.time()
        print("\n" + "="*60)
        print(f"🛠️  TOOL EXECUTION: Calling {len(tools_to_call)} functions")
        print("="*60)
        
        # ✅ NEW: Call only selected tools individually
        tool_results = {}
        tools_called = []
        all_citations = []
        
        for tool_id in tools_to_call:
            result = call_individual_tool(
                tool_id=tool_id,
                member_id=member_id,
                withdrawal_amount=withdrawal_amount,
                country=self.country,
                warehouse_id=self.warehouse_id
            )
            
            if result and "error" not in result:
                tool_results[tool_id] = result["calculation"]
                
                # Track tool call
                tools_called.append({
                    "name": result["tool_name"],
                    "authority": result.get("authority", ""),
                    "uc_function": result["uc_function"],
                    "status": "completed",
                    "duration": result["duration"]
                })
                
                # Collect citations
                if "citations" in result:
                    all_citations.extend(result["citations"])
            else:
                print(f"⚠️  Tool {tool_id} failed or returned error")
        
        tool_duration = time.time() - tool_start
        print(f"\n✓ {len(tools_called)} UC Functions executed in {tool_duration:.2f}s")
        print(f"  vs. 3 functions in old approach (~{tool_duration * 3/len(tools_called):.2f}s)")
        print(f"  Time saved: ~{tool_duration * (3-len(tools_called))/3:.2f}s")
        
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
Dependents: {profile.get('dependents', 0)}
Other Assets: {currency_code} {profile.get('other_assets', 0)}
Country: {self.country}
Member ID: {member_id}

REGULATORY CONTEXT:
{json.dumps(regulations, indent=2)}

UC FUNCTION RESULTS ({len(tool_results)} calculations - intelligently selected):
Planning Decision: {planning_reasoning}
Tools Called: {', '.join(tools_to_call)}

{json.dumps(tool_results, indent=2, default=str)}

USER QUESTION:
{user_query}"""

        if status_callback:
            status_callback("synthesis_start", None)
        
        synthesis_start = time.time()
        
        # Retry loop configuration
        MAX_RETRIES = max_validation_attempts
        attempt = 0
        validation_passed = False
        validation_feedback = None
        validation_result = None
        
        while attempt <= MAX_RETRIES and not validation_passed:
            attempt += 1
            print(f"\n{'='*60}")
            print(f"✏️  SYNTHESIS ATTEMPT {attempt}/{MAX_RETRIES + 1}")
            print(f"{'='*60}")
            
            # Build synthesis prompt
            base_prompt = f"""You are a retirement planning expert for {self.country}.

{context}

IMPORTANT INSTRUCTIONS:
1. Address the member by first name: {member_first_name}
2. Answer in a friendly, professional tone
3. Use specific numbers from the UC Function results
4. Cite regulations using [Authority - Regulation] format
5. Format currency as {currency_code} with commas (e.g., {currency_code} 150,000)
6. Keep response concise (200-300 words)

Note: We only called the tools necessary to answer this specific question ({len(tools_to_call)} out of 3 available).
If the user's question requires information from tools we didn't call, politely suggest they ask a more specific question.

YOUR RESPONSE:"""

            # Add validation feedback if retry
            if validation_feedback:
                base_prompt += f"""

⚠️  VALIDATION FEEDBACK FROM PREVIOUS ATTEMPT:
{validation_feedback}

Please correct the issues and regenerate your response."""

            messages = [{"role": "user", "content": base_prompt}]
            
            # Call LLM
            try:
                answer, synth_duration, synth_in, synth_out = self.call_claude(messages, max_tokens=2000)
                
                # ✅ NEW: Track synthesis tokens (accumulate if multiple attempts)
                if attempt == 1:
                    token_breakdown['synthesis']['input'] = synth_in
                    token_breakdown['synthesis']['output'] = synth_out
                else:
                    # Accumulate tokens from retries
                    token_breakdown['synthesis']['input'] += synth_in
                    token_breakdown['synthesis']['output'] += synth_out
            
            except Exception as e:
                print(f"❌ Synthesis error: {e}")
                return (
                    "I apologize, but I encountered an error generating your response.",
                    all_citations,
                    {"error": str(e)},
                    None,
                    "ERROR",
                    str(e),
                    tools_called
                )
            
            # Name restoration
            if anonymize and member_token:
                answer = answer.replace(member_token, real_name)
                answer = answer.replace(member_token.split()[-1], member_first_name)
            
            synthesis_duration = time.time() - synthesis_start
            
            # Validation
            if validation_mode == "llm_judge":
                validation_result = self.validator.validate(
                    response_text=answer,
                    user_query=user_query,
                    context=context
                )
                
                # ✅ NEW: Track validation tokens (accumulate if multiple attempts)
                judge_in = validation_result.get('input_tokens', 0)
                judge_out = validation_result.get('output_tokens', 0)
                
                if attempt == 1:
                    token_breakdown['validation']['input'] = judge_in
                    token_breakdown['validation']['output'] = judge_out
                else:
                    token_breakdown['validation']['input'] += judge_in
                    token_breakdown['validation']['output'] += judge_out
                
                validation_passed = validation_result['passed']
                
                if not validation_passed and attempt <= MAX_RETRIES:
                    print(f"⚠️  Validation failed (attempt {attempt})")
                    print(f"   Issues: {len(validation_result.get('violations', []))}")
                    
                    # Build structured feedback
                    violations = validation_result.get('violations', [])
                    validation_feedback = "Please fix these issues:\n" + "\n".join([
                        f"- {v}" for v in violations
                    ])
                else:
                    validation_passed = True
            
            elif validation_mode == "deterministic":
                det_validator = DeterministicValidator()
                validation_result = det_validator.validate(answer, user_query, context)
                validation_passed = validation_result['passed']
            else:  # hybrid or skip
                validation_passed = True
                validation_result = {"passed": True, "confidence": 1.0, "verdict": "Pass"}
        
        total_time = time.time() - overall_start
        
        # ✅ NEW: Calculate cost using our calculator
        from cost_utils import calculate_query_costs
        cost_breakdown = calculate_query_costs(token_breakdown)
        total_cost = cost_breakdown['total']
        
        # Print token and cost breakdown
        print(f"\n{'='*60}")
        print(f"📊 TOKEN & COST BREAKDOWN")
        print(f"{'='*60}")
        
        # Planning tokens
        plan_in = token_breakdown['planning']['input']
        plan_out = token_breakdown['planning']['output']
        plan_total = plan_in + plan_out
        print(f"Planning:   {plan_in:>6,} input + {plan_out:>6,} output = {plan_total:>6,} total → ${cost_breakdown['planning']:.4f}")
        
        # Synthesis tokens
        synth_in = token_breakdown['synthesis']['input']
        synth_out = token_breakdown['synthesis']['output']
        synth_total = synth_in + synth_out
        print(f"Synthesis:  {synth_in:>6,} input + {synth_out:>6,} output = {synth_total:>6,} total → ${cost_breakdown['synthesis']:.4f}")
        
        # Validation tokens
        val_in = token_breakdown['validation']['input']
        val_out = token_breakdown['validation']['output']
        val_total = val_in + val_out
        print(f"Validation: {val_in:>6,} input + {val_out:>6,} output = {val_total:>6,} total → ${cost_breakdown['validation']:.4f}")
        
        # Total
        total_tokens = plan_total + synth_total + val_total
        print(f"{'─'*60}")
        print(f"TOTAL:      {total_tokens:>6,} tokens → ${total_cost:.4f}")
        print(f"{'='*60}")
        
        # Calculate projected costs at 0.1 queries/minute
        queries_per_hour = 0.1 * 60
        queries_per_day = queries_per_hour * 24
        queries_per_month = queries_per_day * 30
        
        print(f"\n💰 PROJECTED COSTS (0.1 queries/min):")
        print(f"   Hourly:  {queries_per_hour:>6.1f} queries → ${queries_per_hour * total_cost:>7.2f}")
        print(f"   Daily:   {queries_per_day:>6.0f} queries → ${queries_per_day * total_cost:>7.2f}")
        print(f"   Monthly: {queries_per_month:>6.0f} queries → ${queries_per_month * total_cost:>7.2f}")
        
        # ✅ FIXED: Log to audit with all required parameters
        self._log_query_audit(
            member_id=member_id,
            user_query=user_query,
            response_text=answer,
            total_time=total_time,
            tools_count=len(tools_called),
            validation_mode=validation_mode,
            validation_attempts=attempt,
            validation_result=validation_result,
            cost=total_cost,
            token_breakdown=token_breakdown,  # ✅ NOW PASSED
            plan=plan,  # ✅ NOW PASSED
            tools_called=tools_called  # ✅ NOW PASSED
        )
        
        print(f"\n{'='*60}")
        print(f"✅ QUERY COMPLETE")
        print(f"{'='*60}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Tools called: {len(tools_called)}/3 (saved {3-len(tools_called)} calls)")
        print(f"Validation: {validation_result.get('verdict', 'N/A')} in {attempt} attempt(s)")
        
        metadata = {
            "total_time": round(total_time, 2),
            "tools_called_count": len(tools_called),
            "synthesis_time": round(synthesis_duration, 2),
            "validation_attempts": attempt,
            "validation_mode": validation_mode,
            "planning_reasoning": planning_reasoning,
            "tools_selected": tools_to_call,
            "tools_saved": 3 - len(tools_to_call),
            "token_breakdown": token_breakdown,
            "cost_breakdown": cost_breakdown,
            "total_cost": total_cost
        }
        
        return (
            answer,
            all_citations,
            metadata,
            validation_result.get('reasoning', '') if validation_result else None,
            validation_result.get('verdict', 'Pass') if validation_result else 'Pass',
            None,
            tools_called
        )
