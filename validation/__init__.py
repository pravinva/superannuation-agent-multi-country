"""
validation
==========

Validation package for superannuation agent.

This package provides validation utilities for response quality checking:
- LLMJudgeValidator: LLM-based validation with comprehensive checking
- DeterministicValidator: Fast deterministic validation without LLM costs
- TokenCalculator: Token tracking and cost calculation
- JSONParser: Robust JSON parsing with fallback strategies

Modules:
    token_calculator: Token and cost tracking
    json_parser: JSON parsing utilities

Usage:
    >>> from validation import LLMJudgeValidator, DeterministicValidator
    >>> from validation.token_calculator import TokenCalculator
    >>> from validation.json_parser import JSONParser
    >>>
    >>> validator = LLMJudgeValidator()
    >>> result = validator.validate(response_text, user_query, context)

Author: Refactoring Team
Date: 2024-11-24
"""

import importlib.util
from pathlib import Path

from validation.token_calculator import TokenCalculator, get_token_calculator
from validation.json_parser import JSONParser, get_json_parser

# Also expose classes from the root-level validation.py file
# This resolves the naming conflict between validation.py file and validation/ package
_validation_module_path = Path(__file__).parent.parent / 'validation.py'
if _validation_module_path.exists():
    _spec = importlib.util.spec_from_file_location("_root_validation", _validation_module_path)
    if _spec and _spec.loader:
        _root_validation = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_root_validation)

        # Export validator classes from root validation.py
        LLMJudgeValidator = _root_validation.LLMJudgeValidator
        DeterministicValidator = _root_validation.DeterministicValidator

        __all__ = [
            'TokenCalculator',
            'get_token_calculator',
            'JSONParser',
            'get_json_parser',
            'LLMJudgeValidator',
            'DeterministicValidator',
        ]
else:
    __all__ = [
        'TokenCalculator',
        'get_token_calculator',
        'JSONParser',
        'get_json_parser',
    ]
