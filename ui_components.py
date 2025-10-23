# ui_components.py
# VERSION: 2.0 - HTML FIX APPLIED

"""UI components for the retirement advisory app"""

import streamlit as st
import os
import pandas as pd
from config import BRANDCONFIG, NATIONAL_COLORS
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS
 
st.sidebar.write("✅ ui_components.py VERSION 2.0 LOADED")


def render_logo():
    """Render brand title and subtitle (logo in sidebar)"""
    st.markdown(f"## 🏦 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'))


def render_member_card(member, is_selected=False, country="Australia"):
    """Render a member profile card with flag, gradient backgrounds, and national colors"""
    # Map display names to country codes
    country_code_map = {
        "Australia": "AU",
        "USA": "US",
        "United Kingdom": "UK",
        "India": "IN"
    }
    
    country_code = country_code_map.get(country, "AU")
    
    # Theme configuration
    themes = {
        "AU": {
            "flag": "🇦🇺",
            "primary": "#FFCD00",  # Gold
            "secondary": "#00843D",  # Green
            "border": "#00843D",
            "gradient": "linear-gradient(135deg, #FFCD00 0%, #00843D 100%)",
            "light_bg": "rgba(255, 205, 0, 0.1)",
            "shadow": "0 4px 15px rgba(0, 132, 61, 0.15)"
        },
        "US": {
            "flag": "🇺🇸",
            "primary": "#B22234",  # Red
            "secondary": "#3C3B6E",  # Blue
            "border": "#991b2e",
            "gradient": "linear-gradient(135deg, #B22234 0%, #3C3B6E 100%)",
            "light_bg": "rgba(178, 34, 52, 0.1)",
            "shadow": "0 4px 15px rgba(178, 34, 52, 0.2)"
        },
        "UK": {
            "flag": "🇬🇧",
            "primary": "#012169",  # Navy
            "secondary": "#C8102E",  # Red
            "border": "#011352",
            "gradient": "linear-gradient(135deg, #012169 0%, #C8102E 100%)",
            "light_bg": "rgba(1, 33, 105, 0.1)",
            "shadow": "0 4px 15px rgba(1, 33, 105, 0.15)"
        },
        "IN": {
            "flag": "🇮🇳",
            "primary": "#FF9933",  # Saffron
            "secondary": "#138808",  # Green
            "border": "#205080",
            "gradient": "linear-gradient(135deg, #FF9933 0%, #138808 100%)",
            "light_bg": "rgba(255, 153, 51, 0.1)",
            "shadow": "0 4px 15px rgba(32, 80, 128, 0.12)"
        }
    }
    
    theme = themes.get(country_code, themes["AU"])
    
    # Convert balance to float if it's a string
    balance = member.get('super_balance', 0)
    try:
        balance = float(balance) if balance else 0
    except (ValueError, TypeError):
        balance = 0
    
    # Card styling based on selection state
    if is_selected:
        border_style = f"border: 3px solid {theme['border']};"
        bg_color = theme['light_bg']
        box_shadow = theme['shadow']
    else:
        border_style = "border: 1px solid #ddd;"
        bg_color = "#ffffff"
        box_shadow = "0 2px 4px rgba(0,0,0,0.1)"
    
    card_html = f"""
    <div style="
        {border_style}
        border-radius: 12px;
        padding: 18px;
        background: {bg_color};
        box-shadow: {box_shadow};
        margin-bottom: 12px;
        transition: all 0.3s ease;
    ">
        <div style="
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        ">
            <span style="font-size: 2.2em; margin-right: 12px;">{theme['flag']}</span>
            <div style="flex: 1;">
                <h3 style="
                    margin: 0;
                    color: {theme['primary']};
                    font-size: 1.3em;
                ">{member.get('name', 'Unknown')}</h3>
            </div>
        </div>
        
        <div style="
            border-top: 2px solid;
            border-image: {theme['gradient']} 1;
            padding-top: 10px;
        ">
            <p style="margin: 5px 0; color: #333;">
                <strong>Age:</strong> {member.get('age', 'N/A')}
            </p>
            <p style="margin: 5px 0; color: #333;">
                <strong>Status:</strong> {member.get('employment_status', 'N/A')}
            </p>
            <p style="margin: 5px 0; color: #333;">
                <strong>Balance:</strong> 
                <span style="color: {theme['primary']}; font-weight: bold;">
                    ${balance:,.0f}
                </span>
            </p>
            <p style="margin: 5px 0; font-size: 0.8em; color: #666;">
                ID: {member.get('member_id', 'N/A')}
            </p>
        </div>
    </div>
    """
    
    # FIX APPLIED: Added unsafe_allow_html=True
    st.markdown(card_html, unsafe_allow_html=True)


def render_question_card(question, emoji="💬"):
    """Render a sample question card"""
    card_html = f"""
    <div style="
        border-left: 4px solid #4CAF50;
        padding: 12px 16px;
        background: linear-gradient(135deg, #f5f5f5 0%, #e8f5e9 100%);
        border-radius: 8px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
    " onmouseover="this.style.background='linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)'" 
       onmouseout="this.style.background='linear-gradient(135deg, #f5f5f5 0%, #e8f5e9 100%)'">
        <p style="margin: 0; color: #333; font-size: 0.95em;">
            <span style="font-size: 1.2em; margin-right: 8px;">{emoji}</span>
            {question}
        </p>
    </div>
    """
    
    # FIX APPLIED: Added unsafe_allow_html=True
    st.markdown(card_html, unsafe_allow_html=True)


def render_country_welcome(country, prompt_text, disclaimer):
    """Render consolidated welcome section with prompt and disclaimer"""
    # Map display names to country codes for theming
    country_code_map = {
        "Australia": "AU",
        "USA": "US",
        "United Kingdom": "UK",
        "India": "IN"
    }
    
    country_code = country_code_map.get(country, "AU")
    
    # Theme colors
    themes = {
        "AU": {"primary": "#FFCD00", "secondary": "#00843D"},
        "US": {"primary": "#B22234", "secondary": "#3C3B6E"},
        "UK": {"primary": "#012169", "secondary": "#C8102E"},
        "IN": {"primary": "#FF9933", "secondary": "#138808"}
    }
    
    theme = themes.get(country_code, themes["AU"])
    
    welcome_html = f"""
    <div style="margin-bottom: 20px;">
        <!-- Separator -->
        <div style="
            height: 2px;
            background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
            margin: 16px 0;
            opacity: 0.3;
        "></div>
        
        <!-- Welcome Info -->
        <div style="margin-bottom: 16px;">
            <p style="color: #444; line-height: 1.7; font-size: 0.95em; margin: 0;">
                <strong>ℹ️ About:</strong> {prompt_text}
            </p>
        </div>
        
        <!-- Disclaimer -->
        <div style="
            padding: 14px;
            background: rgba(255, 243, 205, 0.3);
            border-left: 3px solid #ff9800;
            border-radius: 6px;
            margin-top: 12px;
        ">
            <p style="color: #666; font-size: 0.88em; line-height: 1.5; margin: 0;">
                <strong>⚠️ Disclaimer:</strong> {disclaimer}
            </p>
        </div>
    </div>
    """
    
    # FIX APPLIED: Added unsafe_allow_html=True
    st.markdown(welcome_html, unsafe_allow_html=True)


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimer = POST_ANSWER_DISCLAIMERS.get(country, POST_ANSWER_DISCLAIMERS.get("Australia", ""))
    
    disclaimer_html = f"""
    <div style="
        margin-top: 20px;
        padding: 16px;
        background: rgba(255, 243, 205, 0.2);
        border-left: 4px solid #ff9800;
        border-radius: 8px;
    ">
        <p style="color: #666; font-size: 0.9em; line-height: 1.6; margin: 0;">
            <strong>⚠️ Important:</strong> {disclaimer}
        </p>
    </div>
    """
    
    # FIX APPLIED: Added unsafe_allow_html=True
    st.markdown(disclaimer_html, unsafe_allow_html=True)


def render_audit_table(audit_df):
    """Render audit/governance table"""
    if audit_df is None or audit_df.empty:
        st.info("No audit records found.")
        return
    
    # Display as a styled dataframe
    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )

