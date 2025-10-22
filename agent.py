# agent.py
import uuid
from agent_processor import agent_query

def run_agent_interaction(user_id, country, query_str, extra_context=None, 
                         session_id=None, judge_llm_fn=None, mlflow_experiment_path=None):
    """Run a complete agent interaction"""
    session_id = session_id or str(uuid.uuid4())
    
    answer, citations, result, judge_resp, judge_verdict, error_info = agent_query(
        user_id=user_id,
        country=country,
        query_str=query_str,
        extra_context=extra_context,
        session_id=session_id,
        judge_llm_fn=judge_llm_fn,
        mlflow_experiment_path=mlflow_experiment_path
    )
    
    return {
        "answer": answer,
        "citations": citations,
        "result": result,
        "judge_response": judge_resp,
        "judge_verdict": judge_verdict,
        "error": error_info,
        "session_id": session_id
    }

