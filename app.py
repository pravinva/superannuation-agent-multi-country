# app.py
"""
Multi-Country Retirement Advisory Application
Main Streamlit application with two-page navigation
"""

import streamlit as st
import uuid
from config import BRANDCONFIG, MLFLOW_PROD_EXPERIMENT_PATH, ARCHITECTURECONTENT
from ui_components import (
    render_logo, render_member_card, render_question_card,
    render_country_prompt, render_disclaimer, render_postanswer_disclaimer,
    render_audit_table
)
from progress_utils import render_progress
from audit.audit_utils import get_audit_log
from mlflow_utils import show_mlflow_runs
from agent import run_agent_interaction
from data_utils import get_members_by_country

# Supported countries
COUNTRIES = ["Australia", "USA", "UK", "India"]

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
if "country" not in st.session_state:
    st.session_state.country = "Australia"
if "show_logs" not in st.session_state:
    st.session_state.show_logs = True
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user@example.com"  # Replace with auth in production
if "agent_output" not in st.session_state:
    st.session_state.agent_output = None
if "selected_member" not in st.session_state:
    st.session_state.selected_member = None

# Sidebar navigation
st.sidebar.title(BRANDCONFIG["brand_name"])
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "📍 Navigation",
    ["Advisory", "Audit/Governance"],
    key="page_nav"
)

st.sidebar.markdown("---")

# Log toggle button
log_status = "Hide Logs" if st.session_state.show_logs else "Show Logs"
if st.sidebar.button(f"👁️ {log_status}"):
    st.session_state.show_logs = not st.session_state.show_logs

st.sidebar.markdown("---")
st.sidebar.caption(f"Session: {st.session_state.session_id[:8]}...")
st.sidebar.caption(f"User: {st.session_state.user_id}")

st.session_state.page = page

# ============================================================================
# PAGE 1: ADVISORY INTERFACE
# ============================================================================
if page == "Advisory":
    render_logo()

    # Country selector
    col1, col2 = st.columns([1, 3])
    with col1:
        country = st.selectbox(
            "🌍 Select Country",
            COUNTRIES,
            index=COUNTRIES.index(st.session_state.country),
            key="country_selector"
        )
        st.session_state.country = country

    st.markdown("---")

    # Country-specific prompts and disclaimer
    render_country_prompt(country)
    render_disclaimer(country)

    st.markdown("---")

    # Member selection
    st.subheader("📋 Select Member Profile")

    # Retrieve members from Unity Catalog
    members_df = get_members_by_country(country)

    if members_df.empty:
        st.warning(f"⚠️ No members found for {country}. Please add members to the database.")
        st.info("Run the SQL scripts in the `sql/` folder to add sample members.")
    else:
        members = members_df.to_dict('records')

        # Display members in a grid
        cols = st.columns(min(3, len(members)))
        selected_idx = None

        for idx, member in enumerate(members):
            with cols[idx % 3]:
                is_selected = st.session_state.selected_member == member.get('member_id')
                if st.button(
                    f"Select {member.get('name', 'Unknown')}",
                    key=f"member_{idx}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.selected_member = member.get('member_id')
                    selected_idx = idx

                render_member_card(member, is_selected, country)

        # Get currently selected member
        if st.session_state.selected_member:
            member = next(
                (m for m in members if m.get('member_id') == st.session_state.selected_member),
                members[0]
            )
        else:
            member = members[0]
            st.session_state.selected_member = member.get('member_id')

        st.markdown("---")

        # Query input
        st.subheader("💬 Ask Your Question")

        # Sample questions for the country
        sample_questions = {
            "Australia": [
                "How much can I withdraw from my super?",
                "What are my preservation age rules?",
                "Can I access my super early?"
            ],
            "USA": [
                "What's my 401(k) distribution amount?",
                "When can I withdraw without penalty?",
                "How much is my required minimum distribution?"
            ],
            "UK": [
                "What are my pension withdrawal options?",
                "Can I transfer my pension overseas?",
                "What's my tax-free lump sum?"
            ],
            "India": [
                "How much can I withdraw from EPF?",
                "What are my PF withdrawal rules?",
                "Can I withdraw before retirement?"
            ]
        }

        st.caption("💡 Sample questions:")
        cols = st.columns(3)
        for idx, q in enumerate(sample_questions.get(country, [])[:3]):
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
                    try:
                        agent_output = run_agent_interaction(
                            user_id=st.session_state.user_id,
                            country=country,
                            query_str=question,
                            extra_context=member,
                            session_id=st.session_state.session_id
                        )
                        st.session_state.agent_output = agent_output
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        st.session_state.agent_output = None

        # Show logs/progress
        render_progress(st.session_state.show_logs)

        # Display results
        if st.session_state.agent_output:
            st.markdown("---")
            st.subheader("📊 Recommendation")

            # Main answer
            st.success(st.session_state.agent_output["answer"])

            # Post-answer disclaimer
            render_postanswer_disclaimer(country)

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
            filter_country = st.selectbox(
                "Filter by Country",
                ["All"] + COUNTRIES,
                key="audit_country_filter"
            )
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
        country_filter = None if filter_country == "All" else filter_country
        user_filter = filter_user if filter_user else None
        session_filter = filter_session if filter_session else None

        # Retrieve audit logs
        with st.spinner("Loading audit logs..."):
            audit_df = get_audit_log(
                session_id=session_filter,
                user_id=user_filter,
                country=country_filter
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
                    pass_rate = (audit_df['judge_verdict'] == 'Pass').sum() / len(audit_df) * 100
                    st.metric("Pass Rate", f"{pass_rate:.1f}%")
            with col4:
                if 'error_info' in audit_df.columns:
                    error_count = (audit_df['error_info'] != '').sum()
                    st.metric("Errors", error_count)

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
            eval_country = st.selectbox("Country", COUNTRIES, key="eval_country")
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
            user001,Australia,"How much can I withdraw?",65,450000
            ```

            **Command:**
            ```bash
            python run_evaluation.py --mode offline --csv_path /path/to/eval_data.csv
            ```
            """)

            st.info("Upload CSV and run evaluation from Databricks notebook or terminal.")

# Footer
st.markdown("---")
st.caption(f"🏦 {BRANDCONFIG['brand_name']} | Session: {st.session_state.session_id[:8]}... | Support: {BRANDCONFIG['support_email']}")
