"""
Fetch country headlines from NewsAPI and map them into the existing trend payload shape.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from config import API_REQUEST_TIMEOUT, MAX_NEWSAPI_TRENDS_PER_COUNTRY, USER_AGENT

NEWSAPI_COUNTRY_MAP = {
    "US": "us",
    "GB": "gb",
    "CA": "ca",
    "DE": "de",
    "CH": "ch",
}


def fetch_newsapi_trends(country: dict[str, str]) -> list[dict[str, Any]]:
    """
    Return a list of trend items in the existing payload shape:
    { keyword, article_urls, trend_source }
    """
    api_key = (os.environ.get("NEWSAPI_KEY") or "").strip()
    if not api_key:
        return []

    newsapi_country = NEWSAPI_COUNTRY_MAP.get(country["geo"])
    if not newsapi_country:
        return []

    try:
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "country": newsapi_country,
                "pageSize": MAX_NEWSAPI_TRENDS_PER_COUNTRY,
                "apiKey": api_key,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=API_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(f"NewsAPI failed for {country['geo']}: {exc}")
        return []

    articles = payload.get("articles") or []
    results: list[dict[str, Any]] = []
    seen_keywords: set[str] = set()

    for article in articles:
        title = str(article.get("title") or "").strip()
        url = str(article.get("url") or "").strip()
        if not title or not url:
            continue
        keyword = title.split(" - ")[0].strip()
        lowered = keyword.lower()
        if len(keyword) < 2 or lowered in seen_keywords:
            continue
        seen_keywords.add(lowered)
        results.append(
            {
                "keyword": keyword,
                "article_urls": [url],
                "trend_source": "newsapi",
            }
        )
        if len(results) >= MAX_NEWSAPI_TRENDS_PER_COUNTRY:
            break

    return results
