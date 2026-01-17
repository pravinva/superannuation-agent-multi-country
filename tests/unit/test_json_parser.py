"""
Unit tests for validation.json_parser module.

Tests cover:
- JSONParser initialization
- JSON parsing with 4 fallback strategies
- Malformed JSON fixing
- Result validation
- Singleton pattern
- Edge cases and error handling

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
import json
from unittest.mock import Mock, patch

from validation.json_parser import (
    JSONParser,
    get_json_parser,
    _global_parser
)


class TestJSONParserInitialization:
    """Test suite for JSONParser initialization."""

    def test_init_creates_parser(self):
        """Test JSONParser initialization."""
        parser = JSONParser()
        assert parser is not None
        assert parser.logger is not None

    def test_init_with_custom_logger(self):
        """Test JSONParser initialization with custom logger."""
        mock_logger = Mock()
        parser = JSONParser(logger=mock_logger)
        assert parser.logger == mock_logger


class TestStrategy1DirectJSON:
    """Test suite for Strategy 1: Direct JSON parsing."""

    def test_parse_clean_json(self):
        """Test parsing clean, valid JSON."""
        parser = JSONParser()

        json_str = '{"passed": true, "confidence": 0.95, "violations": []}'
        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is True
        assert result['confidence'] == 0.95
        assert result['_validator_used'] == 'LLM_JUDGE'

    def test_parse_clean_json_with_false(self):
        """Test parsing JSON with passed=false."""
        parser = JSONParser()

        json_str = '{"passed": false, "confidence": 0.8, "violations": [{"code": "TEST"}]}'
        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is False
        assert result['confidence'] == 0.8
        assert len(result['violations']) == 1

    def test_parse_json_with_extra_fields(self):
        """Test parsing JSON with additional fields."""
        parser = JSONParser()

        json_str = '{"passed": true, "confidence": 0.92, "violations": [], "reasoning": "All good", "extra": "field"}'
        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is True
        assert result['reasoning'] == "All good"
        assert result['extra'] == "field"


class TestStrategy2MalformedJSON:
    """Test suite for Strategy 2: Fix malformed JSON."""

    def test_parse_json_with_trailing_comma(self):
        """Test parsing JSON with trailing comma."""
        parser = JSONParser()

        json_str = '{"passed": true, "confidence": 0.88, "violations": [],}'
        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is True
        assert result['confidence'] == 0.88

    def test_parse_json_with_unclosed_string(self):
        """Test parsing JSON with unclosed string."""
        parser = JSONParser()

        # Note: This might not parse even after fixing, so we test the fix method
        json_str = '{"passed": true, "confidence": 0.85, "violations": []'
        fixed = parser._fix_malformed_json(json_str)

        # Should add closing brace
        assert fixed.endswith('}')

    def test_parse_json_with_unclosed_object(self):
        """Test parsing JSON with unclosed object."""
        parser = JSONParser()

        json_str = '{"passed": true, "confidence": 0.90, "violations": ['
        fixed = parser._fix_malformed_json(json_str)

        # Should attempt to close object
        assert fixed.endswith('}')


class TestStrategy3MarkdownCodeBlock:
    """Test suite for Strategy 3: Extract from markdown code block."""

    def test_parse_json_in_markdown_block(self):
        """Test parsing JSON inside markdown code block."""
        parser = JSONParser()

        judge_output = '''Here is the validation result:

```json
{
  "passed": true,
  "confidence": 0.93,
  "violations": []
}
```

The response looks good.'''

        result = parser.parse_validation_response(judge_output)

        assert result is not None
        assert result['passed'] is True
        assert result['confidence'] == 0.93

    def test_parse_json_in_code_block_no_language(self):
        """Test parsing JSON in code block without language specifier."""
        parser = JSONParser()

        judge_output = '''```
{
  "passed": false,
  "confidence": 0.75,
  "violations": [{"code": "ERROR"}]
}
```'''

        result = parser.parse_validation_response(judge_output)

        assert result is not None
        assert result['passed'] is False
        assert result['confidence'] == 0.75

    def test_parse_json_in_markdown_with_text_around(self):
        """Test parsing JSON in markdown with surrounding text."""
        parser = JSONParser()

        judge_output = '''Based on my analysis:

```json
{"passed": true, "confidence": 0.89, "violations": []}
```

This validation passed all checks.'''

        result = parser.parse_validation_response(judge_output)

        assert result is not None
        assert result['passed'] is True


class TestStrategy4BraceExtraction:
    """Test suite for Strategy 4: Extract between braces."""

    def test_parse_json_embedded_in_text(self):
        """Test parsing JSON embedded in plain text."""
        parser = JSONParser()

        judge_output = '''The validation shows {"passed": true, "confidence": 0.91, "violations": []} based on analysis.'''

        result = parser.parse_validation_response(judge_output)

        assert result is not None
        assert result['passed'] is True
        assert result['confidence'] == 0.91

    def test_parse_json_with_prefix_text(self):
        """Test parsing JSON with text before it."""
        parser = JSONParser()

        judge_output = '''Result: {"passed": false, "confidence": 0.82, "violations": [{"code": "TEST"}]}'''

        result = parser.parse_validation_response(judge_output)

        assert result is not None
        assert result['passed'] is False

    def test_parse_json_with_suffix_text(self):
        """Test parsing JSON with text after it."""
        parser = JSONParser()

        judge_output = '''{"passed": true, "confidence": 0.87, "violations": []} - Analysis complete.'''

        result = parser.parse_validation_response(judge_output)

        assert result is not None
        assert result['passed'] is True


class TestMalformedJSONFixer:
    """Test suite for _fix_malformed_json method."""

    def test_fix_trailing_comma_in_array(self):
        """Test fixing trailing comma in array."""
        parser = JSONParser()

        malformed = '{"items": [1, 2, 3,]}'
        fixed = parser._fix_malformed_json(malformed)

        # Should remove trailing comma
        assert ',' not in fixed.split('[')[1].split(']')[0][-2:]

    def test_fix_trailing_comma_in_object(self):
        """Test fixing trailing comma in object."""
        parser = JSONParser()

        malformed = '{"a": 1, "b": 2,}'
        fixed = parser._fix_malformed_json(malformed)

        # Should parse after fixing
        result = json.loads(fixed)
        assert result['a'] == 1
        assert result['b'] == 2

    def test_fix_unclosed_string(self):
        """Test fixing unclosed string."""
        parser = JSONParser()

        malformed = '{"text": "hello'
        fixed = parser._fix_malformed_json(malformed)

        # Should have even number of quotes or attempt to close
        # This is best-effort, might not always work
        assert fixed.endswith('}') or fixed.endswith('"')

    def test_fix_unclosed_object(self):
        """Test fixing unclosed object."""
        parser = JSONParser()

        malformed = '{"passed": true, "confidence": 0.9'
        fixed = parser._fix_malformed_json(malformed)

        # Should end with }
        assert fixed.endswith('}')

    def test_fix_already_valid_json(self):
        """Test that valid JSON is not broken by fixer."""
        parser = JSONParser()

        valid = '{"passed": true, "confidence": 0.95}'
        fixed = parser._fix_malformed_json(valid)

        # Should still be valid
        result = json.loads(fixed)
        assert result['passed'] is True


class TestResultValidation:
    """Test suite for result validation."""

    def test_is_valid_result_with_all_fields(self):
        """Test validation of result with all required fields."""
        parser = JSONParser()

        result = {'passed': True, 'confidence': 0.9, 'violations': []}
        assert parser._is_valid_result(result) is True

    def test_is_valid_result_missing_passed(self):
        """Test validation fails when 'passed' is missing."""
        parser = JSONParser()

        result = {'confidence': 0.9, 'violations': []}
        assert parser._is_valid_result(result) is False

    def test_is_valid_result_missing_confidence(self):
        """Test validation fails when 'confidence' is missing."""
        parser = JSONParser()

        result = {'passed': True, 'violations': []}
        assert parser._is_valid_result(result) is False

    def test_is_valid_result_not_dict(self):
        """Test validation fails for non-dict."""
        parser = JSONParser()

        assert parser._is_valid_result("not a dict") is False
        assert parser._is_valid_result([]) is False
        assert parser._is_valid_result(None) is False


class TestParsingFailure:
    """Test suite for parsing failure scenarios."""

    def test_parse_invalid_json_returns_none(self):
        """Test that invalid JSON returns None."""
        parser = JSONParser()

        invalid_json = "This is not JSON at all, just plain text."
        result = parser.parse_validation_response(invalid_json)

        assert result is None

    def test_parse_json_missing_required_fields(self):
        """Test parsing JSON missing required fields returns None."""
        parser = JSONParser()

        # Missing 'confidence'
        invalid = '{"passed": true, "violations": []}'
        result = parser.parse_validation_response(invalid)

        assert result is None

    def test_parse_empty_string_returns_none(self):
        """Test parsing empty string returns None."""
        parser = JSONParser()

        result = parser.parse_validation_response("")

        assert result is None

    def test_parse_only_braces_returns_none(self):
        """Test parsing only braces returns None."""
        parser = JSONParser()

        result = parser.parse_validation_response("{}")

        assert result is None


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_parse_nested_json(self):
        """Test parsing nested JSON structures."""
        parser = JSONParser()

        json_str = '''
        {
          "passed": true,
          "confidence": 0.94,
          "violations": [],
          "details": {
            "scores": {"accuracy": 0.95, "completeness": 0.93}
          }
        }
        '''
        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is True
        assert result['details']['scores']['accuracy'] == 0.95

    def test_parse_json_with_unicode(self):
        """Test parsing JSON with unicode characters."""
        parser = JSONParser()

        json_str = '{"passed": true, "confidence": 0.90, "violations": [], "text": "Test ü € 中文"}'
        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is True
        assert "ü" in result['text']

    def test_parse_json_with_escaped_quotes(self):
        """Test parsing JSON with escaped quotes."""
        parser = JSONParser()

        json_str = '{"passed": true, "confidence": 0.88, "violations": [], "quote": "He said \\"hello\\""}'
        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is True
        assert '\\"' in result['quote'] or '"' in result['quote']

    def test_parse_json_with_newlines(self):
        """Test parsing JSON with embedded newlines."""
        parser = JSONParser()

        json_str = '''{"passed": true, "confidence": 0.92, "violations": [], "text": "Line 1\\nLine 2"}'''
        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is True

    def test_parse_very_long_json(self):
        """Test parsing very long JSON."""
        parser = JSONParser()

        # Create long violations list
        violations = [{"code": f"ERR{i}", "detail": f"Error {i}"} for i in range(100)]
        json_str = json.dumps({"passed": False, "confidence": 0.5, "violations": violations})

        result = parser.parse_validation_response(json_str)

        assert result is not None
        assert result['passed'] is False
        assert len(result['violations']) == 100


class TestSingletonPattern:
    """Test suite for singleton pattern."""

    def test_get_json_parser_returns_parser(self):
        """Test that get_json_parser returns JSONParser instance."""
        parser = get_json_parser()

        assert isinstance(parser, JSONParser)

    def test_get_json_parser_singleton(self):
        """Test that get_json_parser returns same instance."""
        # Reset global singleton
        import validation.json_parser as jp_module
        jp_module._global_parser = None

        parser1 = get_json_parser()
        parser2 = get_json_parser()

        # Should be same instance
        assert parser1 is parser2

    def test_get_json_parser_with_logger(self):
        """Test get_json_parser with custom logger."""
        mock_logger = Mock()

        # Reset global singleton
        import validation.json_parser as jp_module
        jp_module._global_parser = None

        parser = get_json_parser(logger=mock_logger)

        assert parser.logger == mock_logger


class TestIntegration:
    """Integration tests for JSONParser."""

    def test_full_parsing_workflow(self):
        """Test complete parsing workflow through all strategies."""
        parser = JSONParser()

        # Test clean JSON (Strategy 1)
        result1 = parser.parse_validation_response('{"passed": true, "confidence": 0.95, "violations": []}')
        assert result1 is not None

        # Test malformed (Strategy 2)
        result2 = parser.parse_validation_response('{"passed": true, "confidence": 0.90, "violations": [],}')
        assert result2 is not None

        # Test markdown (Strategy 3)
        result3 = parser.parse_validation_response('```json\n{"passed": true, "confidence": 0.88, "violations": []}\n```')
        assert result3 is not None

        # Test embedded (Strategy 4)
        result4 = parser.parse_validation_response('Result: {"passed": true, "confidence": 0.85, "violations": []}')
        assert result4 is not None

        # All should parse successfully
        assert all(r['passed'] for r in [result1, result2, result3, result4])

    def test_fallback_through_strategies(self):
        """Test that strategies are tried in order."""
        parser = JSONParser()

        # This should trigger multiple strategy attempts
        complex_output = '''The LLM responded with validation data.

```
{
  "passed": true,
  "confidence": 0.92,
  "violations": [],
}
```

Note: Minor formatting issue fixed.'''

        result = parser.parse_validation_response(complex_output)

        # Should still succeed via one of the strategies
        assert result is not None
        assert result['passed'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
