# API Documentation Organization

This document outlines how the API documentation is organized for the AILF library during its transition from a flat structure to a src-based layout.

## Module Organization

The API documentation is organized into the following main sections:

### Core Package Components

```text
ailf/
├── agent/         # Agent components and base classes
├── ai/            # AI model integrations and engines
├── cloud/         # Cloud service integrations
├── core/          # Core utilities and infrastructure
├── messaging/     # Messaging and communication components
├── schemas/       # Data models and schema definitions
├── storage/       # Storage implementations for various backends
└── workers/       # Asynchronous task processing components
```

### Additional Components

- **communication/** - Communication utilities including web scrapers
- **mcp/** - Model Context Protocol server implementations
- **utils/** - Legacy utility modules (being migrated to src/ailf/)

## Documentation File Structure

The API documentation files are organized in a structure that mirrors the package organization:

```text
docs/source/api/
├── agent/         # Agent component documentation
├── ai/            # AI integration documentation
├── cloud/         # Cloud service documentation
├── core/          # Core utilities documentation
├── messaging/     # Messaging documentation
├── schemas/       # Schema definitions documentation
├── storage/       # Storage implementations documentation
└── workers/       # Worker component documentation
```

## Working with the Documentation

### Finding Documentation

- For **src-based** components, look in the appropriate subdirectory under `docs/source/api/` 
- For **legacy components**, documentation may still reference the old structure but will be migrated over time

### Building Documentation

To build the documentation:

```bash
cd docs
make html
```

### Handling Import Errors

During the transition period, some import errors may occur due to:

1. Modules that exist in the new structure but not the old one
2. Modules that exist in the old structure but not the new one
3. Modules referenced in documentation but not yet implemented

These errors are handled by mocking the relevant modules during the documentation build process.

## API Reference Structure

The API reference is organized hierarchically:

1. **Top-level modules** - Main package components (agent, ai, cloud, etc.)
2. **Submodules** - Components within each top-level module
3. **Classes and functions** - Documentation for individual components

Each module documentation page includes:

- Module description
- Class and function listings
- Parameter details
- Usage examples (where available)
