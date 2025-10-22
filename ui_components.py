# ui_components.py
"""UI components for the retirement advisory app"""

import streamlit as st
import os
import pandas as pd
from config import BRANDCONFIG, NATIONAL_COLORS
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS

def render_logo():
    """Render brand logo, subtitle, and title"""
    # Check if logo.png exists in root
    if os.path.exists("logo.png"):
        # Display logo centered
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("logo.png", use_column_width=True)
    
    # Display brand name and subtitle
    st.markdown(f"## 🏦 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'))


def render_member_card(member, is_selected=False, country="Australia"):
    """Render a member profile card with national colors"""
    colors = NATIONAL_COLORS.get(country, NATIONAL_COLORS["Australia"])
    primary_color = colors[0]
    
    border_style = f"border: 3px solid {primary_color};" if is_selected else "border: 1px solid #ddd;"
    
    card_html = f"""
    <div style="
        padding: 15px;
        border-radius: 10px;
        {border_style}
        background-color: {'#f0f8ff' if is_selected else '#ffffff'};
        margin: 10px 0;
    ">
        <h4 style="color: {primary_color}; margin: 0 0 10px 0;">{member.get('name', 'Unknown')}</h4>
        <p style="margin: 5px 0;"><strong>Age:</strong> {member.get('age', 'N/A')}</p>
        <p style="margin: 5px 0;"><strong>Status:</strong> {member.get('employment_status', 'N/A')}</p>
        <p style="margin: 5px 0;"><strong>Balance:</strong> ${member.get('super_balance', 0):,.0f}</p>
        <p style="margin: 5px 0; font-size: 0.8em; color: #666;">ID: {member.get('member_id', 'N/A')}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_question_card(question, country="Australia"):
    """Render a sample question card with national colors"""
    colors = NATIONAL_COLORS.get(country, NATIONAL_COLORS["Australia"])
    primary_color = colors[0]
    
    card_html = f"""
    <div style="
        padding: 12px;
        border-left: 4px solid {primary_color};
        background-color: #f9f9f9;
        margin: 8px 0;
        border-radius: 5px;
    ">
        <p style="margin: 0; color: #333;">{question}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_country_prompt(country):
    """Render country-specific prompts and information"""
    prompts = COUNTRY_PROMPTS.get(country, COUNTRY_PROMPTS["Australia"])
    
    st.info(prompts.get('welcome', 'Welcome to the retirement advisory portal.'))
    
    if 'info' in prompts:
        for info in prompts['info']:
            st.info(info)


def render_disclaimer(country):
    """Render country-specific disclaimer"""
    disclaimer = COUNTRY_DISCLAIMERS.get(country, COUNTRY_DISCLAIMERS["Australia"])
    st.warning(disclaimer)


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimer = POST_ANSWER_DISCLAIMERS.get(country, POST_ANSWER_DISCLAIMERS["Australia"])
    st.info(disclaimer)


def render_audit_table(audit_df):
    """Render audit logs in a table format"""
    if audit_df.empty:
        st.warning("No audit logs found.")
        return
    
    # Select and rename columns for display
    display_columns = ['timestamp', 'user_id', 'country', 'query_string', 'tool_used', 'judge_verdict', 'cost']
    
    # Check which columns actually exist
    available_columns = [col for col in display_columns if col in audit_df.columns]
    
    if not available_columns:
        st.warning("No displayable columns found in audit data.")
        return
    
    display_df = audit_df[available_columns].copy()
    
    # Format timestamp if it exists
    if 'timestamp' in display_df.columns:
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Format cost if it exists
    if 'cost' in display_df.columns:
        display_df['cost'] = display_df['cost'].apply(lambda x: f"${x:.4f}" if pd.notnull(x) else "$0.00")
    
    # Truncate long query strings
    if 'query_string' in display_df.columns:
        display_df['query_string'] = display_df['query_string'].apply(
            lambda x: (x[:50] + '...') if isinstance(x, str) and len(x) > 50 else x
        )
    
    # Display the table
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Add download button
    csv = audit_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Audit Log (CSV)",
        data=csv,
        file_name="audit_log.csv",
        mime="text/csv"
    )

