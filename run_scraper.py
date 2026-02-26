#!/usr/bin/env python3
"""
Scrape Google Trends (4h real-time) for US, UK, Canada, Germany, Switzerland.
Fetch full content from top articles for each trend and send to n8n.

Usage:
  pip install -r requirements.txt
  set N8N_WEBHOOK_URL=https://your-n8n-instance/webhook/...
  python run_scraper.py

  Optional: HEADLESS=false to show browser, COUNTRIES=US,GB to limit countries.
"""

import os
import json
import time
from dotenv import load_dotenv

from config import TREND_COUNTRIES, MAX_ARTICLES_PER_TREND, SEARCH_URLS_TO_TRY, MIN_ARTICLE_CONTENT_LENGTH
from trends_scraper import scrape_all_trends, create_driver
from google_search import get_top_search_urls
from article_extractor import extract_article_content
from n8n_sender import send_to_n8n

load_dotenv()


def main():
    headless = os.environ.get("HEADLESS", "true").lower() == "true"
    countries_filter = os.environ.get("COUNTRIES", "").strip()
    webhook_url = os.environ.get("N8N_WEBHOOK_URL")

    if countries_filter:
        geos = [g.strip().upper() for g in countries_filter.split(",")]
        countries = [c for c in TREND_COUNTRIES if c["geo"] in geos]
    else:
        countries = TREND_COUNTRIES

    if not countries:
        print("No countries to scrape. Set COUNTRIES=US,GB,CA,DE,CH or leave unset for all.")
        return

    print("Scraping Google Trends (real-time / 4h) for:", [c["geo"] for c in countries])
    trends_by_country = scrape_all_trends(headless=headless, countries=countries)

    # For each trend: fetch more URLs (news-oriented), then keep only articles with real content until we have enough
    print("Getting recent articles per trend (news search, skip empty until we have 2 with content)...")
    driver = create_driver(headless=headless)
    try:
        for country_data in trends_by_country:
            for trend in country_data["trends"]:
                keyword = trend.get("keyword", "")
                if not keyword:
                    trend["article_urls"] = []
                    continue
                urls = get_top_search_urls(driver, keyword, count=SEARCH_URLS_TO_TRY)
                trend["_urls_to_try"] = urls
                if urls:
                    kw = keyword[:50].encode("ascii", "replace").decode("ascii")
                    print(f"  [{country_data['geo']}] \"{kw}\" -> {len(urls)} URLs to try")
                time.sleep(0.8)
    finally:
        driver.quit()

    # Fetch content; for each trend, keep only articles with content and take up to MAX_ARTICLES_PER_TREND (skip empty, go to next)
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
                    trend["articles"].append({
                        "url": art["url"],
                        "title": art.get("title") or "",
                        "content": content,
                        "success": True,
                    })
            if trend["articles"]:
                kw = (trend.get("keyword", "") or "")[:50].encode("ascii", "replace").decode("ascii")
                print(f"  \"{kw}\" -> {len(trend['articles'])} articles with content")

    # Build payload for n8n
    payload = {
        "source": "google-trends-selenium",
        "timeframe": "4h",
        "countries": [
            {
                "country": r["country"],
                "geo": r["geo"],
                "trends": r["trends"],
            }
            for r in trends_by_country
        ],
    }

    # Save to file for inspection
    out_path = os.path.join(os.path.dirname(__file__), "trends_output.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Saved payload to {out_path}")

    if webhook_url:
        result = send_to_n8n(payload, webhook_url)
        if result.get("success"):
            print("Sent to n8n successfully.")
        else:
            print("n8n send failed:", result.get("error") or result.get("response"))
    else:
        print("N8N_WEBHOOK_URL not set. Set it in .env to send to n8n.")


if __name__ == "__main__":
    main()
