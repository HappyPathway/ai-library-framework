# Repository Cleanup and Reorganization Plan

This document outlines a comprehensive plan for cleaning up and reorganizing the `template-python-dev` repository to improve its structure, maintainability, and developer experience.

## Current Structure Analysis

The current repository structure has several areas that can be improved:

1. **Schema Organization**: Pydantic models are scattered across different modules
2. **Test Organization**: Tests are inconsistently organized 
3. **Messaging Infrastructure**: ZMQ-related code is spread across multiple files
4. **Documentation**: Inconsistent documentation across modules
5. **Cloud Infrastructure**: Cloud-related code is spread across different utility modules
6. **Development Environment**: Setup code scattered between Makefile, requirements.txt, and documentation
7. **Utility Functions**: Many utility functions defined at module level

## Proposed Directory Structure

```
template-python-dev/
├── agent/                      # Core agent functionality (future feature)
├── utils/                      # Core utilities
│   ├── __init__.py
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── monitoring.py
│   ├── ai/                     # AI-related functionality
│   │   ├── __init__.py
│   │   ├── engine.py           # Refactored from ai_engine.py
│   │   └── tools/              # AI tools implementations
│   ├── storage/                # Storage-related functionality
│   │   ├── __init__.py
│   │   ├── local.py            # Local storage implementation
│   │   └── setup.py            # Storage setup functionality
│   ├── cloud/                  # Cloud-related functionality
│   │   ├── __init__.py
│   │   ├── gcs.py              # GCS operations (renamed from gcs_config_stash.py)
│   │   └── secrets.py          # Cloud secrets management
│   ├── messaging/              # Messaging infrastructure
│   │   ├── __init__.py
│   │   ├── zmq.py              # ZMQ implementation
│   │   └── devices.py          # ZMQ devices implementation
│   ├── database.py             # Database functionality
│   ├── github_client.py        # GitHub API client
│   └── web_scraper.py          # Web scraping functionality
├── schemas/                    # All Pydantic models
│   ├── __init__.py
│   ├── ai.py                   # AI-related schemas
│   ├── storage.py              # Storage-related schemas
│   ├── database.py             # Database-related schemas
│   ├── messaging/              # Messaging schemas
│   │   ├── __init__.py
│   │   ├── zmq.py
│   │   └── devices.py
│   └── api/                    # API-related schemas
│       ├── __init__.py
│       └── github.py           # GitHub API schemas
├── tests/                      # Test organization
│   ├── __init__.py
│   ├── conftest.py             # Common test fixtures
│   ├── unit/                   # All unit tests
│   │   ├── __init__.py
│   │   ├── utils/              # Unit tests for utils modules
│   │   │   ├── __init__.py
│   │   │   ├── ai/             # Tests for AI modules
│   │   │   ├── core/           # Tests for core modules
│   │   │   ├── storage/        # Tests for storage modules
│   │   │   ├── cloud/          # Tests for cloud modules
│   │   │   └── messaging/      # Tests for messaging modules
│   │   └── schemas/            # Unit tests for schemas
│   └── integration/            # All integration tests
│       ├── __init__.py
│       ├── conftest.py         # Integration-specific fixtures
│       └── utils/              # Integration tests for utils modules
├── examples/                   # Example implementations
├── setup/                      # Development environment setup
│   ├── __init__.py
│   ├── dev_setup.py            # Development environment setup
│   └── requirements/           # Split requirements files
│       ├── base.txt            # Core dependencies
│       ├── dev.txt             # Development dependencies
│       └── prod.txt            # Production dependencies
└── docs/                       # Documentation
```

## Migration Plan

We'll implement the reorganization in phases to minimize disruption:

### Phase 1: Schema Reorganization

1. Move schema models from utils to central schemas directory
2. Update imports in all files
3. Create appropriate new schema files for logical grouping
4. Update documentation

### Phase 2: Test Reorganization

1. Create new test directory structure
2. Move tests to appropriate locations
3. Update imports in test files
4. Update CI configuration

### Phase 3: Utils Reorganization

1. Create subdirectories in utils
2. Move files to appropriate locations
3. Update imports across the codebase
4. Update documentation

### Phase 4: Documentation Standardization

1. Create documentation templates
2. Update existing documentation to follow templates
3. Update Sphinx configuration
4. Generate new documentation

### Phase 5: Development Environment Improvement

1. Create setup directory
2. Split requirements.txt into specialized files
3. Create standardized setup scripts
4. Update Makefile targets

## Detailed Migration Steps

### Phase 1: Schema Reorganization

#### Step 1: Prepare the Schema Structure

```bash
# Create new schema directories
mkdir -p schemas/messaging
mkdir -p schemas/api

# Create new __init__.py files
touch schemas/__init__.py
touch schemas/database.py
touch schemas/messaging/__init__.py
touch schemas/api/__init__.py
touch schemas/api/github.py
```

#### Step 2: Move Schema Files

1. Move `utils/schemas/ai.py` to `schemas/ai.py`
2. Move `utils/schemas/storage.py` to `schemas/storage.py`
3. Move `utils/schemas/zmq.py` to `schemas/messaging/zmq.py`
4. Move `utils/schemas/zmq_devices.py` to `schemas/messaging/devices.py`
5. Create `schemas/api/github.py` for GitHub API schemas

#### Step 3: Update Imports

Update all import statements across the codebase to reference the new schema locations.

### Phase 2: Test Reorganization

#### Step 1: Prepare Test Structure

```bash
# Create new test directories
mkdir -p tests/unit/utils/ai
mkdir -p tests/unit/utils/core
mkdir -p tests/unit/utils/storage
mkdir -p tests/unit/utils/cloud
mkdir -p tests/unit/utils/messaging
mkdir -p tests/unit/schemas

# Create new __init__.py files
touch tests/unit/__init__.py
touch tests/unit/utils/__init__.py
touch tests/unit/utils/ai/__init__.py
touch tests/unit/utils/core/__init__.py
touch tests/unit/utils/storage/__init__.py
touch tests/unit/utils/cloud/__init__.py
touch tests/unit/utils/messaging/__init__.py
touch tests/unit/schemas/__init__.py
```

#### Step 2: Move Test Files

Move tests to their appropriate locations in the new structure.

### Phase 3: Utils Reorganization

#### Step 1: Prepare Utils Structure

```bash
# Create new utils directories
mkdir -p utils/core
mkdir -p utils/ai
mkdir -p utils/ai/tools
mkdir -p utils/storage
mkdir -p utils/cloud
mkdir -p utils/messaging

# Create new __init__.py files
touch utils/core/__init__.py
touch utils/ai/__init__.py
touch utils/ai/tools/__init__.py
touch utils/storage/__init__.py
touch utils/cloud/__init__.py
touch utils/messaging/__init__.py
```

#### Step 2: Move Utility Files

1. Move `utils/logging.py` to `utils/core/logging.py`
2. Move `utils/monitoring.py` to `utils/core/monitoring.py`
3. Move `utils/ai_engine.py` to `utils/ai/engine.py`
4. Move `utils/storage.py` to `utils/storage/local.py`
5. Move `utils/setup_storage.py` to `utils/storage/setup.py`
6. Move `utils/gcs_config_stash.py` to `utils/cloud/gcs.py`
7. Move `utils/secrets.py` to `utils/cloud/secrets.py`
8. Move `utils/zmq.py` to `utils/messaging/zmq.py`
9. Move `utils/zmq_devices.py` to `utils/messaging/devices.py`

## Change Management

For each phase:

1. Create a feature branch
2. Make the required changes
3. Update all affected imports
4. Run tests to ensure everything works
5. Update documentation
6. Create a pull request
7. Review and merge

## Testing Strategy

1. Validate all unit tests pass after each phase
2. Validate all integration tests pass after each phase
3. Manual testing of examples
4. Test documentation build

## Backward Compatibility

To maintain backward compatibility during transition:

1. Keep old modules temporarily with import forwarding
2. Add deprecation warnings to old modules
3. After sufficient time, remove deprecated modules

## Timeline

1. **Phase 1**: Schema Reorganization (1 day)
2. **Phase 2**: Test Reorganization (1 day)
3. **Phase 3**: Utils Reorganization (2 days)
4. **Phase 4**: Documentation Standardization (1 day)
5. **Phase 5**: Development Environment Improvement (1 day)

Total estimated time: **6 days**

## Rollback Plan

For each phase:
1. Maintain backups of original files
2. Create rollback scripts
3. Document rollback procedures
4. Test rollback procedures

## Conclusion

This migration plan will improve the structure and maintainability of the `template-python-dev` repository by organizing code more logically, improving documentation, and establishing better development patterns. The phased approach will minimize disruption while ensuring a smooth transition to the improved structure.
