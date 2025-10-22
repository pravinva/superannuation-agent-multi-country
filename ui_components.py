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
        padding: 15px;
        border-radius: 12px;
        {border_style}
        background-color: {bg_color};
        margin: 10px 0;
        box-shadow: {box_shadow};
        transition: all 0.3s ease;
    ">
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        ">
            <h4 style="
                background: {theme['gradient']};
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 0;
                font-size: 1.1em;
                font-weight: bold;
            ">{member.get('name', 'Unknown')}</h4>
            <span style="font-size: 2em;">{theme['flag']}</span>
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
                <span style="color: {theme['secondary']}; font-weight: bold;">
                    ${balance:,.0f}
                </span>
            </p>
            <p style="margin: 5px 0; font-size: 0.8em; color: #666;">
                ID: {member.get('member_id', 'N/A')}
            </p>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_question_card(question, country="Australia"):
    """Render a sample question card with flag emoji and themed gradient styling"""
    # Map display names to country codes
    country_code_map = {
        "Australia": "AU",
        "USA": "US",
        "United Kingdom": "UK",
        "India": "IN"
    }
    
    country_code = country_code_map.get(country, "AU")
    
    # Theme configuration matching member cards
    themes = {
        "AU": {
            "flag": "🇦🇺",
            "gradient": "linear-gradient(135deg, #FFCD00 0%, #00843D 100%)",
            "border": "#00843D"
        },
        "US": {
            "flag": "🇺🇸",
            "gradient": "linear-gradient(135deg, #B22234 0%, #3C3B6E 100%)",
            "border": "#991b2e"
        },
        "UK": {
            "flag": "🇬🇧",
            "gradient": "linear-gradient(135deg, #012169 0%, #C8102E 100%)",
            "border": "#011352"
        },
        "IN": {
            "flag": "🇮🇳",
            "gradient": "linear-gradient(135deg, #FF9933 0%, #138808 100%)",
            "border": "#205080"
        }
    }
    
    theme = themes.get(country_code, themes["AU"])
    
    card_html = f"""
    <div style="
        padding: 14px 16px;
        border-left: 5px solid;
        border-image: {theme['gradient']} 1;
        background: linear-gradient(to right, rgba(255,255,255,0.9), rgba(249,249,249,1));
        margin: 10px 0;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        cursor: pointer;
        transition: all 0.2s ease;
    " onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.12)'" 
       onmouseout="this.style.boxShadow='0 2px 6px rgba(0,0,0,0.08)'">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.3em;">{theme['flag']}</span>
            <p style="margin: 0; color: #333; font-size: 0.95em; line-height: 1.4;">
                {question}
            </p>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_country_welcome(country):
    """Render consolidated country welcome section with prompt and disclaimer in one styled box"""
    
    # Get prompts and disclaimer
    prompts = COUNTRY_PROMPTS.get(country, COUNTRY_PROMPTS.get("Australia", []))
    disclaimer = COUNTRY_DISCLAIMERS.get(country, COUNTRY_DISCLAIMERS.get("Australia", ""))
    
    # Map country to theme
    country_code_map = {
        "Australia": "AU",
        "USA": "US",
        "United Kingdom": "UK",
        "India": "IN"
    }
    
    country_code = country_code_map.get(country, "AU")
    
    themes = {
        "AU": {"gradient": "linear-gradient(135deg, #FFCD00 0%, #00843D 100%)", "flag": "🇦🇺", "color": "#00843D"},
        "US": {"gradient": "linear-gradient(135deg, #B22234 0%, #3C3B6E 100%)", "flag": "🇺🇸", "color": "#B22234"},
        "UK": {"gradient": "linear-gradient(135deg, #012169 0%, #C8102E 100%)", "flag": "🇬🇧", "color": "#012169"},
        "IN": {"gradient": "linear-gradient(135deg, #FF9933 0%, #138808 100%)", "flag": "🇮🇳", "color": "#FF9933"}
    }
    
    theme = themes.get(country_code, themes["AU"])
    
    # Build prompt text
    if isinstance(prompts, list):
        prompt_text = " ".join(prompts)
    elif isinstance(prompts, dict):
        parts = []
        if 'welcome' in prompts:
            parts.append(prompts['welcome'])
        if 'info' in prompts:
            parts.extend(prompts['info'])
        prompt_text = " ".join(parts)
    else:
        prompt_text = f"Welcome to {country} retirement planning."
    
    # Render consolidated box
    box_html = f"""
    <div style="
        padding: 24px;
        border-radius: 12px;
        background: linear-gradient(to bottom right, rgba(255,255,255,0.98), rgba(249,249,249,1));
        border-left: 6px solid {theme['color']};
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
        margin: 20px 0;
    ">
        <!-- Header with Flag -->
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <span style="font-size: 2.5em;">{theme['flag']}</span>
            <div>
                <h3 style="
                    margin: 0;
                    background: {theme['gradient']};
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-size: 1.4em;
                    font-weight: 600;
                ">{country} Retirement Advisory</h3>
                <p style="margin: 4px 0 0 0; color: #666; font-size: 0.9em;">
                    Ask questions about your retirement planning and pension benefits
                </p>
            </div>
        </div>
        
        <!-- Separator -->
        <div style="
            height: 2px;
            background: {theme['gradient']};
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
    st.markdown(box_html, unsafe_allow_html=True)


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimer = POST_ANSWER_DISCLAIMERS.get(country, POST_ANSWER_DISCLAIMERS.get("Australia", "Please verify with official sources."))
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

