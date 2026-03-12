# Bay Blog

Simple reflective blog built with Next.js.  
Posts are published through `POST /api/blog/create` and rendered on the home page.

## Local files

- `selenium-trends.json` (root): trend tags shown on the homepage.
- `blog-posts.json` (root): persisted posts for local/dev usage.

## Run

```bash
npm install
copy .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

When `DATABASE_URL` is set, posts from n8n are stored in Supabase Postgres (`blog_posts` table).
If `DATABASE_URL` is not set, the app falls back to `blog-posts.json`.

## Publish API (for n8n)

- Method: `POST`
- URL: `https://bay-blog.vercel.app/api/blog/create`
- Auth header:
  - `Authorization: Bearer 786273jiahgsdiuhjsda8721y378213nbsadjhgsdajhgsajdg982738972931`
- Required header:
  - `Content-Type: application/json`
- Recommended header:
  - `Accept: application/json`

Example body:

```json
{
  "title": "Quiet Notes from Selenium Pipelines",
  "slug": "quiet-notes-from-selenium-pipelines",
  "content": "Today I slowed down and fixed one flaky test at the source...",
  "tags": ["selenium", "testing", "reflection"],
  "published": true
}
```

### n8n fix for your 400 error

Your error says:

`Accept type "...text/html...image/*..." not supported`

Set the HTTP Request node headers explicitly:

- `Accept: application/json`
- `Content-Type: application/json`

And keep response format as JSON.

## Note about Vercel persistence

`blog-posts.json` works locally, but file writes are not durable across Vercel serverless executions.  
For production persistence, move post storage to a database (Supabase/Postgres/Prisma).
