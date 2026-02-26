"""
Get top search result URLs for a query (used to find articles for each trend).
Uses DuckDuckGo HTML via Selenium (DDG serves full results to browsers, minimal to plain requests).
"""

import re
import time
import urllib.parse


# Domains to skip (not article content; often empty or corporate homepages)
SKIP_DOMAINS = (
    "google.com", "youtube.com", "facebook.com", "twitter.com", "instagram.com",
    "tiktok.com", "linkedin.com", "duckduckgo.com", "wikipedia.org",
    "openai.com", "chatgpt.com", "tesla.com", "nvidia.com", "bestbuy.com",
)


def _should_skip(url: str) -> bool:
    lower = url.lower()
    for d in SKIP_DOMAINS:
        if d in lower:
            return True
    return False


def _extract_uddg_urls(html: str, count: int) -> list[str]:
    """Parse DDG HTML for uddg= links; return up to count real URLs."""
    urls = []
    # Match uddg=ENCODED (encoded URL can contain %26 for &)
    pattern = re.compile(r"uddg=([^&\"']+)")
    for match in pattern.finditer(html):
        if len(urls) >= count:
            break
        try:
            encoded = match.group(1)
            if "%" in encoded:
                real_url = urllib.parse.unquote(encoded)
            else:
                real_url = encoded
            if real_url.startswith("http") and real_url not in urls and not _should_skip(real_url):
                urls.append(real_url)
        except Exception:
            continue
    return urls[:count]


def get_top_search_urls(driver, query: str, count: int = 2) -> list[str]:
    """
    Load DuckDuckGo HTML search in the given driver and return top `count` result URLs.
    Appends " news" to the query so results are recent/news-oriented.
    Uses Selenium so DDG serves full HTML (they block or limit plain requests).
    """
    urls = []
    try:
        # Add " news" to get recent/news results instead of generic or corporate homepages
        search_query = f"{query} news" if query.strip() else query
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(search_query)
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
        urls = _extract_uddg_urls(html, count)
    except Exception as e:
        print(f"  DuckDuckGo failed for \"{query[:40]}...\": {e}")
    return urls


def get_top_search_urls_duckduckgo(query: str, count: int = 2) -> list[str]:
    """
    Standalone DDG fetch (requests only). May return [] if DDG serves minimal page to bots.
    Prefer using get_top_search_urls(driver, query, count) with a browser.
    """
    try:
        import requests
        r = requests.get(
            "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query),
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"},
            timeout=15,
        )
        r.raise_for_status()
        return _extract_uddg_urls(r.text, count)
    except Exception as e:
        print(f"  DuckDuckGo (requests) failed: {e}")
    return []
