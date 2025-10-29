#!/usr/bin/env python3
# progress_utils.py – FIXED VERSION with EXPANDER DROPDOWN
# ✅ Single dropdown that doesn't repeat
# ✅ Phases shown only once in collapsible expander
# ✅ Real-time updates as phases progress
# ✅ Clean layout with no duplication

import streamlit as st
from datetime import datetime

def initialize_live_progress_tracker():
    """Initialize the 8-phase progress tracker in session state"""
    if 'phases' not in st.session_state:
        st.session_state.phases = {
            'phase_1_retrieval': {'status': 'pending', 'start': None, 'duration': None},
            'phase_2_anonymization': {'status': 'pending', 'start': None, 'duration': None},
            'phase_3_planning': {'status': 'pending', 'start': None, 'duration': None},
            'phase_4_execution': {'status': 'pending', 'start': None, 'duration': None},
            'phase_5_synthesis': {'status': 'pending', 'start': None, 'duration': None},
            'phase_6_validation': {'status': 'pending', 'start': None, 'duration': None},
            'phase_7_restoration': {'status': 'pending', 'start': None, 'duration': None},
            'phase_8_logging': {'status': 'pending', 'start': None, 'duration': None},
        }
    
    if 'progress_placeholder' not in st.session_state:
        # Create a single placeholder that won't repeat
        st.session_state.progress_placeholder = st.empty()
        st.session_state.progress_initialized = True


def mark_phase_running(phase_key):
    """Mark a phase as currently running"""
    if 'phases' not in st.session_state:
        initialize_live_progress_tracker()
    
    if phase_key in st.session_state.phases:
        st.session_state.phases[phase_key]['status'] = 'running'
        st.session_state.phases[phase_key]['start'] = datetime.now()
        _update_progress_display()


def mark_phase_complete(phase_key, duration=None):
    """Mark a phase as completed with optional manual duration"""
    if 'phases' not in st.session_state:
        initialize_live_progress_tracker()
    
    if phase_key in st.session_state.phases:
        phase = st.session_state.phases[phase_key]
        phase['status'] = 'completed'
        
        # Use manual duration if provided, otherwise calculate from start time
        if duration is not None:
            phase['duration'] = duration
        elif phase['start']:
            phase['duration'] = (datetime.now() - phase['start']).total_seconds()
        
        _update_progress_display()


def mark_phase_error(phase_key, error_msg=None):
    """Mark a phase as errored"""
    if 'phases' not in st.session_state:
        initialize_live_progress_tracker()
    
    if phase_key in st.session_state.phases:
        phase = st.session_state.phases[phase_key]
        phase['status'] = 'error'
        if phase['start']:
            phase['duration'] = (datetime.now() - phase['start']).total_seconds()
        phase['error'] = error_msg
        _update_progress_display()


def _update_progress_display():
    """Update the progress display with current phase statuses - SINGLE EXPANDER"""
    if 'progress_placeholder' not in st.session_state:
        return
    
    # Build content for the expander
    expander_content = []
    
    phases_display = [
        ('phase_1_retrieval', '🔍 Phase 1: Data Retrieval', 'Loading member profile from Unity Catalog...'),
        ('phase_2_anonymization', '🔒 Phase 2: Privacy Anonymization', 'Processing data anonymization...'),
        ('phase_3_planning', '🧠 Phase 3: Tool Planning', 'Planning which tools to use...'),
        ('phase_4_execution', '⚙️ Phase 4: Tool Execution', 'Executing tools and calculations...'),
        ('phase_5_synthesis', '✏️ Phase 5: Response Synthesis', 'Generating AI response...'),
        ('phase_6_validation', '⚖️ Phase 6: LLM Validation', 'Validating response quality...'),
        ('phase_7_restoration', '🔓 Phase 7: Name Restoration', 'Restoring member names...'),
        ('phase_8_logging', '📝 Phase 8: Audit Logging', 'Logging to MLflow and governance table...'),
    ]
    
    # Build HTML for all phases
    phases_html = ""
    for phase_key, phase_title, phase_detail in phases_display:
        if phase_key in st.session_state.phases:
            phase_data = st.session_state.phases[phase_key]
            status = phase_data['status']
            duration = phase_data.get('duration')
            
            card_html = _render_phase_card_html(phase_title, status, phase_detail, duration)
            phases_html += card_html
    
    # Update the placeholder with expander
    with st.session_state.progress_placeholder.container():
        with st.expander("🔎 Processing Pipeline Phases", expanded=False):
            st.markdown("### 📊 Pipeline Progress")
            st.markdown(phases_html, unsafe_allow_html=True)


def _render_phase_card_html(phase_name, status, details=None, duration=None):
    """Render a single phase card as HTML - no duplicates"""
    
    if status == "completed":
        bg_color = "#d4edda"
        border_color = "#28a745"
        status_icon = "✅"
        status_text = "Completed"
    elif status == "error":
        bg_color = "#f8d7da"
        border_color = "#dc3545"
        status_icon = "❌"
        status_text = "Error"
    elif status == "running":
        bg_color = "#fff3cd"
        border_color = "#ffc107"
        status_icon = "🔄"
        status_text = "Running"
    else:  # pending
        bg_color = "#e7f3ff"
        border_color = "#0066cc"
        status_icon = "⏳"
        status_text = "Pending"
    
    duration_text = f" → {duration:.2f}s" if duration else ""
    details_html = f"<br/><small>{details}</small>" if details else ""
    
    card_html = f"""
<div style="
    background-color: {bg_color};
    border-left: 4px solid {border_color};
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 4px;
    font-family: monospace;
">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <span><strong>{status_icon} {phase_name}</strong></span>
        <span style="color: {border_color}; font-weight: bold;">{status_text}{duration_text}</span>
    </div>
    {details_html}
</div>
"""
    return card_html


def render_phase_card(phase_name, status, details=None, duration=None, icon="🔄"):
    """Backward compatibility - this function is deprecated, use _render_phase_card_html instead"""
    # This is kept for backward compatibility but not used in the new flow
    pass


# ============================================================================
# KEY IMPROVEMENTS:
# ============================================================================
#
# ✅ SINGLE EXPANDER: All phases in one collapsible dropdown
# ✅ NO REPEATING: Uses st.session_state.progress_placeholder.container() only
# ✅ NO DUPLICATION: Only calls _update_progress_display() from mark_phase_* functions
# ✅ REAL-TIME: Updates in-place as phases progress
# ✅ CLEAN: No extra logging or console output from progress tracking
#
# ============================================================================
