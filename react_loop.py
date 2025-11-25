#!/usr/bin/env python3
"""
ReAct Agentic Loop - Separated from main agent
Implements the Reasoning + Acting pattern for multi-step query processing
"""

import time
import traceback
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from config import SQL_WAREHOUSE_ID, MAX_VALIDATION_ATTEMPTS, CLASSIFIER_LLM_ENDPOINT
from prompts_registry import get_prompts_registry
from country_config import get_country_config
from classifier import EmbeddingCascadeClassifier


@dataclass
class AgentState:
    """State management for the agentic loop."""
    member_id: str
    user_query: str
    country: str
    member_profile: Dict
    withdrawal_amount: Optional[float] = None
    
    # Context and names
    context: str = ""
    real_name: str = "Unknown Member"
    anonymized_name: Optional[str] = None
    
    # Classification results
    classification: Dict = field(default_factory=dict)
    is_on_topic: bool = True
    
    # Tool execution
    selected_tools: List[str] = field(default_factory=list)
    tool_results: Dict = field(default_factory=dict)
    
    # Response generation
    synthesis_attempts: List[Dict] = field(default_factory=list)
    validation_history: List[Dict] = field(default_factory=list)
    
    # Final response
    final_response: str = ""
    citations: List[Dict] = field(default_factory=list)
    
    # Metrics
    attempts: int = 0
    validation_passed: bool = False


class ReactAgenticLoop:
    """
    ReAct (Reasoning + Acting) pattern implementation for retirement advisory.
    
    This class implements the core agentic loop:
    1. Reason: Classify query, select tools, analyze context
    2. Act: Execute tools, generate responses, validate
    3. Observe: Check validation, iterate if needed
    """
    
    def __init__(self, agent_instance):
        """
        Initialize ReAct loop with reference to parent agent.
        
        Args:
            agent_instance: Reference to SuperAdvisorAgent instance
        """
        self.agent = agent_instance
        self.w = WorkspaceClient()
        self.prompts_registry = get_prompts_registry()
        
        # Initialize new embedding-based cascade classifier
        # Uses OSS GPT 120B for Stage 3 LLM fallback (cost optimized!)
        self.classifier = EmbeddingCascadeClassifier(
            prompts_registry=self.prompts_registry,
            enable_cache=True,
            llm_endpoint=CLASSIFIER_LLM_ENDPOINT  # databricks-gpt-oss-120b
        )
        
        self.printf = printf
    
    def classify_query_topic(self, user_query: str) -> Dict:
        """
        Intelligent 3-stage cascade classification:
        Stage 1: Regex patterns (80% of queries, <1ms, $0)
        Stage 2: Embedding similarity (15% of queries, ~100ms, ~$0.0001)
        Stage 3: LLM fallback (5% of queries, ~300ms, ~$0.001)
        
        Args:
            user_query: User's query to classify
            
        Returns:
            Classification result dictionary with:
            - is_on_topic: bool
            - confidence: float (0-1)
            - classification: str
            - method: str (which stage was used)
            - latency_ms: float
            - cost_usd: float
        """
        try:
            result = self.classifier.classify(user_query)
            
            # Log classification details
            method = result.get('method', 'unknown')
            confidence = result.get('confidence', 0.0)
            latency = result.get('latency_ms', 0.0)
            cost = result.get('cost_usd', 0.0)
            cached = result.get('cached', False)
            
            if cached:
                self.printf(f"💾 Classification cached: {result['classification']} (confidence: {confidence:.2f})")
            else:
                self.printf(f"🏷️  Query classified via {method}: '{result['classification']}'")
                self.printf(f"   Confidence: {confidence:.2f} | Latency: {latency:.1f}ms | Cost: ${cost:.6f}")
            
            return result
            
        except Exception as e:
            self.printf(f"❌ Error in classification: {e}")
            # Default to on-topic to avoid false rejections
            return {
                "is_on_topic": True,
                "classification": "error",
                "confidence": 0.0,
                "method": "error_fallback",
                "error": str(e)
            }
    
    def handle_off_topic_query(self, state: AgentState) -> Dict:
        """
        Handle off-topic queries with polite decline message.
        
        Args:
            state: Current agent state
            
        Returns:
            Response dictionary
        """
        self.printf(f"❌ OFF-TOPIC QUERY DETECTED: {state.classification['classification']}")
        self.printf("✅ Ending conversation politely without tool/LLM calls")
        self.printf("💰 Cost saved: $0.08+ (no tools, no synthesis, no validation)")
        
        decline_message = self.prompts_registry.get_off_topic_decline_message(
            real_name=state.real_name,
            classification=state.classification['classification']
        )
        
        return {
            "response": decline_message,
            "validation": {
                "passed": True, 
                "confidence": 1.0, 
                "violations": [],
                "reasoning": f"Off-topic query ({state.classification['classification']}) correctly declined with ai_classify filter",
                "validator_used": "ai_classify_filter"
            },
            "tools_used": [],
            "attempts": 0,
            "synthesis_results": [],
            "validation_results": [],
            "off_topic": True,
            "classification": state.classification
        }
    
    def reason_and_select_tools(self, state: AgentState) -> List[str]:
        """
        Reasoning phase: Select appropriate tools based on query analysis.
        Uses country-specific configuration for tool selection.
        
        Args:
            state: Current agent state
            
        Returns:
            List of selected tool names
        """
        query_lower = state.user_query.lower()
        config = get_country_config(state.country)
        tools = []
        
        # Tax-related queries
        if any(word in query_lower for word in ["tax", "taxed", "taxation", "penalty", "penalties"]):
            if "tax" in config.available_tools:
                tools.append("tax")
        
        # Benefit queries - use country-specific tools from config
        if any(word in query_lower for word in ["pension", "benefit", "social security", "centrelink", "state pension", "eps", "monthly pension", "nps", "annuity"]):
            # Check which benefit tool is available for this country
            if "eps_benefit" in config.available_tools:
                tools.append("eps_benefit")
            elif "benefit" in config.available_tools:
                tools.append("benefit")
        
        # Projection queries
        if any(word in query_lower for word in ["project", "forecast", "grow", "future", "years", "balance in"]):
            if "projection" in config.available_tools:
                tools.append("projection")
        
        # Default fallback - use first 2 available tools from config
        if not tools:
            tools = config.available_tools[:2] if len(config.available_tools) >= 2 else config.available_tools
        
        return list(set(tools))
    
    def act_execute_tools(self, state: AgentState, tools: List[str]) -> Dict:
        """
        Acting phase: Execute selected tools and gather results.
        
        Args:
            state: Current agent state
            tools: List of tools to execute
            
        Returns:
            Dictionary of tool results
        """
        tool_results = {}
        
        for tool_name in tools:
            try:
                result = self.agent.tools.call_tool(
                    tool_name, 
                    state.member_id, 
                    state.withdrawal_amount or 0, 
                    state.country
                )
                tool_results[tool_name] = result
                self.printf(f"✅ Tool '{tool_name}' executed successfully")
            except Exception as e:
                self.printf(f"❌ Tool '{tool_name}' failed: {e}")
                tool_results[tool_name] = {"error": str(e)}
        
        return tool_results
    
    def synthesize_response(self, state: AgentState, attempt: int) -> Dict:
        """
        Generate AI response for current attempt.
        
        Args:
            state: Current agent state
            attempt: Current attempt number
            
        Returns:
            Response data dictionary with text, tokens, and cost
        """
        self.printf(f"\n🔄 Synthesis Attempt {attempt}/{MAX_VALIDATION_ATTEMPTS}")
        
        response_data = self.agent.generate_response(
            state.user_query,
            state.context,
            state.tool_results,
            state.validation_history
        )
        
        state.synthesis_attempts.append({
            "attempt": attempt,
            "input_tokens": response_data["input_tokens"],
            "output_tokens": response_data["output_tokens"],
            "cost": response_data["cost"],
            "duration": response_data["duration"],
            "model": self.agent.model_type
        })
        
        return response_data
    
    def observe_and_validate(self, response_text: str, state: AgentState) -> Dict:
        """
        Observation phase: Validate the generated response.
        
        Args:
            response_text: Generated response to validate
            state: Current agent state
            
        Returns:
            Validation result dictionary
        """
        if not self.agent.validator:
            return {"passed": True, "confidence": 1.0, "violations": []}
        
        validation_result = self.agent.validator.validate(
            response_text,
            state.user_query,
            state.context,
            member_profile=state.member_profile,
            tool_output=state.tool_results
        )
        
        state.validation_history.append(validation_result)
        return validation_result
    
    def finalize_response(self, response_text: str, state: AgentState) -> str:
        """
        Finalize response with name restoration, greeting, and citations.
        
        Args:
            response_text: Raw response text
            state: Current agent state
            
        Returns:
            Finalized response text
        """
        # Restore real name if anonymized
        if state.anonymized_name and state.real_name:
            response_text = self.agent.restore_member_name(
                response_text, 
                state.anonymized_name, 
                state.real_name
            )
            self.printf(f"🔓 Restored anonymised '{state.anonymized_name}' → '{state.real_name}'")
        
        # Add personalized greeting
        response_text = self.agent.add_personalized_greeting(response_text, state.real_name)
        self.printf(f"✅ Added personalized greeting for {state.real_name}")
        
        # Add citations and disclaimer
        response_text = self.agent.add_citations_and_disclaimer(
            response_text, 
            state.country, 
            state.selected_tools
        )
        self.printf(f"📚 Added citations for {state.country}")
        
        return response_text
    
    def get_classifier_metrics(self) -> Dict:
        """
        Get classifier performance metrics.
        
        Returns:
            Dictionary with classification statistics
        """
        return self.classifier.get_metrics()
    
    def print_classifier_metrics(self):
        """Print classifier performance metrics."""
        self.classifier.print_metrics()
    
    def run_agentic_loop(self, state: AgentState) -> Dict:
        """
        Main ReAct agentic loop: Reason → Act → Observe → Iterate.
        
        Args:
            state: Initial agent state
            
        Returns:
            Complete response dictionary
        """
        # Phase 1: REASON - Classify query
        self.printf("🔍 Phase 1: REASON - Classifying query topic...")
        try:
            from utils.progress import mark_phase_running, mark_phase_complete, mark_phase_error
            mark_phase_running('phase_3_classification')
        except:
            pass
        
        try:
            state.classification = self.classify_query_topic(state.user_query)
            
            # Check if classification failed
            if state.classification.get('method') == 'llm_fallback_error' or state.classification.get('error'):
                try:
                    mark_phase_error('phase_3_classification', state.classification.get('error', 'Classification failed'))
                except:
                    pass
            else:
                try:
                    mark_phase_complete('phase_3_classification')
                except:
                    pass
        except Exception as e:
            self.printf(f"❌ Classification error: {e}")
            try:
                mark_phase_error('phase_3_classification', str(e))
            except:
                pass
            state.classification = {
                "is_on_topic": True,
                "classification": "error",
                "confidence": 0.0,
                "method": "error_fallback",
                "error": str(e)
            }
        
        if not state.classification["is_on_topic"]:
            return self.handle_off_topic_query(state)
        
        self.printf(f"✅ Query is ON-TOPIC: '{state.classification['classification']}'")
        
        # Phase 2: REASON - Select tools
        self.printf("\n🧠 Phase 2: REASON - Selecting tools...")
        try:
            mark_phase_running('phase_4_planning')
        except:
            pass
        
        state.selected_tools = self.reason_and_select_tools(state)
        self.printf(f"✅ Tools selected: {state.selected_tools}")
        
        try:
            mark_phase_complete('phase_4_planning')
        except:
            pass
        
        # Phase 3: ACT - Execute tools
        self.printf("\n⚙️  Phase 3: ACT - Executing tools...")
        try:
            mark_phase_running('phase_5_execution')
        except:
            pass
        
        state.tool_results = self.act_execute_tools(state, state.selected_tools)
        
        try:
            mark_phase_complete('phase_5_execution')
        except:
            pass
        
        # Phase 4: ITERATE - Synthesis + Validation Loop
        self.printf("\n🔄 Phase 4: ITERATE - Synthesis + Validation...")
        
        # Mark synthesis phase as running
        try:
            from utils.progress import mark_phase_running, mark_phase_complete
            mark_phase_running('phase_6_synthesis')
        except:
            pass
        
        for attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):
            # ACT: Generate response
            response_data = self.synthesize_response(state, attempt)
            response_text = response_data["text"]
            
            # Mark synthesis complete after first attempt
            if attempt == 1:
                try:
                    mark_phase_complete('phase_6_synthesis')
                except:
                    pass
            
            # Mark validation phase as running
            try:
                mark_phase_running('phase_7_validation')
            except:
                pass
            
            # OBSERVE: Validate response
            validation_result = self.observe_and_validate(response_text, state)
            
            # Mark validation complete
            try:
                mark_phase_complete('phase_7_validation')
            except:
                pass
            
            if validation_result.get("passed", True):
                self.printf(f"✅ Validation PASSED on attempt {attempt}")
                state.validation_passed = True
                state.attempts = attempt
                state.final_response = self.finalize_response(response_text, state)
                
                # Fetch citations
                state.citations = self.agent.get_citations_for_tools(
                    state.country, 
                    state.selected_tools
                )
                
                return {
                    "response": state.final_response,
                    "validation": validation_result,
                    "tools_used": list(state.tool_results.keys()),
                    "attempts": state.attempts,
                    "synthesis_results": state.synthesis_attempts,
                    "validation_results": state.validation_history,
                    "classification": state.classification,
                    "citations": state.citations
                }
            else:
                self.printf(f"❌ Validation FAILED on attempt {attempt}/{MAX_VALIDATION_ATTEMPTS}")
                if attempt < MAX_VALIDATION_ATTEMPTS:
                    self.printf("🔄 Retrying with validation feedback...")
                    continue
        
        # Max attempts reached - return best response
        self.printf("⚠️ Max attempts reached. Using last response.")
        state.attempts = MAX_VALIDATION_ATTEMPTS
        state.final_response = self.finalize_response(response_text, state)
        state.citations = self.agent.get_citations_for_tools(state.country, state.selected_tools)
        
        return {
            "response": state.final_response,
            "validation": state.validation_history[-1] if state.validation_history else {"passed": False, "confidence": 0.0},
            "tools_used": list(state.tool_results.keys()),
            "attempts": state.attempts,
            "synthesis_results": state.synthesis_attempts,
            "validation_results": state.validation_history,
            "classification": state.classification,
            "citations": state.citations
        }


def printf(msg):
    """Print with timestamp."""
    print(f"{msg}")

