# app.py – Multi-Country Retirement Advisory (Final Corrected Version)

import streamlit as st
import uuid
import os

from config import (
    BRANDCONFIG,
    MLFLOW_PROD_EXPERIMENT_PATH,
    ARCHITECTURECONTENT,
    MAIN_LLM_ENDPOINT,
    JUDGE_LLM_ENDPOINT,
    SQL_WAREHOUSE_ID
)

from ui_components import (
    render_logo,
    render_member_card,
    render_question_card,
    render_country_welcome,
    render_postanswer_disclaimer,
    render_audit_table
)

from progress_utils import render_progress
from audit import get_audit_log
from mlflow_utils import show_mlflow_runs
from agent_processor import agent_query
from data_utils import get_members_by_country
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS

# --------------------------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------------------------
st.set_page_config(page_title="Global Retirement Advisory", page_icon="💰", layout="wide")

# Initialize Session State
if "page" not in st.session_state:
    st.session_state.page = "Advisory"
if "country_display" not in st.session_state:
    st.session_state.country_display = "Australia"
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user@example.com"
if "agent_output" not in st.session_state:
    st.session_state.agent_output = None
if "selected_member" not in st.session_state:
    st.session_state.selected_member = None
if "members_list" not in st.session_state:
    st.session_state.members_list = []
if "validation_mode" not in st.session_state:
    st.session_state.validation_mode = "llmjudge"

# --------------------------------------------------------------------
# SIDEBAR CONFIGURATION
# --------------------------------------------------------------------
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)

st.sidebar.title(BRANDCONFIG["brand_name"])
st.sidebar.caption(BRANDCONFIG.get("subtitle", "Enterprise-Grade Agentic AI on Databricks"))
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigation", ["Advisory", "Audit & Governance"], key="page_nav")
st.sidebar.markdown("---")
st.sidebar.caption(f"Session: {st.session_state.session_id[:8]}")
st.sidebar.caption(f"User: {st.session_state.user_id}")

# --------------------------------------------------------------------
# VALIDATION MODE SELECTOR
# --------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Validation Mode")

mode_options = {
    "LLM Judge Only": "llmjudge",
    "Hybrid Fast + Smart": "hybrid",
    "Deterministic Only": "deterministic"
}
selected_mode = st.sidebar.radio("Choose Strategy", options=list(mode_options.keys()), index=0)
st.session_state.validation_mode = mode_options[selected_mode]

# --------------------------------------------------------------------
# ADVISORY PAGE - RETIREMENT QUESTIONS
# --------------------------------------------------------------------
if page == "Advisory":
    render_logo()
    st.subheader("Select Country")

    country_options = {
        "Australia": "Australia",
        "USA": "USA",
        "United Kingdom": "United Kingdom",
        "India": "India"
    }

    selected_country = st.radio(
        "Choose your country",
        options=list(country_options.keys()),
        horizontal=True
    )
    country_display = country_options[selected_country]
    st.session_state.country_display = country_display

    # Retrieve members from Databricks Unity Catalog
    members_df = get_members_by_country(country_display)
    if members_df is not None and not members_df.empty:
        st.session_state.members_list = members_df.to_dict("records")
        st.success(f"Loaded {len(members_df)} members for {country_display}.")
    else:
        st.warning(f"No members available for {country_display}. Run setup scripts.")

    st.markdown("---")
    st.subheader("Ask Your Question")
    question = st.text_input("Your question", placeholder="Type your retirement or pension question here...")

    if st.button("Get Recommendation", type="primary", use_container_width=True):
        if not question:
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Processing your request..."):
                try:
                    result = agent_query(
                        user_id=st.session_state.user_id,
                        country=country_display,
                        query_str=question,
                        extra_context=None,
                        session_id=st.session_state.session_id,
                        validation_mode=st.session_state.validation_mode
                    )
                    st.session_state.agent_output = result
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.agent_output:
        st.markdown("---")
        st.subheader("Recommendation")
        st.success(st.session_state.agent_output[0])

# --------------------------------------------------------------------
# AUDIT & GOVERNANCE PAGE
# --------------------------------------------------------------------
elif page == "Audit & Governance":
    st.title("Governance & Compliance Portal")
    tab1, tab2, tab3 = st.tabs(["Governance Overview", "Audit Logs", "Developer Tools"])

    # --- Tab 1: Governance Overview ---
    with tab1:
        st.markdown("### Governance Overview")
        with st.spinner("Loading governance metrics..."):
            all_audit_df = get_audit_log(limit=1000)

        if all_audit_df is not None and not all_audit_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Queries", len(all_audit_df))
            with col2:
                total_cost = float(all_audit_df["cost"].sum()) if "cost" in all_audit_df.columns else 0.0
                st.metric("Total Cost ($)", f"{total_cost:.2f}")
            with col3:
                if "judge_verdict" in all_audit_df.columns:
                    passed = (all_audit_df["judge_verdict"] == "Pass").sum()
                    pass_rate = (passed / len(all_audit_df)) * 100 if len(all_audit_df) else 0
                    st.metric("Validation Pass Rate", f"{pass_rate:.1f}%")
                else:
                    st.metric("Pass Rate", "N/A")
            with col4:
                if "validation_attempts" in all_audit_df.columns:
                    avg_retry = all_audit_df["validation_attempts"].mean()
                    st.metric("Avg Retry Attempts", f"{avg_retry:.1f}")
                else:
                    st.metric("Avg Retries", "N/A")
        else:
            st.info("No audit data available yet. Run advisory queries first.")

    # --- Tab 2: Audit Logs ---
    with tab2:
        st.markdown("### Query Audit Logs")
        with st.spinner("Loading audit logs..."):
            audit_df = get_audit_log()

        if audit_df is not None and not audit_df.empty:
            st.markdown(f"**{len(audit_df)} Records Found**")
            render_audit_table(audit_df)
        else:
            st.warning("No audit logs found.")

    # --- Tab 3: Developer Tools ---
    with tab3:
        st.markdown("### Developer Tools")
        col1, col2 = st.columns(2)
        with col1:
            st.code(f"Main LLM: {MAIN_LLM_ENDPOINT}\nJudge LLM: {JUDGE_LLM_ENDPOINT}")
        with col2:
            st.code(f"Warehouse: {SQL_WAREHOUSE_ID}")

        st.markdown("---")
        st.markdown("MLflow Experiment")
        col1, col2 = st.columns(2)
        with col1:
            st.code(MLFLOW_PROD_EXPERIMENT_PATH)
        with col2:
            if st.button("View MLflow Runs"):
                try:
                    show_mlflow_runs(exp_path=MLFLOW_PROD_EXPERIMENT_PATH)
                except Exception as e:
                    st.warning(f"MLflow viewer unavailable: {e}")

# --------------------------------------------------------------------
# FOOTER
# --------------------------------------------------------------------
st.markdown("---")
st.caption(f"{BRANDCONFIG['brand_name']} | Session: {st.session_state.session_id[:8]}")

