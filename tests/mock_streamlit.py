"""
Mock Streamlit Module for Testing
==================================

Provides minimal streamlit mocks so tests can run without streamlit installed.
"""

import sys
from unittest.mock import MagicMock

# Create mock streamlit module
streamlit_mock = MagicMock()
streamlit_mock.__version__ = "1.0.0-mock"

# Mock common streamlit functions used in the codebase
streamlit_mock.empty = MagicMock()
streamlit_mock.container = MagicMock()
streamlit_mock.markdown = MagicMock()
streamlit_mock.info = MagicMock()
streamlit_mock.error = MagicMock()
streamlit_mock.warning = MagicMock()
streamlit_mock.success = MagicMock()
streamlit_mock.expander = MagicMock()
streamlit_mock.caption = MagicMock()
streamlit_mock.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
streamlit_mock.metric = MagicMock()
streamlit_mock.dataframe = MagicMock()
streamlit_mock.write = MagicMock()
streamlit_mock.code = MagicMock()
streamlit_mock.session_state = {}

# Mock datetime module if needed
class MockDatetime:
    @staticmethod
    def now():
        from datetime import datetime
        return datetime.now()

streamlit_mock.datetime = MockDatetime

# Install mock into sys.modules
sys.modules['streamlit'] = streamlit_mock

print("✅ Streamlit mock installed for testing")
