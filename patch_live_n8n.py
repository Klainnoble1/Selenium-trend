import os
import requests
from dotenv import load_dotenv

load_dotenv('selenium-trends/.env')

base = os.environ['N8N_BASE_URL'].rstrip('/')
api_key = os.environ['N8N_API_KEY']
wid = os.environ['N8N_WORKFLOW_ID']
hf_token = os.environ['HF_TOKEN']

headers = {
    'X-N8N-API-KEY': api_key,
    'Content-Type': 'application/json',
}

r = requests.get(f'{base}/api/v1/workflows/{wid}', headers=headers, timeout=30)
r.raise_for_status()
wf = r.json()

for n in wf.get('nodes', []):
    if n.get('name') == 'AI Rewrite (Mistral-7B)' and n.get('type') == 'n8n-nodes-base.httpRequest':
        p = n.setdefault('parameters', {})
        p['method'] = 'POST'
        p['url'] = 'https://router.huggingface.co/v1/chat/completions'
        p['sendHeaders'] = True
        p['headerParameters'] = {
            'parameters': [
                {'name': 'Authorization', 'value': f'Bearer {hf_token}'},
                {'name': 'Content-Type', 'value': 'application/json'},
            ]
        }
        p['sendBody'] = True
        p['specifyBody'] = 'json'
        p['jsonBody'] = '={"model":"mistralai/Mistral-7B-Instruct-v0.3","messages":[{"role":"system","content":"You rewrite news summaries into SEO blog posts and return strict JSON with keys: title, blog_content, tags, meta_description."},{"role":"user","content":"Topic: {{$json.keyword}}\\n\\nContent:\\n{{$json.summary_for_ai}}"}],"temperature":0.7,"max_tokens":1400}'
        p.pop('bodyParameters', None)

    if n.get('name') == 'Parse Mistral JSON' and n.get('type') == 'n8n-nodes-base.code':
        n.setdefault('parameters', {})['jsCode'] = (
            'try {\n'
            '  const aiOutputRaw = $json?.choices?.[0]?.message?.content || "";\n'
            '  const jsonMatch = aiOutputRaw.match(/\\{[\\s\\S]*\\}/);\n'
            '  if (!jsonMatch) return { json: { error: "Failed to parse JSON" } };\n'
            '  const parsed = JSON.parse(jsonMatch[0]);\n'
            '  return { json: { keyword: $("Code Formatting").item.json.keyword, ...parsed } };\n'
            '} catch (e) {\n'
            '  return { json: { error: e.message } };\n'
            '}'
        )

payload = {
    'name': wf.get('name'),
    'nodes': wf.get('nodes', []),
    'connections': wf.get('connections', {}),
    'settings': {},
}

u = requests.put(f'{base}/api/v1/workflows/{wid}', headers=headers, json=payload, timeout=30)
print('PUT', u.status_code)
print(u.text[:400])
u.raise_for_status()

a = requests.post(f'{base}/api/v1/workflows/{wid}/activate', headers=headers, timeout=30)
print('ACT', a.status_code)
print(a.text[:200])
a.raise_for_status()

print('patched workflow')
