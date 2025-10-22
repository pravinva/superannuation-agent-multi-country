# progress_utils.py
"""Progress tracking and log display utilities"""

import streamlit as st

def render_progress(show_logs=True):
    """
    Display agent processing progress - shows summary after completion
    """
    if not show_logs:
        return
    
    st.markdown("### 📋 View Logs")
    
    # Check if there's agent output
    if "agent_output" in st.session_state and st.session_state.agent_output:
        output = st.session_state.agent_output
        
        st.success("✅ Processing complete!")
        
        # Show processing summary
        with st.expander("📊 Processing Summary", expanded=True):
            st.write("✅ Retrieved member profile")
            st.write("✅ Called Unity Catalog functions")
            st.write("✅ Generated recommendation")
            st.write("✅ Logged to governance table")
            
            if "tool_used" in output:
                st.write(f"Tool: `{output['tool_used']}`")
            
            if "judge_verdict" in output and output["judge_verdict"]:
                st.write(f"Judge verdict: {output['judge_verdict']}")
    else:
        st.info("Agent processing logs will appear here...")
        st.caption("No processing has occurred yet. Click 'Get Recommendation' to start.")

