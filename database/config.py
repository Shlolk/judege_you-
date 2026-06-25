"""Database configuration and session management"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import os
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and connection management"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://warroom:warroom_secret_2024@localhost:5432/warroom"
        )
        self.engine = None
        self.async_session_maker = None
        self._initialized = False

    async def initialize(self):
        """Initialize database engine and session factory"""
        if self._initialized:
            return
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=os.getenv("DEBUG", "false").lower() == "true",
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
                pool_pre_ping=True,
            )
            self.async_session_maker = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False,
            )
            self._initialized = True
            logger.info("Database engine initialized")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}. Repositories will use mock mode.")

    @asynccontextmanager
    async def session(self, existing_session: Optional[AsyncSession] = None) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session.

        If an existing_session is provided, uses it (no commit/rollback).
        Otherwise creates a new session with auto commit/rollback.
        """
        if existing_session is not None:
            yield existing_session
            return

        if not self._initialized:
            await self.initialize()

        if self.async_session_maker is None:
            logger.debug("No database connection, yielding None session")
            yield None
            return

        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self):
        """Create all tables"""
        if not self._initialized:
            await self.initialize()
        if self.engine:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")

    async def drop_tables(self):
        """Drop all tables"""
        if not self._initialized:
            await self.initialize()
        if self.engine:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

    async def close(self):
        """Close database engine"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database engine disposed")


db_config = DatabaseConfig()
