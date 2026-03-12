import os
import requests
from dotenv import load_dotenv

load_dotenv('selenium-trends/.env')

base = os.environ['N8N_BASE_URL'].rstrip('/')
api_key = os.environ['N8N_API_KEY']
workflow_id = os.environ['N8N_WORKFLOW_ID']

headers = {
    'X-N8N-API-KEY': api_key,
    'Content-Type': 'application/json',
}

wf = requests.get(f'{base}/api/v1/workflows/{workflow_id}', headers=headers, timeout=30).json()

model = 'Qwen/Qwen2.5-7B-Instruct'
json_body_expr = (
    '={{ {"model":"' + model + '","messages":['
    '{"role":"system","content":"You rewrite news summaries into SEO blog posts and return strict JSON with keys: title, blog_content, tags, meta_description."},'
    '{"role":"user","content":"Topic: " + ($json.keyword || "") + "\\n\\nContent:\\n" + ($json.summary_for_ai || "") }'
    '],"temperature":0.7,"max_tokens":1400} }}'
)

for node in wf.get('nodes', []):
    if node.get('name') == 'AI Rewrite (Mistral-7B)' and node.get('type') == 'n8n-nodes-base.httpRequest':
        p = node.setdefault('parameters', {})
        p['url'] = 'https://router.huggingface.co/v1/chat/completions'
        p['jsonBody'] = json_body_expr

payload = {
    'name': wf.get('name'),
    'nodes': wf.get('nodes', []),
    'connections': wf.get('connections', {}),
    'settings': {},
}

res = requests.put(f'{base}/api/v1/workflows/{workflow_id}', headers=headers, json=payload, timeout=30)
print('PUT', res.status_code)
print(res.text[:260])
res.raise_for_status()

act = requests.post(f'{base}/api/v1/workflows/{workflow_id}/activate', headers=headers, timeout=30)
print('ACT', act.status_code)
print(act.text[:160])
act.raise_for_status()

print('AI model patched to chat-compatible model')
