# test_member_cards.py - Standalone Diagnostic Test
"""
Test member card selection behavior and styling independently.
Run with: streamlit run test_member_cards.py
"""

import streamlit as st

# Mock data for testing
MOCK_MEMBERS = {
    "Australia": [
        {"member_id": "AU001", "name": "John Smith", "age": 56, "super_balance": 450000},
        {"member_id": "AU002", "name": "Sarah Jones", "age": 62, "super_balance": 680000},
        {"member_id": "AU003", "name": "Michael Brown", "age": 48, "super_balance": 320000},
    ],
    "USA": [
        {"member_id": "US001", "name": "David Johnson", "age": 54, "super_balance": 520000},
        {"member_id": "US002", "name": "Emily Davis", "age": 59, "super_balance": 710000},
    ]
}

# Country color themes
COUNTRY_COLORS = {
    "Australia": {"primary": "#FFCD00", "secondary": "#00843D", "flag": "🇦🇺"},
    "USA": {"primary": "#B22234", "secondary": "#3C3B6E", "flag": "🇺🇸"},
    "United Kingdom": {"primary": "#012169", "secondary": "#C8102E", "flag": "🇬🇧"},
    "India": {"primary": "#FF9933", "secondary": "#138808", "flag": "🇮🇳"}
}

st.set_page_config(page_title="Member Card Test", layout="wide")

st.title("🧪 Member Card Selection Test")
st.markdown("---")

# Initialize session state
if "selected_member" not in st.session_state:
    st.session_state.selected_member = None
if "current_country" not in st.session_state:
    st.session_state.current_country = "Australia"
if "members_cache" not in st.session_state:
    st.session_state.members_cache = {}

# Country selector
country = st.radio("Select Country", ["Australia", "USA"], horizontal=True)

# Check if country changed (this triggers member list reload)
if country != st.session_state.current_country:
    st.session_state.current_country = country
    st.session_state.selected_member = None  # Reset selection
    st.info(f"🔄 Country changed to {country} - member selection reset")

# Load members for current country (with caching to prevent reload)
if country not in st.session_state.members_cache:
    st.session_state.members_cache[country] = MOCK_MEMBERS.get(country, [])
    st.success(f"✅ Loaded {len(st.session_state.members_cache[country])} members for {country}")

members = st.session_state.members_cache[country]

st.markdown("---")
st.subheader(f"📋 {COUNTRY_COLORS[country]['flag']} {country} Members")

# Debug info
with st.expander("🔍 Debug Info"):
    st.json({
        "current_country": st.session_state.current_country,
        "selected_member": st.session_state.selected_member,
        "members_count": len(members),
        "members_in_cache": list(st.session_state.members_cache.keys())
    })

# Display member cards
cols = st.columns(3)

for idx, member in enumerate(members):
    with cols[idx % 3]:
        member_id = member['member_id']
        is_selected = st.session_state.selected_member == member_id

        # Button with selection indicator
        button_label = f"{'✓ SELECTED' if is_selected else 'Select'} {member['name']}"

        if st.button(
            button_label,
            key=f"btn_{member_id}",
            use_container_width=True,
            type="primary" if is_selected else "secondary"
        ):
            st.session_state.selected_member = member_id
            st.rerun()

        # Render member card with country colors
        colors = COUNTRY_COLORS[country]

        # Card styling based on selection
        if is_selected:
            border_color = colors['secondary']
            border_width = "4px"
            bg_color = f"linear-gradient(135deg, {colors['primary']}15 0%, {colors['secondary']}15 100%)"
            shadow = "0 8px 16px rgba(0,0,0,0.2)"
        else:
            border_color = "#ddd"
            border_width = "1px"
            bg_color = "#ffffff"
            shadow = "0 2px 4px rgba(0,0,0,0.1)"

        # Render card with inline CSS
        st.markdown(f"""
        <div style="
            border: {border_width} solid {border_color};
            border-radius: 12px;
            padding: 20px;
            background: {bg_color};
            box-shadow: {shadow};
            margin-bottom: 10px;
            transition: all 0.3s ease;
        ">
            <h3 style="margin: 0 0 10px 0; color: {colors['secondary']};">
                {colors['flag']} {member['name']}
            </h3>
            <p style="margin: 5px 0; color: #666;">
                <strong>ID:</strong> {member_id}<br>
                <strong>Age:</strong> {member['age']}<br>
                <strong>Balance:</strong> ${member['super_balance']:,}
            </p>
            <p style="
                margin: 10px 0 0 0;
                padding: 8px;
                background: {colors['primary']}30;
                border-left: 3px solid {colors['primary']};
                color: {colors['secondary']};
                font-weight: bold;
                border-radius: 4px;
            ">
                {'🎯 SELECTED' if is_selected else '◯ Not selected'}
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Show selected member info
if st.session_state.selected_member:
    selected = next((m for m in members if m['member_id'] == st.session_state.selected_member), None)
    if selected:
        st.success(f"✅ Currently selected: **{selected['name']}** (ID: {selected['member_id']})")
    else:
        st.error("⚠️ Selected member not found in current list!")
else:
    st.info("ℹ️ No member selected yet")

# Test instructions
st.markdown("---")
st.subheader("🧪 Test Instructions")
st.markdown("""
**What to test:**
1. Click on a member card - it should highlight with country colors
2. Click on another member - previous one should unhighlight, new one highlights
3. Switch country using radio buttons - selection should reset
4. Cards should NOT reload/shuffle when clicking

**Expected behavior:**
- Selected card shows:
  - Thick colored border (green for Australia, blue for USA)
  - Light gradient background with country colors
  - Stronger shadow
  - "🎯 SELECTED" badge

- Non-selected cards show:
  - Thin gray border
  - White background
  - Light shadow
  - "◯ Not selected" text

**If you see issues:**
- Cards reload/shuffle → Problem with session state
- No colors → CSS not applying
- Multiple cards selected → State management issue
""")
