"""Standardized Logging Configuration

This module provides a unified logging setup that ensures all components use consistent 
log formatting and behavior, making it easier to monitor and debug the application.

Key Features:
- Consistency: Uniform log formatting across all modules
- Ease of Use: Simple function to set up logging for any module
- Scalability: Supports adding custom handlers if needed

Example Usage:
    ```python
    from ailf.core.logging import setup_logging
    
    logger = setup_logging('my_module')
    logger.info('This is an info message')
    logger.error('This is an error message')
    ```

Use this module to ensure reliable and consistent logging throughout your application.
"""
import sys
import os
import logging
from typing import Optional, Dict, Any

def setup_logging(
    name: str, 
    level: Optional[int] = None,
    formatter: Optional[logging.Formatter] = None
) -> logging.Logger:
    """Set up a logger with consistent formatting.
    
    Args:
        name: Logger name, typically the module name
        level: Optional logging level (defaults to INFO or environment variable)
        formatter: Optional custom formatter
        
    Returns:
        Configured Logger instance
    """
    # Get level from env var if not provided
    if level is None:
        level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Check if logger already has handlers to avoid duplicates
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Create formatter if not provided
        if formatter is None:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Make sure the root logger has a handler to avoid "no handler found" warnings
logging.getLogger().addHandler(logging.NullHandler())
