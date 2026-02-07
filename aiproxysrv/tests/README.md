# aiproxysrv Unit Tests

Unit test suite for aiproxysrv to detect regressions after refactorings and library migrations.

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures and test configuration
├── unit/                            # Unit tests (no external dependencies)
│   ├── test_controllers/           # Controller layer tests
│   │   ├── test_chat_controller.py # ChatController (Ollama chat generation)
│   │   └── test_ollama_controller.py # OllamaController (model discovery)
│   ├── test_database/              # Database layer tests
│   │   ├── test_models.py          # SQLAlchemy model instantiation
│   │   └── test_song_service.py    # SongService CRUD operations
│   └── test_utils/                 # Utility tests
│       └── test_database_helpers.py # Database helper functions
└── README.md                        # This file
```

## Running Tests

### All Tests

```bash
# From aiproxysrv directory
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=src --cov-report=html
```

### Specific Test Categories

```bash
# Only unit tests
pytest tests/unit/

# Only database tests
pytest tests/unit/test_database/

# Only controller tests
pytest tests/unit/test_controllers/

# Specific test file
pytest tests/unit/test_controllers/test_chat_controller.py

# Specific test class
pytest tests/unit/test_controllers/test_chat_controller.py::TestChatControllerGenerateChat

# Specific test method
pytest tests/unit/test_controllers/test_chat_controller.py::TestChatControllerGenerateChat::test_generate_chat_success
```

### Using Markers

```bash
# Only unit tests
pytest -m unit

# Exclude slow tests
pytest -m "not slow"
```

## Test Philosophy

### Unit Tests Only

These tests are **pure unit tests** with the following characteristics:

- **No external dependencies**: No real database, Redis, or external API calls
- **Mocked dependencies**: All external services are mocked using `pytest-mock`
- **Fast execution**: All 73 tests run in ~1 second
- **Isolated**: Each test is independent and can run in any order

### What We Test

1. **Model Instantiation** (`test_models.py`)
   - SQLAlchemy model creation
   - Model validation
   - Relationships

2. **Service Layer** (`test_song_service.py`)
   - CRUD operations with mocked DB sessions
   - Error handling
   - Redis cleanup logic

3. **Controllers** (`test_chat_controller.py`, `test_ollama_controller.py`)
   - Business logic
   - API call handling (mocked)
   - Response transformation
   - Error handling

4. **Utilities** (`test_database_helpers.py`)
   - Helper functions
   - Data sanitization

### What We Don't Test

- **Integration tests**: No real database or external API calls
- **End-to-end tests**: No full request/response cycles
- **Performance tests**: Focus is on correctness, not performance

## Test Coverage

Current coverage: **~11%** (484 of 4398 statements)

This is expected for unit tests that focus on critical business logic:

- **100% coverage**: Models, Settings, Config
- **74% coverage**: ChatController
- **84% coverage**: OllamaController
- **40% coverage**: SongService (CRUD operations tested, bulk operations not)
- **0% coverage**: Routes, Celery tasks, API app (requires integration tests)

## Fixtures (conftest.py)

### Database Fixtures

- `mock_db_session`: Mock SQLAlchemy session
- `mock_get_db`: Mock get_db dependency

### Redis Fixtures

- `mock_redis_client`: Mock Redis client
- `mock_redis_connection`: Mock Redis connection

### HTTP Fixtures

- `mock_requests_get`: Mock HTTP GET requests
- `mock_requests_post`: Mock HTTP POST requests

### Sample Data Fixtures

- `sample_song_data`: Sample song dictionary
- `sample_choice_data`: Sample song choice dictionary
- `sample_ollama_response`: Sample Ollama API response
- `sample_ollama_models_response`: Sample Ollama /api/tags response

### Environment Fixtures

- `mock_env_vars`: Mock environment variables

## Writing New Tests

### Example Unit Test

```python
import pytest
from unittest.mock import MagicMock

@pytest.mark.unit
class TestMyService:
    """Test MyService business logic"""

    def test_my_method_success(self, mocker, mock_db_session):
        """Test successful operation"""
        # Arrange: Setup mocks
        mocker.patch("db.database.get_db", return_value=iter([mock_db_session]))
        mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock()

        # Act: Call method under test
        service = MyService()
        result = service.my_method("test-id")

        # Assert: Verify behavior
        assert result is not None
        assert mock_db_session.query.called
```

### Best Practices

1. **Use `@pytest.mark.unit` marker**: Mark all unit tests
2. **AAA Pattern**: Arrange, Act, Assert
3. **Descriptive names**: `test_method_name_scenario_expected_outcome`
4. **One assertion per test**: Focus on single behavior
5. **Mock at boundaries**: Mock external dependencies, not internal logic
6. **Test error paths**: Test both success and failure scenarios

## CI/CD Integration

### Pre-commit Hook (Ruff)

```bash
# Install pre-commit
pip install -e ".[dev]"
pre-commit install

# Run manually
pre-commit run --all-files
```

### Running Tests Before Commit

```bash
# Quick check
pytest tests/unit/ -x  # Stop on first failure

# Full check
pytest tests/unit/ -v --cov=src
```

## Troubleshooting

### Tests Fail After Library Upgrade

**Purpose of these tests!** Check which tests fail:

1. **Model tests fail**: SQLAlchemy API changed
2. **Controller tests fail**: HTTP library or business logic changed
3. **Service tests fail**: Database layer changed

Review failing tests to understand what changed and update code or tests accordingly.

### Import Errors

```bash
# Reinstall package in editable mode
pip install -e ".[test]"
```

### Mock Not Working

Check that you're patching at the correct location:

```python
# ❌ Wrong: Patch at definition location
mocker.patch("config.settings.OLLAMA_URL", ...)

# ✅ Correct: Patch at import location
mocker.patch("api.controllers.ollama_controller.OLLAMA_URL", ...)
```

## Future Enhancements

Potential additions (not yet implemented):

- **Integration tests**: Test with real database (Docker)
- **API tests**: Test Flask routes with test client
- **Performance tests**: Benchmark critical operations
- **Contract tests**: Verify external API mocks match real APIs
- **Mutation tests**: Verify test quality with mutation testing

## Questions?

Check the main project documentation in `/docs` or see `CLAUDE.md` for project structure and patterns.
