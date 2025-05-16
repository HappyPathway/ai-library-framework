# Direct Agent Example

This page documents the Direct Agent Example module, which demonstrates how to use the agent framework with direct imports.

## Overview

The `direct_agent_example.py` script demonstrates a simple implementation of an agent with tools and a mock AI engine, using a direct import strategy to ensure it works even if the agent module hasn't been properly installed.

## Module Components

### Helper Functions

```{eval-rst}
.. autofunction:: examples.direct_agent_example.module_exists
```

### Agent Status

```{eval-rst}
.. autoclass:: examples.direct_agent_example.AgentStatus
   :members:
   :undoc-members:
```

### Agent Configuration

```{eval-rst}
.. autoclass:: examples.direct_agent_example.AgentConfig
   :members:
```

### Tool Decorator

```{eval-rst}
.. autofunction:: examples.direct_agent_example.tool
```

### Agent Class

```{eval-rst}
.. autoclass:: examples.direct_agent_example.Agent
   :members:
```

### Planning Strategies

```{eval-rst}
.. autoclass:: examples.direct_agent_example.ReactivePlan
   :members:

.. autoclass:: examples.direct_agent_example.DeliberativePlan
   :members:
```

### Tool Execution

```{eval-rst}
.. autofunction:: examples.direct_agent_example.execute_tool
```

### Data Models

```{eval-rst}
.. autoclass:: examples.direct_agent_example.SearchResult
   :members:
```

### Mock AI Engine

```{eval-rst}
.. autoclass:: examples.direct_agent_example.MockAIEngine
   :members:
```

### Example Functions

```{eval-rst}
.. autofunction:: examples.direct_agent_example.web_search
.. autofunction:: examples.direct_agent_example.calculate
.. autofunction:: examples.direct_agent_example.run_simple_agent
```

## Running the Example

The example can be run directly from the command line:

```bash
python examples/direct_agent_example.py
```

This will instantiate an agent with two tools (web search and calculate) and run it with two different queries to demonstrate its functionality.
