# AILF (AI Liberation Front) Documentation

Welcome to the AILF documentation. This project provides a comprehensive framework for AI agent development with structured components and utilities.

## Getting Started

To get started with this framework, check out the [Development Setup Guide](guides/development_setup.md) for instructions on how to install and configure your environment.

## Key Components

This project includes several core components for AI agent development:

- **AI Engine**: Unified AI/LLM interaction interface with multiple provider support
- **Agent Framework**: Base classes and patterns for building intelligent agents
- **Messaging**: Inter-agent communication via ZMQ and Redis
- **Storage**: Local and cloud storage management
- **MCP**: Model Context Protocol server implementations
- **Tools**: Registration and execution framework for agent capabilities
- **Schemas**: Pydantic models for structured data validation
- **Logging**: Contextual logging with tracing
- **Monitoring**: Performance and error tracking
- **Secrets**: Secure secrets management with Google Secret Manager
- **Cloud Integration**: Google Cloud and other provider integrations

## Project Documentation

```{toctree}
:maxdepth: 2
:caption: Project Reference

documentation_transition_plan
doc_transition_plan
migration_plan
ai_module_example
implementation_plan
migration_guide
capabilities_map
component_relationships
```

## Examples

```{toctree}
:maxdepth: 2
:caption: Examples

examples/direct_agent_example
```

## User Guides

```{toctree}
:maxdepth: 2
:caption: User Guides

guides/development_setup
guides/src_structure
guides/documentation_structure
guides/import_patterns
guides/handling_unused_imports
guides/contributing_docs
guides/ci_integration
guides/testing
guides/logging
guides/redis_messaging
guides/messaging
guides/redis
guides/async_tasks
guides/celery
```

## API Documentation

```{toctree}
:maxdepth: 2
:caption: API Reference

api_organization
api/index
```

## Legacy Category Pages

```{toctree}
:maxdepth: 1
:caption: Legacy Category Pages

api/ai
api/cloud
api/core
api/mcp
api/mcp/servers
api/messaging
api/storage
api/workers
```

## Indices and Tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
