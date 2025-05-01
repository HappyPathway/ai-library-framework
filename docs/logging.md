# Logging

This module provides a standardized logging configuration to ensure consistent logging behavior across your application.

## Quick Start

```python
from utils.logging import setup_logging

logger = setup_logging('my_module')
logger.info('Application started')
```

## Features

- **Standardized Formatting**: All logs follow a consistent format 
- **Easy Setup**: Single function call to configure logging
- **Flexible Configuration**: Supports custom log levels and handlers
- **Avoid Duplicates**: Prevents duplicate handlers
- **Default Settings**: Sensible defaults for quick setup

## Configuration

By default, logs are formatted as:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

This includes:
- Timestamp
- Module name
- Log level
- Message content

## Best Practices

1. Create one logger per module:
   ```python
   logger = setup_logging(__name__)
   ```

2. Use appropriate log levels:
   ```python
   logger.debug('Detailed information for debugging')
   logger.info('General information about program execution')
   logger.warning('Warning messages for potentially harmful situations')
   logger.error('Error messages for serious problems')
   logger.critical('Critical messages for fatal errors')
   ```

3. Include relevant context in log messages:
   ```python
   logger.error(f'Failed to process item {item_id}: {str(e)}')
   ```

## API Reference

For detailed API documentation, see the {doc}`api/logging` page.
