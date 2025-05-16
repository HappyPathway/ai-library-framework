"""Integration tests for prompt template management in PromptLibrary.

These tests verify that the PromptLibrary can properly manage versioned templates
and handle updates from the AdaptiveLearningManager.
"""

import os
import json
import pytest
import tempfile
import time
from typing import Dict, Any, List

from ailf.cognition.prompt_library import PromptLibrary
from ailf.schemas.prompt_engineering import PromptTemplateV1, PromptLibraryConfig


@pytest.fixture
def prompt_library_path() -> str:
    """Create a temporary directory for prompt templates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_template() -> Dict[str, Any]:
    """Return a sample prompt template for testing."""
    return {
        "template_id": "test_template",
        "version": 1,
        "description": "A test prompt template",
        "system_prompt": "You are a helpful assistant.",
        "user_prompt_template": "Answer the following question: {question}",
        "placeholders": ["question"],
        "tags": ["test"],
        "created_at": time.time()
    }


@pytest.fixture
def prompt_library(prompt_library_path, sample_template) -> PromptLibrary:
    """Create a prompt library with an initial template."""
    # Create template file
    filename = f"{sample_template['template_id']}_v{sample_template['version']}.json"
    filepath = os.path.join(prompt_library_path, filename)
    with open(filepath, 'w') as f:
        json.dump(sample_template, f, indent=2)
    
    # Initialize the prompt library
    config = PromptLibraryConfig(
        library_path=prompt_library_path,
        default_prompt_id=sample_template["template_id"],
        auto_save=True
    )
    
    return PromptLibrary(config)


def test_update_template(prompt_library, sample_template):
    """
    Test that PromptLibrary.update_template correctly updates a template and increments its version.
    """
    # Get the initial template
    template_id = sample_template["template_id"]
    initial_template = prompt_library.get_template(template_id)
    assert initial_template is not None
    assert initial_template.version == 1
    
    # Update the template with new content
    new_content = {
        "system_prompt": "You are a specialized assistant for testing.",
        "user_prompt_template": "Please answer this test question thoroughly: {question}",
        "updated_by_component": "test_harness"
    }
    
    # Update with version notes
    updated_template = prompt_library.update_template(
        template_id, 
        new_content,
        version_notes="Test update with more thorough instructions."
    )
    
    # Verify the update
    assert updated_template is not None
    assert updated_template.version == 2
    assert updated_template.system_prompt == new_content["system_prompt"]
    assert updated_template.user_prompt_template == new_content["user_prompt_template"]
    assert updated_template.updated_by_component == new_content["updated_by_component"]
    assert updated_template.version_notes == "Test update with more thorough instructions."
    
    # Verify that getting the template without specifying version returns the latest
    latest = prompt_library.get_template(template_id)
    assert latest.version == 2
    
    # Verify that we can still retrieve the original version
    original = prompt_library.get_template(template_id, version=1)
    assert original is not None
    assert original.version == 1
    assert original.system_prompt == sample_template["system_prompt"]


def test_add_new_template_version(prompt_library, sample_template):
    """
    Test that PromptLibrary.add_new_template_version correctly adds a new version of a template.
    """
    # Get the initial template
    template_id = sample_template["template_id"]
    initial_template = prompt_library.get_template(template_id)
    assert initial_template is not None
    
    # Create a new version of the template
    new_template_dict = initial_template.dict()
    new_template_dict.update({
        "version": 2,
        "system_prompt": "You are a specialized testing assistant.",
        "updated_by_component": "test_harness",
        "optimization_source": "manual_test",
        "version_notes": "Test of add_new_template_version"
    })
    new_template = PromptTemplateV1(**new_template_dict)
    
    # Add the new version
    success = prompt_library.add_new_template_version(template_id, new_template)
    assert success is True
    
    # Verify that getting the template returns the new version
    latest = prompt_library.get_template(template_id)
    assert latest.version == 2
    assert latest.system_prompt == "You are a specialized testing assistant."
    assert latest.updated_by_component == "test_harness"
    
    # Verify the version history
    history = prompt_library.get_version_history(template_id)
    assert len(history) == 2
    # Versions should be in ascending order
    assert history[0].version == 1
    assert history[1].version == 2


def test_get_version_history(prompt_library, sample_template):
    """
    Test that PromptLibrary.get_version_history returns the correct history of template versions.
    """
    template_id = sample_template["template_id"]
    
    # Initially should have just one version
    history = prompt_library.get_version_history(template_id)
    assert len(history) == 1
    assert history[0].version == 1
    
    # Add multiple versions
    for i in range(2, 5):
        # Update template content
        new_content = {
            "version": i,
            "system_prompt": f"You are version {i} of the assistant.",
            "version_notes": f"Test version {i}"
        }
        prompt_library.update_template(template_id, new_content)
    
    # Get history again
    history = prompt_library.get_version_history(template_id)
    assert len(history) == 4  # Should have 4 versions (1-4)
    
    # Check order and correctness
    for i, template in enumerate(history):
        assert template.version == i + 1
        if i > 0:  # Version 1 has the original system prompt
            assert template.system_prompt == f"You are version {i+1} of the assistant."
            assert template.version_notes == f"Test version {i+1}"


def test_template_optimization_fields(prompt_library, sample_template):
    """
    Test that the optimization-related fields are properly handled.
    """
    template_id = sample_template["template_id"]
    
    # Update with optimization fields
    optimization_metrics = {
        "error_rate": 0.35,
        "average_feedback_score": 0.6
    }
    
    new_content = {
        "updated_by_component": "AdaptiveLearningManager",
        "optimization_source": "error_rate",
        "optimization_metrics": optimization_metrics
    }
    
    updated_template = prompt_library.update_template(template_id, new_content)
    
    # Verify the optimization fields
    assert updated_template.updated_by_component == "AdaptiveLearningManager"
    assert updated_template.optimization_source == "error_rate"
    assert updated_template.optimization_metrics == optimization_metrics
    
    # Get the template and verify fields persist
    latest = prompt_library.get_template(template_id)
    assert latest.updated_by_component == "AdaptiveLearningManager"
    assert latest.optimization_source == "error_rate"
    assert latest.optimization_metrics == optimization_metrics
