"""
Shared pipeline helpers for source-specific trend runners.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import requests

from article_extractor import extract_article_content
from config import (
    MAX_ARTICLES_PER_TREND,
    MIN_ARTICLE_CONTENT_LENGTH,
    SEARCH_URLS_TO_TRY,
)
from google_search import get_top_search_urls
from n8n_sender import send_to_n8n
from trends_scraper import create_driver


def enrich_trends_with_articles(trends_by_country: list[dict[str, Any]], headless: bool = True) -> list[dict[str, Any]]:
    """
    For each trend, collect candidate URLs and keep only articles with real content.
    """
    print("Getting recent articles per trend (news search, skip empty until we have enough content)...")
    driver = create_driver(headless=headless)
    try:
        for country_data in trends_by_country:
            for trend in country_data["trends"]:
                keyword = trend.get("keyword", "")
                if not keyword:
                    trend["article_urls"] = []
                    continue
                existing_urls = [
                    u
                    for u in (trend.get("article_urls") or [])
                    if isinstance(u, str) and u.startswith("http")
                ]
                extra_urls = get_top_search_urls(driver, keyword, count=SEARCH_URLS_TO_TRY)
                urls = []
                for candidate in existing_urls + extra_urls:
                    if candidate not in urls:
                        urls.append(candidate)
                trend["_urls_to_try"] = urls
                if urls:
                    kw = keyword[:50].encode("ascii", "replace").decode("ascii")
                    source = trend.get("trend_source") or "google"
                    print(f"  [{country_data['geo']}/{source}] \"{kw}\" -> {len(urls)} URLs to try")
                time.sleep(0.8)
    finally:
        driver.quit()

    print("Fetching full content (skipping empty, using next until we have enough)...")
    for country_data in trends_by_country:
        for trend in country_data["trends"]:
            urls_to_try = trend.pop("_urls_to_try", []) or trend.get("article_urls", [])
            trend["article_urls"] = []
            trend["articles"] = []
            for url in urls_to_try:
                if len(trend["articles"]) >= MAX_ARTICLES_PER_TREND:
                    break
                art = extract_article_content(url)
                content = (art.get("content") or "").strip()
                if art.get("success") and len(content) >= MIN_ARTICLE_CONTENT_LENGTH:
                    trend["article_urls"].append(art["url"])
                    trend["articles"].append(
                        {
                            "url": art["url"],
                            "title": art.get("title") or "",
                            "content": content,
                            "success": True,
                        }
                    )
            if trend["articles"]:
                kw = (trend.get("keyword", "") or "")[:50].encode("ascii", "replace").decode("ascii")
                print(f"  \"{kw}\" -> {len(trend['articles'])} articles with content")

    return trends_by_country


def build_payload(source: str, timeframe: str, trends_by_country: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": source,
        "timeframe": timeframe,
        "countries": [
            {
                "country": row["country"],
                "geo": row["geo"],
                "trends": row["trends"],
            }
            for row in trends_by_country
        ],
    }


def save_payload(payload: dict[str, Any], source_slug: str) -> str:
    out_path = os.path.join(os.path.dirname(__file__), f"trends_output_{source_slug}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Saved payload to {out_path}")
    return out_path


def send_payload(payload: dict[str, Any]) -> None:
    webhook_url = (os.environ.get("N8N_WEBHOOK_URL") or "").strip()
    if webhook_url:
        result = send_to_n8n(payload, webhook_url)
        if result.get("success"):
            print("Sent to n8n successfully.")
        else:
            print("n8n send failed:", result.get("error") or result.get("response"))
    else:
        print("N8N_WEBHOOK_URL not set. Set it in .env to send to n8n.")

    openclaw_url = (os.environ.get("OPENCLAW_WEBHOOK_URL") or "").strip()
    if openclaw_url:
        for country_data in payload.get("countries", []):
            region = country_data.get("geo", "US")
            trends = [t.get("keyword", "").strip() for t in country_data.get("trends", []) if t.get("keyword")]
            if not trends:
                continue
            try:
                r = requests.post(
                    openclaw_url,
                    json={"trends": trends, "region": region},
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )
                if r.ok:
                    print(f"Open Claw ({region}): sent {len(trends)} trends.")
                else:
                    print(f"Open Claw ({region}): {r.status_code} {r.text[:200]}")
            except Exception as e:
                print(f"Open Claw ({region}): {e}")
    else:
        print("OPENCLAW_WEBHOOK_URL not set. Set it in .env to send to Open Claw.")
