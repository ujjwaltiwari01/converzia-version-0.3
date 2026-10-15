"""
Pytest Global Test Fixtures
"""
import pytest
from app.db.session import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database schema is created before running any tests."""
    init_db()
