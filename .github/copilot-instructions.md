# GitHub Copilot Instructions

## Project Purpose
This repository houses the AILF (AI Liberation Front) Python library - a comprehensive framework for AI agent development. It provides a rich collection of utilities, patterns, and infrastructure components specifically designed to create sophisticated AI agents with:

- Structured LLM interactions via Pydantic models
- Tool registration and management
- Distributed computing via ZeroMQ
- Configurable storage backends
- Comprehensive logging and monitoring
- Secure secret management
- Testing patterns for AI components
- MCP (Model Context Protocol) server implementations
- Agent-to-Agent (A2A) communication patterns

This library provides developers with production-ready components for building sophisticated AI agents that can be easily extended with domain-specific functionality.

## Role and Behavior
- Act as a software engineer specializing in AI agent development
- Provide code suggestions and explanations for agent functionality
- Use Python and Pydantic for type-safe development
- Follow best practices for modular design, error handling, and testing
- Use Sphinx-style docstrings for documentation
- Use Pydantic-AI for structured LLM interactions
- Use a virtual environment or development container for Python projects
- Avoid content that violates copyrights
- Keep responses short and impersonal
- If asked for harmful content, respond with "Sorry, I can't assist with that."

## Current Library Structure

The AILF library is currently in transition from a flat structure to a more organized src-based layout used by many professional Python packages. The current structure is:

```
ailf/                      # Main package (AI Liberation Front library)
├── ailf/                   # Main package implementation
│   ├── __init__.py         # Package initialization
│   ├── cognition/          # AI cognitive capabilities
│   │   └── ...             # Reasoning and thought process models
│   ├── communication/      # Communication modules
│   │   └── ...             # Inter-agent communication protocols
│   ├── feedback/           # Feedback processing
│   │   └── ...             # User and system feedback mechanisms
│   ├── interaction/        # Interaction handling
│   │   └── ...             # User interaction components
│   ├── memory/             # Memory components
│   │   └── ...             # Short and long-term agent memory systems
│   ├── messaging/          # Messaging infrastructure
│   │   └── ...             # Pub/sub and message queue implementations
│   ├── registry_client/    # Registry client
│   │   └── ...             # Service discovery and registration
│   ├── routing/            # Routing functionality
│   │   └── ...             # Message and request routing components
│   ├── schemas/            # AILF-specific schemas
│   │   └── ...             # Pydantic models for all subsystems
│   └── tooling/            # Tool management components
│       └── ...             # Tool registration and execution framework
├── src/                    # Source code in the new src-based layout (preferred for new development)
│   └── ailf/               # The src-based version of the package
│       ├── __init__.py     # Package initialization
│       ├── agent/          # Core agent functionality
│       │   └── ...         # Base agent classes and agent factories
│       ├── ai/             # AI-specific functionality
│       │   ├── engine.py   # Enhanced AI engine for model interactions
│       │   └── ...         # Provider-specific adapters and utilities
│       ├── cloud/          # Cloud service integrations
│       │   ├── gcp.py      # Google Cloud Platform integrations
│       │   └── ...         # AWS, Azure, etc. integration components
│       ├── core/           # Core utilities
│       │   ├── logging.py  # Enhanced logging with context tracking
│       │   └── ...         # Error handling and monitoring components
│       ├── messaging/      # Messaging infrastructure
│       │   ├── zmq.py      # ZeroMQ based messaging
│       │   └── ...         # Kafka, RabbitMQ, etc. implementations
│       ├── schemas/        # Data models
│       │   └── ...         # Pydantic models for all components
│       └── storage/        # Storage implementations
│           ├── local.py    # Local file system storage
│           └── ...         # Cloud storage adapters
├── utils/                  # Legacy utilities (being migrated to src/ailf/)
│   ├── __init__.py
│   ├── ai/                 # AI-related functionality
│   │   ├── engine.py       # Core AI engine
│   │   └── ...             # AI tools and utilities
│   ├── core/               # Core functionality
│   │   ├── logging.py      # Centralized logging
│   │   ├── monitoring.py   # Instrumentation and metrics
│   │   └── ...             # Base utilities
│   ├── cloud/              # Cloud integrations
│   │   └── ...             # Cloud-specific adapters
│   ├── messaging/          # Messaging modules
│   │   └── ...             # Communication components
│   └── storage/            # Storage implementations
│       └── ...             # Storage adapters
├── schemas/                # Legacy schema definitions (being migrated to src/ailf/schemas/)
│   ├── __init__.py
│   ├── ai.py               # AI-related schemas
│   ├── mcp.py              # MCP protocol schemas
│   ├── storage.py          # Storage-related schemas
│   └── ...                 # Other schema definitions
├── examples/               # Example agent implementations
│   ├── simple_agent.py     # Basic agent example
│   ├── distributed_agents.py # Multi-agent system example
│   └── ...                 # Other example implementations
├── tests/                  # Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py         # Common test fixtures
│   ├── unit/               # Unit tests for all components
│   │   └── ...             # Component-specific tests
│   └── integration/        # Integration tests
│       └── ...             # End-to-end and integration tests
├── docs/                   # Library documentation
│   ├── ...                 # User guides and API references
│   └── updated_project_instructions.md # This guide
└── setup/                  # Additional setup scripts and requirements
    ├── __init__.py
    └── requirements/       # Split requirements files
        ├── base.txt        # Core dependencies
        ├── dev.txt         # Development dependencies
        └── prod.txt        # Production dependencies
```

> **Note**: The library is transitioning toward consolidating all functionality under the `src/ailf` package with a standard Python src-based layout. For any new development, add code to the appropriate `src/ailf/` subdirectory, not to the legacy top-level `utils/` or `schemas/` directories. This transition enhances the library's compatibility with standard Python packaging practices.

## Import Patterns

Current import patterns in the library vary due to the ongoing transition to the src-based layout:

- Legacy imports (being phased out)
- Recommended imports for internal development
- Recommended imports for external packages using the published library

## Modular Agent Development Patterns

### 1. Inheritance-Friendly Design Pattern

Utility classes are designed to support inheritance for customization:

- Protected Extension Points: Methods prefixed with `_` that subclasses can override
- Clear Documentation: Extension points are documented with override instructions
- Sensible Defaults: Base implementations provide reasonable defaults
- Composition Over Inheritance: Use dependency injection for maximum flexibility

### 2. Agent Architecture Pattern

Implement agents following a modular architecture:

- Core Engine: Central decision-making component
- Tools Registry: Mechanism for registering and discovering tools
- Adapters: Interfaces to different LLM providers
- Schema Validation: Input/output validation with Pydantic
- Persistent Context: Memory and state management

### 3. Type-Safe Development with Pydantic

Use Pydantic models for type safety and data validation:

- Schema-First Design: Define data models before implementing functionality
- Validation at Boundaries: Validate all external data at system boundaries
- Model Categories: Organize models by their purpose (input, output, domain, etc.)
- Common Fields: Use consistent field names and types across models
- Enum Types: Use enums for fields with predefined options

### 4. Comprehensive Documentation

Use Sphinx-style docstrings for consistent documentation:

- Module Docstrings: Include summary, detailed description, components, and examples
- Class/Function Docstrings: Document purpose, parameters, returns, raises, and examples
- Type Hints: Include type annotations and document them in docstrings
- Examples: Provide usage examples in docstring format

### 5. Error Handling and Logging

Implement consistent error handling and logging:

- Centralized Logger: Use a factory function for consistent logger setup
- Error Categories: Group errors by type (user input, system, external)
- Context Preservation: Include relevant context in error logs
- Graceful Degradation: Implement fallbacks for non-critical failures
- Monitoring Integration: Log metrics for important operations

### 6. Dependency Injection

Use dependency injection for testable, modular code:

- Constructor Injection: Pass dependencies in class constructors
- Default Implementation: Provide sensible defaults for common dependencies
- Interface Adherence: Ensure all implementations follow the same interface
- Configuration Separation: Keep configuration separate from business logic

### 7. Testing Patterns

Implement comprehensive test coverage:

- Unit Tests: Test individual components in isolation
- Integration Tests: Test interactions between components
- End-to-End Tests: Test complete workflows
- Test Fixtures: Create reusable test data and mocks
- Parameterized Tests: Test multiple input variations efficiently

### 8. MCP Server Implementation Best Practices

Follow these patterns when implementing Model Context Protocol servers:

- Server Lifecycle Management: Use async context managers for clean server initialization and teardown
- Tool Registration: Register tools using decorator pattern with clear type hints
- Resource Templating: Define resource templates with consistent URI patterns
- Error Handling: Map internal errors to MCP protocol error responses
- Context Object Pattern: Use context objects to pass request state between components

### 9. Library Development and Contribution

This library supports multiple development environments to accommodate different workflows:

#### Option 1: Development Container (Recommended)

Our recommended approach for library development is to use the provided development container.

#### Option 2: Virtual Environment

Alternatively, use a Python virtual environment.

### Library Dependencies

The library is modularized with core and optional dependencies:

#### Core Dependencies
- pydantic>=2.7.2 - Data validation and settings management
- python-dotenv>=1.0.0 - Load environment variables from .env files

#### AI Module Dependencies (Optional)
- anthropic>=0.50.0 - Anthropic Claude models integration
- openai>=1.77.0 - OpenAI GPT models integration
- google-generativeai>=0.8.5 - Google Gemini models integration
- pydantic-ai>=0.1.9 - Pydantic integration for AI models

#### MCP Dependencies (Optional)
- mcp>=1.7.1 - Model Context Protocol implementation

#### Development Dependencies
- pytest - Testing framework
- pytest-cov - Coverage reporting
- flake8 - Linting
- mypy - Type checking

To install the library with all dependencies:
- Install with all optional features
- Or install with specific optional feature sets
- Install development dependencies

### Authentication Notes

All Google Cloud Platform (GCP) integrations use Application Default Credentials (ADC):
- GCS operations in storage.py
- Cloud SQL connections in database.py
- Local setup: Run `gcloud auth application-default login`
````
