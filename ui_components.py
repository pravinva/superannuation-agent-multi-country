# ui_components.py - FIXED: Simplified Cards + No HTML Leak
"""UI components for the retirement advisory app"""

import streamlit as st
import os
import pandas as pd

# Temporary inline config
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
    Render a SIMPLE member card - just name and selection indicator.
    No HTML details leaked to user.
    """

    # Country color themes
    colors = {
        "Australia": {
            "flag": "🇦🇺",
            "primary": "#FFD700",  # Strong gold
            "secondary": "#00843D",  # Green
        },
        "USA": {
            "flag": "🇺🇸",
            "primary": "#B22234",  # Red
            "secondary": "#3C3B6E",  # Blue
        },
        "United Kingdom": {
            "flag": "🇬🇧",
            "primary": "#C8102E",  # Red
            "secondary": "#012169",  # Navy
        },
        "India": {
            "flag": "🇮🇳",
            "primary": "#FF9933",  # Saffron
            "secondary": "#138808",  # Green
        }
    }

    theme = colors.get(country, colors["Australia"])

    # Styling based on selection
    if is_selected:
        border = f"5px solid {theme['secondary']}"
        bg = f"linear-gradient(135deg, {theme['primary']}20 0%, {theme['secondary']}15 100%)"
        shadow = "0 8px 16px rgba(0,0,0,0.2)"
    else:
        border = "1px solid #e0e0e0"
        bg = "#ffffff"
        shadow = "0 2px 5px rgba(0,0,0,0.08)"

    # Get member info
    member_name = member.get('name', 'Unknown')
    age = member.get('age', 'N/A')
    balance = member.get('super_balance', 0)

    # Format balance as integer (no decimals, no commas to avoid jumbling)
    if isinstance(balance, (int, float)):
        balance_int = int(balance)
        balance_display = f"{balance_int:,}"  # This formats with commas for display only
    else:
        balance_display = str(balance)

    # Simple card - ONLY name, age, balance
    card_html = f"""
    <div style="
        border: {border};
        border-radius: 12px;
        padding: 20px;
        background: {bg};
        box-shadow: {shadow};
        margin-bottom: 12px;
    ">
        <div style="font-size: 1.3em; font-weight: 600; color: {theme['secondary']}; margin-bottom: 12px;">
            {theme['flag']} {member_name}
        </div>
        <div style="color: #666; font-size: 0.95em;">
            Age {age} • Balance: {balance_display}
        </div>
        {f'<div style="margin-top: 12px; background: {theme["primary"]}; padding: 8px 12px; border-radius: 6px; text-align: center; font-weight: 600; color: #000;">✓ SELECTED</div>' if is_selected else ''}
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

    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )
