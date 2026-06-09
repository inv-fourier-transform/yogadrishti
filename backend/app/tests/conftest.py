"""Shared test fixtures for integration tests."""
import asyncio
import pytest
import tempfile
import os
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import init_db, get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temp database path for the test session."""
    db_dir = tmp_path_factory.mktemp("test_db")
    return str(db_dir / "test_yoga.db")


@pytest.fixture(autouse=True)
async def init_test_db(test_db_path, monkeypatch):
    """Initialize a clean test database for each test."""
    # Remove old test DB if exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Monkey-patch the DB_PATH to use test database
    monkeypatch.setattr("app.db.database.DB_PATH", Path(test_db_path))

    # Initialize schema
    await init_db(test_db_path)
    yield


@pytest.fixture
async def client():
    """Create an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_image_bytes():
    """Create a minimal valid JPEG image for testing."""
    import numpy as np
    import cv2
    # Create a simple 200x200 image
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[50:150, 50:150] = [64, 128, 200]  # Orange rectangle
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()
