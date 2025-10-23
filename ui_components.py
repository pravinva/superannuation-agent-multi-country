# ui_components.py
"""UI components with country theming and styled welcome sections"""

import streamlit as st
import pandas as pd
from config import BRANDCONFIG, NATIONAL_COLORS
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS


def render_logo():
    """Render brand title and subtitle"""
    st.markdown(f"## 🏦 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'))


def render_member_card(member, is_selected=False, country="Australia"):
    """Render member card with country theme colors"""
    
    # Country themes
    themes = {
        "Australia": {"flag": "🇦🇺", "color": "#00843D", "bg_color": "#FFFACD"},
        "USA": {"flag": "🇺🇸", "color": "#B22234", "bg_color": "#E6F0FF"},
        "United Kingdom": {"flag": "🇬🇧", "color": "#012169", "bg_color": "#FFE6E6"},
        "India": {"flag": "🇮🇳", "color": "#FF9933", "bg_color": "#FFF5E6"}
    }
    
    theme = themes.get(country, themes["Australia"])
    flag = theme["flag"]
    
    balance = member.get('super_balance', 0)
    try:
        balance = float(balance) if balance else 0
    except (ValueError, TypeError):
        balance = 0
    
    # Use native Streamlit with colored containers
    if is_selected:
        with st.container():
            st.markdown(f"### {flag} {member.get('name', 'Unknown')} ✅")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Age", member.get('age', 'N/A'))
            with col2:
                st.metric("Status", member.get('employment_status', 'N/A'))
            with col3:
                st.metric("Balance", f"${balance:,.0f}")
            st.caption(f"🆔 {member.get('member_id', 'N/A')}")
    else:
        with st.container():
            st.markdown(f"### {flag} {member.get('name', 'Unknown')}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"**Age:** {member.get('age', 'N/A')}")
            with col2:
                st.caption(f"**Status:** {member.get('employment_status', 'N/A')}")
            with col3:
                st.caption(f"**Balance:** ${balance:,.0f}")
            st.caption(f"🆔 {member.get('member_id', 'N/A')}")


def render_question_card(question, emoji="💬"):
    """Render a sample question card"""
    st.info(f"{emoji} {question}")


def render_country_welcome(country, prompt_text, disclaimer):
    """
    Render beautiful country-themed welcome section with colored backgrounds
    """
    
    # Country themes with colors
    themes = {
        "Australia": {
            "flag": "🇦🇺",
            "info_bg": "#E8F5E9",      # Light green
            "warning_bg": "#FFF9C4",   # Light yellow
            "border_color": "#00843D", # Green
            "accent_color": "#FFCD00"  # Gold
        },
        "USA": {
            "flag": "🇺🇸",
            "info_bg": "#E3F2FD",      # Light blue
            "warning_bg": "#FFEBEE",   # Light red
            "border_color": "#3C3B6E", # Blue
            "accent_color": "#B22234"  # Red
        },
        "United Kingdom": {
            "flag": "🇬🇧",
            "info_bg": "#E8EAF6",      # Light indigo
            "warning_bg": "#FCE4EC",   # Light pink
            "border_color": "#012169", # Navy
            "accent_color": "#C8102E"  # Red
        },
        "India": {
            "flag": "🇮🇳",
            "info_bg": "#FFF3E0",      # Light orange
            "warning_bg": "#E8F5E9",   # Light green
            "border_color": "#138808", # Green
            "accent_color": "#FF9933"  # Saffron
        }
    }
    
    theme = themes.get(country, themes["Australia"])
    
    # Render welcome information card
    st.markdown(
        f"""
        <div style="
            background: {theme['info_bg']};
            border-left: 5px solid {theme['border_color']};
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 2em; margin-right: 12px;">{theme['flag']}</span>
                <h3 style="margin: 0; color: {theme['border_color']};">Welcome to {country}</h3>
            </div>
            <p style="
                color: #333;
                line-height: 1.7;
                font-size: 1.05em;
                margin: 0;
            ">
                <strong>ℹ️ About:</strong> {prompt_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Render disclaimer card
    st.markdown(
        f"""
        <div style="
            background: {theme['warning_bg']};
            border-left: 5px solid {theme['accent_color']};
            border-radius: 8px;
            padding: 18px;
            margin: 15px 0 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <p style="
                color: #555;
                line-height: 1.6;
                font-size: 0.95em;
                margin: 0;
            ">
                <strong>⚠️ Disclaimer:</strong> {disclaimer}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer with country colors"""
    disclaimer = POST_ANSWER_DISCLAIMERS.get(country, POST_ANSWER_DISCLAIMERS.get("Australia", ""))
    
    # Country colors for disclaimer
    colors = {
        "Australia": {"bg": "#FFF9C4", "border": "#FFCD00"},
        "USA": {"bg": "#FFEBEE", "border": "#B22234"},
        "United Kingdom": {"bg": "#FCE4EC", "border": "#C8102E"},
        "India": {"bg": "#FFF3E0", "border": "#FF9933"}
    }
    
    theme_color = colors.get(country, colors["Australia"])
    
    st.markdown(
        f"""
        <div style="
            background: {theme_color['bg']};
            border-left: 4px solid {theme_color['border']};
            border-radius: 6px;
            padding: 16px;
            margin: 20px 0;
        ">
            <p style="color: #666; font-size: 0.95em; line-height: 1.6; margin: 0;">
                <strong>⚠️ Important:</strong> {disclaimer}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_audit_table(audit_df):
    """Render audit/governance table"""
    if audit_df is None or audit_df.empty:
        st.info("No audit records found.")
        return
    
    st.dataframe(audit_df, use_container_width=True, hide_index=True)


def render_structured_response(response_dict):
    """
    Render 3-part structured response: Situation → Analysis → Recommendation
    """
    
    # Part 1: Your Current Situation
    st.markdown("## 📊 Your Current Situation")
    situation = response_dict.get('situation', 'No situation data available.')
    st.markdown(situation)
    
    st.markdown("---")
    
    # Part 2: Analysis & Insights
    st.markdown("## 💡 Analysis & Insights")
    insights = response_dict.get('insights', [])
    if insights:
        for insight in insights:
            st.markdown(f"• {insight}")
    else:
        st.markdown("No insights available.")
    
    st.markdown("---")
    
    # Part 3: Our Recommendation
    st.markdown("## ✅ Our Recommendation")
    recommendations = response_dict.get('recommendations', [])
    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            st.markdown(f"{idx}. {rec}")
    else:
        st.markdown("No recommendations available.")

