"""
Scrape Google Trends real-time (4h) for configured countries.
Returns trend keywords and related article URLs for each country.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from config import (
    TREND_COUNTRIES,
    TRENDS_BASE_URL,
    TRENDS_HOURS,
    MAX_TRENDS_PER_COUNTRY,
    MAX_ARTICLES_PER_TREND,
)


def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create headless Chrome/Chromium driver. In Docker (CHROME_BIN set) uses Chromium."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    chrome_bin = os.environ.get("CHROME_BIN")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    if chrome_bin:
        options.binary_location = chrome_bin
    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def scrape_country_trends(driver: webdriver.Chrome, country: dict) -> list[dict]:
    """
    Scrape one country's Trending now page (e.g. past 4h).
    URL: https://trends.google.com/trending?geo=US&hours=4
    Returns list of { "keyword": str, "article_urls": list[str] }.
    """
    geo = country["geo"]
    url = f"{TRENDS_BASE_URL}?geo={geo}&hours={TRENDS_HOURS}"
    trends_data = []

    try:
        driver.get(url)
        time.sleep(5)  # Allow table/content to load

        # Page has table: Trends (title) | Search volume | Started | Trend breakdown
        # Try table rows first (each row = one trend)
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr, tr[role='row'], div[role='row']")
        if not rows:
            rows = driver.find_elements(By.TAG_NAME, "tr")
        seen_keywords = set()
        for row in rows:
            if len(trends_data) >= MAX_TRENDS_PER_COUNTRY:
                break
            try:
                # First cell/column usually has the trend title (link or text)
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    cells = row.find_elements(By.CSS_SELECTOR, "div[role='cell']")
                links_in_row = row.find_elements(By.TAG_NAME, "a")
                keyword = None
                article_urls = []
                for a in links_in_row:
                    href = a.get_attribute("href") or ""
                    text = (a.text or "").strip()
                    if "google.com" in href or "gstatic.com" in href:
                        continue
                    if href.startswith("http") and href not in article_urls:
                        article_urls.append(href)
                    if text and 2 <= len(text) <= 150 and text not in seen_keywords:
                        if not text.isdigit() and text.lower() not in ("news", "article", "stories", "search trends"):
                            keyword = keyword or text
                if not keyword and cells:
                    for cell in cells[:2]:
                        text = (cell.text or "").strip()
                        if text and 2 <= len(text) <= 150 and text not in seen_keywords:
                            if not text.isdigit() and text.lower() not in ("search volume", "started", "trend breakdown", "past 24 hours", "past 4 hours", "past 48 hours", "past 7 days"):
                                keyword = text
                                break
                if keyword:
                    seen_keywords.add(keyword)
                    trends_data.append({
                        "keyword": keyword,
                        "article_urls": article_urls[:MAX_ARTICLES_PER_TREND],
                    })
            except Exception:
                continue

        # Fallback: any clickable trend-like text or list items
        if not trends_data:
            for selector in (
                "div[role='listitem']",
                "div[class*='trend']",
                "div[class*='Trend']",
                "a[href*='trends']",
            ):
                elms = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elms[:MAX_TRENDS_PER_COUNTRY * 2]:
                    if len(trends_data) >= MAX_TRENDS_PER_COUNTRY:
                        break
                    text = (el.text or "").strip()
                    if not text or len(text) < 2 or len(text) > 150 or text in seen_keywords:
                        continue
                    if text.isdigit() or text.lower() in ("news", "article", "stories", "search trends"):
                        continue
                    seen_keywords.add(text)
                    links = el.find_elements(By.TAG_NAME, "a") if el.tag_name != "a" else [el]
                    urls = []
                    for a in links:
                        h = a.get_attribute("href")
                        if h and h.startswith("http") and "google.com" not in h:
                            urls.append(h)
                    trends_data.append({"keyword": text, "article_urls": urls[:MAX_ARTICLES_PER_TREND]})
                if trends_data:
                    break
    except Exception as e:
        print(f"Error scraping {country['name']} ({geo}): {e}")
    return trends_data[:MAX_TRENDS_PER_COUNTRY]


def scrape_all_trends(headless: bool = True, countries: list[dict] | None = None) -> list[dict]:
    """
    Scrape real-time trends for given countries (default: all from config).
    Returns list of { "country": str, "geo": str, "trends": [ { "keyword", "article_urls" } ] }.
    """
    driver = create_driver(headless=headless)
    to_scrape = countries if countries is not None else TREND_COUNTRIES
    results = []
    try:
        for country in to_scrape:
            print(f"Scraping {country['name']} ({country['geo']})...")
            trends = scrape_country_trends(driver, country)
            results.append({
                "country": country["name"],
                "geo": country["geo"],
                "trends": trends,
            })
            time.sleep(1)  # Be nice to the server
    finally:
        driver.quit()
    return results
