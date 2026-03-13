---
title: Selenium-trends
sdk: docker
emoji: "📈"
colorFrom: blue
colorTo: green
---

# Google Trends Scraper -> n8n

Production path:
- Google Trends only

Experimental code kept in repo:
- X trends
- NewsAPI trends

The production scraper collects Google Trends for:
- United States
- United Kingdom
- Canada
- Germany
- Switzerland

Then it:
- finds article URLs
- extracts article content
- sends one JSON payload to n8n

## Production Run

```bash
python run_scraper.py
```

Equivalent:

```bash
python run_google_trends.py
```

## Experimental Runners

These are kept for later and are not part of the recommended production path:

```bash
python run_x_trends.py
python run_newsapi_trends.py
```

## Hugging Face

For production use on Hugging Face, treat Google as the supported path.

Recommended Space env:

```env
APP_MODE=web
HEADLESS=true
COUNTRY_DELAY_SECONDS=600
SCRAPER_SCRIPT=run_scraper.py
N8N_WEBHOOK_URL=https://your-n8n-domain.com/webhook/trend-blog-google
N8N_WEBHOOK_METHOD=POST
N8N_WEBHOOK_AUTH_HEADER=Authorization
N8N_ACCESS_TOKEN=
```

The UI includes buttons for Google, X, and NewsAPI because the code is still present. For production, use:
- `Run Google Trends`

## Worker Mode

Worker mode can run a specific script:

```env
APP_MODE=worker
RUN_ONCE=false
SCRAPE_INTERVAL_MINUTES=360
SCRAPER_SCRIPT=run_scraper.py
```

## Render Deployment

Recommended Render service type:
- Background Worker

Recommended root directory:
- `selenium-trends`

Recommended production env for Google-only mode:

```env
APP_MODE=worker
RUN_ONCE=false
SCRAPE_INTERVAL_MINUTES=360
SCRAPER_SCRIPT=run_scraper.py
HEADLESS=true
COUNTRY_DELAY_SECONDS=600
N8N_WEBHOOK_URL=https://your-n8n-domain.com/webhook/trend-blog-google
N8N_WEBHOOK_METHOD=POST
N8N_WEBHOOK_AUTH_HEADER=Authorization
N8N_ACCESS_TOKEN=
COUNTRIES=
OPENCLAW_WEBHOOK_URL=
```

Safer first deploy values:

```env
COUNTRIES=US,GB
COUNTRY_DELAY_SECONDS=180
```

Notes:
- Use Google-only mode in production.
- Keep `SCRAPER_SCRIPT=run_scraper.py`.
- Do not deploy this as a Render web service unless you specifically want the Gradio UI.

## n8n Payload Shape

```json
{
  "source": "google-trends-selenium",
  "timeframe": "4h",
  "countries": [
    {
      "country": "United States",
      "geo": "US",
      "trends": [
        {
          "keyword": "Trending search term",
          "article_urls": ["https://..."],
          "articles": [
            {
              "url": "https://...",
              "title": "Article title",
              "content": "Full extracted text...",
              "success": true
            }
          ]
        }
      ]
    }
  ]
}
```

## Recommended n8n Workflows

Recommended production workflow:
- one Google-only workflow

Suggested webhook:
- `/webhook/trend-blog-google`

If you decide to revisit the experimental sources later, create separate workflows:
- `/webhook/trend-blog-x`
- `/webhook/trend-blog-newsapi`

Do not merge those sources into the Google production workflow.

## Environment Variables

Required for production:
- `N8N_WEBHOOK_URL`
- `HEADLESS`

Optional:
- `COUNTRIES`
- `COUNTRY_DELAY_SECONDS`
- `OPENCLAW_WEBHOOK_URL`
- `SCRAPER_SCRIPT`

Experimental only:
- `X_API_KEY`
- `X_API_KEY_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`
- `X_BEARER_TOKEN`
- `NEWSAPI_KEY`

## Project Layout

- `run_scraper.py` - production Google runner
- `run_google_trends.py` - Google alias runner
- `run_x_trends.py` - experimental X runner
- `run_newsapi_trends.py` - experimental NewsAPI runner
- `source_pipeline.py` - shared enrich/save/send helpers
- `trends_scraper.py` - Selenium Google Trends scraper
- `google_search.py` - article URL search
- `article_extractor.py` - article content extraction
- `n8n_sender.py` - webhook sender
- `app.py` - Hugging Face UI
- `worker.py` - long-running worker entrypoint
