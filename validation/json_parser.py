"""
validation.json_parser
======================

JSON parsing utilities for validation responses with fallback strategies.

This module provides:
- 4-strategy JSON parsing with progressive fallback
- Malformed JSON fixing (trailing commas, unclosed strings, unclosed objects)
- Validation result structure checking
- Robust error handling for LLM-generated JSON

Extracted from validation.py to improve modularity and testability.

Usage:
    >>> from validation.json_parser import JSONParser
    >>>
    >>> parser = JSONParser()
    >>> result = parser.parse_validation_response(judge_output)
    >>> if result:
    >>>     logger.info(f"Passed: {result['passed']}")

Author: Refactoring Team
Date: 2024-11-24
"""

import json
import re
from typing import Optional, Dict, Any
from shared.logging_config import get_logger


class JSONParser:
    """
    JSON parser for validation responses with fallback strategies.

    Provides robust JSON parsing using a 4-strategy approach to handle
    malformed JSON from LLM responses.
    """

    def __init__(self, logger=None):
        """Initialize JSON parser.

        Args:
            logger: Optional logger instance (uses default if not provided)
        """
        self.logger = logger or get_logger(__name__)

    def parse_validation_response(self, judge_output: str) -> Optional[Dict[str, Any]]:
        """
        Parse validation response using multiple fallback strategies.

        Tries 4 strategies in order:
        1. Direct JSON parsing (clean)
        2. Fix malformed JSON then parse
        3. Extract from markdown code block, fix, and parse
        4. Extract between braces, fix, and parse

        Args:
            judge_output: Raw output from LLM judge

        Returns:
            Parsed validation result dict with keys:
            - passed (bool): Whether validation passed
            - confidence (float): Confidence score 0.0-1.0
            - violations (list): List of violation dicts
            - reasoning (str): Validation reasoning
            - _validator_used (str): Validator type marker

            Returns None if all strategies fail.

        Examples:
            >>> parser = JSONParser()
            >>> result = parser.parse_validation_response('{"passed": true, "confidence": 0.95}')
            >>> assert result['passed'] == True
            >>> assert result['_validator_used'] == 'LLM_JUDGE'
        """
        self.logger.info(f"🔍 Parsing LLM judge output ({len(judge_output)} chars)")

        # Strategy 1: Direct JSON (clean parse)
        try:
            result = json.loads(judge_output)
            if self._is_valid_result(result):
                self.logger.info("✅ Strategy 1: Direct JSON parse succeeded - LLM JUDGE WORKING")
                result['_validator_used'] = 'LLM_JUDGE'
                self.logger.info(f"✅ Validation result from LLM: passed={result['passed']}, confidence={result['confidence']}")
                return result
        except json.JSONDecodeError as e:
            self.logger.warning(f"⚠️ Strategy 1 failed: {str(e)[:100]}")

        # Strategy 2: Fix malformed JSON
        try:
            fixed_output = self._fix_malformed_json(judge_output)
            result = json.loads(fixed_output)
            if self._is_valid_result(result):
                self.logger.info("✅ Strategy 2: Fixed malformed JSON - LLM JUDGE WORKING")
                result['_validator_used'] = 'LLM_JUDGE'
                self.logger.info(f"✅ Validation result from LLM: passed={result['passed']}, confidence={result['confidence']}")
                return result
        except Exception as e:
            self.logger.warning(f"⚠️ Strategy 2 failed: {str(e)[:100]}")

        # Strategy 3: Extract from markdown code block
        try:
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', judge_output, re.MULTILINE | re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                # Remove 'json' language identifier if present
                json_str = re.sub(r'^json\s*', '', json_str, flags=re.IGNORECASE | re.MULTILINE)
                json_str = self._fix_malformed_json(json_str)
                result = json.loads(json_str)
                if self._is_valid_result(result):
                    self.logger.info("✅ Strategy 3: Markdown + fixed - LLM JUDGE WORKING")
                    result['_validator_used'] = 'LLM_JUDGE'
                    self.logger.info(f"✅ Validation result from LLM: passed={result['passed']}, confidence={result['confidence']}")
                    return result
        except Exception as e:
            self.logger.warning(f"⚠️ Strategy 3 failed: {str(e)[:100]}")

        # Strategy 4: Extract between braces and fix
        try:
            first_brace = judge_output.find('{')
            last_brace = judge_output.rfind('}')
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                json_str = judge_output[first_brace:last_brace+1]
                json_str = self._fix_malformed_json(json_str)
                result = json.loads(json_str)
                if self._is_valid_result(result):
                    self.logger.info("✅ Strategy 4: Brace extraction + fixed - LLM JUDGE WORKING")
                    result['_validator_used'] = 'LLM_JUDGE'
                    self.logger.info(f"✅ Validation result from LLM: passed={result['passed']}, confidence={result['confidence']}")
                    return result
        except Exception as e:
            self.logger.warning(f"⚠️ Strategy 4 failed: {str(e)[:100]}")

        self.logger.error("❌ ALL LLM JUDGE JSON STRATEGIES FAILED")
        self.logger.debug(f"🔍 Judge output (first 500 chars): {judge_output[:500]}")
        self.logger.warning("⚠️ Falling back to keyword-based validation")
        return None

    def _is_valid_result(self, result: Any) -> bool:
        """
        Check if parsed result has required validation structure.

        Args:
            result: Parsed JSON object

        Returns:
            True if result is a dict with 'passed' and 'confidence' keys

        Examples:
            >>> parser = JSONParser()
            >>> assert parser._is_valid_result({'passed': True, 'confidence': 0.9})
            >>> assert not parser._is_valid_result({'passed': True})  # missing confidence
            >>> assert not parser._is_valid_result("not a dict")
        """
        return (
            isinstance(result, dict) and
            "passed" in result and
            "confidence" in result
        )

    def _fix_malformed_json(self, json_str: str) -> str:
        """
        Fix common malformed JSON issues.

        Handles:
        - Trailing commas before closing brackets/braces
        - Unclosed strings (missing closing quote)
        - Unclosed objects (missing closing brace)

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Fixed JSON string (best effort)

        Examples:
            >>> parser = JSONParser()
            >>> fixed = parser._fix_malformed_json('{"foo": "bar",}')
            >>> assert fixed == '{"foo": "bar"}'
            >>>
            >>> fixed = parser._fix_malformed_json('{"foo": "bar')
            >>> assert '"' in fixed  # adds closing quote
        """
        # Remove trailing commas before closing brackets/braces
        json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)

        # Fix unclosed strings
        json_str = json_str.rstrip()
        if not json_str.endswith('"'):
            if json_str.count('"') % 2 == 1:
                json_str = json_str + '"'

        # Fix unclosed objects
        if not json_str.endswith('}'):
            last_brace = json_str.rfind('}')
            if last_brace != -1:
                json_str = json_str[:last_brace+1]
            else:
                json_str = json_str + '}'

        return json_str


# Singleton instance for global access
_global_parser: Optional[JSONParser] = None


def get_json_parser(logger=None) -> JSONParser:
    """
    Get or create the global JSON parser instance.

    Args:
        logger: Optional logger instance (only used on first call)

    Returns:
        JSONParser instance

    Examples:
        >>> parser = get_json_parser()
        >>> result = parser.parse_validation_response(judge_output)
    """
    global _global_parser

    if _global_parser is None:
        _global_parser = JSONParser(logger=logger)

    return _global_parser


if __name__ == "__main__":
    # Test JSON parser when run directly
    logger.info("=" * 70)
    logger.info("JSON Parser - Test Suite")
    logger.info("=" * 70)

    parser = JSONParser()

    # Test 1: Clean JSON
    logger.info("\nTest 1: Clean JSON")
    clean_json = '{"passed": true, "confidence": 0.95, "violations": []}'
    result = parser.parse_validation_response(clean_json)
    logger.info(f"  Result: {result is not None}")
    logger.info(f"  Passed: {result['passed'] if result else 'N/A'}")
    logger.info(f"  Validator: {result.get('_validator_used', 'N/A') if result else 'N/A'}")

    # Test 2: Malformed JSON (trailing comma)
    logger.info("\nTest 2: Malformed JSON (trailing comma)")
    malformed = '{"passed": false, "confidence": 0.8, "violations": [],}'
    result = parser.parse_validation_response(malformed)
    logger.info(f"  Result: {result is not None}")
    logger.info(f"  Passed: {result['passed'] if result else 'N/A'}")

    # Test 3: Markdown code block
    logger.info("\nTest 3: Markdown code block")
    markdown = '''Here is the validation result:

```json
{
  "passed": true,
  "confidence": 0.92,
  "violations": []
}
```

The response looks good.'''
    result = parser.parse_validation_response(markdown)
    logger.info(f"  Result: {result is not None}")
    logger.info(f"  Passed: {result['passed'] if result else 'N/A'}")

    # Test 4: Embedded in text
    logger.info("\nTest 4: Embedded in text")
    embedded = '''The validation shows {"passed": true, "confidence": 0.88, "violations": []} based on analysis.'''
    result = parser.parse_validation_response(embedded)
    logger.info(f"  Result: {result is not None}")
    logger.info(f"  Passed: {result['passed'] if result else 'N/A'}")

    # Test 5: Invalid JSON (should fail all strategies)
    logger.info("\nTest 5: Invalid JSON (should fail)")
    invalid = "This is not JSON at all, just plain text."
    result = parser.parse_validation_response(invalid)
    logger.info(f"  Result: {result is None}")

    # Test 6: Fix malformed JSON
    logger.info("\nTest 6: Fix malformed JSON")
    test_cases = [
        ('{"foo": "bar",}', 'trailing comma'),
        ('{"foo": "bar', 'unclosed string'),
        ('{"foo": "bar"', 'unclosed object'),
    ]
    for test_str, description in test_cases:
        try:
            fixed = parser._fix_malformed_json(test_str)
            json.loads(fixed)  # Try to parse
            logger.info(f"  ✅ Fixed {description}: {test_str[:30]}")
        except Exception as e:
            logger.info(f"  ❌ Failed {description}: {str(e)[:50]}")

    # Test 7: Singleton pattern
    logger.info("\nTest 7: Singleton pattern")
    parser1 = get_json_parser()
    parser2 = get_json_parser()
    logger.info(f"  Same instance: {parser1 is parser2}")

    logger.info("\n" + "=" * 70)
