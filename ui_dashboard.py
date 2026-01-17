"""
Professional Dashboard View for Governance Page

Clean, at-a-glance overview with:
- 4 key metric cards
- Recent activity feed
- Quick trend charts
- System status
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List
from utils.lakehouse import execute_sql_query
from config import UNITY_CATALOG, UNITY_SCHEMA


def render_metric_card(label: str, value: str, delta: str, delta_positive: bool = True):
    """Render a professional metric card."""
    delta_color = "#059669" if delta_positive else "#ef4444"
    delta_arrow = "↑" if delta_positive else "↓"
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta" style="color: {delta_color};">
            {delta_arrow} {delta}
        </div>
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_dashboard_data() -> pd.DataFrame:
    """Get last 24 hours of data for dashboard (cached for 60s)."""
    try:
        # ✅ FIXED: timestamp is STRING (ISO 8601), so convert to TIMESTAMP for comparison
        # Databricks SQL can parse ISO 8601 strings when casting to TIMESTAMP
        query = f"""
        SELECT
            timestamp,
            user_id,
            country,
            query_string,
            cost,
            total_time_seconds as runtime_sec,
            judge_verdict,
            tool_used,
            error_info
        FROM {UNITY_CATALOG}.{UNITY_SCHEMA}.governance
        WHERE CAST(timestamp AS TIMESTAMP) >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
        ORDER BY CAST(timestamp AS TIMESTAMP) DESC
        LIMIT 1000
        """
        return execute_sql_query(query)
    except Exception as e:
        st.error(f"Error loading dashboard data: SQL execution error: {e}")
        import traceback
        st.code(traceback.format_exc())
        
        # ✅ FALLBACK: Try simpler query without timestamp filtering
        try:
            st.info("⚠️ Attempting fallback query (last 100 records)...")
            fallback_query = f"""
            SELECT
                timestamp,
                user_id,
                country,
                query_string,
                cost,
                total_time_seconds as runtime_sec,
                judge_verdict,
                tool_used,
                error_info
            FROM {UNITY_CATALOG}.{UNITY_SCHEMA}.governance
            ORDER BY timestamp DESC
            LIMIT 100
            """
            return execute_sql_query(fallback_query)
        except Exception as e2:
            st.error(f"Fallback query also failed: {e2}")
            return pd.DataFrame()


def calculate_key_metrics(df: pd.DataFrame) -> Dict:
    """Calculate the 4 key metrics for dashboard."""
    if df.empty:
        return {
            "total_queries": 0,
            "pass_rate": 0.0,
            "avg_cost": 0.0,
            "health_score": 0
        }
    
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
    df['runtime_sec'] = pd.to_numeric(df['runtime_sec'], errors='coerce')
    
    total_queries = len(df)
    pass_rate = (df['judge_verdict'] == 'Pass').sum() / total_queries if total_queries > 0 else 0
    avg_cost = df['cost'].mean()
    
    # Health score: weighted combination of pass_rate and low error rate
    error_rate = (df['judge_verdict'] == 'Fail').sum() / total_queries if total_queries > 0 else 0
    health_score = int((pass_rate * 0.7 + (1 - error_rate) * 0.3) * 100)
    
    return {
        "total_queries": total_queries,
        "pass_rate": pass_rate,
        "avg_cost": avg_cost,
        "health_score": health_score
    }


def render_health_stars(score: int) -> str:
    """Convert health score to star rating."""
    if score >= 90:
        return "⭐⭐⭐⭐⭐"
    elif score >= 80:
        return "⭐⭐⭐⭐"
    elif score >= 70:
        return "⭐⭐⭐"
    elif score >= 60:
        return "⭐⭐"
    else:
        return "⭐"


def render_activity_feed(df: pd.DataFrame, limit: int = 10):
    """Render recent activity feed."""
    if df.empty:
        st.info("No recent activity in the last 24 hours.")
        return
    
    st.markdown("### Recent Activity")
    
    # Take last N records
    recent = df.head(limit)
    
    for _, row in recent.iterrows():
        timestamp = pd.to_datetime(row['timestamp']).strftime("%H:%M:%S")
        country = row.get('country', 'Unknown')
        user_id = row.get('user_id', 'Unknown')[:8]
        runtime = row.get('runtime_sec', 0)
        cost = row.get('cost', 0)
        verdict = row.get('judge_verdict', 'Unknown')
        
        # Status emoji
        if verdict == 'Pass':
            status_emoji = "✅"
            status_class = "status-success"
        elif verdict == 'Fail':
            status_emoji = "❌"
            status_class = "status-error"
        else:
            status_emoji = "⏳"
            status_class = "status-pending"
        
        st.markdown(f"""
        <div class="activity-item {status_class}">
            <span class="activity-emoji">{status_emoji}</span>
            <span class="activity-country">{country}</span>
            <span class="activity-user">User: {user_id}</span>
            <span class="activity-stats">{runtime:.1f}s • ${cost:.4f}</span>
            <span class="activity-time">{timestamp}</span>
        </div>
        """, unsafe_allow_html=True)


def render_quick_charts(df: pd.DataFrame):
    """Render two quick trend charts."""
    if df.empty:
        st.info("No data available for charts.")
        return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Query Volume (Hourly)")
        hourly_volume = df.set_index('timestamp').resample('H').size().reset_index(name='count')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly_volume['timestamp'],
            y=hourly_volume['count'],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#0ea5e9', width=3),
            marker=dict(size=6),
            name='Queries'
        ))
        fig.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="",
            yaxis_title="Queries",
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Cost Trend (Hourly)")
        hourly_cost = df.set_index('timestamp').resample('H').agg(
            avg_cost=('cost', 'mean')
        ).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly_cost['timestamp'],
            y=hourly_cost['avg_cost'],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#059669', width=3),
            marker=dict(size=6),
            name='Avg Cost'
        ))
        fig.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="",
            yaxis_title="Cost (USD)",
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)


def render_system_status(df: pd.DataFrame):
    """Render system status banner."""
    if df.empty:
        st.markdown("""
        <div class="system-status status-unknown">
            ⚪ No recent data available
        </div>
        """, unsafe_allow_html=True)
        return
    
    df['runtime_sec'] = pd.to_numeric(df['runtime_sec'], errors='coerce')
    
    total = len(df)
    errors = (df['judge_verdict'] == 'Fail').sum()
    error_rate = errors / total if total > 0 else 0
    avg_latency = df['runtime_sec'].mean()
    
    # Determine status
    if error_rate < 0.05 and avg_latency < 5:
        status_class = "status-healthy"
        status_icon = "🟢"
        status_text = "All systems operational"
    elif error_rate < 0.10:
        status_class = "status-warning"
        status_icon = "🟡"
        status_text = "Minor issues detected"
    else:
        status_class = "status-critical"
        status_icon = "🔴"
        status_text = "System degraded"
    
    # Get tool usage breakdown (instead of classification_method)
    tool_usage = df['tool_used'].value_counts() if 'tool_used' in df.columns else pd.Series()
    primary_tool = tool_usage.index[0] if len(tool_usage) > 0 else "none"
    primary_tool_pct = (tool_usage.iloc[0] / total * 100) if len(tool_usage) > 0 else 0
    
    st.markdown(f"""
    <div class="system-status {status_class}">
        <div class="status-main">
            <span class="status-icon">{status_icon}</span>
            <span class="status-text">{status_text}</span>
        </div>
        <div class="status-details">
            <span>⚡ Avg latency: {avg_latency:.1f}s</span>
            <span>•</span>
            <span>🔧 Primary tool: {primary_tool} ({primary_tool_pct:.0f}%)</span>
            <span>•</span>
            <span>❌ Error rate: {error_rate:.1%}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_trust_footer():
    """Render professional trust signals."""
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="trust-badge">
            <div class="trust-icon">🔒</div>
            <div class="trust-title">Secure</div>
            <div class="trust-desc">PII Anonymization</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="trust-badge">
            <div class="trust-icon">✅</div>
            <div class="trust-title">Validated</div>
            <div class="trust-desc">LLM-as-a-Judge</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="trust-badge">
            <div class="trust-icon">📊</div>
            <div class="trust-title">Monitored</div>
            <div class="trust-desc">MLflow Tracking</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="trust-badge">
            <div class="trust-icon">🌍</div>
            <div class="trust-title">Global</div>
            <div class="trust-desc">Multi-Country</div>
        </div>
        """, unsafe_allow_html=True)


def render_dashboard_tab():
    """
    Main dashboard rendering function.
    
    Shows:
    - 4 key metric cards
    - Recent activity feed
    - Quick trend charts
    - System status banner
    - Trust signals
    """
    
    # Get data (cached for 60 seconds)
    df = get_dashboard_data()
    
    if df.empty:
        st.info("📊 No data available for the last 24 hours. Run some queries to populate the dashboard!")
        return
    
    # Calculate metrics
    metrics = calculate_key_metrics(df)
    
    # Key Metrics Row
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
    
    # Recent Activity Feed
    render_activity_feed(df, limit=10)
    
    st.markdown("---")
    
    # Quick Charts
    st.markdown("### Trends")
    render_quick_charts(df)
    
    # Trust Footer
    render_trust_footer()

