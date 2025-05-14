"""Database Configuration and Session Management.

This module provides essential database functionality built on SQLAlchemy.
It offers:
- Configuration: Centralized database setup and connection management
- Session Management: Context manager for handling database sessions
- Base Model: Declarative base for defining database models

Key Components:
- `engine`: SQLAlchemy engine for database connections
- `SessionLocal`: Factory for creating database sessions
- `Base`: Declarative base for ORM models
- `get_session`: Context manager for database sessions

Example Usage:
    >>> from ailf.storage.database import get_session, Base
    >>> 
    >>> with get_session() as session:
    ...     users = session.query(User).all()

Note:
    This module uses SQLAlchemy. Install with `pip install sqlalchemy`.
    
    For GCP Cloud SQL connections, it uses Application Default Credentials (ADC).
    Local setup requires running `gcloud auth application-default login`.
"""
import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Generator, TypeVar, Generic, Type
from urllib.parse import quote_plus

from sqlalchemy import create_engine, Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ailf.core.logging import setup_logging
from ailf.cloud.secrets import get_secret

logger = setup_logging("database")

# Create a base class for models
Base = declarative_base()

# Type variable for session context manager
T = TypeVar('T')

# Default settings - can be overridden with environment variables
DATABASE_CONFIG = {
    "dialect": os.getenv("DB_DIALECT", "sqlite"),
    "driver": os.getenv("DB_DRIVER", ""),
    "host": os.getenv("DB_HOST", ""),
    "port": os.getenv("DB_PORT", ""),
    "username": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "database.db"),
    "params": {
        "connect_timeout": os.getenv("DB_CONNECT_TIMEOUT", "10"),
        "check_same_thread": "false",  # For SQLite
    }
}


def create_db_engine(config: Optional[Dict[str, Any]] = None) -> Any:
    """Create a SQLAlchemy engine with given configuration.
    
    Args:
        config: Database configuration dictionary. If not provided,
               the default configuration will be used.
        
    Returns:
        SQLAlchemy engine instance
    """
    config = config or DATABASE_CONFIG
    dialect = config.get("dialect", "sqlite")
    
    # Build connection URL based on dialect
    if dialect == "sqlite":
        database = config.get("database", "database.db")
        if not database.startswith("/:memory:") and not os.path.isabs(database):
            database = os.path.join(os.getcwd(), database)
        url = f"{dialect}:///{database}"
    else:
        # Get components - ensure all are properly URL-encoded
        driver = config.get("driver", "")
        driver_str = f"+{driver}" if driver else ""
        
        host = config.get("host", "")
        port = config.get("port", "")
        port_str = f":{port}" if port else ""
        
        username = config.get("username", "")
        password = config.get("password", "")
        
        # Get password from secrets manager if needed
        password_secret = config.get("password_secret")
        if password_secret and not password:
            password = get_secret(password_secret)
        
        # URL encode username and password
        username = quote_plus(username) if username else ""
        password = quote_plus(password) if password else ""
        auth = f"{username}:{password}@" if username else ""
        
        database = config.get("database", "")
        
        # Build URL
        url = f"{dialect}{driver_str}://{auth}{host}{port_str}/{database}"
    
    # Add URL parameters
    params = config.get("params", {})
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{param_str}"
    
    logger.debug(f"Creating database engine with dialect: {dialect}")
    
    # Create engine with appropriate settings
    connect_args = {}
    if dialect == "sqlite":
        connect_args = {"check_same_thread": False}
    
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


# Create the engine and session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions.
    
    Example:
        >>> with get_session() as session:
        ...     user = session.query(User).first()
    
    Yields:
        SQLAlchemy session
    
    Raises:
        Exception: Any exception that occurs within the session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


class TimestampMixin:
    """Mixin to add timestamp columns to models."""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
