#!/usr/bin/env python3

# agent.py - COMPLETE WITH AI_CLASSIFY TOPIC FILTERING + INDIA EPF/NPS SPLIT

# ✅ Type conversion fix for super_balance
# ✅ Working citations with .name attribute check
# ✅ Anonymization + Name Restoration + Personalized Greeting
# ✅ All validation modes working
# ✅ Multi-country support (AU, US, UK, IN)
# ✅ Cleaner LLM prompt (no emoji/special chars)
# ✅ TOKEN TRACKING: Synthesis LLM costs now tracked!
# ✅ NEW: India EPF/NPS balance split transparency
# ✅ NEW: ai_classify topic filtering to block off-topic queries early

import os
import time
import re
import json
import uuid
import traceback

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from databricks.sdk.service.sql import StatementState
from tools import SuperAdvisorTools
from validation import LLMJudgeValidator, DeterministicValidator
from config import (
    MAIN_LLM_ENDPOINT, MAIN_LLM_TEMPERATURE, MAIN_LLM_MAX_TOKENS,
    JUDGE_LLM_ENDPOINT, MAX_VALIDATION_ATTEMPTS, SQL_WAREHOUSE_ID,
    calculate_llm_cost
)

class SuperAdvisorAgent:
    """Multi-country superannuation/retirement advisor agent with validation"""
    
    AUTHORITY_MAP = {
        'AU': {
            'tax': 'Australian Taxation Office (ATO)',
            'benefit': 'Department of Social Services (DSS)',
            'projection': 'ASIC - Australian Securities and Investments Commission'
        },
        'US': {
            'tax': 'Internal Revenue Service (IRS)',
            'benefit': 'Social Security Administration (SSA)',
            'projection': 'U.S. Department of Labor (DOL)'
        },
        'UK': {
            'tax': "Her Majesty's Revenue and Customs (HMRC)",
            'benefit': 'UK Pensions Regulator (TPR)',
            'projection': 'Financial Conduct Authority (FCA)'
        },
        'IN': {
            'tax': 'Income Tax Department',
            'benefit': 'Pension Fund Regulatory and Development Authority (PFRDA)',
            'projection': 'Employees Provident Fund Organisation (EPFO)',
            'eps_benefit': 'Employees Provident Fund Organisation (EPFO)'
        }
    }
    
    def __init__(self, tools=None, validator=None, main_llm_endpoint=None, validation_mode='llm_judge'):
        self.w = WorkspaceClient()
        self.tools = tools or SuperAdvisorTools()
        self.main_llm_endpoint = main_llm_endpoint or MAIN_LLM_ENDPOINT
        self.validation_mode = validation_mode
        
        # Determine model type for cost calculation
        if "opus" in self.main_llm_endpoint.lower():
            self.model_type = "claude-opus-4-1"
        elif "sonnet" in self.main_llm_endpoint.lower():
            self.model_type = "claude-sonnet-4"
        elif "haiku" in self.main_llm_endpoint.lower():
            self.model_type = "claude-haiku-4"
        else:
            self.model_type = "claude-sonnet-4"
        
        if validation_mode == 'llm_judge':
            self.validator = LLMJudgeValidator(judge_endpoint=JUDGE_LLM_ENDPOINT)
        elif validation_mode == 'deterministic':
            self.validator = DeterministicValidator()
        elif validation_mode == 'none':
            self.validator = None
        else:
            self.validator = validator
        
        print(f"✓ SuperAdvisorAgent initialized with main LLM: {self.main_llm_endpoint}")
        print(f"✓ Synthesis model: {self.model_type}")
        print(f"✓ Validation mode: {validation_mode}")
    
    def classify_query_topic(self, user_query):
        """Use Databricks ai_classify to determine if query is retirement-related"""
        try:
            # Escape single quotes in query
            escaped_query = user_query.replace("'", "''")
            
            # Use ai_classify SQL function
            query = f"""
            SELECT ai_classify(
                '{escaped_query}',
                ARRAY(
                    'retirement_planning',
                    'superannuation_withdrawal', 
                    'pension_benefits',
                    'tax_questions',
                    'contribution_rules',
                    'off_topic'
                )
            ) AS topic_classification
            """
            
            statement = self.w.statement_execution.execute_statement(
                warehouse_id=SQL_WAREHOUSE_ID,
                statement=query,
                wait_timeout="10s"
            )
            
            # Wait for result
            while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
                time.sleep(0.2)
                statement = self.w.statement_execution.get_statement(statement.statement_id)
            
            if statement.status.state == StatementState.SUCCEEDED and statement.result and statement.result.data_array:
                classification = statement.result.data_array[0][0]
                
                is_on_topic = classification != 'off_topic'
                
                print(f"🏷️  Query classified as: '{classification}'")
                
                return {
                    'is_on_topic': is_on_topic,
                    'classification': classification,
                    'confidence': 1.0  # ai_classify is deterministic
                }
            else:
                print(f"⚠️ ai_classify returned no results, defaulting to on-topic")
                return {
                    'is_on_topic': True,  # Default to allowing query
                    'classification': 'unknown',
                    'confidence': 0.5
                }
                
        except Exception as e:
            print(f"❌ Error in ai_classify: {e}")
            # Fail open - allow query to proceed
            return {
                'is_on_topic': True,
                'classification': 'error',
                'confidence': 0.0
            }
    
    def get_authority(self, country, tool_type):
        """Get authority for a country and tool type"""
        return self.AUTHORITY_MAP.get(country, {}).get(tool_type, 'Unknown Authority')
    
    def safe_float(self, value, default=0.0):
        """Safely convert value to float"""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
                if not value or value.lower() == 'none':
                    return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def anonymize_member_name(self, name):
        """Anonymize member name for privacy"""
        if not name or name == "Unknown Member":
            return "Member_unknown"
        
        import hashlib
        name_hash = hashlib.md5(name.encode()).hexdigest()[:6]
        return f"Member_{name_hash}"
    
    def restore_member_name(self, text, anonymized_name, real_name):
        """Restore real name in response text"""
        if anonymized_name and real_name and anonymized_name in text:
            text = text.replace(anonymized_name, real_name)
        return text
    
    def add_personalized_greeting(self, text, member_name):
        """Add personalized greeting to response"""
        if not member_name or member_name == "Unknown Member":
            return text
        
        if not text.strip().startswith(("Hi", "Hello", "Dear")):
            greeting = f"Hi {member_name},\n\n"
            text = greeting + text
        
        return text
    
    def get_country_from_context(self, context):
        """Extract country from context"""
        country_match = re.search(r'Country:\s*([A-Z]{2})', context)
        if country_match:
            return country_match.group(1)
        return "AU"
    
    def build_base_context(self, member_profile, anonymize=True):
        """Build base context from member profile"""
        real_name = member_profile.get('name', 'Unknown Member')
        
        if anonymize:
            display_name = self.anonymize_member_name(real_name)
            print(f"🔒 Privacy Mode: Anonymised '{real_name}' → '{display_name}'")
        else:
            display_name = real_name
        
        country = member_profile.get('country', 'AU')
        age = member_profile.get('age', 'Unknown')
        balance_raw = member_profile.get('super_balance', 0)
        balance = self.safe_float(balance_raw)
        
        employment = member_profile.get('employment_status', 'Unknown')
        
        context = f"""Member Profile:
- Name: {display_name}
- Age: {age}
- Country: {country}
- Employment: {employment}
- Retirement Corpus: {balance:,.2f} {self.get_currency(country)}
"""
        
        if country == 'AU':
            pres_age = member_profile.get('preservation_age', 'Unknown')
            context += f"- Preservation Age: {pres_age}\n"
        
        context_data = {
            'text': context,
            'real_name': real_name,
            'anonymized_name': display_name if anonymize else None
        }
        
        return context_data
    
    def get_currency(self, country):
        """Get currency symbol for country"""
        currency_map = {
            'AU': 'AUD',
            'US': 'USD',
            'UK': 'GBP',
            'IN': 'INR'
        }
        return currency_map.get(country, 'AUD')
    
    def select_tools(self, user_query, country):
        """Select appropriate tools based on query"""
        query_lower = user_query.lower()
        tools = []
        
        # Tax-related queries
        if any(word in query_lower for word in ['tax', 'taxed', 'taxation', 'penalty', 'penalties']):
            tools.append('tax')
        
        # Benefit-related queries (country-specific)
        if country == 'IN':
            if any(word in query_lower for word in ['eps', 'pension scheme', 'monthly pension']):
                tools.append('eps_benefit')
            elif any(word in query_lower for word in ['nps', 'annuity', 'national pension']):
                tools.append('benefit')
            elif any(word in query_lower for word in ['benefit', 'pension', 'retirement income']):
                tools.append('eps_benefit')
        else:
            if any(word in query_lower for word in ['pension', 'benefit', 'social security', 'centrelink', 'state pension']):
                tools.append('benefit')
        
        # Projection-related queries
        if any(word in query_lower for word in ['project', 'forecast', 'grow', 'future', 'years', 'balance in']):
            tools.append('projection')
        
        # Default to tax if no specific tools identified
        if not tools:
            tools = ['tax', 'benefit']
        
        return list(set(tools))
    
    def format_tool_results(self, tool_results, country="AU"):
        """Format tool results for context - WITH INDIA BALANCE SPLIT DISPLAY"""
        if not tool_results:
            return ""
        
        result_lines = ["=" * 70]
        result_lines.append("UC FUNCTION RESULTS")
        result_lines.append("=" * 70)
        
        for tool_name, results in tool_results.items():
            result_lines.append(f"\n{tool_name.upper()} RESULTS")
            result_lines.append("-" * 40)
            
            if isinstance(results, dict):
                if "error" in results:
                    result_lines.append(f"❌ Error: {results['error']}")
                    continue
                
                tool_name_display = results.get("tool_name", f"Unknown {tool_name} Tool")
                authority = results.get("authority", "")
                calculation = results.get("calculation", "")
                
                if not authority:
                    authority = self.get_authority(country, tool_name)
                
                result_lines.append(f"✓ Tool: {tool_name_display}")
                result_lines.append(f"  Authority: {authority}")
                
                # 🆕 NEW: Display balance split for India tools
                if "balance_split" in results:
                    split = results["balance_split"]
                    result_lines.append(f"  Total Balance: {split['total_balance']:,.2f} INR")
                    result_lines.append(f"  ├─ EPF Balance: {split['epf_balance']:,.2f} INR (75%)")
                    result_lines.append(f"  └─ NPS Balance: {split['nps_balance']:,.2f} INR (25%)")
                
                # 🆕 NEW: Display calculation note if present
                if "calculation_note" in results:
                    result_lines.append(f"  Note: {results['calculation_note']}")
                
                result_lines.append(f"  Calculation: {str(calculation)[:300]}")
            else:
                result_lines.append(f"Result: {str(results)[:200]}")
        
        result_lines.append("=" * 70)
        return "\n".join(result_lines)
    
    def generate_response(self, user_query, context, tool_results, validation_history=None):
        """Generate AI response using ChatMessage objects - NOW TRACKS TOKENS"""
        
        country = self.get_country_from_context(context)
        
        # Normalize terminology
        if "super_balance" in context and country == "UK":
            context = context.replace("super_balance", "pension_balance")
            context += "\n(Note: 'pension_balance' refers to the member's UK pension pot, not Australian superannuation.)"
        elif "super_balance" in context and country == "US":
            context = context.replace("super_balance", "retirement_balance")
            context += "\n(Note: 'retirement_balance' refers to 401(k)/IRA-style personal savings.)"
        elif "super_balance" in context and country == "IN":
            context = context.replace("super_balance", "retirement_corpus")
            context += "\n(Note: 'retirement_corpus' refers to combined EPF+NPS under Indian pension rules.)"
        
        # 🆕 NEW: Add India-specific balance split instructions
        india_balance_note = ""
        if country == "IN":
            india_balance_note = """

⚠️ CRITICAL FOR INDIA MEMBERS:
- The member's retirement corpus is split into TWO schemes:
  * EPF (Employees' Provident Fund): 75% of total - mandatory provident fund
  * NPS (National Pension System): 25% of total - voluntary pension scheme
- When discussing EPF, ONLY reference the EPF balance (75%), NOT the total
- When discussing NPS, ONLY reference the NPS balance (25%), NOT the total
- The tool results show the exact balances used for each calculation
- ALWAYS use the balance amounts shown in the tool calculation notes
"""
        
        system_prompt = f"""You are SuperAdvisor, an expert retirement and superannuation advisor for {country}.

INSTRUCTIONS:
1. Answer the user's question directly and clearly
2. Use specific numbers from the member profile AND tool results
3. Use simple language - no emoji or special characters
4. Format with clear sections separated by blank lines
5. Keep recommendations practical and easy to understand
{india_balance_note}

MEMBER CONTEXT:
{context}

USER QUESTION:
{user_query}

RESPONSE FORMAT:
Start with a direct answer to their question.
Then explain key considerations.
End with a clear recommendation.

Use this structure for your response:

- Direct Answer: (answer their specific question)
- Key Considerations: (list 2-3 important points)
- Recommendation: (actionable advice)

IMPORTANT RULES:
- Do NOT use emoji (no emojis)
- Do NOT use special characters or symbols
- Do NOT use asterisks for emphasis
- DO separate numbers and words with spaces
- DO use simple, clear English
- DO keep sentences short
- For India members: ONLY use EPF/NPS balances from tool results, NOT total balance
- If the user asked "How much can I withdraw?" WITHOUT specifying an amount:
  Answer generally about withdrawal rules, not specific dollar calculations
- Only calculate specific amounts if user gave a specific amount
- Don't make up withdrawal amounts the user didn't ask about

Example format:

Answer: You can withdraw up to 100,000 AUD.

Key Considerations:
- Your balance needs to last your retirement
- You have dependents to consider
- Your other assets provide financial buffer

Recommendation: Consider withdrawing only what you need now.
"""
        
        # Format tool results
        tool_context = self.format_tool_results(tool_results, country)
        
        full_context = f"""{context}

{tool_context}
"""
        
        messages = [
            ChatMessage(role=ChatMessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=ChatMessageRole.USER, content=full_context)
        ]
        
        try:
            start_time = time.time()
            response = self.w.serving_endpoints.query(
                name=self.main_llm_endpoint,
                messages=messages,
                max_tokens=MAIN_LLM_MAX_TOKENS,
                temperature=MAIN_LLM_TEMPERATURE
            )
            elapsed = time.time() - start_time
            
            # 🆕 EXTRACT TOKEN USAGE
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'prompt_tokens', 0)
                output_tokens = getattr(response.usage, 'completion_tokens', 0)
                print(f"📊 Synthesis tokens: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} total")
            else:
                input_tokens = len(system_prompt + full_context) // 4
                output_tokens = 150
                print(f"⚠️ Token usage not available, estimated: {input_tokens} input + {output_tokens} output")
            
            # 🆕 CALCULATE COST
            synthesis_cost = calculate_llm_cost(input_tokens, output_tokens, self.model_type)
            print(f"💰 Synthesis cost: ${synthesis_cost:.6f} ({self.model_type})")
            
            if hasattr(response, 'choices') and response.choices:
                response_text = response.choices[0].message.content
            else:
                response_text = str(response)
            
            print(f"✅ LLM response: {len(response_text)} chars in {elapsed:.2f}s")
            
            return {
                'text': response_text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost': synthesis_cost,
                'duration': elapsed
            }
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            traceback.print_exc()
            return {
                'text': "I apologize, but I encountered an error generating your response. Please try again.",
                'input_tokens': 0,
                'output_tokens': 0,
                'cost': 0.0,
                'duration': 0.0
            }
    
    def process_query(self, member_id, user_query, withdrawal_amount=None):
        """Main query processing pipeline with ai_classify topic filtering"""
        
        # Get member profile
        member_profile = self.tools.get_member_profile(member_id)
        if not member_profile or "error" in member_profile:
            return {"error": f"Member {member_id} not found"}
        
        country = member_profile.get('country', 'AU')
        real_name = member_profile.get('name', 'Unknown Member')
        
        # 🆕 NEW: Use ai_classify to check if query is retirement-related
        print(f"\n🔍 Classifying query topic with ai_classify...")
        classification_result = self.classify_query_topic(user_query)
        
        if not classification_result['is_on_topic']:
            print(f"⚠️ OFF-TOPIC QUERY DETECTED: '{classification_result['classification']}'")
            print(f"   Ending conversation politely without tool/LLM calls")
            print(f"   💰 Cost saved: ~$0.08 (no tools, no synthesis, no validation)")
            
            # Return polite decline immediately - NO tool calls, NO LLM calls
            decline_message = f"""Hi {real_name},

Thank you for reaching out! I noticed your question appears to be outside my expertise as it is {classification_result['classification'].replace('_', ' ')}.

I'm a Superannuation Advisor, and I specialize exclusively in retirement and superannuation planning. I can help you with:

• Retirement savings (EPF, NPS, Superannuation, 401(k), Pensions)
• Withdrawal rules and eligibility
• Tax implications on retirement withdrawals
• Retirement benefit calculations
• Long-term retirement projections

Is there anything about your retirement planning I can help you with today?"""
            
            return {
                'response': decline_message,
                'validation': {
                    'passed': True,
                    'confidence': 1.0,
                    'violations': [],
                    'reasoning': f"Off-topic query ('{classification_result['classification']}') correctly declined with ai_classify filter",
                    '_validator_used': 'ai_classify_filter'
                },
                'tools_used': [],
                'attempts': 0,
                'synthesis_results': [],
                'validation_results': [],
                'off_topic': True,
                'classification': classification_result
            }
        
        # Query is on-topic - continue with normal processing
        print(f"✅ Query is ON-TOPIC: '{classification_result['classification']}'")
        print(f"\n{'='*70}")
        print(f"🌍 Processing query for {country} member: {member_id}")
        print(f"{'='*70}")
        
        # Build context with anonymization
        context_data = self.build_base_context(member_profile, anonymize=True)
        context = context_data['text']
        anonymized_name = context_data['anonymized_name']
        
        print(f"✅ Base context created: {len(context)} chars")
        
        # Select and execute tools
        selected_tools = self.select_tools(user_query, country)
        print(f"🧠 Tools selected: {selected_tools}")
        
        tool_results = {}
        for tool_name in selected_tools:
            try:
                result = self.tools.call_tool(tool_name, member_id, withdrawal_amount or 0, country)
                tool_results[tool_name] = result
            except Exception as e:
                print(f"❌ Tool {tool_name} failed: {e}")
                tool_results[tool_name] = {"error": str(e)}
        
        # Validation loop
        validation_history = []
        synthesis_attempts = []
        
        for attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):
            print(f"\n🔄 Attempt {attempt}/{MAX_VALIDATION_ATTEMPTS}")
            
            # Generate response
            response_data = self.generate_response(user_query, context, tool_results, validation_history)
            response_text = response_data['text']
            
            synthesis_attempts.append({
                'attempt': attempt,
                'input_tokens': response_data['input_tokens'],
                'output_tokens': response_data['output_tokens'],
                'cost': response_data['cost'],
                'duration': response_data['duration'],
                'model': self.model_type
            })
            
            # Validate if validator exists
            if self.validator:
                validation_result = self.validator.validate(
                    response_text,
                    user_query,
                    context,
                    member_profile=member_profile,
                    tool_output=tool_results
                )
                
                validation_history.append(validation_result)
                
                if validation_result.get('passed', True):
                    print(f"✅ PASSED! Using this response.")
                    
                    # Restore real name
                    if anonymized_name and real_name:
                        response_text = self.restore_member_name(response_text, anonymized_name, real_name)
                        print(f"🔓 Restored anonymised '{anonymized_name}' → '{real_name}'")
                    
                    # Add personalized greeting
                    response_text = self.add_personalized_greeting(response_text, real_name)
                    print(f"✅ Added personalized greeting for {real_name}")
                    
                    return {
                        'response': response_text,
                        'validation': validation_result,
                        'tools_used': list(tool_results.keys()),
                        'attempts': attempt,
                        'synthesis_results': synthesis_attempts,
                        'validation_results': validation_history,
                        'classification': classification_result
                    }
                else:
                    print(f"⚠️ FAILED (attempt {attempt}/{MAX_VALIDATION_ATTEMPTS})")
                    if attempt < MAX_VALIDATION_ATTEMPTS:
                        continue
            else:
                # No validation - use first response
                if anonymized_name and real_name:
                    response_text = self.restore_member_name(response_text, anonymized_name, real_name)
                
                response_text = self.add_personalized_greeting(response_text, real_name)
                
                return {
                    'response': response_text,
                    'validation': {'passed': True, 'confidence': 1.0, 'violations': []},
                    'tools_used': list(tool_results.keys()),
                    'attempts': 1,
                    'synthesis_attempts': synthesis_attempts,
                    'validation_history': [],
                    'classification': classification_result
                }
        
        # Max attempts reached - return best response
        print(f"⚠️ Max attempts reached. Using last response.")
        if anonymized_name and real_name:
            response_text = self.restore_member_name(response_text, anonymized_name, real_name)
        
        response_text = self.add_personalized_greeting(response_text, real_name)
        
        return {
            'response': response_text,
            'validation': validation_history[-1] if validation_history else {'passed': False, 'confidence': 0.0},
            'tools_used': list(tool_results.keys()),
            'attempts': MAX_VALIDATION_ATTEMPTS,
            'synthesis_results': synthesis_attempts,
            'validation_results': validation_history,
            'classification': classification_result
        }

