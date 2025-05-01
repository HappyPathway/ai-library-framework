"""Integration tests for web scraper utilities."""
import pytest
from utils.web_scraper import WebScraper

@pytest.fixture
def scraper():
    """Create test web scraper instance."""
    return WebScraper(rate_limit=0.1)  # Short rate limit for testing

def test_get_with_caching(scraper):
    """Test HTTP GET with caching."""
    # First request
    response = scraper.get('https://httpbin.org/get')
    assert response is not None
    assert response.status_code == 200
    
    # Cached request
    cached_response = scraper.get('https://httpbin.org/get')
    assert cached_response is not None
    assert cached_response.status_code == 200
    assert cached_response == response  # Should be same object from cache

def test_rate_limiting(scraper):
    """Test rate limiting functionality."""
    import time
    
    start_time = time.time()
    
    # Make multiple requests
    for _ in range(3):
        response = scraper.get('https://httpbin.org/get')
        assert response is not None
        assert response.status_code == 200
    
    duration = time.time() - start_time
    assert duration >= 0.2  # Should take at least 2 * rate_limit

def test_html_parsing(scraper):
    """Test HTML parsing functionality."""
    url = 'https://httpbin.org/html'
    soup = scraper.get_soup(url)
    assert soup is not None
    
    # Extract title
    title = scraper.extract_text(soup, 'h1')
    assert title == "Herman Melville - Moby-Dick"
    
    # Extract all paragraphs
    paragraphs = scraper.extract_all_text(soup, 'p')
    assert len(paragraphs) > 0
