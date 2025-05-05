# Agent Capabilities Map

This document provides a high-level overview of the capabilities available in the template-python-dev repository, organized by functional area. Use this as a quick reference to locate specific functionality within the codebase.

## AI/LLM Integration

| Capability | Module | Description |
|------------|--------|-------------|
| Text Generation | `utils.ai_engine` | Core text generation with multiple provider support (OpenAI, Anthropic, Google) |
| Structured Output | `utils.schemas.ai` | Pydantic models for structured LLM outputs |
| Content Analysis | `utils.ai_engine` | Content analysis with various analysis types |
| Classification | `utils.ai_engine` | Classification of text into predefined categories |
| MCP Integration | `utils.base_mcp` | Model Context Protocol server implementation |

## Messaging & Communication

| Capability | Module | Description |
|------------|--------|-------------|
| ZeroMQ Messaging | `utils.zmq` | High-performance messaging using ZeroMQ |
| ZMQ Patterns | `utils.zmq_devices` | Implementation of common ZMQ patterns (pub/sub, push/pull, etc.) |
| Redis PubSub | `utils.messaging.redis` | Real-time messaging with Redis Pub/Sub |
| Redis Streams | `utils.messaging.redis` | Persistent, ordered message processing with Redis Streams |
| Distributed Coordination | `utils.messaging.redis` | Locks, rate limiting, and synchronization primitives |

## Task Processing

| Capability | Module | Description |
|------------|--------|-------------|
| Async Task Management | `utils.async_tasks` | AsyncIO-based task management, tracking, and coordination |
| Distributed Tasks | `utils.workers.celery_app` | Distributed task processing with Celery |
| Task State Management | `utils.workers.tasks` | Task status tracking and error handling |
| Task Progress Updates | `utils.async_tasks` | Real-time progress tracking for long-running tasks |
| Task Monitoring | `utils.monitoring` | Performance monitoring and instrumentation |

## Storage & Data Management

| Capability | Module | Description |
|------------|--------|-------------|
| Local Storage | `utils.storage` | Local file system storage operations |
| Google Cloud Storage | `utils.storage` | Cloud storage with GCS integration |
| Database Operations | `utils.database` | Database connection and session management |
| JSON Document Storage | `utils.storage` | JSON document storage and retrieval |
| Schema Validation | `utils.schemas.*` | Pydantic models for data validation |

## Authentication & Security

| Capability | Module | Description |
|------------|--------|-------------|
| Secret Management | `utils.secrets` | Secure secrets management with Google Secret Manager |
| GitHub Authentication | `utils.github_client` | GitHub API authentication |
| GCP Authentication | `utils.gcs_config_stash` | Google Cloud authentication |
| Redis Security | `utils.messaging.redis` | Secure Redis connection handling |

## Operational Support

| Capability | Module | Description |
|------------|--------|-------------|
| Logging | `utils.logging` | Centralized, configurable logging |
| Monitoring | `utils.monitoring` | Performance metrics and instrumentation |
| Error Handling | Various modules | Standardized error handling patterns |
| Web Scraping | `utils.web_scraper` | Rate-limited, respectful web content retrieval |

## Integration Patterns

| Pattern | Example | Description |
|---------|---------|-------------|
| AsyncIO + Redis | `examples.async_redis_celery_example` | Combining AsyncIO with Redis messaging |
| AsyncIO + Celery | `examples.async_redis_celery_example` | Using AsyncIO to coordinate Celery tasks |
| MCP + AsyncIO | `examples.mcp_async_redis_example` | MCP server with AsyncIO task management |
| Multi-Protocol Agent | `examples.multi_protocol_agent` | Agent supporting multiple messaging protocols |
| Distributed Processing | `examples.integrated_agent_system` | Fully integrated system with multiple components |

## Extension Points

The following modules provide clear extension points through inheritance:

| Module | Extension Points | Purpose |
|--------|------------------|---------|
| `utils.ai_engine` | `_setup_provider`, `_get_provider_settings` | Customize AI provider handling |
| `utils.storage` | `_get_default_dirs`, `_ensure_dir_exists` | Customize storage structure |
| `utils.zmq` | `_create_socket`, `_handle_recv` | Custom ZeroMQ behaviors |
| `utils.base_mcp` | `_setup`, `_process_message` | MCP server customization |
| `utils.async_tasks` | `_cleanup_completed` | Custom task cleanup logic |
