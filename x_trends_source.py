"""
Fetch X location trends using the v1.1 trends/place endpoint with OAuth1.
"""

from __future__ import annotations

import os
from typing import Any

import requests
from requests_oauthlib import OAuth1

from config import API_REQUEST_TIMEOUT, MAX_X_TRENDS_PER_COUNTRY, USER_AGENT, X_WOEIDS


def _get_oauth() -> OAuth1 | None:
    api_key = (os.environ.get("X_API_KEY") or "").strip()
    api_key_secret = (os.environ.get("X_API_KEY_SECRET") or "").strip()
    access_token = (os.environ.get("X_ACCESS_TOKEN") or "").strip()
    access_token_secret = (os.environ.get("X_ACCESS_TOKEN_SECRET") or "").strip()

    if not (api_key and api_key_secret and access_token and access_token_secret):
        return None

    return OAuth1(api_key, api_key_secret, access_token, access_token_secret)


def fetch_x_trends(country: dict[str, str]) -> list[dict[str, Any]]:
    """
    Return a list of trend items in the existing payload shape:
    { keyword, article_urls, trend_source }
    """
    oauth = _get_oauth()
    if oauth is None:
        return []

    woeid = X_WOEIDS.get(country["geo"])
    if not woeid:
        return []

    try:
        response = requests.get(
            "https://api.twitter.com/1.1/trends/place.json",
            params={"id": woeid},
            auth=oauth,
            headers={"User-Agent": USER_AGENT},
            timeout=API_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(f"X trends failed for {country['geo']}: {exc}")
        return []

    if not isinstance(payload, list) or not payload:
        return []

    trend_list = payload[0].get("trends") or []
    results: list[dict[str, Any]] = []
    seen_keywords: set[str] = set()

    for trend in trend_list:
        name = str(trend.get("name") or "").strip()
        if not name:
            continue
        keyword = name.lstrip("#").strip()
        if len(keyword) < 2:
            continue
        lowered = keyword.lower()
        if lowered in seen_keywords:
            continue
        seen_keywords.add(lowered)
        results.append(
            {
                "keyword": keyword,
                "article_urls": [],
                "trend_source": "x",
            }
        )
        if len(results) >= MAX_X_TRENDS_PER_COUNTRY:
            break

    return results
