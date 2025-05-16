"""Manages a library of prompt templates for AILF agents."""

import json
import os
import logging
import time
import copy
from typing import Any, Dict, Optional, List, Tuple

from ailf.schemas.prompt_engineering import PromptTemplateV1, PromptLibraryConfig

logger = logging.getLogger(__name__)

class PromptLibrary:
    """
    Manages loading, storing, and accessing versioned prompt templates.
    Templates can be loaded from a directory of JSON files or potentially other sources.
    """

    def __init__(self, config: PromptLibraryConfig):
        """
        Initializes the PromptLibrary.

        :param config: Configuration for the prompt library, including the path to template files.
        :type config: PromptLibraryConfig
        """
        self.config = config
        self._templates: Dict[str, PromptTemplateV1] = {}
        self._version_history: Dict[str, List[PromptTemplateV1]] = {}  # Store version history
        self._load_library()

    def _load_library(self) -> None:
        """
        Loads prompt templates from the configured source (e.g., directory).
        Currently supports loading from a directory of JSON files.
        Each JSON file should represent a PromptTemplateV1 schema.
        The filename (without .json) is used as the template_id if not present in the file.
        """
        if not self.config.library_path or not os.path.isdir(self.config.library_path):
            logger.warning(f"Prompt library path '{self.config.library_path}' is not a valid directory. No templates loaded.")
            return

        logger.info(f"Loading prompt templates from: {self.config.library_path}")
        for filename in os.listdir(self.config.library_path):
            if filename.endswith(".json"):
                filepath = os.path.join(self.config.library_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        template_data = json.load(f)
                    
                    # Ensure template_id is present, using filename if necessary
                    if 'template_id' not in template_data:
                        template_data['template_id'] = filename[:-5] # Remove .json
                    
                    template = PromptTemplateV1(**template_data)
                    self.add_template(template, overwrite=True) # Overwrite if loaded template is newer or same
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {filepath}: {e}")
                except Exception as e: # Catch Pydantic validation errors or other issues
                    logger.error(f"Error loading template from {filepath}: {e}")
        logger.info(f"Loaded {len(self._templates)} prompt templates.")

    def add_template(self, template: PromptTemplateV1, overwrite: bool = False) -> None:
        """
        Adds a new prompt template to the library or updates an existing one.
        If a template with the same id already exists, it's only updated if the new
        template has a higher version or if overwrite is True.

        :param template: The PromptTemplateV1 object to add.
        :type template: PromptTemplateV1
        :param overwrite: If True, always overwrite an existing template with the same ID,
                          regardless of version. Defaults to False.
        :type overwrite: bool
        """
        if template.template_id in self._templates:
            existing_template = self._templates[template.template_id]
            
            # Add to version history if not already there
            if template.template_id not in self._version_history:
                self._version_history[template.template_id] = []
            
            if overwrite or template.version > existing_template.version:
                # Archive the current version in history
                self._version_history[template.template_id].append(copy.deepcopy(existing_template))
                
                # Update to new version
                self._templates[template.template_id] = copy.deepcopy(template)
                logger.info(f"Updated template '{template.template_id}' to version {template.version}.")
                
                # Save to disk if auto_save is enabled
                if self.config.auto_save:
                    self._save_template_to_disk(template)
            elif template.version < existing_template.version:
                logger.info(f"Skipped adding template '{template.template_id}' version {template.version} (older than existing version {existing_template.version}).")
            else: # Same version, not overwriting
                logger.info(f"Skipped adding template '{template.template_id}' version {template.version} (same as existing, overwrite=False).")
        else:
            # New template, add it
            self._templates[template.template_id] = copy.deepcopy(template)
            self._version_history[template.template_id] = []
            logger.info(f"Added new template '{template.template_id}' version {template.version}.")
            
            # Save to disk if auto_save is enabled
            if self.config.auto_save:
                self._save_template_to_disk(template)

    def get_template(self, template_id: str, version: Optional[int] = None) -> Optional[PromptTemplateV1]:
        """
        Retrieves a specific prompt template by its ID and optionally by version.
        If version is not specified, it returns the latest version of the template.

        :param template_id: The ID of the prompt template to retrieve.
        :type template_id: str
        :param version: The specific version of the template.
        :type version: Optional[int]
        :return: The PromptTemplateV1 object if found, otherwise None.
        :rtype: Optional[PromptTemplateV1]
        """
        if version is not None:
            # Check the version history for this specific version
            if template_id in self._version_history:
                for hist_template in self._version_history[template_id]:
                    if hist_template.version == version:
                        return copy.deepcopy(hist_template)
            
            # Check if the current template matches the requested version
            template = self._templates.get(template_id)
            if template and template.version == version:
                return copy.deepcopy(template)
            elif template: # Template exists but version mismatch
                logger.warning(f"Template '{template_id}' found, but version {template.version} does not match requested version {version}.")
                return None 
            return None # Template ID not found
        
        # Return the latest version
        template = self._templates.get(template_id)
        return copy.deepcopy(template) if template else None

    def get_default_template(self) -> Optional[PromptTemplateV1]:
        """
        Retrieves the default prompt template specified in the library configuration.

        :return: The default PromptTemplateV1 object if configured and found, otherwise None.
        :rtype: Optional[PromptTemplateV1]
        """
        if self.config.default_prompt_id:
            return self.get_template(self.config.default_prompt_id)
        return None

    def list_template_ids(self) -> List[str]:
        """
        Lists the IDs of all available prompt templates in the library.

        :return: A list of template IDs.
        :rtype: List[str]
        """
        return list(self._templates.keys())

    def update_template(self, template_id: str, new_content: Dict[str, Any], 
                      version_notes: Optional[str] = None) -> Optional[PromptTemplateV1]:
        """
        Update an existing template with new content and create a new version.
        
        :param template_id: The ID of the template to update.
        :type template_id: str
        :param new_content: Dictionary with fields to update in the template.
        :type new_content: Dict[str, Any]
        :param version_notes: Optional notes explaining the changes in this version.
        :type version_notes: Optional[str]
        :return: The updated template, or None if template not found.
        :rtype: Optional[PromptTemplateV1]
        """
        template = self.get_template(template_id)
        if not template:
            logger.error(f"Cannot update template '{template_id}': not found in library.")
            return None
            
        # Create a copy of the template to update
        updated_template = copy.deepcopy(template)
        
        # Update timestamp
        updated_template.updated_at = time.time()
        
        # Set previous version reference
        updated_template.previous_version_id = f"{template_id}_v{template.version}"
        
        # Increment version
        updated_template.version += 1
        
        # Add version notes if provided
        if version_notes:
            updated_template.version_notes = version_notes
            
        # Update fields from new_content
        for key, value in new_content.items():
            if hasattr(updated_template, key):
                setattr(updated_template, key, value)
            else:
                logger.warning(f"Ignoring unknown field '{key}' when updating template '{template_id}'.")
                
        # Add the updated template to the library
        self.add_template(updated_template, overwrite=True)
        
        return updated_template

    def add_new_template_version(self, template_id: str, 
                               new_template: PromptTemplateV1) -> bool:
        """
        Add a new version of a template that has already been constructed.
        
        :param template_id: The ID of the original template.
        :type template_id: str
        :param new_template: The new template object.
        :type new_template: PromptTemplateV1
        :return: True if successful, False otherwise.
        :rtype: bool
        """
        # Check if the template exists
        if template_id not in self._templates:
            logger.error(f"Cannot add new version: template '{template_id}' not found.")
            return False
            
        # Verify the new template has the correct ID
        if new_template.template_id != template_id:
            logger.error(f"Template ID mismatch: expected '{template_id}', got '{new_template.template_id}'.")
            return False
            
        # Add the new template, which will handle versioning
        self.add_template(new_template, overwrite=True)
        return True

    def get_version_history(self, template_id: str) -> List[PromptTemplateV1]:
        """
        Get the version history of a template.
        
        :param template_id: The ID of the template.
        :type template_id: str
        :return: List of historical versions.
        :rtype: List[PromptTemplateV1]
        """
        history = []
        
        # Add historical versions
        if template_id in self._version_history:
            history = [copy.deepcopy(t) for t in self._version_history[template_id]]
        
        # Add current version if it exists
        current = self._templates.get(template_id)
        if current:
            history.append(copy.deepcopy(current))
            
        # Sort by version
        history.sort(key=lambda t: t.version)
        
        return history

    def _save_template_to_disk(self, template: PromptTemplateV1) -> bool:
        """
        Save a template to disk.
        
        :param template: The template to save.
        :type template: PromptTemplateV1
        :return: True if saved successfully, False otherwise.
        :rtype: bool
        """
        if not self.config.library_path:
            logger.warning("Cannot save template: library_path not configured.")
            return False
            
        os.makedirs(self.config.library_path, exist_ok=True)
        
        # Create a filename based on template ID and version
        filename = f"{template.template_id}_v{template.version}.json"
        filepath = os.path.join(self.config.library_path, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(template.dict(), f, indent=2)
            logger.info(f"Saved template to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving template to {filepath}: {e}")
            return False
