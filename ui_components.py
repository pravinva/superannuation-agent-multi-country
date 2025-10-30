# ui_components.py — CORRECTED VERSION
"""
Global Retirement Advisory UI Components
✅ Working CSS restored
✅ Full error handling from test files
✅ Step-by-step debugging enabled
"""

import streamlit as st
import pandas as pd
import mlflow
from databricks.sdk import WorkspaceClient

BRANDCONFIG = {
    "brand_name": "Global Retirement Advisory",
    "subtitle": "Enterprise-Grade Agentic AI on Databricks",
}

def apply_custom_styles():
    """Apply card-style tabs with gold-green theme — FIXED CSS."""
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        width: 100%;
        border-bottom: 3px solid #00843D;
        padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 70px;
        flex: 1;
        background-color: #f8f9fa;
        border: none;
        border-radius: 8px 8px 0 0;
        color: #2c3e50;
        font-size: 18px;
        font-weight: 600;
        padding: 1rem 2rem;
        margin: 0 2px;
        transition: all 0.3s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #FFD700 0%, #00843D 100%);
        color: white;
        transform: translateY(-3px);
        box-shadow: 0 4px 8px rgba(0,132,61,0.3);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00843D 0%, #FFD700 100%);
        color: white !important;
        border-bottom: 3px solid #FFD700;
    }
    </style>
    """, unsafe_allow_html=True)

def render_logo():
    apply_custom_styles()
    st.markdown(f"## 🏦 {BRANDCONFIG['brand_name']}")
    st.caption(BRANDCONFIG["subtitle"])

# Advisory functions
def render_member_card(member, is_selected=False, country="Australia"):
    """Render member card with flags, colors, and country-specific currency."""
    
    # Complete color/currency config with ALL keys
    colors = {
        "Australia": {
            "flag": "🇦🇺", 
            "primary": "#FFD700", 
            "secondary": "#00843D", 
            "currency": "A$"
        },
        "USA": {
            "flag": "🇺🇸", 
            "primary": "#B22234", 
            "secondary": "#3C3B6E", 
            "currency": "$"
        },
        "United Kingdom": {
            "flag": "🇬🇧", 
            "primary": "#C8102E", 
            "secondary": "#012169", 
            "currency": "£"
        },
        "India": {
            "flag": "🇮🇳", 
            "primary": "#FF9933", 
            "secondary": "#138808", 
            "currency": "₹"
        }
    }
    
    # Get theme for country (with fallback to Australia)
    t = colors.get(country, colors["Australia"])
    
    # Styling based on selection state
    border = f"5px solid {t['secondary']}" if is_selected else "1px solid #CCC"
    bg = f"linear-gradient(135deg,{t['primary']}22,{t['secondary']}10)" if is_selected else "#FFF"
    shadow = "0 6px 14px rgba(0,0,0,0.15)" if is_selected else "0 1px 4px rgba(0,0,0,0.08)"
    
    # Extract member data
    label = member.get("name", "Unknown")
    age = member.get("age", "N/A")
    bal = member.get("super_balance", 0)
    
    # Format balance with country-specific currency
    bal_fmt = f"{t['currency']}{int(bal):,}"
    
    # Render card
    st.markdown(
        f"""
        <div style="background:{bg};border:{border};box-shadow:{shadow};
                    border-radius:10px;padding:14px;margin-bottom:10px;">
            <b>{t['flag']} {label}</b><br>
            Age: {age} • Balance: {bal_fmt}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_country_welcome(country, intro, disclaimer):
    # Select appropriate flag for the chosen country
    flags = {
        "Australia": "🇦🇺",
        "USA": "🇺🇸",
        "United Kingdom": "🇬🇧",
        "India": "🇮🇳"
    }
    country_flag = flags.get(country, "🌐")

    # Render country header with flag
    st.subheader(f"{country_flag} Advisory for {country}")

    # Render main introduction
    st.info(intro)

    # Render disclaimer if available
    if disclaimer:
        st.caption(f"⚠️ {disclaimer}")

def render_question_card(question, example=False):
    border = "2px dashed #AFAFAF" if example else "2px solid #00843D"
    bg = "#F9F9F9" if example else "#E8F5E9"
    st.markdown(f"""
        <div style="background:{bg};border:{border};
                    border-radius:8px;padding:10px;margin-bottom:8px;">
            💬 {question}
        </div>
    """,unsafe_allow_html=True)

def render_postanswer_disclaimer(country):
    notes = {
        "Australia": "Superannuation results are summaries only; verify with your fund.",
        "USA": "Assumes 401(k) contribution plan; verify withdrawal rules with IRS.",
        "United Kingdom": "Complies with pension calculation guidelines but not FCA advice.",
        "India": "EPF corpus shown for typical contribution/interest; consult EPFO portal.",
    }
    st.caption(f"⚠️ {notes.get(country, 'General retirement illustration only.')}")

def render_audit_table(df):
    if df is None or df.empty:
        st.warning("No audit log entries found.")
        return
    try:
        def color_verdict(v):
            if isinstance(v, str):
                if v.lower() == "pass": return "background-color:#E8F5E9;color:#2E7D32;"
                if v.lower() == "fail": return "background-color:#FFEBEE;color:#C62828;"
            return ""
        sty = df.style.applymap(color_verdict, subset=["judge_verdict"]) \
            if "judge_verdict" in df.columns else df.style
        st.dataframe(sty, use_container_width=True)
    except Exception as e:
        st.error(f"Audit table render error: {e}")

# GOVERNANCE TABS — WITH FULL ERROR HANDLING FROM TEST FILES

def render_enhanced_audit_tab():
    st.markdown("### 🧾 Governance & Audit Data")
    try:
        from audit.audit_utils import get_audit_log
        result = get_audit_log()
        df = pd.DataFrame(result) if isinstance(result, list) else result
        if df.empty:
            st.info("No audit records available.")
            return
        countries = sorted(df["country"].dropna().unique().tolist()) if "country" in df else []
        users = sorted(df["user_id"].dropna().unique().tolist()) if "user_id" in df else []
        sessions = sorted(df["session_id"].dropna().unique().tolist()) if "session_id" in df else []
        
        c1, c2, c3 = st.columns(3)
        with c1: f1 = st.selectbox("Filter Country", ["All"] + countries)
        with c2: f2 = st.selectbox("Filter User", ["All"] + users)
        with c3: f3 = st.selectbox("Filter Session", ["All"] + sessions)
        
        if f1 != "All": df = df[df["country"] == f1]
        if f2 != "All": df = df[df["user_id"] == f2]
        if f3 != "All": df = df[df["session_id"] == f3]
        
        render_audit_table(df)
    except Exception as e:
        st.error(f"❌ Audit tab error: {e}")
        import traceback
        st.code(traceback.format_exc())

def render_mlflow_traces_tab():
    """MLflow tab - Clean production version."""
    import logging
    
    logger = logging.getLogger(__name__)
    st.markdown("### 📊 MLflow Experiments & Evaluations")
    
    try:
        from config import MLFLOW_PROD_EXPERIMENT_PATH
        
        logger.info("Setting up MLflow connection...")
        mlflow.set_tracking_uri("databricks")
        
        client = mlflow.tracking.MlflowClient()
        exp = mlflow.get_experiment_by_name(MLFLOW_PROD_EXPERIMENT_PATH)
        
        if not exp:
            st.error(f"❌ Experiment not found: `{MLFLOW_PROD_EXPERIMENT_PATH}`")
            st.caption("Verify the experiment exists in your Databricks workspace.")
            return
        
        # Success - show experiment info
        st.success(f"✅ Connected to experiment: **{exp.name}**")
        st.caption(f"Experiment ID: `{exp.experiment_id}` | Tracking URI: `{mlflow.get_tracking_uri()}`")
        
        logger.info(f"Fetching runs from experiment {exp.experiment_id}...")
        runs = mlflow.search_runs(
            [exp.experiment_id],
            order_by=["start_time DESC"],
            max_results=10
        )
        
        if runs.empty:
            st.info("ℹ️ No MLflow runs logged yet. Run some queries to populate this tab.")
            return
        
        st.markdown(f"**Recent Runs** ({len(runs)} most recent)")
        display_cols = ["run_id", "status", "start_time", "end_time"]
        
        # Add metrics if they exist
        metric_cols = [c for c in runs.columns if c.startswith("metrics.")]
        if metric_cols:
            display_cols += metric_cols[:3]  # Show first 3 metrics
        
        st.dataframe(runs[display_cols], use_container_width=True)
        
        st.markdown("---")
        
        # Run inspector
        st.subheader("🔍 Inspect Individual Run")
        selected = st.selectbox("Choose run to inspect:", runs["run_id"].tolist())
        
        if selected:
            run_details = client.get_run(selected)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**⚙️ Parameters**")
                if run_details.data.params:
                    st.json(run_details.data.params)
                else:
                    st.caption("No parameters logged")
            
            with col2:
                st.markdown("**📈 Metrics**")
                if run_details.data.metrics:
                    st.json(run_details.data.metrics)
                else:
                    st.caption("No metrics logged")
            
            # Show tags if any
            if run_details.data.tags:
                with st.expander("🏷️ Tags"):
                    st.json(run_details.data.tags)
            
    except Exception as e:
        logger.error(f"MLflow error: {e}", exc_info=True)
        st.error(f"❌ MLflow connection failed: {str(e)[:100]}")
        st.caption("Check your Databricks CLI authentication and experiment path.")

def render_cost_analysis_tab():
    """Cost Analysis tab - Clean production version with last run cost."""
    import pandas as pd
    import logging
    
    # Set up logging (messages go to console, not Streamlit)
    logger = logging.getLogger(__name__)
    
    st.markdown("### 💰 Cost Analysis Dashboard")
    
    try:
        from audit.audit_utils import get_query_cost
        
        logger.info("Loading cost data from UC governance...")
        data = get_query_cost(limit=100)
        
        if data and len(data) > 0:
            df = pd.DataFrame(data)
            
            # Convert to numeric
            df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce')
            df['avg_cost'] = pd.to_numeric(df['avg_cost'], errors='coerce')
            df['query_count'] = pd.to_numeric(df['query_count'], errors='coerce')
            
            # Calculate totals
            total_cost = df['total_cost'].sum()
            total_queries = df['query_count'].sum()
            overall_avg = total_cost / total_queries if total_queries > 0 else 0
            
            # Get last run cost (most recent query)
            try:
                from audit.audit_utils import get_audit_log
                audit_data = get_audit_log(limit=1)  # Get most recent run
                if audit_data:
                    last_run = audit_data[0]
                    last_cost = float(last_run.get('cost', 0))
                else:
                    last_cost = 0
            except:
                last_cost = 0
            
            # Display key metrics (4 columns with last run prominent)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Cost", f"${total_cost:.4f}")
            
            with col2:
                st.metric("Total Queries", f"{int(total_queries)}")
            
            with col3:
                st.metric("Avg Cost/Query", f"${overall_avg:.5f}")
            
            with col4:
                # Highlight last run cost
                st.metric(
                    "Last Run Cost", 
                    f"${last_cost:.5f}",
                    delta=f"{((last_cost - overall_avg) / overall_avg * 100):.1f}%" if overall_avg > 0 else None,
                    delta_color="inverse"  # Red if higher than average
                )
            
            st.markdown("---")
            
            # Cost by country chart
            st.markdown("**Total Cost by Country**")
            country_costs = df.groupby('country')['total_cost'].sum().sort_values(ascending=False)
            st.bar_chart(country_costs)
            
            # Cost by user chart
            st.markdown("**Top Users by Cost**")
            user_costs = df.groupby('user_id')['total_cost'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(user_costs)
            
            # Detailed breakdown (expandable)
            with st.expander("📊 Detailed Cost Breakdown"):
                display_df = df.copy()
                display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x:.4f}")
                display_df['avg_cost'] = display_df['avg_cost'].apply(lambda x: f"${x:.5f}")
                display_df['query_count'] = display_df['query_count'].astype(int)
                st.dataframe(display_df, use_container_width=True)
            
        else:
            st.warning("⚠️ No cost data available yet. Run some queries first!")
    
    except Exception as e:
        logger.error(f"Cost analysis error: {e}", exc_info=True)
        st.error(f"❌ Unable to load cost data: {str(e)[:100]}")

def render_configuration_tab():
    """Configuration tab with warehouses, dual LLM params, and offline evaluation."""
    from databricks.sdk.service.sql import EndpointInfoWarehouseType
    import os
    
    st.markdown("### ⚙️ Databricks Workspace Configuration")
    st.caption("Manage SQL warehouse, LLM settings, and offline evaluations.")
    
    # ===== WAREHOUSE SELECTOR =====
    st.subheader("📦 SQL Warehouse")
    try:
        w = WorkspaceClient()
        with st.spinner("Loading warehouses..."):
            warehouses = list(w.warehouses.list())
        
        valid = [wh for wh in warehouses
                 if getattr(wh, "warehouse_type", None) in 
                    [EndpointInfoWarehouseType.PRO, EndpointInfoWarehouseType.CLASSIC]]
        
        if not valid:
            st.warning("No Serverless or PRO warehouses available.")
            selected_id = None
        else:
            # Load current warehouse from config
            from config import SQL_WAREHOUSE_ID
            current_wh = next((wh for wh in valid if wh.id == SQL_WAREHOUSE_ID), None)
            default_idx = valid.index(current_wh) if current_wh else 0
            
            opts = [f"{wh.name} ({wh.id[:8]}...)" for wh in valid]
            sel = st.selectbox("Select Warehouse:", opts, index=default_idx)
            selected_id = valid[opts.index(sel)].id
            
            wh = next((w for w in valid if w.id == selected_id), None)
            if wh:
                st.caption(f"**Status:** {wh.state.value if wh.state else 'N/A'}")
                st.caption(f"**Type:** {wh.warehouse_type.value if wh.warehouse_type else 'N/A'}")
    except Exception as e:
        st.error(f"Warehouse load error: {e}")
        selected_id = None
    
    st.markdown("---")
    
    # ===== DUAL LLM CONFIGURATION =====
    st.subheader("🤖 LLM Configuration")
    
    # Load current values from config
    from config import (
        MAIN_LLM_TEMPERATURE, MAIN_LLM_MAX_TOKENS,
        JUDGE_LLM_TEMPERATURE, JUDGE_LLM_MAX_TOKENS
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Main Advisory LLM** (Claude Opus 4.1)")
        main_temp = st.slider(
            "Main Temperature", 
            0.0, 1.0, 
            float(MAIN_LLM_TEMPERATURE), 
            0.05, 
            key="main_temp",
            help="Controls creativity. Lower = more factual."
        )
        main_tokens = st.number_input(
            "Main Max Tokens", 
            100, 4000, 
            int(MAIN_LLM_MAX_TOKENS), 
            50, 
            key="main_tokens",
            help="Maximum response length for advisory answers."
        )

    with col2:
        st.markdown("**Judge Validation LLM** (Claude Sonnet 4)")
        judge_temp = st.slider(
            "Judge Temperature", 
            0.0, 1.0, 
            float(JUDGE_LLM_TEMPERATURE), 
            0.05, 
            key="judge_temp",
            help="Lower = more consistent validation."
        )
        judge_tokens = st.number_input(
            "Judge Max Tokens", 
            100, 1000, 
            int(JUDGE_LLM_MAX_TOKENS), 
            50, 
            key="judge_tokens",
            help="Maximum length for validation responses."
        )
    
    # Save button
    if st.button("💾 Save All Configuration", type="primary"):
        success = update_all_configuration(selected_id, main_temp, main_tokens, judge_temp, judge_tokens)
        if success:
            st.success("✅ Configuration saved! Restart the app to apply changes.")
            st.info("🔄 Run: `streamlit run app.py` to reload with new settings.")
        else:
            st.error("❌ Failed to save configuration.")
    
    st.markdown("---")
    
    # ===== OFFLINE EVALUATION =====
    st.subheader("🧪 Offline Evaluation")
    st.caption("Upload a CSV file with columns: `user_id`, `country`, `query_str`")
    
    uploaded_csv = st.file_uploader(
        "Upload Evaluation CSV", 
        type=["csv"],
        help="CSV must contain: user_id, country, query_str"
    )
    
    if uploaded_csv:
        try:
            df_preview = pd.read_csv(uploaded_csv)
            st.info(f"📄 Uploaded: {uploaded_csv.name} ({len(df_preview)} rows)")
            
            with st.expander("Preview Data"):
                st.dataframe(df_preview.head(10), use_container_width=True)
            
            uploaded_csv.seek(0)
            
            if st.button("▶️ Run Offline Evaluation", type="primary"):
                from run_evaluation import run_csv_evaluation
                
                st.info("🔄 Running offline evaluation... This may take a few minutes.")
                
                with st.spinner("Processing queries..."):
                    try:
                        result = run_csv_evaluation(uploaded_csv)
                        
                        if "error" in result:
                            st.error(f"❌ Evaluation failed: {result['error']}")
                        else:
                            st.success(f"✅ Evaluation complete! Processed {result['total_queries']} queries.")
                            st.json(result)
                            
                            from config import MLFLOW_OFFLINE_EVAL_PATH
                            st.info(f"📊 Results logged to MLflow: `{MLFLOW_OFFLINE_EVAL_PATH}`")
                            
                    except Exception as e:
                        st.error(f"❌ Evaluation error: {e}")
                        import traceback
                        st.code(traceback.format_exc())
        
        except Exception as e:
            st.error(f"❌ Invalid CSV: {e}")
    else:
        st.info("ℹ️ Upload a CSV file to begin offline evaluation.")
    
    # Example CSV
    with st.expander("📋 CSV Format Example"):
        example_df = pd.DataFrame({
            "user_id": ["AU001", "US002", "UK003"],
            "country": ["Australia", "USA", "United Kingdom"],
            "query_str": [
                "How much superannuation will I have at retirement?",
                "What's my 401k balance?",
                "When can I access my pension?"
            ]
        })
        st.dataframe(example_df, use_container_width=True)
        st.download_button(
            label="⬇️ Download Example CSV",
            data=example_df.to_csv(index=False),
            file_name="eval_example.csv",
            mime="text/csv"
        )


def update_all_configuration(sql_id, main_temp, main_tokens, judge_temp, judge_tokens):
    """Update config.py with all settings."""
    import os
    try:
        cfg = os.path.join(os.path.dirname(__file__), "config.py")
        with open(cfg, "r") as f:
            lines = f.readlines()
        
        with open(cfg, "w") as f:
            for line in lines:
                if line.strip().startswith("SQL_WAREHOUSE_ID ="):
                    f.write(f'SQL_WAREHOUSE_ID = "{sql_id}"\n')
                elif line.strip().startswith("MAIN_LLM_TEMPERATURE ="):
                    f.write(f"MAIN_LLM_TEMPERATURE = {main_temp}\n")
                elif line.strip().startswith("MAIN_LLM_MAX_TOKENS ="):
                    f.write(f"MAIN_LLM_MAX_TOKENS = {main_tokens}\n")
                elif line.strip().startswith("JUDGE_LLM_TEMPERATURE ="):
                    f.write(f"JUDGE_LLM_TEMPERATURE = {judge_temp}\n")
                elif line.strip().startswith("JUDGE_LLM_MAX_TOKENS ="):
                    f.write(f"JUDGE_LLM_MAX_TOKENS = {judge_tokens}\n")
                else:
                    f.write(line)
        return True
    except Exception as e:
        import logging
        logging.error(f"Config save error: {e}")
        return False

# ============================================================================ #
# VALIDATION RESULT RENDERING (NEW)
# ============================================================================ #

from config import LLM_JUDGE_CONFIDENCE_THRESHOLD
def render_validation_results(validation, timings):
    """Render LLM Judge validation results in a nice card with confidence threshold."""
    if not validation:
        return

    passed = validation.get("passed", False)
    confidence = validation.get("confidence", 0.0)
    violations = validation.get("violations", [])
    validation_time = validation.get("duration", 0)

    if isinstance(validation_time, dict):
        validation_time = validation_time.get("total", 0)
    elif not isinstance(validation_time, (int, float)):
        validation_time = 0

    # --- Red Box: Real flag only when confidence >= threshold and violations exist
    if len(violations) > 0 and confidence >= LLM_JUDGE_CONFIDENCE_THRESHOLD:
        st.markdown(f"""
            <div style="background:#FFEBEE;border-left:4px solid #DC2626;
                        padding:1rem;border-radius:8px;margin:1rem 0;">
                ❌ <strong>LLM Judge: FLAGGED</strong><br>
                Found {len(violations)} potential issues<br>
                Model: {validation.get('judge_model', 'Claude Sonnet 4')} •
                Confidence: {confidence:.0%} •
                Time: {validation_time:.2f}s
            </div>
        """, unsafe_allow_html=True)

    # --- Amber Box: Low confidence, generic caution
    elif len(violations) > 0 and confidence < LLM_JUDGE_CONFIDENCE_THRESHOLD:
        st.markdown(f"""
            <div style="background:#FFF8E1;border-left:4px solid #F59E0B;
                        padding:1rem;border-radius:8px;margin:1rem 0;">
                ⚠️ <strong>LLM Judge: Low Confidence</strong><br>
                {len(violations)} potential issue(s) detected, but judge confidence is only {confidence:.0%}.<br>
                Please review manually.
            </div>
        """, unsafe_allow_html=True)

    # --- Green Box: Full pass or no issues
    else:
        label = "PASSED" if passed else "COMPLETED (NO FLAGGED ISSUES)"
        st.markdown(f"""
            <div style="background:#E8F5E9;border-left:4px solid #16A34A;
                        padding:1rem;border-radius:8px;margin:1rem 0;">
                ✅ <strong>LLM Judge: {label}</strong><br>
                Model: {validation.get('judge_model', 'Claude Sonnet 4')} •
            </div>
        """, unsafe_allow_html=True)


def render_performance_metrics(timings):
    """Render performance metrics in an expander."""
    if not isinstance(timings, dict):
        return
    
    total_time = timings.get('total_elapsed', 0)
    
    with st.expander("⏱️ Performance Metrics", expanded=False):
        st.markdown(f"""
        **Performance Breakdown:**
        
        - **Total Time:** {total_time:.2f}s
        
        **LLM Calls:**
        - Planning: {timings.get('planning', 0):.2f}s
        - Synthesis: {timings.get('synthesis', 0):.2f}s
        
        **Tools:**
        - Tax Calculation: {timings.get('tax_calc', 0):.2f}s
        - Pension Check: {timings.get('pension', 0):.2f}s
        - Projection: {timings.get('projection', 0):.2f}s
        
        **Validation:**
        - LLM Judge: {timings.get('validation', 0):.2f}s
        """)

