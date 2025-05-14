"""Standardized Logging Configuration

DEPRECATED: This module has been moved to ailf.core.logging.
Please update your imports to: from ailf.core.logging import setup_logging

This module provides a unified logging setup that ensures all components use consistent 
log formatting and behavior, making it easier to monitor and debug the application.

Key Features:
- Consistency: Uniform log formatting across all modules
- Ease of Use: Simple function to set up logging for any module
- Scalability: Supports adding custom handlers if needed

Example Usage:
    ```python
    from core.logging import setup_logging
    
    logger = setup_logging('my_module')
    logger.info('This is an info message')
    logger.error('This is an error message')
    ```

Use this module to ensure reliable and consistent logging throughout your application.
"""
import warnings
import sys

# Add deprecation warning
warnings.warn(
    "The utils.core.logging module is deprecated. Use ailf.core.logging instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all public symbols from the new module location
from ailf.core.logging import *

# Make sure the root logger has a handler to avoid "no handler found" warnings
logging.getLogger().addHandler(logging.NullHandler())
