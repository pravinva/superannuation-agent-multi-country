# app.py - COMPLETE VERSION WITH MLFLOW TRACES

"""
Multi-Country Retirement Advisory Application

✅ MLflow traces integration with experiment tracking
✅ Enhanced governance tab with 4 sub-tabs (Governance, MLflow, Tokens, Costs)
✅ Token analysis and cost projections
✅ Safe DataFrame operations
✅ Comprehensive audit logging
"""

import streamlit as st
import uuid
import os
import pandas as pd
import numpy as np
import mlflow
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
    render_audit_table,
    render_enhanced_audit_tab
)

from progress_utils import render_progress, initialize_live_progress_tracker
from audit.audit_utils import get_audit_log
from agent_processor import agent_query
from data_utils import get_members_by_country
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS, POST_ANSWER_DISCLAIMERS

# ============================================================================
# MLFLOW CONFIGURATION
# ============================================================================

def initialize_mlflow():
    """Initialize MLflow tracking"""
    try:
        if MLFLOW_PROD_EXPERIMENT_PATH:
            mlflow.set_experiment(MLFLOW_PROD_EXPERIMENT_PATH)
            print(f"✅ MLflow experiment set: {MLFLOW_PROD_EXPERIMENT_PATH}")
        else:
            print("⚠️ MLFLOW_PROD_EXPERIMENT_PATH not configured")
    except Exception as e:
        print(f"❌ MLflow initialization error: {e}")

# Initialize MLflow on startup
initialize_mlflow()

# ============================================================================
# SAFE DATAFRAME UTILITY FUNCTIONS
# ============================================================================

def safe_dataframe_check(df):
    """Safely check if DataFrame exists and is non-empty"""
    return df is not None and isinstance(df, pd.DataFrame) and not df.empty

def safe_column_sum(df, column_name, default=0):
    """Safely sum a DataFrame column with numeric conversion"""
    if not safe_dataframe_check(df) or column_name not in df.columns:
        return default
    try:
        values = pd.to_numeric(df[column_name], errors='coerce').fillna(0)
        return float(values.sum())
    except (ValueError, TypeError, Exception):
        return default

def safe_value_count(df, column_name, target_value):
    """Safely count occurrences of target_value in column"""
    if not safe_dataframe_check(df) or column_name not in df.columns:
        return 0
    try:
        return (df[column_name] == target_value).sum()
    except (ValueError, TypeError, Exception):
        return 0

def safe_column_mean(df, column_name, default=0):
    """Safely calculate mean of a DataFrame column"""
    if not safe_dataframe_check(df) or column_name not in df.columns:
        return default
    try:
        values = pd.to_numeric(df[column_name], errors='coerce').dropna()
        if len(values) == 0:
            return default
        return float(values.mean())
    except (ValueError, TypeError, Exception):
        return default

def safe_get_column(df, column_name, default_value=None):
    """Safely get a column from DataFrame"""
    if not safe_dataframe_check(df) or column_name not in df.columns:
        return default_value
    return df[column_name]


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


# ============================================================================
# CUSTOM CSS FOR BEAUTIFUL TABS
# ============================================================================

st.markdown("""
    <style>
    /* Beautiful tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 10px 20px;
        background: linear-gradient(135deg, #00843D 0%, #FFD700 100%);
        border-radius: 8px;
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 132, 61, 0.3);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FFD700 0%, #00843D 100%);
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.5);
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
if "mlflow_run_id" not in st.session_state:
    st.session_state.mlflow_run_id = None

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
if st.session_state.mlflow_run_id:
    st.sidebar.caption(f"MLflow Run: {st.session_state.mlflow_run_id[:8]}...")

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

# Show mode explanation
if st.session_state.validation_mode == "llm_judge":
    st.sidebar.info("🎯 Uses LLM for comprehensive quality checks")
elif st.session_state.validation_mode == "hybrid":
    st.sidebar.info("⚡ Fast checks first, then LLM if needed")
else:
    st.sidebar.info("🚀 Rule-based validation only")


# ============================================================================
# PAGE 1: ADVISORY
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
        
        # ✅ FIXED: Use safe DataFrame checking + randomly select 4 members
        if safe_dataframe_check(members_df):
            # Randomly select up to 4 members
            if len(members_df) > 4:
                members_df = members_df.sample(n=4, random_state=None)
            st.session_state.members_list = members_df.to_dict('records')
        else:
            st.session_state.members_list = []
        
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
        
        # ====================================================================
        # QUERY INTERFACE
        # ====================================================================
        
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
                # ✅ Initialize live progress tracker FIRST
                initialize_live_progress_tracker()
                
                # Start MLflow run
                try:
                    mlflow_run = mlflow.start_run(
                        run_name=f"query_{st.session_state.session_id[:8]}"
                    )
                    st.session_state.mlflow_run_id = mlflow_run.info.run_id
                    
                    # Log parameters
                    mlflow.log_param("country", country_display)
                    mlflow.log_param("validation_mode", st.session_state.validation_mode)
                    mlflow.log_param("member_id", member.get('member_id'))
                    mlflow.log_param("session_id", st.session_state.session_id)
                    
                except Exception as e:
                    st.warning(f"MLflow tracking unavailable: {e}")
                    mlflow_run = None
                
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
                        
                        # Log to MLflow
                        if mlflow_run:
                            try:
                                # Log metrics
                                mlflow.log_metric("validation_attempts", 1)
                                mlflow.log_param("judge_verdict", judge_verdict)
                                mlflow.log_metric("pass", 1 if judge_verdict == "Pass" else 0)
                                
                                # Log query and response
                                mlflow.log_text(question, "query.txt")
                                mlflow.log_text(answer, "response.txt")
                                
                                # End run
                                mlflow.end_run()
                                
                            except Exception as e:
                                st.warning(f"MLflow logging error: {e}")
                        
                        if not st.session_state.show_logs:
                            progress_placeholder.empty()
                    
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                        st.session_state.agent_output = None
                        
                        if mlflow_run:
                            mlflow.end_run(status="FAILED")
                        
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


# ============================================================================
# PAGE 2: AUDIT/GOVERNANCE WITH ENHANCED TAB
# ============================================================================

elif page == "Audit/Governance":
    st.title("🔒 Governance & Compliance Portal")
    
    # Use the enhanced audit tab with all 4 sub-tabs
    render_enhanced_audit_tab()
    
    # Footer
    st.markdown("---")
    st.caption(f"🏦 {BRANDCONFIG['brand_name']} | Session: {st.session_state.session_id[:8]}...")
