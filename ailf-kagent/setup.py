"""
Setup script for the ailf-kagent package.
"""

from setuptools import setup, find_packages
import os

# Read the contents of the README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get version from the __init__.py file
with open(os.path.join(this_directory, 'ailf_kagent/__init__.py'), encoding='utf-8') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('=')[1].strip(' \'"')
            break

setup(
    name="ailf-kagent",
    version=version,
    description="Integration between AILF and Kagent frameworks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AILF Team",
    author_email="info@ailf.dev",
    url="https://github.com/your-org/ailf-kagent",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        # These would need to be adjusted based on actual package names
        # and compatibility requirements
        "kagent>=0.1.0",
        "ailf>=0.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="ai, agents, llm, kagent, ailf, integration",
)
