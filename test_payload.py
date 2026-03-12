import json

with open('trends_output.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

countries = payload.get('countries', [])
print(f"Source: {payload.get('source')} | Timeframe: {payload.get('timeframe')}")
print(f"Countries scraped: {len(countries)}\n")

total_trends = 0
total_articles = 0
for c in countries:
    trends = c.get('trends', [])
    total_trends += len(trends)
    arts_with_content = 0
    for t in trends:
        arts = [a for a in t.get('articles', []) if a.get('success') and len((a.get('content') or '').strip()) >= 100]
        arts_with_content += len(arts)
    total_articles += arts_with_content
    print(f"  [{c['geo']}] {c['country']}: {len(trends)} trends, {arts_with_content} articles with content")

print(f"\nTOTAL trends: {total_trends}")
print(f"TOTAL articles with content (>=100 chars): {total_articles}")

# Show first usable trend as a sample
print("\n--- SAMPLE TREND ---")
for c in countries:
    for t in c.get('trends', []):
        arts = [a for a in t.get('articles', []) if a.get('success') and len((a.get('content') or '').strip()) >= 100]
        if arts:
            print(f"Keyword: {t['keyword']}")
            print(f"Country: {c['country']} ({c['geo']})")
            print(f"Articles with content: {len(arts)}")
            a = arts[0]
            print(f"  Title: {a.get('title', '')[:80]}")
            print(f"  Content length: {len(a.get('content', ''))} chars")
            print(f"  Content preview:\n    {a.get('content', '')[:300]}")
            break
    else:
        continue
    break
