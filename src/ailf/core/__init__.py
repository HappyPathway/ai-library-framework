"""Core package providing foundational utilities.

This package contains core functionality that forms the foundation of the AILF toolkit,
including logging, monitoring, storage, and other essential services.
"""

# Import key components for easy access
from . import logging
from . import monitoring
from . import storage

try:
    from .logging import setup_logging
    from .monitoring import setup_monitoring
except ImportError:
    pass  # Handle case where modules aren't available

__all__ = [
    "logging",
    "monitoring",
    "storage",
    "setup_logging",
    "setup_monitoring"
]
