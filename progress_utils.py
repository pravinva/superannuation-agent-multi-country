# progress_utils_ENHANCED.py
"""
Enhanced progress tracking with thin phase cards
Matches the style from your screenshot with detailed phase information
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


def render_privacy_card(original_name, anonymized_name, restored=False):
    """Render privacy protection card"""
    if not restored:
        details = f'Original: "{original_name}" → Anonymized: "{anonymized_name}"<br/><em>Real name will not be sent to Claude API. It will be restored in final response.</em>'
        render_phase_card(
            phase_name="🔒 Privacy Protection Active",
            status="completed",
            details=details,
            icon="🔒"
        )
    else:
        details = f'Anonymized: "{anonymized_name}" → Restored: "{original_name}"'
        render_phase_card(
            phase_name="🔓 Privacy Protection Restored",
            status="completed",
            details=details,
            icon="🔓"
        )


def render_llm_planning_card(estimated_time=None):
    """Render LLM planning phase"""
    if estimated_time:
        details = f"Estimated: {estimated_time} seconds"
    else:
        details = "Calling Claude Opus for query planning..."
    
    render_phase_card(
        phase_name="🤖 Claude Opus 4.1: Query Planning",
        status="running",
        details=details,
        icon="🤖"
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


def render_synthesis_header():
    """Render synthesis section header"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 10px 0;
        font-weight: bold;
    ">
        ✍️ Multi-Stage Synthesis: Generating personalized advice (Estimated: ~45 seconds total)
    </div>
    """, unsafe_allow_html=True)


def render_synthesis_progress_bar(current_stage, total_stages=3):
    """Render progress bar for synthesis"""
    progress = current_stage / total_stages
    st.markdown(f"**Overall Synthesis Progress: Stage {current_stage}/{total_stages}**")
    st.progress(progress)


def render_synthesis_stage_card(stage_num, stage_name, status, duration=None, estimated_tokens=None):
    """Render synthesis stage card"""
    stage_icons = {
        1: "📝",
        2: "🔍",
        3: "💡"
    }
    
    icon = stage_icons.get(stage_num, "📝")
    
    phase_name = f"Stage {stage_num}/3: {stage_name}"
    
    if estimated_tokens:
        details = f"Estimated: {estimated_tokens} tokens"
    else:
        details = None
    
    if status == "completed":
        full_name = f"✅ {phase_name}: Complete"
    else:
        full_name = f"⏳ {phase_name}"
    
    render_phase_card(
        phase_name=full_name,
        status=status,
        details=details,
        duration=duration,
        icon=icon
    )


def render_validation_card(validation_mode, verdict, confidence=None, violations=None, attempts=1):
    """Render validation phase card"""
    mode_display = validation_mode.replace('_', ' ').title()
    
    if verdict == "Pass":
        status = "completed"
        if confidence:
            details = f"Mode: {mode_display} • Confidence: {confidence:.0%} • Attempts: {attempts}"
        else:
            details = f"Mode: {mode_display} • Attempts: {attempts}"
    else:
        status = "error" if verdict == "ERROR" else "running"
        if violations:
            details = f"Mode: {mode_display} • Violations: {violations} • Needs review"
        else:
            details = f"Mode: {mode_display} • Needs review"
    
    render_phase_card(
        phase_name="⚖️ Judge Validation",
        status=status,
        details=details,
        icon="⚖️"
    )


def render_retry_card(attempt_num, violations_count):
    """Render retry notification card"""
    render_phase_card(
        phase_name=f"🔄 Retry Attempt {attempt_num}",
        status="running",
        details=f"Correcting {violations_count} compliance issue(s) with structured feedback",
        icon="🔄"
    )


def render_audit_card(session_id):
    """Render audit logging card"""
    render_phase_card(
        phase_name="📝 Logged to Governance Table",
        status="completed",
        details=f"Session: {session_id[:12]}... | Stored in super_advisory_demo.member_data.governance",
        icon="📝"
    )


def render_progress_with_cards(member_data=None, tools_called=None, synthesis_stages=None, 
                               validation_result=None, show_logs=True):
    """
    Enhanced progress display with thin cards for each phase
    
    Args:
        member_data: Member profile dict
        tools_called: List of tools executed [{name, authority, status, duration}, ...]
        synthesis_stages: List of synthesis stages [{stage_num, stage_name, status, duration}, ...]
        validation_result: Validation result dict
        show_logs: Whether to show logs
    """
    
    if not show_logs:
        return
    
    st.markdown("### 📋 Agent Processing Logs")
    
    # Check if there's agent output
    if "agent_output" not in st.session_state or not st.session_state.agent_output:
        st.info("🔄 Agent processing logs will appear here...")
        st.caption("No processing has occurred yet. Click '🚀 Get Recommendation' to start.")
        return
    
    output = st.session_state.agent_output
    
    # Overall status
    st.success("✅ Processing complete!")
    
    # Estimated time
    if "estimated_time" in output:
        st.info(f"⏱️ **Estimated Processing Time:** {output['estimated_time']}")
    
    # Create expandable section
    with st.expander("📊 Detailed Processing Phases", expanded=True):
        
        # PHASE 0: Data Retrieval
        if member_data:
            render_data_retrieval_card(member_data)
        
        # PHASE 0.5: Temperature Setting (if shown)
        if output.get("temperature"):
            render_phase_card(
                phase_name="🌡️ Temperature Setting",
                status="completed",
                details=f"Temperature: {output['temperature']}",
                icon="🌡️"
            )
        
        # PHASE 0.75: Privacy (if anonymized)
        if output.get("was_anonymized"):
            original_name = output.get("original_name", "")
            anonymized_name = output.get("anonymized_name", "")
            render_privacy_card(original_name, anonymized_name, restored=False)
        
        # PHASE 0.9: Validation Setting
        if output.get("validation_mode"):
            validation_mode_display = output['validation_mode'].replace('_', ' ').title()
            render_phase_card(
                phase_name="⚖️ Validation Mode",
                status="completed",
                details=f"Using {validation_mode_display} validation with Claude Sonnet 4",
                icon="⚖️"
            )
        
        # PHASE 1: LLM Planning (if shown)
        if output.get("show_planning"):
            render_llm_planning_card(estimated_time="3-5")
        
        # PHASE 2: Tool Execution
        if tools_called and len(tools_called) > 0:
            for tool in tools_called:
                render_tool_execution_card(
                    tool_name=tool.get('name', 'Unknown Tool'),
                    authority=tool.get('authority', ''),
                    status=tool.get('status', 'completed'),
                    duration=tool.get('duration'),
                    details=tool.get('details')
                )
        
        # PHASE 3: Multi-Stage Synthesis
        if synthesis_stages and len(synthesis_stages) > 0:
            render_synthesis_header()
            
            # Progress bar
            current_stage = max([s.get('stage_num', 1) for s in synthesis_stages])
            render_synthesis_progress_bar(current_stage, total_stages=3)
            
            # Individual stage cards
            for stage in synthesis_stages:
                render_synthesis_stage_card(
                    stage_num=stage.get('stage_num', 1),
                    stage_name=stage.get('stage_name', 'Processing'),
                    status=stage.get('status', 'completed'),
                    duration=stage.get('duration'),
                    estimated_tokens=stage.get('estimated_tokens')
                )
        
        # PHASE 4: Validation
        if validation_result:
            render_validation_card(
                validation_mode=validation_result.get('mode', 'llm_judge'),
                verdict=validation_result.get('verdict', 'Pass'),
                confidence=validation_result.get('confidence'),
                violations=len(validation_result.get('violations', [])),
                attempts=validation_result.get('attempts', 1)
            )
            
            # Show retries if any
            if validation_result.get('attempts', 1) > 1:
                for attempt in range(2, validation_result.get('attempts', 1) + 1):
                    render_retry_card(attempt, len(validation_result.get('violations', [])))
        
        # PHASE 5: Privacy Restoration (if anonymized)
        if output.get("was_anonymized") and output.get("name_restored"):
            original_name = output.get("original_name", "")
            anonymized_name = output.get("anonymized_name", "")
            render_privacy_card(original_name, anonymized_name, restored=True)
        
        # PHASE 6: Audit Logging
        session_id = st.session_state.get("session_id", "unknown")
        render_audit_card(session_id)
        
        # Summary Metrics Section
        st.markdown("---")
        st.markdown("**📊 Summary Metrics**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_time = output.get("total_time", 0)
            st.metric("Total Time", f"{total_time:.2f}s")
        
        with col2:
            tools_count = len(tools_called) if tools_called else 0
            st.metric("Tools Called", tools_count)
        
        with col3:
            citations_count = len(output.get("citations", []))
            st.metric("Citations", citations_count)
        
        with col4:
            validation_attempts = validation_result.get('attempts', 1) if validation_result else 1
            st.metric("Validation Attempts", validation_attempts)


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
