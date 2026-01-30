"""Pytest configuration and fixtures."""

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from benchmark.core.config import Settings
from benchmark.core.database import DatabaseManager
from benchmark.core.models import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Create test settings."""
    return Settings(
        pyannote_api_key="test_key",
        pyannote_api_base_url="http://test.api",
        database_url=os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://benchmark:benchmark@postgres:5432/diarization_benchmark"
        ),
        data_dir=tmp_path / "data",
        results_dir=tmp_path / "results",
        cache_dir=tmp_path / "cache",
        log_level="DEBUG",
        environment="test",
    )


@pytest.fixture
async def db_manager(test_settings: Settings) -> AsyncGenerator[DatabaseManager, None]:
    """Create test database manager."""
    manager = DatabaseManager(str(test_settings.database_url))

    # Create tables
    await manager.create_tables()

    yield manager

    # Cleanup
    await manager.drop_tables()
    await manager.close()


@pytest.fixture
async def db_session(db_manager: DatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async with db_manager.session() as session:
        yield session


@pytest.fixture
def sample_rttm_content() -> str:
    """Sample RTTM content for testing."""
    return """SPEAKER file1 1 0.0 2.5 <NA> <NA> speaker1 <NA>
SPEAKER file1 1 2.5 3.0 <NA> <NA> speaker2 <NA>
SPEAKER file1 1 5.5 1.5 <NA> <NA> speaker1 <NA>
"""


@pytest.fixture
def sample_rttm_file(tmp_path: Path, sample_rttm_content: str) -> Path:
    """Create sample RTTM file for testing."""
    rttm_file = tmp_path / "test.rttm"
    rttm_file.write_text(sample_rttm_content)
    return rttm_file


@pytest.fixture
def sample_hypothesis() -> dict[str, Any]:
    """Sample diarization hypothesis for testing."""
    return {
        "segments": [
            {"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"},
            {"start": 2.5, "end": 5.5, "speaker": "SPEAKER_01"},
            {"start": 5.5, "end": 7.0, "speaker": "SPEAKER_00"},
        ]
    }


@pytest.fixture
def mock_api_response() -> dict[str, Any]:
    """Mock API response for testing."""
    return {
        "segments": [
            {"start": 0.0, "end": 2.4, "speaker": "SPEAKER_00"},
            {"start": 2.6, "end": 5.4, "speaker": "SPEAKER_01"},
            {"start": 5.6, "end": 7.0, "speaker": "SPEAKER_00"},
        ],
        "num_speakers": 2,
    }
