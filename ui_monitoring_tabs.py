#!/usr/bin/env python3
"""
Enhanced Monitoring & Observability Tabs for Streamlit UI
All monitoring data displayed without leaving the app!
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import mlflow
from databricks.sdk import WorkspaceClient


# ============================================================================
# 1. REAL-TIME METRICS DASHBOARD
# ============================================================================

def render_realtime_metrics_tab():
    """
    Real-time metrics dashboard showing live agent performance.
    Updates from Unity Catalog governance table.
    """
    # ✅ REMOVED: Duplicate heading - already shown in tab header
    st.caption("Live metrics from the last 24 hours")
    
    try:
        from utils.audit import get_audit_log
        
        # Get data from last 24 hours
        data = get_audit_log(limit=1000)
        
        if not data:
            st.info("ℹ️ No data available yet. Run some queries to populate metrics.")
            return
        
        df = pd.DataFrame(data)
        
        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Filter last 24 hours
            cutoff = datetime.now() - timedelta(hours=24)
            df = df[df['timestamp'] >= cutoff]
        
        if df.empty:
            st.info("ℹ️ No queries in the last 24 hours")
            return
        
        # Convert numeric columns
        df['cost'] = pd.to_numeric(df.get('cost', 0), errors='coerce')
        df['runtime_sec'] = pd.to_numeric(df.get('runtime_sec', 0), errors='coerce')
        
        # === KEY METRICS ROW ===
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_queries = len(df)
        unique_users = df['user_id'].nunique() if 'user_id' in df.columns else 0
        total_cost = df['cost'].sum()
        avg_latency = df['runtime_sec'].mean()
        pass_rate = (df['judge_verdict'] == 'Pass').sum() / len(df) * 100 if 'judge_verdict' in df.columns else 0
        
        with col1:
            st.metric("Total Queries", f"{total_queries:,}")
        
        with col2:
            st.metric("Unique Users", f"{unique_users}")
        
        with col3:
            st.metric("Total Cost", f"${total_cost:.4f}")
        
        with col4:
            st.metric("Avg Latency", f"{avg_latency:.2f}s")
        
        with col5:
            st.metric("Pass Rate", f"{pass_rate:.1f}%")
        
        st.markdown("---")
        
        # === QUERY VOLUME OVER TIME ===
        st.markdown("#### 📈 Query Volume Over Time")
        
        # Group by hour
        df_hourly = df.copy()
        df_hourly['hour'] = df_hourly['timestamp'].dt.floor('H')
        hourly_counts = df_hourly.groupby('hour').size().reset_index(name='queries')
        
        fig_volume = px.line(
            hourly_counts, 
            x='hour', 
            y='queries',
            title="Queries per Hour (Last 24h)",
            labels={'hour': 'Time', 'queries': 'Query Count'}
        )
        fig_volume.update_traces(line_color='#00843D')
        st.plotly_chart(fig_volume, use_container_width=True)
        
        # === COST AND LATENCY TRENDS ===
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 Cost Trend")
            hourly_cost = df_hourly.groupby('hour')['cost'].sum().reset_index()
            fig_cost = px.area(
                hourly_cost,
                x='hour',
                y='cost',
                title="Cost per Hour (USD)",
                labels={'hour': 'Time', 'cost': 'Cost (USD)'}
            )
            fig_cost.update_traces(fillcolor='rgba(0,132,61,0.2)', line_color='#00843D')
            st.plotly_chart(fig_cost, use_container_width=True)
        
        with col2:
            st.markdown("#### ⚡ Latency Trend")
            hourly_latency = df_hourly.groupby('hour')['runtime_sec'].mean().reset_index()
            fig_latency = px.line(
                hourly_latency,
                x='hour',
                y='runtime_sec',
                title="Avg Latency per Hour (seconds)",
                labels={'hour': 'Time', 'runtime_sec': 'Latency (s)'}
            )
            fig_latency.update_traces(line_color='#FFD700')
            st.plotly_chart(fig_latency, use_container_width=True)
        
        # === COUNTRY BREAKDOWN ===
        st.markdown("#### 🌍 Performance by Country")
        
        if 'country' in df.columns:
            country_stats = df.groupby('country').agg({
                'cost': ['sum', 'mean'],
                'runtime_sec': 'mean',
                'user_id': 'count'
            }).round(4)
            
            country_stats.columns = ['Total Cost ($)', 'Avg Cost ($)', 'Avg Latency (s)', 'Query Count']
            country_stats = country_stats.sort_values('Query Count', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(country_stats, use_container_width=True)
            
            with col2:
                fig_country = px.pie(
                    df,
                    names='country',
                    title='Queries by Country',
                    hole=0.4
                )
                st.plotly_chart(fig_country, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading real-time metrics: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


# ============================================================================
# 2. CLASSIFICATION ANALYTICS
# ============================================================================

def render_classification_analytics_tab():
    """
    Detailed analytics on the 3-stage cascade classifier performance.
    Shows which stage is handling queries and cost savings.
    """
    # ✅ REMOVED: Duplicate heading - already shown in tab header
    st.caption("3-Stage Cascade Classifier: Regex → Embedding → LLM")
    
    try:
        from utils.audit import get_audit_log
        
        data = get_audit_log(limit=1000)
        
        if not data:
            st.info("ℹ️ No classification data available yet.")
            return
        
        df = pd.DataFrame(data)
        
        # Filter for classification method if available
        if 'classification_method' not in df.columns:
            st.warning("⚠️ Classification method not being logged. Update monitoring.py integration.")
            return
        
        # Clean and convert
        df['cost'] = pd.to_numeric(df.get('cost', 0), errors='coerce')
        df['classification_method'] = df['classification_method'].fillna('unknown')
        
        # === STAGE DISTRIBUTION ===
        st.markdown("#### 📊 Classification Stage Distribution")
        
        stage_counts = df['classification_method'].value_counts()
        stage_percentages = (stage_counts / len(df) * 100).round(1)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            regex_pct = stage_percentages.get('regex', 0)
            st.metric(
                "🔤 Stage 1: Regex",
                f"{regex_pct:.1f}%",
                help="Fast keyword matching (<1ms, $0)"
            )
        
        with col2:
            embedding_pct = stage_percentages.get('embedding', 0)
            st.metric(
                "🧠 Stage 2: Embedding",
                f"{embedding_pct:.1f}%",
                help="Semantic similarity (~100ms, ~$0.0001)"
            )
        
        with col3:
            llm_pct = stage_percentages.get('llm', 0)
            st.metric(
                "🤖 Stage 3: LLM",
                f"{llm_pct:.1f}%",
                help="Full LLM classification (~300ms, ~$0.001)"
            )
        
        with col4:
            other_pct = 100 - (regex_pct + embedding_pct + llm_pct)
            st.metric(
                "❓ Other/Unknown",
                f"{other_pct:.1f}%"
            )
        
        # Visualization
        fig_stages = px.funnel(
            x=[regex_pct, embedding_pct, llm_pct],
            y=['Stage 1: Regex', 'Stage 2: Embedding', 'Stage 3: LLM'],
            title="Classification Cascade Funnel"
        )
        st.plotly_chart(fig_stages, use_container_width=True)
        
        st.markdown("---")
        
        # === COST SAVINGS ANALYSIS ===
        st.markdown("#### 💰 Cost Savings vs Pure LLM")
        
        # Estimate costs
        COST_REGEX = 0.0
        COST_EMBEDDING = 0.0001
        COST_LLM = 0.001
        
        actual_cost = (
            stage_counts.get('regex', 0) * COST_REGEX +
            stage_counts.get('embedding', 0) * COST_EMBEDDING +
            stage_counts.get('llm', 0) * COST_LLM
        )
        
        pure_llm_cost = len(df) * COST_LLM
        savings = pure_llm_cost - actual_cost
        savings_pct = (savings / pure_llm_cost * 100) if pure_llm_cost > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Actual Classification Cost", f"${actual_cost:.4f}")
        
        with col2:
            st.metric("Pure LLM Cost", f"${pure_llm_cost:.4f}")
        
        with col3:
            st.metric("💰 Cost Savings", f"${savings:.4f}", delta=f"-{savings_pct:.1f}%")
        
        # === CLASSIFICATION RESULTS ===
        st.markdown("#### 🏷️ Classification Results Distribution")
        
        if 'classification_result' in df.columns:
            results = df['classification_result'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(
                    pd.DataFrame({
                        'Classification': results.index,
                        'Count': results.values,
                        'Percentage': (results.values / len(df) * 100).round(1)
                    }),
                    use_container_width=True
                )
            
            with col2:
                fig_results = px.bar(
                    x=results.values,
                    y=results.index,
                    orientation='h',
                    title="Classification Results",
                    labels={'x': 'Count', 'y': 'Classification'}
                )
                st.plotly_chart(fig_results, use_container_width=True)
        
        # === LATENCY BY STAGE ===
        st.markdown("#### ⚡ Latency by Classification Stage")
        
        if 'runtime_sec' in df.columns:
            df['runtime_sec'] = pd.to_numeric(df['runtime_sec'], errors='coerce')
            latency_by_stage = df.groupby('classification_method')['runtime_sec'].agg(['mean', 'median', 'std']).round(3)
            latency_by_stage.columns = ['Mean (s)', 'Median (s)', 'Std Dev (s)']
            st.dataframe(latency_by_stage, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading classification analytics: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


# ============================================================================
# 3. QUALITY MONITORING
# ============================================================================

def render_quality_monitoring_tab():
    """
    LLM Judge validation quality metrics and trends.
    """
    # ✅ REMOVED: Duplicate heading - already shown in tab header
    st.caption("LLM-as-a-Judge validation results and trends")
    
    try:
        from utils.audit import get_audit_log
        
        data = get_audit_log(limit=1000)
        
        if not data:
            st.info("ℹ️ No validation data available yet.")
            return
        
        df = pd.DataFrame(data)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # === VALIDATION METRICS ===
        st.markdown("#### 📈 Validation Pass Rate")
        
        if 'judge_verdict' in df.columns:
            pass_count = (df['judge_verdict'] == 'Pass').sum()
            total_count = len(df)
            pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Pass Rate", f"{pass_rate:.1f}%")
            
            with col2:
                st.metric("Total Passed", f"{pass_count:,}")
            
            with col3:
                st.metric("Total Failed", f"{total_count - pass_count:,}")
            
            # Pass rate over time
            if 'timestamp' in df.columns:
                df_hourly = df.copy()
                df_hourly['hour'] = df_hourly['timestamp'].dt.floor('H')
                hourly_pass_rate = df_hourly.groupby('hour').apply(
                    lambda x: (x['judge_verdict'] == 'Pass').sum() / len(x) * 100
                ).reset_index(name='pass_rate')
                
                fig_pass_rate = px.line(
                    hourly_pass_rate,
                    x='hour',
                    y='pass_rate',
                    title="Pass Rate Over Time (%)",
                    labels={'hour': 'Time', 'pass_rate': 'Pass Rate (%)'}
                )
                fig_pass_rate.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="Target: 95%")
                fig_pass_rate.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Warning: 80%")
                st.plotly_chart(fig_pass_rate, use_container_width=True)
        
        st.markdown("---")
        
        # === CONFIDENCE ANALYSIS ===
        st.markdown("#### 🎯 Validation Confidence Distribution")
        
        if 'judge_confidence' in df.columns:
            df['judge_confidence'] = pd.to_numeric(df['judge_confidence'], errors='coerce')
            # Filter out NaN values
            df_conf = df[df['judge_confidence'].notna()]
            
            if len(df_conf) == 0:
                st.info("ℹ️ No confidence data available. Confidence scores are logged in judge_response JSON.")
                st.caption("New queries will include confidence scores. Existing queries may not have this data.")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    avg_confidence = df_conf['judge_confidence'].mean()
                    st.metric("Average Confidence", f"{avg_confidence:.1%}", help=f"Based on {len(df_conf)} queries with confidence data")
                    
                    # Confidence histogram
                    fig_conf = px.histogram(
                        df_conf,
                        x='judge_confidence',
                        nbins=20,
                        title="Confidence Score Distribution",
                        labels={'judge_confidence': 'Confidence Score'},
                        color_discrete_sequence=['#00843D']
                    )
                    st.plotly_chart(fig_conf, use_container_width=True)
                
                with col2:
                    # Confidence by verdict
                    if 'judge_verdict' in df_conf.columns:
                        conf_by_verdict = df_conf.groupby('judge_verdict')['judge_confidence'].mean()
                        
                        fig_conf_verdict = px.bar(
                            x=conf_by_verdict.index,
                            y=conf_by_verdict.values,
                            title="Avg Confidence by Verdict",
                            labels={'x': 'Verdict', 'y': 'Avg Confidence'},
                            color_discrete_sequence=['#00843D']
                        )
                        st.plotly_chart(fig_conf_verdict, use_container_width=True)
        else:
            st.info("ℹ️ No confidence data available. Confidence scores are logged in judge_response JSON.")
            st.caption("New queries will include confidence scores. Existing queries may not have this data.")
        
        st.markdown("---")
        
        # === VIOLATION ANALYSIS ===
        st.markdown("#### ⚠️ Common Violations")
        
        if 'violations' in df.columns:
            # Count violations
            violation_counts = {}
            for violations_str in df['violations'].dropna():
                if violations_str and violations_str != '[]':
                    # Parse violations (simplified)
                    violation_counts['Has Violations'] = violation_counts.get('Has Violations', 0) + 1
            
            if violation_counts:
                st.dataframe(
                    pd.DataFrame(list(violation_counts.items()), columns=['Violation Type', 'Count']),
                    use_container_width=True
                )
            else:
                st.success("✅ No violations detected in recent queries!")
        
        # === QUALITY BY COUNTRY ===
        st.markdown("#### 🌍 Quality by Country")
        
        if 'country' in df.columns and 'judge_verdict' in df.columns:
            country_quality = df.groupby('country').agg({
                'judge_verdict': lambda x: (x == 'Pass').sum() / len(x) * 100,
                'user_id': 'count'
            }).round(1)
            country_quality.columns = ['Pass Rate (%)', 'Query Count']
            country_quality = country_quality.sort_values('Pass Rate (%)', ascending=False)
            
            st.dataframe(country_quality, use_container_width=True)
            
            fig_country_quality = px.bar(
                country_quality.reset_index(),
                x='country',
                y='Pass Rate (%)',
                title="Pass Rate by Country",
                color='Pass Rate (%)',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_country_quality, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading quality monitoring: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


# ============================================================================
# 4. ENHANCED COST ANALYSIS
# ============================================================================

def render_enhanced_cost_analysis_tab():
    """
    Comprehensive cost analysis with breakdowns, trends, and projections.
    """
    # ✅ REMOVED: Duplicate heading - already shown in tab header
    st.caption("Detailed cost breakdowns and projections")
    
    try:
        from utils.audit import get_audit_log
        
        data = get_audit_log(limit=1000)
        
        if not data:
            st.info("ℹ️ No cost data available yet.")
            return
        
        df = pd.DataFrame(data)
        df['cost'] = pd.to_numeric(df.get('cost', 0), errors='coerce')
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # === KEY COST METRICS (Unique - no duplicates) ===
        st.markdown("#### 💵 Cost Metrics")
        
        total_cost = df['cost'].sum()
        total_queries = len(df)
        median_cost = df['cost'].median()
        max_cost = df['cost'].max()
        min_cost = df['cost'].min()
        std_cost = df['cost'].std()
        
        # Get last run cost for comparison
        last_cost = float(df.iloc[0]['cost']) if len(df) > 0 else 0
        avg_cost = df['cost'].mean()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Cost", f"${total_cost:.4f}", help=f"Across {total_queries:,} queries")
        
        with col2:
            st.metric("Median Cost", f"${median_cost:.5f}", help="50th percentile - typical query cost")
        
        with col3:
            delta_pct = ((last_cost - avg_cost) / avg_cost * 100) if avg_cost > 0 else None
            st.metric(
                "Last Run Cost",
                f"${last_cost:.5f}",
                delta=f"{delta_pct:.1f}%" if delta_pct else None,
                delta_color="inverse" if delta_pct and delta_pct > 0 else "normal",
                help="Most recent query cost vs average"
            )
        
        with col4:
            st.metric("Max Cost", f"${max_cost:.5f}", help="Most expensive query")
        
        with col5:
            st.metric("Cost Std Dev", f"${std_cost:.5f}", help="Cost variability")
        
        # === COST DISTRIBUTION ===
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Cost Distribution")
            fig_dist = px.histogram(
                df,
                x='cost',
                nbins=30,
                title="Cost per Query Distribution",
                labels={'cost': 'Cost (USD)'}
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            st.markdown("#### 📈 Cost Percentiles")
            percentiles = df['cost'].quantile([0.5, 0.75, 0.90, 0.95, 0.99]).round(5)
            percentile_df = pd.DataFrame({
                'Percentile': ['P50 (Median)', 'P75', 'P90', 'P95', 'P99'],
                'Cost ($)': percentiles.values
            })
            st.dataframe(percentile_df, use_container_width=True)
            
            # Box plot
            fig_box = px.box(
                df,
                y='cost',
                title="Cost Distribution (Box Plot)",
                labels={'cost': 'Cost (USD)'}
            )
            st.plotly_chart(fig_box, use_container_width=True)
        
        st.markdown("---")
        
        # === COST BY CATEGORY ===
        st.markdown("#### 🏷️ Cost Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'country' in df.columns:
                st.markdown("**By Country**")
                country_costs = df.groupby('country')['cost'].agg(['sum', 'mean', 'count'])
                country_costs.columns = ['Total ($)', 'Avg ($)', 'Queries']
                country_costs = country_costs.sort_values('Total ($)', ascending=False)
                st.dataframe(country_costs.round(5), use_container_width=True)
        
        with col2:
            if 'user_id' in df.columns:
                st.markdown("**Top 10 Users by Cost**")
                user_costs = df.groupby('user_id')['cost'].sum().sort_values(ascending=False).head(10)
                st.dataframe(
                    pd.DataFrame({'User': user_costs.index, 'Total Cost ($)': user_costs.values.round(5)}),
                    use_container_width=True
                )
        
        # === COST TREND ===
        st.markdown("#### 📈 Cost Trend Over Time")
        
        if 'timestamp' in df.columns:
            df_hourly = df.copy()
            df_hourly['hour'] = df_hourly['timestamp'].dt.floor('H')
            hourly_cost = df_hourly.groupby('hour')['cost'].agg(['sum', 'mean']).reset_index()
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=hourly_cost['hour'],
                y=hourly_cost['sum'],
                mode='lines+markers',
                name='Total Cost',
                yaxis='y1'
            ))
            fig_trend.add_trace(go.Scatter(
                x=hourly_cost['hour'],
                y=hourly_cost['mean'],
                mode='lines',
                name='Avg Cost',
                yaxis='y2'
            ))
            
            fig_trend.update_layout(
                title="Hourly Cost Trends",
                yaxis=dict(title="Total Cost ($)", side='left'),
                yaxis2=dict(title="Avg Cost ($)", side='right', overlaying='y'),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # === COST PROJECTION ===
        st.markdown("#### 🔮 Monthly Cost Projection")
        
        if len(df) > 0:
            # Calculate daily average
            if 'timestamp' in df.columns:
                days_of_data = (df['timestamp'].max() - df['timestamp'].min()).days + 1
            else:
                days_of_data = 1
            
            daily_avg = total_cost / days_of_data if days_of_data > 0 else total_cost
            monthly_projection = daily_avg * 30
            annual_projection = daily_avg * 365
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Daily Average", f"${daily_avg:.4f}")
            
            with col2:
                st.metric("Monthly Projection", f"${monthly_projection:.2f}")
            
            with col3:
                st.metric("Annual Projection", f"${annual_projection:.2f}")
        
    except Exception as e:
        st.error(f"❌ Error loading enhanced cost analysis: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


# ============================================================================
# 5. SYSTEM HEALTH & ALERTS
# ============================================================================

def render_system_health_tab():
    """
    System health monitoring with anomaly detection and alerts.
    """
    # ✅ REMOVED: Duplicate heading - already shown in tab header
    st.caption("Monitor system health and detect anomalies")
    
    try:
        from utils.audit import get_audit_log
        
        data = get_audit_log(limit=1000)
        
        if not data:
            st.info("ℹ️ No system data available yet.")
            return
        
        df = pd.DataFrame(data)
        
        # Convert numeric columns
        df['cost'] = pd.to_numeric(df.get('cost', 0), errors='coerce')
        df['runtime_sec'] = pd.to_numeric(df.get('runtime_sec', 0), errors='coerce')
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # === HEALTH STATUS ===
        st.markdown("#### 🚦 System Status")
        
        # Calculate health metrics
        error_count = df[df.get('error_info', '') != ''].shape[0] if 'error_info' in df.columns else 0
        error_rate = (error_count / len(df) * 100) if len(df) > 0 else 0
        
        pass_rate = (df['judge_verdict'] == 'Pass').sum() / len(df) * 100 if 'judge_verdict' in df.columns else 0
        
        avg_latency = df['runtime_sec'].mean()
        
        avg_cost = df['cost'].mean()
        
        # Determine overall health
        health_score = 100
        issues = []
        
        if error_rate > 5:
            health_score -= 30
            issues.append(f"High error rate: {error_rate:.1f}%")
        
        if pass_rate < 90:
            health_score -= 25
            issues.append(f"Low pass rate: {pass_rate:.1f}%")
        
        if avg_latency > 10:
            health_score -= 20
            issues.append(f"High latency: {avg_latency:.2f}s")
        
        if avg_cost > 0.01:
            health_score -= 15
            issues.append(f"High cost: ${avg_cost:.4f}/query")
        
        # Display health status
        if health_score >= 90:
            st.success(f"✅ System Health: EXCELLENT ({health_score}/100)")
        elif health_score >= 70:
            st.warning(f"⚠️ System Health: FAIR ({health_score}/100)")
        else:
            st.error(f"❌ System Health: POOR ({health_score}/100)")
        
        if issues:
            st.markdown("**Issues Detected:**")
            for issue in issues:
                st.markdown(f"- {issue}")
        
        st.markdown("---")
        
        # === KEY INDICATORS ===
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            error_color = "normal" if error_rate < 5 else "inverse"
            st.metric("Error Rate", f"{error_rate:.1f}%", delta=f"{error_count} errors", delta_color=error_color)
        
        with col2:
            pass_color = "normal" if pass_rate >= 90 else "inverse"
            st.metric("Pass Rate", f"{pass_rate:.1f}%", delta_color=pass_color)
        
        with col3:
            latency_color = "normal" if avg_latency < 10 else "inverse"
            st.metric("Avg Latency", f"{avg_latency:.2f}s", delta_color=latency_color)
        
        with col4:
            cost_color = "normal" if avg_cost < 0.01 else "inverse"
            st.metric("Avg Cost", f"${avg_cost:.4f}", delta_color=cost_color)
        
        st.markdown("---")
        
        # === ANOMALY DETECTION ===
        st.markdown("#### 🔍 Anomaly Detection")
        
        # Detect cost anomalies (>3 std devs)
        cost_mean = df['cost'].mean()
        cost_std = df['cost'].std()
        cost_threshold = cost_mean + (3 * cost_std)
        
        cost_anomalies = df[df['cost'] > cost_threshold]
        
        # Detect latency anomalies
        latency_mean = df['runtime_sec'].mean()
        latency_std = df['runtime_sec'].std()
        latency_threshold = latency_mean + (3 * latency_std)
        
        latency_anomalies = df[df['runtime_sec'] > latency_threshold]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Cost Anomalies** (>3σ)")
            if len(cost_anomalies) > 0:
                st.warning(f"⚠️ {len(cost_anomalies)} queries with unusually high cost")
                st.dataframe(
                    cost_anomalies[['timestamp', 'user_id', 'country', 'cost']].head(10),
                    use_container_width=True
                )
            else:
                st.success("✅ No cost anomalies detected")
        
        with col2:
            st.markdown("**Latency Anomalies** (>3σ)")
            if len(latency_anomalies) > 0:
                st.warning(f"⚠️ {len(latency_anomalies)} queries with unusually high latency")
                st.dataframe(
                    latency_anomalies[['timestamp', 'user_id', 'country', 'runtime_sec']].head(10),
                    use_container_width=True
                )
            else:
                st.success("✅ No latency anomalies detected")
        
        st.markdown("---")
        
        # === ERROR ANALYSIS ===
        st.markdown("#### ❌ Error Analysis")
        
        if 'error_info' in df.columns:
            errors_df = df[df['error_info'] != '']
            
            if len(errors_df) > 0:
                st.error(f"⚠️ {len(errors_df)} errors detected")
                
                # Error timeline
                if 'timestamp' in errors_df.columns:
                    errors_df_hourly = errors_df.copy()
                    errors_df_hourly['hour'] = errors_df_hourly['timestamp'].dt.floor('H')
                    error_timeline = errors_df_hourly.groupby('hour').size().reset_index(name='errors')
                    
                    fig_errors = px.bar(
                        error_timeline,
                        x='hour',
                        y='errors',
                        title="Errors Over Time",
                        labels={'hour': 'Time', 'errors': 'Error Count'}
                    )
                    fig_errors.update_traces(marker_color='red')
                    st.plotly_chart(fig_errors, use_container_width=True)
                
                # Recent errors
                with st.expander("📋 Recent Errors"):
                    st.dataframe(
                        errors_df[['timestamp', 'user_id', 'country', 'error_info']].tail(20),
                        use_container_width=True
                    )
            else:
                st.success("✅ No errors in recent queries!")
        
    except Exception as e:
        st.error(f"❌ Error loading system health: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())

