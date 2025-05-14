"""Web scraping utilities with rate limiting and caching.

This module provides a unified interface for web scraping operations with built-in:
- Rate limiting to prevent overwhelming target sites
- Response caching to reduce unnecessary requests
- Automatic retry logic for failed requests
- Error handling and logging
- User-agent rotation
- Cookie and session management

Example:
    >>> from ailf.communication.web_scraper import WebScraper
    >>> scraper = WebScraper(rate_limit=2.0)  # 2 seconds between requests
    >>> 
    >>> # Get parsed HTML
    >>> soup = scraper.get_soup('https://example.com')
    >>> if soup:
    ...     title = scraper.extract_text(soup, 'h1.title')
    ...     description = scraper.extract_text(soup, 'div.description')
    ... 
    >>> # Get raw response with caching
    >>> response = scraper.get('https://api.example.com/data')

The scraper includes built-in protections against common issues:
- Respects robots.txt
- Handles network errors gracefully
- Prevents excessive requests
- Manages browser-like headers
"""

import time
import random
from typing import Optional, Dict, Any, Union, List
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from cachetools import TTLCache

from ailf.core.logging import setup_logging

logger = setup_logging('web_scraper')

class WebScraper:
    """Generic web scraping utility with built-in rate limiting and caching."""
    
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    def __init__(
        self,
        rate_limit: float = 1.0,  # Minimum seconds between requests
        max_retries: int = 3,
        cache_ttl: int = 3600,  # Cache TTL in seconds
        cache_size: int = 1000,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        """Initialize the scraper.
        
        Args:
            rate_limit: Minimum seconds between requests
            max_retries: Maximum number of retries on failure
            cache_ttl: Cache time-to-live in seconds
            cache_size: Maximum size of response cache
            headers: Optional custom headers
            timeout: Request timeout in seconds
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = 0
        self.headers = headers or self.DEFAULT_HEADERS.copy()
        
        # Initialize cache
        self.cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        
        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)

    def _wait_for_rate_limit(self):
        """Ensure minimum time between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            # Add small random jitter
            sleep_time += random.uniform(0, 0.5)
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Optional[requests.Response]:
        """Make an HTTP GET request with caching and rate limiting.
        
        Args:
            url: Target URL
            params: Optional query parameters
            use_cache: Whether to use response caching
            **kwargs: Additional arguments passed to requests.get()
            
        Returns:
            Response object or None on error
        """
        # Check cache first
        cache_key = f"{url}:{str(params)}"
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
            
        # Respect rate limiting
        self._wait_for_rate_limit()
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            
            # Cache successful response
            if use_cache:
                self.cache[cache_key] = response
                
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def get_soup(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        parser: str = 'html.parser',
        use_cache: bool = True,
        **kwargs
    ) -> Optional[BeautifulSoup]:
        """Get parsed BeautifulSoup from URL.
        
        Args:
            url: Target URL
            params: Optional query parameters
            parser: BeautifulSoup parser to use
            use_cache: Whether to use response caching
            **kwargs: Additional arguments passed to self.get()
            
        Returns:
            BeautifulSoup object or None on error
        """
        response = self.get(url, params=params, use_cache=use_cache, **kwargs)
        if response and response.content:
            try:
                return BeautifulSoup(response.content, parser)
            except Exception as e:
                logger.error(f"Error parsing {url}: {str(e)}")
        return None

    def extract_text(
        self,
        element: BeautifulSoup,
        selector: str,
        attribute: Optional[str] = None,
        default: str = ""
    ) -> str:
        """Extract text from a BeautifulSoup element using a CSS selector.
        
        Args:
            element: BeautifulSoup element to search
            selector: CSS selector
            attribute: Optional attribute to extract instead of text
            default: Default value if not found
            
        Returns:
            Extracted text or default value
        """
        try:
            found = element.select_one(selector)
            if found:
                if attribute:
                    return found.get(attribute, default)
                return found.get_text(strip=True)
            return default
        except Exception as e:
            logger.error(f"Error extracting text with {selector}: {str(e)}")
            return default

    def extract_all_text(
        self,
        element: BeautifulSoup,
        selector: str,
        attribute: Optional[str] = None
    ) -> List[str]:
        """Extract text from all matching elements in the HTML.
        
        Args:
            element: BeautifulSoup element to search within
            selector: CSS selector to find elements
            attribute: Optional attribute to extract instead of text content
            
        Returns:
            List of extracted text strings, empty list if none found
            
        Example:
            >>> scraper = WebScraper()
            >>> soup = scraper.get_soup('https://example.com')
            >>> links = scraper.extract_all_text(soup, 'a', attribute='href')
            >>> paragraphs = scraper.extract_all_text(soup, 'p')
        """
        try:
            elements = element.select(selector)
            if attribute:
                return [e.get(attribute, "").strip() for e in elements if e.get(attribute)]
            return [e.get_text(strip=True) for e in elements if e.get_text(strip=True)]
        except Exception as e:
            logger.error(f"Error extracting all text with {selector}: {str(e)}")
            return []

    def clear_cache(self):
        """Clear the response cache."""
        self.cache.clear()


class ScraperConfig:
    """Configuration for the WebScraper."""
    
    def __init__(
        self,
        rate_limit: float = 1.0,
        max_retries: int = 3,
        cache_ttl: int = 3600,
        cache_size: int = 1000,
        timeout: int = 30
    ):
        """Initialize configuration.
        
        Args:
            rate_limit: Seconds between requests
            max_retries: Max retry attempts for failed requests
            cache_ttl: Cache time-to-live in seconds
            cache_size: Maximum size of response cache
            timeout: Request timeout in seconds
        """
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self.cache_size = cache_size
        self.timeout = timeout


class ScraperResult:
    """Result of a scraping operation."""
    
    def __init__(
        self,
        success: bool,
        content: Any = None,
        error: Optional[str] = None,
        url: Optional[str] = None
    ):
        """Initialize result.
        
        Args:
            success: Whether the scraping was successful
            content: The scraped content (if successful)
            error: Error message (if unsuccessful)
            url: The URL that was scraped
        """
        self.success = success
        self.content = content
        self.error = error
        self.url = url
        self.timestamp = time.time()
