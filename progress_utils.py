# progress_utils.py - CORRECTED TO MATCH app.py CALLING PATTERN
"""
Enhanced progress tracking with thin phase cards
✅ FIXED: render_progress() now takes 3 arguments to match app.py line 294
"""

import streamlit as st
from datetime import datetime


def render_phase_card(phase_name, status, details=None, duration=None, icon="🔄"):
    """
    Render a thin card for a processing phase
    
    Args:
        phase_name: Name of phase (e.g., "Tool Server: ATO Tax Calculator")
        status: "running", "completed", "error"
        details: Optional details string
        duration: Optional duration in seconds
        icon: Icon to display
    """
    
    # Status-based styling
    if status == "completed":
        bg_color = "#d4edda"  # Light green
        border_color = "#28a745"  # Green
        status_icon = "✅"
    elif status == "error":
        bg_color = "#f8d7da"  # Light red
        border_color = "#dc3545"  # Red
        status_icon = "❌"
    elif status == "running":
        bg_color = "#fff3cd"  # Light yellow
        border_color = "#ffc107"  # Yellow
        status_icon = "🔄"
    else:
        bg_color = "#e7f3ff"  # Light blue
        border_color = "#0066cc"  # Blue
        status_icon = "ℹ️"
    
    # Build duration text
    duration_text = f" → Completed in {duration:.2f}s" if duration else ""
    details_html = f"<br/><span style='font-size: 0.85em; color: #555; font-style: italic;'>{details}</span>" if details else ""
    
    card_html = f"""
    <div style="
        background: {bg_color};
        border-left: 5px solid {border_color};
        padding: 12px 16px;
        margin: 6px 0;
        border-radius: 6px;
        font-size: 0.95em;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.2em; margin-right: 8px;">{status_icon}</span>
            <strong>{phase_name}</strong>
            <span style="color: #666; margin-left: auto;">{duration_text}</span>
        </div>
        {details_html}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)


def render_data_retrieval_card(member_data):
    """Render data retrieval phase card"""
    member_name = member_data.get('name', 'Unknown')
    member_age = member_data.get('age', 'N/A')
    member_balance = member_data.get('super_balance', 0)
    preservation_age = member_data.get('preservation_age', 60)
    employment = member_data.get('employment_status', 'Unknown')
    marital = member_data.get('marital_status', 'Unknown')
    dependents = member_data.get('dependents', 0)
    
    # Format balance with commas
    if isinstance(member_balance, (int, float)):
        balance_display = f"AUD {int(member_balance):,}"
    else:
        balance_display = str(member_balance)
    
    details = (
        f"Member: {member_name} (Age {member_age}) • Balance: {balance_display}<br/>"
        f"Marital Status: {marital} • Employment: {employment} • Dependents: {dependents}"
    )
    
    render_phase_card(
        phase_name="Data Retrieved from Unity Catalog",
        status="completed",
        details=details,
        icon="📊"
    )


def render_tool_execution_card(tool_name, authority, status, duration=None, details=None):
    """Render tool execution card"""
    if not details and authority:
        details = f"Authority: {authority}"
    
    render_phase_card(
        phase_name=f"🛠️ Tool Server: {tool_name}",
        status=status,
        details=details,
        duration=duration,
        icon="🛠️"
    )


def render_audit_card(session_id):
    """Render audit logging card"""
    render_phase_card(
        phase_name="📝 Logged to Governance Table",
        status="completed",
        details=f"Session: {session_id[:12]}... | Stored in super_advisory_demo.member_data.governance",
        icon="📝"
    )


def render_progress(member_data, tools_called, show_logs=True):
    """
    ✅ MAIN FUNCTION - Matches app.py line 294 calling pattern
    
    Args:
        member_data: Member profile dict (from app.py line 292)
        tools_called: List of tools executed (from app.py line 293)
        show_logs: Whether to show logs (from app.py line 294)
    """
    
    if not show_logs:
        return
    
    st.markdown("### 📋 Agent Processing Logs")
    
    # Check if there's any data to display
    if not member_data and not tools_called:
        st.info("📄 Agent processing logs will appear here...")
        st.caption("No processing has occurred yet. Click '🚀 Get Recommendation' to start.")
        return
    
    # Overall status
    st.success("✅ Processing complete!")
    
    # Create expandable section
    with st.expander("📊 Detailed Processing Phases", expanded=True):
        
        # PHASE 1: Data Retrieval
        if member_data:
            render_data_retrieval_card(member_data)
        
        # PHASE 2: Tool Execution
        if tools_called and len(tools_called) > 0:
            st.markdown("#### ⚙️ UC Functions Executed")
            
            for i, tool in enumerate(tools_called, 1):
                tool_name = tool.get('name', 'Unknown Tool')
                authority = tool.get('authority', '')
                status = tool.get('status', 'completed')
                duration = tool.get('duration')
                uc_function = tool.get('uc_function', '')
                regulation = tool.get('regulation', '')
                
                # Build details
                details_parts = []
                if authority:
                    details_parts.append(f"Authority: {authority}")
                if regulation:
                    details_parts.append(f"Regulation: {regulation}")
                if uc_function:
                    details_parts.append(f"Function: {uc_function}")
                
                details = " • ".join(details_parts) if details_parts else None
                
                render_tool_execution_card(
                    tool_name=tool_name,
                    authority=authority,
                    status=status,
                    duration=duration,
                    details=details
                )
        
        # PHASE 3: Audit Logging
        session_id = st.session_state.get("session_id", "unknown")
        render_audit_card(session_id)
        
        # Summary Metrics Section
        st.markdown("---")
        st.markdown("**📊 Summary Metrics**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get total time from agent_output if available
            total_time = 0
            if st.session_state.get("agent_output"):
                timings = st.session_state.agent_output.get("timings", {})
                total_time = timings.get("total", 0)
            st.metric("Total Time", f"{total_time:.2f}s" if total_time > 0 else "N/A")
        
        with col2:
            tools_count = len(tools_called) if tools_called else 0
            st.metric("UC Functions Called", tools_count)
        
        with col3:
            # Get citations count from agent_output
            citations_count = 0
            if st.session_state.get("agent_output"):
                citations = st.session_state.agent_output.get("citations", [])
                citations_count = len(citations)
            st.metric("Citations", citations_count)


def display_agent_progress(member_data, tools_called, show_logs=True):
    """
    Alternative function name for compatibility
    Same signature as render_progress
    """
    render_progress(member_data, tools_called, show_logs)


def show_processing_status(stage, message=None):
    """
    Show real-time processing status (called from agent during execution)
    
    Args:
        stage: Stage name (e.g., 'tool_start', 'synthesis_stage', 'validation_start')
        message: Optional message dict with details
    """
    
    # This function can be enhanced to update a progress placeholder in real-time
    # For now, it's a placeholder for future real-time updates
    pass
