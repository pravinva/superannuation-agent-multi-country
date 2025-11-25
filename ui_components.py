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
from ui.theme_config import COUNTRY_COLORS, COUNTRY_FLAGS, COUNTRY_WELCOME_COLORS

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

    # Get theme for country (with fallback to Australia)
    t = COUNTRY_COLORS.get(country, COUNTRY_COLORS["Australia"])
    
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
    country_flag = COUNTRY_FLAGS.get(country, "🌐")
    
    # Get colors for current country (default to Australia if not found)
    colors = COUNTRY_WELCOME_COLORS.get(country, COUNTRY_WELCOME_COLORS["Australia"])
    
    # Render country header with flag
    st.subheader(f"{country_flag} Advisory for {country}")
    
    # ✅ Professional pension company welcome message with national color gradients
    st.markdown(f"""
    <div style="
        background: {colors['gradient']};
        padding: 28px 32px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        border-left: 4px solid {colors['border']};
        position: relative;
    ">
        <div style="
            background: {colors['text_bg']};
            padding: 16px 20px;
            border-radius: 8px;
            color: {colors['text']};
            font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.7;
            font-weight: 500;
            letter-spacing: 0.01em;
        ">
            {intro}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
        "United Kingdom": "For general information only. Not regulated financial advice. Consult an FCA-authorized advisor for personal recommendations.",
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
        from utils.audit import get_audit_log
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
    """MLflow tab - Clean production version with prompt registry."""
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Create tabs for different MLflow views
    tab1, tab2 = st.tabs(["📊 Experiment Runs", "📝 Prompt Registry"])
    
    with tab1:
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
    
    with tab2:
        st.markdown("### 📝 Prompt Registry")
        st.caption("View and iterate on prompts registered in MLflow")
        
        # ✅ Add button to manually register prompts
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("💡 **Tip:** Prompts are not automatically registered. Click the button below to register them now.")
        with col2:
            if st.button("🚀 Register Prompts Now", type="primary", use_container_width=True):
                try:
                    from prompts_registry import register_prompts_now
                    with st.spinner("Registering prompts with MLflow..."):
                        run_id = register_prompts_now()
                    if run_id:
                        st.success(f"✅ Prompts registered successfully! Run ID: `{run_id[:8]}...`")
                        st.rerun()  # Refresh to show new run
                    else:
                        st.error("❌ Failed to register prompts. Check console for details.")
                except Exception as e:
                    st.error(f"❌ Error registering prompts: {str(e)}")
                    import traceback
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())
        
        st.markdown("---")
        
        try:
            from config import MLFLOW_PROD_EXPERIMENT_PATH
            
            mlflow.set_tracking_uri("databricks")
            client = mlflow.tracking.MlflowClient()
            exp = mlflow.get_experiment_by_name(MLFLOW_PROD_EXPERIMENT_PATH)
            
            if not exp:
                st.error(f"❌ Experiment not found: `{MLFLOW_PROD_EXPERIMENT_PATH}`")
                return
            
            # Search for prompt registry runs (runs with prompt_version parameter)
            all_runs = mlflow.search_runs(
                [exp.experiment_id],
                order_by=["start_time DESC"],
                max_results=100
            )
            
            # Filter for prompt registry runs
            # Check if columns exist before filtering
            has_prompt_version = 'params.prompt_version' in all_runs.columns
            has_run_name = 'tags.mlflow.runName' in all_runs.columns
            
            if has_prompt_version and has_run_name:
                prompt_runs = all_runs[
                    all_runs['tags.mlflow.runName'].str.contains('prompts_', na=False, case=False) |
                    all_runs['params.prompt_version'].notna()
                ]
            elif has_run_name:
                # Only filter by run name if prompt_version column doesn't exist
                prompt_runs = all_runs[
                    all_runs['tags.mlflow.runName'].str.contains('prompts_', na=False, case=False)
                ]
            elif has_prompt_version:
                # Only filter by prompt_version if run name column doesn't exist
                prompt_runs = all_runs[
                    all_runs['params.prompt_version'].notna()
                ]
            else:
                # No filtering columns available, try to fetch individual runs
                prompt_runs = pd.DataFrame()
            
            if prompt_runs.empty:
                st.info("ℹ️ No prompt registry runs found yet.")
                st.caption("Prompts are registered automatically when the system starts.")
                st.markdown("""
                **To register prompts manually:**
                ```python
                from prompts_registry import register_prompts_now
                register_prompts_now()
                ```
                """)
                return
            
            st.success(f"✅ Found {len(prompt_runs)} prompt registry version(s)")
            
            # Show prompt versions
            st.markdown("**📋 Prompt Versions**")
            prompt_versions = []
            for _, run_row in prompt_runs.iterrows():
                run_id = run_row['run_id']
                try:
                    run = client.get_run(run_id)
                    # Check if prompt_version parameter exists
                    version = run.data.params.get('prompt_version', None)
                    if version is None:
                        # Skip runs without prompt_version
                        continue
                    reg_time = run.data.params.get('registration_time', run.info.start_time)
                    prompt_versions.append({
                        'version': version,
                        'run_id': run_id,
                        'registered': reg_time,
                        'run_name': run.info.run_name
                    })
                except Exception as e:
                    # Skip runs that can't be loaded
                    continue
            
            if not prompt_versions:
                st.info("ℹ️ No prompt registry runs found yet.")
                st.caption("Prompts are registered automatically when the system starts.")
                st.markdown("""
                **To register prompts manually:**
                ```python
                from prompts_registry import register_prompts_now
                register_prompts_now()
                ```
                """)
                return
            
            st.success(f"✅ Found {len(prompt_versions)} prompt registry version(s)")
            
            # Sort by version (newest first)
            prompt_versions.sort(key=lambda x: x['registered'], reverse=True)
            
            # Version selector
            version_options = [f"{v['version']} ({v['registered'][:10]})" for v in prompt_versions]
            selected_version_idx = st.selectbox(
                "Select prompt version to view:",
                range(len(version_options)),
                format_func=lambda x: version_options[x]
            )
            
            selected_version = prompt_versions[selected_version_idx]
            selected_run_id = selected_version['run_id']
            
            st.markdown(f"**Version:** `{selected_version['version']}` | **Run ID:** `{selected_run_id[:8]}...`")
            
            # Fetch artifacts for this run
            try:
                run = client.get_run(selected_run_id)
                
                # List artifacts
                artifact_uri = run.info.artifact_uri
                artifacts = []
                try:
                    from mlflow.tracking.artifact_utils import _download_artifact_from_uri
                    import os
                    import tempfile
                    
                    # Get artifact list
                    artifact_list = client.list_artifacts(selected_run_id, "prompts")
                    artifacts = [art.path for art in artifact_list if art.path.startswith("prompts/")]
                    
                    if artifacts:
                        st.markdown("**📝 Registered Prompts**")
                        
                        # Display each prompt
                        for artifact_path in sorted(artifacts):
                            prompt_name = artifact_path.replace("prompts/", "").replace(".txt", "").replace(".json", "")
                            
                            with st.expander(f"📄 {prompt_name.replace('_', ' ').title()}", expanded=False):
                                try:
                                    # Download and display artifact
                                    with tempfile.TemporaryDirectory() as tmpdir:
                                        local_path = client.download_artifacts(selected_run_id, artifact_path, tmpdir)
                                        with open(local_path, 'r') as f:
                                            content = f.read()
                                        
                                        # Display with copy button
                                        st.code(content, language='text')

                                        # Copy button
                                        # Escape content for JavaScript (can't use backslash in f-string expression)
                                        escaped_content = content.replace('`', '\\`').replace('$', '\\$')
                                        st.markdown(f"""
                                        <button onclick="navigator.clipboard.writeText(`{escaped_content}`)"
                                                style="padding: 8px 16px; background: #00843D; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                            📋 Copy Prompt
                                        </button>
                                        """, unsafe_allow_html=True)
                                        
                                except Exception as e:
                                    st.error(f"Error loading {prompt_name}: {e}")
                                    
                    else:
                        st.warning("⚠️ No prompt artifacts found in this run.")
                        st.caption("Prompts may not have been registered yet, or artifacts were not logged.")
                
                except Exception as e:
                    st.warning(f"⚠️ Could not load artifacts: {e}")
                    st.caption("Try downloading artifacts directly from MLflow UI.")
                
                # Show metadata
                with st.expander("📊 Prompt Metadata"):
                    if run.data.params:
                        st.json(run.data.params)
                    if run.data.metrics:
                        st.json(run.data.metrics)
            
            except Exception as e:
                st.error(f"Error loading prompt version: {e}")
                import traceback
                st.code(traceback.format_exc())
        
        except Exception as e:
            logger.error(f"Prompt registry error: {e}", exc_info=True)
            st.error(f"❌ Error loading prompt registry: {str(e)[:200]}")
            import traceback
            with st.expander("Error details"):
                st.code(traceback.format_exc())

def render_cost_analysis_tab():
    """Cost Analysis tab - Clean production version with last run cost."""
    import pandas as pd
    import logging
    
    # Set up logging (messages go to console, not Streamlit)
    logger = logging.getLogger(__name__)
    
    st.markdown("### 💰 Cost Analysis Dashboard")
    
    try:
        from utils.audit import get_query_cost
        
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
                from utils.audit import get_audit_log
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
    """Update config/config.yaml with all settings."""
    import os
    import yaml
    from pathlib import Path

    try:
        # Path to config.yaml
        config_dir = Path(__file__).parent / "config"
        config_file = config_dir / "config.yaml"

        # Load current config
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Update values
        config['databricks']['sql_warehouse_id'] = sql_id
        config['llm']['temperature'] = float(main_temp)
        config['llm']['max_tokens'] = int(main_tokens)
        config['validation_llm']['temperature'] = float(judge_temp)
        config['validation_llm']['max_tokens'] = int(judge_tokens)

        # Write back to file
        with open(config_file, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

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

