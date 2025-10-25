# ui_components.py - UPDATED FOR 12 UC FUNCTIONS (3 per country)
"""
UI components for the retirement advisory app
NOW DISPLAYS: Tax + Government Benefit + Projection for ALL countries
✨ ENHANCED: Beautiful tab styling with hover effects
"""

import streamlit as st
import os
import pandas as pd

# Temporary inline config
BRANDCONFIG = {
    "brand_name": "Global Retirement Advisory",
    "subtitle": "Enterprise-Grade Agentic AI on Databricks"
}


def apply_custom_styles():
    """
    Apply custom CSS styling for enhanced UI
    ✨ Beautiful tabs with logo colors (Green #00843D & Gold #FFD700)
    ✨ Hover effects and animations
    ✨ Professional gradients
    """
    st.markdown("""
    <style>
        /* ============================================
           ENHANCED TAB STYLING
           ============================================ */
        
        /* Tab container */
        .stTabs {
            width: 100%;
            margin-top: 1rem;
        }
        
        /* Tab list container */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0px;
            width: 100%;
            border-bottom: 3px solid #00843D;
            padding: 0;
        }
        
        /* Individual tabs */
        .stTabs [data-baseweb="tab"] {
            height: 70px;
            flex: 1;
            white-space: pre-wrap;
            background-color: #f8f9fa;
            border: none;
            border-radius: 8px 8px 0 0;
            color: #2c3e50;
            font-size: 18px;
            font-weight: 600;
            padding: 1rem 2rem;
            margin: 0 2px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Tab hover effect - gradient with logo colors */
        .stTabs [data-baseweb="tab"]:hover {
            background: linear-gradient(135deg, #00843D 0%, #FFD700 100%);
            color: white;
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0, 132, 61, 0.3);
            font-size: 19px;
        }
        
        /* Active tab */
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #00843D 0%, #006B2E 100%) !important;
            color: white !important;
            border-bottom: 4px solid #FFD700;
            box-shadow: 0 4px 8px rgba(0, 132, 61, 0.4);
            transform: scale(1.02);
        }
        
        /* Tab panel content */
        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 2rem;
        }
        
        /* Pulse animation for active tab */
        @keyframes pulse-gold {
            0%, 100% { border-bottom-color: #FFD700; }
            50% { border-bottom-color: #FFC700; }
        }
        
        .stTabs [aria-selected="true"] {
            animation: pulse-gold 2s ease-in-out infinite;
        }
        
        /* Focus indicator */
        .stTabs [data-baseweb="tab"]:focus {
            outline: 3px solid #FFD700;
            outline-offset: 2px;
        }
        
        /* ============================================
           ADDITIONAL UI ENHANCEMENTS
           ============================================ */
        
        /* Metric containers */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 700;
            color: #00843D;
        }
        
        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            transition: all 0.2s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Info boxes */
        .stAlert {
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)


def render_logo():
    """Render brand title and subtitle with custom styling"""
    # Apply custom CSS styles
    apply_custom_styles()
    
    st.markdown(f"## 🦢 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'))


def render_member_card(member, is_selected=False, country="Australia"):
    """
    Render a SIMPLE member card - just name and selection indicator.
    No HTML details leaked to user.
    """

    # Country color themes
    colors = {
        "Australia": {
            "flag": "🇦🇺",
            "primary": "#FFD700",  # Strong gold
            "secondary": "#00843D",  # Green
        },
        "USA": {
            "flag": "🇺🇸",
            "primary": "#B22234",  # Red
            "secondary": "#3C3B6E",  # Blue
        },
        "United Kingdom": {
            "flag": "🇬🇧",
            "primary": "#C8102E",  # Red
            "secondary": "#012169",  # Navy
        },
        "India": {
            "flag": "🇮🇳",
            "primary": "#FF9933",  # Saffron
            "secondary": "#138808",  # Green
        }
    }

    theme = colors.get(country, colors["Australia"])

    # Styling based on selection
    if is_selected:
        border = f"5px solid {theme['secondary']}"
        bg = f"linear-gradient(135deg, {theme['primary']}20 0%, {theme['secondary']}15 100%)"
        shadow = "0 8px 16px rgba(0,0,0,0.2)"
    else:
        border = "1px solid #e0e0e0"
        bg = "#ffffff"
        shadow = "0 2px 5px rgba(0,0,0,0.08)"

    # Get member info
    member_name = member.get('name', 'Unknown')
    age = member.get('age', 'N/A')
    balance = member.get('super_balance', 0)

    # Format balance
    if isinstance(balance, (int, float)):
        balance_int = int(balance)
        balance_display = f"{balance_int:,}"
    else:
        balance_display = str(balance)

    # Simple card
    card_html = f"""
    <div style="
        border: {border};
        border-radius: 12px;
        padding: 20px;
        background: {bg};
        box-shadow: {shadow};
        margin-bottom: 12px;
    ">
        <div style="font-size: 1.3em; font-weight: 600; color: {theme['secondary']}; margin-bottom: 12px;">
            {theme['flag']} {member_name}
        </div>
        <div style="color: #666; font-size: 0.95em;">
            Age {age} • Balance: {balance_display}
        </div>
        {f'<div style="margin-top: 12px; background: {theme["primary"]}; padding: 8px 12px; border-radius: 6px; text-align: center; font-weight: 600; color: #000;">✓ SELECTED</div>' if is_selected else ''}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_country_welcome(country, prompt_text, disclaimer):
    """Render country-specific welcome message"""
    st.info(f"**{country} Retirement Planning**\n\n{prompt_text}")
    if disclaimer:
        with st.expander("⚠️ Important Information"):
            st.caption(disclaimer)


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimers = {
        "Australia": "This is general information only and does not take into account your personal circumstances.",
        "USA": "This information is for educational purposes only and should not be considered financial advice.",
        "United Kingdom": "This information is general in nature and you should seek professional advice.",
        "India": "This is general information only. Please consult a qualified financial advisor."
    }

    disclaimer = disclaimers.get(country, disclaimers["Australia"])
    st.warning(f"⚠️ **Disclaimer:** {disclaimer}")


def render_question_card(question_text):
    """Render a question card"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
    ">
        <h4 style="margin: 0; color: white;">💬 Your Question</h4>
        <p style="margin: 10px 0 0 0; font-size: 1.1em;">{question_text}</p>
    </div>
    """, unsafe_allow_html=True)


def render_uc_functions_details(tools_called, country):
    """
    NEW: Render details about the 3 UC Functions that were called
    Shows thin cards with UC function names, authorities, and durations
    """
    
    if not tools_called or len(tools_called) == 0:
        return
    
    st.markdown("### 🔧 Calculations Performed")
    st.caption(f"{len(tools_called)} Unity Catalog functions executed:")
    
    for i, tool in enumerate(tools_called, 1):
        tool_name = tool.get('name', 'Calculator')
        authority = tool.get('authority', 'Authority')
        uc_function = tool.get('uc_function', '')
        duration = tool.get('duration', 0)
        status = tool.get('status', 'completed')
        
        # Status icon
        status_icon = "✅" if status == "completed" else "⚠️"
        
        # Color based on index
        colors = ["#3498db", "#2ecc71", "#9b59b6"]
        color = colors[i-1] if i <= 3 else "#95a5a6"
        
        st.markdown(f"""
        <div style="
            border-left: 4px solid {color};
            background: #f8f9fa;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 4px;
        ">
            <div style="font-weight: 600; color: #2c3e50; margin-bottom: 4px;">
                {status_icon} {i}. {tool_name}
            </div>
            <div style="font-size: 0.85em; color: #7f8c8d;">
                Authority: {authority} • {duration:.2f}s
            </div>
            {f'<div style="font-size: 0.75em; color: #95a5a6; margin-top: 4px; font-family: monospace;">{uc_function}</div>' if uc_function else ''}
        </div>
        """, unsafe_allow_html=True)


def format_currency(amount, country):
    """Format currency based on country"""
    if amount is None:
        return "N/A"
    
    currency_info = {
        "Australia": {"symbol": "AUD $", "code": "AUD"},
        "USA": {"symbol": "USD $", "code": "USD"},
        "United Kingdom": {"symbol": "GBP £", "code": "GBP"},
        "India": {"symbol": "INR ₹", "code": "INR"}
    }
    
    info = currency_info.get(country, {"symbol": "$", "code": ""})
    
    try:
        amount_float = float(amount)
        return f"{info['symbol']}{amount_float:,.2f}"
    except:
        return f"{info['symbol']}{amount}"


def render_calculation_results(tools_called, agent_output, country):
    """
    NEW: Display results from all 3 UC Functions per country
    Each country shows: Tax + Government Benefit + Projection
    """
    
    st.markdown("---")
    st.markdown("## 📊 Detailed Calculations")
    st.caption("Results from Unity Catalog regulatory functions")
    
    # Show which UC functions were called
    if tools_called:
        with st.expander("🔧 View UC Functions Called", expanded=False):
            render_uc_functions_details(tools_called, country)
    
    # Extract the actual calculation results from agent_output
    # agent_output contains the full tool_result dict
    
    # AUSTRALIA: 3 results
    if country == "Australia":
        render_australia_results(agent_output)
    
    # USA: 3 results
    elif country == "USA":
        render_usa_results(agent_output)
    
    # UK: 3 results
    elif country == "United Kingdom":
        render_uk_results(agent_output)
    
    # INDIA: 3 results
    elif country == "India":
        render_india_results(agent_output)
    
    else:
        st.info("Results display not configured for this country yet.")


def render_australia_results(agent_output):
    """Render Australia's 3 calculation results"""
    
    # 1. Tax Calculation
    if 'tax_calculation' in agent_output:
        st.markdown("### 💰 1. ATO Tax Calculation")
        tax = agent_output['tax_calculation']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Withdrawal Amount", format_currency(tax.get('withdrawal_amount'), "Australia"))
        with col2:
            st.metric("Tax Amount", format_currency(tax.get('tax_amount'), "Australia"))
        with col3:
            st.metric("Net Amount", format_currency(tax.get('net_withdrawal'), "Australia"))
        
        if 'status' in tax:
            st.info(f"ℹ️ {tax['status']}")
        
        if 'regulation' in tax:
            st.caption(f"📜 Regulation: {tax['regulation']}")
    
    st.markdown("---")
    
    # 2. Age Pension Impact
    if 'pension_impact' in agent_output:
        st.markdown("### 🏛️ 2. Centrelink Age Pension Impact")
        pension = agent_output['pension_impact']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Estimated Annual Pension", 
                     format_currency(pension.get('estimated_annual_pension'), "Australia"))
            st.metric("Annual Super Income", 
                     format_currency(pension.get('annual_super_income'), "Australia"))
        with col2:
            st.metric("Combined Annual Income", 
                     format_currency(pension.get('combined_annual_income'), "Australia"))
            eligible = pension.get('age_pension_eligible', False)
            st.metric("Age Pension Eligible", "Yes" if eligible else "No")
        
        if 'pension_status' in pension:
            st.success(f"✅ {pension['pension_status']}")
        
        if 'regulation' in pension:
            st.caption(f"📜 Regulation: {pension['regulation']}")
    
    st.markdown("---")
    
    # 3. Retirement Projection
    if 'retirement_projection' in agent_output:
        st.markdown("### 📊 3. Superannuation Projection")
        proj = agent_output['retirement_projection']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Balance", format_currency(proj.get('current_balance'), "Australia"))
        with col2:
            st.metric("Projected Balance", format_currency(proj.get('estimated_final_balance'), "Australia"))
        with col3:
            depleted = proj.get('balance_depleted', False)
            st.metric("Balance Depleted", "⚠️ Yes" if depleted else "✅ No")
        
        if 'summary' in proj:
            st.info(f"📝 {proj['summary']}")
        
        if 'regulation' in proj:
            st.caption(f"📜 Standard: {proj['regulation']}")


def render_usa_results(agent_output):
    """Render USA's 3 calculation results"""
    
    # 1. 401(k) Tax Calculation
    if 'tax_calculation' in agent_output:
        st.markdown("### 💰 1. 401(k)/IRA Tax Calculation")
        tax = agent_output['tax_calculation']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Withdrawal Amount", format_currency(tax.get('withdrawal_amount'), "USA"))
        with col2:
            st.metric("Early Withdrawal Penalty", format_currency(tax.get('early_withdrawal_penalty'), "USA"))
            st.metric("Income Tax", format_currency(tax.get('income_tax_amount'), "USA"))
        with col3:
            st.metric("Total Tax", format_currency(tax.get('total_tax'), "USA"))
            st.metric("Net Amount", format_currency(tax.get('net_withdrawal'), "USA"))
        
        if 'status' in tax:
            st.info(f"ℹ️ {tax['status']}")
        
        if 'regulation' in tax:
            st.caption(f"📜 Regulation: {tax['regulation']}")
    
    st.markdown("---")
    
    # 2. Social Security Benefits
    if 'social_security' in agent_output:
        st.markdown("### 🏛️ 2. Social Security Benefits")
        ss = agent_output['social_security']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Estimated Monthly Benefit", 
                     format_currency(ss.get('estimated_monthly_benefit'), "USA"))
            st.metric("Estimated Annual Benefit", 
                     format_currency(ss.get('estimated_annual_benefit'), "USA"))
        with col2:
            st.metric("Combined Annual Income", 
                     format_currency(ss.get('combined_annual_income'), "USA"))
            reduction = ss.get('reduction_or_increase_pct', 0)
            st.metric("Benefit Adjustment", f"{reduction:+.1f}%")
        
        if 'benefit_status' in ss:
            st.success(f"✅ {ss['benefit_status']}")
        
        if 'regulation' in ss:
            st.caption(f"📜 Regulation: {ss['regulation']}")
    
    st.markdown("---")
    
    # 3. Retirement Balance Projection
    if 'retirement_projection' in agent_output:
        st.markdown("### 📊 3. Retirement Balance Projection")
        proj = agent_output['retirement_projection']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Balance", format_currency(proj.get('current_balance'), "USA"))
        with col2:
            st.metric("Projected Balance", format_currency(proj.get('estimated_final_balance'), "USA"))
        with col3:
            rmd_required = proj.get('rmd_required', False)
            st.metric("RMD Required", "Yes (Age 73)" if rmd_required else "Not Yet")
        
        if 'summary' in proj:
            st.info(f"📝 {proj['summary']}")
        
        if 'regulation' in proj:
            st.caption(f"📜 Regulation: {proj['regulation']}")


def render_uk_results(agent_output):
    """Render UK's 3 calculation results"""
    
    # 1. Pension Tax Calculation
    if 'tax_calculation' in agent_output:
        st.markdown("### 💰 1. Pension Tax Calculation")
        tax = agent_output['tax_calculation']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Withdrawal Amount", format_currency(tax.get('withdrawal_amount'), "United Kingdom"))
        with col2:
            st.metric("Tax-Free Lump Sum", format_currency(tax.get('tax_free_lump_sum'), "United Kingdom"))
            st.metric("Taxable Amount", format_currency(tax.get('taxable_amount'), "United Kingdom"))
        with col3:
            st.metric("Tax Amount", format_currency(tax.get('tax_amount'), "United Kingdom"))
            st.metric("Net Amount", format_currency(tax.get('net_withdrawal'), "United Kingdom"))
        
        if 'status' in tax:
            st.info(f"ℹ️ {tax['status']}")
        
        if 'regulation' in tax:
            st.caption(f"📜 Regulation: {tax['regulation']}")
    
    st.markdown("---")
    
    # 2. State Pension
    if 'state_pension' in agent_output:
        st.markdown("### 🏛️ 2. State Pension Eligibility")
        sp = agent_output['state_pension']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Weekly State Pension", 
                     format_currency(sp.get('weekly_state_pension'), "United Kingdom"))
            st.metric("Annual State Pension", 
                     format_currency(sp.get('annual_state_pension'), "United Kingdom"))
        with col2:
            st.metric("Combined Annual Income", 
                     format_currency(sp.get('combined_annual_income'), "United Kingdom"))
            eligible = sp.get('full_state_pension_eligible', False)
            st.metric("Full Pension Eligible", "Yes" if eligible else "Partial")
        
        if 'pension_status' in sp:
            st.success(f"✅ {sp['pension_status']}")
        
        if 'regulation' in sp:
            st.caption(f"📜 Regulation: {sp['regulation']}")
    
    st.markdown("---")
    
    # 3. Pension Drawdown Projection
    if 'drawdown_projection' in agent_output:
        st.markdown("### 📊 3. Pension Drawdown Projection")
        proj = agent_output['drawdown_projection']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Pension Pot", format_currency(proj.get('current_pension_pot'), "United Kingdom"))
        with col2:
            st.metric("Projected Balance", format_currency(proj.get('estimated_final_balance'), "United Kingdom"))
        with col3:
            depleted = proj.get('balance_depleted', False)
            st.metric("Balance Depleted", "⚠️ Yes" if depleted else "✅ No")
        
        if 'summary' in proj:
            st.info(f"📝 {proj['summary']}")
        
        if 'regulation' in proj:
            st.caption(f"📜 Regulation: {proj['regulation']}")


def render_india_results(agent_output):
    """Render India's 3 calculation results"""
    
    # 1. EPF Tax Calculation
    if 'epf_tax_calculation' in agent_output:
        st.markdown("### 💰 1. EPF Tax Calculation")
        tax = agent_output['epf_tax_calculation']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Withdrawal Amount", format_currency(tax.get('withdrawal_amount'), "India"))
        with col2:
            st.metric("Tax Amount", format_currency(tax.get('tax_amount'), "India"))
            tax_exempt = tax.get('tax_exempt', False)
            st.metric("Tax Exempt", "✅ Yes" if tax_exempt else "❌ No")
        with col3:
            st.metric("Net Withdrawal", format_currency(tax.get('net_withdrawal'), "India"))
        
        if 'status' in tax:
            st.info(f"ℹ️ {tax['status']}")
        
        if 'regulation' in tax:
            st.caption(f"📜 Regulation: {tax['regulation']}")
    
    st.markdown("---")
    
    # 2. NPS Benefits
    if 'nps_benefits' in agent_output:
        st.markdown("### 🏛️ 2. NPS Benefits Calculation")
        nps = agent_output['nps_benefits']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total NPS Corpus", format_currency(nps.get('total_corpus'), "India"))
            st.metric("Lump Sum (Tax-Free)", format_currency(nps.get('lump_sum_tax_free'), "India"))
        with col2:
            st.metric("Annuity Amount", format_currency(nps.get('annuity_amount'), "India"))
            st.metric("Estimated Monthly Pension", format_currency(nps.get('estimated_monthly_pension'), "India"))
        
        if 'nps_status' in nps:
            st.success(f"✅ {nps['nps_status']}")
        
        if 'regulation' in nps:
            st.caption(f"📜 Regulation: {nps['regulation']}")
    
    st.markdown("---")
    
    # 3. Retirement Corpus Projection
    if 'retirement_projection' in agent_output:
        st.markdown("### 📊 3. Retirement Corpus Projection (EPF + NPS)")
        proj = agent_output['retirement_projection']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current EPF Balance", format_currency(proj.get('current_epf_balance'), "India"))
            st.metric("Projected EPF Balance", format_currency(proj.get('projected_epf_balance'), "India"))
        with col2:
            st.metric("Current NPS Balance", format_currency(proj.get('current_nps_balance'), "India"))
            st.metric("Projected NPS Balance", format_currency(proj.get('projected_nps_balance'), "India"))
        with col3:
            st.metric("Total Projected Corpus", 
                     format_currency(proj.get('total_projected_corpus'), "India"))
        
        if 'summary' in proj:
            st.info(f"📝 {proj['summary']}")
        
        if 'regulation' in proj:
            st.caption(f"📜 Regulation: {proj['regulation']}")


def render_audit_table(audit_df):
    """Render audit log table"""
    if audit_df is None or audit_df.empty:
        st.info("No audit logs found.")
        return

    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )


def render_enhanced_audit_tab():
    """Enhanced Audit Tab with 4 comprehensive views"""
    import mlflow
    from datetime import datetime
    from audit.audit_utils import get_audit_log
    from config import MLFLOW_PROD_EXPERIMENT_PATH, get_governance_table_path
    
    # Create 4 tabs - full width
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗄️ Governance Logs",
        "🔬 MLflow Traces", 
        "📊 Token Analysis",
        "💰 Cost Analysis"
    ])
    
    # TAB 1: GOVERNANCE LOGS
    with tab1:
        st.subheader("🗄️ Unity Catalog Governance Logs")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_country = st.selectbox("Country", ["All", "Australia", "USA", "United Kingdom", "India"], key="gov_country")
        with col2:
            filter_verdict = st.selectbox("Verdict", ["All", "Pass", "Fail", "Review", "ERROR"], key="gov_verdict")
        with col3:
            filter_mode = st.selectbox("Mode", ["All", "llm_judge", "hybrid", "deterministic"], key="gov_mode")
        with col4:
            limit = st.number_input("Limit", 10, 1000, 100, 10, key="gov_limit")
        
        if st.button("🔄 Refresh", key="refresh_gov"):
            if 'gov_logs_cache' in st.session_state:
                del st.session_state.gov_logs_cache
        
        if 'gov_logs_cache' not in st.session_state:
            with st.spinner("Loading..."):
                try:
                    st.session_state.gov_logs_cache = get_audit_log(limit=limit)
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.gov_logs_cache = pd.DataFrame()
        
        df = st.session_state.gov_logs_cache
        
        if df is not None and not df.empty:
            df_filtered = df.copy()
            
            if filter_country != "All" and 'country' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['country'] == filter_country]
            if filter_verdict != "All" and 'judge_verdict' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['judge_verdict'] == filter_verdict]
            if filter_mode != "All" and 'validation_mode' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['validation_mode'] == filter_mode]
            
            st.markdown("---")
            st.markdown("### 📈 Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Queries", f"{len(df_filtered):,}")
            with col2:
                if 'cost' in df_filtered.columns:
                    st.metric("Cost", f"${pd.to_numeric(df_filtered['cost'], errors='coerce').sum():.2f}")
                else:
                    st.metric("Cost", "N/A")
            with col3:
                if 'judge_verdict' in df_filtered.columns:
                    pass_rate = ((df_filtered['judge_verdict'] == 'Pass').sum() / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
                    st.metric("Pass Rate", f"{pass_rate:.1f}%")
                else:
                    st.metric("Pass Rate", "N/A")
            with col4:
                if 'total_time_seconds' in df_filtered.columns:
                    st.metric("Avg Time", f"{pd.to_numeric(df_filtered['total_time_seconds'], errors='coerce').mean():.2f}s")
                else:
                    st.metric("Avg Time", "N/A")
            
            st.markdown("---")
            
            display_cols = ['timestamp', 'user_id', 'country', 'query_string', 'judge_verdict', 'validation_mode', 'total_time_seconds', 'cost', 'tool_used']
            available_cols = [col for col in display_cols if col in df_filtered.columns]
            
            if 'timestamp' in df_filtered.columns:
                try:
                    df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            st.dataframe(df_filtered[available_cols], use_container_width=True, height=400)
            
            csv = df_filtered.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
        else:
            st.info("No logs. Run a query first.")
    
    # TAB 2: MLFLOW TRACES
    with tab2:
        st.subheader("🔬 MLflow Traces")
        
        if not MLFLOW_PROD_EXPERIMENT_PATH:
            st.error("Configure MLFLOW_PROD_EXPERIMENT_PATH in config.py")
            st.stop()
        
        st.markdown(f"**Experiment:** `{MLFLOW_PROD_EXPERIMENT_PATH}`")
        
        if st.button("🔄 Refresh", key="refresh_mlflow"):
            if 'mlflow_runs_cache' in st.session_state:
                del st.session_state.mlflow_runs_cache
        
        if 'mlflow_runs_cache' not in st.session_state:
            with st.spinner("Loading MLflow..."):
                try:
                    mlflow.set_experiment(MLFLOW_PROD_EXPERIMENT_PATH)
                    runs_df = mlflow.search_runs(
                        experiment_names=[MLFLOW_PROD_EXPERIMENT_PATH],
                        max_results=100,
                        order_by=["start_time DESC"]
                    )
                    st.session_state.mlflow_runs_cache = runs_df
                    st.success(f"✅ Loaded {len(runs_df)} runs")
                except Exception as e:
                    st.error(f"Error: {e}")
                    with st.expander("Troubleshooting"):
                        st.markdown("1. Run a query first\n2. Check experiment path\n3. Verify permissions")
                        try:
                            experiments = mlflow.search_experiments()
                            if experiments is not None and len(experiments) > 0:
                                st.dataframe(pd.DataFrame({'Name': [e.name for e in experiments]}))
                        except:
                            pass
                    st.session_state.mlflow_runs_cache = pd.DataFrame()
        
        runs_df = st.session_state.mlflow_runs_cache
        
        if runs_df is not None and not runs_df.empty:
            st.markdown("---")
            st.markdown("### 📊 Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Runs", f"{len(runs_df):,}")
            with col2:
                if 'metrics.cost_usd' in runs_df.columns:
                    st.metric("Cost", f"${pd.to_numeric(runs_df['metrics.cost_usd'], errors='coerce').sum():.2f}")
                else:
                    st.metric("Cost", "Not logged")
            with col3:
                if 'metrics.total_time_seconds' in runs_df.columns:
                    st.metric("Avg Time", f"{pd.to_numeric(runs_df['metrics.total_time_seconds'], errors='coerce').mean():.2f}s")
                else:
                    st.metric("Avg Time", "N/A")
            with col4:
                if 'metrics.tools_called' in runs_df.columns:
                    st.metric("Avg Tools", f"{pd.to_numeric(runs_df['metrics.tools_called'], errors='coerce').mean():.1f}")
                else:
                    st.metric("Avg Tools", "N/A")
            
            st.markdown("---")
            
            display_cols = ['start_time', 'run_name', 'status', 'params.country', 'params.validation_mode', 'metrics.total_time_seconds', 'metrics.cost_usd', 'metrics.tools_called']
            available_cols = [col for col in display_cols if col in runs_df.columns]
            
            runs_df_display = runs_df.copy()
            if 'start_time' in runs_df_display.columns:
                try:
                    runs_df_display['start_time'] = pd.to_datetime(runs_df_display['start_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            st.dataframe(runs_df_display[available_cols].head(50), use_container_width=True, height=400)
            
            st.markdown("---")
            st.markdown("### 🔍 Run Details")
            
            if len(runs_df) > 0:
                run_options = [f"{row.get('run_name', row.get('run_id', 'Unknown')[:8])} | {row.get('start_time', 'Unknown')}" for idx, row in runs_df.head(20).iterrows()]
                selected_idx = st.selectbox("Select Run", range(len(run_options)), format_func=lambda x: run_options[x], key="mlflow_run_selector")
                
                if selected_idx is not None:
                    selected_run = runs_df.iloc[selected_idx]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Parameters:**")
                        param_cols = [col for col in runs_df.columns if col.startswith('params.')]
                        if param_cols:
                            for col in param_cols:
                                val = selected_run[col]
                                if pd.notna(val):
                                    st.text(f"• {col.replace('params.', '')}: {val}")
                        else:
                            st.info("No parameters")
                    
                    with col2:
                        st.markdown("**Metrics:**")
                        metric_cols = [col for col in runs_df.columns if col.startswith('metrics.')]
                        if metric_cols:
                            for col in metric_cols:
                                val = selected_run[col]
                                if pd.notna(val):
                                    st.text(f"• {col.replace('metrics.', '')}: {val:.4f}" if isinstance(val, float) else f"• {col.replace('metrics.', '')}: {val}")
                        else:
                            st.info("No metrics")
        else:
            st.warning("No runs found")
            st.info("**Next:** Run a query, then refresh")
    
    # TAB 3: TOKEN ANALYSIS
    with tab3:
        st.subheader("📊 Token Analysis")
        
        st.info("💡 Token tracking enabled. Check console output.")
        
        if 'mlflow_runs_cache' not in st.session_state:
            try:
                mlflow.set_experiment(MLFLOW_PROD_EXPERIMENT_PATH)
                st.session_state.mlflow_runs_cache = mlflow.search_runs(experiment_names=[MLFLOW_PROD_EXPERIMENT_PATH], max_results=500)
            except:
                st.session_state.mlflow_runs_cache = pd.DataFrame()
        
        runs_df = st.session_state.mlflow_runs_cache
        
        if runs_df is not None and not runs_df.empty:
            token_cols = [col for col in runs_df.columns if 'token' in col.lower()]
            
            if token_cols:
                st.success("✅ Token data found")
                st.markdown("### 📈 Token Stats")
                
                col1, col2, col3 = st.columns(3)
                
                for col_name in ['metrics.total_tokens', 'metrics.token_count']:
                    if col_name in runs_df.columns:
                        with col1:
                            st.metric("Avg Total", f"{pd.to_numeric(runs_df[col_name], errors='coerce').mean():,.0f}")
                        break
                
                for col_name in ['metrics.input_tokens', 'metrics.prompt_tokens']:
                    if col_name in runs_df.columns:
                        with col2:
                            st.metric("Avg Input", f"{pd.to_numeric(runs_df[col_name], errors='coerce').mean():,.0f}")
                        break
                
                for col_name in ['metrics.output_tokens', 'metrics.completion_tokens']:
                    if col_name in runs_df.columns:
                        with col3:
                            st.metric("Avg Output", f"{pd.to_numeric(runs_df[col_name], errors='coerce').mean():,.0f}")
                        break
            else:
                st.warning("No token metrics in MLflow")
                st.info("Tokens tracked in console. To log to MLflow, add:\n```python\nmlflow.log_metrics({\"input_tokens\": x, \"output_tokens\": y})\n```")
        
        if 'gov_logs_cache' not in st.session_state:
            try:
                st.session_state.gov_logs_cache = get_audit_log(limit=500)
            except:
                st.session_state.gov_logs_cache = pd.DataFrame()
        
        gov_df = st.session_state.gov_logs_cache
        
        if gov_df is not None and not gov_df.empty and 'query_string' in gov_df.columns:
            st.markdown("---")
            st.markdown("### 📏 Query Length")
            
            gov_df['query_length'] = gov_df['query_string'].str.len()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg", f"{gov_df['query_length'].mean():.0f} chars")
            with col2:
                st.metric("Min", f"{gov_df['query_length'].min():.0f} chars")
            with col3:
                st.metric("Max", f"{gov_df['query_length'].max():.0f} chars")
    
    # TAB 4: COST ANALYSIS
    with tab4:
        st.subheader("💰 Cost Analysis")
        
        if 'gov_logs_cache' not in st.session_state:
            try:
                st.session_state.gov_logs_cache = get_audit_log(limit=500)
            except:
                st.session_state.gov_logs_cache = pd.DataFrame()
        
        df = st.session_state.gov_logs_cache
        
        if df is not None and not df.empty and 'cost' in df.columns:
            df['cost'] = pd.to_numeric(df['cost'], errors='coerce').fillna(0)
            df_with_cost = df[df['cost'] > 0]
            
            if len(df_with_cost) > 0:
                st.markdown("### 💵 Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                total_cost = df_with_cost['cost'].sum()
                avg_cost = df_with_cost['cost'].mean()
                
                with col1:
                    st.metric("Total", f"${total_cost:.2f}")
                with col2:
                    st.metric("Avg/Query", f"${avg_cost:.4f}")
                with col3:
                    st.metric("Min", f"${df_with_cost['cost'].min():.4f}")
                with col4:
                    st.metric("Max", f"${df_with_cost['cost'].max():.4f}")
                
                if 'country' in df_with_cost.columns:
                    st.markdown("---")
                    st.markdown("### 🌍 By Country")
                    
                    country_stats = df_with_cost.groupby('country').agg({'cost': ['sum', 'mean', 'count']}).round(4)
                    country_stats.columns = ['Total ($)', 'Avg ($)', 'Count']
                    st.dataframe(country_stats.sort_values('Total ($)', ascending=False), use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 🔮 Projections")
                
                queries_per_min = st.slider("Queries/min", 0.1, 10.0, 0.1, 0.1, help="Adjust volume")
                
                queries_per_hour = queries_per_min * 60
                queries_per_day = queries_per_hour * 24
                queries_per_month = queries_per_day * 30
                queries_per_year = queries_per_month * 12
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Hourly", f"${queries_per_hour * avg_cost:.2f}", delta=f"{queries_per_hour:.0f} queries")
                with col2:
                    st.metric("Daily", f"${queries_per_day * avg_cost:.2f}", delta=f"{queries_per_day:.0f} queries")
                with col3:
                    st.metric("Monthly", f"${queries_per_month * avg_cost:.2f}", delta=f"{queries_per_month:.0f} queries")
                with col4:
                    st.metric("Yearly", f"${queries_per_year * avg_cost:,.2f}", delta=f"{queries_per_year:,.0f} queries")
            else:
                st.info("No costs yet. Run a query!")
        else:
            st.info("💡 Cost tracking enabled!")
            st.markdown("""
            **Avg: ~$0.135/query**
            
            | Type | Cost |
            |------|------|
            | Simple | $0.08 |
            | Medium | $0.13 |
            | Complex | $0.15 |
            
            **@ 0.1 queries/min:**
            - Hourly: $0.81
            - Daily: $19.47
            - Monthly: $584.19
            """)
