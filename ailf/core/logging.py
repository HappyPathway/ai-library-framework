"""Logging utilities.

This module provides a centralized logging configuration system
for consistent logging across all components.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from typing import Optional, Union, Dict

# Basic models and functions for logging
from pydantic import BaseModel

class LogConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_file: bool = False
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 3
    
def setup_logging(
    name: str,
    level: Optional[str] = None,
    config: Optional[LogConfig] = None,
    include_timestamp: bool = True,
) -> logging.Logger:
    """Set up and return a logger with the specified configuration.
    
    Args:
        name: The name of the logger
        level: The logging level (overrides config if provided)
        config: Optional logging configuration
        include_timestamp: Whether to include timestamp in the log format
        
    Returns:
        Configured logger instance
    """
    # Use defaults if config not provided
    if config is None:
        config = LogConfig()
        
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level from parameter or config
    log_level = level or config.level
    logger.setLevel(getattr(logging, log_level))
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    
    # Create formatter
    if include_timestamp:
        formatter = logging.Formatter(config.format)
    else:
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if configured
    if config.log_to_file:
        log_file = config.log_file or f"{name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
    
    class LogConfig(BaseModel):
        """Configuration for logging setup."""
        level: str = "INFO"
        format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_path: Optional[str] = None
        max_size_mb: int = 10
        backup_count: int = 5
    
    def setup_logging(name: str, config: Optional[Union[Dict, LogConfig]] = None) -> logging.Logger:
        """
        Set up logging with consistent configuration.
        
        Args:
            name: Logger name
            config: Optional logging configuration
            
        Returns:
            Configured logger instance
        """
        if isinstance(config, dict):
            config = LogConfig(**config)
        elif config is None:
            config = LogConfig()
            
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, config.level))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(config.format))
        logger.addHandler(console_handler)
        
        # File handler if file_path is provided
        if config.file_path:
            os.makedirs(os.path.dirname(config.file_path), exist_ok=True)
            file_handler = RotatingFileHandler(
                config.file_path, 
                maxBytes=config.max_size_mb * 1024 * 1024,
                backupCount=config.backup_count
            )
            file_handler.setFormatter(logging.Formatter(config.format))
            logger.addHandler(file_handler)
            
        return logger
    
    def get_logger(name: str) -> logging.Logger:
        """Get a logger by name, creating it if necessary."""
        return logging.getLogger(name)

__all__ = [
    "setup_logging",
    "LogConfig",
    "get_logger"
]
