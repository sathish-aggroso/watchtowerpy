import pytest
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create application for testing."""
    from app import create_app

    app = create_app("app.config.Config")
    app.config.update(
        {
            "TESTING": True,
            "DATABASE_PATH": ":memory:",
        }
    )

    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        "id": 1,
        "name": "Test Project",
        "description": "A test project",
        "created_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_link():
    """Sample link data."""
    return {
        "id": 1,
        "url": "https://example.com",
        "title": "Example",
        "project_id": 1,
        "tags": "test,example",
        "created_at": "2024-01-01T00:00:00",
        "last_checked": "2024-01-01T00:00:00",
        "last_content": "<html><body>Old content</body></html>",
        "last_error": None,
        "project_name": "Test Project",
    }


@pytest.fixture
def sample_history():
    """Sample history data."""
    return {
        "id": 1,
        "link_id": 1,
        "content": "<html><body>New content</body></html>",
        "content_hash": "abc123",
        "checked_at": "2024-01-01T00:00:00",
        "summary": "Content changed",
        "price": "$10.00",
        "price_amount": "10.00",
        "price_currency": "USD",
        "screenshot": "1.png",
        "timezone": "UTC",
    }


@pytest.fixture
def sample_html_old():
    """Sample old HTML content."""
    return """<!DOCTYPE html>
<html>
<head><title>Old Page</title></head>
<body>
    <h1>Welcome</h1>
    <p>This is old content.</p>
    <div class="content">
        <p>First paragraph</p>
        <p>Second paragraph</p>
    </div>
</body>
</html>"""


@pytest.fixture
def sample_html_new():
    """Sample new HTML content."""
    return """<!DOCTYPE html>
<html>
<head><title>New Page</title></head>
<body>
    <h1>Welcome</h1>
    <p>This is new content!</p>
    <div class="content">
        <p>First paragraph (updated)</p>
        <p>Third paragraph added</p>
    </div>
</body>
</html>"""
