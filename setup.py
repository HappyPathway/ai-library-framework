"""
This file is kept for backwards compatibility. The actual build configuration
is in pyproject.toml as per PEP 517/518 standards.

For most use cases, you should use the following commands:
- To install in development mode: pip install -e .
- To build the package: python -m build
"""

import setuptools

# This setup.py is a thin wrapper around the pyproject.toml configuration
setuptools.setup()

# Cloud dependencies
CLOUD_DEPS = [
    "google-cloud-storage>=2.14.0",
    "google-cloud-secret-manager>=2.23.3",
]

# Dev & test dependencies
TEST_DEPS = [
    "pytest>=8.1.1",
    "pytest-asyncio>=0.23.5",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.10.0",
]

DEV_DEPS = [
    "black>=24.3.0",
    "flake8>=7.0.0",
    "mypy>=1.9.0",
    "isort>=5.13.2",
] + TEST_DEPS

# ZMQ dependencies
ZMQ_DEPS = [
    "pyzmq>=25.1.2",
]

# Redis dependencies
REDIS_DEPS = [
    "redis>=5.0.1",
    "async-timeout>=4.0.3",  # Used by aioredis for timeouts
]

# Define all extras
extras_require = {
    "ai": AI_DEPS,
    "mcp": MCP_DEPS,
    "cloud": CLOUD_DEPS,
    "zmq": ZMQ_DEPS,
    "redis": REDIS_DEPS,
    "test": TEST_DEPS,
    "dev": DEV_DEPS,
    # You can define new combinations like:
    "agent": AI_DEPS + MCP_DEPS,
    # Or a comprehensive all-in-one:
    "all": AI_DEPS + MCP_DEPS + CLOUD_DEPS + ZMQ_DEPS + REDIS_DEPS,
}

setup(
    name="ailf",
    version="0.1.0",
    description="AI Liberation Front: Freedom tools for AI agent development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AI Liberation Front Team",
    author_email="ailf@example.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="agent, development, ai, llm, tools, utils, pydantic",
    packages=find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*", "examples", "docs"]),
    python_requires=">=3.10",
    install_requires=CORE_DEPS,
    extras_require=extras_require,
    include_package_data=True,
    package_data={"ailf": ["py.typed"]},
    project_urls={
        "Bug Reports": "https://github.com/ai-liberation-front/ailf/issues",
        "Source": "https://github.com/ai-liberation-front/ailf",
        "Documentation": "https://ailf.readthedocs.io/",
    },
)
