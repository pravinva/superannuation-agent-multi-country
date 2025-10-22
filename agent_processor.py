# agent_processor.py
"""Agent query processing with logging and validation"""

import traceback
from tools import get_country_tool
from country_content import COUNTRY_REGULATIONS
from audit.audit_utils import log_query_event
from mlflow_utils import log_mlflow_run
from config import MLFLOW_PROD_EXPERIMENT_PATH

def agent_query(user_id, country, query_str, extra_context, session_id, 
                judge_llm_fn=None, mlflow_experiment_path=None):
    """
    Process agent query with full logging
    """
    tool_fn = get_country_tool(country)
    user_data = extra_context or {}
    
    answer = ""
    result_preview = ""
    citations = []
    tool_used = ""
    error_info = ""
    judge_resp = ""
    judge_verdict = "N/A"
    
    try:
        # Call the country-specific UC function
        calc_result = tool_fn(user_data)
        
        # Extract results
        amount = calc_result.get('amount', 0)
        answer = calc_result.get('summary', f"Estimated: ${amount:,.2f}")
        result_preview = f"${amount:,.2f}"
        citations = calc_result.get('citations', [])
        tool_used = calc_result.get('tool_used', 'Unknown')
        
    except Exception as e:
        answer = f"An error occurred during calculation: {str(e)}"
        error_info = traceback.format_exc()
        amount = 0
        result_preview = "Error"
        tool_used = "Error"
    
    # Judge validation (if provided)
    if judge_llm_fn:
        try:
            judge_resp, judge_verdict = judge_llm_fn(answer, query_str, country)
        except Exception as e:
            judge_verdict = "ERROR"
            error_info += f"\nJudge error: {traceback.format_exc()}"
    
    # Log to Unity Catalog governance table
    try:
        log_query_event(
            user_id=user_id,
            country=country,
            query_string=query_str,
            cost=0.05,
            agent_response=answer,
            result_preview=result_preview,
            citations=citations,
            tool_used=tool_used,
            judge_response=judge_resp,
            judge_verdict=judge_verdict,
            error_info=error_info,
            session_id=session_id
        )
    except Exception as e:
        print(f"Error logging to Unity Catalog: {e}")
    
    # Log to MLflow
    exp_path = mlflow_experiment_path or MLFLOW_PROD_EXPERIMENT_PATH
    try:
        log_mlflow_run(
            experiment_path=exp_path,
            params={
                "user_id": user_id,
                "country": country,
                "tool_used": tool_used,
                "judge_verdict": judge_verdict,
                "session_id": session_id
            },
            metrics={
                "cost": 0.05,
                "judge_pass": int(judge_verdict == "Pass"),
                "has_error": int(bool(error_info))
            },
            artifacts={
                "query": query_str,
                "answer": answer,
                "error": error_info if error_info else "None"
            }
        )
    except Exception as e:
        print(f"Error logging to MLflow: {e}")
    
    return answer, citations, {"amount": result_preview}, judge_resp, judge_verdict, error_info

