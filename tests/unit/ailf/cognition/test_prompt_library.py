"""Unit tests for the PromptLibrary class.

This module focuses on testing the PromptLibrary's ability to manage 
template versions and support the automated optimization workflow.
"""

import pytest
import json
import os
from unittest.mock import Mock, MagicMock, patch, mock_open
import tempfile
import time
import copy
from typing import Dict, Any, List

from ailf.cognition.prompt_library import PromptLibrary
from ailf.schemas.prompt_engineering import PromptTemplateV1, PromptLibraryConfig


class TestPromptLibrary:
    """Tests for the PromptLibrary class."""
    
    @pytest.fixture
    def sample_template(self):
        """Return a sample prompt template."""
        return PromptTemplateV1(
            template_id="test_template",
            version=1,
            description="A test template",
            system_prompt="You are a test assistant.",
            user_prompt_template="This is a test prompt with {placeholder}.",
            placeholders=["placeholder"],
            tags=["test"]
        )
    
    @pytest.fixture
    def prompt_library_mock(self, sample_template):
        """Create a mock PromptLibrary instance with predefined templates."""
        with patch('ailf.cognition.prompt_library.PromptLibrary._load_library'):
            config = PromptLibraryConfig(library_path="/mock/path")
            library = PromptLibrary(config)
            
            # Manually add templates to the library
            library._templates = {
                sample_template.template_id: copy.deepcopy(sample_template)
            }
            library._version_history = {
                sample_template.template_id: []
            }
            
            # Mock _save_template_to_disk to avoid file system operations
            library._save_template_to_disk = Mock(return_value=True)
            
            return library
    
    def test_add_template(self, prompt_library_mock, sample_template):
        """Test adding templates to the library."""
        library = prompt_library_mock
        
        # Create a new template
        new_template = PromptTemplateV1(
            template_id="new_template",
            version=1,
            description="A new test template",
            user_prompt_template="This is a new template with {var}.",
            placeholders=["var"]
        )
        
        # Add the new template
        library.add_template(new_template)
        
        # Verify it was added
        assert "new_template" in library._templates
        assert library._templates["new_template"].template_id == "new_template"
        
        # Test overwriting with a newer version
        updated_template = copy.deepcopy(new_template)
        updated_template.version = 2
        updated_template.description = "Updated description"
        
        library.add_template(updated_template)
        
        # Verify it was updated
        assert library._templates["new_template"].version == 2
        assert library._templates["new_template"].description == "Updated description"
        
        # Test not overwriting with an older version
        older_template = copy.deepcopy(new_template)
        older_template.version = 1
        older_template.description = "This shouldn't be used"
        
        library.add_template(older_template)
        
        # Verify it wasn't downgraded
        assert library._templates["new_template"].version == 2
        assert library._templates["new_template"].description == "Updated description"
        
        # Test forcing overwrite with an older version
        library.add_template(older_template, overwrite=True)
        
        # Verify it was downgraded due to forced overwrite
        assert library._templates["new_template"].version == 1
        assert library._templates["new_template"].description == "This shouldn't be used"
    
    def test_update_template(self, prompt_library_mock, sample_template):
        """Test updating an existing template with new content."""
        library = prompt_library_mock
        template_id = sample_template.template_id
        
        # Verify initial state
        assert library._templates[template_id].version == 1
        assert len(library._version_history[template_id]) == 0
        
        # Update the template
        new_content = {
            "system_prompt": "You are an updated assistant.",
            "user_prompt_template": "This is an updated prompt with {placeholder}.",
            "updated_by_component": "test_case"
        }
        
        updated = library.update_template(template_id, new_content, "Test update")
        
        # Verify the update
        assert updated is not None
        assert updated.version == 2
        assert updated.system_prompt == "You are an updated assistant."
        assert updated.user_prompt_template == "This is an updated prompt with {placeholder}."
        assert updated.updated_by_component == "test_case"
        assert updated.version_notes == "Test update"
        
        # Verify the template in the library was updated
        assert library._templates[template_id].version == 2
        assert library._templates[template_id].system_prompt == "You are an updated assistant."
        
        # Verify the previous version was stored in history
        assert len(library._version_history[template_id]) == 1
        assert library._version_history[template_id][0].version == 1
        assert library._version_history[template_id][0].system_prompt == "You are a test assistant."
        
        # Verify the save method was called
        assert library._save_template_to_disk.called
    
    def test_update_template_nonexistent(self, prompt_library_mock):
        """Test updating a template that doesn't exist."""
        library = prompt_library_mock
        
        # Try to update a non-existent template
        updated = library.update_template("nonexistent", {"system_prompt": "New prompt"})
        
        # Verify the update failed
        assert updated is None
        
        # Verify the save method was not called
        assert not library._save_template_to_disk.called
    
    def test_add_new_template_version(self, prompt_library_mock, sample_template):
        """Test adding a new version of an existing template."""
        library = prompt_library_mock
        template_id = sample_template.template_id
        
        # Create a new version of the template
        new_version = copy.deepcopy(sample_template)
        new_version.version = 2
        new_version.system_prompt = "You are version 2 of the assistant."
        new_version.updated_by_component = "AdaptiveLearningManager"
        new_version.optimization_source = "performance_metrics"
        
        # Add the new version
        success = library.add_new_template_version(template_id, new_version)
        
        # Verify it was added successfully
        assert success is True
        
        # Verify the template was updated
        assert library._templates[template_id].version == 2
        assert library._templates[template_id].system_prompt == "You are version 2 of the assistant."
        
        # Verify the previous version was stored in history
        assert len(library._version_history[template_id]) == 1
        assert library._version_history[template_id][0].version == 1
        
        # Try adding with ID mismatch
        mismatched = copy.deepcopy(new_version)
        mismatched.template_id = "wrong_id"
        
        success = library.add_new_template_version(template_id, mismatched)
        
        # Verify it failed
        assert success is False
        
        # Try adding for non-existent template
        success = library.add_new_template_version("nonexistent", new_version)
        
        # Verify it failed
        assert success is False
    
    def test_get_version_history(self, prompt_library_mock, sample_template):
        """Test retrieving version history for a template."""
        library = prompt_library_mock
        template_id = sample_template.template_id
        
        # Initially should have no history, just the current version
        history = library.get_version_history(template_id)
        assert len(history) == 1
        assert history[0].version == 1
        
        # Add multiple versions
        for i in range(2, 5):
            new_version = copy.deepcopy(sample_template)
            new_version.version = i
            new_version.system_prompt = f"You are version {i} of the assistant."
            library.add_template(new_version)
        
        # Get history again
        history = library.get_version_history(template_id)
        
        # Should have 4 versions (original + 3 updates)
        assert len(history) == 4
        
        # Check versions are in order
        for i, template in enumerate(history):
            assert template.version == i + 1
        
        # Check content of versions
        assert history[0].system_prompt == "You are a test assistant."
        for i in range(1, 4):
            assert history[i].system_prompt == f"You are version {i+1} of the assistant."
        
        # Test getting history for non-existent template
        history = library.get_version_history("nonexistent")
        assert len(history) == 0
    
    def test_get_template_by_version(self, prompt_library_mock, sample_template):
        """Test retrieving specific versions of a template."""
        library = prompt_library_mock
        template_id = sample_template.template_id
        
        # Add multiple versions
        for i in range(2, 4):
            new_version = copy.deepcopy(sample_template)
            new_version.version = i
            new_version.system_prompt = f"You are version {i} of the assistant."
            library.add_template(new_version)
        
        # Get version 1 (should be in history)
        v1 = library.get_template(template_id, version=1)
        assert v1 is not None
        assert v1.version == 1
        assert v1.system_prompt == "You are a test assistant."
        
        # Get version 2 (should be in history)
        v2 = library.get_template(template_id, version=2)
        assert v2 is not None
        assert v2.version == 2
        assert v2.system_prompt == "You are version 2 of the assistant."
        
        # Get version 3 (should be current)
        v3 = library.get_template(template_id, version=3)
        assert v3 is not None
        assert v3.version == 3
        assert v3.system_prompt == "You are version 3 of the assistant."
        
        # Get non-existent version
        v4 = library.get_template(template_id, version=4)
        assert v4 is None
        
        # Get latest version (no version specified)
        latest = library.get_template(template_id)
        assert latest is not None
        assert latest.version == 3
        assert latest.system_prompt == "You are version 3 of the assistant."
