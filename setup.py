from setuptools import setup, find_packages

setup(
    name="template-python-dev",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic",
        "pydantic-ai",
        "python-dotenv",
    ],
    extras_require={
        "test": ["pytest", "pytest-asyncio", "pytest-mock"],
    },
)