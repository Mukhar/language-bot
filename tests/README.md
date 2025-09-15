# Healthcare Communication Practice Bot - Tests

This directory contains comprehensive test suites for the healthcare communication practice bot backend.

## Test Structure

### Test Files

- **`test_main.py`** - Integration tests for the FastAPI application
  - Health endpoint testing
  - Application startup/shutdown
  - API route integration
  - Database connectivity

- **`test_models.py`** - Database model tests
  - Model creation and validation
  - Relationship testing
  - Database constraints
  - Data integrity checks

- **`test_scenarios.py`** - Scenario management tests
  - Scenario generation via LM Studio
  - CRUD operations
  - Category and difficulty filtering
  - Validation and error handling

- **`test_responses.py`** - Response handling tests
  - Response submission and validation
  - Text length requirements
  - User association
  - Scenario relationship testing

- **`test_evaluations.py`** - Evaluation system tests
  - LM Studio evaluation integration
  - Score calculation and feedback
  - Improvement suggestions
  - Fallback mechanisms

- **`test_lm_studio.py`** - LM Studio service tests
  - API integration mocking
  - Fallback scenario testing
  - Error handling
  - JSON response parsing

### Configuration

- **`conftest.py`** - Pytest configuration and fixtures
  - Test database setup
  - Cleanup utilities
  - Custom markers
  - Shared fixtures

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Files

```bash
# Run integration tests
pytest tests/test_main.py

# Run model tests
pytest tests/test_models.py

# Run API endpoint tests
pytest tests/test_scenarios.py tests/test_responses.py tests/test_evaluations.py
```

### Run with Coverage

```bash
pip install pytest-cov
pytest tests/ --cov=app --cov-report=html
```

### Run with Markers

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m integration
```

## Test Database

Tests use SQLite databases that are automatically created and cleaned up:

- Separate test databases for each test module
- Automatic schema creation and teardown
- Isolated test environments
- No impact on development database

## Mocking Strategy

### LM Studio Service
- HTTP requests are mocked using `unittest.mock`
- Fallback responses tested for error conditions
- JSON parsing validation
- Timeout and connection error simulation

### Database Operations
- In-memory SQLite for fast execution
- Transaction rollback for test isolation
- Fixture-based test data creation
- Automatic cleanup between tests

## Test Coverage

Current test coverage includes:

- ✅ API endpoint functionality
- ✅ Database models and relationships
- ✅ LM Studio service integration
- ✅ Request/response validation
- ✅ Error handling and edge cases
- ✅ Authentication preparation (basic structure)
- ⏳ User progress tracking (partial)
- ⏳ Advanced filtering and search
- ⏳ Performance and load testing

## Writing New Tests

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test functions: `test_<functionality>_<condition>`
- Test classes: `Test<ClassName>`

### Example Test Structure

```python
def test_function_success_case():
    """Test successful operation"""
    # Arrange
    test_data = create_test_data()
    
    # Act
    result = function_under_test(test_data)
    
    # Assert
    assert result.status == "success"
    assert result.data is not None

def test_function_error_case():
    """Test error handling"""
    # Arrange
    invalid_data = create_invalid_data()
    
    # Act & Assert
    with pytest.raises(ValueError):
        function_under_test(invalid_data)
```

### Async Test Example

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality"""
    result = await async_function()
    assert result is not None
```

## Continuous Integration

Tests are designed to run in CI/CD environments:

- No external dependencies required
- Fast execution (< 30 seconds)
- Deterministic results
- Clear error reporting
- Automatic cleanup

## Debugging Tests

### Verbose Output
```bash
pytest -v tests/
```

### Stop on First Failure
```bash
pytest -x tests/
```

### Debug Mode
```bash
pytest --pdb tests/test_specific.py::test_function
```

### Print Statements
```bash
pytest -s tests/  # Don't capture stdout
```

## Performance Considerations

- Tests use SQLite for speed
- Mocked external services
- Minimal test data creation
- Parallel execution safe
- Resource cleanup automated

## Future Enhancements

### Planned Test Additions
1. **Load Testing** - Performance under concurrent users
2. **Security Testing** - Authentication and authorization
3. **Integration Testing** - Full workflow scenarios
4. **API Documentation Testing** - OpenAPI spec validation
5. **Migration Testing** - Database schema changes

### Test Infrastructure Improvements
1. **Test Data Factories** - Automated test data generation
2. **Custom Assertions** - Domain-specific validation
3. **Test Reporting** - Enhanced coverage and metrics
4. **CI/CD Integration** - Automated test execution
5. **Performance Benchmarking** - Response time validation
