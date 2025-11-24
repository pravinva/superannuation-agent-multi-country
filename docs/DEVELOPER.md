# Developer Agent Instructions
## Maker Role in Maker-Checker Pattern

**Role:** Development Agent (Maker)
**Responsibility:** Implement refactoring according to plan with NO stubs, TODOs, or incomplete code
**Quality Standard:** Production-ready, fully tested, documented code

---

## Core Principles

### 1. NO STUBS OR INCOMPLETE CODE
```python
# ❌ NEVER DO THIS:
def calculate_cost():
    # TODO: implement this
    pass

# ❌ NEVER DO THIS:
def parse_json():
    # Stub implementation
    return {}

# ✅ ALWAYS DO THIS:
def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate LLM cost based on token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier

    Returns:
        Cost in dollars

    Raises:
        ValueError: If tokens are negative
        KeyError: If model not in pricing config
    """
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Token counts cannot be negative")

    pricing = get_model_pricing(model)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return round(input_cost + output_cost, 6)
```

### 2. EVERY FUNCTION MUST HAVE
- **Type hints** on all parameters and return values
- **Comprehensive docstring** with Args, Returns, Raises
- **Error handling** for edge cases
- **Unit tests** with 85%+ coverage
- **Integration test** if it interacts with external systems

### 3. NO PRINT STATEMENTS
```python
# ❌ NEVER DO THIS:
print("Starting validation...")
print(f"❌ Error: {e}")

# ✅ ALWAYS DO THIS:
logger.info("Starting validation")
logger.error(f"Validation failed: {e}", exc_info=True)
```

---

## Implementation Workflow

### For Each Task in REFACTORING_PLAN.md:

#### Step 1: Create File Structure
```bash
# Example for Task 1.1 (Logging System)
mkdir -p shared
touch shared/__init__.py
touch shared/logging_config.py
touch shared/logger.py
mkdir -p tests/unit
touch tests/unit/test_logging_config.py
```

#### Step 2: Implement Core Functionality
- Write the main implementation
- Include ALL error handling
- Add comprehensive docstrings
- Add type hints

**Example:**
```python
from typing import Optional, Dict
import logging
from shared.logging_config import get_logger

logger = get_logger(__name__)

def calculate_tokens(
    response: Any,
    prompt_length: int,
    model_type: str
) -> Dict[str, int]:
    """
    Extract token usage from API response.

    Args:
        response: API response object from LLM
        prompt_length: Length of prompt in characters
        model_type: Model identifier (e.g., 'databricks-claude-opus-4-1')

    Returns:
        Dictionary with keys: input_tokens, output_tokens, total_tokens

    Raises:
        ValueError: If prompt_length is negative
        TypeError: If response is None

    Examples:
        >>> response = MockResponse(prompt_tokens=100, completion_tokens=50)
        >>> calculate_tokens(response, 400, 'claude-opus')
        {'input_tokens': 100, 'output_tokens': 50, 'total_tokens': 150}
    """
    if response is None:
        raise TypeError("Response cannot be None")

    if prompt_length < 0:
        raise ValueError(f"Prompt length cannot be negative: {prompt_length}")

    input_tokens = 0
    output_tokens = 0

    try:
        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0)
            output_tokens = getattr(response.usage, 'completion_tokens', 0)
            logger.debug(f"Extracted tokens: in={input_tokens}, out={output_tokens}")
        else:
            # Fallback estimation
            input_tokens = prompt_length // 4
            output_tokens = 100
            logger.warning(f"No usage data in response, estimating: in={input_tokens}, out={output_tokens}")
    except Exception as e:
        logger.error(f"Error extracting tokens: {e}", exc_info=True)
        # Still return estimated values
        input_tokens = prompt_length // 4
        output_tokens = 100

    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens
    }
```

#### Step 3: Write Comprehensive Tests
```python
import pytest
from unittest.mock import Mock
from validation.token_calculator import calculate_tokens

class TestCalculateTokens:
    """Test suite for calculate_tokens function"""

    def test_calculate_tokens_with_usage(self):
        """Test token extraction from response with usage data"""
        # Arrange
        mock_response = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        # Act
        result = calculate_tokens(mock_response, 400, 'claude-opus')

        # Assert
        assert result['input_tokens'] == 100
        assert result['output_tokens'] == 50
        assert result['total_tokens'] == 150

    def test_calculate_tokens_without_usage(self):
        """Test token estimation when no usage data available"""
        # Arrange
        mock_response = Mock()
        mock_response.usage = None

        # Act
        result = calculate_tokens(mock_response, 400, 'claude-opus')

        # Assert
        assert result['input_tokens'] == 100  # 400 // 4
        assert result['output_tokens'] == 100  # fallback
        assert result['total_tokens'] == 200

    def test_calculate_tokens_none_response(self):
        """Test error handling for None response"""
        # Act & Assert
        with pytest.raises(TypeError, match="Response cannot be None"):
            calculate_tokens(None, 400, 'claude-opus')

    def test_calculate_tokens_negative_prompt_length(self):
        """Test error handling for negative prompt length"""
        # Arrange
        mock_response = Mock()

        # Act & Assert
        with pytest.raises(ValueError, match="Prompt length cannot be negative"):
            calculate_tokens(mock_response, -10, 'claude-opus')

    def test_calculate_tokens_with_exception(self):
        """Test graceful handling of exceptions during extraction"""
        # Arrange
        mock_response = Mock()
        mock_response.usage.side_effect = AttributeError("No usage")

        # Act
        result = calculate_tokens(mock_response, 400, 'claude-opus')

        # Assert - should still return estimated values
        assert result['input_tokens'] == 100
        assert result['output_tokens'] == 100
```

#### Step 4: Write Integration Tests (if applicable)
```python
import pytest
from validation.validator import ResponseValidator
from validation.token_calculator import TokenCostCalculator

class TestValidationIntegration:
    """Integration tests for validation flow"""

    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return ResponseValidator(
            model_type="databricks-claude-sonnet-4",
            confidence_threshold=0.70
        )

    def test_end_to_end_validation_success(self, validator):
        """Test complete validation flow with passing validation"""
        # Arrange
        response_text = "I can help with your superannuation questions."
        query = "Can I withdraw my super early?"

        # Act
        result = validator.validate_response(response_text, query)

        # Assert
        assert result.passed is True
        assert result.confidence >= 0.70
        assert result.input_tokens > 0
        assert result.output_tokens > 0
        assert result.cost > 0
        assert len(result.violations) == 0

    def test_end_to_end_validation_failure(self, validator):
        """Test complete validation flow with failing validation"""
        # Arrange
        response_text = "Let me tell you a joke instead..."
        query = "What's my super balance?"

        # Act
        result = validator.validate_response(response_text, query)

        # Assert
        assert result.passed is False
        assert len(result.violations) > 0
        assert result.violations[0].severity in ['high', 'critical']
```

#### Step 5: Update Documentation
```python
"""
validation.result_builder
=========================

This module provides data structures for validation results.

Classes:
    ValidationViolation: Represents a single validation violation
    ValidationResult: Complete validation result with metadata

Usage:
    >>> violation = ValidationViolation(
    ...     code="OFF_TOPIC",
    ...     severity="high",
    ...     detail="Response is not about retirement",
    ...     evidence="Talking about weather"
    ... )
    >>> result = ValidationResult(
    ...     passed=False,
    ...     confidence=0.95,
    ...     violations=[violation],
    ...     reasoning="Query is off-topic",
    ...     validator_used="judge_llm"
    ... )
    >>> result.to_dict()
    {...}

Author: Development Team
Date: 2024-11-24
"""
```

#### Step 6: Run Quality Checks
```bash
# Run tests
pytest tests/unit/test_token_calculator.py -v --cov=validation.token_calculator

# Check type hints
mypy validation/token_calculator.py

# Check code style
black validation/token_calculator.py
flake8 validation/token_calculator.py

# Check for print statements
grep -n "print(" validation/token_calculator.py
# Should return nothing!
```

---

## Task Completion Checklist

Before marking a task as complete, verify:

### Code Quality
- [ ] NO print() statements anywhere
- [ ] NO stub functions or TODO comments
- [ ] ALL functions have type hints
- [ ] ALL functions have docstrings
- [ ] ALL error cases are handled
- [ ] ALL edge cases are tested
- [ ] Logging is used instead of print()

### Testing
- [ ] Unit tests written for all functions
- [ ] Unit test coverage >= 85%
- [ ] Integration tests written (if applicable)
- [ ] All tests pass locally
- [ ] Performance tests written (if applicable)
- [ ] Edge cases are tested
- [ ] Error handling is tested

### Documentation
- [ ] Module docstring present
- [ ] Function docstrings complete (Args, Returns, Raises, Examples)
- [ ] README updated (if applicable)
- [ ] Configuration changes documented
- [ ] Migration notes written (if breaking changes)

### Integration
- [ ] Backward compatibility maintained (or migration path provided)
- [ ] Configuration files updated
- [ ] Dependencies added to requirements.txt
- [ ] No breaking changes to existing APIs (unless planned)

### Code Review Readiness
- [ ] Code follows PEP 8
- [ ] Code passes mypy type checking
- [ ] Code passes flake8 linting
- [ ] Code formatted with black
- [ ] No security vulnerabilities
- [ ] No hardcoded secrets or credentials

---

## Common Patterns

### 1. Error Handling Pattern
```python
from shared.logging_config import get_logger

logger = get_logger(__name__)

def process_data(data: Dict) -> Dict:
    """Process data with comprehensive error handling"""
    try:
        # Validate input
        if not data:
            raise ValueError("Data cannot be empty")

        if 'required_field' not in data:
            raise KeyError("Missing required field: required_field")

        # Process
        result = perform_operation(data)

        # Validate output
        if not result:
            logger.warning("Operation returned empty result")
            return {}

        logger.info(f"Successfully processed data with {len(result)} items")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except KeyError as e:
        logger.error(f"Missing key: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing data: {e}", exc_info=True)
        raise RuntimeError(f"Failed to process data: {e}") from e
```

### 2. Configuration Loading Pattern
```python
from functools import lru_cache
from pathlib import Path
import yaml

@lru_cache(maxsize=1)
def load_config(config_file: str) -> Dict:
    """
    Load configuration from YAML file (cached).

    Args:
        config_file: Path to YAML config file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_path = Path(__file__).parent / config_file

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded configuration from {config_path}")
        return config

    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {config_path}: {e}")
        raise
```

### 3. Context Manager Pattern
```python
from contextlib import contextmanager
import time

@contextmanager
def track_operation(operation_name: str):
    """
    Context manager for tracking operation execution.

    Args:
        operation_name: Name of operation being tracked

    Yields:
        None

    Examples:
        >>> with track_operation("data_processing"):
        ...     process_data()
    """
    start_time = time.time()
    logger.info(f"Starting operation: {operation_name}")

    try:
        yield
        duration = time.time() - start_time
        logger.info(f"Completed {operation_name} in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Operation {operation_name} failed after {duration:.2f}s: {e}")
        raise
```

### 4. Dataclass Pattern
```python
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    success: bool
    items_processed: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: float = 0.0
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def has_errors(self) -> bool:
        """Check if result has errors"""
        return len(self.errors) > 0

    def error_summary(self) -> str:
        """Get summary of errors"""
        if not self.errors:
            return "No errors"
        return f"{len(self.errors)} errors: {', '.join(self.errors[:3])}"
```

---

## Anti-Patterns to Avoid

### ❌ DON'T: Use print() statements
```python
def process():
    print("Starting process...")
    result = do_work()
    print(f"✅ Done! Result: {result}")
```

### ✅ DO: Use structured logging
```python
def process():
    logger.info("Starting process")
    result = do_work()
    logger.info(f"Process completed successfully with result: {result}")
```

---

### ❌ DON'T: Leave TODOs or stubs
```python
def calculate_tax():
    # TODO: Implement tax calculation
    pass
```

### ✅ DO: Implement completely or don't commit
```python
def calculate_tax(income: float, country: str) -> float:
    """Calculate tax based on income and country"""
    tax_rates = get_tax_rates(country)
    return income * tax_rates['standard_rate']
```

---

### ❌ DON'T: Ignore error cases
```python
def parse_json(text: str) -> Dict:
    return json.loads(text)
```

### ✅ DO: Handle all errors
```python
def parse_json(text: str) -> Dict:
    """Parse JSON with error handling"""
    if not text:
        raise ValueError("Input text cannot be empty")

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        raise ValueError(f"Failed to parse JSON: {e}") from e
```

---

### ❌ DON'T: Skip type hints
```python
def process_data(data):
    return [item for item in data if item['value'] > 10]
```

### ✅ DO: Add comprehensive type hints
```python
from typing import List, Dict, Any

def process_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter data items where value > 10"""
    return [item for item in data if item.get('value', 0) > 10]
```

---

## Communication with QA Agent

After completing each task:

1. **Create a Pull Request** with:
   - Task number and description
   - List of files changed
   - Test coverage report
   - Migration notes (if applicable)

2. **Add PR Description** including:
   ```markdown
   ## Task Completed
   Task 2.1: Validation Refactoring

   ## Changes Made
   - Created validation/result_builder.py with ValidationResult dataclass
   - Created validation/token_calculator.py with TokenCostCalculator
   - Created validation/json_parser.py with RobustJSONParser
   - Refactored validation.py to use new classes
   - Removed 4 duplicate token calculation blocks

   ## Testing
   - Unit tests: 23 tests, 92% coverage
   - Integration tests: 5 tests, all passing
   - Performance: No degradation

   ## Checklist
   - [x] No print statements
   - [x] All functions have type hints
   - [x] All functions have docstrings
   - [x] 85%+ test coverage
   - [x] All tests pass
   - [x] Code formatted with black
   - [x] Mypy passes
   - [x] No TODOs or stubs

   ## QA Notes
   - Backward compatible - old validation results still work
   - New JSON parser handles all edge cases from production logs
   - Token calculation matches existing implementation exactly
   ```

3. **Tag QA Agent** in PR comments

---

## Final Checklist Before Handoff

Before handing off to QA Agent, ensure:

- [ ] All files committed and pushed
- [ ] PR created with complete description
- [ ] All tests passing locally
- [ ] Coverage report generated
- [ ] Documentation updated
- [ ] No print statements (verified with grep)
- [ ] No TODO/FIXME comments (verified with grep)
- [ ] Type checking passes (mypy)
- [ ] Linting passes (flake8)
- [ ] Code formatted (black)
- [ ] Migration guide written (if needed)
- [ ] Ready for production deployment

---

**Remember:** The QA Agent will reject incomplete code. Every function must be fully implemented, tested, and documented. No exceptions.

**Quality Standard:** Production-ready code that can be deployed immediately after QA approval.
