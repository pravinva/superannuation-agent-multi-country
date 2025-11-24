"""
Widget debugging utilities to diagnose 'Bad setIn index' errors.
"""

import streamlit as st
from functools import wraps
import time

# Global widget counter
_widget_count = 0
_widget_registry = []

def reset_widget_tracking():
    """Reset widget tracking at start of each render."""
    global _widget_count, _widget_registry
    _widget_count = 0
    _widget_registry = []

def track_widget(widget_type, key, location):
    """Track a widget creation."""
    global _widget_count, _widget_registry
    _widget_count += 1
    _widget_registry.append({
        'index': _widget_count - 1,
        'type': widget_type,
        'key': key,
        'location': location
    })
    return _widget_count - 1

def log_session_state_change(key, old_value, new_value, location):
    """Log a session state change."""
    if 'debug_mode' in st.session_state and st.session_state.debug_mode:
        st.sidebar.text(f"[{location}] {key}: {old_value} → {new_value}")

def display_widget_debug_info():
    """Display widget debugging information in sidebar."""
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False

    with st.sidebar:
        st.markdown("---")
        st.subheader("🐛 Debug Mode")
        debug_mode = st.checkbox("Enable Widget Debugging", value=st.session_state.debug_mode, key="debug_toggle")
        st.session_state.debug_mode = debug_mode

        if debug_mode:
            st.markdown("### Widget Registry")
            st.metric("Total Widgets Created", len(_widget_registry))

            with st.expander("📋 Widget Details", expanded=False):
                for widget in _widget_registry:
                    st.text(f"[{widget['index']}] {widget['type']}: {widget['key']}")
                    st.caption(f"   Location: {widget['location']}")

            st.markdown("### Session State Keys")
            widget_keys = [k for k in st.session_state.keys() if not k.startswith('_')]
            st.metric("Widget Keys in Session State", len(widget_keys))

            with st.expander("🔑 Session State Keys", expanded=False):
                for key in sorted(widget_keys):
                    st.text(f"  {key}: {type(st.session_state[key]).__name__}")

def monitor_button(label, key, location, **kwargs):
    """Monitored button wrapper."""
    idx = track_widget('button', key, location)
    if st.session_state.get('debug_mode', False):
        st.caption(f"🔘 Widget [{idx}]: {key}")
    return st.button(label, key=key, **kwargs)

def monitor_selectbox(label, options, key, location, **kwargs):
    """Monitored selectbox wrapper."""
    idx = track_widget('selectbox', key, location)
    if st.session_state.get('debug_mode', False):
        st.caption(f"📋 Widget [{idx}]: {key}")
    return st.selectbox(label, options, key=key, **kwargs)

def monitor_text_input(label, key, location, **kwargs):
    """Monitored text input wrapper."""
    idx = track_widget('text_input', key, location)
    if st.session_state.get('debug_mode', False):
        st.caption(f"✏️  Widget [{idx}]: {key}")
    return st.text_input(label, key=key, **kwargs)

def monitor_checkbox(label, key, location, **kwargs):
    """Monitored checkbox wrapper."""
    idx = track_widget('checkbox', key, location)
    if st.session_state.get('debug_mode', False):
        st.caption(f"☑️  Widget [{idx}]: {key}")
    return st.checkbox(label, key=key, **kwargs)

def log_rerun(location, reason=""):
    """Log a st.rerun() call."""
    if st.session_state.get('debug_mode', False):
        timestamp = time.strftime("%H:%M:%S")
        st.sidebar.warning(f"🔄 [{timestamp}] RERUN from {location}\n{reason}")
