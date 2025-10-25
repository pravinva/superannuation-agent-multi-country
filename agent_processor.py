# agent_processor.py - ENHANCED WITH LIVE PROGRESS UPDATES
"""
Agent processor wrapper that integrates with Streamlit UI
✅ FIXED: Changed agent.process_query() → agent.query()
✅ FIXED: Updated parameters to match agent.query() signature
✅ ADDED: Enhanced error handling and type safety
✅ NEW: Live progress updates using progress_utils
"""

from agent import MultiCountryAdvisorAgent
import streamlit as st
import time
from progress_utils import update_live_progress_phase, update_live_progress_summary


def safe_list_conversion(data, default=None):
    """Safely convert data to list, handling various edge cases"""
    if default is None:
        default = []
    
    if data is None:
        return default
    elif isinstance(data, list):
        return data
    elif isinstance(data, (tuple, set)):
        return list(data)
    else:
        try:
            return list(data)
        except (TypeError, ValueError):
            return default


def agent_query(user_id, country, query_str, extra_context, session_id,
                judge_llm_fn=None, mlflow_experiment_path=None, 
                validation_mode="llm_judge"):
    """
    Process agent query with LIVE progress updates
    
    Args:
        user_id: User identifier
        country: Country name ("Australia", "USA", "United Kingdom", "India")
        query_str: User's retirement question
        extra_context: Member profile dict with member_id, age, balance, name, etc.
        session_id: Session identifier
        judge_llm_fn: (Ignored - using built-in validator)
        mlflow_experiment_path: (Optional) MLflow logging path
        validation_mode: "llm_judge", "hybrid", or "deterministic"
    
    Returns:
        Tuple: (answer, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called)
    """
    
    def status_callback(stage, message):
        """
        ✅ NEW: Real-time status updates with LIVE phase updates
        """
        
        if stage == "planning_start":
            update_live_progress_phase(
                phase_num=1,
                phase_name="📊 Phase 1: Data Retrieval & Planning",
                status="running",
                details=f"Analyzing query with {validation_mode} validation...",
                icon="📊"
            )
            
        elif stage == "planning_complete":
            # Keep phase 1 in running state, will complete when data is loaded
            pass
        
        elif stage == "data_loaded":
            # Data is loaded, complete phase 1
            if isinstance(message, dict):
                member_name = message.get('name', 'Member')
                member_age = message.get('age', 'N/A')
                balance = message.get('super_balance', 0)
                balance_str = f"${int(balance):,}" if isinstance(balance, (int, float)) else str(balance)
                
                update_live_progress_phase(
                    phase_num=1,
                    phase_name="📊 Phase 1: Data Retrieval & Planning",
                    status="completed",
                    details=f"Member: {member_name} (Age {member_age}) • Balance: {balance_str}",
                    icon="📊"
                )
        
        elif stage == "tool_start":
            tool_count = message if isinstance(message, int) else 3
            update_live_progress_phase(
                phase_num=2,
                phase_name="⚙️ Phase 2: UC Function Execution",
                status="running",
                details=f"Calling {tool_count} {country} UC Functions...",
                icon="⚙️"
            )
        
        elif stage == "tool_complete":
            if isinstance(message, dict):
                tools_called = message.get('tools_called', [])
                duration = message.get('duration', 0)
                
                update_live_progress_phase(
                    phase_num=2,
                    phase_name="⚙️ Phase 2: UC Function Execution",
                    status="completed",
                    details=f"Executed {len(tools_called)} functions successfully",
                    duration=duration,
                    icon="⚙️"
                )
            else:
                update_live_progress_phase(
                    phase_num=2,
                    phase_name="⚙️ Phase 2: UC Function Execution",
                    status="completed",
                    details="Calculator functions completed",
                    icon="⚙️"
                )
        
        elif stage == "synthesis_start":
            update_live_progress_phase(
                phase_num=3,
                phase_name="✏️ Phase 3: LLM Synthesis (Claude Opus 4.1)",
                status="running",
                details="Generating personalized response...",
                icon="✏️"
            )
        
        elif stage == "synthesis_stage":
            if isinstance(message, dict):
                stage_num = message.get('stage', 1)
                task = message.get('task', 'Processing')
                update_live_progress_phase(
                    phase_num=3,
                    phase_name="✏️ Phase 3: LLM Synthesis (Claude Opus 4.1)",
                    status="running",
                    details=f"Stage {stage_num}/3: {task}...",
                    icon="✏️"
                )
        
        elif stage == "synthesis_complete":
            if isinstance(message, dict):
                attempts = message.get('attempts', 1)
                duration = message.get('duration', 0)
                
                if attempts > 1:
                    details = f"Response generated after {attempts} attempts"
                else:
                    details = "Response generated successfully"
                
                update_live_progress_phase(
                    phase_num=3,
                    phase_name="✏️ Phase 3: LLM Synthesis (Claude Opus 4.1)",
                    status="completed",
                    details=details,
                    duration=duration,
                    icon="✏️"
                )
        
        elif stage == "validation_start":
            mode_display = validation_mode.replace('_', ' ').title()
            update_live_progress_phase(
                phase_num=4,
                phase_name="⚖️ Phase 4: Judge Validation (Claude Sonnet 4)",
                status="running",
                details=f"Running {mode_display} validation...",
                icon="⚖️"
            )
        
        elif stage == "validation_complete":
            if isinstance(message, dict):
                passed = message.get('passed', True)
                confidence = message.get('confidence', 0)
                violations = message.get('violations', [])
                duration = message.get('duration', 0)
                
                status = "completed" if passed else "error"
                verdict_text = "✅ Passed" if passed else "⚠️ Issues Found"
                
                update_live_progress_phase(
                    phase_num=4,
                    phase_name="⚖️ Phase 4: Judge Validation (Claude Sonnet 4)",
                    status=status,
                    details=f"{verdict_text} • Confidence: {confidence:.0%} • Issues: {len(violations)}",
                    duration=duration,
                    icon="⚖️"
                )
            else:
                passed = message.get('passed', True) if isinstance(message, dict) else True
                status = "completed" if passed else "error"
                update_live_progress_phase(
                    phase_num=4,
                    phase_name="⚖️ Phase 4: Judge Validation",
                    status=status,
                    details="Validation complete",
                    icon="⚖️"
                )
        
        elif stage == "retry":
            if isinstance(message, dict):
                attempt = message.get('attempt', 2)
                violations = message.get('violations', 0)
                
                update_live_progress_phase(
                    phase_num=3,
                    phase_name="✏️ Phase 3: LLM Synthesis (Retry)",
                    status="running",
                    details=f"Retry {attempt}: Correcting {violations} issue(s)...",
                    icon="🔄"
                )
        
        elif stage == "audit_start":
            update_live_progress_phase(
                phase_num=5,
                phase_name="📝 Phase 5: Audit Logging",
                status="running",
                details="Writing to governance table...",
                icon="📝"
            )
        
        elif stage == "audit_complete":
            if isinstance(message, dict):
                session_id = message.get('session_id', 'unknown')
                update_live_progress_phase(
                    phase_num=5,
                    phase_name="📝 Phase 5: Audit Logging",
                    status="completed",
                    details=f"Session: {session_id[:12]}... | Stored in governance table",
                    icon="📝"
                )
            else:
                update_live_progress_phase(
                    phase_num=5,
                    phase_name="📝 Phase 5: Audit Logging",
                    status="completed",
                    details="Logged to governance table",
                    icon="📝"
                )
        
        elif stage == "complete":
            # Update summary metrics
            if isinstance(message, dict):
                total_time = message.get('total_time', 0)
                tools_count = message.get('tools_count', 0)
                citations_count = message.get('citations_count', 0)
                
                update_live_progress_summary(total_time, tools_count, citations_count)
    
    # Initialize agent for country
    agent = MultiCountryAdvisorAgent(country=country)
    agent.session_id = session_id
    
    # Get member_id and name with safe defaults
    member_id = extra_context.get('member_id', user_id) if extra_context else user_id
    member_name = extra_context.get('name', 'Member') if extra_context else 'Member'
    
    # Notify that data is loaded
    if extra_context:
        status_callback("data_loaded", extra_context)
    
    try:
        # ✅ FIXED: Call agent.query() with correct parameters
        result = agent.query(
            user_query=query_str,
            member_id=member_id,
            anonymize=False,  # Use real names for hyper-personalization
            validation_mode=validation_mode,
            max_validation_attempts=2,
            status_callback=status_callback
        )
        
        # ✅ ENHANCED: Safe unpacking with type checking
        if isinstance(result, (list, tuple)) and len(result) >= 7:
            answer, citations, metadata, judge_resp, judge_verdict, error_info, tools_called = result
        else:
            # Handle unexpected return format
            answer = str(result) if result else "No response generated"
            citations = []
            metadata = {}
            judge_resp = ""
            judge_verdict = "UNKNOWN"
            error_info = "Unexpected return format from agent.query()"
            tools_called = []
        
        # ✅ ENHANCED: Ensure all return values are safe types
        citations = safe_list_conversion(citations, [])
        tools_called = safe_list_conversion(tools_called, [])
        judge_resp = str(judge_resp) if judge_resp else ""
        judge_verdict = str(judge_verdict) if judge_verdict else "UNKNOWN"
        error_info = str(error_info) if error_info else ""
        
        # Final completion message
        status_callback("complete", {
            'total_time': metadata.get('total_time', 0),
            'tools_count': len(tools_called),
            'citations_count': len(citations)
        })
        
        # Parse response into structured format
        response_dict = {
            "situation": "",
            "insights": [],
            "recommendations": []
        }
        
        if answer and isinstance(answer, str):
            sections = answer.split("##")
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
        
        return answer, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called
        
    except Exception as e:
        import traceback
        error_info = f"{str(e)}\n{traceback.format_exc()}"
        
        # Show error in all phases
        for phase_num in range(1, 6):
            update_live_progress_phase(
                phase_num=phase_num,
                phase_name=f"Phase {phase_num}",
                status="error",
                details=f"Error: {str(e)}",
                icon="❌"
            )
        
        return (
            f"Error: {str(e)}",
            [],
            {"situation": "", "insights": [], "recommendations": []},
            "",
            "ERROR",
            error_info,
            []
        )
