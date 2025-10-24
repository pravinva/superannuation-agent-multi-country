# app.py - COMPLETE FIXED VERSION
"""
Multi-Country Retirement Advisory Application
✅ FIXED: ValueError on cost metric
✅ FIXED: Australia filter
✅ ADDED: 3 sleek tabs (Governance | Audit | Developer)
✅ IMPROVED: Better UX throughout
"""

import streamlit as st
import uuid
import os

from config import BRANDCONFIG, MLFLOW_PROD_EXPERIMENT_PATH, ARCHITECTURECONTENT, MAIN_LLM_ENDPOINT, JUDGE_LLM_ENDPOINT, SQL_WAREHOUSE_ID
from ui_components import (
    render_logo, render_member_card, render_question_card,
    render_country_welcome, render_postanswer_disclaimer,
    render_audit_table
)
from progress_utils import render_progress
from audit.audit_utils import get_audit_log
from mlflow_utils import show_mlflow_runs
from agent_processor import agent_query
from data_utils import get_members_by_country
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS

# Country codes to display names mapping
COUNTRY_CODES = {
    "AU": "Australia",
    "US": "USA",
    "UK": "United Kingdom",
    "IN": "India"
}

# Reverse mapping
COUNTRY_DISPLAY_TO_CODE = {v: k for k, v in COUNTRY_CODES.items()}

# Display names
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

# Sidebar
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

st.session_state.show_logs = st.sidebar.checkbox(
    "👀 Show Processing Logs",
    value=st.session_state.show_logs,
    key="log_toggle"
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Session: {st.session_state.session_id[:8]}...")
st.sidebar.caption(f"User: {st.session_state.user_id}")

st.session_state.page = page

# Validation mode selector
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Validation Mode")

if "validation_mode" not in st.session_state:
    st.session_state.validation_mode = "llm_judge"

mode_options = {
    "🎯 LLM Judge Only": "llm_judge",
    "⚡ Hybrid (Fast + Smart)": "hybrid", 
    "🚀 Deterministic Only": "deterministic"
}

selected = st.sidebar.radio(
    "Choose strategy:",
    options=list(mode_options.keys()),
    index=0
)

st.session_state.validation_mode = mode_options[selected]

# ============================================================================
# PAGE 1: ADVISORY INTERFACE
# ============================================================================

if page == "Advisory":
    render_logo()

    st.subheader("🌍 Select Country")

    country_options = {
        "🇦🇺 Australia": "Australia",
        "🇺🇸 USA": "USA",
        "🇬🇧 United Kingdom": "United Kingdom",
        "🇮🇳 India": "India"
    }

    selected_country_with_flag = st.radio(
        "Choose your country:",
        options=list(country_options.keys()),
        horizontal=True,
        key="country_selector",
        label_visibility="collapsed"
    )

    country_display = country_options[selected_country_with_flag]
    st.session_state.country_display = country_display

    country_code = COUNTRY_DISPLAY_TO_CODE[country_display]

    st.markdown("---")

    prompt_text = COUNTRY_PROMPTS.get(country_display, COUNTRY_PROMPTS["Australia"])
    disclaimer = COUNTRY_DISCLAIMERS.get(country_display, COUNTRY_DISCLAIMERS["Australia"])
    render_country_welcome(country_display, prompt_text, disclaimer)

    st.markdown("---")

    # ========================================================================
    # MEMBER SELECTION
    # ========================================================================
    st.subheader("📋 Select Member Profile")

    # Load members ONCE per country
    if st.session_state.current_country_code != country_code:
        members_df = get_members_by_country(country_code)
        st.session_state.members_list = members_df.to_dict('records') if not members_df.empty else []
        st.session_state.current_country_code = country_code
        st.session_state.selected_member = None

    members = st.session_state.members_list

    if not members:
        st.warning(f"⚠️ No members found for {country_display}.")
        st.info("Run SQL scripts to add members.")
    else:
        # Display in grid
        cols = st.columns(min(3, len(members)))

        for idx, member in enumerate(members):
            with cols[idx % 3]:
                member_id = member.get('member_id')
                is_selected = (st.session_state.selected_member == member_id)

                button_type = "primary" if is_selected else "secondary"
                button_label = f"{'✓ ' if is_selected else ''}Select {member.get('name', 'Unknown')}"

                if st.button(
                    button_label,
                    key=f"btn_{member_id}_{country_code}",
                    use_container_width=True,
                    type=button_type
                ):
                    st.session_state.selected_member = member_id
                    st.rerun()

                render_member_card(member, is_selected, country_display)

        # Get selected member
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

        # Get recommendation
        if st.button("🚀 Get Recommendation", type="primary", use_container_width=True):
            if not question:
                st.warning("Please enter a question first.")
            else:
                with st.spinner("🔄 Processing your request..."):
                    if not st.session_state.show_logs:
                        progress_placeholder = st.empty()
                        progress_placeholder.info("⏳ Processing your request. Estimated completion: 5-10 seconds.")

                    try:
                        answer, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called = agent_query(
                            user_id=st.session_state.user_id,
                            country=country_display,
                            query_str=question,
                            extra_context=member,
                            session_id=st.session_state.session_id,
                            judge_llm_fn=None,
                            mlflow_experiment_path=None,
                            validation_mode=st.session_state.validation_mode
                        )

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

                        if not st.session_state.show_logs:
                            progress_placeholder.empty()

                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                        st.session_state.agent_output = None
                        if not st.session_state.show_logs:
                            progress_placeholder.empty()

        # Show logs if enabled
        if st.session_state.show_logs:
            member_data = member if st.session_state.agent_output else None
            tools_called = st.session_state.agent_output.get("tools_called", []) if st.session_state.agent_output else []
            render_progress(member_data, tools_called, True)

        # Display results
        if st.session_state.agent_output:
            st.markdown("---")
            st.subheader("📊 Recommendation")

            st.success(st.session_state.agent_output["answer"])

            render_postanswer_disclaimer(country_display)

            st.markdown("#### 📚 Citations & References")
            citations = st.session_state.agent_output.get("citations", [])
            if citations:
                for i, cite in enumerate(citations[:3], 1):
                    st.caption(f"[{i}] {cite}")
            else:
                st.caption("No citations available.")

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
# PAGE 2: AUDIT/GOVERNANCE - COMPLETE REWRITE WITH 3 TABS
# ============================================================================

elif page == "Audit/Governance":
    st.title("🔒 Governance & Compliance Portal")
    
    # ✅ FIX 3: Create 3 sleek horizontal tabs
    tab1, tab2, tab3 = st.tabs(["📊 Governance Overview", "🔍 Audit Logs", "👨‍💻 Developer Tools"])
    
    # ========================================================================
    # TAB 1: GOVERNANCE OVERVIEW
    # ========================================================================
    with tab1:
        st.markdown("## 📊 Governance Overview")
        st.caption("High-level metrics and compliance monitoring")
        
        # Quick stats
        with st.spinner("Loading governance metrics..."):
            all_audit_df = get_audit_log(limit=1000)
        
        if not all_audit_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Queries", len(all_audit_df))
            
            with col2:
                # ✅ FIX 1: Convert cost to float before formatting
                total_cost = all_audit_df['cost'].sum() if 'cost' in all_audit_df.columns else 0
                try:
                    total_cost = float(total_cost)
                except (ValueError, TypeError):
                    total_cost = 0.0
                st.metric("Total Cost", f"${total_cost:.2f}")
            
            with col3:
                if 'judge_verdict' in all_audit_df.columns:
                    pass_count = (all_audit_df['judge_verdict'] == 'Pass').sum()
                    pass_rate = pass_count / len(all_audit_df) * 100 if len(all_audit_df) > 0 else 0
                    st.metric("Validation Pass Rate", f"{pass_rate:.1f}%")
                else:
                    st.metric("Pass Rate", "N/A")
            
            with col4:
                if 'validation_attempts' in all_audit_df.columns:
                    avg_attempts = all_audit_df['validation_attempts'].mean()
                    st.metric("Avg Retry Attempts", f"{avg_attempts:.1f}")
                else:
                    st.metric("Avg Retries", "N/A")
            
            # Queries by country
            st.markdown("---")
            st.markdown("### 🌍 Queries by Country")
            
            if 'country' in all_audit_df.columns:
                country_counts = all_audit_df['country'].value_counts()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.bar_chart(country_counts)
                
                with col2:
                    for country, count in country_counts.items():
                        st.metric(country, count)
            
            # Validation mode usage
            st.markdown("---")
            st.markdown("### ⚖️ Validation Modes Used")
            
            if 'validation_mode' in all_audit_df.columns:
                mode_counts = all_audit_df['validation_mode'].value_counts()
                
                col1, col2, col3 = st.columns(3)
                
                modes = list(mode_counts.items())
                if len(modes) > 0:
                    with col1:
                        st.metric(modes[0][0].replace('_', ' ').title(), modes[0][1])
                if len(modes) > 1:
                    with col2:
                        st.metric(modes[1][0].replace('_', ' ').title(), modes[1][1])
                if len(modes) > 2:
                    with col3:
                        st.metric(modes[2][0].replace('_', ' ').title(), modes[2][1])
            
            # Recent activity
            st.markdown("---")
            st.markdown("### 🕐 Recent Activity")
            
            recent_cols = ['timestamp', 'country', 'query_string', 'judge_verdict']
            available_cols = [col for col in recent_cols if col in all_audit_df.columns]
            recent_df = all_audit_df.head(10)[available_cols]
            st.dataframe(recent_df, use_container_width=True, hide_index=True)
        
        else:
            st.info("No audit data available yet. Process some queries to see governance metrics.")
    
    # ========================================================================
    # TAB 2: AUDIT LOGS (Existing functionality with fixes)
    # ========================================================================
    with tab2:
        st.markdown("## 🔍 Query Audit Logs")
        st.caption("Detailed logs of all retirement advisory queries")
        
        # Filters
        st.markdown("### 🔎 Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_country_display = st.selectbox(
                "Filter by Country",
                ["All"] + COUNTRIES,
                key="audit_country_filter"
            )
        
        # ✅ FIX 2: Use display name directly, don't convert to code
        filter_country = None if filter_country_display == "All" else filter_country_display
        
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
        
        user_filter = filter_user if filter_user else None
        session_filter = filter_session if filter_session else None
        
        # Load filtered audit logs
        with st.spinner("Loading audit logs..."):
            audit_df = get_audit_log(
                session_id=session_filter,
                user_id=user_filter,
                country=filter_country
            )
        
        # Display audit table
        if not audit_df.empty:
            st.markdown(f"### 📋 {len(audit_df)} Records Found")
            render_audit_table(audit_df)
            
            # Summary metrics for filtered data
            st.markdown("---")
            st.markdown("### 📈 Filtered Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Queries", len(audit_df))
            
            with col2:
                # ✅ FIX 1: Convert cost to float
                total_cost = audit_df['cost'].sum() if 'cost' in audit_df.columns else 0
                try:
                    total_cost = float(total_cost)
                except (ValueError, TypeError):
                    total_cost = 0.0
                st.metric("Total Cost", f"${total_cost:.2f}")
            
            with col3:
                if 'judge_verdict' in audit_df.columns:
                    pass_count = (audit_df['judge_verdict'] == 'Pass').sum()
                    pass_rate = pass_count / len(audit_df) * 100 if len(audit_df) > 0 else 0
                    st.metric("Pass Rate", f"{pass_rate:.1f}%")
                else:
                    st.metric("Pass Rate", "N/A")
            
            with col4:
                if 'total_time_seconds' in audit_df.columns:
                    avg_time = audit_df['total_time_seconds'].mean()
                    st.metric("Avg Time", f"{avg_time:.1f}s")
                else:
                    st.metric("Avg Time", "N/A")
        else:
            st.warning("No audit logs found matching the filters.")
            st.info("💡 **Tip:** Try removing some filters or selecting 'All' for country.")
    
    # ========================================================================
    # TAB 3: DEVELOPER TOOLS (NEW!)
    # ========================================================================
    with tab3:
        st.markdown("## 👨‍💻 Developer Tools")
        st.caption("Technical utilities and system information")
        
        # System info
        st.markdown("### ⚙️ System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🤖 LLM Endpoints**")
            st.code(f"""
Main LLM: {MAIN_LLM_ENDPOINT}
Judge LLM: {JUDGE_LLM_ENDPOINT}
            """)
        
        with col2:
            st.markdown("**🗄️ Data Sources**")
            st.code(f"""
Warehouse: {SQL_WAREHOUSE_ID[:20]}...
Catalog: super_advisory_demo
Schema: pension_calculators
            """)
        
        # UC Functions status
        st.markdown("---")
        st.markdown("### 🔧 Unity Catalog Functions")
        
        if st.button("🔍 Check UC Functions Status"):
            with st.spinner("Checking UC functions..."):
                try:
                    from databricks.sdk import WorkspaceClient
                    w = WorkspaceClient()
                    
                    # Try to list functions
                    query = "SHOW FUNCTIONS IN super_advisory_demo.pension_calculators"
                    statement = w.statement_execution.execute_statement(
                        warehouse_id=SQL_WAREHOUSE_ID,
                        statement=query,
                        wait_timeout="10s"
                    )
                    
                    st.success("✅ UC Functions schema exists!")
                    
                    # Show function count
                    if statement.result and statement.result.data_array:
                        function_count = len(statement.result.data_array)
                        st.metric("Functions Deployed", function_count)
                        
                        # Expected: 12 functions (3 per country × 4 countries)
                        if function_count == 12:
                            st.success("✅ All 12 functions deployed correctly!")
                        else:
                            st.warning(f"⚠️ Expected 12 functions, found {function_count}")
                    
                except Exception as e:
                    st.error(f"❌ Error checking UC functions: {e}")
                    st.info("💡 Make sure you've run the SQL deployment scripts.")
        
        # MLflow integration
        st.markdown("---")
        st.markdown("### 📊 MLflow Integration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Experiment Path**")
            st.code(MLFLOW_PROD_EXPERIMENT_PATH)
        
        with col2:
            if st.button("🔗 View MLflow Runs"):
                st.info("Opening MLflow UI...")
                try:
                    show_mlflow_runs(exp_path=MLFLOW_PROD_EXPERIMENT_PATH)
                except:
                    st.warning("MLflow viewer not available")
        
        # Session debug info
        st.markdown("---")
        st.markdown("### 🐛 Session Debug Info")
        
        with st.expander("View Session State", expanded=False):
            debug_info = {
                "session_id": st.session_state.get("session_id", "N/A"),
                "user_id": st.session_state.get("user_id", "N/A"),
                "country": st.session_state.get("country_display", "N/A"),
                "show_logs": st.session_state.get("show_logs", "N/A"),
                "validation_mode": st.session_state.get("validation_mode", "N/A"),
                "has_agent_output": st.session_state.get("agent_output") is not None
            }
            st.json(debug_info)
        
        # Clear cache button
        st.markdown("---")
        if st.button("🗑️ Clear All Caches"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ All caches cleared!")
            st.rerun()

# Footer
st.markdown("---")
st.caption(f"🏦 {BRANDCONFIG['brand_name']} | Session: {st.session_state.session_id[:8]}... | Support: {BRANDCONFIG.get('support_email', 'support@example.com')}")
