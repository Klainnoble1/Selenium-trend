import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

base = os.environ['N8N_BASE_URL'].rstrip('/')
api_key = os.environ['N8N_API_KEY']
token = os.environ['N8N_ACCESS_TOKEN']
wid = os.environ['N8N_WORKFLOW_ID']

headers = {
    'X-N8N-API-KEY': api_key,
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
}

print(f"Fetching workflow {wid}...")
r = requests.get(f'{base}/api/v1/workflows/{wid}', headers=headers, timeout=30)
r.raise_for_status()
wf = r.json()

nodes = wf.get('nodes', [])
connections = wf.get('connections', {})

# 1. Update AI Rewrite node
for node in nodes:
    if "ai rewrite" in node.get('name', '').lower():
        print(f"Updating AI node: {node['name']}")
        # Use Groq schema from user's provided JSON
        node['parameters']['jsonBody'] = node['parameters'].get('jsonBody', '').replace('max_tokens\":220', 'max_tokens\":2048')
        # Also ensure it's pointing to Groq if the GET returned something else
        if "groq" not in node['parameters'].get('url', '').lower():
             node['parameters']['url'] = "https://api.groq.com/openai/v1/chat/completions"

# 2. Add Parse node if missing
parse_node_name = "Parse AI Output"
has_parse_node = any(n.get('name') == parse_node_name for n in nodes)

if not has_parse_node:
    print("Adding Parse AI Output node...")
    parse_node = {
      "parameters": {
        "jsCode": "try {\n  const aiOutputRaw = $input.item.json.choices[0].message.content;\n  const jsonMatch = aiOutputRaw.match(/\\{[\\s\\S]*\\}/);\n  if (jsonMatch) {\n    const parsed = JSON.parse(jsonMatch[0]);\n    return {\n      json: {\n        keyword: $node[\"Code Formatting\"].json.keyword,\n        ...parsed\n      }\n    };\n  }\n  return { json: { error: \"Failed to parse JSON\", raw: aiOutputRaw } };\n} catch (e) {\n  return { json: { error: e.message } };\n}"
      },
      "id": "parse-node-unique",
      "name": parse_node_name,
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [
        864,
        304
      ]
    }
    nodes.append(parse_node)

# 3. Fix connections
# Webhook (1) -> Formatter (2) -> AI (3) -> Parser (4) -> Publish (6)
# User IDs: Webhook=1, Formatter=2, AI=3, Parser=parse-node-unique, Publish=6

print("Updating connections...")
new_connections = {
    "Webhook receive JSON": { "main": [[{ "node": "Code Formatting", "type": "main", "index": 0 }]] },
    "Code Formatting": { "main": [[{ "node": "AI Rewrite (Mistral-7B)", "type": "main", "index": 0 }]] },
    "AI Rewrite (Mistral-7B)": { "main": [[{ "node": parse_node_name, "type": "main", "index": 0 }]] },
    parse_node_name: { "main": [[{ "node": "Publish to Next.js Blog", "type": "main", "index": 0 }]] }
}
connections.update(new_connections)

# 4. Update Publish node Input references
for node in nodes:
    if "publish" in node.get('name', '').lower():
        print(f"Updating Publish node: {node['name']}")
        params = node.get('parameters', {})
        if 'bodyParameters' in params:
             for p in params['bodyParameters'].get('parameters', []):
                 p['value'] = p.get('value', '').replace('$node["Parse Mistral JSON"]', f'$node["{parse_node_name}"]')
        elif 'jsonBody' in params:
             # If it's a JSON body, replace references
             params['jsonBody'] = params.get('jsonBody', '').replace('$node["Parse Mistral JSON"]', f'$node["{parse_node_name}"]')
             # Also ensure the publish node uses the parser's json directly if it was simple
             params['jsonBody'] = params.get('jsonBody', '').replace('{{ $json.', f'{{ $node["{parse_node_name}"].json.')

# 5. PUT back
payload = {
    'name': wf.get('name'),
    'nodes': nodes,
    'connections': connections,
    'settings': wf.get('settings', {}),
}

print("Pushing updated workflow...")
res = requests.put(f'{base}/api/v1/workflows/{wid}', headers=headers, json=payload, timeout=30)
if not res.ok:
    print(f"Error: {res.status_code}")
    print(res.text)
    res.raise_for_status()

print("Activating workflow...")
requests.post(f'{base}/api/v1/workflows/{wid}/activate', headers=headers, timeout=30).raise_for_status()

print("✅ Success! Workflow repaired and active.")
