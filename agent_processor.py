# agent_processor.py
"""Agent query processing with dynamic tool tracking"""

import traceback
import time
from tools import get_country_tool
from country_content import COUNTRY_REGULATIONS
from audit.audit_utils import log_query_event
from mlflow_utils import log_mlflow_run
from config import MLFLOW_PROD_EXPERIMENT_PATH


def agent_query(user_id, country, query_str, extra_context, session_id,
                judge_llm_fn=None, mlflow_experiment_path=None):
    """
    Process agent query and return structured response with tool tracking
    """
    
    tool_fn = get_country_tool(country)
    user_data = extra_context or {}
    
    # Initialize response structure
    response_dict = {
        "situation": "",
        "insights": [],
        "recommendations": []
    }
    
    # Track tools called
    tools_called = []
    
    error_info = ""
    judge_resp = ""
    judge_verdict = "N/A"
    citations = []
    
    try:
        # Call country-specific UC function and track timing
        start_time = time.time()
        calc_result = tool_fn(user_data)
        duration = time.time() - start_time
        
        # Record tool execution
        tool_name = calc_result.get('tool_name', 'retirement_calculator')
        tools_called.append({
            "name": tool_name,
            "duration": duration,
            "status": "completed"
        })
        
        # Extract results
        amount = calc_result.get('amount', 0)
        
        # DYNAMIC RESPONSE BUILDING (using actual data)
        member_name = user_data.get('name', 'Member')
        age = user_data.get('age', 'N/A')
        balance = user_data.get('super_balance', 0)
        try:
            balance = float(balance)
        except:
            balance = 0
        
        # Get actual response from tool or build from data
        if 'situation' in calc_result:
            response_dict['situation'] = calc_result['situation']
        else:
            response_dict['situation'] = f"{member_name}, based on your current balance of ${balance:,.0f} and age {age}, here is your retirement situation analysis."
        
        if 'insights' in calc_result:
            response_dict['insights'] = calc_result['insights']
        else:
            response_dict['insights'] = [
                f"Your current balance: ${balance:,.0f}",
                f"Estimated withdrawal amount: ${amount:,.0f}",
                f"Remaining balance after withdrawal: ${balance - amount:,.0f}"
            ]
        
        if 'recommendations' in calc_result:
            response_dict['recommendations'] = calc_result['recommendations']
        else:
            response_dict['recommendations'] = [
                "Review your withdrawal strategy based on your retirement goals.",
                "Consider consulting a financial advisor for personalized advice."
            ]
        
        citations = calc_result.get('citations', [
            f"{country} Tax Authority Guidelines",
            f"{country} Pension Regulations 2025"
        ])
        
        # Combine for legacy 'answer' field
        answer = (
            f"**Your Current Situation:**\n{response_dict['situation']}\n\n"
            f"**Analysis & Insights:**\n" + "\n".join(f"• {i}" for i in response_dict['insights']) + "\n\n"
            f"**Our Recommendations:**\n" + "\n".join(f"{idx+1}. {r}" for idx, r in enumerate(response_dict['recommendations']))
        )
        
        result_preview = f"${amount:,.2f}"
        tool_used = tool_name
        
        # Judge LLM validation (optional)
        if judge_llm_fn:
            try:
                judge_start = time.time()
                judge_resp = judge_llm_fn(query_str, answer, user_data)
                judge_duration = time.time() - judge_start
                
                tools_called.append({
                    "name": "Judge LLM (Claude Sonnet 4)",
                    "duration": judge_duration,
                    "status": "completed"
                })
                
                judge_verdict = "Pass" if "approve" in judge_resp.lower() else "Review"
            except Exception as e:
                judge_resp = f"Judge error: {str(e)}"
                judge_verdict = "ERROR"
        
        # Log to governance table
        log_query_event(
            user_id=user_id,
            session_id=session_id,
            country=country,
            query_str=query_str,
            agent_response=answer,
            result_preview=result_preview,
            citations=citations,
            tool_used=tool_used,
            judge_response=judge_resp,
            judge_verdict=judge_verdict
        )
        
        # Log to MLflow
        if mlflow_experiment_path:
            log_mlflow_run(
                experiment_path=mlflow_experiment_path,
                query=query_str,
                response=answer,
                country=country,
                user_id=user_id
            )
        
    except Exception as e:
        error_info = f"{str(e)}\n{traceback.format_exc()}"
        answer = f"Error processing query: {str(e)}"
        result_preview = "ERROR"
        citations = []
        tool_used = "error"
        
        # Record failed tool
        tools_called.append({
            "name": "Tool Execution",
            "duration": 0,
            "status": "error"
        })
    
    # Return with tools_called for progress display
    return answer, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called

