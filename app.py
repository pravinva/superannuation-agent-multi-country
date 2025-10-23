# app.py - Complete with Fixed Member Selection & Country Colors
"""
Multi-Country Retirement Advisory Application
Main Streamlit application with two-page navigation
"""

import streamlit as st
import uuid
import os

from config import BRANDCONFIG, MLFLOW_PROD_EXPERIMENT_PATH, ARCHITECTURECONTENT
from ui_components import (
    render_logo, render_member_card, render_question_card,
    render_country_welcome, render_postanswer_disclaimer,
    render_audit_table
)
from progress_utils import render_progress
from audit.audit_utils import get_audit_log
from mlflow_utils import show_mlflow_runs
from agent_processor import agent_query  # Using agent_processor wrapper
from data_utils import get_members_by_country
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS

# Country codes to display names mapping
COUNTRY_CODES = {
    "AU": "Australia",
    "US": "USA",
    "UK": "United Kingdom",
    "IN": "India"
}

# Reverse mapping for display to code
COUNTRY_DISPLAY_TO_CODE = {v: k for k, v in COUNTRY_CODES.items()}

# Display names for dropdown
COUNTRIES = ["Australia", "USA", "United Kingdom", "India"]

# Page configuration
st.set_page_config(
    page_title="Global Retirement Advisory",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Advisory"
if "country_display" not in st.session_state:
    st.session_state.country_display = "Australia"
if "show_logs" not in st.session_state:
    st.session_state.show_logs = True
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
if "current_country_code" not in st.session_state:
    st.session_state.current_country_code = None

# Sidebar navigation
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)

st.sidebar.title(BRANDCONFIG["brand_name"])
st.sidebar.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'))
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "📍 Navigation",
    ["Advisory", "Audit/Governance"],
    key="page_nav"
)

st.sidebar.markdown("---")

# Log toggle with checkbox
st.session_state.show_logs = st.sidebar.checkbox(
    "👀 Show Processing Logs",
    value=st.session_state.show_logs,
    key="log_toggle"
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Session: {st.session_state.session_id[:8]}...")
st.sidebar.caption(f"User: {st.session_state.user_id}")

st.session_state.page = page

# ============================================================================
# PAGE 1: ADVISORY INTERFACE
# ============================================================================

if page == "Advisory":
    render_logo()

    # Country selector with flags as horizontal radio buttons
    st.subheader("🌍 Select Country")

    # Country options with flag emojis
    country_options = {
        "🇦🇺 Australia": "Australia",
        "🇺🇸 USA": "USA",
        "🇬🇧 United Kingdom": "United Kingdom",
        "🇮🇳 India": "India"
    }

    # Radio buttons horizontal
    selected_country_with_flag = st.radio(
        "Choose your country:",
        options=list(country_options.keys()),
        horizontal=True,
        key="country_selector",
        label_visibility="collapsed"
    )

    # Get the country display name without flag
    country_display = country_options[selected_country_with_flag]
    st.session_state.country_display = country_display

    # Convert display name to code for database query
    country_code = COUNTRY_DISPLAY_TO_CODE[country_display]

    st.markdown("---")

    # Consolidated country welcome section
    prompt_text = COUNTRY_PROMPTS.get(country_display, COUNTRY_PROMPTS["Australia"])
    disclaimer = COUNTRY_DISCLAIMERS.get(country_display, COUNTRY_DISCLAIMERS["Australia"])
    render_country_welcome(country_display, prompt_text, disclaimer)

    st.markdown("---")

    # ========================================================================
    # MEMBER SELECTION (FIXED - NO REFRESH, COUNTRY COLORS)
    # ========================================================================
    st.subheader("📋 Select Member Profile")

    # Load members ONCE per country to prevent refresh
    if st.session_state.current_country_code != country_code:
        members_df = get_members_by_country(country_code)
        st.session_state.members_list = members_df.to_dict('records') if not members_df.empty else []
        st.session_state.current_country_code = country_code
        st.session_state.selected_member = None  # Reset selection on country change

    members = st.session_state.members_list

    if not members:
        st.warning(f"⚠️ No members found for {country_display}. Please add members to the database.")
        st.info("Run the SQL scripts in the `sql/` folder to add sample members.")
    else:
        # Display members in a grid WITHOUT causing refresh
        cols = st.columns(min(3, len(members)))

        for idx, member in enumerate(members):
            with cols[idx % 3]:
                member_id = member.get('member_id')
                is_selected = st.session_state.selected_member == member_id

                # Use button with custom styling (no full page reload)
                button_label = f"{'✓ ' if is_selected else ''}Select {member.get('name', 'Unknown')}"

                if st.button(
                    button_label,
                    key=f"select_btn_{member_id}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.selected_member = member_id
                    st.rerun()  # Light rerun to update UI only

                # Render card with country colors and selection highlight
                render_member_card(member, is_selected, country_display)

        # Get currently selected member
        if st.session_state.selected_member:
            member = next(
                (m for m in members if m.get('member_id') == st.session_state.selected_member),
                members[0]
            )
        else:
            # Auto-select first member if none selected
            member = members[0]
            st.session_state.selected_member = member.get('member_id')

        st.markdown("---")

        # Query input
        st.subheader("💬 Ask Your Question")

        # Sample questions for the country
        sample_questions = {
            "Australia": [
                "💰 What's the maximum amount I can withdraw from my superannuation this year?",
                "🎂 At what age can I access my super without restrictions?",
                "🏥 Can I access my super early for medical reasons or financial hardship?"
            ],
            "USA": [
                "💵 How much can I safely withdraw from my 401(k) without facing penalties?",
                "📅 What are the required minimum distributions (RMDs) for my age?",
                "🎓 Can I withdraw from my 401(k) early for education or home purchase?"
            ],
            "United Kingdom": [
                "💷 How much of my pension can I take as a tax-free lump sum?",
                "✈️ Can I transfer my UK pension to another country if I move abroad?",
                "⏰ What are my options for accessing my pension before state pension age?"
            ],
            "India": [
                "💸 What percentage of my EPF can I withdraw before retirement?",
                "🏠 Can I withdraw from my PF for buying a house or medical emergency?",
                "📊 How is my Employees' Pension Scheme (EPS) calculated at retirement?"
            ]
        }

        st.caption("💡 Try these sample questions:")
        cols = st.columns(3)

        for idx, q in enumerate(sample_questions.get(country_display, [])[:3]):
            with cols[idx]:
                if st.button(q, key=f"sample_q_{idx}", use_container_width=True):
                    st.session_state.query_input = q

        question = st.text_input(
            "Your question:",
            placeholder="Type your retirement/pension question here...",
            key="query_input"
        )

        # Get recommendation button
        if st.button("🚀 Get Recommendation", type="primary", use_container_width=True):
            if not question:
                st.warning("Please enter a question first.")
            else:
                with st.spinner("🔄 Processing your request..."):
                    # Show progress message if logs are hidden
                    if not st.session_state.show_logs:
                        progress_placeholder = st.empty()
                        progress_placeholder.info("⏳ Processing your request. Estimated completion: 5-10 seconds.")

                    try:
                        # Call agent_query with real-time progress
                        answer, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called = agent_query(
                            user_id=st.session_state.user_id,
                            country=country_display,
                            query_str=question,
                            extra_context=member,  # Pass full member profile including name
                            session_id=st.session_state.session_id,
                            judge_llm_fn=None,
                            mlflow_experiment_path=None
                        )

                        # Build agent_output dict for compatibility
                        agent_output = {
                            "answer": answer,
                            "citations": citations,
                            "response_dict": response_dict,
                            "judge_response": judge_resp,
                            "judge_verdict": judge_verdict,
                            "error_info": error_info,
                            "tools_called": tools_called,
                            "tool_used": f"{country_display} Calculator"
                        }

                        st.session_state.agent_output = agent_output

                        # Clear progress message
                        if not st.session_state.show_logs:
                            progress_placeholder.empty()

                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                        st.session_state.agent_output = None
                        if not st.session_state.show_logs:
                            progress_placeholder.empty()

        # Show logs IF enabled
        if st.session_state.show_logs:
            member_data = member if st.session_state.agent_output else None
            tools_called = st.session_state.agent_output.get("tools_called", []) if st.session_state.agent_output else []
            render_progress(member_data, tools_called, True)

        # Display results
        if st.session_state.agent_output:
            st.markdown("---")
            st.subheader("📊 Recommendation")

            # Main answer
            st.success(st.session_state.agent_output["answer"])

            # Post-answer disclaimer
            render_postanswer_disclaimer(country_display)

            # Citations
            st.markdown("#### 📚 Citations & References")
            citations = st.session_state.agent_output.get("citations", [])
            if citations:
                for i, cite in enumerate(citations[:3], 1):
                    st.caption(f"[{i}] {cite}")
            else:
                st.caption("No citations available.")

            # Judge validation (if available)
            if st.session_state.agent_output.get("judge_verdict"):
                with st.expander("🔍 Quality Validation Details"):
                    verdict = st.session_state.agent_output["judge_verdict"]
                    if verdict == "Pass":
                        st.success(f"✅ Validation: {verdict}")
                    elif verdict == "ERROR":
                        st.error(f"❌ Validation: {verdict}")
                    else:
                        st.warning(f"⚠️ Validation: {verdict}")

                    if st.session_state.agent_output.get("judge_response"):
                        st.text(st.session_state.agent_output["judge_response"])

# ============================================================================
# PAGE 2: AUDIT/GOVERNANCE & DEVELOPER
# ============================================================================

elif page == "Audit/Governance":
    st.title("🔒 Governance & Developer Tools")

    tab1, tab2 = st.tabs(["🔒 Governance", "🛠️ Developer"])

    # ========================================================================
    # GOVERNANCE TAB
    # ========================================================================
    with tab1:
        st.header("Audit Trail & Compliance")
        st.markdown(f"""
All user interactions are logged to Unity Catalog for compliance and governance.

**Table:** `{ARCHITECTURECONTENT.get('infra_details', 'Unity Catalog governance table')}`
        """)

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_country_display = st.selectbox(
                "Filter by Country",
                ["All"] + COUNTRIES,
                key="audit_country_filter"
            )

        # Convert display name to code if not "All"
        filter_country = None if filter_country_display == "All" else COUNTRY_DISPLAY_TO_CODE.get(filter_country_display)

        with col2:
            filter_user = st.text_input(
                "Filter by User ID",
                placeholder="Leave empty for all",
                key="audit_user_filter"
            )

        with col3:
            filter_session = st.text_input(
                "Filter by Session",
                placeholder="Leave empty for all",
                key="audit_session_filter"
            )

        # Apply filters
        user_filter = filter_user if filter_user else None
        session_filter = filter_session if filter_session else None

        # Retrieve audit logs
        with st.spinner("Loading audit logs..."):
            audit_df = get_audit_log(
                session_id=session_filter,
                user_id=user_filter,
                country=filter_country
            )

        # Display audit table
        render_audit_table(audit_df)

        # Summary metrics
        if not audit_df.empty:
            st.markdown("---")
            st.subheader("📈 Summary Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Queries", len(audit_df))

            with col2:
                total_cost = audit_df['cost'].sum() if 'cost' in audit_df.columns else 0
                st.metric("Total Cost", f"${total_cost:.2f}")

            with col3:
                if 'judge_verdict' in audit_df.columns:
                    pass_count = (audit_df['judge_verdict'] == 'Pass').sum()
                    pass_rate = pass_count / len(audit_df) * 100 if len(audit_df) > 0 else 0
                    st.metric("Pass Rate", f"{pass_rate:.1f}%")
                else:
                    st.metric("Pass Rate", "N/A")

            with col4:
                if 'error_info' in audit_df.columns:
                    error_count = audit_df['error_info'].notna().sum()
                    st.metric("Errors", error_count)
                else:
                    st.metric("Errors", 0)

    # ========================================================================
    # DEVELOPER TAB
    # ========================================================================
    with tab2:
        st.header("MLflow Experiment Tracking & Evaluation")
        st.markdown("""
View MLflow experiment runs and trigger evaluations.
        """)

        # MLflow experiment selector
        exp_type = st.radio(
            "Select Experiment Type",
            ["Production", "Offline Evaluation"],
            horizontal=True,
            key="mlflow_exp_type"
        )

        exp_path = MLFLOW_PROD_EXPERIMENT_PATH if exp_type == "Production" else st.session_state.get("mlflow_offline_path", "/Shared/experiments/offline/retirement-eval")

        st.info(f"📊 Viewing: `{exp_path}`")

        # Display MLflow runs
        with st.spinner("Loading MLflow runs..."):
            show_mlflow_runs(exp_path=exp_path)

        st.markdown("---")

        # Evaluation tools
        st.subheader("🧪 Run Evaluation")

        eval_mode = st.radio(
            "Evaluation Mode",
            ["Online (Single Query)", "Offline (Batch CSV)"],
            key="eval_mode"
        )

        if eval_mode == "Online (Single Query)":
            st.markdown("Test a single query immediately:")
            eval_country_display = st.selectbox("Country", COUNTRIES, key="eval_country")
            eval_query = st.text_input("Query", key="eval_query")

            if st.button("▶️ Run Online Evaluation"):
                if eval_query:
                    st.info("Online evaluation triggered. Check MLflow for results.")
                else:
                    st.warning("Please enter a query.")
        else:  # Offline mode
            st.markdown("""
Run batch evaluation from a CSV file:

**CSV Format:**
```
user_id,country,query_str,age,super_balance
user001,AU,"How much can I withdraw?",65,450000
```

**Command:**
```
python run_evaluation.py --mode offline --csv_path /path/to/eval_data.csv
```
            """)
            st.info("Upload CSV and run evaluation from Databricks notebook or terminal.")

# Footer
st.markdown("---")
st.caption(f"🏦 {BRANDCONFIG['brand_name']} | Session: {st.session_state.session_id[:8]}... | Support: {BRANDCONFIG.get('support_email', 'support@example.com')}")
