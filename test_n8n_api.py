"""Push the complete corrected BayBlog workflow and activate it."""
import json
import requests

N8N_BASE = "https://klain-n8n.hf.space"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYTM3MDE4OC0wZWU5LTRjN2YtOGQyMi1kYjE0ZGY1Mjg4ZjQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMmViMGJmNzYtY2FmZS00MzQzLWIyOTEtMWUwNjJlNjlhYzhjIiwiaWF0IjoxNzcyODExNTg0fQ.lH4Wwi2M23OjXKe4eju78so2GA2z4iJF-3LasSVXujU"
WF_ID = "S7LQxpXYjT5ziTmd"
HEADERS = {"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json"}
HF_TOKEN = "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"

CODE_FLATTEN = """const item = $input.first();
const data = item.json.body ?? item.json;
if (!data || !data.countries) return [{ json: { error: "Invalid payload" } }];
const MIN = 100;
const seen = new Set();
const results = [];
for (const c of data.countries) {
  for (const trend of c.trends || []) {
    const keyword = (trend.keyword || '').trim();
    if (!keyword || seen.has(keyword.toLowerCase())) continue;
    seen.add(keyword.toLowerCase());
    const arts = (trend.articles || []).filter(a => a.success === true && (a.content||'').trim().length >= MIN);
    const hasContent = arts.length > 0;
    results.push({ json: {
      keyword, country: c.country, geo: c.geo,
      has_content: hasContent,
      summary_for_ai: hasContent
        ? arts.map(a => (a.title ? a.title+'\\n' : '') + (a.content||'').slice(0,2500)).join('\\n\\n---\\n\\n')
        : '',
    }});
  }
}
return results.length ? results : [{ json: { error: 'No trends' } }];"""

CODE_PARSE = """const raw = $input.item.json;
const generated = Array.isArray(raw) ? raw[0]?.generated_text : (raw?.generated_text || '');
const match = (generated || '').match(/\\{[\\s\\S]*\\}/);
if (!match) return { json: { error: 'No JSON in AI output', preview: (generated||'').slice(0,200) } };
let parsed;
try { parsed = JSON.parse(match[0]); } catch(e) { return { json: { error: 'Parse error: '+e.message } }; }
const keyword = $('Code in JavaScript').item.json.keyword || '';
const slug = (parsed.title||keyword).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
return { json: {
  title: parsed.title || keyword,
  slug,
  blog_content: parsed.blog_content || parsed.content || '',
  tags: parsed.tags || [keyword],
  meta_description: parsed.meta_description || '',
}};"""

HF_BODY = '{"inputs":"[INST] You are a professional blog writer. Write an SEO-optimized blog article about this trending topic.\\n\\nTopic: {{ $json.keyword }} ({{ $json.country }})\\n\\nContext:\\n{{ $json.summary_for_ai }}\\n\\nRequirements:\\n- Minimum 6 paragraphs, HTML formatted using <h2> and <p> tags\\n- Add an introduction and conclusion\\n- Only use facts from the context\\n\\nReturn ONLY this exact JSON (no other text or explanation):\\n{\\"title\\":\\"...\\",'
HF_BODY += '  \\"blog_content\\":\\"<h2>...</h2><p>...</p>\\",\\"tags\\":[\\"tag1\\",\\"tag2\\"],\\"meta_description\\":\\"...\\"} [/INST]",'
HF_BODY += '"parameters":{"max_new_tokens":1500,"temperature":0.7,"return_full_text":false}}'

BLOG_BODY = '={"title":"{{ $json.title }}","slug":"{{ $json.slug }}","content":"{{ $json.blog_content.replace(/"/g, \'\\\\"\') }}","featured_image":null,"tags":{{ JSON.stringify($json.tags) }},"published":true}'

nodes = [
    {
        "parameters": {"httpMethod": "POST", "path": "5c7459c0-cb2f-4839-94ea-14ed1da0bce9", "responseMode": "onReceived", "options": {}},
        "type": "n8n-nodes-base.webhook", "typeVersion": 2.1, "position": [0, 0],
        "id": "79970630-eb6e-440e-b00f-188546548aa0", "name": "Webhook",
        "webhookId": "5c7459c0-cb2f-4839-94ea-14ed1da0bce9"
    },
    {
        "parameters": {"jsCode": CODE_FLATTEN},
        "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [220, 0],
        "id": "32388b63-fbb3-4c9f-969f-38366b801b8a", "name": "Code in JavaScript"
    },
    {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 3},
                "conditions": [{"id": "9777b6c6-c2c2-459d-8fee-ed2ecd627e02", "leftValue": "={{ $json.has_content }}", "rightValue": "", "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                "combinator": "and"
            },
            "options": {}
        },
        "type": "n8n-nodes-base.if", "typeVersion": 2.3, "position": [440, 0],
        "id": "9ce84a52-f439-46c7-b413-d421d15c220d", "name": "If"
    },
    {
        "parameters": {
            "method": "POST",
            "url": f"https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
            "sendHeaders": True,
            "headerParameters": {"parameters": [
                {"name": "Authorization", "value": f"Bearer {HF_TOKEN}"},
                {"name": "Content-Type", "value": "application/json"}
            ]},
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": f"={{{{ \"inputs\": \"[INST] You are a professional blog writer. Write an SEO-optimized blog article about this trending topic.\\\\n\\\\nTopic: {{{{ $json.keyword }}}} ({{{{ $json.country }}}})\\\\n\\\\nContext:\\\\n{{{{ $json.summary_for_ai }}}}\\\\n\\\\nRequirements:\\\\n- Minimum 6 paragraphs, HTML formatted using h2 and p tags\\\\n- Add an introduction and conclusion\\\\n- Only use facts from the context\\\\n\\\\nReturn ONLY valid JSON (no markdown, no explanation):\\\\n{{\\\\\"title\\\\\":\\\\\"...\\\\\",\\\\\"blog_content\\\\\":\\\\\"<h2>...</h2><p>...</p>\\\\\",\\\\\"tags\\\\\":[\\\\\"tag1\\\\\"],\\\\\"meta_description\\\\\":\\\\\"...\\\\\"}} [/INST]\", \"parameters\": {{\"max_new_tokens\": 1500, \"temperature\": 0.7, \"return_full_text\": false}} }}}}",
            "options": {}
        },
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.4, "position": [660, -120],
        "id": "244c922e-826f-4655-90a9-5ff8685c455c", "name": "AI Rewrite (Mistral-7B)"
    },
    {
        "parameters": {"jsCode": CODE_PARSE},
        "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [880, -120],
        "id": "parse-mistral-output-001", "name": "Parse AI Output"
    },
    {
        "parameters": {
            "method": "POST",
            "url": "https://bay-blog.vercel.app/api/blog/create",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={\"title\": \"{{ $json.title }}\", \"slug\": \"{{ $json.slug }}\", \"content\": \"{{ $json.blog_content }}\", \"featured_image\": null, \"tags\": {{ JSON.stringify($json.tags) }}, \"published\": true}",
            "options": {}
        },
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.4, "position": [1100, -120],
        "id": "publish-to-blog-001", "name": "Publish to Blog"
    }
]

connections = {
    "Webhook": {"main": [[{"node": "Code in JavaScript", "type": "main", "index": 0}]]},
    "Code in JavaScript": {"main": [[{"node": "If", "type": "main", "index": 0}]]},
    "If": {"main": [[{"node": "AI Rewrite (Mistral-7B)", "type": "main", "index": 0}]]},
    "AI Rewrite (Mistral-7B)": {"main": [[{"node": "Parse AI Output", "type": "main", "index": 0}]]},
    "Parse AI Output": {"main": [[{"node": "Publish to Blog", "type": "main", "index": 0}]]},
}

payload = {
    "name": "BayBlog",
    "nodes": nodes,
    "connections": connections,
    "settings": {},
    "staticData": None
}

print("=== Pushing updated workflow ===")
r = requests.put(f"{N8N_BASE}/api/v1/workflows/{WF_ID}", headers=HEADERS, json=payload, timeout=20)
print(f"Status: {r.status_code}")
if r.ok:
    wf = r.json()
    print(f"✅ Updated! Nodes: {len(wf.get('nodes', []))}")
    for n in wf.get("nodes", []):
        print(f"  - {n['name']}")

    print("\n=== Activating workflow ===")
    r2 = requests.post(f"{N8N_BASE}/api/v1/workflows/{WF_ID}/activate", headers=HEADERS, timeout=15)
    print(f"Activate status: {r2.status_code}")
    if r2.ok:
        print(f"✅ Active: {r2.json().get('active')}")
        print(f"\n🔗 Webhook URL (production):")
        print(f"   {N8N_BASE}/webhook/5c7459c0-cb2f-4839-94ea-14ed1da0bce9")
    else:
        print(f"Activate error: {r2.text[:400]}")
else:
    print(f"Error: {r.text[:600]}")
