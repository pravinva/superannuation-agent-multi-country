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
from utils.formatting import get_currency, get_currency_symbol, safe_float
from country_config import get_authority, get_country_config, get_balance_terminology
from prompts_registry import get_prompts_registry
from react_loop import ReactAgenticLoop, AgentState
from agents.context_formatter import get_context_formatter
from agents.response_builder import get_response_builder
from shared.logging_config import get_logger

logger = get_logger(__name__)

class SuperAdvisorAgent:
    """Multi-country superannuation/retirement advisor agent with validation."""
    
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

        # Initialize context formatter and response builder
        self.context_formatter = get_context_formatter()
        self.response_builder = get_response_builder(
            workspace_client=self.w,
            llm_endpoint=self.main_llm_endpoint,
            model_type=self.model_type
        )

        logger.info(f"SuperAdvisorAgent initialized with main LLM: {self.main_llm_endpoint}")
        logger.info(f"Synthesis model: {self.model_type}")
        logger.info(f"Validation mode: {validation_mode}")
        logger.info(f"Prompts registry: {'MLflow enabled' if enable_mlflow_prompts else 'MLflow disabled'}")
    
    # ========== UTILITY METHODS ==========
 
    def get_authority(self, country, tool_type):
        """Get authority for a country and tool type."""
        return get_authority(country, tool_type)
    
    def anonymize_member_name(self, name):
        """Anonymize member name for privacy (delegates to ContextFormatter)."""
        return self.context_formatter.anonymize_member_name(name)

    def restore_member_name(self, text, anonymized_name, real_name):
        """Restore real name in response text (delegates to ContextFormatter)."""
        return self.context_formatter.restore_member_name(text, anonymized_name, real_name)

    def add_personalized_greeting(self, text, member_name):
        """Add personalized greeting to response (delegates to ContextFormatter)."""
        return self.context_formatter.add_personalized_greeting(text, member_name)

    def get_country_from_context(self, context):
        """Extract country from context (delegates to ContextFormatter)."""
        return self.context_formatter.get_country_from_context(context)
    
    def build_base_context(self, member_profile, anonymize=True):
        """Build base context from member profile (delegates to ContextFormatter)."""
        return self.context_formatter.build_base_context(member_profile, anonymize)
    
    def format_tool_results(self, tool_results, country="AU"):
        """Format tool results for context (delegates to ContextFormatter)."""
        return self.context_formatter.format_tool_results(tool_results, country)
    
    def generate_response(self, user_query, context, tool_results, validation_history=None):
        """Generate AI response (delegates to ResponseBuilder)."""
        country = self.get_country_from_context(context)

        # Use response builder to generate response
        result = self.response_builder.generate_response(
            user_query=user_query,
            context=context,
            tool_results=tool_results,
            country=country,
            validation_history=validation_history
        )

        # Convert ResponseResult dataclass to dictionary for backwards compatibility
        return {
            "text": result.text,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cost": result.cost,
            "duration": result.duration
        }
    
    # ========== NEW CITATION METHODS (FROM agent-2.py) ==========
    
    def get_citations_for_tools(self, country, tools_used):
        """Fetch citations from database."""
        try:
            country_upper = country.upper() if country else "AU"
            if not tools_used:
                return []
            
            logger.info(f"📚 Fetching citations for {country_upper}, tools: {tools_used}")
            
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
                logger.warning(f"⚠️ Query failed: {status_name}")
                return []
            
            # Parse results
            citations = []
            if result.result and hasattr(result.result, 'data_array') and result.result.data_array:
                rows = result.result.data_array
                logger.info(f"✅ Found {len(rows)} citations")
                
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
                        logger.warning(f"⚠️ Error parsing row: {parse_err}")
            else:
                logger.warning("⚠️ No citations found")
            
            return citations
            
        except Exception as e:
            logger.error(f"❌ Citation fetch error: {e}", exc_info=True)
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
        logger.info("="*70)
        logger.info(f"🚀 SuperAdvisor Processing Query")
        logger.info("="*70)
        
        # Get member profile
        member_profile = self.tools.get_member_profile(member_id)
        if not member_profile or "error" in member_profile:
            return {"error": f"Member {member_id} not found"}
        
        country = member_profile.get("country", "AU")
        real_name = member_profile.get("name", "Unknown Member")
        
        logger.info(f"🌍 Member: {member_id} | Country: {country}")
        
        # Build context with anonymization
        context_data = self.build_base_context(member_profile, anonymize=True)
        context = context_data["text"]
        anonymized_name = context_data["anonymized_name"]
        logger.info(f"✅ Base context created: {len(context)} chars")
        
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
        logger.info("\n🤖 Starting ReAct Agentic Loop...")
        logger.info("="*70)
        result = self.react_loop.run_agentic_loop(state)

        logger.info("\n" + "="*70)
        logger.info(f"✅ Query Processing Complete - Attempts: {result.get('attempts', 0)}")
        logger.info("="*70)
        
        return result
