#!/usr/bin/env python3
"""
SuperAdvisor Agent - Multi-country retirement planning with validation
NOW WITH: Refactored ReAct loop, centralized prompts, and MLflow integration
"""

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
    JUDGE_LLM_ENDPOINT, MAX_VALIDATION_ATTEMPTS, SQL_WAREHOUSE_ID, calculate_llm_cost
)
from prompts_registry import get_prompts_registry
from react_loop import ReactAgenticLoop, AgentState
from country_config import get_country_config, get_balance_terminology, get_currency_info

class SuperAdvisorAgent:
    """Multi-country superannuation/retirement advisor agent with validation."""
    
    AUTHORITY_MAP = {
        "AU": {
            "tax": "Australian Taxation Office (ATO)",
            "benefit": "Department of Social Services (DSS)",
            "projection": "ASIC - Australian Securities and Investments Commission"
        },
        "US": {
            "tax": "Internal Revenue Service (IRS)",
            "benefit": "Social Security Administration (SSA)",
            "projection": "U.S. Department of Labor (DOL)"
        },
        "UK": {
            "tax": "Her Majesty's Revenue and Customs (HMRC)",
            "benefit": "UK Pensions Regulator (TPR)",
            "projection": "Financial Conduct Authority (FCA)"
        },
        "IN": {
            "tax": "Income Tax Department",
            "benefit": "Pension Fund Regulatory and Development Authority (PFRDA)",
            "projection": "Employees' Provident Fund Organisation (EPFO)",
            "eps_benefit": "Employees' Provident Fund Organisation (EPFO)"
        }
    }
    
    def __init__(self, tools=None, validator=None, main_llm_endpoint=None, validation_mode="llm_judge", 
                 enable_mlflow_prompts=True):
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
        
        # Set up validator
        if validation_mode == "llm_judge":
            self.validator = LLMJudgeValidator(judge_endpoint=JUDGE_LLM_ENDPOINT)
        elif validation_mode == "deterministic":
            self.validator = DeterministicValidator()
        elif validation_mode == "none":
            self.validator = None
        else:
            self.validator = validator
        
        # Initialize prompts registry and ReAct loop
        self.prompts_registry = get_prompts_registry(enable_mlflow=enable_mlflow_prompts)
        self.react_loop = ReactAgenticLoop(agent_instance=self)
        
        printf(f"SuperAdvisorAgent initialized with main LLM: {self.main_llm_endpoint}")
        printf(f"Synthesis model: {self.model_type}")
        printf(f"Validation mode: {validation_mode}")
        printf(f"Prompts registry: {'MLflow enabled' if enable_mlflow_prompts else 'MLflow disabled'}")
    
    # ========== UTILITY METHODS ==========
 
    def get_authority(self, country, tool_type):
        """Get authority for a country and tool type."""
        return self.AUTHORITY_MAP.get(country, {}).get(tool_type, "Unknown Authority")
    
    def safe_float(self, value, default=0.0):
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.replace(",", "").strip()
            if not value or str(value).lower() == "none":
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def anonymize_member_name(self, name):
        """Anonymize member name for privacy."""
        if not name or name == "Unknown Member":
            return "Member_unknown"
        import hashlib
        name_hash = hashlib.md5(name.encode()).hexdigest()[:6]
        return f"Member_{name_hash}"
    
    def restore_member_name(self, text, anonymized_name, real_name):
        """Restore real name in response text."""
        if anonymized_name and real_name and anonymized_name in text:
            text = text.replace(anonymized_name, real_name)
        return text
    
    def add_personalized_greeting(self, text, member_name):
        """Add personalized greeting to response."""
        if not member_name or member_name == "Unknown Member":
            return text
        if not text.strip().startswith(("Hi", "Hello", "Dear")):
            greeting = f"Hi {member_name},\n\n{text}"
            text = greeting
        return text
    
    def get_country_from_context(self, context):
        """Extract country from context."""
        country_match = re.search(r"Country: ([A-Z]{2})", context)
        if country_match:
            return country_match.group(1)
        return "AU"
    
    def build_base_context(self, member_profile, anonymize=True):
        """Build base context from member profile."""
        real_name = member_profile.get("name", "Unknown Member")
        
        if anonymize:
            display_name = self.anonymize_member_name(real_name)
            printf(f"🔒 Privacy Mode: Anonymised '{real_name}' → '{display_name}'")
        else:
            display_name = real_name
        
        country = member_profile.get("country", "AU")
        age = member_profile.get("age", "Unknown")
        balance_raw = member_profile.get("super_balance", 0)
        balance = self.safe_float(balance_raw)
        employment = member_profile.get("employment_status", "Unknown")
        
        context = f"""Member Profile:
- Name: {display_name}
- Age: {age}
- Country: {country}
- Employment: {employment}
- Retirement Corpus: {balance:,.2f} {self.get_currency(country)}
"""
        
        if country == "AU":
            pres_age = member_profile.get("preservation_age", "Unknown")
            context += f"- Preservation Age: {pres_age}\n"
        
        context_data = {
            "text": context,
            "real_name": real_name,
            "anonymized_name": display_name if anonymize else None
        }
        
        return context_data
    
    def get_currency(self, country):
        """Get currency code for country."""
        currency_info = get_currency_info(country)
        return currency_info["code"]  # "AUD", "USD", "GBP", "INR"
    
    def get_currency_symbol(self, country):
        """Get currency symbol for country."""
        currency_info = get_currency_info(country)
        return currency_info["symbol"]  # "$", "£", "₹"
    
    def format_tool_results(self, tool_results, country="AU"):
        """Format tool results for context - WITH INDIA BALANCE SPLIT DISPLAY."""
        if not tool_results:
            return ""
        
        result_lines = ["=" * 70]
        result_lines.append("UC FUNCTION RESULTS:")
        result_lines.append("=" * 70)
        
        for tool_name, results in tool_results.items():
            result_lines.append(f"\n{tool_name.upper()} RESULTS:")
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
                
                result_lines.append(f"Tool: {tool_name_display}")
                result_lines.append(f"Authority: {authority}")
                
                if "balance_split" in results:
                    split = results["balance_split"]
                    result_lines.append(f"Total Balance: {split['total_balance']:,.2f} INR")
                    result_lines.append(f"EPF Balance: {split['epf_balance']:,.2f} INR (75%)")
                    result_lines.append(f"NPS Balance: {split['nps_balance']:,.2f} INR (25%)")
                
                if "calculation_note" in results:
                    result_lines.append(f"Note: {results['calculation_note']}")
                
                result_lines.append(f"Calculation: {str(calculation)[:300]}")
            else:
                result_lines.append(f"Result: {str(results)[:200]}")
        
        result_lines.append("=" * 70)
        return "\n".join(result_lines)
    
    def generate_response(self, user_query, context, tool_results, validation_history=None):
        """Generate AI response using ChatMessage objects - NOW TRACKS TOKENS."""
        country = self.get_country_from_context(context)
        
        # Get country-specific configuration
        config = get_country_config(country)
        balance_term = get_balance_terminology(country)
        
        # Update context terminology based on country (dynamic from config)
        if "superbalance" in context:
            context = context.replace("superbalance", balance_term)
            context += f"\nNote: {balance_term} refers to the member's {config.retirement_account_term} balance."
        
        # Get system prompt from registry (already includes country-specific instructions)
        system_prompt_base = self.prompts_registry.get_system_prompt(country)
        
        # Build complete system prompt with context and query
        system_prompt = f"""{system_prompt_base}

MEMBER CONTEXT:
{context}

USER QUESTION:
{user_query}
"""
        
        tool_context = self.format_tool_results(tool_results, country)
        full_context = f"{context}\n\n{tool_context}"
        
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
            
            input_tokens = 0
            output_tokens = 0
            
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'prompt_tokens', 0)
                output_tokens = getattr(response.usage, 'completion_tokens', 0)
                printf(f"📊 Synthesis tokens: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} total")
            else:
                input_tokens = len(system_prompt + full_context) // 4
                output_tokens = 150
                printf(f"⚠️ Token usage not available, estimated: {input_tokens} input + {output_tokens} output")
            
            synthesis_cost = calculate_llm_cost(input_tokens, output_tokens, self.model_type)
            printf(f"💰 Synthesis cost: ${synthesis_cost:.6f} ({self.model_type})")
            
            if hasattr(response, 'choices') and response.choices:
                response_text = response.choices[0].message.content
            else:
                response_text = str(response)
            
            printf(f"✅ LLM response: {len(response_text)} chars in {elapsed:.2f}s")
            
            return {
                "text": response_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": synthesis_cost,
                "duration": elapsed
            }
        
        except Exception as e:
            printf(f"❌ Error generating response: {e}")
            traceback.print_exc()
            return {
                "text": "I apologize, but I encountered an error generating your response. Please try again.",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
                "duration": 0.0
            }
    
    # ========== NEW CITATION METHODS (FROM agent-2.py) ==========
    
    def get_citations_for_tools(self, country, tools_used):
        """Fetch citations from database."""
        try:
            country_upper = country.upper() if country else "AU"
            if not tools_used:
                return []
            
            printf(f"📚 Fetching citations for {country_upper}, tools: {tools_used}")
            
            # Build query
            query_parts = []
            query_parts.append("SELECT DISTINCT")
            query_parts.append("  citation_id, country, authority, regulation_name,")
            query_parts.append("  regulation_code, source_url, description")
            query_parts.append("FROM super_advisory_demo.member_data.citation_registry")
            query_parts.append(f"WHERE country = '{country_upper}'")
            
            # Add tool conditions
            tool_conditions = [f"tool_type = '{tool}'" for tool in tools_used]
            where_clause = " OR ".join(tool_conditions)
            query_parts.append(f"  AND ({where_clause})")
            query_parts.append("ORDER BY citation_id")
            
            query = "\n".join(query_parts)
            
            # Execute query
            result = self.w.statement_execution.execute_statement(
                warehouse_id=SQL_WAREHOUSE_ID,
                statement=query,
                wait_timeout="30s"
            )
            
            status_name = result.status.state.name if hasattr(result.status.state, 'name') else str(result.status.state)
            
            if status_name != "SUCCEEDED":
                printf(f"⚠️ Query failed: {status_name}")
                return []
            
            # Parse results
            citations = []
            if result.result and hasattr(result.result, 'data_array') and result.result.data_array:
                rows = result.result.data_array
                printf(f"✅ Found {len(rows)} citations")
                
                for row in rows:
                    try:
                        citations.append({
                            'citation_id': row[0],
                            'country': row[1],
                            'authority': row[2],
                            'regulation_name': row[3],
                            'regulation_code': row[4],
                            'source_url': row[5],
                            'description': row[6]
                        })
                    except Exception as parse_err:
                        printf(f"⚠️ Error parsing row: {parse_err}")
            else:
                printf("⚠️ No citations found")
            
            return citations
            
        except Exception as e:
            printf(f"❌ Citation fetch error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def format_citation(self, citation):
        """Format a single citation entry."""
        parts = [f"{citation['citation_id']} - {citation['authority']}"]
        
        if citation.get('regulation_name'):
            parts.append(f"{citation['regulation_name']}")
        
        if citation.get('regulation_code'):
            parts.append(f"({citation['regulation_code']})")
        
        return " ".join(parts)
    
    def add_citations_and_disclaimer(self, response, country, tools_used):
        """Add citations and disclaimer to response."""
        citations = self.get_citations_for_tools(country, tools_used)
        
        citations_section = "\n\n---\n\n### References & Citations\n\n"
        
        if citations and len(citations) > 0:
            citations_section += "Based on the following regulatory authorities and guidelines:\n\n"
            
            for citation in citations:
                formatted = self.format_citation(citation)
                citations_section += f"- {formatted}\n"
                
                if citation.get('source_url'):
                    citations_section += f"  Source: {citation['source_url']}\n"
        else:
            citations_section += "References: General retirement and pension regulations\n"
        
        citations_section += "\n**Disclaimer:**\n"
        citations_section += "- This advice is generated by an AI system for educational guidance only\n"
        citations_section += "- Does not constitute personal financial advice\n"
        citations_section += "- Please consult a qualified advisor before making financial decisions\n"
        
        return response + citations_section
    
    # ========== MAIN PROCESS_QUERY METHOD (UPDATED WITH CITATIONS) ==========
    
    def get_classifier_metrics(self):
        """
        Get classifier performance metrics.
        
        Returns:
            Dictionary with classification statistics
        """
        return self.react_loop.get_classifier_metrics()
    
    def print_classifier_metrics(self):
        """Print classifier performance metrics in a readable format."""
        self.react_loop.print_classifier_metrics()
    
    def process_query(self, member_id, user_query, withdrawal_amount=None):
        """
        Main query processing pipeline using ReAct agentic loop.
        
        This method now delegates to ReactAgenticLoop for the core logic,
        keeping this interface simple and focused on data preparation.
        """
        printf("="*70)
        printf(f"🚀 SuperAdvisor Processing Query")
        printf("="*70)
        
        # Get member profile
        member_profile = self.tools.get_member_profile(member_id)
        if not member_profile or "error" in member_profile:
            return {"error": f"Member {member_id} not found"}
        
        country = member_profile.get("country", "AU")
        real_name = member_profile.get("name", "Unknown Member")
        
        printf(f"🌍 Member: {member_id} | Country: {country}")
        
        # Build context with anonymization
        context_data = self.build_base_context(member_profile, anonymize=True)
        context = context_data["text"]
        anonymized_name = context_data["anonymized_name"]
        printf(f"✅ Base context created: {len(context)} chars")
        
        # Initialize agent state
        state = AgentState(
            member_id=member_id,
            user_query=user_query,
            country=country,
            member_profile=member_profile,
            withdrawal_amount=withdrawal_amount,
            context=context,
            real_name=real_name,
            anonymized_name=anonymized_name
        )
        
        # Run the ReAct agentic loop
        printf("\n🤖 Starting ReAct Agentic Loop...")
        printf("="*70)
        result = self.react_loop.run_agentic_loop(state)
        
        printf("\n" + "="*70)
        printf(f"✅ Query Processing Complete - Attempts: {result.get('attempts', 0)}")
        printf("="*70)
        
        return result


def printf(msg):
    """Print with timestamp."""
    print(f"{msg}")
