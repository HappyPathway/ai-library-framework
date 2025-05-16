"""AILF Schemas for Feedback Systems.

This package contains Pydantic models used by the ailf.feedback module,
primarily for interaction logging and feedback data structures.

Key Schemas:
    LoggedInteraction: Defines the structure for a detailed log of an agent interaction.
"""

# Import local model only to avoid circular imports
from .models import LoggedInteraction

# Export all the necessary names - they'll be imported directly from the parent module
__all__ = [
    "LoggedInteraction",
]
