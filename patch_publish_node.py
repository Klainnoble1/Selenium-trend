import os
import requests
from dotenv import load_dotenv

load_dotenv('selenium-trends/.env')

base = os.environ['N8N_BASE_URL'].rstrip('/')
api_key = os.environ['N8N_API_KEY']
workflow_id = os.environ['N8N_WORKFLOW_ID']
blog_secret = os.environ.get('BLOG_API_SECRET') or os.environ.get('CRON_SECRET')
blog_url = 'https://my-blog-ten-gamma-87.vercel.app/api/blog/create'

headers = {
    'X-N8N-API-KEY': api_key,
    'Content-Type': 'application/json',
}

wf = requests.get(f'{base}/api/v1/workflows/{workflow_id}', headers=headers, timeout=30).json()

publish_json_body = '={{ {"title": $json.title || $json.keyword || "Untitled", "slug": (($json.title || $json.keyword || "untitled").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")), "content": ($json.blog_content || "<p>No content generated.</p>"), "featured_image": null, "tags": (Array.isArray($json.tags) ? $json.tags : [$json.keyword || "news"]), "published": true } }}'

for node in wf.get('nodes', []):
    if node.get('name') == 'Publish to Next.js Blog' and node.get('type') == 'n8n-nodes-base.httpRequest':
        p = node.setdefault('parameters', {})
        p['method'] = 'POST'
        p['url'] = blog_url
        p['sendHeaders'] = True
        p['headerParameters'] = {
            'parameters': [
                {'name': 'Authorization', 'value': f'Bearer {blog_secret}'},
                {'name': 'Content-Type', 'value': 'application/json'},
            ]
        }
        p['sendBody'] = True
        p['specifyBody'] = 'json'
        p['jsonBody'] = publish_json_body
        p.pop('bodyParameters', None)

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
