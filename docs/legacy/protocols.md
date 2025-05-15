# Protocol Integrations for Agent Communication

This document outlines a structured plan to integrate multiple communication protocols into the agent development template, enhancing its versatility for various agent scenarios.

---

## Supported Protocols

The template will support the following protocols for agent communication:

- **Agent Protocol (LangChainAI):**  
  Standardizes agent client-server interactions using HTTP and JSON.  
  - [Agent Protocol Spec](https://github.com/langchain-ai/agent-protocol)
  - [Agent Protocol Python SDK](https://github.com/langchain-ai/agent-protocol/tree/main/python)
  - [Agent Protocol API Reference](https://langchain-ai.github.io/agent-protocol/api)
  - [LangChain Integration Example](https://python.langchain.com/docs/integrations/agent_toolkits/agent_protocol)

- **WebSockets:**  
  Enables full-duplex, real-time, bidirectional communication.  
  - [WebSocket Protocol RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)
  - [WebSocket API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
  - [WebSocket Protocol Overview](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers)
  - [websockets Python Library](https://websockets.readthedocs.io/)
  - [asyncio websockets Tutorial](https://websockets.readthedocs.io/en/stable/intro/tutorial1.html)

- **Server-Sent Events (SSE):**  
  Provides server-to-client streaming over HTTP for real-time updates.  
  - [SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
  - [SSE Overview (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
  - [SSE Guide (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
  - [aiohttp SSE Implementation](https://docs.aiohttp.org/en/stable/web_advanced.html#server-sent-events)
  - [FastAPI SSE Support](https://fastapi.tiangolo.com/advanced/custom-response/#server-sent-events)
  - [sse-starlette Library](https://github.com/sysid/sse-starlette)

- **JSON-RPC:**  
  Lightweight remote procedure call protocol using JSON over HTTP or WebSocket.  
  - [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
  - [JSON-RPC Wiki](https://en.wikipedia.org/wiki/JSON-RPC)
  - [jsonrpcclient Python Library](https://jsonrpcclient.readthedocs.io/)
  - [jsonrpcserver Python Library](https://jsonrpcserver.readthedocs.io/)
  - [JSON-RPC vs REST Comparison](https://www.alexhudson.com/2011/06/15/json-rpc-vs-rest/)
  - [Python-JSONRPC Implementation](https://github.com/pavlov99/json-rpc)

- **Protocol Buffers (protobuf):**  
  Efficient binary serialization for high-performance, strongly-typed messaging (future/optional, for advanced use cases).  
  - [Protocol Buffers Documentation](https://protobuf.dev/)
  - [Protocol Buffers Overview](https://developers.google.com/protocol-buffers)
  - [Protocol Buffers Reference](https://protobuf.dev/reference/)
  - [Protocol Buffer Techniques](https://protobuf.dev/programming-guides/techniques/)
  - [Protocol Buffers Encoding](https://protobuf.dev/programming-guides/encoding/)
  - [protobuf Python Tutorial](https://protobuf.dev/getting-started/pythontutorial/)
  - [protobuf Python API](https://googleapis.dev/python/protobuf/latest/index.html)
  - [gRPC Python Tutorial](https://grpc.io/docs/languages/python/basics/)
  - [gRPC Python Quickstart](https://grpc.io/docs/languages/python/quickstart/)
  - [gRPC Python API](https://grpc.github.io/grpc/python/grpc.html)

---

## General Strategy

- **Modularity:** Each protocol is implemented in its own module within `utils/messaging/`.
- **Schemas:** Protocol-specific Pydantic models reside in `schemas/messaging/`. For protobuf, `.proto` files and generated Python classes will be placed in `schemas/messaging/protobuf/`.
- **Abstraction:** Provide both client and (where appropriate) server abstractions.
- **Configuration:** Components are configurable (e.g., endpoints, ports).
- **Async Support:** Use `async`/`await` for I/O-bound operations.
- **Testing:** Implement unit and integration tests for each protocol.
- **Documentation:** Add Sphinx-style docstrings and update the `docs/` directory.
- **Examples:** Provide usage examples in the `examples/` directory.

---

## 1. Agent Protocol (LangChainAI)

**Purpose:** Standardizes client-server interaction for agent systems using HTTP and JSON.

- **Docs:** 
  - [Agent Protocol Spec](https://github.com/langchain-ai/agent-protocol)
  - [Agent Protocol API Reference](https://langchain-ai.github.io/agent-protocol/api)
- **Python SDK:** 
  - [Agent Protocol Python SDK](https://github.com/langchain-ai/agent-protocol/tree/main/python)
  - [LangChain Integration](https://python.langchain.com/docs/integrations/agent_toolkits/agent_protocol)

### Implementation Plan

- **Schemas:**
  - Review the [LangChainAI Agent Protocol](https://github.com/langchain-ai/agent-protocol) specification.
  - Implement Pydantic models in `schemas/messaging/agent_protocol.py`:
    - `TaskRequestBody`, `StepRequestBody`, `Artifact`, `Task`, `Step`, etc.

- **Client:**
  - Create `utils/messaging/agent_protocol_client.py`.
  - Implement `AgentProtocolClient` with methods:
    - `create_task`, `execute_step`, `upload_artifact`, etc.
  - Use `httpx` for HTTP communication.
  - Handle protocol-specific errors.

- **Server (Optional/Future):**
  - Consider a server stub in `utils/messaging/agent_protocol_server.py` for exposing compliant agents.

- **Configuration:**
  - Allow setting the agent server base URL.

- **Testing:**
  - Unit tests for schemas and client methods (mock HTTP).
  - Integration tests with a mock or public Agent Protocol server.

- **Documentation & Examples:**
  - Sphinx docstrings for all classes/methods.
  - Example usage in `examples/`.

---

## 2. WebSockets

**Purpose:** Enables full-duplex, real-time, bidirectional communication.

- **Docs:** 
  - [WebSocket Protocol RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)
  - [WebSocket API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
  - [WebSocket Protocol Overview (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers)
- **Python Libraries:**
  - [websockets Python Library](https://websockets.readthedocs.io/)
  - [websockets API Reference](https://websockets.readthedocs.io/en/stable/reference/index.html)
  - [asyncio websockets Tutorial](https://websockets.readthedocs.io/en/stable/intro/tutorial1.html)

### Implementation Plan

- **Library:** Use the [`websockets`](https://websockets.readthedocs.io/) library.

- **Schemas:**
  - Define message envelope models in `schemas/messaging/websockets.py` if a standard format is needed.

- **Client:**
  - Create `utils/messaging/websocket_client.py`.
  - Implement `WebSocketClient` with:
    - `connect`, `send`, `receive`, `disconnect`
    - Support for JSON-serialized Pydantic models or raw payloads.
    - Automatic reconnection strategies.

- **Server:**
  - Create `utils/messaging/websocket_server.py`.
  - Implement `WebSocketServer` base class:
    - Manages connections and provides hooks: `on_connect`, `on_message`, `on_disconnect`.

- **Configuration:**
  - Client: WebSocket URI.
  - Server: Host, port.

- **Testing:**
  - Unit tests for client/server logic.
  - Integration tests for message exchange.

- **Documentation & Examples:**
  - Sphinx docstrings.
  - Example: simple chat or real-time data feed in `examples/`.

---

## 3. Server-Sent Events (SSE)

**Purpose:** Server-to-client streaming over HTTP for real-time updates.

- **Docs:** 
  - [SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
  - [SSE Overview (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
  - [SSE Guide (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- **Python Libraries:**  
  - [aiohttp SSE Implementation](https://docs.aiohttp.org/en/stable/web_advanced.html#server-sent-events)
  - [FastAPI SSE Support](https://fastapi.tiangolo.com/advanced/custom-response/#server-sent-events)
  - [sse-starlette Library](https://github.com/sysid/sse-starlette)

### Implementation Plan

- **Library:**
  - Client: Use `httpx` for SSE streams.
  - Server: Use FastAPI/Starlette or `aiohttp` for SSE endpoints.

- **Schemas:**
  - Define event models in `schemas/messaging/sse.py` (e.g., `id`, `event`, `data`).

- **Client:**
  - Create `utils/messaging/sse_client.py`.
  - Implement `SSEClient`:
    - Connects to SSE endpoint, parses events, dispatches via callbacks or async generator.
    - Handles reconnection.

- **Server:**
  - Create `utils/messaging/sse_server.py`.
  - Implement an `EventSource` or similar class to manage event queues and connections.

- **Configuration:**
  - Client: SSE endpoint URL.
  - Server: Endpoint path, CORS settings.

- **Testing:**
  - Unit tests for event parsing and generation.
  - Integration tests for streaming updates.

- **Documentation & Examples:**
  - Sphinx docstrings.
  - Example: live log/status updates in `examples/`.

---

## 4. JSON-RPC

**Purpose:** Lightweight remote procedure calls using JSON over HTTP or WebSocket.

- **Docs:** 
  - [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
  - [JSON-RPC Wiki](https://en.wikipedia.org/wiki/JSON-RPC)
  - [JSON-RPC vs REST Comparison](https://www.alexhudson.com/2011/06/15/json-rpc-vs-rest/)
- **Python Libraries:**  
  - [jsonrpcclient Python Library](https://jsonrpcclient.readthedocs.io/)
  - [jsonrpcserver Python Library](https://jsonrpcserver.readthedocs.io/)
  - [Python-JSONRPC Implementation](https://github.com/pavlov99/json-rpc)

### Implementation Plan

- **Library:** Use [`jsonrpcclient`](https://jsonrpcclient.readthedocs.io/) and [`jsonrpcserver`](https://jsonrpcserver.readthedocs.io/) or a custom implementation.

- **Schemas:**
  - Define models in `schemas/messaging/json_rpc.py`:
    - `JsonRpcRequest`, `JsonRpcResponse`, error/result structures.

- **Client:**
  - Create `utils/messaging/json_rpc_client.py`.
  - Implement `JsonRpcClient`:
    - Accepts a transport (HTTP/WebSocket).
    - Method: `call(method_name, **params)`.
    - Handles serialization, deserialization, error handling.

- **Server:**
  - Create `utils/messaging/json_rpc_server.py`.
  - Implement `JsonRpcDispatcher` or `JsonRpcServer`:
    - Registers methods, handles incoming requests, dispatches to Python functions.
    - Serializes responses/errors.

- **Transport:**
  - Start with HTTP; add WebSocket support later.

- **Configuration:**
  - Client: RPC endpoint URL.
  - Server: Endpoint path, registered methods.

- **Testing:**
  - Unit tests for schemas, serialization, client/server logic.
  - Integration tests for RPC calls over HTTP.

- **Documentation & Examples:**
  - Sphinx docstrings.
  - Example: exposing and calling remote procedures in `examples/`.

---

## 5. Protocol Buffers (protobuf)

**Purpose:** Efficient, strongly-typed binary serialization for high-performance agent messaging (optional/advanced).

- **Docs:**
  - [Protocol Buffers Documentation](https://protobuf.dev/)
  - [Protocol Buffers Overview](https://developers.google.com/protocol-buffers)
  - [Protocol Buffers Reference](https://protobuf.dev/reference/)
  - [Protocol Buffer Techniques](https://protobuf.dev/programming-guides/techniques/)
  - [Protocol Buffers Encoding](https://protobuf.dev/programming-guides/encoding/)

- **Python Libraries:**  
  - [protobuf Python Tutorial](https://protobuf.dev/getting-started/pythontutorial/)
  - [protobuf Python API](https://googleapis.dev/python/protobuf/latest/index.html)
  - [gRPC Python Tutorial](https://grpc.io/docs/languages/python/basics/)
  - [gRPC Python Quickstart](https://grpc.io/docs/languages/python/quickstart/)
  - [gRPC Python API](https://grpc.github.io/grpc/python/grpc.html)

### Implementation Plan

- **Schemas:**
  - Define `.proto` files in `schemas/messaging/protobuf/`.
  - Generate Python classes using `protoc` or `grpcio-tools`.

- **Client/Server:**
  - Create `utils/messaging/protobuf_client.py` and `protobuf_server.py` as needed.
  - Use `grpc` or other protobuf-compatible libraries for transport.
  - Provide base classes for message serialization/deserialization and service stubs.

- **Configuration:**
  - Support for specifying endpoints, ports, and service definitions.

- **Testing:**
  - Unit tests for serialization/deserialization.
  - Integration tests for client-server communication.

- **Documentation & Examples:**
  - Sphinx docstrings.
  - Example: high-performance agent messaging in `examples/`.

---

## Implementation Steps (for Each Protocol)

1. **Directory & File Creation**
    - `utils/messaging/<protocol>_client.py`
    - `utils/messaging/<protocol>_server.py` (if applicable)
    - `schemas/messaging/<protocol>.py` or `.proto`
    - Test files in `tests/unit/utils/messaging/` and `tests/integration/utils/messaging/`

2. **Schema Definition**
    - Implement Pydantic models or protobuf schemas for protocol messages.

3. **Core Logic**
    - Implement client/server classes.

4. **Init Updates**
    - Add new modules/classes to `__init__.py` in relevant directories.

5. **Testing**
    - Unit tests for core logic and edge cases.
    - Integration tests for client-server interactions.

6. **Documentation**
    - Sphinx-style docstrings for all public classes/methods.

7. **Examples**
    - Add simple, illustrative examples in `examples/`.

8. **Project Documentation**
    - Update guides and API references in `docs/source/`.

---

This plan ensures a modular, extensible, and well-documented approach to supporting multiple agent communication protocols in the template.