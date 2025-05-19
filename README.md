# AI Library Framework (AILF)

## About

This package provides a collection of utilities, patterns, and infrastructure components specifically designed to accelerate the development of AI agents with:

- Structured LLM interactions via Pydantic models
- Tool registration and management
- Distributed computing via ZeroMQ
- Configurable storage backends
- Comprehensive logging and monitoring
- Secure secret management
- Testing patterns for AI components

## Installation

```bash
# Basic installation
pip install ailf

# With AI support
pip install ailf[ai]

# With all features
pip install ailf[all]
```

## Core Agent Patterns

AILF provides implementations of advanced LLM agent patterns:

- **ReAct**: Reasoning and Acting in an iterative loop
- **Tree of Thoughts**: Exploring multiple reasoning paths in a tree structure
- **Task Planning**: Decomposing complex tasks into actionable steps
- **Reflection**: Self-monitoring and improvement through reflection

## Documentation

Comprehensive documentation is available in the `docs` directory. The documentation covers:

- API Reference
- User Guides
- Examples
- Development Guidelines

### Building Documentation

To build the documentation locally:

```bash
cd docs
./build_docs.sh
```

The generated HTML documentation will be available in `docs/build/html/`.

### Tree of Thoughts

Tree of Thoughts (ToT) is an advanced reasoning technique that extends beyond simple prompt-response patterns by exploring multiple reasoning paths in parallel. The pattern allows AI agents to:

- Generate multiple possible thoughts at each step
- Evaluate the potential of each thought path
- Explore the most promising paths first (beam search)
- Backtrack when necessary to find optimal solutions

**Example usage:**

```python
from ailf.cognition.tree_of_thoughts import TreeOfThoughtsProcessor
from ailf.schemas.tree_of_thought import ToTConfiguration

# Configure Tree of Thoughts
config = ToTConfiguration(
    max_depth=3,        # Maximum tree depth
    branching_factor=3, # Branches per node
    beam_width=2        # Number of paths to explore
)

# Create processor
tot_processor = TreeOfThoughtsProcessor(ai_engine, config=config)

# Process a complex problem
result = await tot_processor.process(context)
```

For more details, see the [Tree of Thoughts documentation](docs/tree-of-thought.md).

## Security Features

### Comprehensive Secret Management

AILF provides a flexible and secure secrets management system that supports multiple providers:

- **Google Secret Manager**: For GCP environments
- **AWS Secrets Manager**: For AWS environments
- **Azure Key Vault**: For Azure environments
- **HashiCorp Vault**: For cross-cloud and enterprise environments
- **Environment Variables / .env Files**: For local development

The unified API makes it easy to switch between providers without changing application code:

```python
from ailf.cloud.secrets import secret_manager

# Configure providers
secret_manager.configure_provider('google', project_id='my-project')
secret_manager.configure_provider('aws', region_name='us-west-2')
secret_manager.configure_provider('vault', url='https://vault.example.com', token='my-token')

# Access secrets (auto-selects configured default provider)
db_password = secret_manager.get_secret('DB_PASSWORD')

# Explicitly specify provider
api_key = secret_manager.get_secret('API_KEY', provider='aws')
```

Security best practices are built-in:
- No secrets exposed in logs or exceptions
- In-memory caching with configurable TTL
- Support for automatic rotation where available
- Environment-specific secrets

## AILF in the Agentic AI Ecosystem

AILF is a robust framework designed to accelerate the development of AI agents by providing modular, type-safe, and distributed computing capabilities. It stands out in the Agentic AI ecosystem due to its multi-protocol support, comprehensive logging, and secure secret management.

### Competitors

AILF competes with several frameworks in the Agentic AI ecosystem, each offering unique features:

1. **LangChain**:
   - Focus: Building applications with LLMs through composable chains.
   - Strengths: Extensive integrations, prompt templates, and memory management.
   - Weakness: Limited support for distributed computing and multi-protocol interoperability.

2. **AutoGen**:
   - Focus: Multi-agent systems with autonomous task delegation.
   - Strengths: Agent-to-agent communication and task orchestration.
   - Weakness: Less modular compared to AILF.

3. **Semantic Kernel**:
   - Focus: Semantic memory and skill orchestration.
   - Strengths: Tight integration with Microsoft services.
   - Weakness: Limited flexibility for non-Microsoft ecosystems.

4. **DSPy**:
   - Focus: Declarative agent programming.
   - Strengths: Simplicity and declarative syntax.
   - Weakness: Lacks advanced features like distributed computing.

5. **Vertex AI Agents**:
   - Focus: Deploying scalable AI agents on Google Cloud.
   - Strengths: Scalability and integration with Google Cloud services.
   - Weakness: Cloud-dependent and less customizable.

6. **IBM watsonx.ai**:
   - Focus: Enterprise AI with agent capabilities.
   - Strengths: Enterprise-grade security and compliance.
   - Weakness: High cost and complexity.

7. **AgentGPT**:
   - Focus: Rapid prototyping of autonomous agents.
   - Strengths: User-friendly interface.
   - Weakness: Limited scalability and customization.

### Why Choose AILF?

AILF's unique strengths include:
- **Multi-Protocol Support**: Seamlessly integrates with MCP, A2A, and ACP protocols.
- **Distributed Computing**: Built-in support for ZeroMQ enables scalable agent deployments.
- **Type Safety**: Pydantic models ensure structured and validated interactions.
- **Modularity**: Highly extensible design for domain-specific customizations.

AILF is ideal for developers seeking a flexible, scalable, and secure framework for building sophisticated AI agents.

## Documentation

For full documentation, visit [ailf.readthedocs.io](https://ailf.readthedocs.io/)

## Development

### Using the Dev Container

This project includes a development container configuration to ensure consistent development environments across different machines. The dev container includes all necessary dependencies and tools for AI agent development.

#### VS Code Dev Container

If you're using VS Code with the Remote - Containers extension:

1. Open the project in VS Code
2. When prompted, click "Reopen in Container"
3. Alternatively, press F1 and select "Remote-Containers: Reopen in Container"

#### GitHub Codespaces

You can also develop using GitHub Codespaces, which will automatically use the dev container configuration.

### CI/CD Workflows

Our GitHub Actions workflows use the same dev container configuration as local development, ensuring consistency across development and CI environments:

- **Build Dev Container**: Builds and publishes the dev container image when the container configuration changes
- **Integration Tests**: Runs tests in the dev container
- **Dev Container CI**: Tests the dev container build and functionality
- **Dev Container Tests**: Additional container-specific tests
- **Publish to PyPI**: Builds and publishes packages using the dev container

The workflows use the `devcontainers/ci` action to leverage the same development environment defined in the `.devcontainer` directory. This ensures that:

1. Local development (VS Code Dev Container)
2. CI/CD pipelines (GitHub Actions)
3. Production builds

All use identical environments, eliminating "works on my machine" issues.
