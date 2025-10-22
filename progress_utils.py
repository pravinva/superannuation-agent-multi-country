# progress_utils.py
import streamlit as st

def render_progress(show_logs, eta_msg="Estimated completion: 5-10 seconds."):
    """Handle display of logs/progress vs waiting message"""
    if not show_logs:
        st.info(f"⏳ Processing your request. {eta_msg} Please hold while we finalize your result.")
    else:
        with st.expander("View Logs", expanded=True):
            st.write("Agent processing logs will appear here...")

