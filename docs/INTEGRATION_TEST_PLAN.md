# Integration Test Plan
# Superannuation Agent Multi-Country System

**Created:** 2024-11-24
**Status:** Draft
**Owner:** QA Team

---

## Executive Summary

This document outlines the integration test strategy for the Superannuation Agent Multi-Country system. The goal is to achieve comprehensive test coverage of all system components working together, including:

- End-to-end query processing workflows
- MLflow experiment tracking and logging
- Multi-country data handling
- Tool orchestration and execution
- Error recovery and resilience
- UI components and progress tracking

**Current Test Coverage:**
- Unit Tests: 90% (GREEN)
- Integration Tests: 0% (RED - CRITICAL GAP)
- **Target:** 80%+ integration test coverage

---

## Test Environments

### 1. Local Development Environment
- **Purpose:** Developer testing, rapid iteration
- **Requirements:**
  - Mock Databricks SQL Warehouse
  - Mock MLflow tracking server
  - Test data fixtures (member profiles, citations)
  - All 4 countries: AU, US, UK, IN

### 2. Staging Environment
- **Purpose:** Pre-production integration testing
- **Requirements:**
  - Real Databricks workspace (non-production)
  - Real MLflow tracking
  - Sanitized production-like data
  - Full Unity Catalog setup

### 3. CI/CD Pipeline
- **Purpose:** Automated testing on every PR
- **Tools:** GitHub Actions / Databricks Workflows
- **Requirements:**
  - Fast test execution (<5 minutes)
  - Parallel test execution
  - Test result reporting

---

## Test Categories

## 1. End-to-End Workflow Tests

### Test Suite: `tests/integration/test_e2e_query_flow.py`

#### Test 1.1: Complete Query Processing - Balance Inquiry
```python
def test_e2e_balance_inquiry_australia():
    """
    Test complete flow from user query to final response.

    Flow:
    1. User asks: "What's my current balance?"
    2. Agent retrieves member profile (AU001)
    3. Classifies query as "balance_inquiry" (3-stage cascade)
    4. Calls get_current_balance tool
    5. Synthesizes response with AUD currency
    6. LLM Judge validates response
    7. Logs to governance table
    8. Logs to MLflow

    Expected:
    - Response contains correct balance: A$125,450.75
    - Classification method: regex (fast path)
    - Judge verdict: PASS
    - MLflow run logged with correct tags
    - Governance table has event record
    """
    pass
```

#### Test 1.2: Multi-Tool Query - Contribution + Projection
```python
def test_e2e_multi_tool_contribution_projection():
    """
    Test query requiring multiple tool calls.

    Query: "If I contribute $500/month, what will my balance be in 10 years?"

    Tools Called:
    1. get_current_balance
    2. get_contribution_limits
    3. calculate_future_balance

    Validation:
    - All 3 tools executed successfully
    - Results combined in synthesis
    - Citation added for contribution limits
    - Total cost tracked correctly
    """
    pass
```

#### Test 1.3: Validation Failure and Retry
```python
def test_e2e_validation_failure_retry():
    """
    Test system handling of failed LLM Judge validation.

    Scenario:
    - First response fails validation (missing disclaimer)
    - Agent retries with improved prompt
    - Second attempt passes

    Expected:
    - validation_attempts = 2
    - Final response has disclaimer
    - Both attempts logged to MLflow
    - Total cost = cost_attempt1 + cost_attempt2
    """
    pass
```

---

## 2. Multi-Country Workflow Tests

### Test Suite: `tests/integration/test_multi_country.py`

#### Test 2.1: All Countries - Balance Inquiry
```python
@pytest.mark.parametrize("country,member_id,currency,expected_balance", [
    ("AU", "AU001", "A$", 125450.75),
    ("US", "US001", "$", 87230.50),
    ("UK", "UK001", "£", 95680.25),
    ("IN", "IN001", "₹", 1250000.00),
])
def test_balance_inquiry_all_countries(country, member_id, currency, expected_balance):
    """
    Test balance inquiry works for all 4 countries.

    Validation:
    - Correct currency symbol in response
    - Correct authority cited (APRA/DOL/FCA/PFRDA)
    - Country-specific regulations referenced
    """
    pass
```

#### Test 2.2: Country-Specific Tool Routing
```python
def test_country_specific_tool_routing():
    """
    Test that tools route to correct country implementations.

    Example: get_contribution_limits
    - AU: concessional_cap=30000, non_concessional_cap=120000
    - US: ira_limit=7000, 401k_limit=23000
    - UK: pension_allowance=60000
    - IN: epf_limit=250000
    """
    pass
```

#### Test 2.3: Multi-Country Data Consistency
```python
def test_multi_country_data_consistency():
    """
    Verify governance table tracks all countries correctly.

    Process:
    1. Run queries for all 4 countries
    2. Query governance table
    3. Validate country field populated correctly
    4. Validate cost aggregation per country
    """
    pass
```

---

## 3. MLflow Integration Tests

### Test Suite: `tests/integration/test_mlflow_integration.py`

#### Test 3.1: Experiment Creation and Logging
```python
def test_mlflow_experiment_lifecycle():
    """
    Test MLflow experiment and run creation.

    Steps:
    1. Create/get experiment: "superannuation-agent-queries"
    2. Start run with tags (country, member_id, query_type)
    3. Log parameters (model, temperature, max_tokens)
    4. Log metrics (cost, latency, validation_attempts)
    5. End run
    6. Verify run appears in MLflow UI
    """
    pass
```

#### Test 3.2: Prompt Template Versioning
```python
def test_mlflow_prompt_template_versioning():
    """
    Test prompt template retrieval from MLflow Model Registry.

    Validation:
    - System prompt loaded from MLflow (if enabled)
    - Version tracked in run tags
    - Fallback to local prompts if MLflow disabled
    """
    pass
```

#### Test 3.3: Cost Tracking Accuracy
```python
def test_mlflow_cost_tracking():
    """
    Verify cost calculation accuracy across models.

    Test Cases:
    - Claude Sonnet 4: $3/1M input, $15/1M output
    - Claude Opus 4: $15/1M input, $75/1M output
    - Multiple LLM calls (ReAct + Synthesis + Judge)

    Validation:
    - Total cost = sum(all LLM calls)
    - Cost logged to MLflow metrics
    - Cost logged to governance table
    """
    pass
```

---

## 4. Tool Orchestration Tests

### Test Suite: `tests/integration/test_tool_orchestration.py`

#### Test 4.1: Tool Discovery and Registration
```python
def test_tool_discovery():
    """
    Verify all tools properly registered and discoverable.

    Expected Tools:
    - get_member_profile
    - get_current_balance
    - get_recent_transactions
    - get_contribution_limits
    - calculate_future_balance
    - get_preservation_age
    - get_early_access_conditions

    Validation:
    - Tool schema valid (name, description, parameters)
    - All countries have implementations
    """
    pass
```

#### Test 4.2: Tool Execution with SQL Warehouse
```python
def test_tool_sql_execution():
    """
    Test tool execution against real SQL Warehouse.

    Tool: get_recent_transactions(member_id="AU001", limit=10)

    Validation:
    - SQL statement submitted successfully
    - Results returned as DataFrame
    - Results formatted correctly for LLM context
    """
    pass
```

#### Test 4.3: Tool Error Handling
```python
def test_tool_error_handling():
    """
    Test graceful handling of tool errors.

    Scenarios:
    1. Member not found (invalid member_id)
    2. SQL Warehouse timeout
    3. Invalid tool parameters

    Expected:
    - Errors captured and logged
    - Agent continues with error message
    - No system crash
    """
    pass
```

---

## 5. Error Recovery Tests

### Test Suite: `tests/integration/test_error_recovery.py`

#### Test 5.1: Network Timeout Recovery
```python
def test_network_timeout_recovery():
    """
    Test system behavior during network timeouts.

    Inject:
    - SQL Warehouse connection timeout
    - MLflow logging timeout

    Expected:
    - Graceful degradation
    - User receives partial response
    - Error logged to stderr
    """
    pass
```

#### Test 5.2: Invalid LLM Response Handling
```python
def test_invalid_llm_response():
    """
    Test handling of malformed LLM responses.

    Scenarios:
    1. LLM returns invalid JSON for tool call
    2. LLM hallucinates non-existent tool
    3. LLM omits required parameters

    Expected:
    - Parse errors caught
    - Agent retries with corrected prompt
    - Max retry limit enforced (3 attempts)
    """
    pass
```

#### Test 5.3: Partial Tool Failure
```python
def test_partial_tool_failure():
    """
    Test handling when some tools succeed, others fail.

    Query: "What's my balance and recent transactions?"

    Inject:
    - get_current_balance: SUCCESS
    - get_recent_transactions: TIMEOUT

    Expected:
    - Response includes balance (partial success)
    - Error message about transactions
    - User informed of partial data
    """
    pass
```

---

## 6. Classification System Tests

### Test Suite: `tests/integration/test_classification.py`

#### Test 6.1: 3-Stage Cascade Performance
```python
def test_classification_cascade():
    """
    Test 3-stage classification cascade (Regex → Embedding → LLM).

    Queries:
    - "What's my balance?" → Regex (fast)
    - "How much do I have saved?" → Embedding (medium)
    - "Should I consolidate multiple super accounts?" → LLM (slow)

    Validation:
    - classification_method logged correctly
    - Latency: regex < 50ms, embedding < 200ms, llm < 2000ms
    - Accuracy: 95%+ correct classification
    """
    pass
```

#### Test 6.2: Classification Confidence Tracking
```python
def test_classification_confidence():
    """
    Track classification confidence across methods.

    Validation:
    - Regex: confidence = 1.0 (exact match)
    - Embedding: confidence from cosine similarity (0.7-1.0)
    - LLM: confidence from JSON response (0.5-1.0)

    Low confidence (< 0.6):
    - Escalate to LLM classifier
    - Log warning in governance table
    """
    pass
```

---

## 7. UI and Progress Tracking Tests

### Test Suite: `tests/integration/test_ui_integration.py`

#### Test 7.1: Streamlit App Launch
```python
def test_streamlit_app_launch():
    """
    Test Streamlit app launches without errors.

    Validation:
    - App starts on port 8501
    - All tabs render (Query, Monitoring, Admin)
    - Country selector works
    - Session state initialized
    """
    pass
```

#### Test 7.2: Real-Time Progress Tracking
```python
def test_progress_tracking_updates():
    """
    Test 8-phase progress tracker updates in real-time.

    Phases:
    1. Data Retrieval
    2. Privacy Anonymization
    3. Query Classification
    4. Tool Planning
    5. Tool Execution
    6. Response Synthesis
    7. Quality Validation
    8. Audit Logging

    Validation:
    - All phases transition: pending → running → completed
    - Duration tracked for each phase
    - Progress bar updates (0% → 100%)
    """
    pass
```

---

## 8. Performance and Load Tests

### Test Suite: `tests/integration/test_performance.py`

#### Test 8.1: Concurrent Query Handling
```python
@pytest.mark.slow
def test_concurrent_queries():
    """
    Test system under concurrent load.

    Scenario:
    - 10 concurrent users
    - Each submits 5 queries
    - Total: 50 queries

    Validation:
    - All queries complete successfully
    - No race conditions in governance logging
    - Average latency < 5 seconds
    """
    pass
```

#### Test 8.2: Large Result Set Handling
```python
def test_large_result_set():
    """
    Test handling of large SQL query results.

    Query: get_recent_transactions(limit=1000)

    Validation:
    - Results truncated appropriately for LLM context
    - No memory errors
    - Response time reasonable (< 10 seconds)
    """
    pass
```

---

## Test Data Setup

### Fixtures Required

```python
# tests/integration/fixtures.py

@pytest.fixture(scope="session")
def test_members():
    """Create test member profiles for all countries."""
    return {
        "AU001": {...},  # Australian test member
        "US001": {...},  # US test member
        "UK001": {...},  # UK test member
        "IN001": {...},  # Indian test member
    }

@pytest.fixture(scope="session")
def mock_sql_warehouse():
    """Mock Databricks SQL Warehouse for local testing."""
    pass

@pytest.fixture(scope="function")
def clean_governance_table():
    """Clean governance table before each test."""
    pass

@pytest.fixture(scope="function")
def mlflow_test_experiment():
    """Create isolated MLflow experiment for testing."""
    pass
```

---

## Test Execution Strategy

### Phase 1: Core Functionality (Week 1)
- [ ] End-to-End Workflow Tests (Test 1.1 - 1.3)
- [ ] Multi-Country Tests (Test 2.1 - 2.2)
- [ ] Tool Orchestration (Test 4.1 - 4.2)

**Goal:** 40% integration test coverage

### Phase 2: Robustness (Week 2)
- [ ] Error Recovery Tests (Test 5.1 - 5.3)
- [ ] Classification Tests (Test 6.1 - 6.2)
- [ ] MLflow Integration (Test 3.1 - 3.3)

**Goal:** 70% integration test coverage

### Phase 3: Polish (Week 3)
- [ ] UI Integration Tests (Test 7.1 - 7.2)
- [ ] Performance Tests (Test 8.1 - 8.2)
- [ ] Multi-Country Data Consistency (Test 2.3)

**Goal:** 85%+ integration test coverage

---

## Success Criteria

### Must-Have (P0)
- ✅ All end-to-end workflow tests pass
- ✅ All 4 countries tested and working
- ✅ MLflow logging validated
- ✅ Error recovery tests pass

### Should-Have (P1)
- ✅ Classification cascade validated
- ✅ UI integration tests pass
- ✅ Tool error handling verified

### Nice-to-Have (P2)
- ⚪ Performance benchmarks established
- ⚪ Load testing completed
- ⚪ Chaos engineering tests

---

## Test Reporting

### Metrics to Track
1. **Coverage:**
   - Integration test coverage %
   - Lines covered by integration tests

2. **Reliability:**
   - Test pass rate (target: 95%+)
   - Flaky test count (target: 0)

3. **Performance:**
   - Test suite execution time
   - Average query latency

4. **Quality:**
   - Bugs found in integration testing
   - Production incidents prevented

### Reporting Tools
- **Coverage:** `pytest-cov`
- **Results:** JUnit XML → CI/CD dashboard
- **Metrics:** MLflow tracking

---

## Next Steps

1. **Immediate (This Week):**
   - [ ] Set up test environment with mock SQL Warehouse
   - [ ] Create test member fixtures for all countries
   - [ ] Implement Test 1.1 (E2E balance inquiry)

2. **Short-Term (Next 2 Weeks):**
   - [ ] Implement remaining Phase 1 tests
   - [ ] Set up CI/CD pipeline integration
   - [ ] Document test execution procedures

3. **Long-Term (Month 1-2):**
   - [ ] Complete all test suites
   - [ ] Establish performance baselines
   - [ ] Create integration test maintenance runbook

---

## References

- Unit Test Suite: `/tests/unit/`
- Test Fixtures: `/tests/fixtures/`
- CI/CD Config: `.github/workflows/test.yml`
- Test Data: `/tests/data/`

---

**Document Version:** 1.0
**Last Updated:** 2024-11-24
**Review Date:** 2024-12-01
