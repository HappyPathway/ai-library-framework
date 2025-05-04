# Implementation Plan for Repository Reorganization

This document provides a detailed implementation plan for each phase of the repository reorganization.

## Phase 1: Schema Reorganization

### Tasks

1. **Create schema directory structure**
   - Create `/schemas` directory and subdirectories
   - Create necessary `__init__.py` files

2. **Move AI schemas**
   - Move `/utils/schemas/ai.py` to `/schemas/ai.py`
   - Split into separate files if needed (core.py, settings.py, etc.)
   - Update imports in all files that reference AI schemas

3. **Move messaging schemas**
   - Move `/utils/schemas/zmq.py` to `/schemas/messaging/zmq.py`
   - Move `/utils/schemas/zmq_devices.py` to `/schemas/messaging/devices.py`
   - Update imports in all files that reference ZMQ schemas

4. **Move storage schemas**
   - Move `/utils/schemas/storage.py` to `/schemas/storage.py`
   - Update imports in all files that reference storage schemas

5. **Create test schemas**
   - Move `/utils/schemas/test.py` to `/schemas/test.py`

6. **Create database schemas**
   - Create `/schemas/database.py` and move relevant models from other files

7. **Create GitHub API schemas**
   - Create `/schemas/api/github.py` for GitHub API models

8. **Update central __init__.py**
   - Ensure `/schemas/__init__.py` exports all commonly used models
   - Add appropriate import aliases for backward compatibility

9. **Add backward compatibility imports**
   - Create imports in old locations that reference new locations
   - Add deprecation warnings

### Scripts

```python
# Script to create directory structure
import os
import shutil

# Create directories
dirs = [
    "schemas/api",
    "schemas/messaging"
]

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)
    init_file = os.path.join(dir_path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write('"""{}"""\n'.format(dir_path.replace("/", ".") + " package"))
```

## Phase 2: Test Reorganization

### Tasks

1. **Create test directory structure**
   - Create `/tests/unit` directory and subdirectories
   - Create appropriate `__init__.py` files

2. **Move AI tests**
   - Move AI-related tests to `/tests/unit/utils/ai`
   - Update imports in test files

3. **Move messaging tests**
   - Move ZMQ-related tests to `/tests/unit/utils/messaging`
   - Update imports in test files

4. **Move storage tests**
   - Move storage-related tests to `/tests/unit/utils/storage`

5. **Move cloud tests**
   - Move GCS and secrets tests to `/tests/unit/utils/cloud`

6. **Move core tests**
   - Move logging and monitoring tests to `/tests/unit/utils/core`

7. **Update integration tests**
   - Ensure integration tests follow same structure
   - Update imports in integration tests

8. **Update conftest.py**
   - Review and update fixtures in conftest.py
   - Consider splitting fixtures into domain-specific files

9. **Update CI configuration**
   - Update any CI scripts that reference test paths

### Scripts

```python
# Script to create test directory structure
import os
import shutil

# Create directories
dirs = [
    "tests/unit/utils/ai",
    "tests/unit/utils/core",
    "tests/unit/utils/storage",
    "tests/unit/utils/cloud",
    "tests/unit/utils/messaging",
    "tests/unit/schemas"
]

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)
    init_file = os.path.join(dir_path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write('"""{}"""\n'.format(dir_path.replace("/", ".") + " tests"))
```

## Phase 3: Utils Reorganization

### Tasks

1. **Create utils directory structure**
   - Create subdirectories in `/utils`
   - Create necessary `__init__.py` files

2. **Move AI engine code**
   - Move `/utils/ai_engine.py` to `/utils/ai/engine.py`
   - Create provider-specific files if needed
   - Update imports in all files that reference AI engine

3. **Move messaging code**
   - Move `/utils/zmq.py` to `/utils/messaging/zmq.py`
   - Move `/utils/zmq_devices.py` to `/utils/messaging/devices.py`
   - Update imports in all files that reference ZMQ

4. **Move storage code**
   - Move `/utils/storage.py` to `/utils/storage/local.py`
   - Move `/utils/setup_storage.py` to `/utils/storage/setup.py`
   - Update imports in all files that reference storage

5. **Move cloud code**
   - Move `/utils/gcs_config_stash.py` to `/utils/cloud/gcs.py`
   - Move `/utils/secrets.py` to `/utils/cloud/secrets.py`
   - Update imports in all files that reference cloud functions

6. **Move core modules**
   - Move `/utils/logging.py` to `/utils/core/logging.py`
   - Move `/utils/monitoring.py` to `/utils/core/monitoring.py`
   - Update imports in all files that reference these modules

7. **Update __init__.py files**
   - Ensure each `__init__.py` exports the appropriate interfaces
   - Add import aliases for backward compatibility

8. **Add backward compatibility imports**
   - Create imports in old locations that reference new locations
   - Add deprecation warnings

### Scripts

```python
# Script to create utils directory structure
import os
import shutil

# Create directories
dirs = [
    "utils/core",
    "utils/ai",
    "utils/ai/tools",
    "utils/storage",
    "utils/cloud",
    "utils/messaging"
]

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)
    init_file = os.path.join(dir_path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write('"""{}"""\n'.format(dir_path.replace("/", ".") + " package"))
```

## Phase 4: Documentation Standardization

### Tasks

1. **Create documentation templates**
   - Define standard format for module docstrings
   - Define standard format for class docstrings
   - Define standard format for function docstrings

2. **Update docstrings**
   - Update module docstrings to follow template
   - Update class docstrings to follow template
   - Update function docstrings to follow template

3. **Update Sphinx configuration**
   - Update Sphinx configuration to reflect new structure
   - Add appropriate autodoc settings

4. **Update API documentation files**
   - Create new .md files for API documentation
   - Update existing .md files to reference new structure

5. **Generate new documentation**
   - Build documentation with Sphinx
   - Review and fix any issues

### Templates

**Module Docstring Template**:
```python
"""Module Name.

Brief description of module purpose and functionality.

Key Components:
    Component1: Brief description of component
    Component2: Brief description of component

Example:
    >>> from module import Component
    >>> instance = Component()
    >>> result = instance.method()

Note:
    Any important notes or limitations.
"""
```

**Class Docstring Template**:
```python
class ClassName:
    """Brief description of class.

    Detailed description of class purpose and functionality.

    Attributes:
        attribute1: Description of attribute1
        attribute2: Description of attribute2

    Example:
        >>> instance = ClassName()
        >>> result = instance.method()
    """
```

**Function Docstring Template**:
```python
def function_name(param1, param2):
    """Brief description of function.

    Detailed description of function purpose and functionality.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: Description of when exception is raised

    Example:
        >>> result = function_name("value", 123)
    """
```

## Phase 5: Development Environment Improvement

### Tasks

1. **Create setup directory**
   - Create `/setup` directory and subdirectories
   - Create necessary files for setup scripts

2. **Split requirements**
   - Create `/setup/requirements/base.txt` for core dependencies
   - Create `/setup/requirements/dev.txt` for development dependencies
   - Create `/setup/requirements/prod.txt` for production dependencies

3. **Create setup scripts**
   - Create `setup/dev_setup.py` for development environment setup
   - Create `setup/ci_setup.py` for CI environment setup

4. **Update Makefile**
   - Update Makefile targets for new structure
   - Add new targets for common tasks

### Example Files

**setup/requirements/base.txt**:
```
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-cov>=4.1.0
pydantic>=2.0.0
pydantic-ai>=0.1.0
```

**setup/requirements/dev.txt**:
```
-r base.txt
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
sphinx>=7.0.0
```

**setup/requirements/prod.txt**:
```
-r base.txt
gunicorn>=21.0.0
uvicorn>=0.23.0
```

## Change Management

For each phase:

1. Create a feature branch
   ```bash
   git checkout -b phase-1-schema-reorganization
   ```

2. Make required changes
   ```bash
   # Run the scripts to create directory structure
   python scripts/create_schema_dirs.py
   
   # Make the required changes
   # Move files, update imports, etc.
   ```

3. Run tests
   ```bash
   make test
   ```

4. Update documentation
   ```bash
   make docs
   ```

5. Create a pull request
   ```bash
   git push origin phase-1-schema-reorganization
   # Create PR on GitHub
   ```

6. Review and merge
   ```bash
   # After review approvals
   git checkout main
   git pull
   ```

## Testing After Changes

```bash
# Run unit tests
make test-unit

# Run integration tests
make test-integration

# Run full test suite
make test

# Run tests with coverage
make coverage
```

## Rollback Procedures

If problems are encountered:

1. Revert changes to last known good state
   ```bash
   git checkout <previous-commit>
   ```

2. Run tests to verify rollback was successful
   ```bash
   make test
   ```

3. Create a new branch with fixes
   ```bash
   git checkout -b fix-phase-1-issues
   ```

4. Apply fixes and proceed as normal

## Conclusion

This implementation plan provides a detailed roadmap for reorganizing the repository structure. By following this plan, we can systematically improve the organization, maintainability, and developer experience of the repository.
