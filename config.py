"""
Configuration for Google Trends scraper.
Geo codes: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
"""

# Countries to scrape (4h real-time trends)
# US, UK, Canada, Germany, Switzerland
TREND_COUNTRIES = [
    {"geo": "US", "name": "United States", "hl": "en-US"},
    {"geo": "GB", "name": "United Kingdom", "hl": "en-GB"},
    {"geo": "CA", "name": "Canada", "hl": "en-CA"},
    {"geo": "DE", "name": "Germany", "hl": "de"},
    {"geo": "CH", "name": "Switzerland", "hl": "de"},
]

# Trending now URL: geo=XX, hours=4 for past 4 hours
# https://trends.google.com/trending?geo=US&hours=4
TRENDS_BASE_URL = "https://trends.google.com/trending"
TRENDS_HOURS = 4

# Max trends to process per country (to avoid rate limits)
MAX_TRENDS_PER_COUNTRY = 10

# Max articles to keep per trend (only count those with real content)
MAX_ARTICLES_PER_TREND = 2

# How many search result URLs to try per trend (we skip empty/failed until we have enough with content)
SEARCH_URLS_TO_TRY = 8

# Minimum article content length to count as "has content"
MIN_ARTICLE_CONTENT_LENGTH = 150

# Request timeout for fetching article content (seconds)
ARTICLE_REQUEST_TIMEOUT = 15

# User agent for requests (some sites block default)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
