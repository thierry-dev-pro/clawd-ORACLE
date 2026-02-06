"""
Pytest configuration and fixtures for ORACLE tests
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async (deselect with '-m \"not asyncio\"')"
    )

@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing"""
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    yield db_path

@pytest.fixture
async def async_client():
    """Create async HTTP client for testing"""
    import httpx
    async with httpx.AsyncClient() as client:
        yield client

@pytest.fixture
def mock_db():
    """Create mock database session"""
    from unittest.mock import Mock
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.add.return_value = None
    db.commit.return_value = None
    db.rollback.return_value = None
    db.close.return_value = None
    return db

# Markers for test categorization
def pytest_collection_modifyitems(config, items):
    """Modify test items to add markers"""
    for item in items:
        # Mark all async tests
        if "async" in item.keywords:
            item.add_marker(pytest.mark.asyncio)
        
        # Mark test files
        if "test_twitter" in item.nodeid:
            item.add_marker(pytest.mark.twitter_scraper)
        elif "test_airdrop" in item.nodeid:
            item.add_marker(pytest.mark.airdrop_tracker)
        elif "test_scheduler" in item.nodeid:
            item.add_marker(pytest.mark.scheduler)
