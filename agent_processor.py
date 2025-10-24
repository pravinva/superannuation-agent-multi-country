# agent_processor.py - FIXED VERSION
"""
Agent processor wrapper that integrates with Streamlit UI
✅ FIXED: Changed agent.process_query() → agent.query()
✅ FIXED: Updated parameters to match agent.query() signature
"""

from agent import MultiCountryAdvisorAgent
import streamlit as st
import time


def agent_query(user_id, country, query_str, extra_context, session_id,
                judge_llm_fn=None, mlflow_experiment_path=None, 
                validation_mode="llm_judge"):
    """
    Process agent query with real-time progress updates and validation mode support
    
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
    
    # Create progress container for real-time updates
    if 'progress_container' not in st.session_state:
        st.session_state.progress_container = st.empty()
    
    progress_placeholder = st.session_state.progress_container
    
    def status_callback(stage, message):
        """Real-time status updates with progress bars and info messages"""
        
        with progress_placeholder.container():
            
            if stage == "planning_start":
                st.info(f"🧠 **Step 1/5:** Planning query execution ({validation_mode} validation)...")
                st.progress(0.15, text="Analyzing query and preparing context...")
                
            elif stage == "planning_complete":
                st.success(f"✅ **Step 1/5 Complete:** Planning finished")
                st.progress(0.20, text="Query plan ready")
            
            elif stage == "tool_start":
                st.info(f"⚙️ **Step 2/5:** Calling {country} UC Functions...")
                st.progress(0.25, text="Executing Unity Catalog functions...")
            
            elif stage == "tool_complete":
                st.success(f"✅ **Step 2/5 Complete:** UC Functions completed")
                st.progress(0.35, text="Calculator complete")
            
            elif stage == "synthesis_start":
                st.info(f"💭 **Step 3/5:** Generating personalized response...")
                st.progress(0.40, text="Starting synthesis...")
            
            elif stage == "synthesis_stage":
                if isinstance(message, dict):
                    stage_num = message.get('stage', 1)
                    task = message.get('task', 'Processing')
                    progress_val = 0.40 + (stage_num / 3) * 0.20  # 40-60%
                    st.info(f"📝 **Step 3/5:** {task} (Stage {stage_num}/3)")
                    st.progress(progress_val, text=f"Generating {task.lower()}...")
            
            elif stage == "synthesis_complete":
                if isinstance(message, dict):
                    attempts = message.get('attempts', 1)
                    if attempts > 1:
                        st.success(f"✅ **Step 3/5 Complete:** Response generated after {attempts} attempts")
                    else:
                        st.success(f"✅ **Step 3/5 Complete:** Response generated")
                st.progress(0.60, text="Synthesis complete")
            
            elif stage == "validation_start":
                mode_display = validation_mode.replace('_', ' ').title()
                st.info(f"⚖️ **Step 4/5:** Validating response ({mode_display})...")
                st.progress(0.65, text="Running compliance checks...")
            
            elif stage == "validation_complete":
                passed = message.get('passed', True) if isinstance(message, dict) else True
                if passed:
                    st.success(f"✅ **Step 4/5 Complete:** Validation passed")
                    st.progress(0.80, text="Validation passed")
                else:
                    st.warning(f"⚠️ **Step 4/5 Complete:** Validation issues found")
                    st.progress(0.80, text="Validation complete with warnings")
            
            elif stage == "retry":
                if isinstance(message, dict):
                    attempt = message.get('attempt', 2)
                    violations = message.get('violations', 0)
                    st.warning(f"🔄 **Retry {attempt}:** Correcting {violations} issue(s)...")
                    st.progress(0.50, text=f"Regenerating with feedback...")
            
            elif stage == "complete":
                st.success(f"✅ **Step 5/5 Complete:** Ready to display!")
                st.progress(1.0, text="Processing complete!")
    
    # STEP 0: Planning phase (simulate planning)
    status_callback("planning_start", None)
    time.sleep(0.5)  # Brief pause to show planning
    status_callback("planning_complete", None)
    
    # Initialize agent for country
    agent = MultiCountryAdvisorAgent(country=country)
    agent.session_id = session_id
    
    # Get member_id and name
    member_id = extra_context.get('member_id', user_id)
    member_name = extra_context.get('name', 'Member')
    
    try:
        # ✅ FIXED: Call agent.query() with correct parameters
        answer, citations, metadata, judge_resp, judge_verdict, error_info, tools_called = agent.query(
            user_query=query_str,
            member_id=member_id,
            anonymize=False,  # Use real names for hyper-personalization
            validation_mode=validation_mode,
            max_validation_attempts=2,
            status_callback=status_callback
        )
        
        # Final completion message
        status_callback("complete", None)
        
        # Parse response into structured format
        response_dict = {
            "situation": "",
            "insights": [],
            "recommendations": []
        }
        
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
        
        # Show error in progress container
        with progress_placeholder.container():
            st.error(f"❌ Error: {str(e)}")
            st.progress(0.0, text="Processing failed")
        
        return (
            f"Error: {str(e)}",
            [],
            {"situation": "", "insights": [], "recommendations": []},
            "",
            "ERROR",
            error_info,
            []
        )
