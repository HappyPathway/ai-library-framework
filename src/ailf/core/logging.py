"""Standardized Logging Configuration

This module provides a unified logging setup that ensures all components use consistent 
log formatting and behavior, making it easier to monitor and debug the application.

Key Features:
- Consistency: Uniform log formatting across all modules
- Ease of Use: Simple function to set up logging for any module
- Scalability: Supports adding custom handlers if needed
- Multiple Backends: Support for various cloud logging services and formats
  - Console (stdout/stderr)
  - JSON structured logs (for Kubernetes)
  - Google Cloud Logging
  - AWS CloudWatch
  - Logfire

Example Usage:
    ```python
    from ailf.core.logging import setup_logging
    
    logger = setup_logging('my_module')
    logger.info('This is an info message')
    logger.error('This is an error message')

    # With a specific backend
    logger = setup_logging('my_module', backend='json')
    ```

Use this module to ensure reliable and consistent logging throughout your application.
"""
import sys
import os
import json
import logging
import importlib.util
from enum import Enum
from typing import Optional, Dict, Any, List, Union, cast


class LogBackend(str, Enum):
    """Supported logging backends."""
    CONSOLE = 'console'  # Default stdout/stderr logging
    JSON = 'json'        # JSON structured logging for Kubernetes
    GCP = 'gcp'          # Google Cloud Logging
    AWS = 'aws'          # AWS CloudWatch Logs
    LOGFIRE = 'logfire'  # Logfire observability platform


# Check for optional dependencies
LOGFIRE_AVAILABLE = importlib.util.find_spec("logfire") is not None
GCP_LOGGING_AVAILABLE = importlib.util.find_spec("google.cloud.logging") is not None
AWS_CLOUDWATCH_AVAILABLE = importlib.util.find_spec("boto3") is not None


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging.
    
    This is particularly useful in Kubernetes environments.
    """
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'path': record.pathname,
            'lineno': record.lineno,
        }
        
        # Include exception info if available
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Include any custom fields added through extra parameter
        for key, value in getattr(record, '__dict__', {}).items():
            if key not in ['name', 'levelname', 'msg', 'args', 'exc_info', 'module', 
                          'pathname', 'lineno', 'created', 'msecs', 'relativeCreated', 
                          'levelno', 'funcName', 'processName', 'process', 
                          'threadName', 'thread']:
                log_data[key] = value
                
        return json.dumps(log_data)


def setup_logging(
    name: str, 
    level: Optional[str] = None,
    formatter: Optional[logging.Formatter] = None,
    backend: Optional[Union[LogBackend, str]] = None,
    add_console: bool = True,
    **backend_kwargs
) -> logging.Logger:
    """Set up a logger with consistent formatting.
    
    Args:
        name: Logger name, typically the module name
        level: Optional logging level name (defaults to INFO or environment variable)
        formatter: Optional custom formatter
        backend: Optional backend ('console', 'json', 'gcp', 'aws', or 'logfire')
        add_console: Whether to add a console handler in addition to the backend
        **backend_kwargs: Additional arguments for the backend configuration
        
    Returns:
        Configured Logger instance
    """
    # Get level from env var if not provided
    if level is None:
        level = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Convert level to int
    level_value = getattr(logging, level.upper())
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level_value)
    
    # Remove existing handlers to avoid duplicates
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    
    # Determine which backend to use
    backend_name = os.environ.get('LOG_BACKEND', 'console')
    if backend is None:
        try:
            backend = LogBackend(backend_name.lower())
        except ValueError:
            backend = LogBackend.CONSOLE
    elif isinstance(backend, str):
        try:
            backend = LogBackend(backend.lower())
        except ValueError:
            backend = LogBackend.CONSOLE

    # Configure the selected backend
    _configure_backend(logger, backend, level_value, formatter, name=name, **backend_kwargs)
    
    # Add console handler if requested and not already the backend
    if add_console and backend != LogBackend.CONSOLE:
        _add_console_handler(logger, level_value, formatter)
    
    return logger


def _configure_backend(
    logger: logging.Logger,
    backend: LogBackend,
    level: int,
    formatter: Optional[logging.Formatter] = None,
    name: str = "",
    **kwargs
) -> None:
    """Configure the specified logging backend."""
    if backend == LogBackend.CONSOLE:
        _add_console_handler(logger, level, formatter)
    
    elif backend == LogBackend.JSON:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        json_formatter = JsonFormatter()
        handler.setFormatter(json_formatter)
        logger.addHandler(handler)
    
    elif backend == LogBackend.GCP and GCP_LOGGING_AVAILABLE:
        try:
            # Delayed import to avoid dependency issues
            from google.cloud import logging_v2 as gcp_logging
            
            project_id = kwargs.get('project_id')
            gcp_client = gcp_logging.Client(project=project_id)
            handler = gcp_client.get_default_handler()
            handler.setLevel(level)
            logger.addHandler(handler)
            logger.propagate = False  # Prevent double logging
        except (ImportError, AttributeError):
            logger.warning("Google Cloud Logging not available. Falling back to console logging.")
            _add_console_handler(logger, level, formatter)
    
    elif backend == LogBackend.AWS and AWS_CLOUDWATCH_AVAILABLE:
        try:
            # These imports are protected by the AWS_CLOUDWATCH_AVAILABLE check
            # If the check passes but import fails, we'll fall back to console logging
            import boto3  # type: ignore
            import watchtower  # type: ignore
            
            log_group = kwargs.get('log_group', f"ailf/{name}")
            stream_name = kwargs.get('stream_name')
            
            handler = watchtower.CloudWatchLogHandler(  # type: ignore
                log_group=log_group,
                stream_name=stream_name,
                boto3_client=boto3.client('logs')  # type: ignore
            )
            handler.setLevel(level)
            logger.addHandler(handler)
        except ImportError:
            logger.warning("AWS CloudWatch Logs not available. Falling back to console logging.")
            _add_console_handler(logger, level, formatter)
    
    elif backend == LogBackend.LOGFIRE and LOGFIRE_AVAILABLE:
        try:
            # Protected by LOGFIRE_AVAILABLE check
            import logfire  # type: ignore
            
            api_key = kwargs.get('api_key') or os.environ.get('LOGFIRE_API_KEY')
            
            if api_key:
                logfire.init(api_key=api_key)  # type: ignore
            else:
                logfire.init()  # type: ignore
            
            handler = logfire.Handler()  # type: ignore
            handler.setLevel(level)
            logger.addHandler(handler)
        except ImportError:
            logger.warning("Logfire not available. Falling back to console logging.")
            _add_console_handler(logger, level, formatter)
    
    else:
        # Fallback to console handler
        _add_console_handler(logger, level, formatter)


def _add_console_handler(
    logger: logging.Logger,
    level: int,
    formatter: Optional[logging.Formatter] = None
) -> None:
    """Add a console handler to the logger."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter if not provided
    if formatter is None:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# Make sure the root logger has a handler to avoid "no handler found" warnings
logging.getLogger().addHandler(logging.NullHandler())
