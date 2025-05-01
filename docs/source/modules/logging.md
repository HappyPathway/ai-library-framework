# Logging Module

The logging module provides a standardized logging configuration system for the application.

## Overview

This module implements a consistent logging setup with the following features:

- Standardized log formatting
- Configurable log levels
- File and console output handlers
- Automatic log file rotation
- Context-aware logging

## Quick Start

```python
from utils.logging import setup_logging

# Create a logger for your module
logger = setup_logging('my_module')

# Use the logger
logger.info('Application started')
logger.debug('Debug information')
logger.warning('Warning message')
```

## Configuration

The default configuration includes:

- Log Level: INFO
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Output: Console and rotating file handler
- File Location: `logs/app.log`

## Best Practices

1. Use one logger per module:
   ```python
   logger = setup_logging(__name__)
   ```

2. Include context in log messages:
   ```python
   logger.error(f'Failed to process item {item_id}: {str(error)}')
   ```

3. Use appropriate log levels:
   - DEBUG: Detailed information for debugging
   - INFO: General operational events
   - WARNING: Unexpected but handled situations
   - ERROR: Serious problems that need attention
   - CRITICAL: Critical failures requiring immediate action

## API Reference

For detailed API documentation, see the {doc}`/api/logging` page.
