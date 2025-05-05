import os
import pathlib

from setuptools import find_packages, setup

# Read long description from README
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

# Core dependencies needed for minimal functionality
CORE_DEPS = [
    "pydantic>=2.7.2",
    "python-dotenv>=1.0.0",
]

# AI dependencies
AI_DEPS = [
    "anthropic>=0.50.0",
    "openai>=1.77.0",
    "google-generativeai>=0.8.5",
    "pydantic-ai>=0.1.9",
]

# MCP server dependencies
MCP_DEPS = [
    "mcp>=1.7.1",
    "fastapi>=0.95.1",
    "sse-starlette>=1.6.1",
    "uvicorn>=0.23.1",
]

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
    name="template-python-dev",
    version="0.1.0",
    description="Template for Python agent development projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="",
    author_email="",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="agent, development, template, ai, llm",
    packages=find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*", "src"]),
    python_requires=">=3.10",
    install_requires=CORE_DEPS,
    extras_require=extras_require,
    include_package_data=True,
    package_dir={"": "."},  # Explicitly specify the root directory
    project_urls={
        "Bug Reports": "https://github.com/yourusername/template-python-dev/issues",
        "Source": "https://github.com/yourusername/template-python-dev",
    },
)
