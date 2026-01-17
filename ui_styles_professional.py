"""
Professional Pension Company Styling

Clean, trustworthy design with:
- Trust blues (stability)
- Success greens (growth)
- Professional typography
- Smooth animations
"""

import streamlit as st


def apply_professional_pension_theme():
    """Apply comprehensive professional styling."""
    st.markdown("""
    <style>
    /* ============================================================
       PROFESSIONAL COLOR PALETTE
       ============================================================ */
    :root {
        /* Primary - Trust & Stability */
        --trust-blue: #1e3a8a;
        --sky-blue: #0ea5e9;
        --blue-light: #dbeafe;
        
        /* Secondary - Success & Growth */
        --growth-green: #059669;
        --success-light: #d1fae5;
        
        /* Neutral - Professional */
        --slate-900: #0f172a;
        --slate-700: #334155;
        --slate-600: #475569;
        --slate-400: #94a3b8;
        --slate-200: #e2e8f0;
        --slate-100: #f1f5f9;
        --slate-50: #f8fafc;
        
        /* Status Colors */
        --status-success: #10b981;
        --status-warning: #f59e0b;
        --status-error: #ef4444;
        --status-info: #3b82f6;
        
        /* Shadows */
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
        --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
    }
    
    /* ============================================================
       TYPOGRAPHY
       ============================================================ */
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--slate-900);
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', -apple-system, sans-serif;
        font-weight: 600;
        color: var(--trust-blue);
    }
    
    /* Numbers and data */
    .metric-value, .stMetric {
        font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
        font-weight: 500;
    }
    
    /* ============================================================
       PROFESSIONAL TABS (5 CLEAN TABS - FULL WIDTH)
       ============================================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--slate-50);
        padding: 12px;
        border-radius: 12px;
        box-shadow: var(--shadow-sm);
        width: 100%;
        display: flex;
        justify-content: space-between;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 64px;
        background-color: white;
        border-radius: 10px;
        border: 2px solid var(--slate-200);
        color: var(--slate-700);
        font-weight: 600;
        font-size: 16px;
        padding: 0 32px;
        transition: all 0.3s ease;
        flex: 1;
        min-width: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--blue-light);
        border-color: var(--sky-blue);
        color: var(--trust-blue);
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--trust-blue) 0%, var(--sky-blue) 100%);
        color: white !important;
        border-color: var(--trust-blue);
        box-shadow: var(--shadow-lg);
    }
    
    /* ============================================================
       METRIC CARDS (DASHBOARD)
       ============================================================ */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: var(--shadow-md);
        border-left: 4px solid var(--trust-blue);
        transition: all 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-4px);
        border-left-color: var(--sky-blue);
    }
    
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: var(--slate-600);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--trust-blue);
        margin: 8px 0;
    }
    
    .metric-delta {
        font-size: 13px;
        font-weight: 600;
    }
    
    /* ============================================================
       ACTIVITY FEED
       ============================================================ */
    .activity-item {
        background: white;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 12px;
        border-left: 3px solid var(--slate-200);
        transition: all 0.2s ease;
        font-size: 14px;
    }
    
    .activity-item:hover {
        box-shadow: var(--shadow-md);
        transform: translateX(4px);
    }
    
    .activity-item.status-success {
        border-left-color: var(--status-success);
        background: linear-gradient(90deg, var(--success-light) 0%, white 20%);
    }
    
    .activity-item.status-error {
        border-left-color: var(--status-error);
        background: linear-gradient(90deg, #fee2e2 0%, white 20%);
    }
    
    .activity-item.status-pending {
        border-left-color: var(--slate-400);
    }
    
    .activity-emoji {
        font-size: 18px;
    }
    
    .activity-country {
        font-weight: 600;
        color: var(--trust-blue);
    }
    
    .activity-user {
        color: var(--slate-600);
        font-size: 13px;
    }
    
    .activity-stats {
        color: var(--slate-500);
        font-size: 13px;
        margin-left: auto;
    }
    
    .activity-time {
        color: var(--slate-400);
        font-size: 12px;
        font-family: 'SF Mono', monospace;
    }
    
    /* ============================================================
       SYSTEM STATUS BANNER
       ============================================================ */
    .system-status {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: var(--shadow-md);
        border-left: 6px solid var(--slate-400);
    }
    
    .system-status.status-healthy {
        border-left-color: var(--status-success);
        background: linear-gradient(90deg, var(--success-light) 0%, white 30%);
    }
    
    .system-status.status-warning {
        border-left-color: var(--status-warning);
        background: linear-gradient(90deg, #fef3c7 0%, white 30%);
    }
    
    .system-status.status-critical {
        border-left-color: var(--status-error);
        background: linear-gradient(90deg, #fee2e2 0%, white 30%);
    }
    
    .status-main {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    
    .status-icon {
        font-size: 24px;
    }
    
    .status-text {
        font-size: 18px;
        font-weight: 600;
        color: var(--slate-900);
    }
    
    .status-details {
        display: flex;
        gap: 16px;
        font-size: 14px;
        color: var(--slate-600);
    }
    
    /* ============================================================
       TRUST BADGES (FOOTER)
       ============================================================ */
    .trust-badge {
        text-align: center;
        padding: 16px;
        background: white;
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }
    
    .trust-badge:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    .trust-icon {
        font-size: 32px;
        margin-bottom: 8px;
    }
    
    .trust-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--trust-blue);
        margin-bottom: 4px;
    }
    
    .trust-desc {
        font-size: 12px;
        color: var(--slate-600);
    }
    
    /* ============================================================
       EXPANDERS (FOR ANALYTICS TAB)
       ============================================================ */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 8px;
        border: 1px solid var(--slate-200);
        font-weight: 600;
        color: var(--trust-blue);
        padding: 16px;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--blue-light);
        border-color: var(--sky-blue);
    }
    
    /* ============================================================
       BUTTONS
       ============================================================ */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--trust-blue) 0%, var(--sky-blue) 100%);
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }
    
    /* ============================================================
       SIDEBAR
       ============================================================ */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--slate-50) 0%, white 100%);
    }
    
    /* ============================================================
       CHARTS
       ============================================================ */
    .js-plotly-plot {
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
    }
    
    /* ============================================================
       TABLES
       ============================================================ */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }
    
    .dataframe thead tr th {
        background: var(--trust-blue) !important;
        color: white !important;
        font-weight: 600;
    }
    
    .dataframe tbody tr:hover {
        background: var(--blue-light);
    }
    
    /* ============================================================
       PERFORMANCE: REDUCE ANIMATIONS ON MOBILE
       ============================================================ */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation: none !important;
            transition: none !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

