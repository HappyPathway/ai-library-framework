from setuptools import setup, find_packages

setup(
    name="template-python-dev",
    version="0.1.0",
    packages=find_packages(include=["utils", "utils.*"]),
    install_requires=[
        "sqlalchemy>=2.0.28",
        "pydantic>=2.6.3",
        "PyGithub>=2.3.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.3",
        "cachetools>=5.3.3",
        "google-cloud-storage>=2.14.0",
        "google-cloud-secret-manager>=2.19.0",
        "gitpython>=3.1.42",
    ],
    extras_require={
        "test": [
            "pytest>=8.1.1",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            "types-requests>=2.31.0.20240311",
            "types-beautifulsoup4>=4.12.0.20240229",
        ],
    },
    python_requires=">=3.11",
)
