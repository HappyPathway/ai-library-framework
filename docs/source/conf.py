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
    
    # Project modules that might not exist yet
    'ai', 'cloud', 'utils', 'utils.ai', 'utils.core', 'utils.cloud', 
    'utils.messaging', 'utils.storage', 'messaging', 'storage', 'workers',
    'agent', 'documentation', 'test', 'schemas',
    
    # Transitional package structure 
    'ailf.ai', 'ailf.core', 'ailf.cloud', 'ailf.messaging', 'ailf.storage',
    'ailf.mcp', 'ailf.workers', 'ailf.agent', 'ailf.schemas', 'ailf.communication',
]
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# Set environment variables to prevent errors
os.environ['GOOGLE_CLOUD_PROJECT'] = 'mock-project-id'
os.environ['AILF_CONFIG_PATH'] = '/tmp/mock-config'

# Add project directories to path for autodoc
# Add src directory for src-based imports (primary)
sys.path.insert(0, os.path.abspath('../../src'))
# Add project root for legacy module imports
sys.path.insert(0, os.path.abspath('../..'))
# Add examples directory to path for autodoc
sys.path.insert(0, os.path.abspath('../../examples'))

# Project information
project = 'Python Template Dev'
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
