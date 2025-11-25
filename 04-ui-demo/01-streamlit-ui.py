# Databricks notebook source
# MAGIC %md
# MAGIC # Streamlit UI Demo
# MAGIC
# MAGIC This notebook demonstrates the Streamlit web interface for the
# MAGIC multi-country retirement advisory agent.
# MAGIC
# MAGIC **UI Features:**
# MAGIC - Multi-country selector (AU, US, UK, IN)
# MAGIC - Member authentication
# MAGIC - Natural language query interface
# MAGIC - Response display with citations
# MAGIC - Performance metrics
# MAGIC - Session history

# COMMAND ----------

# MAGIC %md
# MAGIC ## UI Architecture

# COMMAND ----------

# The Streamlit UI is built using modular components from ui/

import sys
sys.path.append('..')

from ui.tab_base import TabBase
from ui.theme_config import get_theme_config
from ui.html_builder import HTMLBuilder

print("✓ UI modules imported")
print("\\nUI Architecture:")
print("  Main app: app.py")
print("  Theme config: ui/theme_config.py")
print("  HTML components: ui/html_builder.py")
print("  Base tab class: ui/tab_base.py")
print("  Country-specific tabs: ui_components.py")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Theme Configuration

# COMMAND ----------

# Each country has its own theme
from config import COUNTRIES

for country_code in COUNTRIES:
    theme = get_theme_config(country_code)
    print(f"\\n{country_code} Theme:")
    print(f"  Primary color: {theme['primary_color']}")
    print(f"  Secondary color: {theme['secondary_color']}")
    print(f"  Flag emoji: {theme['flag_emoji']}")
    print(f"  Full name: {theme['country_name']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## HTML Components

# COMMAND ----------

# Reusable UI components
builder = HTMLBuilder()

# Example: Create a styled message box
message_html = builder.create_message_box(
    title="Agent Response",
    content="Based on your member profile, you can access your superannuation without penalties at age 60.",
    box_type="success"
)

print("Sample HTML Component (Message Box):")
print(message_html[:200] + "...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tab Base Class

# COMMAND ----------

# All country tabs inherit from TabBase
# This eliminates code duplication (425 lines saved)

print("TabBase Class Benefits:")
print("  - Consistent layout across all countries")
print("  - DRY principle: Define once, use everywhere")
print("  - Easy to add new countries")
print("  - Centralized query processing")
print("\\nShared functionality:")
print("  - render(): Main tab rendering")
print("  - display_member_info(): Member profile display")
print("  - process_query(): Query execution")
print("  - display_response(): Response formatting")
print("  - show_citations(): Citation references")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Running the Streamlit App

# COMMAND ----------

# MAGIC %md
# MAGIC To run the Streamlit UI locally:
# MAGIC
# MAGIC ```bash
# MAGIC # Activate virtual environment
# MAGIC source venv/bin/activate
# MAGIC
# MAGIC # Run Streamlit app
# MAGIC streamlit run app.py --server.port 8501
# MAGIC ```
# MAGIC
# MAGIC The app will be available at: http://localhost:8501

# COMMAND ----------

# MAGIC %md
# MAGIC ## UI Components Overview

# COMMAND ----------

import pandas as pd

ui_components = [
    {
        "Component": "Country Selector",
        "File": "app.py",
        "Description": "Radio button selector for AU, US, UK, IN"
    },
    {
        "Component": "Member Dropdown",
        "File": "ui/tab_base.py",
        "Description": "Select member from available profiles"
    },
    {
        "Component": "Member Profile Card",
        "File": "ui/tab_base.py",
        "Description": "Display member details (age, balance, etc.)"
    },
    {
        "Component": "Query Input",
        "File": "ui/tab_base.py",
        "Description": "Text area for natural language queries"
    },
    {
        "Component": "Example Queries",
        "File": "ui/tab_base.py",
        "Description": "Pre-defined query buttons for quick testing"
    },
    {
        "Component": "Response Display",
        "File": "ui/html_builder.py",
        "Description": "Styled response with citations"
    },
    {
        "Component": "Performance Metrics",
        "File": "ui/tab_base.py",
        "Description": "Latency, cost, tokens, validation status"
    },
    {
        "Component": "Session History",
        "File": "ui/tab_base.py",
        "Description": "Previous queries in current session"
    },
    {
        "Component": "Error Display",
        "File": "ui/html_builder.py",
        "Description": "Friendly error messages"
    },
    {
        "Component": "Citation Links",
        "File": "ui/tab_base.py",
        "Description": "Expandable citation references"
    }
]

df = pd.DataFrame(ui_components)
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Key Features Demo

# COMMAND ----------

# Feature 1: Multi-Country Support
print("Feature 1: Multi-Country Support")
print("  - 4 countries: AU, US, UK, IN")
print("  - Country-specific themes and colors")
print("  - Locale-aware formatting (currency, dates)")
print("  - Regulatory compliance per jurisdiction")

print("\\nFeature 2: Member Authentication")
print("  - Dropdown selector for available members")
print("  - Display member profile (age, balance, status)")
print("  - Row-level security enforcement")
print("  - PII protection")

print("\\nFeature 3: Natural Language Query")
print("  - Free-text input for questions")
print("  - Example query buttons for quick testing")
print("  - Query history tracking")
print("  - Session persistence")

print("\\nFeature 4: Rich Response Display")
print("  - Formatted agent responses")
print("  - Citation references (expandable)")
print("  - Performance metrics (latency, cost)")
print("  - Validation verdict (LLM-as-a-Judge)")

print("\\nFeature 5: Performance Monitoring")
print("  - Real-time latency tracking")
print("  - Token usage display")
print("  - Cost per query")
print("  - Tool execution details")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example Queries by Country

# COMMAND ----------

example_queries = {
    "AU": [
        "What is my current super balance?",
        "When can I access my super without penalties?",
        "How much tax will I pay on a $50,000 withdrawal?",
        "Am I eligible for Centrelink Age Pension?",
        "What are my investment options?"
    ],
    "US": [
        "What's my 401(k) balance?",
        "When can I take penalty-free withdrawals?",
        "Should I do a Roth conversion?",
        "What are my RMD requirements?",
        "How is Social Security calculated?"
    ],
    "UK": [
        "What's my pension pot value?",
        "Can I access my 25% tax-free lump sum?",
        "What are my State Pension entitlements?",
        "Should I consider pension drawdown?",
        "What's my Normal Minimum Pension Age?"
    ],
    "IN": [
        "What's my EPF balance?",
        "When can I withdraw my NPS corpus?",
        "How much tax will I pay on withdrawal?",
        "What are my senior citizen benefits?",
        "Should I opt for annuity?"
    ]
}

print("Example Queries Available in UI:\\n")
for country, queries in example_queries.items():
    print(f"{country}:")
    for i, query in enumerate(queries, 1):
        print(f"  {i}. {query}")
    print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Response Format

# COMMAND ----------

# Example response structure returned by agent_query()

example_response = {
    "response": "Based on your member profile, you can access your superannuation without penalties at age 60...",
    "citations": [
        {
            "title": "Preservation Age",
            "url": "https://www.ato.gov.au/individuals/super/withdrawing-and-using-your-super/preservation-age"
        },
        {
            "title": "Tax on Super Withdrawals",
            "url": "https://www.ato.gov.au/individuals/super/withdrawing-and-using-your-super/tax-on-withdrawals"
        }
    ],
    "validation": {
        "verdict": "Pass",
        "confidence": 0.92
    },
    "performance": {
        "total_time": 2.34,
        "llm_time": 1.89,
        "tool_time": 0.45,
        "tokens": 1250,
        "cost": 0.0234
    },
    "tools_used": ["check_preservation_age", "calculate_tax"],
    "error": None
}

print("Response Structure:")
print(f"  Response: {example_response['response'][:80]}...")
print(f"  Citations: {len(example_response['citations'])} references")
print(f"  Validation: {example_response['validation']['verdict']} (confidence: {example_response['validation']['confidence']:.2f})")
print(f"  Performance: {example_response['performance']['total_time']:.2f}s, ${example_response['performance']['cost']:.4f}")
print(f"  Tools: {', '.join(example_response['tools_used'])}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Session State Management

# COMMAND ----------

# Streamlit uses session_state to persist data across reruns

print("Session State Variables:")
print("  - selected_country: Currently selected country code")
print("  - selected_member: Currently selected member ID")
print("  - query_history: List of previous queries in session")
print("  - response_cache: Cached responses to avoid redundant API calls")
print("  - performance_metrics: Accumulated metrics for dashboard")
print("\\nBenefits:")
print("  - Fast UI responsiveness")
print("  - Reduced API costs")
print("  - Better user experience")
print("  - Session continuity")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Error Handling

# COMMAND ----------

# The UI gracefully handles various error scenarios

error_scenarios = [
    {
        "Error Type": "LLM Timeout",
        "Handling": "Retry with exponential backoff, show progress spinner",
        "User Message": "Processing your query, this may take a moment..."
    },
    {
        "Error Type": "Tool Execution Failure",
        "Handling": "Fall back to cached data or return partial response",
        "User Message": "Some data unavailable, showing best available information"
    },
    {
        "Error Type": "Validation Failure",
        "Handling": "Retry synthesis, log for review, show confidence score",
        "User Message": "Response quality below threshold, please review carefully"
    },
    {
        "Error Type": "Rate Limit",
        "Handling": "Queue request, implement retry logic",
        "User Message": "High demand detected, your query is queued..."
    },
    {
        "Error Type": "Invalid Member ID",
        "Handling": "Show error, refresh member list",
        "User Message": "Member not found, please select from available members"
    }
]

error_df = pd.DataFrame(error_scenarios)
display(error_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deployment Options

# COMMAND ----------

print("Deployment Options:\\n")

print("1. Local Development:")
print("   streamlit run app.py --server.port 8501")
print("   Best for: Testing, debugging, development")

print("\\n2. Databricks Apps:")
print("   Deploy directly from Databricks workspace")
print("   Best for: Internal company use, secure environment")

print("\\n3. Streamlit Cloud:")
print("   Push to GitHub, deploy via Streamlit Cloud")
print("   Best for: Public demos, external sharing")

print("\\n4. Docker Container:")
print("   Containerize app with dependencies")
print("   Best for: Cloud deployment (AWS, Azure, GCP)")

print("\\n5. Kubernetes:")
print("   Scale horizontally for high traffic")
print("   Best for: Enterprise production deployment")

# COMMAND ----------

# MAGIC %md
# MAGIC ## UI Code Structure

# COMMAND ----------

print("File Organization:\\n")

print("app.py (Main entry point)")
print("  ├── Country selector (radio buttons)")
print("  ├── Import country-specific tabs")
print("  └── Render selected tab\\n")

print("ui/theme_config.py")
print("  ├── Color palettes per country")
print("  ├── Flag emojis")
print("  └── Locale settings\\n")

print("ui/html_builder.py")
print("  ├── create_message_box()")
print("  ├── create_metric_card()")
print("  ├── create_citation_list()")
print("  └── create_error_message()\\n")

print("ui/tab_base.py")
print("  ├── TabBase class (parent)")
print("  ├── render() - Main tab layout")
print("  ├── display_member_info() - Profile card")
print("  ├── process_query() - Query execution")
print("  └── display_response() - Result display\\n")

print("ui_components.py")
print("  ├── AustraliaTab(TabBase)")
print("  ├── USTab(TabBase)")
print("  ├── UKTab(TabBase)")
print("  └── IndiaTab(TabBase)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Performance Optimization

# COMMAND ----------

print("UI Performance Optimizations:\\n")

print("1. Caching:")
print("   @st.cache_data for member data")
print("   @st.cache_resource for agent initialization")
print("   Response caching for duplicate queries")

print("\\n2. Lazy Loading:")
print("   Load components only when tab is active")
print("   Defer heavy computations until needed")

print("\\n3. Async Processing:")
print("   Non-blocking LLM calls")
print("   Progress indicators for long operations")

print("\\n4. Efficient Rendering:")
print("   Minimize st.rerun() calls")
print("   Use session state instead of global variables")

print("\\n5. Resource Management:")
print("   Connection pooling for database")
print("   Proper cleanup in callbacks")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Accessibility & UX

# COMMAND ----------

print("Accessibility Features:\\n")

print("✓ Color contrast: WCAG AA compliant")
print("✓ Keyboard navigation: Tab through all controls")
print("✓ Screen reader support: Proper ARIA labels")
print("✓ Responsive design: Mobile-friendly layout")
print("✓ Clear error messages: Actionable feedback")
print("✓ Loading indicators: User feedback on progress")

print("\\nUX Best Practices:")
print("✓ Example queries for easy onboarding")
print("✓ Inline help tooltips")
print("✓ Confirmation dialogs for destructive actions")
print("✓ Consistent navigation patterns")
print("✓ Progressive disclosure (expandable sections)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Testing the UI

# COMMAND ----------

print("UI Testing Strategy:\\n")

print("1. Manual Testing:")
print("   - Test all example queries per country")
print("   - Verify member switching works correctly")
print("   - Check responsive design on mobile")
print("   - Test error scenarios")

print("\\n2. Automated Testing:")
print("   - Selenium for UI automation")
print("   - Pytest for component testing")
print("   - Mock LLM responses for consistent tests")

print("\\n3. User Acceptance Testing:")
print("   - Gather feedback from actual users")
print("   - Track common queries and pain points")
print("   - Iterate based on usage patterns")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitoring UI Usage

# COMMAND ----------

print("UI Usage Metrics to Track:\\n")

print("User Engagement:")
print("  - Active users per day")
print("  - Queries per session")
print("  - Session duration")
print("  - Bounce rate (single query sessions)")

print("\\nQuery Patterns:")
print("  - Most common queries by country")
print("  - Example query usage vs custom queries")
print("  - Query length distribution")

print("\\nPerformance:")
print("  - Page load time")
print("  - Time to first response")
print("  - Error rate")
print("  - Retry rate")

print("\\nBusiness Metrics:")
print("  - Member satisfaction (feedback ratings)")
print("  - Query resolution rate")
print("  - Cost per session")
print("  - Support ticket reduction")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Streamlit UI Demo Complete
# MAGIC
# MAGIC You've learned about:
# MAGIC - UI architecture with modular components
# MAGIC - Theme configuration for multi-country support
# MAGIC - TabBase class for code reuse
# MAGIC - HTML builder for consistent styling
# MAGIC - Session state management
# MAGIC - Error handling and user feedback
# MAGIC - Deployment options
# MAGIC - Performance optimization
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - Run the app locally: `streamlit run app.py`
# MAGIC - Test all country tabs
# MAGIC - Try example queries
# MAGIC - Explore session history
# MAGIC - Monitor usage metrics in governance dashboard

# COMMAND ----------

print("✅ Streamlit UI demo complete!")
print("   4 country tabs: AU, US, UK, IN")
print("   Modular components: Theme, HTML, TabBase")
print("   Features: Auth, Query, Citations, Metrics")
print("   Ready to run: streamlit run app.py")
print("\\n🎉 All demo notebooks complete!")
