# Documentation Transition Plan

This document outlines the remaining tasks needed to complete the transition of documentation to support the src-based layout.

## Completed Tasks

- ✅ Created legacy directory for outdated documentation
- ✅ Updated conf.py to mock additional modules
- ✅ Added documentation explaining the src-based layout
- ✅ Fixed API documentation structure with proper toctree organization
- ✅ Created index files for all major components
- ✅ Added comprehensive API organization documentation

## Remaining Tasks

### Priority 1: Fix Critical Build Issues

1. **Fix Cognition Schema Import**: 
   - Create the missing `ailf.schemas.cognition` module or update references
   - Update mocking in conf.py to handle this module

2. **Resolve Toctree Reference Errors**:
   - Fix broken references to non-existent documents
   - Ensure all documents are included in a toctree

3. **Fix Code Lexing Errors**:
   - Address directory structure visualization issues

### Priority 2: Address Documentation Content

1. **Update Module Documentation**:
   - Ensure each module has proper docstrings
   - Add examples to key components

2. **Create Transition Guides**:
   - Document how to migrate from legacy imports to src-based imports
   - Create guide for converting existing code to the new structure

3. **Update Code Examples**:
   - Ensure all examples use the src-based imports
   - Update API examples for consistency

### Priority 3: Improve Documentation Quality

1. **Add Diagrams**:
   - Create architecture diagrams using Mermaid or similar
   - Document component relationships visually

2. **Cross-Reference Documentation**:
   - Add internal links between related components
   - Create a glossary for key terms

3. **Add Testing Documentation**:
   - Document how to test components in the src-based layout
   - Create examples of test patterns

## Implementation Timeline

### Phase 1: Fix Build Issues (Current Phase)
- Address all critical build issues
- Ensure documentation builds without errors

### Phase 2: Content Migration (Next Phase)
- Update module documentation 
- Create transition guides
- Update examples

### Phase 3: Quality Improvements (Final Phase)
- Add visual documentation
- Improve cross-referencing
- Enhance test documentation

## Monitoring and Updates

The documentation build process should be monitored to catch any new issues that arise during the transition. Regular builds should be performed to ensure the documentation remains in a usable state throughout the process.

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [MyST Markdown](https://myst-parser.readthedocs.io/en/latest/)
- [Python src-based Layout Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/#a-simple-project)
