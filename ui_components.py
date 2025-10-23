# ui_components.py
"""UI components with country theming and structured response rendering"""

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
        "Australia": {"flag": "🇦🇺", "color": "#00843D", "bg": "#FFFACD"},
        "USA": {"flag": "🇺🇸", "color": "#B22234", "bg": "#E6F0FF"},
        "United Kingdom": {"flag": "🇬🇧", "color": "#012169", "bg": "#FFE6E6"},
        "India": {"flag": "🇮🇳", "color": "#FF9933", "bg": "#FFF5E6"}
    }
    
    theme = themes.get(country, themes["Australia"])
    flag = theme["flag"]
    
    balance = member.get('super_balance', 0)
    try:
        balance = float(balance) if balance else 0
    except (ValueError, TypeError):
        balance = 0
    
    # Create themed container using CSS
    if is_selected:
        # Selected card - highlighted with country color
        card_style = f"""
        <div style='
            border: 3px solid {theme["color"]};
            border-radius: 10px;
            padding: 16px;
            background: {theme["bg"]};
            margin-bottom: 16px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 1.5em;'>{flag} <strong>{member.get('name', 'Unknown')}</strong> ✓</div>
            <div style='margin-top: 12px; display: flex; gap: 20px;'>
                <div><strong>Age:</strong> {member.get('age', 'N/A')}</div>
                <div><strong>Status:</strong> {member.get('employment_status', 'N/A')}</div>
                <div><strong>Balance:</strong> <span style='color: {theme["color"]}; font-weight: bold;'>${balance:,.0f}</span></div>
            </div>
            <div style='margin-top: 8px; font-size: 0.85em; color: #666;'>ID: {member.get('member_id', 'N/A')}</div>
        </div>
        """
    else:
        # Unselected card - subtle gray border with hover effect
        card_style = f"""
        <div style='
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 16px;
            background: white;
            margin-bottom: 16px;
            transition: all 0.3s ease;
        ' onmouseover="this.style.borderColor='{theme["color"]}'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)';" 
           onmouseout="this.style.borderColor='#ddd'; this.style.boxShadow='none';">
            <div style='font-size: 1.5em;'>{flag} <strong>{member.get('name', 'Unknown')}</strong></div>
            <div style='margin-top: 12px; display: flex; gap: 20px; font-size: 0.9em;'>
                <div><strong>Age:</strong> {member.get('age', 'N/A')}</div>
                <div><strong>Status:</strong> {member.get('employment_status', 'N/A')}</div>
                <div><strong>Balance:</strong> ${balance:,.0f}</div>
            </div>
            <div style='margin-top: 8px; font-size: 0.85em; color: #666;'>ID: {member.get('member_id', 'N/A')}</div>
        </div>
        """
    
    st.markdown(card_style, unsafe_allow_html=True)


def render_question_card(question, emoji="💬"):
    """Render a sample question card"""
    st.info(f"{emoji} {question}")


def render_country_welcome(country, prompt_text, disclaimer):
    """Render consolidated welcome section"""
    st.markdown("---")
    st.info(f"ℹ️ **About:** {prompt_text}")
    st.warning(f"⚠️ **Disclaimer:** {disclaimer}")
    st.markdown("---")


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimer = POST_ANSWER_DISCLAIMERS.get(country, POST_ANSWER_DISCLAIMERS.get("Australia", ""))
    st.warning(f"⚠️ **Important:** {disclaimer}")


def render_audit_table(audit_df):
    """Render audit/governance table"""
    if audit_df is None or audit_df.empty:
        st.info("No audit records found.")
        return
    
    st.dataframe(audit_df, use_container_width=True, hide_index=True)


def render_structured_response(response_dict):
    """
    Render 3-part structured response: Situation → Analysis → Recommendation
    
    Args:
        response_dict: Dictionary with keys 'situation', 'insights', 'recommendations'
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

