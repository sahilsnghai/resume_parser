from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("app.database")


engine = create_async_engine(
    settings.database_url_async,
    echo=settings.is_debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)


AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session

    Usage in FastAPI routes:
        @router.get("/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()


async def create_tables():
    """
    Create database tables

    This function should be called during application startup
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def drop_tables():
    """
    Drop all database tables

    Use with caution - this will delete all data!
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


async def test_connection():
    """
    Test database connection

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


class DatabaseManager:
    """Utility class for database operations"""

    @staticmethod
    async def execute_query(session: AsyncSession, query, **params):
        """Execute a query with parameters"""
        try:
            result = await session.execute(query, params)
            return result
        except SQLAlchemyError as e:
            logger.error(f"Query execution error: {e}")
            raise

    @staticmethod
    async def commit_transaction(session: AsyncSession):
        """Commit current transaction"""
        try:
            await session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Transaction commit error: {e}")
            raise

    @staticmethod
    async def rollback_transaction(session: AsyncSession):
        """Rollback current transaction"""
        try:
            await session.rollback()
        except SQLAlchemyError as e:
            logger.error(f"Transaction rollback error: {e}")
            raise
