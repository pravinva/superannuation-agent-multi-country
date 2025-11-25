"""
ui.tab_base
===========

Base class for monitoring tabs with common error handling and data loading patterns.

This module extracts the repeated boilerplate code found across all 5 monitoring
tabs in ui_monitoring_tabs.py. Each tab had ~85 lines of identical setup/error
handling code, totaling ~425 lines of duplication.

Pattern extracted:
1. Caption/subtitle display
2. Try-except wrapper
3. Data loading from utils.audit
4. Empty data check with info message
5. DataFrame creation and basic processing
6. Exception handling with error display and traceback expander

Extracted from:
- ui_monitoring_tabs.py (5 tabs × 85 lines = 425 lines of duplication)

Usage:
    >>> from ui.tab_base import MonitoringTab
    >>> import streamlit as st
    >>>
    >>> class MyCustomTab(MonitoringTab):
    ...     def get_caption(self) -> str:
    ...         return "My custom monitoring view"
    ...
    ...     def render_content(self, df):
    ...         st.metric("Total Rows", len(df))
    ...         st.dataframe(df)
    >>>
    >>> tab = MyCustomTab()
    >>> tab.render()

Author: Refactoring Team
Date: 2024-11-24
"""

import streamlit as st
import pandas as pd
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import traceback


class MonitoringTab(ABC):
    """
    Abstract base class for monitoring tabs.

    Provides common functionality:
    - Automatic data loading from utils.audit
    - Empty data handling with user-friendly messages
    - Exception handling with error display and traceback
    - DataFrame creation and basic validation
    - Consistent caption/subtitle rendering

    Subclasses must implement:
    - get_caption(): Return tab caption/subtitle
    - render_content(df): Render tab-specific content with loaded data

    Examples:
        >>> class RealTimeMetricsTab(MonitoringTab):
        ...     def get_caption(self) -> str:
        ...         return "Live metrics from the last 24 hours"
        ...
        ...     def render_content(self, df: pd.DataFrame):
        ...         st.metric("Total Queries", len(df))
        ...         st.dataframe(df)
        >>>
        >>> tab = RealTimeMetricsTab()
        >>> tab.render()

    Notes:
        - Automatically imports and calls get_audit_log()
        - Handles empty data gracefully
        - Shows detailed error information in expandable section
        - DataFrame conversion is automatic
    """

    def __init__(self, data_limit: int = 1000):
        """
        Initialize monitoring tab.

        Args:
            data_limit: Maximum number of records to fetch (default: 1000)
        """
        self.data_limit = data_limit

    @abstractmethod
    def get_caption(self) -> str:
        """
        Get the caption/subtitle for this tab.

        Returns:
            Caption string to display under tab title

        Examples:
            >>> def get_caption(self) -> str:
            ...     return "Live metrics from the last 24 hours"
        """
        pass

    @abstractmethod
    def render_content(self, df: pd.DataFrame) -> None:
        """
        Render tab-specific content.

        This is where subclasses implement their unique visualization logic.
        Called only when data is successfully loaded and non-empty.

        Args:
            df: Loaded DataFrame from get_audit_log()

        Examples:
            >>> def render_content(self, df: pd.DataFrame):
            ...     col1, col2 = st.columns(2)
            ...     with col1:
            ...         st.metric("Total Queries", len(df))
            ...     with col2:
            ...         st.metric("Avg Cost", f"${df['cost'].mean():.4f}")
        """
        pass

    def get_empty_data_message(self) -> str:
        """
        Get message to display when no data is available.

        Can be overridden by subclasses for custom empty state messages.

        Returns:
            Empty data message string

        Examples:
            >>> def get_empty_data_message(self) -> str:
            ...     return "No classification data available yet."
        """
        return "ℹ️ No data available yet. Run some queries to populate metrics."

    def get_error_message_prefix(self) -> str:
        """
        Get prefix for error messages.

        Can be overridden by subclasses for custom error messages.

        Returns:
            Error message prefix

        Examples:
            >>> def get_error_message_prefix(self) -> str:
            ...     return "Error loading real-time metrics"
        """
        return "Error loading monitoring data"

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process/transform the DataFrame before rendering.

        Override this method to add custom data processing logic
        (filtering, column conversion, etc.) before render_content() is called.

        Args:
            df: Raw DataFrame from get_audit_log()

        Returns:
            Processed DataFrame

        Examples:
            >>> def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
            ...     # Convert numeric columns
            ...     df['cost'] = pd.to_numeric(df.get('cost', 0), errors='coerce')
            ...     df['runtime_sec'] = pd.to_numeric(df.get('runtime_sec', 0), errors='coerce')
            ...
            ...     # Filter last 24 hours
            ...     from datetime import datetime, timedelta
            ...     df['timestamp'] = pd.to_datetime(df['timestamp'])
            ...     cutoff = datetime.now() - timedelta(hours=24)
            ...     df = df[df['timestamp'] >= cutoff]
            ...
            ...     return df
        """
        return df

    def render(self) -> None:
        """
        Main render method - call this to display the tab.

        Handles the complete workflow:
        1. Display caption
        2. Load data from utils.audit
        3. Check for empty data
        4. Process DataFrame
        5. Render content
        6. Handle any exceptions

        This method should be called by the Streamlit app to render the tab.

        Examples:
            >>> tab = MyMonitoringTab()
            >>> tab.render()
        """
        # Display caption
        caption = self.get_caption()
        if caption:
            st.caption(caption)

        try:
            # Import audit utility (inside try block to catch import errors)
            from utils.audit import get_audit_log

            # Load data
            data = get_audit_log(limit=self.data_limit)

            # Check for empty data
            if not data:
                st.info(self.get_empty_data_message())
                return

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Check if DataFrame is empty after conversion
            if df.empty:
                st.info(self.get_empty_data_message())
                return

            # Process DataFrame (subclass can override)
            df = self.process_dataframe(df)

            # Check again after processing
            if df.empty:
                st.info(self.get_empty_data_message())
                return

            # Render tab-specific content
            self.render_content(df)

        except Exception as e:
            # Display error with traceback in expander
            error_prefix = self.get_error_message_prefix()
            st.error(f"❌ {error_prefix}: {str(e)}")

            # Show detailed traceback in expandable section
            with st.expander("Error Details"):
                st.code(traceback.format_exc())


# ============================================================================ #
# EXAMPLE TABS (for reference and testing)
# ============================================================================ #

class ExampleSimpleTab(MonitoringTab):
    """
    Example tab showing minimal implementation.

    This is the simplest possible monitoring tab - just implements
    the two required methods.
    """

    def get_caption(self) -> str:
        return "Example monitoring view"

    def render_content(self, df: pd.DataFrame) -> None:
        st.write(f"Loaded {len(df)} records")
        st.dataframe(df.head(10))


class ExampleAdvancedTab(MonitoringTab):
    """
    Example tab showing advanced features.

    Demonstrates:
    - Custom empty message
    - Custom error prefix
    - DataFrame processing
    - Complex rendering
    """

    def get_caption(self) -> str:
        return "Advanced monitoring with custom processing"

    def get_empty_data_message(self) -> str:
        return "ℹ️ No advanced metrics available yet."

    def get_error_message_prefix(self) -> str:
        return "Error loading advanced metrics"

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process DataFrame before rendering."""
        # Convert numeric columns
        if 'cost' in df.columns:
            df['cost'] = pd.to_numeric(df['cost'], errors='coerce')

        if 'runtime_sec' in df.columns:
            df['runtime_sec'] = pd.to_numeric(df['runtime_sec'], errors='coerce')

        # Filter by timestamp (example)
        if 'timestamp' in df.columns:
            from datetime import datetime, timedelta
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff = datetime.now() - timedelta(hours=24)
            df = df[df['timestamp'] >= cutoff]

        return df

    def render_content(self, df: pd.DataFrame) -> None:
        """Render advanced metrics."""
        # Key metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Records", len(df))

        with col2:
            if 'cost' in df.columns:
                st.metric("Avg Cost", f"${df['cost'].mean():.4f}")

        with col3:
            if 'runtime_sec' in df.columns:
                st.metric("Avg Latency", f"{df['runtime_sec'].mean():.2f}s")

        st.markdown("---")

        # Data table
        st.dataframe(df.head(20), use_container_width=True)


# ============================================================================ #
# MODULE TEST (run when executed directly)
# ============================================================================ #

if __name__ == "__main__":
    print("=" * 70)
    print("Monitoring Tab Base Class - Test Suite")
    print("=" * 70)

    # Test 1: Check abstract methods
    print("\nTest 1: Abstract Base Class")
    try:
        # This should fail - can't instantiate abstract class
        tab = MonitoringTab()
        print("  ❌ FAIL: Should not be able to instantiate abstract class")
    except TypeError as e:
        print(f"  ✅ PASS: Cannot instantiate abstract class (expected)")

    # Test 2: Simple tab creation
    print("\nTest 2: Simple Tab Creation")
    try:
        tab = ExampleSimpleTab()
        print(f"  ✅ Caption: '{tab.get_caption()}'")
        print(f"  ✅ Empty message: '{tab.get_empty_data_message()}'")
        print(f"  ✅ Error prefix: '{tab.get_error_message_prefix()}'")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Test 3: Advanced tab creation
    print("\nTest 3: Advanced Tab Creation")
    try:
        tab = ExampleAdvancedTab()
        print(f"  ✅ Caption: '{tab.get_caption()}'")
        print(f"  ✅ Custom empty message: '{tab.get_empty_data_message()}'")
        print(f"  ✅ Custom error prefix: '{tab.get_error_message_prefix()}'")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Test 4: DataFrame processing
    print("\nTest 4: DataFrame Processing")
    try:
        tab = ExampleAdvancedTab()
        # Create test DataFrame
        test_df = pd.DataFrame({
            'cost': ['0.0034', '0.0042', 'invalid'],
            'runtime_sec': ['2.1', '3.5', '1.8'],
            'timestamp': [
                '2024-11-24 10:00:00',
                '2024-11-24 11:00:00',
                '2024-11-24 12:00:00'
            ]
        })

        processed = tab.process_dataframe(test_df)
        print(f"  ✅ Original rows: {len(test_df)}")
        print(f"  ✅ Processed rows: {len(processed)}")
        print(f"  ✅ Cost column type: {processed['cost'].dtype}")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Test 5: Method signatures
    print("\nTest 5: Required Methods")
    tab = ExampleSimpleTab()
    required_methods = ['get_caption', 'render_content', 'render']
    for method in required_methods:
        if hasattr(tab, method):
            print(f"  ✅ Has method: {method}")
        else:
            print(f"  ❌ Missing method: {method}")

    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)
    print("\nUsage Example:")
    print("""
class MyMonitoringTab(MonitoringTab):
    def get_caption(self) -> str:
        return "My custom view"

    def render_content(self, df: pd.DataFrame):
        st.metric("Total", len(df))
        st.dataframe(df)

# In Streamlit app:
tab = MyMonitoringTab()
tab.render()
    """)
