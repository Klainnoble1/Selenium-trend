"""
Send scraped trends and article content to n8n webhook.
Uses POST by default (payload in JSON body) to avoid 414 URI Too Large.
Set N8N_WEBHOOK_METHOD=GET only for small payloads (no article content).
"""

import json
import os

import requests


def send_to_n8n(payload: dict, webhook_url: str | None = None) -> dict:
    """
    Send payload to n8n webhook. Uses POST by default (body) so large payloads work.
    Set N8N_WEBHOOK_METHOD=GET in .env only if your webhook is GET-only and payload is small.
    """
    url = webhook_url or os.environ.get("N8N_WEBHOOK_URL")
    if not url:
        return {"success": False, "error": "N8N_WEBHOOK_URL not set"}
    method = (os.environ.get("N8N_WEBHOOK_METHOD") or "POST").strip().upper()

    try:
        if method == "GET":
            # GET: only for small payloads (query string size limit ~2k–8k)
            body = json.dumps(payload)
            if len(body) > 1500:
                # Payload too large for GET; use POST instead
                method = "POST"
        if method == "POST":
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
        else:
            import base64
            import urllib.parse
            encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
            full_url = f"{url}?payload={urllib.parse.quote(encoded)}"
            resp = requests.get(full_url, timeout=30)
        return {
            "success": resp.ok,
            "status_code": resp.status_code,
            "response": resp.text[:500] if resp.text else "",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
