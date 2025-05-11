# Makefile for ailf-kagent package

.PHONY: help install dev-install test lint format clean build docs publish

help:
	@echo "Available commands:"
	@echo "  install       Install the package"
	@echo "  dev-install   Install the package in development mode with dev dependencies"
	@echo "  test          Run tests"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code with black and isort"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build distribution packages"
	@echo "  docs          Build documentation"
	@echo "  publish       Publish package to PyPI"

install:
	pip install .

dev-install:
	pip install -e ".[dev,docs]"

test:
	pytest tests/ --cov=ailf_kagent --cov-report=term --cov-report=xml

lint:
	isort --check ailf_kagent tests
	black --check ailf_kagent tests
	mypy ailf_kagent

format:
	isort ailf_kagent tests
	black ailf_kagent tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +

build: clean
	pip install -U pip build
	python -m build

docs:
	cd docs && make html

publish: build
	pip install -U twine
	twine check dist/*
	twine upload dist/*
