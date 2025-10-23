# ui_components.py
"""UI components for the retirement advisory app"""

import streamlit as st
import pandas as pd
from config import BRANDCONFIG, NATIONAL_COLORS
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS


def render_logo():
    """Render brand title and subtitle (logo in sidebar)"""
    st.markdown(f"## 🏦 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'))


def render_member_card(member, is_selected=False, country="Australia"):
    """Render a member profile card with native Streamlit components"""
    flags = {"Australia": "🇦🇺", "USA": "🇺🇸", "United Kingdom": "🇬��", "India": "🇮🇳"}
    flag = flags.get(country, "🌍")
    
    balance = member.get('super_balance', 0)
    try:
        balance = float(balance) if balance else 0
    except (ValueError, TypeError):
        balance = 0
    
    if is_selected:
        with st.container():
            st.markdown(f"### {flag} {member.get('name', 'Unknown')} ✓")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Age", member.get('age', 'N/A'))
            with col2:
                st.metric("Status", member.get('employment_status', 'N/A'))
            with col3:
                st.metric("Balance", f"${balance:,.0f}")
            st.caption(f"ID: {member.get('member_id', 'N/A')}")
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
            st.caption(f"ID: {member.get('member_id', 'N/A')}")


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

