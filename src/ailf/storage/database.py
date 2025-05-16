"""Database Configuration and Session Management for AI Agents.

This module provides a robust SQLAlchemy-based database infrastructure for AI agents,
enabling persistent storage of agent state, conversation history, and other data.
It implements the storage backend pattern defined in the AILF framework.

Features:
- Dynamic Connection Configuration: Support for multiple database backends (SQLite, PostgreSQL, MySQL)
- Cloud SQL Integration: Seamless connection to GCP Cloud SQL instances using ADC
- Secure Credential Management: Integration with ailf.cloud.secrets for secure password retrieval
- Session Management: Thread-safe database session handling with automatic commit/rollback
- ORM Foundation: Declarative base for defining strongly-typed database models
- Timestamp Tracking: Mixin for automatic creation/update timestamp tracking

Key Components:
- `engine`: Configured SQLAlchemy engine for database connections
- `SessionLocal`: Factory for creating properly configured database sessions
- `Base`: Declarative base for creating ORM models with SQLAlchemy
- `get_session`: Context manager for safe database session handling
- `TimestampMixin`: Mixin class to add creation/update timestamps to models
- `create_db_engine`: Factory function for creating database engines with custom configurations

Example Usage:
    >>> from ailf.storage.database import get_session, Base
    >>> from sqlalchemy import Column, Integer, String
    >>> 
    >>> # Define a model
    >>> class User(Base):
    ...     __tablename__ = "users"
    ...     id = Column(Integer, primary_key=True)
    ...     name = Column(String, nullable=False)
    ... 
    >>> # Use the session context manager
    >>> with get_session() as session:
    ...     users = session.query(User).all()

Configuration:
    Database connection parameters can be configured via environment variables:
    - DB_DIALECT: Database dialect (sqlite, postgresql, mysql, etc.)
    - DB_DRIVER: Optional database driver (psycopg2, pymysql, etc.)
    - DB_HOST: Database server hostname
    - DB_PORT: Database server port
    - DB_USER: Database username
    - DB_PASSWORD: Database password (or use password_secret for secure retrieval)
    - DB_NAME: Database name or path (for SQLite)
    
    For SQLite databases, relative paths are resolved relative to the current working directory.

Dependencies:
    - sqlalchemy: Core ORM functionality
    - Optional dialect-specific drivers (psycopg2-binary, pymysql, etc.)

Security Notes:
    For GCP Cloud SQL connections, this module uses Application Default Credentials (ADC).
    Local setup requires running `gcloud auth application-default login`.
    
    Passwords can be securely retrieved from a secrets manager by specifying a
    password_secret key in the configuration instead of a direct password.
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

class DatabaseStorage:
    """Database storage implementation."""

    def __init__(self, session_factory=None):
        """Initialize with a session factory."""
        self.session_factory = session_factory or sessionmaker(bind=engine)
        
    @contextmanager
    def session(self):
        """Get a database session as a context manager."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            
    def store(self, model_obj):
        """Store a SQLAlchemy model in the database."""
        with self.session() as session:
            session.add(model_obj)
            session.commit()
            # Refresh to get any database-generated values
            session.refresh(model_obj)
            return model_obj
            
    def get(self, model_class, id_value):
        """Get a model by its ID."""
        with self.session() as session:
            return session.query(model_class).get(id_value)
            
    def query(self, model_class, **filters):
        """Query models with filters."""
        with self.session() as session:
            query = session.query(model_class)
            for attr, value in filters.items():
                query = query.filter(getattr(model_class, attr) == value)
            return query.all()

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
