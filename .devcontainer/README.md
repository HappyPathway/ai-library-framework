# Dev Container Features

This directory contains custom features for the development container.

## Features

### 1. Repository Cloner

This feature automatically clones specified GitHub repositories when the container is built.

Configuration in `devcontainer.json`:
```json
"./features/repository-cloner": {
    "repositories": "kagent/kagent,a2a-dev/a2a",
    "targetDir": "/workspaces/repositories"
}
```

Parameters:
- `repositories`: Comma-separated list of GitHub repositories to clone (format: owner/repo)
- `targetDir`: Directory where repositories will be cloned

### 2. Python Development Environment Setup

This feature sets up the Python development environment, including:
- Redis installation and configuration
- Virtual environment creation
- Project directories setup
- Environment file initialization

Configuration in `devcontainer.json`:
```json
"./features/python-dev-setup": {
    "installRedis": true,
    "pythonVersion": "3.12",
    "setupVenv": true
}
```

Parameters:
- `installRedis`: Whether to install and configure Redis
- `pythonVersion`: Minimum required Python version
- `setupVenv`: Whether to create a Python virtual environment

## Directory Structure

```
.devcontainer/
├── features/
│   ├── repository-cloner/
│   │   ├── devcontainer-feature.json
│   │   └── install.sh
│   └── python-dev-setup/
│       ├── devcontainer-feature.json
│       └── install.sh
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   ├── ...
└── scripts/
    └── ...
```
