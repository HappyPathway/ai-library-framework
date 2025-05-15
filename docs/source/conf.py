"""Sphinx configuration for Python Template Dev documentation."""

import os
import sys
from unittest.mock import MagicMock


# Mock external libraries that might not be installed
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()


MOCK_MODULES = [
    # External AI services
    'anthropic', 'openai', 'google.generativeai', 'pydantic_ai', 
    
    # Google Cloud modules
    'google.cloud', 'google.cloud.storage', 'google.cloud.secretmanager',
    'google.cloud.exceptions', 'google.api_core', 'google.oauth2',
    
    # Messaging and network modules
    'zmq', 'redis', 'fastapi', 'mcp', 'websockets', 'aiohttp',
    
    # Database and storage
    'sqlalchemy', 'sqlalchemy.orm', 'sqlalchemy.ext',
    
    # External/utility modules
    'ai', 'cloud', 'utils', 'utils.ai', 'utils.core', 'utils.cloud', 
    'utils.messaging', 'utils.storage', 'messaging', 'storage', 'workers',
    'agent', 'documentation', 'test', 'schemas',
    'cognition',
    
    # Redis-related modules that cause import errors
    'redis.asyncio',
    
    # NOTE: We're no longer mocking the internal ailf modules below, so they can be properly documented
    # If you get import errors during doc builds, add specific problematic modules
]
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# Set environment variables to prevent errors
os.environ['GOOGLE_CLOUD_PROJECT'] = 'mock-project-id'
os.environ['AILF_CONFIG_PATH'] = '/tmp/mock-config'

# Add project directories to path for autodoc
# Add examples directory to path for autodoc
sys.path.insert(0, os.path.abspath('../../examples'))
# Add src directory for src-based imports (primary)
sys.path.insert(0, os.path.abspath('../../src'))
# Comment out the legacy path to avoid conflicts
# sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'AI Library Framework (AILF)'
copyright = '2025, David Arnold'
author = 'David Arnold'
version = '1.0'
release = '1.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'myst_parser',
    'sphinx_markdown_builder'
]

# Use MyST parser for Markdown
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Output format configuration
primary_domain = None
highlight_language = 'python'
html_sourcelink_suffix = ''

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Other settings
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'venv']

# HTML output settings
html_theme = 'groundwork'
html_theme_options = {
    'github_user': 'HappyPathway',  # Your GitHub username
    'github_repo': 'ai-library-framework',  # Your repository name
    'github_banner': True,  # Show GitHub banner
    'show_related': True,  # Show related links
    'sidebar_width': '240px',  # Width of the sidebar
    'sidebar_collapse': False,  # Collapse the sidebar by default
    'stickysidebar': True,  # Make the sidebar sticky
    'logo': "logo.png",  # Path to your logo, relative to _static
    'logo_name': False,  # Display the project name under the logo
    'description': 'AI Agent Development Framework',  # Project description
}
html_static_path = ['_static']
html_css_files = ['custom.css']
