# agent.py
"""
Agent orchestration with tool tracking
Coordinates agent interactions and returns structured responses with execution metrics
"""

import uuid
from agent_processor import agent_query


def run_agent_interaction(user_id, country, query_str, extra_context=None,
                          session_id=None, judge_llm_fn=None, mlflow_experiment_path=None):
    """
    Run a complete agent interaction with tool tracking
    
    Args:
        user_id (str): User identifier
        country (str): Country context (e.g., "Australia", "USA", "United Kingdom", "India")
        query_str (str): User's retirement query
        extra_context (dict): Member profile data (name, age, balance, etc.)
        session_id (str, optional): Session identifier. Defaults to new UUID.
        judge_llm_fn (callable, optional): Judge LLM function for validation
        mlflow_experiment_path (str, optional): MLflow experiment path for logging
    
    Returns:
        dict: Complete agent response with:
            - answer (str): Full text response
            - citations (list): List of reference citations
            - response_dict (dict): Structured 3-part response (situation, insights, recommendations)
            - judge_response (str): Judge LLM response
            - judge_verdict (str): Pass/Review/ERROR
            - error (str): Error information if any
            - session_id (str): Session identifier
            - tools_called (list): List of tools executed with timing data
    """
    
    # Generate session ID if not provided
    session_id = session_id or str(uuid.uuid4())
    
    # Call agent_query and unpack all 7 return values
    answer, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called = agent_query(
        user_id=user_id,
        country=country,
        query_str=query_str,
        extra_context=extra_context,
        session_id=session_id,
        judge_llm_fn=judge_llm_fn,
        mlflow_experiment_path=mlflow_experiment_path
    )
    
    # Return comprehensive response dictionary
    return {
        "answer": answer,                      # Full text answer (legacy format)
        "citations": citations,                # List of citations
        "response_dict": response_dict,        # Structured: {situation, insights, recommendations}
        "judge_response": judge_resp,          # Judge LLM feedback
        "judge_verdict": judge_verdict,        # Pass/Review/ERROR
        "error": error_info,                   # Error details if any
        "session_id": session_id,              # Session tracking ID
        "tools_called": tools_called           # List of {name, duration, status}
    }

