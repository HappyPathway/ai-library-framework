# AI Liberation Front (ailf)

A comprehensive toolkit for building sophisticated AI agent systems.

## Features

- **Structured LLM Interactions**: Type-safe AI interactions using Pydantic models
- **Tool Registration**: Easy registration of tools for AI agents
- **AI Abstraction Layer**: Support for multiple AI providers (OpenAI, Anthropic, Gemini)
- **MCP Server**: Model Context Protocol server implementation
- **Distributed Computing**: ZeroMQ and Redis messaging patterns
  - **ZMQ Devices**: Forwarder, Streamer, and Queue patterns with device manager
  - **Redis Messaging**: PubSub, Streams, and basic client operations
- **Storage Backends**: Local and cloud storage abstractions
- **Comprehensive Logging**: Centralized logging configuration
- **Secure Secret Management**: Handle credentials and API keys securely

## Requirements

- Python 3.12 or higher
- pip

## Installation

### Basic Installation

Just the core functionality:

```bash
pip install ailf
```

### Installation with Optional Components

With AI provider support (OpenAI, Anthropic, Google Gemini):
```bash
pip install "ailf[ai]"
```

With cloud storage and secrets management:
```bash
pip install "ailf[cloud]"
```

With specific components:
```bash
pip install "ailf[zmq]"      # ZeroMQ messaging
pip install "ailf[redis]"    # Redis messaging
pip install "ailf[mcp]"      # MCP server functionality
```

Full installation with all dependencies:
```bash
pip install "ailf[all]"
```

Development installation:
```bash
pip install "ailf[dev]"
```

### Install with Specific Features

```bash
# For AI functionality
pip install ailf[ai]

# For MCP server functionality
pip install ailf[mcp]

# For Google Cloud integrations
pip install ailf[cloud]

# For Redis messaging
pip install ailf[redis]

# For ZeroMQ messaging
pip install ailf[zmq]

# For full agent development capabilities
pip install ailf[agent]

# For all features
pip install ailf[all]
```

## Quick Start

### Using the AI Engine

```python
from ailf import AIEngine

# Initialize the AI engine
engine = AIEngine(
    feature_name="text_analysis",
    model_name="openai:gpt-4-turbo"
)

# Generate text
result = await engine.generate(
    prompt="Summarize the benefits of AI agents",
    max_tokens=500
)
print(result)
```

### Using Redis Messaging

```python
from ailf import RedisClient, RedisPubSub, RedisStream

# Basic Redis operations
client = RedisClient()
client.set("key", "value")
value = client.get("key")

# PubSub messaging
pubsub = RedisPubSub()
pubsub.publish("channel", {"message": "Hello from AILF!"})

# Subscriber
def handle_message(data):
    print(f"Received: {data}")

subscriber = RedisPubSub()
subscriber.subscribe("channel", handle_message)
subscriber.run_in_thread()

# Redis Streams for reliable messaging
stream = RedisStream("my_stream")
stream.add({"event": "user_signup", "user_id": "123"})

# Consumer group for distributed processing
stream.create_consumer_group("workers", "worker-1")
messages = stream.read_group(count=10)
for message in messages:
    print(f"Processing {message['data']}")
    stream.acknowledge(message['id'])
```

See `/examples/ailf_redis_agents.py` for a complete multi-agent system example using Redis.

### Using ZMQ Device Manager

```python
from ailf import DeviceManager, ZMQPublisher, ZMQSubscriber

# Create a forwarder device (PUB-SUB pattern)
manager = DeviceManager()
device = manager.create_forwarder("tcp://*:5555", "tcp://*:5556")
device.start()

# Create a publisher
publisher = ZMQPublisher()
publisher.connect("tcp://localhost:5555")
publisher.publish("topic", "Hello, World!")

# Create a subscriber
def message_handler(message):
    print(f"Received: {message}")

subscriber = ZMQSubscriber()
subscriber.connect("tcp://localhost:5556")
subscriber.subscribe("topic")
subscriber.set_message_handler(message_handler)
subscriber.start_receiving()
```

### Creating an MCP Server

```python
from ailf import BaseMCP, Context

# Create MCP server
mcp = BaseMCP(
    name="DocumentationHelper",
    instructions="Help users find and understand documentation"
)

# Add a tool
@mcp.tool()
async def search_docs(ctx: Context, query: str) -> list:
    """Search for documentation based on query."""
    # Implementation...
    results = [{"title": "API Guide", "url": "..."}]
    return results

# Run the server
await mcp.serve()
```

### Using Storage

```python
from ailf import LocalStorage

# Initialize storage
storage = LocalStorage(base_path="./data")

# Save and load data
storage.save_json({"key": "value"}, "configs/settings.json")
data = storage.load_json("configs/settings.json")
```

## Documentation

For full documentation, visit [https://ailf.readthedocs.io/](https://ailf.readthedocs.io/)

## Development

### Setting up a Development Environment

```bash
# Clone the repository
git clone https://github.com/ai-liberation-front/ailf.git
cd ailf

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=ailf tests/
```

### Building the Package

```bash
# Build source and wheel distributions
./build_dist.py
```

This will create both `.tar.gz` (source) and `.whl` (wheel) files in the `dist/` directory.

## License

MIT

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
