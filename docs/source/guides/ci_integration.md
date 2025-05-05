# CI/CD Integration Guide

This guide explains how to integrate the Python Agent Development Template project with CI/CD systems like GitHub Actions.

## GitHub Actions Integration

The project includes a sample GitHub Actions workflow at `.github/workflows/ci.yml` that demonstrates how to properly test and build the package in a CI environment.

### Key Workflow Components

1. **Matrix Testing**: Tests are run against multiple Python versions
2. **Dependency Installation**: Dependencies are installed from `requirements.txt`
3. **Package Installation**: The package itself is installed in development mode with `pip install -e .`
4. **Linting**: Code quality checks with flake8
5. **Testing**: Test suite execution with pytest and coverage reporting

### Common Issues and Solutions

#### Git Reference in Requirements

**Problem**: Including Git repository references in `requirements.txt` can cause permission issues in CI environments:

```
-e git+ssh://git@github.com/Organization/repo.git@commit#egg=package
```

**Solution**: 
- Remove Git references from `requirements.txt`
- Install the package locally in the CI workflow with `pip install -e .`

#### SSH Keys for Private Dependencies

If your project requires private Git dependencies, you'll need to configure SSH keys in your CI environment:

```yaml
steps:
  - uses: actions/checkout@v4
  
  - name: Set up SSH key
    uses: webfactory/ssh-agent@v0.8.0
    with:
      ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
  
  - name: Install dependencies with private repos
    run: pip install -r requirements.txt
```

#### Deployment Package Creation

To create deployment packages for production:

```yaml
- name: Create deployment package
  run: |
    python create_deployment_package.py
    
- name: Archive deployment package
  uses: actions/upload-artifact@v4
  with:
    name: deployment-package
    path: dist/*.zip
```

## Local CI Testing

To test the CI workflow locally before pushing to GitHub:

1. Install [act](https://github.com/nektos/act)
2. Run the workflow locally:
   ```bash
   act -j test
   ```

This can help catch issues with the workflow before committing.
