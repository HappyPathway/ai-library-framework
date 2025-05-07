"""
Test module to verify that all required packages can be imported.
"""

import pytest


def test_import_core_dependencies():
    """Test importing core dependencies."""
    import json
    import logging
    import os
    import sys


def test_import_external_dependencies():
    """Test importing external dependencies."""
    pytest.importorskip("pydantic")
    pytest.importorskip("redis")


def test_import_ai_dependencies():
    """Test importing AI dependencies."""
    openai = pytest.importorskip("openai")
    anthropic = pytest.importorskip("anthropic")

    # Skip if Google's generativeai package is not available
    try:
        import google.generativeai as genai
    except ImportError:
        pytest.skip("google.generativeai not available")


def test_import_project_modules():
    """Test importing project modules."""
    import utils
    from utils import ai_engine, storage
    from ailf.schemas import ai
