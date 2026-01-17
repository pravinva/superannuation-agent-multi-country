import streamlit as st
import uuid
import os
import pandas as pd
from config import BRANDCONFIG
from debug_widgets import reset_widget_tracking, display_widget_debug_info, log_rerun
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
from ui_monitoring_tabs import (
    render_realtime_metrics_tab,
    render_classification_analytics_tab,
    render_quality_monitoring_tab,
    render_enhanced_cost_analysis_tab,
    render_system_health_tab
)
from utils.progress import initialize_progress_tracker
from agent_processor import agent_query
from utils.lakehouse import get_members_by_country
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
if "query_executing" not in st.session_state:
    st.session_state.query_executing = False

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
    st.sidebar.image("logo.png", width='stretch')
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

# ✅ CRITICAL: Initialize query execution flag
if "query_executing" not in st.session_state:
    st.session_state.query_executing = False

# ============================================================================ #
# ADVISORY PAGE
# ============================================================================ #

if page == "Advisory":
    # Reset widget tracking at start of page render
    reset_widget_tracking()

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
    
    # Always show up to 3 members (no extra UI controls).
    # We choose a stable sample per country for this session to avoid widget-key mismatch issues.
    if "members_sample_seed" not in st.session_state:
        st.session_state.members_sample_seed = 42
    if "members_seed_country" not in st.session_state:
        st.session_state.members_seed_country = None

    # New country => pick a new seed once (stable across reruns within that country)
    if st.session_state.members_seed_country != country_code:
        st.session_state.members_sample_seed = uuid.uuid4().int % (2**32 - 1)
        st.session_state.members_seed_country = country_code

    if st.session_state.current_country_code != country_code:
        members_df = get_members_by_country(country_code)
        if safe_dataframe_check(members_df):

            if len(members_df) > 3:
                members_df = members_df.sample(n=3, random_state=st.session_state.members_sample_seed)
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
                
                if st.button(button_label, key=f"btn_{member_id}_{country_code}", width='stretch', type=button_type):
                    st.session_state.selected_member = member_id
                    log_rerun("member_selection", f"Selected member: {member_id}")
                    st.rerun()

                render_member_card(member, is_selected, country_display)

    # ✅ Don't auto-select first member - causes widget state changes on every render
    # Only use selected member if one has been explicitly chosen
    if st.session_state.selected_member:
        member = next((m for m in members if m.get('member_id') == st.session_state.selected_member), None)
    else:
        member = None
    
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
            # ✅ Include country_code in key to avoid conflicts when switching countries
            if st.button(q, key=f"sample_q_{country_code}_{i}", width='stretch'):
                st.session_state.query_input = q
    
    question = st.text_input("Your question:", key="query_input")
    
    # ✅ Show/Hide Logs Toggle (like the GitHub implementation)
    # Initialize to False (not shown by default)
    if 'show_processing_logs' not in st.session_state:
        st.session_state.show_processing_logs = False
    
    # ✅ CRITICAL: Use session_state value directly for checkbox to ensure it respects our reset
    show_logs = st.checkbox(
        "🔍 Show Processing Logs",
        value=st.session_state.show_processing_logs,
        key="show_logs_checkbox"
    )
    
    # ✅ CRITICAL: Update session_state from checkbox value
    # This ensures checkbox state is synced with session_state
    st.session_state.show_processing_logs = show_logs
    
    # ✅ CRITICAL: Show progress tracker if phases exist OR if query is executing
    # This ensures progress shows even when switching pages mid-execution
    has_phases = 'phases' in st.session_state and len(st.session_state.phases) > 0
    is_executing = st.session_state.get('query_executing', False)
    
    # ✅ Show progress if checkbox is checked AND (phases exist OR query is executing)
    # This ensures progress shows when switching back to Advisory page during execution
    if (has_phases or is_executing) and show_logs:
        # ✅ CRITICAL: Create placeholder for real-time updates
        if 'progress_placeholder' not in st.session_state:
            st.session_state.progress_placeholder = st.empty()
        
        # ✅ Render progress display (updates via direct placeholder updates during execution)
        # No fragment needed - direct updates from mark_phase_running/complete work perfectly
        from utils.progress import render_progress_fragment
        try:
            render_progress_fragment()
        except:
            pass
        
        # ✅ Show indicator if query is executing
        if is_executing:
            st.info("🔄 Query is currently processing... Progress will update in real-time.")
    elif has_phases and not show_logs:
        # ✅ CRITICAL: Hide logs when checkbox is unchecked
        # Clear the placeholder to hide progress display
        if 'progress_placeholder' in st.session_state:
            st.session_state.progress_placeholder.empty()
    
    # ✅ CRITICAL: Show status if query is executing but logs are hidden
    if is_executing and not show_logs:
        st.info("🔄 Query is currently processing... Enable 'Show Processing Logs' to see progress.")
    
    if st.button("🚀 Get Recommendation", type="primary", width='stretch'):
        if not question:
            st.warning("Please enter a question first.")
        elif not st.session_state.selected_member:
            st.warning("Please select a member profile first.")
        else:
            # ✅ New query: clear previous output so the execution block doesn't short-circuit
            # (it checks `if st.session_state.get('agent_output')` to avoid double execution).
            st.session_state.agent_output = None

            # ✅ CRITICAL: Initialize phases FIRST (will trigger rerun)
            initialize_progress_tracker()
            st.session_state.query_executing = True
            st.session_state.current_query = question  # Store query for execution block

            # ✅ CRITICAL: Force immediate rerun to show progress
            log_rerun("get_recommendation", f"Starting query execution")
            st.rerun()
    
    # ✅ CRITICAL: Handle query execution (if query_executing flag is set)
    # This runs after st.rerun() when button is clicked
    # ✅ FIXED: Check if query already completed to prevent re-execution
    if st.session_state.get('query_executing', False):
        # ✅ CRITICAL: If agent_output already exists, query already completed
        # Don't re-execute, just mark as complete
        if st.session_state.get('agent_output'):
            st.session_state.query_executing = False
        else:
            # Process query with spinner
            with st.spinner("🔄 Processing your request..."):
                try:
                    # ✅ FIXED: agent_query now returns a dictionary, not 7 separate values
                    result = agent_query(
                        user_id=st.session_state.selected_member,
                        session_id=st.session_state.session_id,
                        country=country_code,  # ✅ Use country_code (AU, US, UK, IN) not display name
                        query_string=st.session_state.get('current_query', question),
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
                    st.session_state.query_executing = False
                finally:
                    # ✅ CRITICAL: Always mark query as complete
                    st.session_state.query_executing = False
    
    # ✅ CRITICAL: Answer display - ALWAYS runs regardless of progress tracker errors
    if st.session_state.agent_output:
        st.markdown("---")
        
        # Check if validation failed (after all retries)
        judge_verdict = st.session_state.agent_output.get("judge_verdict", {})
        validation_passed = judge_verdict.get("passed", True)
        validation_confidence = judge_verdict.get("confidence", 0.0)
        has_violations = len(judge_verdict.get("violations", [])) > 0
        
        # Determine if answer is safe to show
        # Failed if: validation explicitly failed AND has violations
        answer_failed = (not validation_passed) and has_violations
        
        if answer_failed:
            # ❌ VALIDATION FAILED - Show safe fallback message to user
            st.subheader("📊 Response Status")
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
                        border-left: 6px solid #F59E0B;
                        border-radius: 12px;
                        padding: 24px;
                        margin: 16px 0;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 32px;">⚠️</span>
                    <span style="font-size: 20px; font-weight: 600; color: #92400E;">
                        Unable to Process Request
                    </span>
                </div>
                <p style="color: #78350F; font-size: 16px; line-height: 1.6; margin-bottom: 16px;">
                    We're unable to provide a validated answer to your question at this time. 
                    Our AI system detected potential issues with the response quality.
                </p>
                <p style="color: #78350F; font-size: 16px; line-height: 1.6; margin-bottom: 16px;">
                    <strong>What happens next?</strong><br>
                    • Our advisory team has been notified<br>
                    • A qualified advisor will review your question<br>
                    • We'll contact you within 24-48 hours with a personalized response
                </p>
                <p style="color: #78350F; font-size: 14px; margin-top: 16px;">
                    <em>For urgent matters, please contact our member services team directly.</em>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show validation results for transparency
            if judge_verdict:
                render_validation_results(
                    judge_verdict,
                    st.session_state.agent_output.get("response_dict", {})
                )
            
            # 🔒 INTERNAL REVIEW SECTION - Collapsed by default
            with st.expander("🔧 INTERNAL REVIEW - AI Generated Response (For Dev Team Only)", expanded=False):
                st.warning("⚠️ This response FAILED validation and was NOT shown to the user.")
                st.markdown("**AI Generated Answer (Do Not Share With User):**")
                st.code(st.session_state.agent_output["answer"], language=None)
                
                st.markdown("**Validation Issues:**")
                for i, violation in enumerate(judge_verdict.get("violations", []), 1):
                    st.markdown(f"""
                    **Issue {i}:** `{violation.get('code', 'UNKNOWN')}`
                    - **Severity:** {violation.get('severity', 'Unknown')}
                    - **Detail:** {violation.get('detail', 'No details')}
                    - **Evidence:** {violation.get('evidence', 'N/A')[:200]}...
                    """)
                
                st.markdown("**Recommended Actions:**")
                st.markdown("""
                - Review the AI-generated answer above
                - Check tool outputs and member data
                - Verify regulatory compliance
                - Manually craft appropriate response
                - Update member via support channel
                """)
        
        else:
            # ✅ VALIDATION PASSED - Show answer with professional styling
            st.subheader("📊 Your Personalized Recommendation")
            
            # Use simple st.success for clean display (no HTML issues)
            st.success(st.session_state.agent_output["answer"])
            
            # Show validation results
            if judge_verdict:
                render_validation_results(
                    judge_verdict,
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

        # Show citations (only if they have meaningful content)
        citations = st.session_state.agent_output.get("citations", [])
        valid_citations = []

        for cite in citations:
            if isinstance(cite, dict):
                regulation = cite.get('regulation', '')
                # Skip citations with empty or "No details" regulation
                if regulation and regulation != 'No details':
                    valid_citations.append(cite)
            elif cite:  # Non-empty string citation
                valid_citations.append(cite)

        if valid_citations:
            st.markdown("#### 📚 Citations & References")
            for i, cite in enumerate(valid_citations[:3], 1):
                if isinstance(cite, dict):
                    st.caption(f"[{i}] {cite.get('authority', 'Unknown')}: {cite.get('regulation', '')}")
                else:
                    st.caption(f"[{i}] {cite}")

    # Display debug widget information in sidebar (only on Advisory page)
    display_widget_debug_info()

# ============================================================================ #
# GOVERNANCE PAGE
# ============================================================================ #

elif page == "Governance":
    from ui_styles_professional import apply_professional_pension_theme
    from ui_dashboard import render_dashboard_tab
    
    apply_professional_pension_theme()
    
    st.title("🔒 Governance & Observability")
    st.caption("💡 Professional monitoring dashboard - everything at a glance")
    
    # 5-TAB DESIGN: Governance, MLflow, Config, Cost, Observability
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔒 Governance",
        "🔬 MLflow",
        "⚙️ Config",
        "💰 Cost",
        "📊 Observability"
    ])
    
    with tab1:  # Governance - Dashboard overview + Audit trail
        st.markdown("### 📊 Governance Dashboard")
        st.caption("Overview of system performance and audit trail")
        
        # ✅ Import dashboard components
        from ui_dashboard import (
            get_dashboard_data,
            calculate_key_metrics,
            render_metric_card,
            render_health_stars,
            render_system_status,
            render_activity_feed,
            render_quick_charts,
            render_trust_footer
        )
        
        # Get data (cached for 60 seconds)
        df = get_dashboard_data()
        
        if not df.empty:
            # Calculate metrics
            metrics = calculate_key_metrics(df)
            
            # Key Metrics Row (full width)
            st.markdown("### Key Metrics (Last 24 Hours)")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                render_metric_card(
                    "Total Queries",
                    f"{metrics['total_queries']:,}",
                    "Last 24h",
                    True
                )
            
            with col2:
                render_metric_card(
                    "Pass Rate",
                    f"{metrics['pass_rate']:.1%}",
                    "Good" if metrics['pass_rate'] >= 0.8 else "Needs attention",
                    metrics['pass_rate'] >= 0.8
                )
            
            with col3:
                render_metric_card(
                    "Avg Cost",
                    f"${metrics['avg_cost']:.4f}",
                    "Per query",
                    True
                )
            
            with col4:
                health_stars = render_health_stars(metrics['health_score'])
                render_metric_card(
                    "Health Score",
                    health_stars,
                    f"{metrics['health_score']}/100",
                    metrics['health_score'] >= 80
                )
            
            st.markdown("---")
            
            # System Status Banner
            render_system_status(df)
            
            st.markdown("---")
        else:
            st.info("📊 No data available for the last 24 hours. Run some queries to populate the dashboard!")
        
        # ✅ Audit Trail with full width right under key metrics
        st.markdown("### 📋 Audit Trail")
        render_enhanced_audit_tab()
        
        # ✅ Recent Activity Feed below Audit Trail (optional - can be removed if not needed)
        if not df.empty:
            st.markdown("---")
            render_activity_feed(df, limit=10)
            
            st.markdown("---")
            
            # Quick Charts
            st.markdown("### Trends")
            render_quick_charts(df)
            
            # Trust Footer
            render_trust_footer()
    
    with tab2:  # MLflow - MLflow traces
        st.markdown("### 🔬 MLflow Traces")
        st.caption("Advanced MLflow experiment tracking and traces")
        render_mlflow_traces_tab()
    
    with tab3:  # Config - Configuration settings
        render_configuration_tab()
    
    with tab4:  # Cost - Cost analysis
        st.markdown("### 💰 Cost Analysis")
        st.caption("Comprehensive cost breakdowns, trends, and projections")
        
        # ✅ Single comprehensive cost analysis view (no duplicates)
        # All unique metrics are now in render_enhanced_cost_analysis_tab()
        render_enhanced_cost_analysis_tab()
    
    with tab5:  # Observability - Real-time metrics, quality, health, classification
        col1, col2 = st.columns([1, 1])
        with col1:
            render_realtime_metrics_tab()
            
            st.markdown("---")
            render_quality_monitoring_tab()
        
        with col2:
            render_classification_analytics_tab()
            
            st.markdown("---")
            render_system_health_tab()
    
    st.markdown("---")
    st.caption(f"🏦 {BRANDCONFIG['brand_name']} | Session: {st.session_state.session_id[:8]}...")
