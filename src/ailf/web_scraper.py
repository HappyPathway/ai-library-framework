"""Web scraping utilities.

DEPRECATED: This module has been moved to ailf.communication.web_scraper.
Please update your imports to: from ailf.communication.web_scraper import WebScraper

This module provides tools for retrieving and parsing web content.
"""

import warnings

warnings.warn(
    "The ailf.web_scraper module is deprecated. Use ailf.communication.web_scraper instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location
from ailf.communication.web_scraper import (
    WebScraper,
    ScraperConfig,
    ScraperResult
)

__all__ = [
    "WebScraper",
    "ScraperConfig",
    "ScraperResult"
]
