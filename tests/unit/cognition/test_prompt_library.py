"""Tests for prompt library.

This module contains tests for the PromptLibrary class in ailf.cognition.prompt_library.
"""
import os
import json
import shutil
import tempfile
import time
import pytest

from ailf.cognition.prompt_library import PromptLibrary
from ailf.schemas.prompt_engineering import PromptTemplateV1, PromptLibraryConfig


class TestPromptLibrary:
    """Tests for PromptLibrary class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for prompt templates."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after tests
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_templates(self):
        """Create sample prompt templates."""
        template1 = PromptTemplateV1(
            template_id="weather_template",
            version=1,
            description="Template for weather queries",
            template_string="What is the weather like in {{location}}?",
            input_variables=["location"],
            metadata={"category": "weather"}
        )
        
        template2 = PromptTemplateV1(
            template_id="greeting_template",
            version=1,
            description="Template for greetings",
            template_string="Hello, {{name}}! How are you today?",
            input_variables=["name"],
            metadata={"category": "conversation"}
        )
        
        return [template1, template2]

    @pytest.fixture
    def prompt_library(self, temp_dir, sample_templates):
        """Create a PromptLibrary instance with sample templates."""
        config = PromptLibraryConfig(
            library_path=temp_dir,
            default_prompt_id="greeting_template",
            auto_save=False
        )
        library = PromptLibrary(config)
        
        # Add sample templates
        for template in sample_templates:
            library.add_template(template)
        
        return library

    def test_init_with_empty_directory(self, temp_dir):
        """Test initializing with an empty directory."""
        config = PromptLibraryConfig(library_path=temp_dir)
        library = PromptLibrary(config)
        
        assert len(library.list_template_ids()) == 0

    def test_init_with_templates_on_disk(self, temp_dir, sample_templates):
        """Test initializing with templates already on disk."""
        # Save templates to disk first
        os.makedirs(temp_dir, exist_ok=True)
        for template in sample_templates:
            filepath = os.path.join(temp_dir, f"{template.template_id}.json")
            with open(filepath, 'w') as f:
                json.dump(template.dict(), f)
        
        # Initialize library
        config = PromptLibraryConfig(library_path=temp_dir)
        library = PromptLibrary(config)
        
        # Check templates were loaded
        assert len(library.list_template_ids()) == 2
        assert "weather_template" in library.list_template_ids()
        assert "greeting_template" in library.list_template_ids()

    def test_add_template(self, prompt_library):
        """Test adding a new template."""
        new_template = PromptTemplateV1(
            template_id="news_template",
            version=1,
            description="Template for news searches",
            template_string="Find recent news about {{topic}}",
            input_variables=["topic"]
        )
        
        prompt_library.add_template(new_template)
        
        # Verify the template was added
        assert "news_template" in prompt_library.list_template_ids()
        retrieved = prompt_library.get_template("news_template")
        assert retrieved is not None
        assert retrieved.template_string == "Find recent news about {{topic}}"

    def test_add_template_with_same_id_higher_version(self, prompt_library, sample_templates):
        """Test adding a template with same ID but higher version."""
        # Create a new version of an existing template
        updated_template = PromptTemplateV1(
            template_id="weather_template",
            version=2,
            description="Updated template for weather queries",
            template_string="What's the current weather in {{location}}?",
            input_variables=["location"],
            metadata={"category": "weather", "updated": True}
        )
        
        prompt_library.add_template(updated_template)
        
        # Verify the template was updated
        retrieved = prompt_library.get_template("weather_template")
        assert retrieved.version == 2
        assert retrieved.description == "Updated template for weather queries"
        assert "updated" in retrieved.metadata
        
        # Verify version history is maintained
        history = prompt_library.get_version_history("weather_template")
        assert len(history) == 2
        assert history[0].version == 1
        assert history[1].version == 2

    def test_add_template_with_same_id_lower_version(self, prompt_library):
        """Test adding a template with same ID but lower version."""
        # First, update the existing template to version 2
        updated_template = PromptTemplateV1(
            template_id="weather_template",
            version=2,
            template_string="Updated template string"
        )
        prompt_library.add_template(updated_template)
        
        # Now try to add version 1 back
        original_template = PromptTemplateV1(
            template_id="weather_template",
            version=1,
            template_string="Original template string"
        )
        
        prompt_library.add_template(original_template)
        
        # Verify the template was NOT downgraded
        retrieved = prompt_library.get_template("weather_template")
        assert retrieved.version == 2
        assert retrieved.template_string == "Updated template string"

    def test_add_template_with_overwrite(self, prompt_library):
        """Test adding a template with overwrite=True."""
        # Create a template with the same ID but lower version
        older_template = PromptTemplateV1(
            template_id="weather_template",
            version=0,
            description="Deliberately older version",
            template_string="Older template string"
        )
        
        # Add with overwrite=True
        prompt_library.add_template(older_template, overwrite=True)
        
        # Verify the template was overwritten despite lower version
        retrieved = prompt_library.get_template("weather_template")
        assert retrieved.version == 0
        assert retrieved.description == "Deliberately older version"

    def test_get_template(self, prompt_library, sample_templates):
        """Test retrieving a template."""
        retrieved = prompt_library.get_template("weather_template")
        
        assert retrieved is not None
        assert retrieved.template_id == "weather_template"
        assert retrieved.template_string == "What is the weather like in {{location}}?"
        assert retrieved.input_variables == ["location"]

    def test_get_template_with_version(self, prompt_library):
        """Test retrieving a specific version of a template."""
        # Add a second version
        v2_template = PromptTemplateV1(
            template_id="weather_template",
            version=2,
            template_string="Updated template for version 2"
        )
        prompt_library.add_template(v2_template)
        
        # Retrieve specific versions
        v1 = prompt_library.get_template("weather_template", version=1)
        v2 = prompt_library.get_template("weather_template", version=2)
        
        assert v1 is not None
        assert v2 is not None
        assert v1.version == 1
        assert v2.version == 2
        assert v1.template_string != v2.template_string

    def test_get_nonexistent_template(self, prompt_library):
        """Test retrieving a non-existent template."""
        retrieved = prompt_library.get_template("nonexistent_template")
        
        assert retrieved is None

    def test_get_nonexistent_version(self, prompt_library):
        """Test retrieving a non-existent version of a template."""
        retrieved = prompt_library.get_template("weather_template", version=999)
        
        assert retrieved is None

    def test_get_default_template(self, prompt_library):
        """Test retrieving the default template."""
        default = prompt_library.get_default_template()
        
        assert default is not None
        assert default.template_id == "greeting_template"

    def test_list_template_ids(self, prompt_library, sample_templates):
        """Test listing all template IDs."""
        ids = prompt_library.list_template_ids()
        
        assert len(ids) == 2
        assert "weather_template" in ids
        assert "greeting_template" in ids

    def test_update_template(self, prompt_library):
        """Test updating a template with new content."""
        updates = {
            "description": "Updated weather template",
            "template_string": "What's the forecast for {{location}} on {{date}}?",
            "input_variables": ["location", "date"]
        }
        
        updated = prompt_library.update_template("weather_template", updates, "Added date parameter")
        
        assert updated is not None
        assert updated.version == 2  # Version should be incremented
        assert updated.description == "Updated weather template"
        assert updated.template_string == "What's the forecast for {{location}} on {{date}}?"
        assert updated.input_variables == ["location", "date"]
        assert updated.previous_version_id == "weather_template_v1"
        assert updated.version_notes == "Added date parameter"

    def test_update_nonexistent_template(self, prompt_library):
        """Test updating a non-existent template."""
        updates = {"description": "This shouldn't work"}
        
        result = prompt_library.update_template("nonexistent_template", updates)
        
        assert result is None

    def test_add_new_template_version(self, prompt_library):
        """Test adding a new version of a template."""
        new_version = PromptTemplateV1(
            template_id="weather_template",
            version=3,
            template_string="New version template string",
            previous_version_id="weather_template_v2"
        )
        
        result = prompt_library.add_new_template_version("weather_template", new_version)
        
        assert result is True
        retrieved = prompt_library.get_template("weather_template")
        assert retrieved.version == 3
        assert retrieved.template_string == "New version template string"

    def test_add_new_version_with_id_mismatch(self, prompt_library):
        """Test adding a new version with mismatched ID."""
        new_version = PromptTemplateV1(
            template_id="wrong_id",
            version=2,
            template_string="This should fail"
        )
        
        result = prompt_library.add_new_template_version("weather_template", new_version)
        
        assert result is False

    def test_get_version_history(self, prompt_library):
        """Test retrieving version history of a template."""
        # Add multiple versions
        prompt_library.update_template(
            "weather_template", 
            {"description": "Version 2"}, 
            "Update to version 2"
        )
        prompt_library.update_template(
            "weather_template", 
            {"description": "Version 3"}, 
            "Update to version 3"
        )
        
        history = prompt_library.get_version_history("weather_template")
        
        assert len(history) == 3
        assert history[0].version == 1
        assert history[1].version == 2
        assert history[2].version == 3
        assert history[0].description != history[1].description
        assert history[1].description != history[2].description

    def test_save_template_to_disk(self, temp_dir):
        """Test saving a template to disk."""
        # Create library with auto_save=True
        config = PromptLibraryConfig(library_path=temp_dir, auto_save=True)
        library = PromptLibrary(config)
        
        # Add a template
        template = PromptTemplateV1(
            template_id="save_test",
            version=1,
            template_string="Template to be saved"
        )
        library.add_template(template)
        
        # Check file was created
        expected_path = os.path.join(temp_dir, "save_test_v1.json")
        assert os.path.exists(expected_path)
        
        # Verify content
        with open(expected_path, 'r') as f:
            saved_content = json.load(f)
        assert saved_content["template_id"] == "save_test"
        assert saved_content["template_string"] == "Template to be saved"
