# ui_components.py - COMPLETE WITH ENHANCED AUDIT TAB

"""
UI components for the retirement advisory app
✅ All rendering functions in one place
✅ Enhanced audit tab with MLflow traces, token analysis, costs
✅ Beautiful tab styling with hover effects
✅ Safe DataFrame operations
"""

import streamlit as st
import os
import pandas as pd
import mlflow
from datetime import datetime, timedelta
from audit.audit_utils import get_audit_log
from config import (
    BRANDCONFIG, 
    MLFLOW_PROD_EXPERIMENT_PATH, 
    get_governance_table_path
)


# ============================================================================
# SAFE NUMERIC CONVERSION UTILITIES
# ============================================================================

def safe_numeric_sum(df, column_name, default=0.0):
    """Safely sum a numeric column with type conversion"""
    if df is None or df.empty or column_name not in df.columns:
        return default
    try:
        values = pd.to_numeric(df[column_name], errors='coerce').fillna(0)
        return float(values.sum())
    except Exception:
        return default

def safe_numeric_mean(df, column_name, default=0.0):
    """Safely calculate mean of numeric column"""
    if df is None or df.empty or column_name not in df.columns:
        return default
    try:
        values = pd.to_numeric(df[column_name], errors='coerce').dropna()
        if len(values) == 0:
            return default
        return float(values.mean())
    except Exception:
        return default

def safe_numeric_max(df, column_name, default=0.0):
    """Safely get max of numeric column"""
    if df is None or df.empty or column_name not in df.columns:
        return default
    try:
        values = pd.to_numeric(df[column_name], errors='coerce').dropna()
        if len(values) == 0:
            return default
        return float(values.max())
    except Exception:
        return default

def safe_numeric_min(df, column_name, default=0.0):
    """Safely get min of numeric column"""
    if df is None or df.empty or column_name not in df.columns:
        return default
    try:
        values = pd.to_numeric(df[column_name], errors='coerce').dropna()
        if len(values) == 0:
            return default
        return float(values.min())
    except Exception:
        return default


# ============================================================================
# CUSTOM STYLES
# ============================================================================

def apply_custom_styles():
    """Apply custom CSS styling for enhanced UI"""
    st.markdown("""
    <style>
        /* ============================================
           ENHANCED TAB STYLING
           ============================================ */
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 0px;
            width: 100%;
            border-bottom: 3px solid #00843D;
            padding: 0;
        }
        
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
        
        .stTabs [data-baseweb="tab"]:hover {
            background: linear-gradient(135deg, #00843D 0%, #FFD700 100%);
            color: white;
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0, 132, 61, 0.3);
            font-size: 19px;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #00843D 0%, #006B2E 100%) !important;
            color: white !important;
            border-bottom: 4px solid #FFD700;
            box-shadow: 0 4px 8px rgba(0, 132, 61, 0.4);
            transform: scale(1.02);
        }
        
        @keyframes pulse-gold {
            0%, 100% { border-bottom-color: #FFD700; }
            50% { border-bottom-color: #FFC700; }
        }
        
        .stTabs [aria-selected="true"] {
            animation: pulse-gold 2s ease-in-out infinite;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 700;
            color: #00843D;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# BASIC UI COMPONENTS
# ============================================================================

def render_logo():
    """Render brand title and subtitle with custom styling"""
    apply_custom_styles()
    st.markdown(f"## 🦢 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG.get('subtitle', 'Enterprise-Grade Agentic AI on Databricks'))


def render_member_card(member, is_selected=False, country="Australia"):
    """Render a member card with country-specific styling"""
    
    colors = {
        "Australia": {"flag": "🇦🇺", "primary": "#FFD700", "secondary": "#00843D"},
        "USA": {"flag": "🇺🇸", "primary": "#B22234", "secondary": "#3C3B6E"},
        "United Kingdom": {"flag": "🇬🇧", "primary": "#C8102E", "secondary": "#012169"},
        "India": {"flag": "🇮🇳", "primary": "#FF9933", "secondary": "#138808"}
    }
    
    theme = colors.get(country, colors["Australia"])
    
    if is_selected:
        border = f"5px solid {theme['secondary']}"
        bg = f"linear-gradient(135deg, {theme['primary']}20 0%, {theme['secondary']}15 100%)"
        shadow = "0 8px 16px rgba(0,0,0,0.2)"
    else:
        border = "1px solid #e0e0e0"
        bg = "#ffffff"
        shadow = "0 2px 5px rgba(0,0,0,0.08)"
    
    member_name = member.get('name', 'Unknown')
    age = member.get('age', 'N/A')
    balance = member.get('super_balance', 0)
    
    if isinstance(balance, (int, float)):
        balance_display = f"{int(balance):,}"
    else:
        balance_display = str(balance)
    
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


def render_question_card(example_questions):
    """Render example questions card"""
    st.markdown("**💡 Example Questions:**")
    for q in example_questions:
        st.caption(f"• {q}")


def render_country_welcome(country, prompt_text, disclaimer):
    """Render country-specific welcome message"""
    st.info(f"**{country} Retirement Planning**\n\n{prompt_text}")
    if disclaimer:
        with st.expander("⚠️ Important Information"):
            st.caption(disclaimer)


def render_postanswer_disclaimer(country):
    """Render post-answer disclaimer"""
    disclaimers = {
        "Australia": "⚠️ This is general information only. Please consult a licensed financial adviser.",
        "USA": "⚠️ This information is for educational purposes. Consult a financial advisor for personalized advice.",
        "United Kingdom": "⚠️ This is general guidance. Please seek advice from a qualified financial adviser.",
        "India": "⚠️ This is indicative information. Please consult a SEBI-registered investment adviser."
    }
    
    disclaimer = disclaimers.get(country, "⚠️ This is general information only.")
    st.info(disclaimer)


def format_currency(amount, country):
    """Format currency based on country"""
    if amount is None or amount == 0:
        return "N/A"
    
    symbols = {
        "Australia": "A$",
        "USA": "$",
        "United Kingdom": "£",
        "India": "₹"
    }
    
    symbol = symbols.get(country, "$")
    
    try:
        amount_float = float(amount)
        return f"{symbol}{amount_float:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}{amount}"


def render_audit_table(audit_df):
    """Render basic audit log table"""
    if audit_df is None or audit_df.empty:
        st.info("No audit logs found.")
        return
    
    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================================
# COUNTRY-SPECIFIC RESULTS RENDERING
# ============================================================================

def render_australia_results(agent_output):
    """Render Australia's 3 calculation results"""
    
    # 1. Super Tax Calculation
    if 'tax_calculation' in agent_output:
        st.markdown("### 💰 1. Superannuation Tax Calculation")
        tax = agent_output['tax_calculation']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Withdrawal Amount", format_currency(tax.get('withdrawal_amount'), "Australia"))
        with col2:
            st.metric("Tax Amount", format_currency(tax.get('tax_amount'), "Australia"))
        with col3:
            st.metric("Net Withdrawal", format_currency(tax.get('net_withdrawal'), "Australia"))
        
        if 'status' in tax:
            st.info(f"ℹ️ {tax['status']}")
        
        if 'regulation' in tax:
            st.caption(f"📜 Regulation: {tax['regulation']}")
    
    st.markdown("---")
    
    # 2. Age Pension
    if 'age_pension' in agent_output:
        st.markdown("### 🏛️ 2. Age Pension Eligibility")
        pension = agent_output['age_pension']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Fortnightly Payment", format_currency(pension.get('fortnightly_pension'), "Australia"))
            st.metric("Annual Pension", format_currency(pension.get('annual_pension'), "Australia"))
        with col2:
            st.metric("Combined Annual Income", format_currency(pension.get('combined_annual_income'), "Australia"))
            eligible = pension.get('eligible', False)
            st.metric("Eligible", "Yes" if eligible else "Partial")
        
        if 'pension_status' in pension:
            st.success(f"✅ {pension['pension_status']}")
        
        if 'regulation' in pension:
            st.caption(f"📜 Regulation: {pension['regulation']}")
    
    st.markdown("---")
    
    # 3. Super Projection
    if 'super_projection' in agent_output:
        st.markdown("### 📊 3. Superannuation Balance Projection")
        proj = agent_output['super_projection']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Balance", format_currency(proj.get('current_balance'), "Australia"))
        with col2:
            st.metric("Projected Balance", format_currency(proj.get('estimated_balance_at_retirement'), "Australia"))
        with col3:
            depleted = proj.get('balance_depleted', False)
            st.metric("Balance Depleted", "⚠️ Yes" if depleted else "✅ No")
        
        if 'summary' in proj:
            st.info(f"📝 {proj['summary']}")
        
        if 'regulation' in proj:
            st.caption(f"📜 Regulation: {proj['regulation']}")


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
    
    st.markdown("---")
    
    # 2. Social Security
    if 'social_security' in agent_output:
        st.markdown("### 🏛️ 2. Social Security Benefits")
        ss = agent_output['social_security']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Monthly Benefit", format_currency(ss.get('estimated_monthly_benefit'), "USA"))
            st.metric("Annual Benefit", format_currency(ss.get('estimated_annual_benefit'), "USA"))
        with col2:
            st.metric("Combined Income", format_currency(ss.get('combined_annual_income'), "USA"))
            reduction = ss.get('reduction_or_increase_pct', 0)
            st.metric("Adjustment", f"{reduction:+.1f}%")
    
    st.markdown("---")
    
    # 3. Retirement Projection
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


def render_uk_results(agent_output):
    """Render UK's 3 calculation results"""
    
    # 1. Pension Tax
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
    
    st.markdown("---")
    
    # 2. State Pension
    if 'state_pension' in agent_output:
        st.markdown("### 🏛️ 2. State Pension Eligibility")
        sp = agent_output['state_pension']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Weekly Pension", format_currency(sp.get('weekly_state_pension'), "United Kingdom"))
            st.metric("Annual Pension", format_currency(sp.get('annual_state_pension'), "United Kingdom"))
        with col2:
            st.metric("Combined Income", format_currency(sp.get('combined_annual_income'), "United Kingdom"))
            eligible = sp.get('full_state_pension_eligible', False)
            st.metric("Full Pension", "Yes" if eligible else "Partial")
    
    st.markdown("---")
    
    # 3. Drawdown Projection
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


def render_india_results(agent_output):
    """Render India's 3 calculation results"""
    
    # 1. EPF Tax
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
    
    st.markdown("---")
    
    # 2. NPS Benefits
    if 'nps_benefits' in agent_output:
        st.markdown("### 🏛️ 2. NPS Benefits Calculation")
        nps = agent_output['nps_benefits']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Corpus", format_currency(nps.get('total_corpus'), "India"))
            st.metric("Lump Sum (Tax-Free)", format_currency(nps.get('lump_sum_tax_free'), "India"))
        with col2:
            st.metric("Annuity Amount", format_currency(nps.get('annuity_amount'), "India"))
            st.metric("Monthly Pension", format_currency(nps.get('estimated_monthly_pension'), "India"))
    
    st.markdown("---")
    
    # 3. Retirement Projection
    if 'retirement_projection' in agent_output:
        st.markdown("### 📊 3. Retirement Corpus Projection (EPF + NPS)")
        proj = agent_output['retirement_projection']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current EPF", format_currency(proj.get('current_epf_balance'), "India"))
            st.metric("Projected EPF", format_currency(proj.get('projected_epf_balance'), "India"))
        with col2:
            st.metric("Current NPS", format_currency(proj.get('current_nps_balance'), "India"))
            st.metric("Projected NPS", format_currency(proj.get('projected_nps_balance'), "India"))
        with col3:
            st.metric("Total Projected", format_currency(proj.get('total_projected_corpus'), "India"))


# ============================================================================
# ENHANCED AUDIT TAB - THE MAIN EVENT!
# ============================================================================

def render_enhanced_audit_tab():
    """
    Render enhanced audit tab with:
    1. Governance table audit logs
    2. MLflow traces and metrics
    3. Token usage analysis
    4. Cost analysis
    """
    
    st.header("📊 Audit Trail & Analytics")
    st.markdown("Comprehensive governance logs, MLflow experiments, token usage, and cost analysis")
    
    # Create 4 tabs for different views
    audit_tabs = st.tabs([
        "🗄️ Governance Logs",
        "🔬 MLflow Traces", 
        "📊 Token Analysis",
        "💰 Cost Analysis"
    ])
    
    # ============================================================================
    # TAB 1: GOVERNANCE LOGS (Unity Catalog)
    # ============================================================================
    with audit_tabs[0]:
        st.markdown("### 🗄️ Unity Catalog Governance Logs")
        st.caption("Query audit trail from governance table")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            country_filter = st.selectbox(
                "Filter by Country",
                ["All", "Australia", "USA", "United Kingdom", "India"],
                key="gov_country_filter"
            )
        
        with col2:
            verdict_filter = st.selectbox(
                "Filter by Verdict",
                ["All", "Pass", "Reject", "Review", "ERROR"],
                key="gov_verdict_filter"
            )
        
        with col3:
            limit = st.number_input(
                "Max Records",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
                key="gov_limit"
            )
        
        # Load data
        @st.cache_data(ttl=60)
        def load_governance_logs(country=None, verdict=None, limit_val=100):
            """Load and cache governance logs"""
            kwargs = {'limit': limit_val}
            if country and country != "All":
                kwargs['country'] = country
            return get_audit_log(**kwargs)
        
        with st.spinner("Loading governance logs..."):
            gov_df = load_governance_logs(
                country_filter if country_filter != "All" else None,
                verdict_filter if verdict_filter != "All" else None,
                limit
            )
        
        if gov_df is not None and not gov_df.empty:
            # Filter by verdict if needed
            if verdict_filter != "All" and 'judge_verdict' in gov_df.columns:
                gov_df = gov_df[gov_df['judge_verdict'] == verdict_filter]
            
            st.markdown(f"**{len(gov_df)} records found**")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_cost = safe_numeric_sum(gov_df, 'cost', 0.0)
                st.metric("Total Cost", f"${total_cost:.2f}")
            
            with col2:
                if 'judge_verdict' in gov_df.columns:
                    pass_count = (gov_df['judge_verdict'] == 'Pass').sum()
                    pass_rate = (pass_count / len(gov_df) * 100) if len(gov_df) > 0 else 0
                else:
                    pass_rate = 0
                st.metric("Pass Rate", f"{pass_rate:.1f}%")
            
            with col3:
                avg_time = safe_numeric_mean(gov_df, 'total_time_seconds', 0.0)
                st.metric("Avg Time", f"{avg_time:.1f}s")
            
            with col4:
                st.metric("Total Queries", f"{len(gov_df):,}")
            
            st.markdown("---")
            
            # Display table
            display_cols = ['timestamp', 'country', 'query_string', 'judge_verdict', 
                          'validation_mode', 'cost', 'total_time_seconds']
            available_cols = [col for col in display_cols if col in gov_df.columns]
            
            st.dataframe(
                gov_df[available_cols].head(200),
                use_container_width=True,
                hide_index=True
            )
            
            # Download button
            csv = gov_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"governance_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No governance logs found")
    
    # ============================================================================
    # TAB 2: MLFLOW TRACES
    # ============================================================================
    with audit_tabs[1]:
        st.markdown("### 🔬 MLflow Experiment Traces")
        st.caption("View runs, metrics, and parameters from MLflow")
        
        try:
            if MLFLOW_PROD_EXPERIMENT_PATH:
                st.info(f"📂 Experiment: `{MLFLOW_PROD_EXPERIMENT_PATH}`")
                
                # Get experiment
                try:
                    experiment = mlflow.get_experiment_by_name(MLFLOW_PROD_EXPERIMENT_PATH)
                    
                    if experiment:
                        experiment_id = experiment.experiment_id
                        
                        # Search runs
                        with st.spinner("Loading MLflow runs..."):
                            runs = mlflow.search_runs(
                                experiment_ids=[experiment_id],
                                order_by=["start_time DESC"],
                                max_results=100
                            )
                        
                        if not runs.empty:
                            st.markdown(f"**{len(runs)} runs found**")
                            
                            # Summary metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                total_runs = len(runs)
                                st.metric("Total Runs", f"{total_runs:,}")
                            
                            with col2:
                                if 'metrics.cost' in runs.columns:
                                    total_cost = safe_numeric_sum(runs, 'metrics.cost', 0.0)
                                    st.metric("Total Cost", f"${total_cost:.2f}")
                                else:
                                    st.metric("Total Cost", "N/A")
                            
                            with col3:
                                if 'metrics.total_time_seconds' in runs.columns:
                                    avg_time = safe_numeric_mean(runs, 'metrics.total_time_seconds', 0.0)
                                    st.metric("Avg Time", f"{avg_time:.1f}s")
                                else:
                                    st.metric("Avg Time", "N/A")
                            
                            with col4:
                                if 'metrics.pass' in runs.columns:
                                    pass_count = safe_numeric_sum(runs, 'metrics.pass', 0)
                                    pass_rate = (pass_count / len(runs) * 100) if len(runs) > 0 else 0
                                    st.metric("Pass Rate", f"{pass_rate:.1f}%")
                                else:
                                    st.metric("Pass Rate", "N/A")
                            
                            st.markdown("---")
                            
                            # Display runs table
                            display_cols = []
                            for col in ['start_time', 'params.country', 'params.validation_mode', 
                                      'metrics.cost', 'metrics.total_tokens', 'metrics.total_time_seconds',
                                      'params.judge_verdict', 'run_id']:
                                if col in runs.columns:
                                    display_cols.append(col)
                            
                            if display_cols:
                                # Rename columns for better display
                                display_df = runs[display_cols].copy()
                                display_df.columns = [col.replace('params.', '').replace('metrics.', '') 
                                                    for col in display_df.columns]
                                
                                st.dataframe(
                                    display_df.head(50),
                                    use_container_width=True,
                                    hide_index=True
                                )
                            else:
                                st.dataframe(runs.head(50), use_container_width=True)
                            
                            # Download button
                            csv = runs.to_csv(index=False)
                            st.download_button(
                                label="📥 Download MLflow Runs CSV",
                                data=csv,
                                file_name=f"mlflow_runs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                            
                            # Show recent run details
                            st.markdown("---")
                            st.markdown("#### Recent Run Details")
                            
                            run_selector = st.selectbox(
                                "Select a run to view details",
                                options=runs['run_id'].tolist()[:10],
                                format_func=lambda x: f"{x[:8]}... ({runs[runs['run_id']==x]['start_time'].iloc[0]})"
                            )
                            
                            if run_selector:
                                selected_run = runs[runs['run_id'] == run_selector].iloc[0]
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**Parameters:**")
                                    param_cols = [col for col in selected_run.index if col.startswith('params.')]
                                    for col in param_cols:
                                        param_name = col.replace('params.', '')
                                        st.caption(f"• {param_name}: {selected_run[col]}")
                                
                                with col2:
                                    st.markdown("**Metrics:**")
                                    metric_cols = [col for col in selected_run.index if col.startswith('metrics.')]
                                    for col in metric_cols:
                                        metric_name = col.replace('metrics.', '')
                                        st.caption(f"• {metric_name}: {selected_run[col]}")
                        
                        else:
                            st.info("No MLflow runs found in this experiment")
                    
                    else:
                        st.warning(f"Experiment not found: {MLFLOW_PROD_EXPERIMENT_PATH}")
                        st.info("Make sure the experiment exists and you have access to it")
                
                except Exception as e:
                    st.error(f"Error accessing MLflow experiment: {str(e)}")
                    st.info("Ensure MLflow is properly configured and accessible")
            
            else:
                st.warning("⚠️ MLFLOW_PROD_EXPERIMENT_PATH not configured in config.py")
                st.info("Set MLFLOW_PROD_EXPERIMENT_PATH to enable MLflow tracking")
        
        except Exception as e:
            st.error(f"❌ MLflow connection error: {str(e)}")
            st.info("Ensure MLflow is properly configured and accessible")
    
    # ============================================================================
    # TAB 3: TOKEN ANALYSIS
    # ============================================================================
    with audit_tabs[2]:
        st.markdown("### 📊 Token Usage Analysis")
        st.caption("Analyze token consumption patterns across queries")
        
        with st.spinner("Loading token data..."):
            token_df = get_audit_log(limit=1000)
        
        if token_df is not None and not token_df.empty:
            # Check if we have token data
            has_token_data = 'total_tokens' in token_df.columns or 'input_tokens' in token_df.columns
            
            if has_token_data:
                # Use total_tokens if available, otherwise try to calculate
                if 'total_tokens' not in token_df.columns:
                    if 'input_tokens' in token_df.columns and 'output_tokens' in token_df.columns:
                        token_df['total_tokens'] = (
                            pd.to_numeric(token_df['input_tokens'], errors='coerce').fillna(0) +
                            pd.to_numeric(token_df['output_tokens'], errors='coerce').fillna(0)
                        )
                    else:
                        st.warning("Token columns not found in governance table")
                        has_token_data = False
            
            if has_token_data and 'total_tokens' in token_df.columns:
                # Token metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_tokens = safe_numeric_sum(token_df, 'total_tokens', 0)
                    st.metric("Total Tokens", f"{int(total_tokens):,}")
                
                with col2:
                    avg_tokens = safe_numeric_mean(token_df, 'total_tokens', 0)
                    st.metric("Avg per Query", f"{int(avg_tokens):,}")
                
                with col3:
                    max_tokens = safe_numeric_max(token_df, 'total_tokens', 0)
                    st.metric("Max Tokens", f"{int(max_tokens):,}")
                
                with col4:
                    min_tokens = safe_numeric_min(token_df, 'total_tokens', 0)
                    st.metric("Min Tokens", f"{int(min_tokens):,}")
                
                st.markdown("---")
                
                # Token distribution by country
                if 'country' in token_df.columns:
                    st.markdown("#### Token Usage by Country")
                    
                    token_df['total_tokens_numeric'] = pd.to_numeric(
                        token_df['total_tokens'], errors='coerce'
                    ).fillna(0)
                    
                    country_tokens = token_df.groupby('country')['total_tokens_numeric'].agg(
                        ['sum', 'mean', 'count']
                    )
                    country_tokens.columns = ['Total Tokens', 'Avg Tokens', 'Query Count']
                    country_tokens = country_tokens.astype({
                        'Total Tokens': int, 
                        'Avg Tokens': int, 
                        'Query Count': int
                    })
                    
                    st.dataframe(country_tokens, use_container_width=True)
                    st.bar_chart(country_tokens['Total Tokens'])
                
                st.markdown("---")
                
                # Token distribution by validation mode
                if 'validation_mode' in token_df.columns:
                    st.markdown("#### Token Usage by Validation Mode")
                    
                    mode_tokens = token_df.groupby('validation_mode')['total_tokens_numeric'].agg(
                        ['sum', 'mean', 'count']
                    )
                    mode_tokens.columns = ['Total Tokens', 'Avg Tokens', 'Query Count']
                    mode_tokens = mode_tokens.astype({
                        'Total Tokens': int, 
                        'Avg Tokens': int, 
                        'Query Count': int
                    })
                    
                    st.dataframe(mode_tokens, use_container_width=True)
                
                st.markdown("---")
                
                # Historical trend
                if 'timestamp' in token_df.columns:
                    st.markdown("#### Token Usage Over Time")
                    
                    try:
                        token_df['date'] = pd.to_datetime(token_df['timestamp']).dt.date
                        daily_tokens = token_df.groupby('date')['total_tokens_numeric'].sum()
                        st.line_chart(daily_tokens)
                    except Exception as e:
                        st.warning(f"Could not generate trend chart: {str(e)}")
            else:
                st.info("📊 No token data available yet")
                st.caption("Token tracking will appear here once queries are logged")
        else:
            st.info("No token data available")
    
    # ============================================================================
    # TAB 4: COST ANALYSIS
    # ============================================================================
    with audit_tabs[3]:
        st.markdown("### 💰 Cost Analysis & Projections")
        st.caption("Track costs and project future expenses")
        
        with st.spinner("Loading cost data..."):
            cost_df = get_audit_log(limit=1000)
        
        if cost_df is not None and not cost_df.empty and 'cost' in cost_df.columns:
            # Convert cost column to numeric
            cost_df['cost_numeric'] = pd.to_numeric(cost_df['cost'], errors='coerce').fillna(0)
            
            # Cost metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_cost = safe_numeric_sum(cost_df, 'cost', 0.0)
                st.metric("Total Cost", f"${total_cost:.2f}")
            
            with col2:
                avg_cost = safe_numeric_mean(cost_df, 'cost', 0.0)
                st.metric("Avg per Query", f"${avg_cost:.4f}")
            
            with col3:
                max_cost = safe_numeric_max(cost_df, 'cost', 0.0)
                st.metric("Max Cost", f"${max_cost:.4f}")
            
            with col4:
                queries = len(cost_df)
                st.metric("Total Queries", f"{queries:,}")
            
            st.markdown("---")
            
            # Cost by country
            if 'country' in cost_df.columns:
                st.markdown("#### Cost Breakdown by Country")
                
                country_cost = cost_df.groupby('country')['cost_numeric'].agg(['sum', 'mean', 'count'])
                country_cost.columns = ['Total Cost', 'Avg Cost', 'Query Count']
                
                # Format for display
                country_cost_display = country_cost.copy()
                country_cost_display['Total Cost'] = country_cost_display['Total Cost'].apply(
                    lambda x: f"${x:.2f}"
                )
                country_cost_display['Avg Cost'] = country_cost_display['Avg Cost'].apply(
                    lambda x: f"${x:.4f}"
                )
                
                st.dataframe(country_cost_display, use_container_width=True)
            
            st.markdown("---")
            
            # Cost projection
            st.markdown("#### Cost Projection Calculator")
            st.caption("Estimate future costs based on query volume")
            
            col1, col2 = st.columns(2)
            
            with col1:
                queries_per_day = st.number_input(
                    "Expected queries per day",
                    min_value=1,
                    max_value=100000,
                    value=100,
                    step=10
                )
            
            with col2:
                projection_days = st.selectbox(
                    "Projection period (days)",
                    [7, 14, 30, 90, 180, 365],
                    index=2
                )
            
            avg_cost_per_query = safe_numeric_mean(cost_df, 'cost', 0.0)
            
            daily_cost = queries_per_day * avg_cost_per_query
            projected_cost = daily_cost * projection_days
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Daily Projected Cost", f"${daily_cost:.2f}")
            
            with col2:
                st.metric(f"{projection_days}-Day Cost", f"${projected_cost:.2f}")
            
            with col3:
                monthly_cost = daily_cost * 30
                st.metric("Monthly Projected Cost", f"${monthly_cost:.2f}")
            
            st.markdown("---")
            
            # Cost trend over time
            if 'timestamp' in cost_df.columns:
                st.markdown("#### Cost Trend Over Time")
                
                try:
                    cost_df['date'] = pd.to_datetime(cost_df['timestamp']).dt.date
                    daily_cost_actual = cost_df.groupby('date')['cost_numeric'].sum()
                    st.line_chart(daily_cost_actual)
                except Exception as e:
                    st.warning(f"Could not generate cost trend: {str(e)}")
            
            st.markdown("---")
            
            # Cost by validation mode
            if 'validation_mode' in cost_df.columns:
                st.markdown("#### Cost by Validation Mode")
                
                mode_cost = cost_df.groupby('validation_mode')['cost_numeric'].agg(['sum', 'mean', 'count'])
                mode_cost.columns = ['Total Cost', 'Avg Cost', 'Query Count']
                
                # Format for display
                mode_cost_display = mode_cost.copy()
                mode_cost_display['Total Cost'] = mode_cost_display['Total Cost'].apply(
                    lambda x: f"${x:.2f}"
                )
                mode_cost_display['Avg Cost'] = mode_cost_display['Avg Cost'].apply(
                    lambda x: f"${x:.4f}"
                )
                
                st.dataframe(mode_cost_display, use_container_width=True)
        else:
            st.info("💰 No cost data available yet")
            st.caption("Cost tracking will appear here once queries are logged")
