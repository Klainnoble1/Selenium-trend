# Google Trends Scraper (Selenium) → n8n

Scrapes **Google Trends real-time (4h)** for **US, UK, Canada, Germany, and Switzerland**, fetches full content from top articles for each trend, and sends a single JSON payload to an **n8n webhook** so you can use trends and article content in your workflows.

---

## Push to GitHub

1. **Initialize git** (if not already a repo):
   ```bash
   cd selenium-trends
   git init
   ```

2. **Add the remote** and push:
   ```bash
   git remote add origin https://github.com/Klainnoble1/Selenium-trend.git
   git add .
   git commit -m "Initial commit: trends scraper + Docker + Gradio for HF"
   git branch -M main
   git push -u origin main
   ```
   Use a [personal access token](https://github.com/settings/tokens) if prompted for password.

---

## Host on Hugging Face

1. **Create a Space**
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **Create new Space**.
   - Name it (e.g. `Selenium-trend`), choose **Docker** as SDK, set visibility (Public/Private).

2. **Connect your GitHub repo**
   - In the Space creation form, choose **Link to a Git repository** and enter:
     - Repository: `Klainnoble1/Selenium-trend` (or your fork).
   - Or: after creating the Space, in **Settings → Repository**, connect the GitHub repo so HF builds from it.

3. **Add secrets**
   - Open your Space → **Settings** → **Repository secrets**.
   - Add:
     - `N8N_WEBHOOK_URL` = your n8n webhook URL (e.g. `https://your-n8n.com/webhook/xxxx`).
   - Optional: `N8N_WEBHOOK_METHOD` = `POST` (default).

4. **Build**
   - HF builds from the **Dockerfile** in the repo (installs Chromium, Python deps, runs the Gradio app).
   - After build, the Space shows a **Run trends scraper** button; click it to run the scraper. Logs appear in the UI; results are sent to n8n if `N8N_WEBHOOK_URL` is set.

5. **Notes**
   - The Space runs the scraper **on demand** when you click the button (no cron on HF free tier).
   - For scheduled runs, use an external cron (e.g. GitHub Actions, or your n8n cron) that calls your Space or a separate deployment.

---

## Requirements

- **Python 3.10+**
- **Chrome** (for Selenium/ChromeDriver; webdriver-manager installs the driver automatically)

## Setup

```bash
cd selenium-trends
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your n8n webhook URL:

```env
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/xxxx
HEADLESS=true
```

## Run

```bash
python run_scraper.py
```

- Trends are scraped per country from:  
  `https://trends.google.com/trends/trendingsearches/realtime?geo=XX&hl=...`
- For each trend, the script finds related article links on the page and fetches **full text content** (via `trafilatura`).
- Output is written to `trends_output.json` and, if `N8N_WEBHOOK_URL` is set, **POSTed to n8n**.

## n8n payload shape

n8n receives one JSON body per run, e.g.:

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

Use this in n8n to drive workflows (e.g. filter by country, loop over trends, use `articles[].content` for summarization or posting).

## Optional env vars

| Variable | Description |
|----------|-------------|
| `N8N_WEBHOOK_URL` | n8n webhook URL (required to send to n8n). |
| `HEADLESS` | `true` (default) or `false` to show the browser. |
| `COUNTRIES` | Comma-separated geo codes, e.g. `US,GB`. Omit to use all five (US, GB, CA, DE, CH). |

## Troubleshooting

- **No trends / empty list**: Google’s real-time page may have changed structure. You may need to adjust selectors in `trends_scraper.py` (e.g. `div[class*='trend']`, `div[role='listitem']`, or table rows).
- **4h window**: The script tries to click a “Past 4 hours” style control if present; otherwise it uses whatever timeframe the page defaults to (often real-time / 4h).
- **Article content empty**: Some sites block scrapers or use heavy JavaScript; those URLs may have `"success": false` and empty `content`.

## Project layout

- `config.py` – Countries (geo/hl), URLs, limits.
- `trends_scraper.py` – Selenium: load real-time trends page per country, extract trend keywords and article URLs.
- `google_search.py` – DuckDuckGo search for article URLs per trend.
- `article_extractor.py` – Fetch article URL and extract main text with `trafilatura`.
- `n8n_sender.py` – POST aggregated payload to n8n webhook.
- `run_scraper.py` – Orchestrates scrape → extract → save → send.
- `app.py` – Gradio UI for Hugging Face Space (run scraper on demand).
- `Dockerfile` – Docker image with Chromium for HF Spaces.
