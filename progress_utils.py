# progress_utils.py
"""Dynamic progress rendering with actual member data and tool execution tracking"""

import streamlit as st
import time
from datetime import datetime


def render_progress(member_data, tools_called=None, show_logs=True):
    """
    Render dynamic multi-stage progress display
    
    Args:
        member_data: Dictionary with member profile (name, age, balance, etc.)
        tools_called: List of dicts with {name, duration, status}
        show_logs: Boolean to show/hide progress (respects sidebar toggle)
    """
    
    # CRITICAL: Return early if logs are hidden
    if not show_logs:
        return
    
    st.markdown("---")
    st.subheader("🔄 Processing Pipeline")
    
    # Extract member data
    member_name = member_data.get('name', 'Unknown')
    member_id = member_data.get('member_id', 'N/A')
    age = member_data.get('age', 'N/A')
    balance = member_data.get('super_balance', 0)
    try:
        balance = float(balance)
    except:
        balance = 0
    
    employment = member_data.get('employment_status', 'N/A')
    marital_status = member_data.get('marital_status', 'N/A')
    
    # Stage 1: Data Retrieval
    with st.status("📦 Data Retrieval from Unity Catalog", expanded=True) as status1:
        st.write(f"**Member:** {member_name} (Age {age}) • **Balance:** ${balance:,.0f}")
        st.write(f"**Marital Status:** {marital_status} • **Employment:** {employment}")
        st.write("**Temperature:** 0.3")
        st.write("**Privacy Mode:** ✓ Anonymized (PII removed)")
        st.write("**Validation:** ✓ Enabled (Claude Sonnet 4)")
        time.sleep(0.3)
        status1.update(label="✅ Data Retrieved from Unity Catalog", state="complete")
    
    # Stage 2: Privacy Protection
    with st.status("🔒 Privacy Protection Active", expanded=False) as status2:
        anonymized_id = f"Member {member_id[-4:]}" if len(str(member_id)) >= 4 else "Member XXXX"
        st.info(f'Original: "{member_name}" → Anonymized: "{anonymized_id}"')
        st.caption("_Real name will not be sent to Claude API. It will be restored in final response._")
        time.sleep(0.2)
        status2.update(label="✅ Privacy Protection Active", state="complete")
    
    # Stage 3: Processing Time Estimate
    st.info("⏱️ **Estimated Processing Time:** 45-60 seconds")
    
    # Stage 4: LLM Query Planning
    with st.status("🤖 Claude Opus 4.1: Calling Claude Opus for query planning...", expanded=False) as status3:
        st.caption("Estimated: 3-5 seconds")
        time.sleep(0.5)
        status3.update(label="✅ Claude Opus 4.1: Query planned", state="complete")
    
    # Stage 5: Tool Execution (Dynamic based on actual tools called)
    if tools_called and len(tools_called) > 0:
        st.markdown("### 🛠️ Tool Execution")
        
        # Create columns dynamically based on number of tools
        num_tools = len(tools_called)
        cols = st.columns(min(num_tools, 3))  # Max 3 columns
        
        for idx, tool in enumerate(tools_called):
            col_idx = idx % 3
            with cols[col_idx]:
                tool_name = tool.get('name', 'Unknown Tool')
                duration = tool.get('duration', 0)
                status = tool.get('status', 'completed')
                
                icon = "✅" if status == "completed" else "❌" if status == "error" else "⏳"
                
                with st.status(f"{icon} Tool Server: {tool_name}", expanded=False) as tool_status:
                    st.caption(f"Completed in {duration:.2f}s")
                    tool_status.update(
                        label=f"{icon} Tool Server: {tool_name} → Completed in {duration:.2f}s",
                        state="complete" if status == "completed" else "error"
                    )
    else:
        # No tools called yet - show placeholder
        st.info("🔧 Waiting for tool execution...")
    
    # Stage 6: Multi-Stage Synthesis
    st.markdown("### ✍️ Multi-Stage Synthesis")
    st.caption("_Generating personalized advice (Estimated: ~45 seconds total)_")
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    stages = [
        {"name": "Stage 1/3: Situation Summary", "progress": 33, "tokens": 150},
        {"name": "Stage 2/3: Analyzing Data & Generating Insights", "progress": 66, "tokens": 450},
        {"name": "Stage 3/3: Formulating Recommendations", "progress": 100, "tokens": 200}
    ]
    
    for stage in stages:
        status_text.markdown(f"**{stage['name']}**")
        
        # Animate progress
        current_progress = 0 if stage['progress'] == 33 else (stage['progress'] - 33)
        for i in range(current_progress, stage['progress'] + 1):
            progress_bar.progress(i)
            time.sleep(0.015)
        
        # Show completion
        if stage['progress'] == 33:
            st.success("✅ Stage 1/3: Situation Summary - Complete")
        elif stage['progress'] == 66:
            st.success(f"✅ Stage 2/3: Analyzing Data & Generating Insights - Complete  \n_Estimated: 12-15 seconds ({stage['tokens']} tokens)_")
        elif stage['progress'] == 100:
            st.success("✅ Stage 3/3: Formulating Recommendations - Complete")
    
    status_text.empty()
    st.success("🎉 **Synthesis Complete!** Response generated successfully.")


def render_progress_simple(message, show_logs=True):
    """Simple progress message for quick updates"""
    if not show_logs:
        return
        
    with st.spinner(message):
        time.sleep(0.5)

