# ui_components.py
"""UI components for the retirement advisory app"""

import streamlit as st
import os
import pandas as pd
from config import BRANDCONFIG, NATIONAL_COLORS
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS


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
            "primary": "#FFCD00",
            "secondary": "#00843D",
            "border": "#00843D",
            "gradient": "linear-gradient(135deg, #FFCD00 0%, #00843D 100%)",
            "light_bg": "rgba(255, 205, 0, 0.1)",
            "shadow": "0 4px 15px rgba(0, 132, 61, 0.15)"
        },
        "US": {
            "flag": "🇺🇸",
            "primary": "#B22234",
            "secondary": "#3C3B6E",
            "border": "#991b2e",
            "gradient": "linear-gradient(135deg, #B22234 0%, #3C3B6E 100%)",
            "light_bg": "rgba(178, 34, 52, 0.1)",
            "shadow": "0 4px 15px rgba(178, 34, 52, 0.2)"
        },
        "UK": {
            "flag": "🇬🇧",
            "primary": "#012169",
            "secondary": "#C8102E",
            "border": "#011352",
            "gradient": "linear-gradient(135deg, #012169 0%, #C8102E 100%)",
            "light_bg": "rgba(1, 33, 105, 0.1)",
            "shadow": "0 4px 15px rgba(1, 33, 105, 0.15)"
        },
        "IN": {
            "flag": "🇮🇳",
            "primary": "#FF9933",
            "secondary": "#138808",
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
    
    # FIX: Use .format() instead of f-string to avoid quote issues
    card_html = """
    <div style='{border_style} border-radius: 12px; padding: 18px; background: {bg_color}; box-shadow: {box_shadow}; margin-bottom: 12px;'>
        <div style='display: flex; align-items: center; margin-bottom: 12px;'>
            <span style='font-size: 2.2em; margin-right: 12px;'>{flag}</span>
            <div style='flex: 1;'>
                <h3 style='margin: 0; color: {primary}; font-size: 1.3em;'>{name}</h3>
            </div>
        </div>
        <div style='border-top: 2px solid; border-image: {gradient} 1; padding-top: 10px;'>
            <p style='margin: 5px 0; color: #333;'><strong>Age:</strong> {age}</p>
            <p style='margin: 5px 0; color: #333;'><strong>Status:</strong> {status}</p>
            <p style='margin: 5px 0; color: #333;'>
                <strong>Balance:</strong> 
                <span style='color: {primary}; font-weight: bold;'>${balance:,.0f}</span>
            </p>
            <p style='margin: 5px 0; font-size: 0.8em; color: #666;'>ID: {member_id}</p>
        </div>
    </div>
    """.format(
        border_style=border_style,
        bg_color=bg_color,
        box_shadow=box_shadow,
        flag=theme['flag'],
        primary=theme['primary'],
        gradient=theme['gradient'],
        name=member.get('name', 'Unknown'),
        age=member.get('age', 'N/A'),
        status=member.get('employment_status', 'N/A'),
        balance=balance,
        member_id=member.get('member_id', 'N/A')
    )
    
    st.markdown(card_html, unsafe_allow_html=True)


def render_question_card(question, emoji="💬"):
    """Render a sample question card"""
    card_html = f"""
    <div style='border-left: 4px solid #4CAF50; padding: 12px 16px; background: linear-gradient(135deg, #f5f5f5 0%, #e8f5e9 100%); border-radius: 8px; margin-bottom: 10px;'>
        <p style='margin: 0; color: #333; font-size: 0.95em;'>
            <span style='font-size: 1.2em; margin-right: 8px;'>{emoji}</span>
            {question}
        </p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_country_welcome(country, prompt_text, disclaimer):
    """Render consolidated welcome section with prompt and disclaimer"""
    country_code_map = {
        "Australia": "AU",
        "USA": "US",
        "United Kingdom": "UK",
        "India": "IN"
    }
    
    country_code = country_code_map.get(country, "AU")
    
    themes = {
        "AU": {"primary": "#FFCD00", "secondary": "#00843D"},
        "US": {"primary": "#B22234", "secondary": "#3C3B6E"},
        "UK": {"primary": "#012169", "secondary": "#C8102E"},
        "IN": {"primary": "#FF9933", "secondary": "#138808"}
    }
    
    theme = themes.get(country_code, themes["AU"])
    
    # FIX: Use .format() to avoid quote escaping issues
    welcome_html = """
    <div style='margin-bottom: 20px;'>
        <div style='height: 2px; background: linear-gradient(135deg, {primary} 0%, {secondary} 100%); margin: 16px 0; opacity: 0.3;'></div>
        <div style='margin-bottom: 16px;'>
            <p style='color: #444; line-height: 1.7; font-size: 0.95em; margin: 0;'>
                <strong>ℹ️ About:</strong> {prompt_text}
            </p>
        </div>
        <div style='padding: 14px; background: rgba(255, 243, 205, 0.3); border-left: 3px solid #ff9800; border-radius: 6px; margin-top: 12px;'>
            <p style='color: #666; font-size: 0.88em; line-height: 1.5; margin: 0;'>
                <strong>⚠️ Disclaimer:</strong> {disclaimer}
            </p>
        </div>
    </div>
    """.format(
        primary=theme['primary'],
        secondary=theme['secondary'],
        prompt_text=prompt_text,
        disclaimer=disclaimer
    )
    
    st.markdown(welcome_html, unsafe_allow_html=True)


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimer = POST_ANSWER_DISCLAIMERS.get(country, POST_ANSWER_DISCLAIMERS.get("Australia", ""))
    
    disclaimer_html = f"""
    <div style='margin-top: 20px; padding: 16px; background: rgba(255, 243, 205, 0.2); border-left: 4px solid #ff9800; border-radius: 8px;'>
        <p style='color: #666; font-size: 0.9em; line-height: 1.6; margin: 0;'>
            <strong>⚠️ Important:</strong> {disclaimer}
        </p>
    </div>
    """
    
    st.markdown(disclaimer_html, unsafe_allow_html=True)


def render_audit_table(audit_df):
    """Render audit/governance table"""
    if audit_df is None or audit_df.empty:
        st.info("No audit records found.")
        return
    
    st.dataframe(audit_df, use_container_width=True, hide_index=True)

