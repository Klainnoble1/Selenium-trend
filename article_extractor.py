"""
Extract main article content from URLs using trafilatura.
"""

import requests
from trafilatura import extract
from config import ARTICLE_REQUEST_TIMEOUT, USER_AGENT


def extract_article_content(url: str) -> dict:
    """
    Fetch URL and extract main text content.
    Returns dict with url, title, text, and success flag.
    """
    result = {"url": url, "title": "", "content": "", "success": False}
    try:
        resp = requests.get(
            url,
            timeout=ARTICLE_REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        resp.raise_for_status()
        html = resp.text
        text = extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
        if text:
            result["content"] = text.strip()
            result["success"] = True
        from trafilatura import extract_metadata
        meta = extract_metadata(html)
        if meta and meta.title:
            result["title"] = meta.title
    except Exception as e:
        result["error"] = str(e)
    return result
