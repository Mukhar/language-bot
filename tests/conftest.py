import pytest
import tempfile
import os


def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_databases():
    """Clean up test database files after test session"""
    yield
    
    # List of test database files to clean up
    test_db_files = [
        "test.db",
        "test_models.db", 
        "test_scenarios.db",
        "test_responses.db",
        "test_evaluations.db"
    ]
    
    for db_file in test_db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except OSError:
                pass  # Ignore errors if file is locked or doesn't exist


@pytest.fixture
def temp_db_file():
    """Create a temporary database file for testing"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass
