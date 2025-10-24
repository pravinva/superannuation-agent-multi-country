# ui_components.py - UPDATED FOR 12 UC FUNCTIONS (3 per country)
"""
UI components for the retirement advisory app
NOW DISPLAYS: Tax + Government Benefit + Projection for ALL countries
"""

import streamlit as st
import os
import pandas as pd

# Temporary inline config
BRANDCONFIG = {
    "brand_name": "Global Retirement Advisory",
    "subtitle": "Enterprise-Grade Agentic AI on Databricks"
}


def render_logo():
    """Render brand title and subtitle"""
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
