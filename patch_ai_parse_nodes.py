import os
import requests
from dotenv import load_dotenv

load_dotenv('C:/projects/Bay-Blog/selenium-trends/.env')

base = os.environ['N8N_BASE_URL'].rstrip('/')
api_key = os.environ['N8N_API_KEY']
workflow_id = os.environ['N8N_WORKFLOW_ID']

headers = {
    'X-N8N-API-KEY': api_key,
    'Content-Type': 'application/json',
}

wf = requests.get(f'{base}/api/v1/workflows/{workflow_id}', headers=headers, timeout=30).json()

ai_json_body = '''={{ {
  "model": "llama-3.1-8b-instant",
  "messages": [
    {
      "role": "system",
      "content": "Return ONLY valid JSON with keys: title, blog_content, tags, meta_description. blog_content must be HTML using only h2, p, ul, li tags. No markdown. No explanation."
    },
    {
      "role": "user",
      "content": "Topic: " + ($json.keyword || "") + "\\n\\nContent:\\n" + (($json.summary_for_ai || "").slice(0, 1200))
    }
  ],
  "temperature": 0.1,
  "max_tokens": 500,
  "response_format": { "type": "json_object" }
} }}'''

parse_js = '''const source = $("Code Formatting").item?.json || {};
const keyword = source.keyword || "Untitled trend";
const raw = $json?.choices?.[0]?.message?.content || "";

if (!raw || typeof raw !== "string") {
  throw new Error("AI returned empty content");
}

let parsed;
try {
  parsed = JSON.parse(raw);
} catch {
  const match = raw.match(/\{[\s\S]*\}/);
  if (!match) {
    throw new Error("AI returned non-JSON content");
  }
  parsed = JSON.parse(match[0]);
}

const title = String(parsed.title || keyword).trim();
const blogContent = String(parsed.blog_content || parsed.content || "").trim();
const tags = Array.isArray(parsed.tags) ? parsed.tags.map((tag) => String(tag).trim()).filter(Boolean) : [keyword];
const metaDescription = String(parsed.meta_description || "").trim();

if (!blogContent) {
  throw new Error("AI returned empty blog_content");
}

return {
  json: {
    keyword,
    title,
    blog_content: blogContent,
    tags,
    meta_description: metaDescription || blogContent.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, 155),
  },
};'''

for node in wf.get('nodes', []):
    if node.get('name') == 'AI Rewrite (Mistral-7B)' and node.get('type') == 'n8n-nodes-base.httpRequest':
        node['continueOnFail'] = False
        node['onError'] = 'stopWorkflow'
        p = node.setdefault('parameters', {})
        p['jsonBody'] = ai_json_body
        p['options'] = {'batching': {'batch': {'batchSize': 1, 'batchInterval': 8000}}}

    if node.get('name') == 'Parse Mistral JSON' and node.get('type') == 'n8n-nodes-base.code':
        node.setdefault('parameters', {})['jsCode'] = parse_js
        node['continueOnFail'] = False
        node['onError'] = 'stopWorkflow'

payload = {
    'name': wf.get('name'),
    'nodes': wf.get('nodes', []),
    'connections': wf.get('connections', {}),
    'settings': {},
}

res = requests.put(f'{base}/api/v1/workflows/{workflow_id}', headers=headers, json=payload, timeout=30)
print('PUT', res.status_code)
print(res.text[:240])
res.raise_for_status()

act = requests.post(f'{base}/api/v1/workflows/{workflow_id}/activate', headers=headers, timeout=30)
print('ACT', act.status_code)
act.raise_for_status()
