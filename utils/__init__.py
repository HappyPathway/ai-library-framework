"""Core utilities for the Python agent development template.

This package provides a collection of utilities, patterns, and infrastructure components
specifically designed to accelerate the development of AI agents with:

- Structured LLM interactions via Pydantic models
- Tool registration and management
- Distributed computing via ZeroMQ and Redis
- Configurable storage backends
- Comprehensive logging and monitoring
- Secure secret management
- Worker management with Celery
"""

# Core functionality
from .core import logging
from .core import monitoring

# AI-related functionality
from .ai import engine

# Storage functionality
from .storage import local
from .storage import setup as setup_storage

# Cloud functionality
from .cloud import gcs
from .cloud import secrets

# Messaging functionality
from .messaging import zmq
from .messaging import devices as zmq_devices
from .messaging import redis
from .messaging import async_redis
from .messaging import mock_redis

# Worker functionality
from .workers import celery_app
from .workers import tasks

__all__ = [
    # Core
    "logging",
    "monitoring",
    
    # AI
    "engine",
    
    # Storage
    "local",
    "setup_storage",
    
    # Cloud
    "gcs",
    "secrets",
    
    # Messaging
    "zmq",
    "zmq_devices",
    "redis",
    "async_redis",
    "mock_redis",
    
    # Workers
    "celery_app",
    "tasks",
]
