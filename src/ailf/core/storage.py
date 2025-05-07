"""Storage abstraction layer.

This module provides a unified interface for storage operations,
supporting local and cloud storage backends.
"""

from utils.storage import (
    StorageBase,
    LocalStorage,
    CloudStorage
)

__all__ = [
    "StorageBase",
    "LocalStorage",
    "CloudStorage"
]
