"""
Unit Tests for Scraper Service
"""
import pytest
from app.services.scraper import WebsiteScraper

def test_scraper_invalid_url():
    scraper = WebsiteScraper(timeout=2)
    res = scraper.scrape("")
    assert res["success"] is False
    assert "Invalid URL" in res["error"]

def test_scraper_fallback_on_unreachable():
    scraper = WebsiteScraper(timeout=1)
    res = scraper.scrape("https://this-domain-does-not-exist-12345xyz.com")
    # Even if unreachable, graceful degradation returns domain heuristic
    assert "title" in res
    assert "Company at" in res["title"]
