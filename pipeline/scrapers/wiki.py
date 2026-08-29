"""
pipeline/scrapers/wiki.py
==========================
Free scrapers for Wikipedia and Fandom wikis (no API key required).

Wikipedia:  Uses the Wikipedia REST summary endpoint.
Fandom:     Scrapes the Fandom wiki page using httpx + BeautifulSoup4.

Both functions return plain text. Empty string means "nothing useful found" —
the caller decides whether to continue without this source.
"""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"


# ------------------------------------------------------------------
# Wikipedia
# ------------------------------------------------------------------
def get_wikipedia_summary(query: str) -> str:
    """
    Return the Wikipedia introductory extract for a topic.

    Tries direct slug lookup first; falls back to search API if 404.
    Returns empty string if nothing found.
    """
    slug = query.strip().replace(" ", "_")
    with httpx.Client(follow_redirects=True, timeout=10.0) as client:
        r = client.get(f"{WIKI_SUMMARY_URL}/{slug}", headers={"Accept": "application/json"})

        if r.status_code == 404:
            # Try the search API to find the right title
            r2 = client.get(
                WIKI_SEARCH_URL,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": 1,
                },
            )
            results = r2.json().get("query", {}).get("search", [])
            if not results:
                return ""
            slug = results[0]["title"].replace(" ", "_")
            r = client.get(f"{WIKI_SUMMARY_URL}/{slug}", headers={"Accept": "application/json"})

        if r.status_code != 200:
            return ""

        return r.json().get("extract", "")


# ------------------------------------------------------------------
# Fandom
# ------------------------------------------------------------------
def get_fandom_page(slug: str, wiki_subdomain: str) -> str:
    """
    Scrape a Fandom wiki article and return the first few paragraphs as text.

    Args:
        slug:            The article slug, e.g. "Batman" or "Bruce_Wayne"
        wiki_subdomain:  The Fandom subdomain, e.g. "dccomics", "marvelcinematicuniverse"

    Returns:
        Plain text of the first 5 non-trivial paragraphs, or empty string on failure.

    Examples:
        get_fandom_page("Batman", "dccomics")
        get_fandom_page("Tony_Stark", "marvelcinematicuniverse")
        get_fandom_page("Cooper", "interstellarfilm")
    """
    url = f"https://{wiki_subdomain}.fandom.com/wiki/{slug}"
    try:
        with httpx.Client(follow_redirects=True, timeout=12.0) as client:
            r = client.get(url, headers={"User-Agent": "IdeAgentBot/1.0 (research project)"})
            if r.status_code != 200:
                return ""

        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.find("div", class_="mw-parser-output")
        if not content:
            return ""

        paragraphs = [
            p.get_text(" ", strip=True)
            for p in content.find_all("p")
            if len(p.get_text(strip=True)) > 60  # skip navbox / short filler paragraphs
        ]
        return " ".join(paragraphs[:5])

    except Exception:
        return ""
