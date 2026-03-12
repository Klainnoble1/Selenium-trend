import os
import requests
from dotenv import load_dotenv

load_dotenv('selenium-trends/.env')

GROQ_API_KEY = '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'
GROQ_MODEL = 'llama-3.1-8b-instant'

base = os.environ['N8N_BASE_URL'].rstrip('/')
api_key = os.environ['N8N_API_KEY']
workflow_id = os.environ['N8N_WORKFLOW_ID']

headers = {
    'X-N8N-API-KEY': api_key,
    'Content-Type': 'application/json',
}

wf = requests.get(f'{base}/api/v1/workflows/{workflow_id}', headers=headers, timeout=30).json()

groq_json_body = (
    '={{ {"model":"' + GROQ_MODEL + '","messages":['
    '{"role":"system","content":"You rewrite news summaries into SEO blog posts and return strict JSON with keys: title, blog_content, tags, meta_description. Keep responses concise."},'
    '{"role":"user","content":"Topic: " + ($json.keyword || "") + "\\n\\nContent:\\n" + (($json.summary_for_ai || "").slice(0, 1800)) }'
    '],"temperature":0.2,"max_tokens":220} }}'
)

for node in wf.get('nodes', []):
    if node.get('name') == 'Code Formatting' and node.get('type') == 'n8n-nodes-base.code':
        p = node.setdefault('parameters', {})
        js = p.get('jsCode', '')
        js = js.replace('.slice(0, 3000)', '.slice(0, 700)')
        js = js.replace('.slice(0,3000)', '.slice(0,700)')
        js = js.replace(
            'return out.length ? out : [{ json: { error: "No trends with sufficient content" } }];',
            'return out.length ? out.slice(0, 10) : [{ json: { error: "No trends with sufficient content" } }];'
        )
        p['jsCode'] = js

    if node.get('name') == 'AI Rewrite (Mistral-7B)' and node.get('type') == 'n8n-nodes-base.httpRequest':
        p = node.setdefault('parameters', {})
        p['method'] = 'POST'
        p['url'] = 'https://api.groq.com/openai/v1/chat/completions'
        p['sendHeaders'] = True
        p['headerParameters'] = {
            'parameters': [
                {'name': 'Authorization', 'value': f'Bearer {GROQ_API_KEY}'},
                {'name': 'Content-Type', 'value': 'application/json'},
            ]
        }
        p['sendBody'] = True
        p['specifyBody'] = 'json'
        p['jsonBody'] = groq_json_body
        p.pop('bodyParameters', None)
        node['continueOnFail'] = True
        node['onError'] = 'continueRegularOutput'

    if node.get('name') == 'Image Generator (SDXL)' and node.get('type') == 'n8n-nodes-base.httpRequest':
        node['continueOnFail'] = True
        node['onError'] = 'continueRegularOutput'

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

print('patched workflow to Groq low-TPM mode')
