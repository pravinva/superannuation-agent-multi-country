import streamlit as st
import uuid
import os
import pandas as pd
from config import BRANDCONFIG
from ui_components import (
    render_logo,
    render_member_card,
    render_country_welcome,
    render_postanswer_disclaimer,
    render_validation_results,
    render_enhanced_audit_tab,
    render_mlflow_traces_tab,
    render_cost_analysis_tab,
    render_configuration_tab
)
from progress_utils import initialize_live_progress_tracker
from agent_processor import agent_query
from data_utils import get_members_by_country
from country_content import COUNTRY_PROMPTS, COUNTRY_DISCLAIMERS

# ============================================================================ #
# CONFIGURATION & SESSION SETUP
# ============================================================================ #

st.set_page_config(
    page_title="Global Retirement Advisory",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session state initialization
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
if "current_country_code" not in st.session_state:
    st.session_state.current_country_code = None
if "validation_mode" not in st.session_state:
    st.session_state.validation_mode = "llm_judge"

# Country mappings
COUNTRY_CODES = {"AU": "Australia", "US": "USA", "UK": "United Kingdom", "IN": "India"}
COUNTRY_DISPLAY_TO_CODE = {v: k for k, v in COUNTRY_CODES.items()}

# Safe DataFrame utility
def safe_dataframe_check(df):
    return df is not None and isinstance(df, pd.DataFrame) and not df.empty

# ============================================================================ #
# SIDEBAR
# ============================================================================ #

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
st.sidebar.title(BRANDCONFIG["brand_name"])
st.sidebar.caption(BRANDCONFIG.get("subtitle", "Enterprise-Grade Agentic AI on Databricks"))
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "📍 Navigation",
    ["Advisory", "Governance"],
    key="page_nav"
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Validation Mode")

mode_options = {
    "🎯 LLM Judge Only": "llm_judge",
    "⚡ Hybrid (Fast + Smart)": "hybrid",
    "🚀 Deterministic Only": "deterministic",
}

selected = st.sidebar.radio("Choose strategy:", options=list(mode_options.keys()), index=0)
st.session_state.validation_mode = mode_options[selected]

# ============================================================================ #
# ADVISORY PAGE
# ============================================================================ #

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
        label_visibility="collapsed",
    )
    
    country_display = country_options[selected_country_with_flag]
    st.session_state.country_display = country_display
    country_code = COUNTRY_DISPLAY_TO_CODE[country_display]
    
    st.markdown("---")
    
    render_country_welcome(
        country_display,
        COUNTRY_PROMPTS.get(country_display, COUNTRY_PROMPTS["Australia"]),
        COUNTRY_DISCLAIMERS.get(country_display, COUNTRY_DISCLAIMERS["Australia"]),
    )
    
    st.markdown("---")
    st.subheader("📋 Select Member Profile")
    
    if st.session_state.current_country_code != country_code:
        members_df = get_members_by_country(country_code)
        if safe_dataframe_check(members_df):
            if len(members_df) > 4:
                members_df = members_df.sample(n=4, random_state=None)
            st.session_state.members_list = members_df.to_dict("records")
        else:
            st.session_state.members_list = []
        st.session_state.current_country_code = country_code
        st.session_state.selected_member = None
    
    members = st.session_state.members_list
    
    if not members:
        st.warning(f"⚠️ No members found for {country_display}.")
    else:
        cols = st.columns(min(3, len(members)))
        for idx, member in enumerate(members):
            with cols[idx % 3]:
                member_id = member.get('member_id')
                is_selected = (st.session_state.selected_member == member_id)
                button_type = "primary" if is_selected else "secondary"
                button_label = f"{'✓ ' if is_selected else ''}Select {member.get('name','Unknown')}"
                
                if st.button(button_label, key=f"btn_{member_id}_{country_code}", use_container_width=True, type=button_type):
                    st.session_state.selected_member = member_id
                    st.rerun()
                
                render_member_card(member, is_selected, country_display)
    
    if st.session_state.selected_member:
        member = next((m for m in members if m.get('member_id') == st.session_state.selected_member), members[0] if members else {})
    else:
        member = members[0] if members else {}
    
    if member:
        st.session_state.selected_member = member.get('member_id')
    
    st.markdown("---")
    st.subheader("💬 Ask Your Question")
    
    sample_questions = {
        "Australia": [
            "💰 What's the maximum amount I can withdraw from my superannuation this year?",
            "🎂 At what age can I access my super without restrictions?",
            "🏥 Can I access my super early for medical reasons or financial hardship?"
        ],
        "USA": [
            "💵 How much can I withdraw from my 401(k) without penalties?",
            "📅 What are required minimum distributions (RMDs)?",
            "🎓 Can I withdraw from my 401(k) early for education?"
        ],
        "United Kingdom": [
            "💷 How much of my pension can I take tax-free?",
            "✈️ Can I transfer my UK pension abroad?",
            "⏰ How can I access my pension before state age?"
        ],
        "India": [
            "💸 What percentage of my EPF can I withdraw before retirement?",
            "🏠 Can I withdraw PF for housing?",
            "📊 How is my EPS calculated?"
        ]
    }
    
    st.caption("💡 Try these sample questions:")
    cols = st.columns(3)
    for i, q in enumerate(sample_questions.get(country_display, [])):
        with cols[i]:
            if st.button(q, key=f"sample_q_{i}", use_container_width=True):
                st.session_state.query_input = q
    
    question = st.text_input("Your question:", key="query_input")
    
    if st.button("🚀 Get Recommendation", type="primary", use_container_width=True):
        if not question:
            st.warning("Please enter a question first.")
        elif not st.session_state.selected_member:
            st.warning("Please select a member profile first.")
        else:
            # ✅ Initialize live progress BEFORE starting the query
            initialize_live_progress_tracker()
            
            with st.spinner("🔄 Processing your request..."):
                try:
                    # ✅ FIXED: agent_query now returns a dictionary, not 7 separate values
                    result = agent_query(
                        user_id=st.session_state.selected_member,
                        session_id=st.session_state.session_id,
                        country=country_code,  # ✅ Use country_code (AU, US, UK, IN) not display name
                        query_string=question,
                        validation_mode=st.session_state.validation_mode,
                    )
                    
                    # Extract values from the returned dictionary
                    answer = result.get('answer', '')
                    citations = result.get('citations', [])
                    response_dict = result.get('response_dict', {})
                    judge_resp = result.get('judge_verdict', {})
                    judge_verdict = result.get('judge_verdict', {})
                    error_info = result.get('error', None)
                    tools_called = result.get('tools_called', [])
                    
                    st.session_state.agent_output = {
                        "answer": answer,
                        "citations": citations,
                        "response_dict": response_dict,
                        "judge_response": judge_resp,
                        "judge_verdict": judge_verdict,
                        "error_info": error_info,
                        "tools_called": tools_called,
                    }
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    if st.session_state.agent_output:
        st.markdown("---")
        st.subheader("📊 Recommendation")
        st.success(st.session_state.agent_output["answer"])
        
        # Show validation results
        if st.session_state.agent_output.get("judge_verdict"):
            render_validation_results(
                st.session_state.agent_output["judge_verdict"],
                st.session_state.agent_output.get("response_dict", {})
            )
        
        # Show cost information if available
        response_dict = st.session_state.agent_output.get("response_dict", {})
        if response_dict.get("cost") is not None:
            total_cost = response_dict["cost"]
            cost_breakdown = response_dict.get("cost_breakdown", {})
            st.markdown("#### 💰 Cost Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Cost", f"${total_cost:.6f}")
            
            with col2:
                main_cost = total_cost - cost_breakdown.get('validation', {}).get('cost', 0)
                st.metric("Main LLM Cost", f"${main_cost:.6f}")
            
            with col3:
                validation_cost = cost_breakdown.get('validation', {}).get('cost', 0)
                st.metric("Judge LLM Cost", f"${validation_cost:.6f}")
        
        render_postanswer_disclaimer(country_display)
        
        # Show citations
        if st.session_state.agent_output.get("citations"):
            st.markdown("#### 📚 Citations & References")
            for i, cite in enumerate(st.session_state.agent_output.get("citations", [])[:3], 1):
                if isinstance(cite, dict):
                    st.caption(f"[{i}] {cite.get('authority', 'Unknown')}: {cite.get('regulation', 'No details')}")
                else:
                    st.caption(f"[{i}] {cite}")

# ============================================================================ #
# GOVERNANCE PAGE
# ============================================================================ #

elif page == "Governance":
    from ui_components import apply_custom_styles
    
    apply_custom_styles()
    
    st.title("🔒 Governance, MLflow & Configuration")
    
    tabs = st.tabs(["🧾 Governance & Audit", "📊 MLflow Traces", "💰 Cost Analysis", "⚙️ Configuration"])
    
    with tabs[0]:
        render_enhanced_audit_tab()
    
    with tabs[1]:
        render_mlflow_traces_tab()
    
    with tabs[2]:
        render_cost_analysis_tab()
    
    with tabs[3]:
        render_configuration_tab()
    
    st.markdown("---")
    st.caption(f"🏦 {BRANDCONFIG['brand_name']} | Session: {st.session_state.session_id[:8]}...")
