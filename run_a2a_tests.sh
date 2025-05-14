#!/bin/bash
# Run all A2A-related tests

# Set up environment
echo "Setting up test environment..."
export PYTHONPATH=/workspaces/template-python-dev:$PYTHONPATH

# Create test directories if they don't exist
mkdir -p /workspaces/template-python-dev/tests/e2e
mkdir -p /workspaces/template-python-dev/tests/performance

# Run unit tests for A2A components
echo -e "\n\n====== Running A2A Unit Tests ======\n"
python -m pytest /workspaces/template-python-dev/tests/unit/communication/test_a2a_*.py -v

# Run integration tests for A2A components
echo -e "\n\n====== Running A2A Integration Tests ======\n"
python -m pytest /workspaces/template-python-dev/tests/integration/communication/test_a2a_*.py -v

# Run performance benchmarks (if any)
if [ -f "/workspaces/template-python-dev/tests/performance/test_a2a_benchmarks.py" ]; then
    echo -e "\n\n====== Running A2A Performance Benchmarks ======\n"
    python -m pytest /workspaces/template-python-dev/tests/performance/test_a2a_benchmarks.py -v
fi

# Print test summary
echo -e "\n\n====== Test Summary ======\n"
echo "Completed running A2A tests"
echo "For detailed test coverage report, run: pytest --cov=ailf.communication.a2a_* tests/unit/communication/test_a2a_*.py tests/integration/communication/test_a2a_*.py"
