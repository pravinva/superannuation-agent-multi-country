#!/usr/bin/env python3
"""
Progress Tracking Utilities - Enhanced UI

Beautiful progress tracking for the 8-phase agent pipeline:
- Real-time progress bar
- Color-coded phase status
- Professional fonts and styling
- Estimated time remaining
- Clean, modern design
"""

from datetime import datetime
from typing import Dict, Optional
from shared.logging_config import get_logger

# Conditional streamlit import for testing compatibility
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    # Mock streamlit for testing environments
    from unittest.mock import MagicMock
    st = MagicMock()
    STREAMLIT_AVAILABLE = False

logger = get_logger(__name__)

# ============================================================================
# PHASE CONFIGURATION
# ============================================================================

PHASES = [
    {
        'key': 'phase_1_retrieval',
        'icon': '🔍',
        'title': 'Data Retrieval',
        'description': 'Loading member profile from Unity Catalog',
        'weight': 5  # for progress bar calculation
    },
    {
        'key': 'phase_2_anonymization',
        'icon': '🔒',
        'title': 'Privacy Anonymization',
        'description': 'Processing PII protection',
        'weight': 5
    },
    {
        'key': 'phase_3_classification',
        'icon': '🎯',
        'title': 'Query Classification',
        'description': '3-stage cascade (Regex→Embedding→LLM)',
        'weight': 10
    },
    {
        'key': 'phase_4_planning',
        'icon': '🧠',
        'title': 'Tool Planning',
        'description': 'ReAct: Selecting appropriate tools',
        'weight': 10
    },
    {
        'key': 'phase_5_execution',
        'icon': '⚙️',
        'title': 'Tool Execution',
        'description': 'Running SQL functions in Unity Catalog',
        'weight': 25
    },
    {
        'key': 'phase_6_synthesis',
        'icon': '✏️',
        'title': 'Response Synthesis',
        'description': 'Generating personalized advice with LLM',
        'weight': 30
    },
    {
        'key': 'phase_7_validation',
        'icon': '⚖️',
        'title': 'Quality Validation',
        'description': 'LLM-as-a-Judge quality check',
        'weight': 10
    },
    {
        'key': 'phase_8_logging',
        'icon': '📝',
        'title': 'Audit Logging',
        'description': 'Logging to MLflow and governance table',
        'weight': 5
    }
]


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_progress_tracker():
    """Initialize the progress tracker in session state."""
    # ✅ Always initialize phases (they persist until next question)
    if 'phases' not in st.session_state:
        st.session_state.phases = {}
        for phase in PHASES:
            st.session_state.phases[phase['key']] = {
                'status': 'pending',
                'start': None,
                'duration': None,
                'error': None
            }
    
    # ✅ Always create placeholder (needed for toggle functionality)
    if 'progress_placeholder' not in st.session_state:
        st.session_state.progress_placeholder = st.empty()
        st.session_state.progress_initialized = True
    
    # ✅ Note: Don't render here - let caller control when to render
    # This prevents double rendering when called from app.py


def reset_progress_tracker():
    """
    Reset the progress tracker for a new query.
    
    ⚠️ CRITICAL: Call this BEFORE each new query to prevent:
    - Stale progress from previous run
    - UI freezing/hanging
    - Opaque screen issues
    """
    # Clear all phase statuses back to pending
    if 'phases' in st.session_state:
        for phase in PHASES:
            st.session_state.phases[phase['key']] = {
                'status': 'pending',
                'start': None,
                'duration': None,
                'error': None
            }
    
    # Clear the progress placeholder to prevent stale UI
    if 'progress_placeholder' in st.session_state:
        st.session_state.progress_placeholder.empty()
    
    # Reinitialize fresh placeholder
    st.session_state.progress_placeholder = st.empty()
    st.session_state.progress_initialized = True


# ============================================================================
# PHASE STATUS UPDATES
# ============================================================================

def mark_phase_running(phase_key: str):
    """Mark a phase as currently running."""
    # ✅ CRITICAL: Never let UI tracking affect agent execution - wrap in try/except
    try:
        # ✅ CRITICAL: Always track phases (even if expander is closed)
        # This allows user to open expander later and see progress
        if 'phases' not in st.session_state:
            initialize_progress_tracker()
        
        if phase_key in st.session_state.phases:
            st.session_state.phases[phase_key]['status'] = 'running'
            st.session_state.phases[phase_key]['start'] = datetime.now()
            
            # ✅ CRITICAL: Update UI immediately if progress placeholder exists
            # This ensures real-time updates during execution
            if 'progress_placeholder' in st.session_state:
                try:
                    _update_progress_display()
                except:
                    pass
    except Exception:
        # Silently fail - UI tracking should NEVER stop agent execution
        pass


def mark_phase_complete(phase_key: str, duration: Optional[float] = None):
    """Mark a phase as completed."""
    # ✅ CRITICAL: Never let UI tracking affect agent execution - wrap in try/except
    try:
        # ✅ CRITICAL: Always track phases (even if expander is closed)
        # This allows user to open expander later and see progress
        if 'phases' not in st.session_state:
            initialize_progress_tracker()
        
        if phase_key in st.session_state.phases:
            phase = st.session_state.phases[phase_key]
            phase['status'] = 'completed'
            
            if duration is not None:
                phase['duration'] = duration
            elif phase['start']:
                phase['duration'] = (datetime.now() - phase['start']).total_seconds()
            
            # ✅ CRITICAL: Update UI immediately if progress placeholder exists
            # This ensures real-time updates during execution
            if 'progress_placeholder' in st.session_state:
                try:
                    _update_progress_display()
                except:
                    pass
    except Exception:
        # Silently fail - UI tracking should NEVER stop agent execution
        pass


def mark_phase_error(phase_key: str, error_msg: Optional[str] = None):
    """Mark a phase as errored."""
    # ✅ CRITICAL: Never let UI tracking affect agent execution - wrap in try/except
    try:
        # ✅ CRITICAL: Always track phases (even if expander is closed)
        # This allows user to open expander later and see progress
        if 'phases' not in st.session_state:
            initialize_progress_tracker()
        
        if phase_key in st.session_state.phases:
            phase = st.session_state.phases[phase_key]
            phase['status'] = 'error'
            if phase['start']:
                phase['duration'] = (datetime.now() - phase['start']).total_seconds()
            phase['error'] = error_msg
            
            # ✅ CRITICAL: Update UI immediately if progress placeholder exists
            # This ensures real-time updates during execution
            if 'progress_placeholder' in st.session_state:
                try:
                    _update_progress_display()
                except:
                    pass
    except Exception:
        # Silently fail - UI tracking should NEVER stop agent execution
        pass


# ============================================================================
# PROGRESS CALCULATION
# ============================================================================

def _calculate_progress() -> Dict:
    """Calculate overall progress percentage."""
    if 'phases' not in st.session_state:
        return {'percent': 0, 'completed_weight': 0, 'total_weight': 0}
    
    # ✅ CRITICAL: Read directly from session_state (not cached)
    phases = st.session_state.phases
    completed_weight = 0
    total_weight = 0
    
    for phase in PHASES:
        weight = phase.get('weight', 1)
        total_weight += weight
        
        phase_key = phase['key']
        phase_data = phases.get(phase_key, {})
        status = phase_data.get('status', 'pending')
        
        if status == 'completed':
            completed_weight += weight
        elif status == 'running':
            # Count running phases as 50% complete
            completed_weight += weight * 0.5
    
    percent = int((completed_weight / total_weight * 100)) if total_weight > 0 else 0
    
    return {
        'percent': percent,
        'completed_weight': completed_weight,
        'total_weight': total_weight
    }


# ============================================================================
# DISPLAY RENDERING
# ============================================================================

def render_progress_fragment():
    """
    Render progress display into placeholder.
    Simple direct rendering - no fragments needed.
    Updates happen via _update_progress_display() called from mark_phase_* functions.
    """
    # ✅ CRITICAL: Check if logs should be shown (checkbox state)
    if not st.session_state.get('show_processing_logs', False):
        return  # Don't render if checkbox is unchecked
    
    # ✅ CRITICAL: Always read fresh from session_state
    try:
        # Ensure we have phases
        if 'phases' not in st.session_state or len(st.session_state.phases) == 0:
            return
        
        # ✅ CRITICAL: Ensure placeholder exists
        if 'progress_placeholder' not in st.session_state:
            st.session_state.progress_placeholder = st.empty()
        
        # ✅ CRITICAL: Read phases directly from session_state (not cached)
        phases = st.session_state.phases.copy()  # Copy to ensure we have latest
        
        # Render the progress tracker into placeholder
        with st.session_state.progress_placeholder.container():
            # ✅ Add CSS for pulse animation
            st.markdown('<style>@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }</style>', unsafe_allow_html=True)
            
            # Render the progress tracker
            progress = _calculate_progress()
            
            # Progress header - Build as single-line HTML to prevent escaping
            progress_pct = progress['percent']
            progress_html = f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;"><h3 style="color: white; margin: 0; font-weight: 600; font-size: 20px;">🚀 Agent Processing Pipeline</h3><span style="color: white; font-size: 24px; font-weight: 700;">{progress_pct}%</span></div><div style="background: rgba(255,255,255,0.2); height: 24px; border-radius: 12px; overflow: hidden;"><div style="background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%); height: 100%; width: {progress_pct}%; transition: width 0.5s ease; border-radius: 12px; box-shadow: 0 2px 4px rgba(255,215,0,0.4);"></div></div></div>'
            
            st.markdown(progress_html, unsafe_allow_html=True)
            
            # Phase cards - read directly from session_state.phases
            for phase in PHASES:
                phase_key = phase['key']
                phase_data = phases.get(phase_key, {})
                status = phase_data.get('status', 'pending')
                duration = phase_data.get('duration')
                _render_phase_card_streamlit(
                    icon=phase['icon'],
                    title=phase['title'],
                    description=phase['description'],
                    status=status,
                    duration=duration
                )
    except Exception as e:
        # Silent fail - never let UI updates break agent execution
        # Log to console for debugging
        import traceback
        logger.error(f"⚠️ Fragment render error: {e}")
        pass


def _update_progress_display():
    """Update the progress display with enhanced styling."""
    # ✅ CRITICAL: Never let UI updates affect agent execution
    # Wrap entire function in try/except to ensure it never breaks anything
    try:
        # ✅ CRITICAL: Check if logs should be shown (checkbox state)
        if not st.session_state.get('show_processing_logs', False):
            return  # Don't update if checkbox is unchecked
        
        # ✅ CRITICAL: Ensure we have phases before rendering
        if 'phases' not in st.session_state or len(st.session_state.phases) == 0:
            # Phases don't exist yet - nothing to render
            return
        
        # ✅ CRITICAL: Ensure placeholder exists (created in app.py)
        if 'progress_placeholder' not in st.session_state:
            return  # Placeholder not created yet
        
        # ✅ CRITICAL: Don't recreate placeholder - use existing one
        # Recreating causes UI issues during blocking operations
        placeholder = st.session_state.progress_placeholder
        
        # Render the progress tracker into existing placeholder
        with placeholder.container():
            # ✅ Add CSS for pulse animation
            st.markdown('<style>@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }</style>', unsafe_allow_html=True)
            
            # Render the progress tracker
            progress = _calculate_progress()
            
            # Progress header - Build as single-line HTML to prevent escaping
            progress_pct = progress['percent']
            progress_html = f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;"><h3 style="color: white; margin: 0; font-weight: 600; font-size: 20px;">🚀 Agent Processing Pipeline</h3><span style="color: white; font-size: 24px; font-weight: 700;">{progress_pct}%</span></div><div style="background: rgba(255,255,255,0.2); height: 24px; border-radius: 12px; overflow: hidden;"><div style="background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%); height: 100%; width: {progress_pct}%; transition: width 0.5s ease; border-radius: 12px; box-shadow: 0 2px 4px rgba(255,215,0,0.4);"></div></div></div>'
            
            st.markdown(progress_html, unsafe_allow_html=True)
            
            # Phase cards - read directly from session_state
            phases = st.session_state.phases
            for phase in PHASES:
                phase_key = phase['key']
                phase_data = phases.get(phase_key, {})
                status = phase_data.get('status', 'pending')
                duration = phase_data.get('duration')
                _render_phase_card_streamlit(
                    icon=phase['icon'],
                    title=phase['title'],
                    description=phase['description'],
                    status=status,
                    duration=duration
                )
    except Exception as e:
        # ✅ CRITICAL: Silent fail - never let UI updates break agent execution
        # Log to console for debugging
        import traceback
        logger.error(f"⚠️ Progress display error (silent): {e}")
        pass


def _build_progress_html(progress: Dict) -> str:
    """Build beautiful HTML for progress display."""
    
    # Overall progress bar
    progress_bar_html = f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        ">
            <h3 style="
                color: white;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 20px;
            ">
                🚀 Agent Processing Pipeline
            </h3>
            <span style="
                color: white;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 24px;
                font-weight: 700;
            ">
                {progress['percent']}%
            </span>
        </div>
        
        <!-- Progress Bar -->
        <div style="
            background: rgba(255,255,255,0.2);
            height: 24px;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        ">
            <div style="
                background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%);
                height: 100%;
                width: {progress['percent']}%;
                transition: width 0.5s ease;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(255,215,0,0.4);
            "></div>
        </div>
    </div>
    """
    
    # Phase cards
    phases_html = ""
    for phase in PHASES:
        phase_data = st.session_state.phases.get(phase['key'], {})
        status = phase_data.get('status', 'pending')
        duration = phase_data.get('duration')
        error = phase_data.get('error')
        
        card_html = _render_phase_card(
            icon=phase['icon'],
            title=phase['title'],
            description=phase['description'],
            status=status,
            duration=duration,
            error=error
        )
        phases_html += card_html
    
    # Combine all HTML
    full_html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        {progress_bar_html}
        <div style="display: grid; gap: 12px;">
            {phases_html}
        </div>
    </div>
    """
    
    # DO NOT PRINT - this was causing HTML to display as text!
    # print(full_html)
    
    return full_html


def _render_phase_card_streamlit(
    icon: str,
    title: str,
    description: str,
    status: str,
    duration: Optional[float] = None
):
    """Render a phase card using Streamlit markdown - FIXED to prevent HTML escaping!"""
    
    # Status-based styling
    if status == "completed":
        bg_color = "#d4edda"
        border_color = "#28a745"
        status_icon = "✅"
        status_text = "Complete"
        status_color = "#155724"
        progress_width = "100%"  # ✅ Progress bar for completed phase
    elif status == "error":
        bg_color = "#f8d7da"
        border_color = "#dc3545"
        status_icon = "❌"
        status_text = "Error"
        status_color = "#721c24"
        progress_width = "100%"  # Show full bar even on error
    elif status == "running":
        bg_color = "#fff3cd"
        border_color = "#ffc107"
        status_icon = "⏳"
        status_text = "Running..."
        status_color = "#856404"
        progress_width = "50%"  # ✅ Progress bar for running phase (50% animated)
    else:  # pending
        bg_color = "#f8f9fa"
        border_color = "#dee2e6"
        status_icon = "⏸️"
        status_text = "Pending"
        status_color = "#6c757d"
        progress_width = "0%"  # No progress bar for pending
    
    # Build duration HTML separately (avoids nested f-string issues)
    duration_html = ""
    if duration is not None:
        duration_html = f'<span style="color: {border_color}; font-size: 12px; font-weight: 600;">{duration:.2f}s</span>'
    
    # ✅ Add progress bar HTML for each phase
    progress_bar_html = ""
    if status != "pending":  # Show progress bar for running/completed/error
        if status == "running":
            # Animated progress bar for running phase
            progress_bar_html = f'<div style="margin-top: 10px; background: rgba(255,255,255,0.5); height: 6px; border-radius: 3px; overflow: hidden;"><div style="background: linear-gradient(90deg, {border_color}, #ffd700); height: 100%; width: {progress_width}; transition: width 0.5s ease; animation: pulse 2s infinite;"></div></div>'
        else:
            # Static progress bar for completed/error
            progress_bar_html = f'<div style="margin-top: 10px; background: rgba(255,255,255,0.5); height: 6px; border-radius: 3px; overflow: hidden;"><div style="background: {border_color}; height: 100%; width: {progress_width}; transition: width 0.5s ease;"></div></div>'
    
    # Render card - FIXED: Single-line HTML to prevent escaping, includes progress bar
    html = f'<div style="background: {bg_color}; border-left: 5px solid {border_color}; padding: 16px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 8px;"><div style="display: flex; justify-content: space-between; align-items: center;"><div style="flex: 1;"><div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;"><span style="font-size: 24px;">{icon}</span><span style="font-weight: 600; font-size: 16px; color: #2c3e50;">{title}</span></div><div style="font-size: 13px; color: #6c757d; margin-left: 34px;">{description}</div>{progress_bar_html}</div><div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;"><div style="display: flex; align-items: center; gap: 6px;"><span style="font-size: 18px;">{status_icon}</span><span style="font-weight: 600; font-size: 14px; color: {status_color};">{status_text}</span></div>{duration_html}</div></div></div>'
    
    st.markdown(html, unsafe_allow_html=True)


def _render_phase_card(
    icon: str,
    title: str,
    description: str,
    status: str,
    duration: Optional[float] = None,
    error: Optional[str] = None
) -> str:
    """DEPRECATED: Use _render_phase_card_streamlit instead."""
    
    # Status-based styling
    if status == "completed":
        bg_color = "#d4edda"
        border_color = "#28a745"
        status_icon = "✅"
        status_text = "Complete"
        status_color = "#155724"
    elif status == "error":
        bg_color = "#f8d7da"
        border_color = "#dc3545"
        status_icon = "❌"
        status_text = "Error"
        status_color = "#721c24"
    elif status == "running":
        bg_color = "#fff3cd"
        border_color = "#ffc107"
        status_icon = "⏳"
        status_text = "Running..."
        status_color = "#856404"
    else:  # pending
        bg_color = "#f8f9fa"
        border_color = "#dee2e6"
        status_icon = "⏸️"
        status_text = "Pending"
        status_color = "#6c757d"
    
    # Duration text
    duration_html = ""
    if duration is not None:
        duration_html = f"""
        <span style="
            color: {border_color};
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            font-weight: 600;
        ">
            {duration:.2f}s
        </span>
        """
    
    # Error message
    error_html = ""
    if error:
        error_html = f"""
        <div style="
            margin-top: 8px;
            padding: 8px;
            background: rgba(220,53,69,0.1);
            border-radius: 4px;
            font-size: 12px;
            color: #721c24;
        ">
            ⚠️ {error}
        </div>
        """
    
    card_html = f"""
    <div style="
        background: {bg_color};
        border-left: 5px solid {border_color};
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 6px;
                ">
                    <span style="font-size: 24px;">{icon}</span>
                    <span style="
                        font-weight: 600;
                        font-size: 16px;
                        color: #2c3e50;
                    ">
                        {title}
                    </span>
                </div>
                <div style="
                    font-size: 13px;
                    color: #6c757d;
                    margin-left: 34px;
                ">
                    {description}
                </div>
                {error_html}
            </div>
            <div style="
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 4px;
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 6px;
                ">
                    <span style="font-size: 18px;">{status_icon}</span>
                    <span style="
                        font-weight: 600;
                        font-size: 14px;
                        color: {status_color};
                    ">
                        {status_text}
                    </span>
                </div>
                {duration_html}
            </div>
        </div>
    </div>
    """
    
    return card_html


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

# Keep old function names for backward compatibility
def mark_phase_running_old(phase_key):
    """Deprecated: use mark_phase_running()"""
    mark_phase_running(phase_key)

def mark_phase_complete_old(phase_key, duration=None):
    """Deprecated: use mark_phase_complete()"""
    mark_phase_complete(phase_key, duration)

def mark_phase_error_old(phase_key, error_msg=None):
    """Deprecated: use mark_phase_error()"""
    mark_phase_error(phase_key, error_msg)


# ============================================================================
# SUMMARY
# ============================================================================

"""
Progress Tracking Features:
✅ Real-time progress bar (0-100%)
✅ Beautiful gradient colors
✅ Professional typography
✅ Color-coded phase status
✅ Duration tracking per phase
✅ Error display
✅ Modern card design
✅ Smooth animations
✅ Weighted progress calculation
"""

