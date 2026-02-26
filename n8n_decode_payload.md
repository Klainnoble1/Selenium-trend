# n8n Webhook (POST) – Code node

The scraper sends a **POST** request with the payload as **JSON in the body**.  
The Webhook node puts the body in the item, so the payload is already in `$input.item.json` (or `$json`).

---

## Option 1: Pass-through (one item, full payload)

Use this when the next nodes work with the full payload (e.g. loop over `countries` in a later node).

**Code node – Run Once for All Items:**

```javascript
const item = $input.first();
// POST body: n8n may put it in .body or directly on .json
const data = item.json.body ?? item.json;

if (!data || !data.countries) {
  return [{ json: { error: "Invalid payload: missing body or countries" } }];
}

return [{ json: data }];
```

Then use:
- `$json.source` → `"google-trends-selenium"`
- `$json.timeframe` → `"4h"`
- `$json.countries` → array of `{ country, geo, trends }`
- Each trend: `keyword`, `article_urls`, `articles` (each article: `url`, `title`, `content`, `success`)

---

## Option 2: One item per trend (recommended for a blog)

Use this when you want one execution per trend (e.g. one n8n item = one blog post).  
Adds **blog-ready fields**: only articles with usable content, and a flag so you can skip trends with no content.

**Code node – Run Once for All Items:**

```javascript
const item = $input.first();
const data = item.json.body ?? item.json;

if (!data || !data.countries) {
  return [{ json: { error: "Invalid payload: missing body or countries" } }];
}

const MIN_CONTENT_LENGTH = 100; // minimum chars to consider article usable

const results = [];
for (const c of data.countries) {
  for (const trend of c.trends || []) {
    const articles = trend.articles || [];
    const articlesWithContent = articles.filter(
      (a) => a.success === true && (a.content || "").trim().length >= MIN_CONTENT_LENGTH
    );
    const hasContent = articlesWithContent.length > 0;

    results.push({
      json: {
        source: data.source,
        timeframe: data.timeframe,
        country: c.country,
        geo: c.geo,
        keyword: trend.keyword,
        article_urls: trend.article_urls || [],
        articles: trend.articles || [],
        articles_with_content: articlesWithContent,
        has_content: hasContent,
        summary_for_ai: hasContent
          ? articlesWithContent.map((a) => (a.title ? `${a.title}\n` : "") + (a.content || "").slice(0, 3000)).join("\n\n---\n\n")
          : "",
      },
    });
  }
}

return results.length ? results : [{ json: { error: "No trends" } }];
```

**Fields per item:**

| Field | Use |
|-------|-----|
| `keyword` | Trend topic (e.g. "nvidia", "china") |
| `country`, `geo` | Location context |
| `articles` | All 2 articles (some may have empty content) |
| `articles_with_content` | Only articles where `success === true` and content length ≥ 100 chars |
| `has_content` | `true` if at least one article has usable content – **filter on this** before generating a post |
| `summary_for_ai` | Concatenation of title + first 3000 chars of each article with content – ready to send to an LLM for a blog post |

**In the next node:** Use an **IF** or **Filter** so you only run “Generate post” when `$json.has_content === true`. Use `$json.summary_for_ai` as the context for your LLM (e.g. “Write a short blog post about the trend: [keyword], using this context: [summary_for_ai]”).

---

## Option 3: One item per article (for per-article logic)

Use this when you want to process each article (e.g. summarise or send each one).

**Code node – Run Once for All Items:**

```javascript
const item = $input.first();
const data = item.json.body ?? item.json;

if (!data || !data.countries) {
  return [{ json: { error: "Invalid payload" } }];
}

const results = [];
for (const c of data.countries) {
  for (const trend of c.trends || []) {
    for (const art of trend.articles || []) {
      if (!art.url) continue;
      results.push({
        json: {
          source: data.source,
          timeframe: data.timeframe,
          country: c.country,
          geo: c.geo,
          keyword: trend.keyword,
          article_url: art.url,
          article_title: art.title || "",
          article_content: art.content || "",
          article_success: art.success === true,
        },
      });
    }
  }
}

return results.length ? results : [{ json: { error: "No articles" } }];
```

---

**Note:** If your Webhook node puts the raw body in a different field (e.g. `item.binary.data` or `item.json.rawBody`), use that instead of `item.json.body` and parse `JSON.parse(...)` if needed.
