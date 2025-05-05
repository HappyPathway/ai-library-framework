#!/bin/bash
# This script installs packages using pip with a non-interactive flag

# Set environment variable to prevent pip from prompting for user input
export PIP_NO_INPUT=1

# Install requirements
pip install -r requirements.txt

# Install the package in development mode from the root directory
pip install -e .
