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

code_js = '''try {
  const aiOutputRaw = $input.item.json.choices[0].message.content;
  const jsonMatch = aiOutputRaw.match(/\{[\s\S]*\}/);

  if (!jsonMatch) {
    return { json: { error: "Failed to parse JSON", raw: aiOutputRaw } };
  }

  const parsed = JSON.parse(jsonMatch[0]);
  const title = parsed.title || "Untitled Post";
  const blogContent = parsed.blog_content || parsed.content || "";

  return {
    json: {
      title,
      slug: title
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, ''),
      blog_content: blogContent,
      content: blogContent,
      tags: Array.isArray(parsed.tags) ? parsed.tags : [],
      meta_description: parsed.meta_description || "",
      published: true
    }
  };
} catch (e) {
  return { json: { error: e.message } };
}'''

for node in wf.get('nodes', []):
    if node.get('name') == 'Code in JavaScript' and node.get('type') == 'n8n-nodes-base.code':
        node.setdefault('parameters', {})['jsCode'] = code_js

payload = {
    'name': wf.get('name'),
    'nodes': wf.get('nodes', []),
    'connections': wf.get('connections', {}),
    'settings': {},
}

res = requests.put(f'{base}/api/v1/workflows/{workflow_id}', headers=headers, json=payload, timeout=30)
print('PUT', res.status_code)
print(res.text[:220])
res.raise_for_status()

act = requests.post(f'{base}/api/v1/workflows/{workflow_id}/activate', headers=headers, timeout=30)
print('ACT', act.status_code)
act.raise_for_status()
