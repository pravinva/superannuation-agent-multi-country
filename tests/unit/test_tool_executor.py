"""
Unit tests for tools.tool_executor module.

Tests cover:
- Configuration loading and validation
- Parameter resolution from profiles
- Query building from templates
- Tool execution for AU/US/UK
- Error handling (ToolConfigurationError, ToolExecutionError)
- Citation loading
- Logging integration

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
import yaml
import logging
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path

from tools.tool_executor import (
    UnifiedToolExecutor,
    ToolConfigurationError,
    ToolExecutionError,
    create_executor
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_config():
    """Sample tool configuration for testing."""
    return {
        'countries': {
            'AU': {
                'tools': {
                    'tax': {
                        'name': 'ATO Tax Calculator',
                        'uc_function': 'au_calculate_tax',
                        'authority': 'Australian Taxation Office',
                        'citations': ['AU-TAX-001'],
                        'query_template': "SELECT au_tax('{member_id}', {age}, {withdrawal_amount})",
                        'params': ['member_id', 'age', 'withdrawal_amount']
                    },
                    'benefit': {
                        'name': 'Centrelink Calculator',
                        'uc_function': 'au_check_pension',
                        'authority': 'DSS',
                        'citations': ['AU-PENSION-001'],
                        'query_template': "SELECT au_pension('{member_id}', {age}, {balance})",
                        'params': ['member_id', 'age', {'balance': 'super_balance'}]
                    }
                }
            },
            'US': {
                'tools': {
                    'tax': {
                        'name': 'IRS Tax Calculator',
                        'uc_function': 'us_calculate_tax',
                        'authority': 'IRS',
                        'citations': ['US-TAX-001'],
                        'query_template': "SELECT us_tax('{member_id}', {age})",
                        'params': ['member_id', 'age']
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_profile():
    """Sample member profile for testing."""
    return {
        'member_id': 'M001',
        'age': 65,
        'super_balance': 500000,
        'marital_status': 'Single',
        'other_assets': 100000,
        'preservation_age': 60
    }


@pytest.fixture
def mock_sql_result():
    """Mock SQL execution result."""
    result = Mock()
    result.result.data_array = [['12345.67']]
    return result


# ============================================================================
# TEST CONFIGURATION LOADING
# ============================================================================

class TestConfigurationLoading:
    """Tests for configuration loading and validation."""

    def test_load_valid_config(self, sample_config, tmp_path):
        """Test loading valid configuration file."""
        config_file = tmp_path / "tool_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        executor = UnifiedToolExecutor(
            warehouse_id="test123",
            config_path=str(config_file)
        )

        assert executor.warehouse_id == "test123"
        assert 'AU' in executor.config
        assert 'US' in executor.config

    def test_load_missing_config_file(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(ToolConfigurationError, match="not found"):
            UnifiedToolExecutor(
                warehouse_id="test123",
                config_path="/nonexistent/path/config.yaml"
            )

    def test_load_invalid_yaml(self, tmp_path):
        """Test error on invalid YAML syntax."""
        config_file = tmp_path / "bad_config.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: syntax: [")

        with pytest.raises(ToolConfigurationError, match="Invalid YAML"):
            UnifiedToolExecutor(
                warehouse_id="test123",
                config_path=str(config_file)
            )

    def test_load_config_missing_countries(self, tmp_path):
        """Test error when config missing 'countries' section."""
        config_file = tmp_path / "no_countries.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({'other_section': {}}, f)

        with pytest.raises(ToolConfigurationError, match="missing 'countries'"):
            UnifiedToolExecutor(
                warehouse_id="test123",
                config_path=str(config_file)
            )

    def test_load_empty_config(self, tmp_path):
        """Test error when config file is empty."""
        config_file = tmp_path / "empty.yaml"
        config_file.touch()

        with pytest.raises(ToolConfigurationError, match="missing 'countries'"):
            UnifiedToolExecutor(
                warehouse_id="test123",
                config_path=str(config_file)
            )


# ============================================================================
# TEST PARAMETER RESOLUTION
# ============================================================================

class TestParameterResolution:
    """Tests for parameter resolution from profiles."""

    @pytest.fixture
    def executor(self, sample_config, tmp_path):
        """Create executor with sample config."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        return UnifiedToolExecutor("test123", config_path=str(config_file))

    def test_resolve_simple_string_member_id(self, executor, sample_profile):
        """Test resolving 'member_id' special value."""
        result = executor._resolve_param_value(
            "member_id", sample_profile, 50000, "M001"
        )
        assert result == "M001"

    def test_resolve_simple_string_withdrawal_amount(self, executor, sample_profile):
        """Test resolving 'withdrawal_amount' special value."""
        result = executor._resolve_param_value(
            "withdrawal_amount", sample_profile, 50000, "M001"
        )
        assert result == 50000

    def test_resolve_simple_string_age(self, executor, sample_profile):
        """Test resolving 'age' from profile."""
        result = executor._resolve_param_value(
            "age", sample_profile, None, "M001"
        )
        assert result == 65

    def test_resolve_simple_string_balance(self, executor, sample_profile):
        """Test resolving 'balance' maps to super_balance."""
        result = executor._resolve_param_value(
            "balance", sample_profile, None, "M001"
        )
        assert result == 500000

    def test_resolve_dict_with_default(self, executor):
        """Test resolving dict parameter with default value."""
        profile = {'age': 60}
        result = executor._resolve_param_value(
            {'preservation_age': 65}, profile, None, "M001"
        )
        assert result == 65  # default

        profile['preservation_age'] = 55
        result = executor._resolve_param_value(
            {'preservation_age': 65}, profile, None, "M001"
        )
        assert result == 55  # from profile

    def test_resolve_dict_super_balance_default(self, executor):
        """Test resolving super_balance with default."""
        profile = {}
        result = executor._resolve_param_value(
            {'super_balance': 10000}, profile, None, "M001"
        )
        assert result == 10000  # default

        profile['super_balance'] = 50000
        result = executor._resolve_param_value(
            {'super_balance': 10000}, profile, None, "M001"
        )
        assert result == 50000  # from profile

    def test_resolve_missing_required_param(self, executor):
        """Test error when required parameter missing from profile."""
        profile = {}
        with pytest.raises(ToolConfigurationError, match="not found in profile"):
            executor._resolve_param_value(
                "required_field", profile, None, "M001"
            )

    def test_resolve_literal_value(self, executor, sample_profile):
        """Test resolving literal int/float values."""
        result = executor._resolve_param_value(100, sample_profile, None, "M001")
        assert result == 100

        result = executor._resolve_param_value(25.5, sample_profile, None, "M001")
        assert result == 25.5


# ============================================================================
# TEST QUERY BUILDING
# ============================================================================

class TestQueryBuilding:
    """Tests for SQL query building from templates."""

    @pytest.fixture
    def executor(self, sample_config, tmp_path):
        """Create executor with sample config."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        return UnifiedToolExecutor("test123", config_path=str(config_file))

    def test_build_query_simple_params(self, executor, sample_profile):
        """Test building query with simple parameters."""
        tool_config = {
            'query_template': "SELECT func('{member_id}', {age})",
            'params': ['member_id', 'age']
        }

        query = executor._build_query(
            tool_config, "M001", sample_profile, None
        )

        assert "SELECT func('M001', 65)" == query

    def test_build_query_with_defaults(self, executor):
        """Test building query with default values."""
        tool_config = {
            'query_template': "SELECT func({balance}, {other_assets})",
            'params': [
                {'balance': 'super_balance'},
                {'other_assets': 0}
            ]
        }

        profile = {'super_balance': 500000}  # other_assets missing
        query = executor._build_query(tool_config, "M001", profile, None)

        assert "SELECT func(500000, 0)" == query

    def test_build_query_with_withdrawal_amount(self, executor, sample_profile):
        """Test building query with withdrawal amount."""
        tool_config = {
            'query_template': "SELECT tax({withdrawal_amount}, {age})",
            'params': ['withdrawal_amount', 'age']
        }

        query = executor._build_query(
            tool_config, "M001", sample_profile, 50000
        )

        assert "SELECT tax(50000, 65)" == query

    def test_build_query_missing_param_in_template(self, executor, sample_profile):
        """Test error when template references undefined parameter."""
        tool_config = {
            'query_template': "SELECT func({undefined_param})",
            'params': []
        }

        with pytest.raises(ToolConfigurationError, match="Missing parameter"):
            executor._build_query(tool_config, "M001", sample_profile, None)


# ============================================================================
# TEST TOOL EXECUTION
# ============================================================================

class TestToolExecution:
    """Tests for end-to-end tool execution."""

    @pytest.fixture
    def executor(self, sample_config, tmp_path):
        """Create executor with sample config."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        return UnifiedToolExecutor("test123", config_path=str(config_file))

    @patch('tools.tool_executor.execute_sql_statement')
    @patch('tools.tool_executor.get_citations')
    def test_execute_tool_successful(self, mock_citations, mock_sql, executor, sample_profile, mock_sql_result):
        """Test successful tool execution."""
        mock_sql.return_value = mock_sql_result
        mock_citations.return_value = [{'id': 'AU-TAX-001', 'url': 'https://ato.gov.au'}]

        result = executor.execute_tool(
            country="AU",
            tool_id="tax",
            member_id="M001",
            profile=sample_profile,
            withdrawal_amount=50000
        )

        assert result['tool_name'] == 'ATO Tax Calculator'
        assert result['tool_id'] == 'tax'
        assert result['uc_function'] == 'au_calculate_tax'
        assert result['authority'] == 'Australian Taxation Office'
        assert result['calculation'] == '12345.67'
        assert len(result['citations']) == 1
        assert isinstance(result['duration'], float)

        # Verify SQL was called
        mock_sql.assert_called_once()
        call_args = mock_sql.call_args[0]
        assert 'au_tax' in call_args[0]
        assert "'M001'" in call_args[0]

    @patch('tools.tool_executor.execute_sql_statement')
    @patch('tools.tool_executor.get_citations')
    def test_execute_tool_all_countries(self, mock_citations, mock_sql, executor, sample_profile, mock_sql_result):
        """Test execution for all configured countries."""
        mock_sql.return_value = mock_sql_result
        mock_citations.return_value = []

        # Test AU
        result = executor.execute_tool("AU", "tax", "M001", sample_profile, 50000)
        assert result['authority'] == 'Australian Taxation Office'

        # Test US
        result = executor.execute_tool("US", "tax", "M001", sample_profile, 50000)
        assert result['authority'] == 'IRS'

    def test_execute_tool_invalid_country(self, executor, sample_profile):
        """Test error on invalid country code."""
        with pytest.raises(ToolConfigurationError, match="not supported"):
            executor.execute_tool(
                country="XX",
                tool_id="tax",
                member_id="M001",
                profile=sample_profile,
                withdrawal_amount=50000
            )

    def test_execute_tool_invalid_tool_id(self, executor, sample_profile):
        """Test error on invalid tool_id."""
        with pytest.raises(ToolConfigurationError, match="not found"):
            executor.execute_tool(
                country="AU",
                tool_id="invalid_tool",
                member_id="M001",
                profile=sample_profile,
                withdrawal_amount=50000
            )

    @patch('tools.tool_executor.execute_sql_statement')
    def test_execute_tool_sql_execution_failure(self, mock_sql, executor, sample_profile):
        """Test error handling when SQL execution fails."""
        mock_sql.side_effect = Exception("SQL connection failed")

        with pytest.raises(ToolExecutionError, match="Failed to execute"):
            executor.execute_tool(
                country="AU",
                tool_id="tax",
                member_id="M001",
                profile=sample_profile,
                withdrawal_amount=50000
            )

    @patch('tools.tool_executor.execute_sql_statement')
    def test_execute_tool_no_result_returned(self, mock_sql, executor, sample_profile):
        """Test error when SQL returns no result."""
        mock_sql.return_value = None

        with pytest.raises(ToolExecutionError, match="No result"):
            executor.execute_tool(
                country="AU",
                tool_id="tax",
                member_id="M001",
                profile=sample_profile,
                withdrawal_amount=50000
            )

    @patch('tools.tool_executor.execute_sql_statement')
    def test_execute_tool_empty_data_array(self, mock_sql, executor, sample_profile):
        """Test error when result has empty data array."""
        result = Mock()
        result.result.data_array = []
        mock_sql.return_value = result

        with pytest.raises(ToolExecutionError, match="No result"):
            executor.execute_tool(
                country="AU",
                tool_id="tax",
                member_id="M001",
                profile=sample_profile,
                withdrawal_amount=50000
            )


# ============================================================================
# TEST LOGGING INTEGRATION
# ============================================================================

class TestLoggingIntegration:
    """Tests for logging integration."""

    @pytest.fixture
    def executor_with_logger(self, sample_config, tmp_path):
        """Create executor with mock logger."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        mock_logger = Mock(spec=logging.Logger)
        return UnifiedToolExecutor("test123", config_path=str(config_file), logger=mock_logger), mock_logger

    def test_logs_initialization(self, executor_with_logger):
        """Test initialization logging."""
        executor, mock_logger = executor_with_logger
        mock_logger.debug.assert_called()

    @patch('tools.tool_executor.execute_sql_statement')
    @patch('tools.tool_executor.get_citations')
    def test_logs_successful_execution(self, mock_citations, mock_sql, executor_with_logger, sample_profile, mock_sql_result):
        """Test logging on successful execution."""
        executor, mock_logger = executor_with_logger
        mock_sql.return_value = mock_sql_result
        mock_citations.return_value = []

        executor.execute_tool("AU", "tax", "M001", sample_profile, 50000)

        # Should log debug and info messages
        assert mock_logger.debug.call_count >= 2
        mock_logger.info.assert_called()

    @patch('tools.tool_executor.execute_sql_statement')
    def test_logs_execution_error(self, mock_sql, executor_with_logger, sample_profile):
        """Test logging on execution error."""
        executor, mock_logger = executor_with_logger
        mock_sql.side_effect = Exception("SQL error")

        with pytest.raises(ToolExecutionError):
            executor.execute_tool("AU", "tax", "M001", sample_profile, 50000)

        # Should log error
        mock_logger.error.assert_called()


# ============================================================================
# TEST FACTORY FUNCTION
# ============================================================================

class TestFactoryFunction:
    """Tests for create_executor factory function."""

    @patch('tools.tool_executor.UnifiedToolExecutor')
    def test_create_executor(self, mock_class):
        """Test factory function creates executor."""
        executor = create_executor("test123")

        mock_class.assert_called_once()
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs['warehouse_id'] == "test123"

    @patch('tools.tool_executor.UnifiedToolExecutor')
    def test_create_executor_with_logger(self, mock_class):
        """Test factory function with custom logger."""
        mock_logger = Mock(spec=logging.Logger)
        executor = create_executor("test123", logger=mock_logger)

        call_kwargs = mock_class.call_args[1]
        assert call_kwargs['logger'] == mock_logger


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def full_config(self, tmp_path):
        """Create full configuration file."""
        config = {
            'countries': {
                'AU': {
                    'tools': {
                        'tax': {
                            'name': 'ATO Tax Calculator',
                            'uc_function': 'au_calculate_tax',
                            'authority': 'ATO',
                            'citations': ['AU-TAX-001'],
                            'query_template': "SELECT au_tax('{member_id}', {age}, {withdrawal_amount})",
                            'params': ['member_id', 'age', 'withdrawal_amount']
                        }
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        return str(config_file)

    @patch('tools.tool_executor.execute_sql_statement')
    @patch('tools.tool_executor.get_citations')
    def test_end_to_end_execution(self, mock_citations, mock_sql, full_config, sample_profile, mock_sql_result):
        """Test complete end-to-end execution flow."""
        mock_sql.return_value = mock_sql_result
        mock_citations.return_value = [{'id': 'AU-TAX-001'}]

        # Create executor
        executor = UnifiedToolExecutor("test123", config_path=full_config)

        # Execute tool
        result = executor.execute_tool(
            country="AU",
            tool_id="tax",
            member_id="M001",
            profile=sample_profile,
            withdrawal_amount=50000
        )

        # Verify complete result structure
        assert 'tool_name' in result
        assert 'tool_id' in result
        assert 'uc_function' in result
        assert 'authority' in result
        assert 'calculation' in result
        assert 'citations' in result
        assert 'duration' in result

        assert result['calculation'] == '12345.67'
        assert result['duration'] > 0
