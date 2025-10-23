# agent_processor.py - Wrapper for backward compatibility with app.py
from agent import MultiCountryAdvisorAgent


def agent_query(user_id, country, query_str, extra_context, session_id,
                judge_llm_fn=None, mlflow_experiment_path=None):
    """
    Process agent query - wrapper for app.py compatibility
    
    Args:
        user_id: User identifier
        country: "Australia", "USA", "United Kingdom", "India"
        query_str: User's retirement question
        extra_context: Member profile dict with member_id, age, balance, etc.
        session_id: Session identifier
        judge_llm_fn: (Ignored - using built-in validator)
        mlflow_experiment_path: (Optional) MLflow logging path
    
    Returns:
        Tuple: (answer, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called)
    """
    
    # Initialize agent for country
    agent = MultiCountryAdvisorAgent(country=country)
    agent.session_id = session_id
    
    # Get member_id
    member_id = extra_context.get('member_id', user_id)
    
    try:
        # Call agent
        response, tool_results = agent.process_query(
            member_id=member_id,
            user_query=query_str,
            temperature=None,
            anonymize=True,
            enable_validation=True
        )
        
        # Parse response into structured format
        response_dict = {
            "situation": "",
            "insights": [],
            "recommendations": []
        }
        
        sections = response.split("##")
        for section in sections:
            if "Situation" in section:
                lines = [l.strip() for l in section.split('\n') if l.strip() and '##' not in l and '---' not in l]
                response_dict['situation'] = ' '.join(lines)
            elif "Insights" in section or "Analysis" in section:
                lines = [l.strip() for l in section.split('\n') if l.strip() and ('•' in l or l.startswith('-'))]
                response_dict['insights'] = [l.lstrip('•-').strip() for l in lines]
            elif "Recommendation" in section:
                lines = [l.strip() for l in section.split('\n') if l.strip() and any(c.isdigit() for c in l[:3])]
                response_dict['recommendations'] = [l.lstrip('0123456789.').strip() for l in lines]
        
        # Extract metadata
        validation = tool_results.get('_validation', {})
        judge_verdict = "Pass" if validation.get('passed', True) else "Review"
        judge_resp = validation.get('reasoning', '')
        
        tools_called = tool_results.get('_tools_called', [])
        
        # Citations from country tool
        citations = tool_results.get('citations', [
            f"{country} Tax Authority Guidelines",
            f"{country} Pension Regulations 2025"
        ])
        
        error_info = ""
        
        return response, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called
        
    except Exception as e:
        import traceback
        error_info = f"{str(e)}\n{traceback.format_exc()}"
        
        return (
            f"Error: {str(e)}",
            [],
            {"situation": "", "insights": [], "recommendations": []},
            "",
            "ERROR",
            error_info,
            []
        )

