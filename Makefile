# Python commands
PYTHON := python3
PIP := pip3
PYTEST := pytest

# Project directories
SRC_DIR := core utils
TEST_DIR := tests
DOC_DIR := docs

# Test settings
PYTEST_ARGS := -v --cov=$(SRC_DIR) --cov-report=term-missing

.PHONY: help clean test test-unit test-integration coverage lint format install docs

help:
	@echo "Available commands:"
	@echo "  make install         - Install project dependencies"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make coverage       - Generate test coverage report"
	@echo "  make lint           - Run code linting"
	@echo "  make format         - Format code"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make docs           - Build documentation"

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .  # Install package in development mode

test: install test-unit test-integration

test-unit:
	$(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)/utils --ignore=$(TEST_DIR)/integration

test-integration:
	$(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)/integration

coverage:
	$(PYTEST) $(PYTEST_ARGS) --cov-report=html:coverage_html $(TEST_DIR)
	@echo "Coverage report generated in coverage_html/"

lint:
	flake8 $(SRC_DIR) $(TEST_DIR)
	mypy $(SRC_DIR)

format:
	black $(SRC_DIR) $(TEST_DIR)
	isort $(SRC_DIR) $(TEST_DIR)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.pyc" -exec rm -rf {} +
	find . -type d -name "*.pyo" -exec rm -rf {} +
	find . -type d -name "*.pyd" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "coverage_html" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

docs:
	$(MAKE) -C $(DOC_DIR) html
	@echo "Documentation built in $(DOC_DIR)/build/html/"
