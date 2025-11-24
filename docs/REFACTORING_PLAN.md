# Comprehensive Refactoring Plan
## Superannuation Agent Multi-Country Codebase

**Status:** Planning Phase
**Start Date:** 2024-11-24
**Target Completion:** 4 weeks
**Approach:** Maker-Checker Pattern (Developer Agent + QA Agent)

---

## Executive Summary

The codebase shows good separation of concerns but suffers from significant DRY violations, inconsistent logging, and repeated patterns across agent logic, validation, UI components, and prompts. This plan provides specific, actionable refactoring steps with a maker-checker approach to ensure quality.

### Key Findings

- **60+ print statements** across the codebase requiring structured logging
- **3 duplicate `printf()` functions** in different files
- **Massive code duplication** in tool execution (4 country implementations with 90% identical code)
- **Agent loop orchestration** spanning 400+ lines with repeated patterns
- **UI component styling** duplicated across multiple functions
- **Validation logic** with 4 repeated token/cost calculation blocks
- **Hard-coded prompts** that should be externalized to templates

### Expected Outcomes

1. **Code Reduction**: 30-40% reduction in total lines of code
2. **Maintainability**: Single source of truth for each concept
3. **Testability**: Smaller, focused classes easier to test
4. **Extensibility**: New countries/tools/features easier to add
5. **Debuggability**: Structured logging makes issues easier to trace
6. **Performance**: No degradation (configuration loading cached)

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal:** Set up infrastructure for refactoring

#### Task 1.1: Centralized Logging System
**Files to Create:**
- `shared/logging_config.py` - Main logging configuration
- `shared/logger.py` - Backward compatible wrapper

**Implementation:**
```python
# shared/logging_config.py
import logging
import sys
from typing import Optional

# Custom log level for phase tracking
PHASE = 25  # Between INFO and WARNING
logging.addLevelName(PHASE, "PHASE")

class ColoredFormatter(logging.Formatter):
    """Colored console formatter with emoji support"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'PHASE': '\033[35m',     # Magenta
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'RESET': '\033[0m'
    }

    EMOJI = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'PHASE': '📍',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }

    def format(self, record):
        levelname = record.levelname
        emoji = self.EMOJI.get(levelname, '')
        color = self.COLORS.get(levelname, self.COLORS['RESET'])

        record.emoji = emoji
        record.color_start = color
        record.color_end = self.COLORS['RESET']

        return super().format(record)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Configure logging for the application"""
    logger = logging.getLogger("superannuation_agent")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(
        fmt='[%(asctime)s] [%(levelname)s] %(emoji)s %(color_start)s%(name)s:%(lineno)d%(color_end)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler without colors (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(module_name: str) -> logging.Logger:
    """Get logger for specific module"""
    return logging.getLogger(f"superannuation_agent.{module_name}")
```

**Testing Requirements:**
- Test log output formatting
- Test file logging
- Test log levels
- Test module-specific loggers

**Success Criteria:**
- All log levels work correctly
- Console output is colored and formatted
- File output is plain text
- No errors when importing

---

#### Task 1.2: Progress Tracker Context Manager
**Files to Create:**
- `shared/progress_tracker.py`

**Implementation:**
```python
from contextlib import contextmanager
from typing import Optional
import time

@contextmanager
def track_phase(phase_name: str, description: str = ""):
    """Context manager for phase tracking with error handling"""
    try:
        from utils.progress import mark_phase_running, mark_phase_complete, mark_phase_error
    except ImportError:
        # Fallback if progress module not available
        mark_phase_running = lambda x: None
        mark_phase_complete = lambda x: None
        mark_phase_error = lambda x, y: None

    start_time = time.time()
    try:
        mark_phase_running(phase_name)
        yield
        duration = time.time() - start_time
        mark_phase_complete(phase_name)
    except Exception as e:
        duration = time.time() - start_time
        mark_phase_error(phase_name, str(e))
        raise

@contextmanager
def track_phase_with_timing(phase_name: str, phase_num: int, logger):
    """Enhanced context manager with logging and timing"""
    from utils.progress import mark_phase_running, mark_phase_complete, mark_phase_error

    start = time.time()
    logger.log(25, f"PHASE {phase_num}: {phase_name}")  # PHASE log level

    try:
        mark_phase_running(f'phase_{phase_num}_{phase_name.lower().replace(" ", "_")}')
        yield
        duration = time.time() - start
        logger.info(f"Phase {phase_num} completed in {duration:.2f}s")
        mark_phase_complete(f'phase_{phase_num}_{phase_name.lower().replace(" ", "_")}')
    except Exception as e:
        duration = time.time() - start
        mark_phase_error(f'phase_{phase_num}_{phase_name.lower().replace(" ", "_")}', str(e))
        logger.error(f"Phase {phase_num} failed after {duration:.2f}s: {e}")
        raise
```

**Testing Requirements:**
- Test successful phase completion
- Test phase error handling
- Test timing accuracy
- Test with/without progress module

**Success Criteria:**
- Context manager works correctly
- Timing is accurate
- Errors are properly caught and re-raised
- Progress tracking calls are made

---

#### Task 1.3: Configuration Management
**Files to Create:**
- `config/app_config.yaml`
- `config/countries.yaml`
- `config/config_loader.py`

**Implementation:**
```python
# config/config_loader.py
import os
import yaml
from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path

@dataclass
class LLMConfig:
    endpoint: str
    temperature: float
    max_tokens: int
    pricing: Dict[str, float]

@dataclass
class AppConfig:
    """Main application configuration"""
    main_llm: LLMConfig
    judge_llm: LLMConfig
    classifier_llm: LLMConfig
    sql_warehouse_id: str
    unity_catalog: str
    unity_schema: str
    mlflow_experiment_path: str
    mlflow_eval_path: str
    max_validation_attempts: int
    judge_confidence_threshold: float

    @classmethod
    def from_yaml(cls, config_file: str = "config/app_config.yaml") -> "AppConfig":
        """Load configuration from YAML file with environment variable overrides"""
        config_path = Path(__file__).parent / config_file
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        config_data = cls._apply_env_overrides(config_data)

        return cls(
            main_llm=LLMConfig(**config_data['llm']['main']),
            judge_llm=LLMConfig(**config_data['llm']['judge']),
            classifier_llm=LLMConfig(**config_data['llm']['classifier']),
            sql_warehouse_id=config_data['database']['sql_warehouse_id'],
            unity_catalog=config_data['database']['unity_catalog'],
            unity_schema=config_data['database']['unity_schema'],
            mlflow_experiment_path=config_data['mlflow']['experiment_path'],
            mlflow_eval_path=config_data['mlflow']['eval_path'],
            max_validation_attempts=config_data['validation']['max_attempts'],
            judge_confidence_threshold=config_data['validation']['confidence_threshold']
        )

    @staticmethod
    def _apply_env_overrides(config: Dict) -> Dict:
        """Override config values with environment variables"""
        env_mapping = {
            'SUPER_SQL_WAREHOUSE_ID': ['database', 'sql_warehouse_id'],
            'SUPER_LLM_MAIN_ENDPOINT': ['llm', 'main', 'endpoint'],
            'SUPER_LLM_JUDGE_ENDPOINT': ['llm', 'judge', 'endpoint'],
            'SUPER_LLM_CLASSIFIER_ENDPOINT': ['llm', 'classifier', 'endpoint'],
        }

        for env_var, keys in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                d = config
                for key in keys[:-1]:
                    d = d[key]
                d[keys[-1]] = value

        return config

# Global config instance
_config: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """Get application configuration (singleton)"""
    global _config
    if _config is None:
        _config = AppConfig.from_yaml()
    return _config
```

**YAML Files:**
```yaml
# config/app_config.yaml
llm:
  main:
    endpoint: "databricks-claude-opus-4-1"
    temperature: 0.2
    max_tokens: 750
    pricing:
      input_tokens: 15.00
      output_tokens: 75.00
  judge:
    endpoint: "databricks-claude-sonnet-4"
    temperature: 0.1
    max_tokens: 300
    pricing:
      input_tokens: 3.00
      output_tokens: 15.00
  classifier:
    endpoint: "databricks-gpt-oss-120b"
    pricing:
      input_tokens: 0.15
      output_tokens: 0.15

database:
  sql_warehouse_id: "4b9b953939869799"
  unity_catalog: "super_advisory_demo"
  unity_schema: "member_data"

mlflow:
  experiment_path: "/Users/pravin.varma@databricks.com/prodretirement-advisory"
  eval_path: "/Users/pravin.varma@databricks.com/retirement-eval"

validation:
  max_attempts: 2
  confidence_threshold: 0.70
```

**Testing Requirements:**
- Test YAML loading
- Test environment variable overrides
- Test singleton pattern
- Test config validation

**Success Criteria:**
- Configuration loads correctly from YAML
- Environment variables override defaults
- Config is accessible throughout app
- Invalid config raises errors

---

### Phase 2: Core Refactoring (Week 2-3)

#### Task 2.1: Validation Refactoring

**Files to Create:**
- `validation/result_builder.py`
- `validation/token_calculator.py`
- `validation/json_parser.py`

**Files to Modify:**
- `validation.py` - Use new classes

**Implementation:** See detailed implementation in section below

**Testing Requirements:**
- Test ValidationResult creation
- Test token calculation with various responses
- Test JSON parsing with malformed input
- Test backward compatibility

**Success Criteria:**
- All validation tests pass
- Token calculation is accurate
- JSON parsing handles edge cases
- No print statements remain

---

#### Task 2.2: Unified Tool Executor

**Files to Create:**
- `tools/tool_config.yaml`
- `tools/tool_executor.py`
- `tools/tool_config_loader.py`

**Files to Modify:**
- `tools.py` - Use UnifiedToolExecutor

**Testing Requirements:**
- Test tool execution for all countries
- Test error handling
- Test parameter mapping
- Test SQL query generation

**Success Criteria:**
- All countries use same executor
- 75% code reduction in tools.py
- All existing tool tests pass
- Configuration is external

---

#### Task 2.3: Prompt Template System

**Files to Create:**
- `prompts/templates/` directory
- `prompts/templates/system_prompt.jinja2`
- `prompts/templates/validation_prompt.jinja2`
- `prompts/templates/off_topic_decline.jinja2`
- `prompts/prompt_loader.py`
- `prompts/archetypes.yaml`

**Files to Modify:**
- `prompts_registry.py` - Use template loader

**Testing Requirements:**
- Test template loading
- Test template rendering
- Test country-specific prompts
- Test archetype loading

**Success Criteria:**
- All prompts load from templates
- No hard-coded prompt strings
- Country-specific rendering works
- All prompt tests pass

---

#### Task 2.4: Agent Response Builder

**Files to Create:**
- `agents/response_builder.py`
- `agents/context_formatter.py`

**Files to Modify:**
- `agent.py` - Use ResponseBuilder

**Testing Requirements:**
- Test context building
- Test tool result formatting
- Test template rendering
- Test token tracking

**Success Criteria:**
- generate_response() is simplified
- Formatting is consistent
- Templates are reusable
- All agent tests pass

---

### Phase 3: UI & Orchestration (Week 3-4)

#### Task 3.1: UI Component Refactoring

**Files to Create:**
- `ui/theme_config.py`
- `ui/html_builder.py`
- `ui/tab_base.py`

**Files to Modify:**
- `ui_components.py` - Use new builders
- `ui_monitoring_tabs.py` - Use BaseMonitoringTab

**Testing Requirements:**
- Test theme configuration
- Test HTML generation
- Test tab rendering
- Test error handling

**Success Criteria:**
- No duplicate styling code
- All tabs use base class
- HTML is template-driven
- All UI tests pass

---

#### Task 3.2: Agent Orchestrator

**Files to Create:**
- `agents/orchestrator.py`

**Files to Modify:**
- `agent_processor.py` - Use AgentOrchestrator

**Testing Requirements:**
- Test phase execution
- Test timing accuracy
- Test error handling
- Test MLflow integration

**Success Criteria:**
- agent_query() under 150 lines
- Phase tracking is automatic
- Error handling is centralized
- All orchestration tests pass

---

### Phase 4: Polish & Documentation (Week 4)

#### Task 4.1: Migration & Cleanup

**Tasks:**
1. Remove all print() statements
2. Remove duplicate printf() functions
3. Add type hints throughout
4. Add comprehensive docstrings
5. Update requirements.txt

**Testing Requirements:**
- Full test suite passes
- No print statements found
- Type checking passes (mypy)
- Documentation is complete

**Success Criteria:**
- 0 print statements
- 100% type hints on public APIs
- All functions have docstrings
- Mypy passes with no errors

---

#### Task 4.2: Integration Testing

**Tasks:**
1. End-to-end testing all flows
2. Performance benchmarking
3. Load testing
4. Error scenario testing

**Testing Requirements:**
- All integration tests pass
- Performance is equal or better
- No memory leaks
- Error handling is robust

**Success Criteria:**
- All integration tests green
- Performance within 5% of baseline
- Memory usage stable
- 95%+ test coverage

---

## Detailed Implementation Specifications

### Validation Refactoring (Task 2.1)

**validation/result_builder.py:**
```python
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional

@dataclass
class ValidationViolation:
    """Represents a single validation violation"""
    code: str
    severity: str
    detail: str
    evidence: str

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ValidationResult:
    """Structured validation result"""
    passed: bool
    confidence: float
    violations: List[ValidationViolation]
    reasoning: str
    validator_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    model: str = "unknown"
    duration: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for backwards compatibility"""
        result = asdict(self)
        result['violations'] = [v.to_dict() for v in self.violations]
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "ValidationResult":
        """Create from dictionary"""
        violations = [ValidationViolation(**v) for v in data.get('violations', [])]
        data_copy = data.copy()
        data_copy['violations'] = violations
        return cls(**data_copy)
```

**validation/token_calculator.py:**
```python
from typing import Dict, Any
from shared.logging_config import get_logger

logger = get_logger(__name__)

def calculate_llm_cost(input_tokens: int, output_tokens: int, model_type: str) -> float:
    """Calculate LLM cost based on token usage and model type"""
    # This should be moved to config/app_config.yaml eventually
    pricing = {
        "databricks-claude-opus-4-1": {"input": 15.00, "output": 75.00},
        "databricks-claude-sonnet-4": {"input": 3.00, "output": 15.00},
        "databricks-gpt-oss-120b": {"input": 0.15, "output": 0.15},
    }

    model_pricing = pricing.get(model_type, {"input": 0, "output": 0})
    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

    return input_cost + output_cost

class TokenCostCalculator:
    """Calculate tokens and cost from API responses"""

    @staticmethod
    def calculate_from_response(
        response: Any,
        prompt_length: int,
        model_type: str
    ) -> Dict:
        """Extract tokens and calculate cost from API response"""
        input_tokens = 0
        output_tokens = 0

        # Try to extract from response
        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0)
            output_tokens = getattr(response.usage, 'completion_tokens', 0)
            logger.debug(f"Extracted tokens from response: {input_tokens} input, {output_tokens} output")
        else:
            # Fallback estimation
            input_tokens = prompt_length // 4
            output_tokens = 100
            logger.debug(f"Estimated tokens (no usage data): {input_tokens} input, {output_tokens} output")

        cost = calculate_llm_cost(input_tokens, output_tokens, model_type)

        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'cost': cost,
            'model': model_type
        }
```

**validation/json_parser.py:**
```python
import json
import re
from typing import Optional, Dict
from shared.logging_config import get_logger

logger = get_logger(__name__)

class RobustJSONParser:
    """Parse JSON from LLM outputs with multiple fallback strategies"""

    @staticmethod
    def parse_validation_response(judge_output: str) -> Optional[Dict]:
        """Try multiple strategies to parse JSON from LLM output"""
        strategies = [
            ("Direct JSON", RobustJSONParser._direct_parse),
            ("Fix Malformed", RobustJSONParser._fix_malformed_json),
            ("Extract Markdown", RobustJSONParser._extract_from_markdown),
            ("Extract Braces", RobustJSONParser._extract_between_braces)
        ]

        for strategy_name, strategy_func in strategies:
            try:
                logger.debug(f"Trying parsing strategy: {strategy_name}")
                result = strategy_func(judge_output)

                if result and "passed" in result and "confidence" in result:
                    logger.debug(f"Successfully parsed with strategy: {strategy_name}")
                    return result
            except Exception as e:
                logger.debug(f"Strategy {strategy_name} failed: {e}")
                continue

        logger.warning("All JSON parsing strategies failed")
        return None

    @staticmethod
    def _direct_parse(text: str) -> Dict:
        """Strategy 1: Direct JSON parsing"""
        return json.loads(text)

    @staticmethod
    def _fix_malformed_json(text: str) -> Dict:
        """Strategy 2: Fix common JSON issues"""
        # Remove trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        # Fix unquoted keys
        text = re.sub(r'(\w+):', r'"\1":', text)
        return json.loads(text)

    @staticmethod
    def _extract_from_markdown(text: str) -> Dict:
        """Strategy 3: Extract JSON from markdown code blocks"""
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError("No markdown code block found")

    @staticmethod
    def _extract_between_braces(text: str) -> Dict:
        """Strategy 4: Extract content between first { and last }"""
        start = text.find('{')
        end = text.rfind('}')

        if start != -1 and end != -1:
            json_str = text[start:end+1]
            return json.loads(json_str)

        raise ValueError("No JSON object found")
```

---

## Testing Strategy

### Unit Tests

**Location:** `tests/unit/`

**Required Test Files:**
- `test_logging_config.py`
- `test_progress_tracker.py`
- `test_config_loader.py`
- `test_validation_result.py`
- `test_token_calculator.py`
- `test_json_parser.py`
- `test_tool_executor.py`
- `test_prompt_loader.py`
- `test_response_builder.py`
- `test_orchestrator.py`
- `test_ui_builder.py`

**Coverage Target:** 85%+

### Integration Tests

**Location:** `tests/integration/`

**Required Test Files:**
- `test_agent_end_to_end.py`
- `test_validation_flow.py`
- `test_tool_execution.py`
- `test_ui_rendering.py`

**Coverage Target:** 70%+

### Performance Tests

**Location:** `tests/performance/`

**Required Test Files:**
- `test_response_time.py`
- `test_memory_usage.py`
- `test_concurrent_requests.py`

**Baseline:** Current performance

---

## Risk Mitigation

### 1. Backward Compatibility

**Strategy:** Keep legacy interfaces during migration

**Implementation:**
- Legacy `printf()` wrapper during transition
- Dual configuration support (old + new)
- Feature flags for new implementations

### 2. Incremental Rollout

**Strategy:** Refactor one module at a time with tests

**Implementation:**
- Complete Phase 1 before Phase 2
- Ensure all tests pass after each task
- Code review after each major change

### 3. Feature Flags

**Strategy:** Switch between old/new implementations

**Implementation:**
```python
# config/app_config.yaml
features:
  use_new_validation: false
  use_unified_tools: false
  use_agent_orchestrator: false
```

### 4. Rollback Plan

**Strategy:** Git branches and tags for each phase

**Implementation:**
- Tag before each phase starts
- Separate branch for each major refactor
- Document rollback procedures

---

## Success Metrics

### Code Quality
- [ ] 0 print() statements in codebase
- [ ] 0 duplicate functions (printf, etc.)
- [ ] 85%+ test coverage
- [ ] 100% type hints on public APIs
- [ ] All docstrings present
- [ ] Mypy passes with no errors

### Code Reduction
- [ ] 30%+ reduction in total LOC
- [ ] tools.py: 75%+ reduction
- [ ] agent_processor.py: 60%+ reduction
- [ ] ui_components.py: 40%+ reduction
- [ ] validation.py: 50%+ reduction

### Performance
- [ ] Response time within 5% of baseline
- [ ] Memory usage stable or improved
- [ ] No new memory leaks
- [ ] All integration tests pass

### Maintainability
- [ ] Single source of truth for each concept
- [ ] Configuration externalized
- [ ] Prompts in templates
- [ ] Tool definitions in YAML
- [ ] Country configs in YAML

---

## Appendix A: File Structure After Refactoring

```
superannuation-agent-multi-country/
├── config/
│   ├── __init__.py
│   ├── app_config.yaml
│   ├── countries.yaml
│   └── config_loader.py
├── shared/
│   ├── __init__.py
│   ├── logging_config.py
│   ├── logger.py
│   └── progress_tracker.py
├── validation/
│   ├── __init__.py
│   ├── result_builder.py
│   ├── token_calculator.py
│   └── json_parser.py
├── tools/
│   ├── __init__.py
│   ├── tool_config.yaml
│   ├── tool_executor.py
│   └── tool_config_loader.py
├── prompts/
│   ├── __init__.py
│   ├── templates/
│   │   ├── system_prompt.jinja2
│   │   ├── validation_prompt.jinja2
│   │   └── off_topic_decline.jinja2
│   ├── archetypes.yaml
│   └── prompt_loader.py
├── agents/
│   ├── __init__.py
│   ├── response_builder.py
│   ├── context_formatter.py
│   └── orchestrator.py
├── ui/
│   ├── __init__.py
│   ├── theme_config.py
│   ├── html_builder.py
│   └── tab_base.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── performance/
├── agent.py (refactored)
├── agent_processor.py (refactored)
├── validation.py (refactored)
├── tools.py (refactored)
├── prompts_registry.py (refactored)
├── ui_components.py (refactored)
├── ui_monitoring_tabs.py (refactored)
├── app.py
├── requirements.txt
├── REFACTORING_PLAN.md
├── DEVELOPER.md
└── QA.md
```

---

## Appendix B: Migration Checklist

### Pre-Refactoring
- [ ] Create feature branch
- [ ] Document current performance baseline
- [ ] Run full test suite and record results
- [ ] Create backup of current implementation
- [ ] Review and approve refactoring plan

### Phase 1
- [ ] Create directory structure
- [ ] Implement logging system
- [ ] Implement progress tracker
- [ ] Implement configuration loader
- [ ] Write unit tests
- [ ] Update documentation

### Phase 2
- [ ] Refactor validation logic
- [ ] Implement unified tool executor
- [ ] Create prompt template system
- [ ] Create response builder
- [ ] Write unit tests
- [ ] Update documentation

### Phase 3
- [ ] Refactor UI components
- [ ] Create agent orchestrator
- [ ] Write unit tests
- [ ] Update documentation

### Phase 4
- [ ] Remove all print statements
- [ ] Add type hints
- [ ] Add docstrings
- [ ] Run full test suite
- [ ] Performance testing
- [ ] Create migration guide
- [ ] Update README

### Post-Refactoring
- [ ] Code review
- [ ] QA testing
- [ ] Performance validation
- [ ] Documentation review
- [ ] Merge to main
- [ ] Deploy
- [ ] Monitor production

---

**Document Version:** 1.0
**Last Updated:** 2024-11-24
**Next Review:** End of Phase 1
