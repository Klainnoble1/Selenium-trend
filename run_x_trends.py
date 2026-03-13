#!/usr/bin/env python3
"""
Run the X trends source only.
"""

import os

from dotenv import load_dotenv

from config import TREND_COUNTRIES
from source_pipeline import build_payload, enrich_trends_with_articles, save_payload, send_payload
from x_trends_source import fetch_x_trends

load_dotenv()


def main() -> None:
    headless = os.environ.get("HEADLESS", "true").lower() == "true"
    countries_filter = os.environ.get("COUNTRIES", "").strip()

    if countries_filter:
        geos = [g.strip().upper() for g in countries_filter.split(",")]
        countries = [c for c in TREND_COUNTRIES if c["geo"] in geos]
    else:
        countries = TREND_COUNTRIES

    if not countries:
        print("No countries to scrape. Set COUNTRIES=US,GB,CA,DE,CH or leave unset for all.")
        return

    print("Fetching X trends for:", [c["geo"] for c in countries])
    trends_by_country = []
    for country in countries:
        trends_by_country.append(
            {
                "country": country["name"],
                "geo": country["geo"],
                "trends": fetch_x_trends(country),
            }
        )

    trends_by_country = enrich_trends_with_articles(trends_by_country, headless=headless)
    payload = build_payload("x-trends-api", "live", trends_by_country)
    save_payload(payload, "x")
    send_payload(payload)


if __name__ == "__main__":
    main()
