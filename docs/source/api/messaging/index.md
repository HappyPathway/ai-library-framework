# Messaging Components

This section documents the messaging components of the AILF library.

```{toctree}
:maxdepth: 2

agent_protocol
agent_protocol_client
async_redis
devices
mock_redis
protobuf/index
redis
websocket_client
websocket_server
websockets
zmq
zmq_device_manager
zmq_devices
```

The messaging module provides components for inter-agent and system-to-system communication.

## Key Components

- **ZeroMQ**: Low-latency messaging between components
- **Redis**: Pub/sub and data storage
- **Websockets**: Real-time web communication
- **Protocol Buffers**: Efficient binary serialization
- **Agent Protocol**: A2A and ACP compatible client implementations
