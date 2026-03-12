"""
Test: Send the cached trends_output.json payload to the n8n webhook.
This simulates exactly what run_scraper.py does, without re-running the full browser scrape.
"""
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

with open('trends_output.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

# Trim to just 1 country x 2 trends x 1 article each for a fast test
test_payload = {
    "source": payload["source"],
    "timeframe": payload["timeframe"],
    "countries": []
}

for c in payload["countries"][:1]:  # Only US
    trends_with_content = []
    for t in c["trends"]:
        arts = [a for a in t.get("articles", [])
                if a.get("success") and len((a.get("content") or "").strip()) >= 100]
        if arts:
            trends_with_content.append({
                "keyword": t["keyword"],
                "article_urls": [a["url"] for a in arts[:1]],
                "articles": arts[:1],  # 1 article per trend
            })
        if len(trends_with_content) >= 2:  # Only 2 trends for test
            break

    test_payload["countries"].append({
        "country": c["country"],
        "geo": c["geo"],
        "trends": trends_with_content
    })

webhook_url = os.environ.get("N8N_WEBHOOK_URL", "").strip()
print(f"Webhook URL: {webhook_url}")
print(f"Sending {len(test_payload['countries'][0]['trends'])} trends for {test_payload['countries'][0]['country']}")
for t in test_payload["countries"][0]["trends"]:
    print(f"  - \"{t['keyword']}\" ({len(t['articles'])} article, {len(t['articles'][0]['content'])} chars)")

print("\nSending to n8n...")
try:
    resp = requests.post(
        webhook_url,
        json=test_payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
