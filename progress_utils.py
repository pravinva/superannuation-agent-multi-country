# progress_utils.py - COMPLETE VERSION
"""
Progress and logging utilities for displaying agent execution details
"""

import streamlit as st


def render_progress(agent_output):
    """
    Render agent progress and execution details
    
    Args:
        agent_output: Dict containing agent execution metadata including:
            - _tools_called: List of tools/functions called
            - _validation: Validation results
            - timings: Execution timings
            - member_data: Member profile data
    """
    
    if not agent_output:
        return
    
    st.markdown("---")
    st.markdown("## 🔍 Execution Details")
    
    # Show tools called
    tools_called = agent_output.get('_tools_called', [])
    if tools_called:
        st.markdown("### ⚙️ UC Functions Executed")
        
        for i, tool in enumerate(tools_called, 1):
            tool_name = tool.get('name', 'Unknown Tool')
            duration = tool.get('duration', 0)
            status = tool.get('status', 'completed')
            authority = tool.get('authority', '')
            uc_function = tool.get('uc_function', '')
            
            # Status icon
            status_icon = "✅" if status == "completed" else "⚠️"
            
            # Color coding
            colors = {
                1: "#3498db",  # Blue
                2: "#2ecc71",  # Green
                3: "#9b59b6"   # Purple
            }
            color = colors.get(i, "#95a5a6")
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="
                        border-left: 4px solid {color};
                        background: #f8f9fa;
                        padding: 12px 16px;
                        margin: 8px 0;
                        border-radius: 4px;
                    ">
                        <div style="font-weight: 600; color: #2c3e50; margin-bottom: 4px;">
                            {status_icon} {i}. {tool_name}
                        </div>
                        <div style="font-size: 0.85em; color: #7f8c8d;">
                            {f'Authority: {authority}' if authority else 'Regulatory Calculator'}
                        </div>
                        {f'<div style="font-size: 0.75em; color: #95a5a6; margin-top: 4px; font-family: monospace;">{uc_function}</div>' if uc_function else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.metric("Duration", f"{duration:.2f}s")
    
    # Show validation results
    validation = agent_output.get('_validation', {})
    if validation:
        st.markdown("### ⚖️ Validation Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            passed = validation.get('passed', False)
            if passed:
                st.success("✅ Passed")
            else:
                st.warning("⚠️ Review Needed")
        
        with col2:
            confidence = validation.get('confidence', 0.0)
            st.metric("Confidence", f"{confidence*100:.0f}%")
        
        with col3:
            violations = validation.get('violations', [])
            st.metric("Violations", len(violations))
        
        # Show violations if any
        if violations:
            with st.expander("⚠️ View Violations", expanded=False):
                for v in violations:
                    severity = v.get('severity', 'UNKNOWN')
                    code = v.get('code', 'N/A')
                    detail = v.get('detail', 'No details')
                    
                    if severity == 'CRITICAL':
                        st.error(f"**{code}:** {detail}")
                    elif severity == 'MEDIUM':
                        st.warning(f"**{code}:** {detail}")
                    else:
                        st.info(f"**{code}:** {detail}")
    
    # Show timings
    timings = agent_output.get('timings', {})
    if timings:
        st.markdown("### ⏱️ Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total = timings.get('total', 0)
            st.metric("Total Time", f"{total:.2f}s")
        
        with col2:
            tool_time = timings.get('tool', 0)
            st.metric("UC Functions", f"{tool_time:.2f}s")
        
        with col3:
            synthesis = timings.get('synthesis', 0)
            st.metric("LLM Synthesis", f"{synthesis:.2f}s")


def display_agent_progress(agent_output, show_logs=True):
    """
    Alternative function name for compatibility
    Same as render_progress but with show_logs parameter
    
    Args:
        agent_output: Dict containing agent execution metadata
        show_logs: Whether to show logs (default: True)
    """
    if show_logs:
        render_progress(agent_output)


def render_tools_called_cards(tools_called):
    """
    Render individual cards for each tool called
    
    Args:
        tools_called: List of tool execution dicts
    """
    
    if not tools_called:
        st.info("No tools were called for this query.")
        return
    
    st.markdown(f"### 🔧 {len(tools_called)} UC Functions Called")
    
    for i, tool in enumerate(tools_called, 1):
        tool_name = tool.get('name', 'Unknown Tool')
        duration = tool.get('duration', 0)
        status = tool.get('status', 'completed')
        authority = tool.get('authority', 'Authority')
        regulation = tool.get('regulation', '')
        uc_function = tool.get('uc_function', '')
        
        # Determine color based on index
        colors = ["#3498db", "#2ecc71", "#9b59b6", "#e74c3c", "#f39c12"]
        color = colors[(i-1) % len(colors)]
        
        # Status styling
        if status == "completed":
            status_badge = "✅ Completed"
            status_color = "#2ecc71"
        elif status == "error":
            status_badge = "❌ Error"
            status_color = "#e74c3c"
        else:
            status_badge = "⏳ Pending"
            status_color = "#f39c12"
        
        # Render card
        st.markdown(f"""
        <div style="
            border: 2px solid {color};
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            background: linear-gradient(135deg, {color}08 0%, {color}15 100%);
        ">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="font-size: 1.1em; font-weight: 600; color: {color}; margin-bottom: 8px;">
                        {i}. {tool_name}
                    </div>
                    <div style="font-size: 0.9em; color: #555; margin-bottom: 4px;">
                        <strong>Authority:</strong> {authority}
                    </div>
                    {f'<div style="font-size: 0.85em; color: #777; margin-bottom: 8px;"><strong>Regulation:</strong> {regulation}</div>' if regulation else ''}
                    {f'<div style="font-size: 0.75em; color: #999; font-family: monospace; margin-top: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px;">{uc_function}</div>' if uc_function else ''}
                </div>
                <div style="text-align: right; margin-left: 16px;">
                    <div style="
                        background: {status_color}20;
                        color: {status_color};
                        padding: 6px 12px;
                        border-radius: 6px;
                        font-size: 0.85em;
                        font-weight: 600;
                        margin-bottom: 8px;
                    ">
                        {status_badge}
                    </div>
                    <div style="font-size: 1.2em; font-weight: 600; color: #333;">
                        {duration:.2f}s
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_validation_summary(validation_result):
    """
    Render validation summary in a clean format
    
    Args:
        validation_result: Dict with validation results
    """
    
    if not validation_result:
        return
    
    st.markdown("### ⚖️ Compliance Validation")
    
    passed = validation_result.get('passed', False)
    confidence = validation_result.get('confidence', 0.0)
    violations = validation_result.get('violations', [])
    reasoning = validation_result.get('reasoning', 'No reasoning provided')
    
    # Header row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if passed:
            st.success("✅ **PASSED**")
        else:
            st.error("❌ **FAILED**")
    
    with col2:
        st.metric("Confidence", f"{confidence*100:.0f}%", 
                 help="Judge's confidence in the validation decision")
    
    with col3:
        critical_count = len([v for v in violations if v.get('severity') == 'CRITICAL'])
        st.metric("Critical Issues", critical_count,
                 help="Number of critical compliance violations")
    
    # Reasoning
    if reasoning:
        with st.expander("📋 Validation Reasoning", expanded=True):
            st.info(reasoning)
    
    # Violations detail
    if violations:
        with st.expander(f"⚠️ {len(violations)} Violation(s) Found", expanded=not passed):
            for i, violation in enumerate(violations, 1):
                severity = violation.get('severity', 'UNKNOWN')
                code = violation.get('code', 'N/A')
                detail = violation.get('detail', 'No details')
                evidence = violation.get('evidence', '')
                
                # Color coding by severity
                if severity == 'CRITICAL':
                    icon = "🔴"
                    color = "#e74c3c"
                elif severity == 'MEDIUM':
                    icon = "🟡"
                    color = "#f39c12"
                else:
                    icon = "🔵"
                    color = "#3498db"
                
                st.markdown(f"""
                <div style="
                    border-left: 4px solid {color};
                    background: {color}10;
                    padding: 12px;
                    margin: 8px 0;
                    border-radius: 4px;
                ">
                    <div style="font-weight: 600; color: {color};">
                        {icon} {i}. {code} - {severity}
                    </div>
                    <div style="margin-top: 8px; color: #333;">
                        {detail}
                    </div>
                    {f'<div style="margin-top: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px; font-family: monospace; font-size: 0.85em; color: #666;"><strong>Evidence:</strong> {evidence}</div>' if evidence else ''}
                </div>
                """, unsafe_allow_html=True)


def format_execution_time(seconds):
    """
    Format execution time in human-readable format
    
    Args:
        seconds: Time in seconds (float)
    
    Returns:
        Formatted string (e.g., "2.5s", "1m 30s", "2h 15m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
