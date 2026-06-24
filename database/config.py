from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Optional
import os
from pathlib import Path

from .models import Base

class DatabaseConfig:
    """Database configuration and connection management"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://warroom:warroom_secret_2024@localhost:5432/warroom"
        )
        self.engine = None
        self.async_session_maker = None

    async def initialize(self):
        """Initialize database engine and session factory"""
        self.engine = create_async_engine(
            self.database_url,
            echo=os.getenv("DEBUG", "false").lower() == "true",
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_pre_ping=True,
        )

        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_tables(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session"""
        if self.async_session_maker is None:
            await self.initialize()

        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close database engine"""
        if self.engine:
            await self.engine.dispose()

# Global database config instance
db_config = DatabaseConfig()
