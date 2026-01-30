"""Database connection and session management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from benchmark.core.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str, **engine_kwargs: Any) -> None:
        """Initialize database manager.

        Args:
            database_url: Database connection URL
            **engine_kwargs: Additional arguments for create_async_engine
        """
        self.database_url = database_url

        # Default engine configuration
        default_config = {
            "echo": False,
            "pool_pre_ping": True,
            "pool_size": 5,
            "max_overflow": 10,
        }
        default_config.update(engine_kwargs)

        self._engine: AsyncEngine = create_async_engine(database_url, **default_config)
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        return self._engine

    async def create_tables(self) -> None:
        """Create all tables in the database."""
        logger.info("Creating database tables")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async def drop_tables(self) -> None:
        """Drop all tables from the database."""
        logger.warning("Dropping all database tables")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for database sessions.

        Yields:
            AsyncSession: Database session

        Example:
            async with db_manager.session() as session:
                result = await session.execute(select(Benchmark))
        """
        session: AsyncSession = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """Close database connections."""
        logger.info("Closing database connections")
        await self._engine.dispose()


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager(database_url: str | None = None, **engine_kwargs: Any) -> DatabaseManager:
    """Get or create global database manager instance.

    Args:
        database_url: Database connection URL (required for first call)
        **engine_kwargs: Additional arguments for create_async_engine

    Returns:
        DatabaseManager: Global database manager instance

    Raises:
        ValueError: If database_url is not provided on first call
    """
    global _db_manager

    if _db_manager is None:
        if database_url is None:
            raise ValueError("database_url must be provided when creating DatabaseManager")
        _db_manager = DatabaseManager(database_url, **engine_kwargs)

    return _db_manager


async def close_db() -> None:
    """Close the global database connection."""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.close()
        _db_manager = None
