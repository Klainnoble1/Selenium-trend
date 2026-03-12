#!/usr/bin/env python3
"""Create or update the n8n BayBlog workflow and activate it."""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
WORKFLOW_TEMPLATE = ROOT / "n8n-trend-blog-workflow.json"


def get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = (os.environ.get(name) or default or "").strip()
    if required and not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def replace_hf_token(node: dict, hf_token: str) -> None:
    params = node.get("parameters", {})

    header_params = params.get("headerParameters", {}).get("parameters", [])
    for header in header_params:
        if header.get("name", "").lower() == "authorization":
            header["value"] = f"Bearer {hf_token}"


def patch_publish_node(node: dict, blog_api_url: str, blog_api_secret: str) -> None:
    params = node.setdefault("parameters", {})
    params["url"] = blog_api_url
    params["sendHeaders"] = True
    params["headerParameters"] = {
        "parameters": [
            {
                "name": "Authorization",
                "value": f"Bearer {blog_api_secret}",
            }
        ]
    }


def patch_workflow(workflow: dict) -> dict:
    hf_token = get_env("HF_TOKEN", required=True)
    blog_api_url = get_env(
        "BLOG_API_URL", "https://bay-blog.vercel.app/api/blog/create", required=True
    )
    blog_api_secret = get_env("BLOG_API_SECRET", required=True)

    for node in workflow.get("nodes", []):
        node_name = (node.get("name") or "").lower()

        if "ai rewrite" in node_name or "image generator" in node_name:
            replace_hf_token(node, hf_token)

        if "publish to next.js blog" in node_name or "publish to blog" in node_name:
            patch_publish_node(node, blog_api_url, blog_api_secret)

    return workflow


def n8n_request(method: str, url: str, api_key: str, payload: dict | None = None, access_token: str | None = None) -> requests.Response:
    headers = {
        "Content-Type": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    else:
        headers["X-N8N-API-KEY"] = api_key
    return requests.request(method, url, headers=headers, json=payload, timeout=60)


def main() -> None:
    load_dotenv(ROOT / ".env")

    n8n_base = get_env("N8N_BASE_URL", required=True).rstrip("/")
    n8n_api_key = get_env("N8N_API_KEY", required=True)
    workflow_name = get_env("N8N_WORKFLOW_NAME", "Auto Blog Post Generation from Google Trends")
    n8n_access_token = get_env("N8N_ACCESS_TOKEN", "")
    workflow_id = get_env("N8N_WORKFLOW_ID", "")

    if not WORKFLOW_TEMPLATE.exists():
        raise RuntimeError(f"Workflow template not found: {WORKFLOW_TEMPLATE}")

    workflow = json.loads(WORKFLOW_TEMPLATE.read_text(encoding="utf-8"))
    workflow = patch_workflow(workflow)
    workflow["name"] = workflow_name
    workflow.setdefault("settings", {})

    if workflow_id:
        print(f"Updating existing workflow: {workflow_id}")
        res = n8n_request(
            "PUT",
            f"{n8n_base}/api/v1/workflows/{workflow_id}",
            n8n_api_key,
            workflow,
            access_token=n8n_access_token
        )
    else:
        print("Creating new workflow")
        res = n8n_request(
            "POST",
            f"{n8n_base}/api/v1/workflows",
            n8n_api_key,
            workflow,
            access_token=n8n_access_token
        )

    if not res.ok:
        raise RuntimeError(f"Workflow upsert failed ({res.status_code}): {res.text[:800]}")

    body = res.json()
    wf_id = body.get("id") or workflow_id
    if not wf_id:
        raise RuntimeError(f"Unable to determine workflow id from response: {body}")

    activate = n8n_request(
        "POST",
        f"{n8n_base}/api/v1/workflows/{wf_id}/activate",
        n8n_api_key,
        access_token=n8n_access_token
    )
    if not activate.ok:
        raise RuntimeError(
            f"Workflow created/updated but activation failed ({activate.status_code}): {activate.text[:800]}"
        )

    webhook_path = "trend-blog"
    for node in body.get("nodes", []):
        if (node.get("type") or "").endswith("webhook"):
            webhook_path = node.get("parameters", {}).get("path") or webhook_path
            break

    print("Done")
    print(f"Workflow ID: {wf_id}")
    print(f"Production webhook: {n8n_base}/webhook/{webhook_path}")


if __name__ == "__main__":
    main()


