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

# NEW Parser node name we want to use
parse_node_name = "Parse AI Output"

# 1. Ensure the parser node exists and has the correct name
parser_node = None
for node in nodes:
    if "parse" in node.get('name', '').lower() and (node.get('type') == 'n8n-nodes-base.code' or node.get('name') == parse_node_name):
        parser_node = node
        print(f"Found existing parser node: {node['name']}")
        node['name'] = parse_node_name # Rename it strictly to our target
        break

if not parser_node:
    print(f"Parser node not found. Adding {parse_node_name}...")
    parser_node = {
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
    nodes.append(parser_node)

# 2. GLOBAL REPLACEMENT of stale node references in ALL parameters
print("Performing global replacement of 'Parse Mistral JSON' references...")
nodes_json = json.dumps(nodes)
# Replace both quoted and potentially unquoted references in expressions
nodes_json = nodes_json.replace('Parse Mistral JSON', parse_node_name)
nodes = json.loads(nodes_json)

# 3. Re-verify connections with strictly correct names
print("Updating connections with unified node names...")
# We need to find the exact names used for other nodes to be safe
webhook_name = next((n['name'] for n in nodes if "webhook" in n.get('name', '').lower()), "Webhook receive JSON")
formatter_name = next((n['name'] for n in nodes if "formatting" in n.get('name', '').lower()), "Code Formatting")
ai_name = next((n['name'] for n in nodes if "rewrite" in n.get('name', '').lower()), "AI Rewrite (Mistral-7B)")
publish_name = next((n['name'] for n in nodes if "publish" in n.get('name', '').lower()), "Publish to Next.js Blog")

new_connections = {
    webhook_name: { "main": [[{ "node": formatter_name, "type": "main", "index": 0 }]] },
    formatter_name: { "main": [[{ "node": ai_name, "type": "main", "index": 0 }]] },
    ai_name: { "main": [[{ "node": parse_node_name, "type": "main", "index": 0 }]] },
    parse_node_name: { "main": [[{ "node": publish_name, "type": "main", "index": 0 }]] }
}
connections.update(new_connections)

# 4. Final Payload Assembly
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

print("✅ Success! Workflow node references repaired and active.")
