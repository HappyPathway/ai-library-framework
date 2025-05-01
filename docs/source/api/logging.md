# Logging Module

```{eval-rst}
.. automodule:: utils.logging
   :members:
   :undoc-members:
   :show-inheritance:
```

## Overview

The logging module provides a standardized logging configuration for the entire application. It ensures consistent log formatting and behavior across all components.

## Features

- Standardized log formatting
- Automatic handler configuration
- Prevention of duplicate handlers
- Support for different log levels
- Contextual logging

## Usage Example

```python
from utils.logging import setup_logging

# Create a logger for your module
logger = setup_logging(__name__)

# Use various log levels
logger.debug("Detailed information for debugging")
logger.info("General information about program execution")
logger.warning("Warning messages for potential issues")
logger.error("Error messages for serious problems")
logger.critical("Critical messages for fatal errors")
