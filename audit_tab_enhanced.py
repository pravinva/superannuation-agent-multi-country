# audit_tab_enhanced.py

"""
Enhanced Audit Tab with MLflow Traces and Metrics
Displays audit logs, MLflow runs, token usage, and cost analysis

✅ FIXED: Type safety for numeric columns (cost, tokens, time)
✅ FIXED: Proper pandas numeric conversion with error handling
"""

import streamlit as st
import pandas as pd
import mlflow
from datetime import datetime, timedelta

# ✅ FIXED: Correct import path
from audit.audit_utils import get_audit_log
from config import MLFLOW_PROD_EXPERIMENT_PATH, get_governance_table_path


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


def render_enhanced_audit_tab():
    """
    Render enhanced audit tab with:
    1. Governance table audit logs
    2. MLflow traces and metrics
    3. Token usage analysis
    4. Cost analysis
    """
    
    st.header("📊 Audit Trail & MLflow Traces")
    st.markdown("View governance logs, MLflow experiments, token usage, and cost analysis")
    
    # Create tabs for different views
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
                ["All", "Pass", "Fail", "ERROR"],
                key="gov_verdict_filter"
            )
        
        with col3:
            validation_mode_filter = st.selectbox(
                "Filter by Validation Mode",
                ["All", "llm_judge", "hybrid", "deterministic"],
                key="gov_validation_filter"
            )
        
        # Build filter dict
        filters = {}
        if country_filter != "All":
            filters['country'] = country_filter
        if verdict_filter != "All":
            filters['judge_verdict'] = verdict_filter
        if validation_mode_filter != "All":
            filters['validation_mode'] = validation_mode_filter
        
        # Load data with caching
        @st.cache_data(ttl=60)
        def load_governance_logs(country=None, verdict=None, mode=None):
            """Load and cache governance logs"""
            kwargs = {}
            if country:
                kwargs['country'] = country
            if verdict:
                kwargs['judge_verdict'] = verdict
            if mode:
                kwargs['validation_mode'] = mode
            
            return get_audit_log(limit=500, **kwargs)
        
        with st.spinner("Loading governance logs..."):
            gov_df = load_governance_logs(
                filters.get('country'),
                filters.get('judge_verdict'),
                filters.get('validation_mode')
            )
        
        if gov_df is not None and not gov_df.empty:
            st.markdown(f"**{len(gov_df)} records found**")
            
            # Summary metrics with safe numeric conversion
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
                avg_tokens = safe_numeric_mean(gov_df, 'total_tokens', 0.0)
                st.metric("Avg Tokens", f"{int(avg_tokens)}")
            
            # Display table
            st.markdown("---")
            
            # Select columns to display
            display_cols = ['timestamp', 'country', 'query_string', 'judge_verdict', 
                          'validation_mode', 'cost', 'total_tokens']
            available_cols = [col for col in display_cols if col in gov_df.columns]
            
            st.dataframe(
                gov_df[available_cols].head(100),
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
            st.info("No governance logs found. Try adjusting filters.")
    
    # ============================================================================
    # TAB 2: MLFLOW TRACES
    # ============================================================================
    with audit_tabs[1]:
        st.markdown("### 🔬 MLflow Experiment Traces")
        st.caption("View MLflow runs, parameters, and metrics")
        
        try:
            # Set MLflow tracking URI and experiment
            mlflow.set_tracking_uri("databricks")
            
            if MLFLOW_PROD_EXPERIMENT_PATH:
                try:
                    experiment = mlflow.get_experiment_by_name(MLFLOW_PROD_EXPERIMENT_PATH)
                    
                    if experiment:
                        st.success(f"✅ Connected to experiment: `{MLFLOW_PROD_EXPERIMENT_PATH}`")
                        
                        # Search runs
                        runs = mlflow.search_runs(
                            experiment_ids=[experiment.experiment_id],
                            max_results=50,
                            order_by=["start_time DESC"]
                        )
                        
                        if not runs.empty:
                            st.markdown(f"**{len(runs)} runs found**")
                            
                            # Key metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                total_runs = len(runs)
                                st.metric("Total Runs", total_runs)
                            
                            with col2:
                                successful_runs = runs[runs['status'] == 'FINISHED'].shape[0] if 'status' in runs.columns else 0
                                st.metric("Successful", successful_runs)
                            
                            with col3:
                                failed_runs = runs[runs['status'] == 'FAILED'].shape[0] if 'status' in runs.columns else 0
                                st.metric("Failed", failed_runs)
                            
                            with col4:
                                if 'end_time' in runs.columns and 'start_time' in runs.columns:
                                    try:
                                        avg_duration = runs['end_time'] - runs['start_time']
                                        avg_seconds = avg_duration.mean().total_seconds()
                                        st.metric("Avg Duration", f"{avg_seconds:.1f}s")
                                    except Exception:
                                        st.metric("Avg Duration", "N/A")
                                else:
                                    st.metric("Avg Duration", "N/A")
                            
                            # Display runs table
                            st.markdown("---")
                            st.markdown("#### Recent Runs")
                            
                            display_cols = ['run_id', 'status', 'start_time', 'end_time']
                            available_cols = [col for col in display_cols if col in runs.columns]
                            
                            # Add metrics columns if they exist
                            metric_cols = [col for col in runs.columns if col.startswith('metrics.')]
                            available_cols.extend(metric_cols[:5])  # Show first 5 metrics
                            
                            st.dataframe(
                                runs[available_cols].head(20),
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Expandable run details
                            with st.expander("🔍 Detailed Run Information"):
                                selected_run_id = st.selectbox(
                                    "Select Run ID",
                                    runs['run_id'].tolist()
                                )
                                
                                if selected_run_id:
                                    run = mlflow.get_run(selected_run_id)
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("**Parameters:**")
                                        st.json(run.data.params)
                                    
                                    with col2:
                                        st.markdown("**Metrics:**")
                                        st.json(run.data.metrics)
                        else:
                            st.info("No runs found in this experiment")
                    else:
                        st.warning(f"⚠️ Experiment not found: {MLFLOW_PROD_EXPERIMENT_PATH}")
                
                except Exception as e:
                    st.error(f"❌ Error accessing MLflow: {str(e)}")
            else:
                st.warning("⚠️ MLFLOW_PROD_EXPERIMENT_PATH not configured")
        
        except Exception as e:
            st.error(f"❌ MLflow connection error: {str(e)}")
            st.info("Ensure MLflow is properly configured and accessible")
    
    # ============================================================================
    # TAB 3: TOKEN ANALYSIS
    # ============================================================================
    with audit_tabs[2]:
        st.markdown("### 📊 Token Usage Analysis")
        st.caption("Analyze token consumption patterns")
        
        with st.spinner("Loading token data..."):
            token_df = get_audit_log(limit=1000)
        
        if token_df is not None and not token_df.empty and 'total_tokens' in token_df.columns:
            # Token metrics with safe conversion
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
                
                # Convert to numeric first
                token_df['total_tokens_numeric'] = pd.to_numeric(token_df['total_tokens'], errors='coerce').fillna(0)
                
                country_tokens = token_df.groupby('country')['total_tokens_numeric'].agg(['sum', 'mean', 'count'])
                country_tokens.columns = ['Total Tokens', 'Avg Tokens', 'Query Count']
                country_tokens = country_tokens.astype({'Total Tokens': int, 'Avg Tokens': int, 'Query Count': int})
                
                st.dataframe(country_tokens, use_container_width=True)
                
                # Bar chart
                st.bar_chart(country_tokens['Total Tokens'])
            
            st.markdown("---")
            
            # Token distribution by validation mode
            if 'validation_mode' in token_df.columns:
                st.markdown("#### Token Usage by Validation Mode")
                
                mode_tokens = token_df.groupby('validation_mode')['total_tokens_numeric'].agg(['sum', 'mean', 'count'])
                mode_tokens.columns = ['Total Tokens', 'Avg Tokens', 'Query Count']
                mode_tokens = mode_tokens.astype({'Total Tokens': int, 'Avg Tokens': int, 'Query Count': int})
                
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
            st.info("No token data available")
    
    # ============================================================================
    # TAB 4: COST ANALYSIS
    # ============================================================================
    with audit_tabs[3]:
        st.markdown("### 💰 Cost Analysis")
        st.caption("Track and project costs")
        
        with st.spinner("Loading cost data..."):
            cost_df = get_audit_log(limit=1000)
        
        if cost_df is not None and not cost_df.empty and 'cost' in cost_df.columns:
            # Convert cost column to numeric
            cost_df['cost_numeric'] = pd.to_numeric(cost_df['cost'], errors='coerce').fillna(0)
            
            # Cost metrics with safe conversion
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
                
                # Format the display
                country_cost_display = country_cost.copy()
                country_cost_display['Total Cost'] = country_cost_display['Total Cost'].apply(lambda x: f"${x:.2f}")
                country_cost_display['Avg Cost'] = country_cost_display['Avg Cost'].apply(lambda x: f"${x:.4f}")
                
                st.dataframe(country_cost_display, use_container_width=True)
            
            st.markdown("---")
            
            # Cost projection
            st.markdown("#### Cost Projection")
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
                    "Projection period",
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
                
                # Format the display
                mode_cost_display = mode_cost.copy()
                mode_cost_display['Total Cost'] = mode_cost_display['Total Cost'].apply(lambda x: f"${x:.2f}")
                mode_cost_display['Avg Cost'] = mode_cost_display['Avg Cost'].apply(lambda x: f"${x:.4f}")
                
                st.dataframe(mode_cost_display, use_container_width=True)
        else:
            st.info("No cost data available")
