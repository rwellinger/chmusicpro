"""Pytest configuration and shared fixtures for unit tests"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


# ===================================
# Database Fixtures
# ===================================


@pytest.fixture
def mock_db_session():
    """Mock SQLAlchemy database session for unit tests"""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.count.return_value = 0
    session.add.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


@pytest.fixture
def mock_get_db(mocker, mock_db_session):
    """Mock get_db dependency to return mock session"""
    mock_gen = mocker.MagicMock()
    mock_gen.__next__ = MagicMock(return_value=mock_db_session)
    mock_gen.__iter__ = MagicMock(return_value=iter([mock_db_session]))

    # Patch get_db generator
    mocker.patch("db.database.get_db", return_value=mock_gen)
    return mock_gen


# ===================================
# Redis Fixtures
# ===================================


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for unit tests"""
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.exists.return_value = False
    redis_mock.keys.return_value = []
    return redis_mock


@pytest.fixture
def mock_redis_connection(mocker, mock_redis_client):
    """Mock Redis connection from URL"""
    mocker.patch("redis.from_url", return_value=mock_redis_client)
    return mock_redis_client


# ===================================
# HTTP Request Fixtures
# ===================================


@pytest.fixture
def mock_requests_get(mocker):
    """Mock requests.get for HTTP calls"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": []}
    mock_response.text = "{}"
    mock_response.raise_for_status.return_value = None

    mock_get = mocker.patch("requests.get", return_value=mock_response)
    return mock_get


@pytest.fixture
def mock_requests_post(mocker):
    """Mock requests.post for HTTP calls"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "test"}
    mock_response.text = '{"response": "test"}'
    mock_response.raise_for_status.return_value = None

    mock_post = mocker.patch("requests.post", return_value=mock_response)
    return mock_post


# ===================================
# Model Instance Fixtures
# ===================================


@pytest.fixture
def sample_song_data():
    """Sample song data for testing"""
    return {
        "task_id": "test-task-123",
        "lyrics": "Test lyrics",
        "prompt": "Test style prompt",
        "model": "auto",
        "status": "PENDING",
        "is_instrumental": False,
        "title": "Test Song",
    }


@pytest.fixture
def sample_choice_data():
    """Sample song choice data for testing"""
    return {
        "mureka_choice_id": "choice-123",
        "choice_index": 0,
        "mp3_url": "https://example.com/song.mp3",
        "flac_url": "https://example.com/song.flac",
        "duration": 180000.0,
        "title": "Generated Song",
        "tags": "rock,metal",
        "rating": None,
    }


@pytest.fixture
def sample_ollama_response():
    """Sample Ollama API response for testing"""
    return {
        "model": "llama3.2:3b",
        "created_at": "2024-01-01T00:00:00Z",
        "response": "This is a test response",
        "done": True,
        "context": [1, 2, 3, 4],  # Should be cleaned in responses
        "total_duration": 1000000,
        "load_duration": 100000,
        "prompt_eval_count": 10,
        "eval_count": 20,
    }


@pytest.fixture
def sample_ollama_models_response():
    """Sample Ollama /api/tags response for testing"""
    return {
        "models": [
            {
                "name": "llama3.2:3b",
                "modified_at": "2024-01-01T00:00:00Z",
                "size": 2000000000,
                "digest": "abc123",
            },
            {
                "name": "mistral:7b",
                "modified_at": "2024-01-01T00:00:00Z",
                "size": 4000000000,
                "digest": "def456",
            },
        ]
    }


# ===================================
# Environment Fixtures
# ===================================


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "30")
    monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "llama3.2:3b")
    monkeypatch.setenv("OLLAMA_CHAT_MODELS", "")
    monkeypatch.setenv("CHAT_DEBUG_LOGGING", "False")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
