"""
Resilient Web Scraping Service
------------------------------
Extracts structured intelligence from a prospect company's website:
- Title, Meta Description, OpenGraph tags
- Core headings (H1, H2) summarizing offerings
- Cleaned body text snippet
- Heuristic fallback in case of rate limits or Cloudflare bot blocks.

SYSTEM DESIGN / RESILIENCE NOTE:
- Web scraping in high-volume outbound (1,000 leads/day) is prone to network latency and bot blockers.
- We implement:
  1. Strict timeouts (12s max) to prevent blocking worker threads.
  2. Realistic browser headers (User-Agent, Accept-Language).
  3. Clean text sanitization removing scripts, styles, navigation bars, and cookie banners.
  4. Non-fatal graceful degradation: Returns heuristic domain analysis if target website is unreachable.
"""

from typing import Dict, Any, Tuple
import re
import requests
from bs4 import BeautifulSoup
from app.core.config import settings
from app.core.logger import logger


class WebsiteScraper:
    """Extracts prospect brand context and positioning from their web presence."""

    def __init__(self, timeout: int = settings.SCRAPER_TIMEOUT_SECONDS):
        self.timeout = timeout
        self.headers = {
            "User-Agent": settings.SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrapes a target website and returns clean metadata & body text.
        Always returns a structured dict even if scraping encounters an error.
        """
        result = {
            "url": url,
            "title": "",
            "meta_description": "",
            "headings": [],
            "body_snippet": "",
            "success": False,
            "error": None
        }

        if not url or not isinstance(url, str):
            result["error"] = "Invalid URL provided"
            return result

        cleaned_url = url.strip()
        if not cleaned_url.startswith(("http://", "https://")):
            cleaned_url = "https://" + cleaned_url

        try:
            response = requests.get(
                cleaned_url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract Title
            title_tag = soup.find("title")
            result["title"] = title_tag.get_text(strip=True) if title_tag else ""

            # Extract Meta Description (standard or OpenGraph)
            meta_desc = (
                soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or
                soup.find("meta", attrs={"property": "og:description"})
            )
            if meta_desc and meta_desc.get("content"):
                result["meta_description"] = meta_desc["content"].strip()

            # Extract Top Headings (H1 & H2 give immediate value proposition insight)
            headings = []
            for tag in soup.find_all(["h1", "h2"]):
                text = tag.get_text(strip=True)
                if text and len(text) > 4 and text not in headings:
                    headings.append(text)
            result["headings"] = headings[:6]

            # Strip non-informative tags before body extraction
            for unwanted in soup(["script", "style", "nav", "footer", "noscript", "svg", "header"]):
                unwanted.decompose()

            raw_text = soup.get_text(separator=" ", strip=True)
            # Normalize whitespace
            cleaned_text = re.sub(r"\s+", " ", raw_text)
            # Keep first 1200 characters for token-efficient LLM context
            result["body_snippet"] = cleaned_text[:1200]
            result["success"] = True

        except requests.exceptions.RequestException as exc:
            logger.warning(f"Failed to scrape {cleaned_url}: {exc}")
            result["error"] = str(exc)
            # Graceful fallback: synthesize minimal context from domain name
            domain = cleaned_url.split("//")[-1].split("/")[0].replace("www.", "")
            result["title"] = f"Company at {domain}"
            result["meta_description"] = f"Digital presence for {domain}"

        return result


scraper = WebsiteScraper()
