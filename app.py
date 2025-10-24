# app.py - COMPLETE FIXED VERSION WITH WIDE TABS
"""
Multi-Country Retirement Advisory Application
✅ FIXED: ValueError on cost metric
✅ FIXED: Australia filter
✅ ADDED: 3 sleek tabs (Governance | Audit | Developer)
✅ ADDED: Wide tabs CSS for better UX
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

# ✅ WIDE TABS CSS - Makes tabs fill horizontal space and look sleeker
st.markdown("""
<style>
    /* Make tabs fill full width and look sleeker */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        width: 100%;
    }
    
    .stTabs [data-baseweb="tab"] {
        flex-grow: 1;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 6px 6px 0px 0px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 600;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e6e9ef;
        border-color: #4169e1;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-color: #4169e1;
        border-bottom: 2px solid #ffffff;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

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

st.session_state.page = page

# ============================================================================
# ADVISORY PAGE
# ============================================================================

if page == "Advisory":
    render_logo()
    st.markdown("---")
    
    # Country selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("🌍 Select Country")
        country_display = st.selectbox(
            "Country",
            COUNTRIES,
            key="country_select",
            label_visibility="collapsed"
        )
        st.session_state.country_display = country_display
    
    with col2:
        render_country_welcome(country_display)
    
    st.markdown("---")
    
    # Load members when country changes
    country_code = COUNTRY_DISPLAY_TO_CODE.get(country_display, "AU")
    
    if st.session_state.current_country_code != country_code:
        st.session_state.current_country_code = country_code
        st.session_state.members_list = get_members_by_country(country_code)
        st.session_state.selected_member = None
    
    # Member selection
    st.subheader("👤 Select Member")
    
    if not st.session_state.members_list:
        st.warning(f"No members found for {country_display}")
    else:
        # Display members in grid
        cols = st.columns(4)
        for idx, member in enumerate(st.session_state.members_list):
            with cols[idx % 4]:
                is_selected = (st.session_state.selected_member == member['member_id'])
                
                if st.button(
                    f"{'✅ ' if is_selected else ''}{member['name']}",
                    key=f"member_{member['member_id']}",
                    use_container_width=True
                ):
                    st.session_state.selected_member = member['member_id']
                    st.rerun()
                
                # Show card
                render_member_card(member, is_selected, country_display)
    
    st.markdown("---")
    
    # Query input and execution
    if st.session_state.selected_member:
        selected_member_data = next(
            (m for m in st.session_state.members_list if m['member_id'] == st.session_state.selected_member),
            None
        )
        
        if selected_member_data:
            st.subheader("💬 Ask a Question")
            
            # Show example questions
            with st.expander("📝 Example Questions", expanded=False):
                render_question_card(country_display)
            
            user_query = st.text_area(
                "Your question:",
                height=100,
                placeholder=f"e.g., How much tax will I pay if I withdraw $50,000 from my retirement account?"
            )
            
            col1, col2, col3 = st.columns([2, 2, 6])
            
            with col1:
                validation_mode = st.selectbox(
                    "Validation Mode",
                    ["llm_judge", "hybrid", "deterministic"],
                    index=0
                )
            
            with col2:
                if st.button("🚀 Get Recommendation", type="primary", use_container_width=True):
                    if not user_query.strip():
                        st.warning("Please enter a question")
                    else:
                        with st.spinner("Processing your query..."):
                            try:
                                # Call agent
                                answer, citations, response_dict, judge_resp, judge_verdict, error_info, tools_called = agent_query(
                                    user_id=st.session_state.user_id,
                                    country=country_display,
                                    query_str=user_query,
                                    extra_context=selected_member_data,
                                    session_id=st.session_state.session_id,
                                    validation_mode=validation_mode
                                )
                                
                                # Store output
                                st.session_state.agent_output = {
                                    "answer": answer,
                                    "citations": citations,
                                    "response_dict": response_dict,
                                    "judge_response": judge_resp,
                                    "judge_verdict": judge_verdict,
                                    "error_info": error_info,
                                    "tools_called": tools_called,
                                    "member_name": selected_member_data['name']
                                }
                                
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                                import traceback
                                st.code(traceback.format_exc())
            
            # Display results
            if st.session_state.agent_output:
                output = st.session_state.agent_output
                
                st.markdown("---")
                st.subheader("📋 Personalized Recommendation")
                
                # Show answer
                st.markdown(output["answer"])
                
                # Show citations
                if output.get("citations"):
                    with st.expander("📚 Authoritative Citations", expanded=False):
                        for idx, citation in enumerate(output["citations"], 1):
                            if isinstance(citation, dict):
                                st.markdown(f"**{idx}.** {citation.get('text', citation)}")
                                if citation.get('url'):
                                    st.markdown(f"   🔗 [{citation['url']}]({citation['url']})")
                            else:
                                st.markdown(f"**{idx}.** {citation}")
                
                # Show validation
                if output.get("judge_verdict"):
                    verdict = output["judge_verdict"]
                    if verdict == "Pass":
                        st.success(f"✅ Validation: {verdict}")
                    elif verdict == "ERROR":
                        st.error(f"❌ Validation: {verdict}")
                    else:
                        st.warning(f"⚠️ Validation: {verdict}")
                
                # Show tools called
                if output.get("tools_called"):
                    with st.expander("🔧 Tools Called", expanded=False):
                        for tool in output["tools_called"]:
                            st.markdown(f"- **{tool.get('name', 'Unknown')}** ({tool.get('duration', 0):.2f}s)")
                
                # Show disclaimer
                render_postanswer_disclaimer(country_display)
    
    else:
        st.info("👆 Please select a member to continue")

# ============================================================================
# AUDIT/GOVERNANCE PAGE
# ============================================================================

elif page == "Audit/Governance":
    render_logo()
    st.markdown("---")
    
    # ✅ FIXED: 3 sleek tabs
    tab1, tab2, tab3 = st.tabs(["📊 Governance Overview", "📋 Audit Logs", "🛠️ Developer Tools"])
    
    # TAB 1: Governance Overview
    with tab1:
        st.subheader("📊 Governance Dashboard")
        
        # ✅ FIXED: Added limit parameter
        try:
            all_audit_df = get_audit_log(limit=1000)
            
            if all_audit_df.empty:
                st.info("No audit records found")
            else:
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Queries", len(all_audit_df))
                
                with col2:
                    # ✅ FIXED: Convert cost to float before sum
                    total_cost = sum([
                        float(cost) if isinstance(cost, (int, float, str)) and str(cost).replace('.', '').isdigit() 
                        else 0.0 
                        for cost in all_audit_df.get('cost', [0.0])
                    ])
                    st.metric("Total Cost", f"${total_cost:.2f}")
                
                with col3:
                    pass_rate = (all_audit_df['judge_verdict'] == 'Pass').sum() / len(all_audit_df) * 100 if len(all_audit_df) > 0 else 0
                    st.metric("Pass Rate", f"{pass_rate:.1f}%")
                
                with col4:
                    countries = all_audit_df['country'].nunique()
                    st.metric("Countries", countries)
                
                # Country filter
                st.markdown("---")
                st.subheader("Filter by Country")
                
                # ✅ FIXED: Use display names for filter
                filter_country = st.selectbox(
                    "Select Country",
                    ["All"] + COUNTRIES,
                    key="gov_country_filter"
                )
                
                if filter_country == "All":
                    filtered_df = all_audit_df
                else:
                    # ✅ FIXED: Filter by display name, not country code
                    filtered_df = all_audit_df[all_audit_df['country'] == filter_country]
                
                st.dataframe(filtered_df, use_container_width=True, height=400)
        
        except Exception as e:
            st.error(f"Error loading governance data: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    # TAB 2: Audit Logs
    with tab2:
        st.subheader("📋 Detailed Audit Logs")
        
        try:
            audit_df = get_audit_log(limit=100)
            
            if audit_df.empty:
                st.info("No audit logs found")
            else:
                # Show table
                render_audit_table(audit_df)
        
        except Exception as e:
            st.error(f"Error loading audit logs: {str(e)}")
    
    # TAB 3: Developer Tools
    with tab3:
        st.subheader("🛠️ Developer Tools")
        
        # System info
        st.markdown("### System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**LLM Endpoints:**")
            st.code(f"Main: {MAIN_LLM_ENDPOINT}")
            st.code(f"Judge: {JUDGE_LLM_ENDPOINT}")
        
        with col2:
            st.markdown("**Infrastructure:**")
            st.code(f"Warehouse: {SQL_WAREHOUSE_ID}")
            if MLFLOW_PROD_EXPERIMENT_PATH:
                st.code(f"MLflow: {MLFLOW_PROD_EXPERIMENT_PATH}")
        
        st.markdown("---")
        
        # UC Functions check
        st.markdown("### Unity Catalog Functions")
        
        functions_info = {
            "Australia": ["au_calculate_tax", "au_check_pension_impact", "au_project_balance"],
            "USA": ["us_calculate_tax", "us_check_social_security", "us_project_401k"],
            "United Kingdom": ["uk_calculate_tax", "uk_check_state_pension", "uk_project_pension"],
            "India": ["in_calculate_epf_tax", "in_calculate_nps", "in_project_retirement"]
        }
        
        for country, functions in functions_info.items():
            with st.expander(f"🌍 {country} Functions ({len(functions)})", expanded=False):
                for func in functions:
                    st.markdown(f"✅ `super_advisory_demo.pension_calculators.{func}`")
        
        st.markdown("---")
        
        # MLflow runs
        if MLFLOW_PROD_EXPERIMENT_PATH:
            st.markdown("### MLflow Experiment Tracking")
            show_mlflow_runs(MLFLOW_PROD_EXPERIMENT_PATH)
        
        st.markdown("---")
        
        # Debug info
        with st.expander("🐛 Debug Information", expanded=False):
            st.json({
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "current_page": st.session_state.page,
                "selected_country": st.session_state.country_display,
                "selected_member": st.session_state.selected_member
            })
