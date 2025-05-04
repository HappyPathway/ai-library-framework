# GitHub Copilot Instructions

## Project Purpose
This repository serves as a template for Python-based agent development projects. It provides a collection of utilities, patterns, and infrastructure components specifically designed to accelerate the development of AI agents with:

- Structured LLM interactions via Pydantic models
- Tool registration and management
- Distributed computing via ZeroMQ
- Configurable storage backends
- Comprehensive logging and monitoring
- Secure secret management
- Testing patterns for AI components

The template is intended to provide developers with a solid foundation for building sophisticated AI agents that can be easily extended with domain-specific functionality.

## Role and Behavior
- Act as a software engineer specializing in AI agent development
- Provide code suggestions and explanations for agent functionality
- Use Python and Pydantic for type-safe development
- Follow best practices for modular design, error handling, and testing
- Use Sphinx-style docstrings for documentation
- Use Pydantic-AI for structured LLM interactions
- Use a virtual environment for Python projects
- Avoid content that violates copyrights
- Keep responses short and impersonal
- If asked for harmful content, respond with "Sorry, I can't assist with that."

## Recommended Project Structure

The project should follow this structure for clarity and maintainability:

```
template-python-dev/
├── agent/                      # Core agent functionality (future feature)
├── utils/                      # Core utilities
│   ├── __init__.py
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── logging.py          # Centralized logging configuration
│   │   └── monitoring.py       # Instrumentation and metrics
│   ├── ai/                     # AI-related functionality
│   │   ├── __init__.py
│   │   ├── engine.py           # Core AI engine (refactored from ai_engine.py)
│   │   └── tools/              # AI tools implementations
│   ├── storage/                # Storage-related functionality
│   │   ├── __init__.py
│   │   ├── local.py            # Local storage implementation
│   │   └── setup.py            # Storage setup functionality
│   ├── cloud/                  # Cloud-related functionality
│   │   ├── __init__.py
│   │   ├── gcs.py              # GCS operations
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
├── examples/                   # Example agent implementations
│   ├── simple_agent.py
│   ├── distributed_agents.py
│   └── specialized/            # Domain-specific examples
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
├── setup/                      # Development environment setup
│   ├── __init__.py
│   ├── dev_setup.py            # Development environment setup
│   └── requirements/           # Split requirements files
│       ├── base.txt            # Core dependencies
│       ├── dev.txt             # Development dependencies
│       └── prod.txt            # Production dependencies
└── docs/                       # Documentation
    ├── Makefile                # For building docs
    ├── source/                 # All source documentation
    │   ├── conf.py             # Sphinx configuration
    │   ├── index.md            # Main landing page
    │   ├── guides/             # User guides and tutorials
    │   │   └── logging.md      # Guide for using the logging module
    │   ├── api/                # API reference documentation
    │   │   ├── logging.md      # Auto-generated API reference for logging
    │   │   └── ...             # Other API references
    │   └── _static/            # Static assets for documentation
    └── build/                  # Generated output (not in version control)
        └── html/               # HTML documentation output
```

## Code Change Instructions

When suggesting code changes:

1. Describe changes step by step
2. Group changes by file
3. For each file:
   - Show filepath and summary
   - Provide code in language-specific block
   - Use comments for unchanged sections

### Example Format

```python
# filepath: /path/to/file.py
# ...existing code...
def new_function():
    pass
# ...existing code...
```

# Modular Agent Development Patterns

## 1. Inheritance-Friendly Design Pattern

Utility classes are designed to support inheritance for customization:

- **Protected Extension Points**: Methods prefixed with `_` that subclasses can override
- **Clear Documentation**: Extension points are documented with override instructions
- **Sensible Defaults**: Base implementations provide reasonable defaults
- **Composition Over Inheritance**: Use dependency injection for maximum flexibility

Example extending AI Engine:
```python
from utils.ai_engine import AIEngine

class CustomAIEngine(AIEngine):
    """Custom AI engine with specialized behavior."""
    
    def _setup_instrumentation(self):
        """Override to use custom instrumentation."""
        # Custom instrumentation logic
        return MyCustomInstrumentation()
    
    def _get_provider_settings(self):
        """Override to customize provider settings."""
        base_settings = super()._get_provider_settings()
        # Add custom settings
        return base_settings
        
    async def specialized_analysis(self, content, **kwargs):
        """Add new domain-specific methods."""
        # Custom implementation
        return await self.analyze(content, **kwargs)
```

Example extending Storage:
```python
from utils.storage import LocalStorage

class S3BackedStorage(LocalStorage):
    """Storage implementation with S3 backup capabilities."""
    
    def __init__(self, bucket_name, local_path=None):
        """Initialize with S3 bucket and optional local path."""
        super().__init__(local_path)
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3')
    
    def _get_default_dirs(self):
        """Override to customize directory structure."""
        dirs = super()._get_default_dirs()
        dirs.extend(['synced', 'backups'])
        return dirs
        
    async def save_json(self, data, path, backup=True):
        """Override to add S3 backup functionality."""
        # Save locally first
        local_path = super().save_json(data, path)
        
        # Backup to S3 if requested
        if backup:
            self.s3_client.upload_file(local_path, self.bucket_name, path)
            
        return local_path
```

## 2. Agent Architecture Pattern

Implement agents following a modular architecture:

- **Core Engine**: Central decision-making component
- **Tools Registry**: Mechanism for registering and discovering tools
- **Adapters**: Interfaces to different LLM providers
- **Schema Validation**: Input/output validation with Pydantic
- **Persistent Context**: Memory and state management

Example agent engine structure:
```python
class AIEngine:
    """Core AI agent engine for orchestrating LLM interactions."""
    
    def __init__(self, model_name: str, instructions: str):
        self.model_name = model_name
        self.instructions = instructions
        self.tools = {}
        self.memory = AgentMemory()
        self.adapter = get_model_adapter(model_name)
        
    def add_tool(self, func, name=None, description=None):
        """Register a new tool with the agent."""
        # Tool registration logic
        
    async def generate(self, prompt: str, output_schema: Type[BaseModel] = None):
        """Generate a response using the underlying model."""
        # Generation logic with structured output
│   ├── database.py        # Database connection and session management
│   ├── api_client.py      # Base API client functionality
│   ├── monitoring.py      # Instrumentation and metrics
│   └── schemas.py         # Shared data models
└── features/
    ├── feature_a/
    │   ├── __init__.py
    │   ├── models.py
    │   └── service.py
    └── feature_b/
        ├── __init__.py
        ├── models.py
        └── service.py
```

> Note: All Google Cloud Platform (GCP) integrations in utils modules use Application Default Credentials (ADC). 
> This includes storage.py for GCS operations and database.py for Cloud SQL connections.
> Local development setup requires running `gcloud auth application-default login`.

### 1. Modular utils Library Pattern

Maintain a central `utils` module with reusable building blocks:

- **Abstraction First**: Create abstractions for common functionality (logging, storage, API clients)
- **Composition Over Inheritance**: Build features by composing utils components, not through complex inheritance
- **Single Responsibility**: Each utils module should have a clearly defined purpose and responsibility

Example directory structure:
```
project/
├── utils/
│   ├── __init__.py
│   ├── logging.py         # Centralized logging configuration
│   ├── storage.py         # Storage abstractions (cloud, local, etc.)
│   ├── database.py        # Database connection and session management
│   ├── api_client.py      # Base API client functionality
│   ├── monitoring.py      # Instrumentation and metrics
│   └── schemas.py         # Shared data models
└── features/
    ├── feature_a/
    │   ├── __init__.py
    │   ├── models.py
    │   └── service.py
    └── feature_b/
        ├── __init__.py
        ├── models.py
        └── service.py
```

### 2. Type-Safe Development with Pydantic

Use Pydantic models for type safety and data validation:

- **Schema-First Design**: Define data models before implementing functionality
- **Validation at Boundaries**: Validate all external data at system boundaries
- **Model Categories**: Organize models by their purpose (input, output, domain, etc.)
- **Common Fields**: Use consistent field names and types across models
- **Enum Types**: Use enums for fields with predefined options

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class StatusType(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    ARCHIVED = "archived"

class UserProfile(BaseModel):
    """User profile data model."""
    user_id: str
    name: str
    email: str
    status: StatusType = StatusType.PENDING
    tags: List[str] = Field(default_factory=list)
    preferences: Optional[dict] = None
```

### 3. Comprehensive Documentation

Use Sphinx-style docstrings for consistent documentation:

- **Module Docstrings**: Include summary, detailed description, components, and examples
- **Class/Function Docstrings**: Document purpose, parameters, returns, raises, and examples
- **Type Hints**: Include type annotations and document them in docstrings
- **Examples**: Provide usage examples in docstring format

Example module docstring:
```python
"""Storage Management Module.

This module provides a unified interface for file storage operations with support
for both local and cloud storage backends.

Key Components:
    StorageManager: Base class for storage operations
    LocalStorage: File system implementation
    CloudStorage: Cloud storage implementation

Example:
    >>> from utils.storage import CloudStorage
    >>> storage = CloudStorage(bucket="my-app-data")
    >>> storage.save_json(data, "user_profiles/user123.json")

Note:
    Use this module for all file storage operations to ensure consistency.
"""
```

Example function docstring:
```python
def save_document(document: dict, path: str) -> bool:
    """Save a document to the configured storage.

    :param document: The document data to save
    :type document: dict
    :param path: The storage path where the document will be saved
    :type path: str
    :return: True if saved successfully, False otherwise
    :rtype: bool
    :raises StorageError: If the save operation fails
    :raises ValueError: If the document format is invalid
    
    Example:
        >>> success = save_document({"id": "123", "name": "Test"}, "documents/123.json")
        >>> print(success)
        True
    """
```

Example class docstring:
```python
class StorageManager:
    """Base class for storage operations.
    
    This class defines the interface for storage operations and provides
    common functionality for derived storage implementations.
    
    :param base_path: Base path for storage operations
    :type base_path: str
    :param config: Optional storage configuration
    :type config: dict
    
    Example:
        >>> manager = StorageManager("/data", config={"compress": True})
        >>> manager.save("test.txt", "Hello World")
    """
```

### 4. Error Handling and Logging

Implement consistent error handling and logging:

- **Centralized Logger**: Use a factory function for consistent logger setup
- **Error Categories**: Group errors by type (user input, system, external)
- **Context Preservation**: Include relevant context in error logs
- **Graceful Degradation**: Implement fallbacks for non-critical failures
- **Monitoring Integration**: Log metrics for important operations

```python
from utils.logging import setup_logging

logger = setup_logging("feature_name")

def process_item(item_id: str) -> dict:
    """Process an item with comprehensive error handling."""
    try:
        logger.info(f"Processing item {item_id}")
        # Processing logic...
        return result
    except ValueError as e:
        logger.error(f"Invalid input for item {item_id}: {str(e)}")
        raise InputError(f"Invalid item format: {str(e)}") from e
    except ExternalServiceError as e:
        logger.error(f"External service error while processing {item_id}: {str(e)}")
        monitoring.increment("external_service_errors")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing item {item_id}")
        monitoring.track_error("process_item", str(e))
        raise SystemError(f"Processing failure: {str(e)}") from e
```

### 5. Dependency Injection

Use dependency injection for testable, modular code:

- **Constructor Injection**: Pass dependencies in class constructors
- **Default Implementation**: Provide sensible defaults for common dependencies
- **Interface Adherence**: Ensure all implementations follow the same interface
- **Configuration Separation**: Keep configuration separate from business logic

```python
class UserService:
    def __init__(
        self,
        storage=None,
        notification_service=None,
        logger=None
    ):
        self.storage = storage or DefaultStorage()
        self.notification = notification_service or EmailService()
        self.logger = logger or setup_logging("user_service")
    
    def create_user(self, user_data: dict):
        # Business logic using injected dependencies
        self.storage.save(user_data)
        self.notification.send_welcome(user_data["email"])
        self.logger.info(f"Created user: {user_data['id']}")
```

### 6. Testing Patterns

Implement comprehensive test coverage:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete workflows
- **Test Fixtures**: Create reusable test data and mocks
- **Parameterized Tests**: Test multiple input variations efficiently

```python
class TestUserService:
    @pytest.fixture
    def mock_storage(self):
        return MockStorage()
        
    @pytest.fixture
    def mock_notifications(self):
        return MockNotificationService()
        
    @pytest.fixture
    def service(self, mock_storage, mock_notifications):
        return UserService(
            storage=mock_storage,
            notification_service=mock_notifications
        )
    
    def test_create_user_success(self, service, mock_storage, mock_notifications):
        # Test setup
        user_data = {"id": "123", "email": "test@example.com"}
        
        # Execute
        service.create_user(user_data)
        
        # Assert
        mock_storage.save.assert_called_once_with(user_data)
        mock_notifications.send_welcome.assert_called_once_with("test@example.com")

    @pytest.mark.parametrize("invalid_input,expected_error", [
        ({"email": "test@example.com"}, "Missing id"),
        ({"id": "123"}, "Missing email"),
    ])
    def test_create_user_validation(self, service, invalid_input, expected_error):
        with pytest.raises(ValueError, match=expected_error):
            service.create_user(invalid_input)
```

### 7. Monitoring and Instrumentation

Implement systematic monitoring:

- **Success/Failure Metrics**: Track operation outcomes
- **Performance Metrics**: Monitor execution time for key operations
- **Resource Usage**: Track memory and resource consumption
- **Error Rates**: Monitor errors by category and operation
- **Custom Dimensions**: Add contextual information to metrics

```python
def process_batch(items: list) -> dict:
    """Process a batch of items with monitoring."""
    monitoring.increment("process_batch.started")
    start_time = time.time()
    
    try:
        results = []
        success_count = 0
        
        for item in items:
            try:
                result = process_item(item)
                results.append(result)
                success_count += 1
            except Exception as e:
                logger.error(f"Item processing failed: {str(e)}")
                monitoring.track_error("process_item", str(e))
        
        elapsed = time.time() - start_time
        monitoring.track_latency("process_batch", elapsed)
        monitoring.track_success("process_batch", {
            "total": len(items),
            "success": success_count,
            "failure": len(items) - success_count
        })
        
        return {
            "success_count": success_count,
            "failure_count": len(items) - success_count,
            "results": results
        }
        
    except Exception as e:
        monitoring.track_error("process_batch", str(e))
        raise
```

### 8. Advanced Pydantic Usage Patterns

Leverage Pydantic's advanced features for robust data handling:

- **Model Inheritance**: Use inheritance for model variations with shared fields
- **Generic Models**: Create reusable model templates with type parameters
- **Custom Validators**: Implement field-level and model-level validation logic
- **Config Classes**: Customize model behavior through Config classes
- **Root Validators**: Validate interdependent fields together

```python
from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field, validator, root_validator

T = TypeVar('T')

class PaginatedResponse(Generic[T]):
    """Generic paginated response model."""
    items: List[T]
    page: int = 1
    total_pages: int
    total_items: int
    
    @validator('page')
    def page_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Page must be positive')
        return v
        
    @root_validator
    def check_pagination_consistency(cls, values):
        """Ensure pagination values are consistent."""
        if (
            'total_pages' in values 
            and 'page' in values
            and values['page'] > values['total_pages']
        ):
            raise ValueError('Page number cannot exceed total pages')
        return values
        
    class Config:
        """Model configuration."""
        validate_assignment = True
        extra = 'forbid'
```

### 9. MCP Server Implementation Best Practices

Follow these patterns when implementing Model Context Protocol servers:

- **Server Lifecycle Management**: Use async context managers for clean server initialization and teardown
- **Tool Registration**: Register tools using decorator pattern with clear type hints
- **Resource Templating**: Define resource templates with consistent URI patterns
- **Error Handling**: Map internal errors to MCP protocol error responses
- **Context Object Pattern**: Use context objects to pass request state between components

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
from mcp.server.fastmcp import FastMCP, Context

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Server lifespan context manager."""
    # Initialize services
    search_service = SearchService()
    database = Database()
    
    try:
        # Start services
        await search_service.initialize()
        await database.connect()
        
        # Store services in context
        server.state.search = search_service
        server.state.db = database
        
        yield
    finally:
        # Clean up resources
        await database.disconnect()
        await search_service.shutdown()

# Create server with lifespan
mcp = FastMCP(
    name="Document Search",
    instructions="Search and retrieve documents",
    lifespan=server_lifespan
)

# Tool implementation
@mcp.tool()
async def search_documents(ctx: Context, query: str, limit: int = 10) -> list[dict]:
    """Search for documents matching the query."""
    search_service = ctx.server.state.search
    
    try:
        results = await search_service.search(query, limit=limit)
        return [doc.to_dict() for doc in results]
    except Exception as e:
        # Map to appropriate error response
        raise ctx.error(str(e), code="search_error")
```

### 10. Pydantic-AI Integration Best Practices

Utilize Pydantic-AI for structured LLM interactions:

- **Structured Output Models**: Define clear output models for AI responses
- **AI Agent Lifecycle**: Manage AI agent objects properly with initialization and cleanup
- **Error Handling**: Handle AI-specific errors like rate limits and token limits
- **Consistent Temperature**: Set appropriate temperature values for deterministic vs. creative outputs
- **Context Management**: Provide sufficient context for AI operations

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import List, Optional

class AnalysisResult(BaseModel):
    """Structured analysis result."""
    key_topics: List[str] = Field(description="Main topics identified in content")
    sentiment: str = Field(description="Overall sentiment (positive, negative, neutral)")
    summary: str = Field(description="Brief summary of content")
    action_items: Optional[List[str]] = Field(
        default=None, 
        description="Suggested actions based on content"
    )

class ContentAnalyzer:
    """Content analyzer using AI."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """Initialize analyzer."""
        self.agent = Agent(api_key=api_key, model=model)
        
    async def analyze_content(self, content: str) -> AnalysisResult:
        """Analyze content using AI."""
        try:
            # Provide clear instructions through system prompt
            system_prompt = """
            Analyze the provided content objectively. 
            Extract key topics, determine overall sentiment,
            and provide a concise summary. If applicable,
            suggest action items.
            """
            
            # Use structured output schema
            result = await self.agent.run(
                content,
                output_schema=AnalysisResult,
                system=system_prompt,
                temperature=0.1  # Low temperature for deterministic analysis
            )
            
            return result.output
            
        except Exception as e:
            raise AIError(f"Content analysis failed: {str(e)}")
```

### 11. Using a Virtual Environment and Managing Dependencies

To ensure a clean and isolated Python environment, always use a virtual environment for your project.

#### Setting Up a Virtual Environment

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

3. Upgrade `pip` to the latest version:
   ```bash
   pip install --upgrade pip
   ```

#### Adding Dependencies to `requirements.txt`

1. Install a new dependency:
   ```bash
   pip install <package-name>
   ```

2. Add the installed dependency to `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```

3. Install all dependencies from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. Ensure `requirements.txt` is committed to version control to maintain consistency across environments.

### Core Dependencies

Required packages for development:
- python-dotenv>=1.0.0 - Load environment variables from .env files
- pytest - Testing framework
- pytest-cov - Coverage reporting

To install:
```bash
pip install -r requirements.txt
```

### Authentication Notes

All Google Cloud Platform (GCP) integrations use Application Default Credentials (ADC):
- GCS operations in storage.py
- Cloud SQL connections in database.py
- Local setup: Run `gcloud auth application-default login`

# Extension and Inheritance Patterns

## 1. Inheritance-Friendly Design

Design utilities with clear extension points to support customization:

- **Protected Methods for Extension**: Prefix helper methods with underscore that subclasses can override
- **Clear Documentation**: Document extension points and expected behavior
- **Factory Methods**: Use factory methods that can be overridden to change object creation
- **Well-Defined Interfaces**: Define clear interfaces for subclasses to implement

Example of an inheritance-friendly class structure:

```python
class BaseStorage:
    """Base storage class designed for extension."""
    
    def __init__(self, config=None):
        self.config = config or self._get_default_config()
        self._initialize()
    
    def _get_default_config(self):
        """Override to customize default configuration."""
        return {"compress": False, "encrypt": False}
    
    def _initialize(self):
        """Override to customize initialization logic."""
        pass
        
    def save(self, data, path):
        """High-level save method.
        
        The template method pattern - implements the workflow but delegates
        specific operations to protected methods.
        """
        validated_data = self._validate_data(data)
        processed_data = self._process_data(validated_data)
        return self._perform_save(processed_data, path)
    
    def _validate_data(self, data):
        """Override to customize data validation."""
        return data
        
    def _process_data(self, data):
        """Override to customize data processing."""
        return data
        
    def _perform_save(self, data, path):
        """Override this method to implement the actual save operation."""
        raise NotImplementedError("Subclasses must implement _perform_save")

# Example subclass
class CustomStorage(BaseStorage):
    def _get_default_config(self):
        # Customize default configuration
        config = super()._get_default_config()
        config.update({"compress": True})
        return config
        
    def _process_data(self, data):
        # Add custom compression
        data = super()._process_data(data)
        if self.config["compress"]:
            return self._compress(data)
        return data
        
    def _perform_save(self, data, path):
        # Implement the actual save operation
        # ...
        return True
```
