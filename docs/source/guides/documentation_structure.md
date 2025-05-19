# Documentation Structure Guide

This guide provides an overview of the AILF documentation structure and organization.

## Documentation Organization

The documentation for the AILF library is organized into the following main sections:

1. **User Guides**: Practical how-to guides for working with the library
2. **API Reference**: Detailed documentation of the library's components and functions
3. **Examples**: Sample code and tutorials showing the library in action
4. **Project Reference**: Information about the project itself (roadmaps, plans, etc.)

## Documentation Components

### 1. User Guides

Located in `docs/source/guides/`, these guides explain how to use different aspects of the library:

- **Development Setup**: How to set up your development environment
- **Src Structure**: Explanation of the src-based project layout
- **Import Patterns**: How to correctly import library components
- **Contributing**: Guidelines for contributing to the documentation
- **Testing**: How to test components of the library
- **Logging**: Using the library's logging system
- **Messaging**: Working with the messaging infrastructure

### 2. API Reference

Located in `docs/source/api/`, this section documents all components of the library:

- **Component Groups**: Each major component (agent, ai, cloud, etc.) has its own section
- **Class Documentation**: Detailed documentation of all classes, methods, and properties
- **Examples**: Code snippets showing how to use different components
- **Module Relationships**: Information about how different components interact

### 3. Examples

Located in `docs/source/examples/`, this section contains:

- **Direct Agent Example**: How to use the basic agent functionality
- **Additional Examples**: Other examples showing different use cases

### 4. Project Reference

Located at the top level of `docs/source/`, this section contains:

- **Documentation Transition Plan**: The plan for migrating documentation to src-based layout
- **Migration Guides**: Information about migrating code and users to new versions
- **Implementation Plans**: Plans for implementing new features

## Legacy Documentation

Legacy documentation is kept in `docs/legacy/` for historical reference but is not included in the built documentation.

## Documentation Build Process

The documentation is built using Sphinx with the MyST Markdown parser:

1. Source files are written in Markdown format
2. Sphinx processes these files to generate HTML documentation
3. API documentation is automatically generated from docstrings

## Contributor Guidelines

When contributing to the documentation:

1. Place new guides in the appropriate section
2. Use proper Markdown formatting
3. Include code examples and type hints
4. Follow the existing documentation structure
5. Update index files to include new documents
6. Test the documentation build before submitting changes

## Fixing Documentation Issues

To fix common documentation issues:

1. **Missing Module Errors**: Add the module to the MOCK_MODULES list in conf.py
2. **File Not in Toctree**: Add the file to the appropriate toctree
3. **Broken Links**: Check file paths and toctree entries
4. **Missing Components**: Create stub documentation until the component is implemented
