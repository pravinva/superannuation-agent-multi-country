# ui_components.py
import streamlit as st
from config import NATIONAL_COLORS
from country_content import COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS, COUNTRY_PROMPTS

def render_logo():
    """Render brand logo, subtitle, and title"""
    # Check if logo.png exists in root
    if os.path.exists("logo.png"):
        # Display logo centered
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("logo.png", use_container_width=True)
    
    # Display brand name and subtitle
    st.markdown(f"## 🏦 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'


def render_member_card(member, is_selected, country):
    """Render a member card with country-specific colors"""
    colors = NATIONAL_COLORS.get(country, ["#333", "#FFF"])
    border = "3px solid #0066cc" if is_selected else "1px solid #ddd"
    
    card_html = f"""
    <div style='background: linear-gradient(135deg, {colors[0]} 0%, {colors[1]} 100%); 
                padding: 1.2em; border-radius: 10px; margin-bottom: 1em; 
                border: {border}; color: white; font-weight: bold;'>
        <div style='font-size: 1.2em;'>{member.get('name', 'Unknown')}</div>
        <div style='opacity: 0.9; margin-top: 0.5em;'>
            Age: {member.get('age', 'N/A')} | 
            Status: {member.get('employment_status', 'N/A')} | 
            Balance: ${member.get('super_balance', 0):,.0f}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_question_card(question, country):
    """Render a question with country colors"""
    colors = NATIONAL_COLORS.get(country, ["#333", "#FFF"])
    st.markdown(
        f"<div style='padding: 0.8em; border-radius: 8px; "
        f"background: {colors[0]}; color: white; margin: 0.5em 0;'>"
        f"💬 {question}</div>",
        unsafe_allow_html=True
    )

def render_country_prompt(country):
    """Render country-specific welcome prompts"""
    prompts = COUNTRY_PROMPTS.get(country, ["Welcome!"])
    for prompt in prompts[:2]:  # Show first 2 prompts
        st.info(prompt)

def render_disclaimer(country):
    """Render country-specific disclaimer"""
    disclaimer = COUNTRY_DISCLAIMERS.get(country, "General advice only.")
    st.markdown(f"<small style='color: #666;'>⚠️ {disclaimer}</small>", unsafe_allow_html=True)

def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimer = POST_ANSWER_DISCLAIMERS.get(country, "Please verify with official sources.")
    st.markdown(f"<small style='color: #888; font-size: 0.85em;'>💡 {disclaimer}</small>", unsafe_allow_html=True)

def render_audit_table(audit_df):
    """Render audit log table"""
    if audit_df.empty:
        st.warning("No audit data found.")
        return
    
    # Display key columns
    display_cols = ['timestamp', 'user_id', 'country', 'query_string', 'judge_verdict', 'cost']
    available_cols = [col for col in display_cols if col in audit_df.columns]
    st.dataframe(audit_df[available_cols], use_container_width=True)

