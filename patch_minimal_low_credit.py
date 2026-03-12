import os
import requests
from dotenv import load_dotenv

load_dotenv('selenium-trends/.env')

base = os.environ['N8N_BASE_URL'].rstrip('/')
api_key = os.environ['N8N_API_KEY']
workflow_id = os.environ['N8N_WORKFLOW_ID']

headers = {'X-N8N-API-KEY': api_key, 'Content-Type': 'application/json'}

wf = requests.get(f'{base}/api/v1/workflows/{workflow_id}', headers=headers, timeout=30).json()

for n in wf.get('nodes', []):
    if n.get('name') == 'AI Rewrite (Mistral-7B)' and n.get('type') == 'n8n-nodes-base.httpRequest':
        n['continueOnFail'] = True
        n['onError'] = 'continueRegularOutput'

        p = n.setdefault('parameters', {})
        jb = p.get('jsonBody', '')
        jb = jb.replace('"max_tokens":1400', '"max_tokens":350')
        jb = jb.replace('"max_tokens":700', '"max_tokens":350')
        jb = jb.replace('"temperature":0.7', '"temperature":0.4')
        jb = jb.replace('"temperature":0.5', '"temperature":0.4')
        p['jsonBody'] = jb

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

print('patched minimal low-credit mode')
