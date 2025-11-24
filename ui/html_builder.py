"""
ui.html_builder
===============

HTML component builders for consistent UI rendering with Streamlit.

This module provides reusable functions for generating common HTML patterns
used across the UI. All functions maintain exact backward compatibility with
existing code and preserve all styling.

Features:
- Generic card builders
- Status/info cards
- List items (activity feed)
- Badge components
- Maintains exact HTML output for visual compatibility

Extracted from:
- ui_components.py (member cards, question cards, validation results)
- ui_dashboard.py (metric cards, activity items, trust badges)

Usage:
    >>> from ui.html_builder import build_card, build_info_card
    >>> import streamlit as st
    >>>
    >>> # Simple card
    >>> html = build_card(
    ...     content="<b>Hello</b> World",
    ...     background="#FFF",
    ...     border="1px solid #CCC"
    ... )
    >>> st.markdown(html, unsafe_allow_html=True)

Author: Refactoring Team
Date: 2024-11-24
"""

from typing import Optional, Dict, Any, List


# ============================================================================ #
# GENERIC CARD BUILDERS
# ============================================================================ #

def build_card(
    content: str,
    background: str = "#FFF",
    border: str = "1px solid #CCC",
    border_radius: str = "10px",
    padding: str = "14px",
    margin_bottom: str = "10px",
    box_shadow: Optional[str] = None,
    extra_styles: Optional[str] = None
) -> str:
    """
    Build a generic HTML card div.

    This is the most flexible card builder, allowing full customization
    of all styling properties. Used as a base for more specific card types.

    Args:
        content: HTML content to place inside the card
        background: CSS background value (color, gradient, etc.)
        border: CSS border value (e.g., "1px solid #CCC")
        border_radius: CSS border-radius value
        padding: CSS padding value
        margin_bottom: CSS margin-bottom value
        box_shadow: Optional box-shadow value
        extra_styles: Optional additional inline CSS styles

    Returns:
        Complete HTML string with `<div>` wrapper

    Examples:
        >>> # Simple white card
        >>> card = build_card("<b>Title</b><br>Content here")
        >>> st.markdown(card, unsafe_allow_html=True)
        >>>
        >>> # Card with gradient background
        >>> card = build_card(
        ...     content="Featured content",
        ...     background="linear-gradient(135deg, #FFD700 0%, #00843D 100%)",
        ...     border="2px solid #00843D",
        ...     box_shadow="0 6px 14px rgba(0,0,0,0.15)"
        ... )

    Notes:
        - Returns HTML string only (does NOT call st.markdown)
        - Caller must use `st.markdown(..., unsafe_allow_html=True)`
        - All style values are injected as-is (no validation)
    """
    styles = [
        f"background:{background}",
        f"border:{border}",
        f"border-radius:{border_radius}",
        f"padding:{padding}",
        f"margin-bottom:{margin_bottom}"
    ]

    if box_shadow:
        styles.append(f"box-shadow:{box_shadow}")

    if extra_styles:
        styles.append(extra_styles)

    style_str = ";".join(styles)

    return f"""
    <div style="{style_str}">
        {content}
    </div>
    """


def build_info_card(
    content: str,
    card_type: str = "info",
    border_width: str = "4px",
    padding: str = "1rem",
    border_radius: str = "8px",
    margin: str = "1rem 0"
) -> str:
    """
    Build an info/status card with left border accent.

    Used for validation results, system messages, status banners.
    Supports predefined types (success, error, warning, info) with
    corresponding colors.

    Args:
        content: HTML content for the card
        card_type: Type of card - "success", "error", "warning", "info"
        border_width: Width of left border accent
        padding: CSS padding value
        border_radius: CSS border-radius value
        margin: CSS margin value

    Returns:
        Complete HTML string with styled `<div>`

    Examples:
        >>> # Success card (green)
        >>> card = build_info_card("✅ <strong>All good!</strong>", "success")
        >>>
        >>> # Error card (red)
        >>> card = build_info_card("❌ <strong>Failed</strong>", "error")
        >>>
        >>> # Custom styling
        >>> card = build_info_card(
        ...     content="Custom message",
        ...     card_type="warning",
        ...     padding="2rem"
        ... )

    Notes:
        - Default type is "info" (blue)
        - Automatically applies appropriate background and border colors
        - Maintains exact color values from ui_components.py
    """
    # Color mappings from original code
    color_schemes = {
        "success": {
            "bg": "#E8F5E9",
            "border": "#16A34A"
        },
        "error": {
            "bg": "#FFEBEE",
            "border": "#DC2626"
        },
        "warning": {
            "bg": "#FFF8E1",
            "border": "#F59E0B"
        },
        "info": {
            "bg": "#E0F2FE",
            "border": "#0EA5E9"
        }
    }

    scheme = color_schemes.get(card_type, color_schemes["info"])

    return f"""
    <div style="background:{scheme['bg']};border-left:{border_width} solid {scheme['border']};
                padding:{padding};border-radius:{border_radius};margin:{margin};">
        {content}
    </div>
    """


# ============================================================================ #
# SPECIALIZED CARD BUILDERS
# ============================================================================ #

def build_member_card(
    flag: str,
    name: str,
    age: Any,
    balance_formatted: str,
    background: str,
    border: str,
    box_shadow: str,
    border_radius: str = "10px",
    padding: str = "14px",
    margin_bottom: str = "10px"
) -> str:
    """
    Build a member card with flag, name, age, and balance.

    Extracted from ui_components.py render_member_card() function.
    Preserves exact HTML structure and styling.

    Args:
        flag: Unicode flag emoji (e.g., "🇦🇺")
        name: Member name
        age: Member age (any type, will be converted to string)
        balance_formatted: Pre-formatted balance string (e.g., "A$50,000")
        background: CSS background value
        border: CSS border value
        box_shadow: CSS box-shadow value
        border_radius: CSS border-radius value
        padding: CSS padding value
        margin_bottom: CSS margin-bottom value

    Returns:
        Complete HTML string for member card

    Examples:
        >>> from ui.theme_config import get_member_card_styling
        >>>
        >>> # Get styling for selected Australian member
        >>> style = get_member_card_styling("Australia", is_selected=True)
        >>> theme = style['theme']
        >>>
        >>> # Build card
        >>> card = build_member_card(
        ...     flag=theme.flag,
        ...     name="John Smith",
        ...     age=45,
        ...     balance_formatted=f"{theme.currency}150,000",
        ...     background=style['bg'],
        ...     border=style['border'],
        ...     box_shadow=style['shadow']
        ... )
        >>> st.markdown(card, unsafe_allow_html=True)

    Notes:
        - Maintains exact format: "Flag Name" on line 1, "Age: X • Balance: Y" on line 2
        - Caller must format balance with currency symbol
        - Use get_member_card_styling() from theme_config for consistent styling
    """
    content = f"""
        <b>{flag} {name}</b><br>
        Age: {age} • Balance: {balance_formatted}
    """

    return build_card(
        content=content,
        background=background,
        border=border,
        border_radius=border_radius,
        padding=padding,
        margin_bottom=margin_bottom,
        box_shadow=box_shadow
    )


def build_question_card(
    question: str,
    is_example: bool = False,
    border_radius: str = "8px",
    padding: str = "10px",
    margin_bottom: str = "8px"
) -> str:
    """
    Build a question card with emoji prefix.

    Extracted from ui_components.py render_question_card() function.
    Supports both regular questions (solid green) and example questions (dashed gray).

    Args:
        question: Question text (plain text, will be auto-escaped)
        is_example: If True, use dashed border and gray colors
        border_radius: CSS border-radius value
        padding: CSS padding value
        margin_bottom: CSS margin-bottom value

    Returns:
        Complete HTML string for question card

    Examples:
        >>> # Regular question
        >>> card = build_question_card("How much can I withdraw?")
        >>>
        >>> # Example question
        >>> card = build_question_card(
        ...     "Can I access my super early?",
        ...     is_example=True
        ... )

    Notes:
        - Automatically adds 💬 emoji prefix
        - Example questions use dashed border (#AFAFAF) and light gray background
        - Regular questions use solid border (#00843D) and light green background
        - Preserves exact colors from ui_components.py lines 198-199
    """
    if is_example:
        border = "2px dashed #AFAFAF"
        bg = "#F9F9F9"
    else:
        border = "2px solid #00843D"
        bg = "#E8F5E9"

    content = f"💬 {question}"

    return build_card(
        content=content,
        background=bg,
        border=border,
        border_radius=border_radius,
        padding=padding,
        margin_bottom=margin_bottom
    )


def build_validation_result_card(
    icon: str,
    title: str,
    details: str,
    card_type: str = "success"
) -> str:
    """
    Build a validation result card with icon, title, and details.

    Extracted from ui_components.py render_validation_results() function.
    Used to display LLM Judge validation outcomes.

    Args:
        icon: Emoji icon (e.g., "✅", "❌", "⚠️")
        title: Card title (e.g., "LLM Judge: PASSED")
        details: Additional details (HTML allowed)
        card_type: Type of card - "success", "error", "warning"

    Returns:
        Complete HTML string for validation result card

    Examples:
        >>> # Success card
        >>> card = build_validation_result_card(
        ...     icon="✅",
        ...     title="LLM Judge: PASSED",
        ...     details="Model: Claude Sonnet 4 • Confidence: 95% • Time: 1.2s",
        ...     card_type="success"
        ... )
        >>>
        >>> # Error card
        >>> card = build_validation_result_card(
        ...     icon="❌",
        ...     title="LLM Judge: FLAGGED",
        ...     details="Found 3 potential issues<br>Confidence: 92%",
        ...     card_type="error"
        ... )

    Notes:
        - Automatically formats as: "icon <strong>title</strong><br>details"
        - Uses build_info_card() for consistent styling
        - Supports HTML in details parameter
    """
    content = f"{icon} <strong>{title}</strong><br>{details}"
    return build_info_card(content, card_type=card_type)


# ============================================================================ #
# LIST ITEM BUILDERS
# ============================================================================ #

def build_activity_item(
    emoji: str,
    country: str,
    user_id: str,
    stats: str,
    timestamp: str,
    status_class: str = "status-success"
) -> str:
    """
    Build an activity feed item.

    Extracted from ui_dashboard.py render_activity_feed() function.
    Used for displaying recent queries/activities in dashboard.

    Args:
        emoji: Status emoji (e.g., "✅", "❌", "⏳")
        country: Country name (e.g., "Australia")
        user_id: User identifier (truncated, e.g., "AU001")
        stats: Stats string (e.g., "2.5s • $0.0034")
        timestamp: Formatted timestamp (e.g., "14:35:22")
        status_class: CSS class for status styling

    Returns:
        Complete HTML string for activity item

    Examples:
        >>> item = build_activity_item(
        ...     emoji="✅",
        ...     country="Australia",
        ...     user_id="AU001",
        ...     stats="2.1s • $0.0028",
        ...     timestamp="09:45:12",
        ...     status_class="status-success"
        ... )
        >>> st.markdown(item, unsafe_allow_html=True)

    Notes:
        - Requires CSS classes from ui_styles_professional.py:
          - .activity-item
          - .activity-emoji, .activity-country, .activity-user, .activity-stats, .activity-time
          - .status-success, .status-error, .status-pending
        - Layout: emoji | country | user | stats | time
    """
    return f"""
    <div class="activity-item {status_class}">
        <span class="activity-emoji">{emoji}</span>
        <span class="activity-country">{country}</span>
        <span class="activity-user">User: {user_id}</span>
        <span class="activity-stats">{stats}</span>
        <span class="activity-time">{timestamp}</span>
    </div>
    """


# ============================================================================ #
# BADGE/CHIP BUILDERS
# ============================================================================ #

def build_trust_badge(
    icon: str,
    title: str,
    description: str
) -> str:
    """
    Build a trust badge component.

    Extracted from ui_dashboard.py render_trust_footer() function.
    Used for displaying security/feature badges.

    Args:
        icon: Badge icon (emoji or symbol, e.g., "🔒", "✅")
        title: Badge title (e.g., "Secure", "Validated")
        description: Badge description (e.g., "PII Anonymization")

    Returns:
        Complete HTML string for trust badge

    Examples:
        >>> badge = build_trust_badge(
        ...     icon="🔒",
        ...     title="Secure",
        ...     description="PII Anonymization"
        ... )
        >>> st.markdown(badge, unsafe_allow_html=True)
        >>>
        >>> # Multiple badges in columns
        >>> col1, col2, col3 = st.columns(3)
        >>> with col1:
        ...     st.markdown(build_trust_badge("🔒", "Secure", "Encrypted"), unsafe_allow_html=True)
        >>> with col2:
        ...     st.markdown(build_trust_badge("✅", "Validated", "LLM Judge"), unsafe_allow_html=True)

    Notes:
        - Requires CSS class .trust-badge from ui_styles_professional.py
        - Also requires: .trust-icon, .trust-title, .trust-desc
        - Structure: icon at top, title below, description at bottom
    """
    return f"""
    <div class="trust-badge">
        <div class="trust-icon">{icon}</div>
        <div class="trust-title">{title}</div>
        <div class="trust-desc">{description}</div>
    </div>
    """


def build_metric_card(
    label: str,
    value: str,
    delta: str,
    delta_positive: bool = True
) -> str:
    """
    Build a metric card with label, value, and delta indicator.

    Extracted from ui_dashboard.py render_metric_card() function.
    Used for displaying key metrics in dashboard.

    Args:
        label: Metric label (e.g., "Total Queries", "Pass Rate")
        value: Metric value (pre-formatted, e.g., "1,234", "95.2%")
        delta: Delta text (e.g., "Last 24h", "+5.2%")
        delta_positive: If True, show green ↑, else red ↓

    Returns:
        Complete HTML string for metric card

    Examples:
        >>> card = build_metric_card(
        ...     label="Total Queries",
        ...     value="1,234",
        ...     delta="Last 24h",
        ...     delta_positive=True
        ... )
        >>>
        >>> card = build_metric_card(
        ...     label="Avg Cost",
        ...     value="$0.0034",
        ...     delta="-12%",
        ...     delta_positive=True  # Lower cost is good
        ... )

    Notes:
        - Requires CSS class .metric-card from ui_styles_professional.py
        - Also requires: .metric-label, .metric-value, .metric-delta
        - Delta arrow and color based on delta_positive flag
        - Green (#059669) for positive, red (#ef4444) for negative
    """
    delta_color = "#059669" if delta_positive else "#ef4444"
    delta_arrow = "↑" if delta_positive else "↓"

    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta" style="color: {delta_color};">
            {delta_arrow} {delta}
        </div>
    </div>
    """


# ============================================================================ #
# SYSTEM STATUS BUILDERS
# ============================================================================ #

def build_system_status_banner(
    status_icon: str,
    status_text: str,
    details: List[str],
    status_class: str = "status-healthy"
) -> str:
    """
    Build a system status banner with icon, text, and details.

    Extracted from ui_dashboard.py render_system_status() function.
    Used for displaying overall system health status.

    Args:
        status_icon: Status emoji (e.g., "🟢", "🟡", "🔴")
        status_text: Status message (e.g., "All systems operational")
        details: List of detail strings (will be joined with " • ")
        status_class: CSS class for status styling

    Returns:
        Complete HTML string for system status banner

    Examples:
        >>> banner = build_system_status_banner(
        ...     status_icon="🟢",
        ...     status_text="All systems operational",
        ...     details=[
        ...         "⚡ Avg latency: 2.1s",
        ...         "🔧 Primary tool: pension_check (85%)",
        ...         "❌ Error rate: 2.3%"
        ...     ],
        ...     status_class="status-healthy"
        ... )

    Notes:
        - Requires CSS classes from ui_styles_professional.py:
          - .system-status, .status-main, .status-details
          - .status-icon, .status-text
          - .status-healthy, .status-warning, .status-critical
        - Details are joined with " • " separator
    """
    details_html = '<span>•</span>'.join(f'<span>{d}</span>' for d in details)

    return f"""
    <div class="system-status {status_class}">
        <div class="status-main">
            <span class="status-icon">{status_icon}</span>
            <span class="status-text">{status_text}</span>
        </div>
        <div class="status-details">
            {details_html}
        </div>
    </div>
    """


# ============================================================================ #
# MODULE TEST (run when executed directly)
# ============================================================================ #

if __name__ == "__main__":
    print("=" * 70)
    print("HTML Builder - Test Suite")
    print("=" * 70)

    # Test 1: Generic card
    print("\nTest 1: Generic Card")
    card = build_card(
        content="<b>Test Card</b><br>This is a test",
        background="#FFF",
        border="1px solid #CCC"
    )
    print(f"  Length: {len(card)} chars")
    print(f"  Contains <div>: {('<div' in card)}")

    # Test 2: Info cards
    print("\nTest 2: Info Cards")
    for card_type in ["success", "error", "warning", "info"]:
        card = build_info_card(f"Test {card_type} card", card_type=card_type)
        print(f"  {card_type}: {len(card)} chars")

    # Test 3: Member card
    print("\nTest 3: Member Card")
    card = build_member_card(
        flag="🇦🇺",
        name="Test Member",
        age=45,
        balance_formatted="A$150,000",
        background="#FFF",
        border="1px solid #CCC",
        box_shadow="0 2px 4px rgba(0,0,0,0.1)"
    )
    print(f"  Length: {len(card)} chars")
    print(f"  Contains flag: {'🇦🇺' in card}")

    # Test 4: Question card
    print("\nTest 4: Question Card")
    regular = build_question_card("How much can I withdraw?")
    example = build_question_card("Can I access early?", is_example=True)
    print(f"  Regular: {len(regular)} chars")
    print(f"  Example: {len(example)} chars")

    # Test 5: Activity item
    print("\nTest 5: Activity Item")
    item = build_activity_item(
        emoji="✅",
        country="Australia",
        user_id="AU001",
        stats="2.1s • $0.0028",
        timestamp="09:45:12"
    )
    print(f"  Length: {len(item)} chars")
    print(f"  Contains class: {'activity-item' in item}")

    # Test 6: Trust badge
    print("\nTest 6: Trust Badge")
    badge = build_trust_badge("🔒", "Secure", "PII Anonymization")
    print(f"  Length: {len(badge)} chars")
    print(f"  Contains icon: {'🔒' in badge}")

    # Test 7: Metric card
    print("\nTest 7: Metric Card")
    metric = build_metric_card("Total Queries", "1,234", "Last 24h", True)
    print(f"  Length: {len(metric)} chars")
    print(f"  Contains arrow: {'↑' in metric}")

    # Test 8: System status
    print("\nTest 8: System Status Banner")
    status = build_system_status_banner(
        "🟢",
        "All systems operational",
        ["⚡ Avg latency: 2.1s", "❌ Error rate: 2.3%"],
        "status-healthy"
    )
    print(f"  Length: {len(status)} chars")
    print(f"  Contains icon: {'🟢' in status}")

    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)
