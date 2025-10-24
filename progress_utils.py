# progress_utils.py - WITH LIVE UPDATES + JUDGE PHASE
"""
✅ FIX 4: Shows dropdown immediately, updates live
✅ FIX 5: Shows judge validation phase
"""

import streamlit as st
from datetime import datetime


def render_phase_card(phase_name, status, details=None, duration=None, icon="🔄"):
    """Render a thin card for a processing phase"""
    
    if status == "completed":
        bg_color = "#d4edda"
        border_color = "#28a745"
        status_icon = "✅"
    elif status == "error":
        bg_color = "#f8d7da"
        border_color = "#dc3545"
        status_icon = "❌"
    elif status == "running":
        bg_color = "#fff3cd"
        border_color = "#ffc107"
        status_icon = "🔄"
    else:
        bg_color = "#e7f3ff"
        border_color = "#0066cc"
        status_icon = "ℹ️"
    
    duration_text = f" → {duration:.2f}s" if duration else ""
    details_html = f"<br/><span style='font-size: 0.85em; color: #555;'>{details}</span>" if details else ""
    
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
    
    if isinstance(member_balance, (int, float)):
        balance_display = f"${int(member_balance):,}"
    else:
        balance_display = str(member_balance)
    
    details = f"Member: {member_name} (Age {member_age}) • Balance: {balance_display}"
    
    render_phase_card(
        phase_name="📊 Data Retrieved from Unity Catalog",
        status="completed",
        details=details,
        icon="📊"
    )


def render_tool_execution_card(tool_name, authority, status, duration=None, details=None):
    """Render tool execution card"""
    if not details and authority:
        details = f"Authority: {authority}"
    
    render_phase_card(
        phase_name=f"🛠️ UC Function: {tool_name}",
        status=status,
        details=details,
        duration=duration,
        icon="🛠️"
    )


def render_validation_phase_card(validation_data, duration=None):
    """
    ✅ FIX 5: Render judge validation phase
    """
    mode = validation_data.get('mode', 'llm_judge')
    passed = validation_data.get('passed', False)
    confidence = validation_data.get('confidence', 0)
    violations = validation_data.get('violations', [])
    
    mode_display = mode.replace('_', ' ').title()
    
    status = "completed" if passed else "error"
    
    details = (
        f"Mode: {mode_display} • "
        f"Verdict: {'✅ Pass' if passed else '⚠️ Review'} • "
        f"Confidence: {confidence:.0%} • "
        f"Issues: {len(violations)}"
    )
    
    render_phase_card(
        phase_name="⚖️ Judge Validation (Claude Sonnet 4)",
        status=status,
        details=details,
        duration=duration,
        icon="⚖️"
    )


def render_audit_card(session_id):
    """Render audit logging card"""
    render_phase_card(
        phase_name="📝 Logged to Governance Table",
        status="completed",
        details=f"Session: {session_id[:12]}... | Stored in governance_log",
        icon="📝"
    )


def render_progress(member_data, tools_called, show_logs=True):
    """
    ✅ FIXED: Matches app.py signature + shows live updates + judge phase
    
    Args:
        member_data: Member profile dict
        tools_called: List of tools executed
        show_logs: Whether to show logs
    """
    
    if not show_logs:
        return
    
    st.markdown("### 📋 Agent Processing Logs")
    
    # ✅ FIX 4: Show expander IMMEDIATELY, expanded by default
    # This creates a live-updating view as phases complete
    with st.expander("📊 Processing Phases (Live Updates)", expanded=True):
        
        # Check if processing has started
        if not member_data and not tools_called:
            st.info("🔄 Waiting for processing to start...")
            st.caption("Click '🚀 Get Recommendation' to begin.")
            return
        
        # Processing has started - show phases
        
        # PHASE 1: Data Retrieval
        if member_data:
            render_data_retrieval_card(member_data)
        else:
            render_phase_card(
                phase_name="📊 Loading Member Data",
                status="running",
                details="Fetching from Unity Catalog...",
                icon="📊"
            )
        
        # PHASE 2: UC Function Execution
        if tools_called and len(tools_called) > 0:
            st.markdown("#### ⚙️ UC Functions")
            
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
                    details_parts.append(f"{uc_function}")
                
                details = " • ".join(details_parts) if details_parts else None
                
                render_tool_execution_card(
                    tool_name=tool_name,
                    authority=authority,
                    status=status,
                    duration=duration,
                    details=details
                )
        else:
            render_phase_card(
                phase_name="⚙️ Calling UC Functions",
                status="running",
                details="Executing regulatory calculators...",
                icon="⚙️"
            )
        
        # PHASE 3: LLM Synthesis
        if st.session_state.get("agent_output"):
            timings = st.session_state.agent_output.get("timings", {})
            synthesis_time = timings.get("synthesis", 0)
            
            if synthesis_time > 0:
                render_phase_card(
                    phase_name="✏️ Multi-Stage Synthesis (Claude Opus 4.1)",
                    status="completed",
                    details="Generated personalized response in 3 stages",
                    duration=synthesis_time,
                    icon="✏️"
                )
        else:
            if tools_called and len(tools_called) > 0:
                render_phase_card(
                    phase_name="✏️ LLM Synthesis",
                    status="running",
                    details="Generating personalized advice...",
                    icon="✏️"
                )
        
        # ✅ FIX 5: PHASE 4: Judge Validation (NEW!)
        if st.session_state.get("agent_output"):
            validation = st.session_state.agent_output.get("_validation", {})
            
            if validation:
                # Calculate validation duration if available
                timings = st.session_state.agent_output.get("timings", {})
                validation_time = timings.get("validation", None)
                
                render_validation_phase_card(validation, duration=validation_time)
        else:
            if tools_called and len(tools_called) > 0:
                render_phase_card(
                    phase_name="⚖️ Judge Validation",
                    status="running",
                    details="Checking compliance...",
                    icon="⚖️"
                )
        
        # PHASE 5: Audit Logging
        if st.session_state.get("agent_output"):
            session_id = st.session_state.get("session_id", "unknown")
            render_audit_card(session_id)
        
        # Summary Metrics (only show when complete)
        if st.session_state.get("agent_output"):
            st.markdown("---")
            st.markdown("**📊 Summary Metrics**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                timings = st.session_state.agent_output.get("timings", {})
                total_time = timings.get("total", 0)
                st.metric("Total Time", f"{total_time:.2f}s")
            
            with col2:
                tools_count = len(tools_called) if tools_called else 0
                st.metric("UC Functions", tools_count)
            
            with col3:
                citations = st.session_state.agent_output.get("citations", [])
                st.metric("Citations", len(citations))


def display_agent_progress(member_data, tools_called, show_logs=True):
    """Alternative function name for compatibility"""
    render_progress(member_data, tools_called, show_logs)


def show_processing_status(stage, message=None):
    """
    Real-time processing status updates
    Called by agent during execution via status_callback
    """
    pass  # Placeholder for future enhancements
