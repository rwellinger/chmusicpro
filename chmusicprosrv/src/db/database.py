"""Database configuration and engine setup"""

import re

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import (
    DATABASE_ECHO,
    DATABASE_MAX_OVERFLOW,
    DATABASE_POOL_PRE_PING,
    DATABASE_POOL_RECYCLE,
    DATABASE_POOL_SIZE,
    DATABASE_URL,
)
from utils.logger import logger  # Direct import to avoid circular dependency with utils.__init__


def sanitize_url_for_logging(url):
    """Remove password from URL for safe logging"""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)


# Base must be created immediately (for model definitions)
Base = declarative_base()

# Engine and SessionLocal: Lazy initialization
# - Unit tests never create the engine (models are imported but not used)
# - Production/Integration tests create engine on first get_db() call
_engine = None
_SessionLocal = None


def _create_engine():
    """Create database engine (called lazily on first access)"""
    logger.debug("Database connection initiated", database_url=sanitize_url_for_logging(DATABASE_URL))
    try:
        # Create engine with appropriate settings based on database type
        # SQLite (.env_pytest): Minimal settings, no pool parameters (NOT USED - unit tests don't need DB)
        # PostgreSQL (prod/dev): Full connection pool settings
        is_sqlite = DATABASE_URL.startswith("sqlite")

        if is_sqlite:
            # SQLite: Use SingletonThreadPool, no pool parameters
            engine = create_engine(DATABASE_URL, echo=DATABASE_ECHO)
            logger.debug("Database engine created (SQLite)", echo=DATABASE_ECHO)
        else:
            # PostgreSQL: Full connection pool settings
            engine = create_engine(
                DATABASE_URL,
                echo=DATABASE_ECHO,
                pool_size=DATABASE_POOL_SIZE,
                max_overflow=DATABASE_MAX_OVERFLOW,
                pool_pre_ping=DATABASE_POOL_PRE_PING,
                pool_recycle=DATABASE_POOL_RECYCLE,
            )
            logger.debug(
                "Database engine created (PostgreSQL)",
                echo=DATABASE_ECHO,
                pool_size=DATABASE_POOL_SIZE,
                max_overflow=DATABASE_MAX_OVERFLOW,
                pool_pre_ping=DATABASE_POOL_PRE_PING,
                pool_recycle=DATABASE_POOL_RECYCLE,
            )
        return engine
    except Exception as e:
        logger.error("Database engine creation failed", error=str(e), error_type=type(e).__name__)
        raise


def get_engine():
    """Get database engine (lazy initialization)"""
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


# For backwards compatibility (some code imports 'engine' directly)
# This creates a property-like behavior
class _EngineLazy:
    """Lazy engine that creates on first access"""

    def __getattr__(self, name):
        return getattr(get_engine(), name)


engine = _EngineLazy()


def get_session_local():
    """Get SessionLocal (lazy initialization)"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# For backwards compatibility - lazy property
class _SessionLocalLazy:
    """Lazy SessionLocal that creates on first access"""

    def __call__(self, *args, **kwargs):
        return get_session_local()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(get_session_local(), name)


SessionLocal = _SessionLocalLazy()


def get_db():
    """Get database session"""
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error("Database session creation failed", error=str(e), error_type=type(e).__name__)
        raise
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error("Database session close failed", error=str(e), error_type=type(e).__name__)
