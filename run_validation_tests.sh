#!/bin/bash
# filepath: /workspaces/template-python-dev/run_validation_tests.sh
# Run all validation tests for the AILF framework

# Set up environment
echo "Setting up test environment..."
export PYTHONPATH=/workspaces/template-python-dev:$PYTHONPATH

# Create test results directory
RESULTS_DIR="test_results"
mkdir -p $RESULTS_DIR

echo -e "\n\n====== AILF Framework Validation Tests ======\n"

# Function to run tests and save results
run_test_category() {
    category=$1
    test_path=$2
    echo -e "\n\n====== Running $category Tests ======\n"
    python -m pytest $test_path -v --junitxml=$RESULTS_DIR/${category}_results.xml
    
    # Check if tests passed
    if [ $? -eq 0 ]; then
        echo -e "\n✅ $category tests passed"
    else
        echo -e "\n❌ $category tests failed"
    fi
}

# Run unit tests
run_test_category "Unit" "tests/unit"

# Run integration tests
run_test_category "Integration" "tests/integration"

# Run A2A-specific tests
run_test_category "A2A" "tests/unit/communication/test_a2a_*.py tests/integration/communication/test_a2a_*.py"

# Run performance tests if available
if [ -d "tests/performance" ]; then
    run_test_category "Performance" "tests/performance"
fi

# Run documentation tests
if [ -d "tests/docs" ]; then
    run_test_category "Documentation" "tests/docs"
fi

# Run end-to-end tests if enabled
if [ "$RUN_E2E_TESTS" = "1" ]; then
    echo -e "\n\n====== Running End-to-End Tests ======\n"
    python -m pytest tests/e2e -v --junitxml=$RESULTS_DIR/e2e_results.xml
else
    echo -e "\n\n====== Skipping End-to-End Tests ======\n"
    echo "To run E2E tests, set RUN_E2E_TESTS=1"
fi

# Generate coverage report
echo -e "\n\n====== Generating Coverage Report ======\n"
python -m pytest --cov=ailf --cov-report=xml:$RESULTS_DIR/coverage.xml --cov-report=term tests/

# Print summary
echo -e "\n\n====== Test Summary ======\n"
echo "Test results saved to $RESULTS_DIR directory"
echo "To view detailed coverage information: python -m pytest --cov=ailf tests/"
