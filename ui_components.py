# ui_components.py - WORKING VERSION with Country Colors
"""UI components for the retirement advisory app"""

import streamlit as st
import os
import pandas as pd

# You'll need to import these from your config
# from config import BRANDCONFIG, NATIONAL_COLORS

# Temporary inline config for this file
BRANDCONFIG = {
    "brand_name": "Global Retirement Advisory",
    "subtitle": "Enterprise-Grade Agentic AI on Databricks"
}


def render_logo():
    """Render brand title and subtitle"""
    st.markdown(f"## 🏦 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'))


def render_member_card(member, is_selected=False, country="Australia"):
    """
    Render a member profile card with country colors and selection highlighting.
    THIS IS THE WORKING VERSION.
    """

    # Country color themes - STRONGER GOLD
    colors = {
        "Australia": {
            "flag": "🇦🇺",
            "primary": "#FFD700",  # STRONGER GOLD (was #FFCD00)
            "secondary": "#00843D",  # Green
            "text": "#006837"
        },
        "USA": {
            "flag": "🇺🇸",
            "primary": "#B22234",  # Red
            "secondary": "#3C3B6E",  # Blue
            "text": "#002868"
        },
        "United Kingdom": {
            "flag": "🇬🇧",
            "primary": "#C8102E",  # Red
            "secondary": "#012169",  # Navy
            "text": "#012169"
        },
        "India": {
            "flag": "🇮🇳",
            "primary": "#FF9933",  # Saffron
            "secondary": "#138808",  # Green
            "text": "#000080"
        }
    }

    theme = colors.get(country, colors["Australia"])

    # Different styling based on selection
    if is_selected:
        border_color = theme['secondary']
        border_width = "5px"  # Thick border when selected
        bg_gradient = f"linear-gradient(135deg, {theme['primary']}25 0%, {theme['secondary']}20 100%)"
        shadow = "0 10px 20px rgba(0,0,0,0.25)"
        badge_text = "🎯 SELECTED"
        badge_bg = theme['primary']
        badge_color = "#000"
    else:
        border_color = "#e0e0e0"
        border_width = "1px"
        bg_gradient = "#ffffff"
        shadow = "0 2px 5px rgba(0,0,0,0.08)"
        badge_text = ""
        badge_bg = "#f5f5f5"
        badge_color = "#999"

    # Render card with inline CSS (THIS IS KEY - must use unsafe_allow_html=True)
    member_name = member.get('name', 'Unknown')
    member_id = member.get('member_id', 'N/A')
    age = member.get('age', 'N/A')
    balance = member.get('super_balance', 0)

    # Format balance
    balance_formatted = f"${balance:,}" if isinstance(balance, (int, float)) else balance

    card_html = f"""
    <div style="
        border: {border_width} solid {border_color};
        border-radius: 16px;
        padding: 24px;
        background: {bg_gradient};
        box-shadow: {shadow};
        margin-bottom: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    ">
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        ">
            <h3 style="
                margin: 0;
                color: {theme['text']};
                font-size: 1.4em;
                font-weight: 600;
            ">
                {theme['flag']} {member_name}
            </h3>
            {f'''<div style="
                background: {badge_bg};
                color: {badge_color};
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: bold;
                border: 2px solid {theme['secondary']};
            ">{badge_text}</div>''' if is_selected else ''}
        </div>

        <div style="
            background: rgba(255,255,255,0.7);
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 12px;
        ">
            <div style="margin-bottom: 8px; color: #555;">
                <strong style="color: {theme['secondary']};">ID:</strong> {member_id}
            </div>
            <div style="margin-bottom: 8px; color: #555;">
                <strong style="color: {theme['secondary']};">Age:</strong> {age} years old
            </div>
            <div style="color: #555;">
                <strong style="color: {theme['secondary']};">Balance:</strong> {balance_formatted}
            </div>
        </div>

        {f'''<div style="
            background: {theme['primary']};
            border-left: 4px solid {theme['secondary']};
            padding: 10px 14px;
            border-radius: 6px;
            color: #000;
            font-weight: 600;
            font-size: 0.95em;
        ">
            ✓ Selected Member
        </div>''' if is_selected else ''}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_country_welcome(country, prompt_text, disclaimer):
    """Render country-specific welcome message"""
    st.info(f"**{country} Retirement Planning**\n\n{prompt_text}")
    if disclaimer:
        with st.expander("⚠️ Important Information"):
            st.caption(disclaimer)


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimers = {
        "Australia": "This is general information only and does not take into account your personal circumstances.",
        "USA": "This information is for educational purposes only and should not be considered financial advice.",
        "United Kingdom": "This information is general in nature and you should seek professional advice.",
        "India": "This is general information only. Please consult a qualified financial advisor."
    }

    disclaimer = disclaimers.get(country, disclaimers["Australia"])
    st.warning(f"⚠️ **Disclaimer:** {disclaimer}")


def render_question_card(question_text):
    """Render a question card"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
    ">
        <h4 style="margin: 0; color: white;">💬 Your Question</h4>
        <p style="margin: 10px 0 0 0; font-size: 1.1em;">{question_text}</p>
    </div>
    """, unsafe_allow_html=True)


def render_audit_table(audit_df):
    """Render audit log table"""
    if audit_df is None or audit_df.empty:
        st.info("No audit logs found.")
        return

    # Display as dataframe with column configuration
    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )
