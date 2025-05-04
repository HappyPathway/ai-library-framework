# Requirements Management

This directory contains segmented requirements files for different deployment scenarios.

## Usage

### Basic Installation
```bash
pip install -r requirements/base.txt
```

### Feature-specific Installations
Choose the additional features you need:

```bash
# For AI capabilities
pip install -r requirements/base.txt -r requirements/ai.txt

# For MCP server functionality
pip install -r requirements/base.txt -r requirements/mcp.txt

# For cloud integrations
pip install -r requirements/base.txt -r requirements/cloud.txt

# For ZMQ messaging
pip install -r requirements/base.txt -r requirements/zmq.txt
```

### Environment-specific Installations

```bash
# Development environment
pip install -r requirements/base.txt -r requirements/dev.txt

# Production environment
pip install -r requirements/base.txt -r requirements/prod.txt
```

### Complete Installations

```bash
# Full development environment
pip install -r requirements/base.txt -r requirements/ai.txt -r requirements/mcp.txt -r requirements/cloud.txt -r requirements/zmq.txt -r requirements/dev.txt

# Full production environment
pip install -r requirements/base.txt -r requirements/ai.txt -r requirements/mcp.txt -r requirements/cloud.txt -r requirements/zmq.txt -r requirements/prod.txt
```

## Using setup.py

Alternatively, you can use the setup.py extras:

```bash
# Basic installation
pip install -e .

# With specific features
pip install -e ".[ai]"
pip install -e ".[mcp]"
pip install -e ".[cloud]"
pip install -e ".[zmq]"

# Combined features
pip install -e ".[ai,mcp]"  # For building an AI agent with MCP

# Development
pip install -e ".[dev]"

# Full installation
pip install -e ".[all]"
```
