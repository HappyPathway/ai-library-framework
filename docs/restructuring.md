# AILF Framework Restructuring

## Overview

The AILF framework is being restructured to follow modern Python package design principles. This restructuring moves away from a large catch-all `utils` directory toward domain-specific modules that better encapsulate related functionality.

## New Package Structure

The new structure organizes code into domain-specific modules under the `ailf` namespace:

```
src/ailf/
├── __init__.py           # Main package init
├── ai/                   # AI-related functionality
│   ├── __init__.py
│   ├── engine.py         # Core AI engine
│   └── tools/            # AI tools
├── cloud/                # Cloud-related functionality
│   ├── __init__.py
│   ├── secrets.py        # Secret management
│   └── storage/          # Cloud storage implementations
├── communication/        # Communication protocols
│   ├── __init__.py
│   ├── web_scraper.py    # Web scraping utilities
│   └── zmq/              # ZMQ implementations
├── core/                 # Core utilities
│   ├── __init__.py
│   ├── logging.py        # Centralized logging
│   └── monitoring.py     # Instrumentation and metrics
├── schemas/              # All Pydantic models
│   └── __init__.py
└── storage/              # Storage implementations
    ├── __init__.py
    └── database.py       # Database functionality
```

## Migrating to the New Structure

### For New Code

Use the new import paths:

```python
# Old imports
from utils.core.logging import setup_logging
from utils.cloud.secrets import get_secret

# New imports
from ailf.core.logging import setup_logging
from ailf.cloud.secrets import get_secret
```

### For Existing Code

Backward compatibility is maintained through re-export modules that emit deprecation warnings when used. This allows existing code to continue working while providing guidance to update to the new structure.

## Path Forward

1. **Phase 1**: Use new import paths for all new code
2. **Phase 2**: Gradually update existing imports to use new paths
3. **Phase 3**: After sufficient time, remove compatibility modules

## Benefits of the New Structure

- **Clearer Domain Boundaries**: Each module represents a specific capability domain
- **Better Discoverability**: Developers can find related functionality more easily
- **Improved Maintenance**: Changes to one domain are isolated from others
- **Enhanced Documentation**: Documentation can be organized by domain
- **Better Testing Organization**: Tests can align with domain modules
