# AILF Framework Jupyter Notebooks

This directory contains a collection of Jupyter notebooks that demonstrate various features and capabilities of the AILF framework.

## Available Notebooks

1.  **01_prompt_optimization_intro.ipynb**
    *   Introduction to the prompt optimization workflow
    *   Setting up the PromptLibrary with templates
    *   Creating and using a PerformanceAnalyzer
    *   Running optimization cycles with the AdaptiveLearningManager
    *   Analyzing version history and optimization impact

2.  **02_custom_implementation.ipynb**
    *   Extending the framework with custom implementations
    *   Creating domain-specific analyzers and optimization strategies
    *   Building specialized workflows for specific use cases
    *   Example: Customer service chatbot optimization

3.  **03_real_api_integration.ipynb**
    *   Integrating with real LLM APIs (OpenAI, Anthropic)
    *   Creating real performance measurements
    *   Analyzing cost/performance tradeoffs
    *   A/B testing prompt optimizations

4.  **04_task_delegation_worker.ipynb**
    *   Demonstrates task delegation to a worker for prompt refinement.
    *   An `InitialAgent` uses a `TaskWorker` (with its own AI engine) to break down a vague goal into structured components.
    *   The `InitialAgent` then uses these components to build a high-quality prompt for its final task execution.
    *   Illustrates modularity and specialization in agent design.

## Getting Started

To run these notebooks:

1.  Make sure you have Jupyter installed in your environment
2.  For notebooks using real API access, create a `.env` file with your API keys:
    ```
    OPENAI_API_KEY=your_openai_key_here
    ANTHROPIC_API_KEY=your_anthropic_key_here
    ```
3.  Launch Jupyter Lab or Jupyter Notebook:
    ```bash
    jupyter lab
    # or
    jupyter notebook
    ```

## Extending with Your Own Notebooks

Feel free to create your own notebooks to explore specific aspects of the framework. Some ideas:
*   Specialized optimization for specific LLM models
*   Integration with other frameworks like LangChain or LlamaIndex
*   Benchmark different prompt strategies
*   Explore specific domains like legal, medical, or financial prompt optimization