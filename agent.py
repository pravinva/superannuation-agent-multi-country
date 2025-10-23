# agent.py - Multi-Country Retirement Advisor Agent
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from tools import get_country_tool
from validation import LLMJudgeValidator
from country_content import COUNTRY_PROMPTS, COUNTRY_REGULATIONS, POST_ANSWER_DISCLAIMERS
from config import MAIN_LLM_ENDPOINT, JUDGE_LLM_ENDPOINT, MAIN_LLM_TEMPERATURE
from data_utils import get_member_by_id
import json
import time
import uuid
from datetime import datetime


class MultiCountryAdvisorAgent:
    """Multi-country retirement advisor using Claude Opus 4.1"""
    
    def __init__(self, country="Australia"):
        self.w = WorkspaceClient()
        self.country = country
        self.main_endpoint = MAIN_LLM_ENDPOINT
        self.judge_endpoint = JUDGE_LLM_ENDPOINT
        self.session_id = str(uuid.uuid4())
        
        # Initialize LLM Judge validator
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
        """Main agentic workflow"""
        
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
        
        # Anonymization
        real_name = profile['name']
        if anonymize:
            member_token = f"Member {member_id[-4:]}"
            profile['name'] = member_token
            print(f"🔒 Anonymized: '{real_name}' → '{member_token}'")
        else:
            member_token = None
        
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
        
        # STEP 2: Multi-stage synthesis
        regulations = COUNTRY_REGULATIONS.get(self.country, {})
        
        context = f"""MEMBER PROFILE:
Name: {profile['name']}
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
        
        # Stage 1: Situation
        if status_callback:
            status_callback("synthesis_stage", {"stage": 1, "task": "Situation"})
        
        situation_prompt = f"""{context}

Write EXACTLY 2 sentences about {profile['name']}'s retirement situation in {self.country}.

RULES:
- EXACTLY 2 sentences, max 40 words each
- Use their actual data (age, balance)
- NO asterisks or special characters

Write directly (no headers)."""
        
        situation, sit_time = self.call_claude(
            [{"role": "user", "content": situation_prompt}],
            max_tokens=250,
            temperature=temp
        )
        timings['situation'] = sit_time
        
        # Stage 2: Insights
        if status_callback:
            status_callback("synthesis_stage", {"stage": 2, "task": "Insights"})
        
        insights_prompt = f"""{context}

Write EXACTLY 3 key insights for {self.country} retirement planning.

RULES:
- EXACTLY 3 bullet points
- Max 30 words per bullet
- Use actual numbers from tool results

Write directly (no headers)."""
        
        insights, ins_time = self.call_claude(
            [{"role": "user", "content": insights_prompt}],
            max_tokens=450,
            temperature=temp
        )
        timings['insights'] = ins_time
        
        # Stage 3: Recommendations
        if status_callback:
            status_callback("synthesis_stage", {"stage": 3, "task": "Recommendations"})
        
        recommendations_prompt = f"""{context}

PREVIOUS:
{situation}
{insights}

Write EXACTLY 2 actionable recommendations.

RULES:
- EXACTLY 2 numbered items
- ONE sentence each, max 35 words

Write directly (no headers)."""
        
        recommendations, rec_time = self.call_claude(
            [{"role": "user", "content": recommendations_prompt}],
            max_tokens=300,
            temperature=temp
        )
        timings['recommendations'] = rec_time
        
        timings['synthesis_total'] = time.time() - synthesis_start
        
        if status_callback:
            status_callback("synthesis_complete", None)
        
        # STEP 3: Judge validation
        if enable_validation:
            if status_callback:
                status_callback("validation_start", "Validating...")
            
            try:
                full_response = f"{situation}\n\n{insights}\n\n{recommendations}"
                validation_result = self.validator.validate_response(
                    response_text=full_response,
                    member_profile=profile,
                    tool_results=tool_result,
                    user_query=user_query
                )
                
                timings['validation'] = validation_result.get('duration', 0)
                print(f"⚖️  Validation: {validation_result.get('passed')}")
                
                if status_callback:
                    status_callback("validation_complete", validation_result)
            except Exception as e:
                print(f"⚠️  Validation error: {e}")
        
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

*Response for {self.country} | Session: {self.session_id[:8]}*"""
        
        # De-anonymize
        if anonymize and member_token:
            response = response.replace(member_token, real_name)
            print(f"🔓 Restored: '{member_token}' → '{real_name}'")
        
        # Add metadata
        tool_result['_timings'] = timings
        tool_result['_tools_called'] = tools_called
        
        total_elapsed = time.time() - overall_start
        timings['total'] = total_elapsed
        
        # Log audit
        self._log_query_audit(member_id, user_query, response, total_elapsed, len(tools_called))
        
        print(f"\n✅ Completed in {total_elapsed:.2f}s")
        print(f"{'='*70}\n")
        
        return response, tool_result

