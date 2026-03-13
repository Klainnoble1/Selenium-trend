"""
Gradio app for Hugging Face Space: run source-specific trends scrapers from the UI.
Set N8N_WEBHOOK_URL in Space Secrets to send results to n8n.
"""

import os
import subprocess
import sys

import gradio as gr

from dotenv import load_dotenv

load_dotenv()


def run_scraper(script_name: str):
    """Run a source-specific script and return combined stdout + stderr."""
    env = os.environ.copy()
    env["HEADLESS"] = "true"
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=2400,
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        combined = out + ("\n" + err if err else "")
        if result.returncode != 0:
            combined = f"[Exit code {result.returncode}]\n{combined}"
        return combined or "Done (no output)."
    except subprocess.TimeoutExpired:
        return "Scraper timed out after 40 minutes. Try again or reduce countries."
    except Exception as e:
        return f"Error: {e}"


def main():
    has_webhook = "N8N_WEBHOOK_URL" in os.environ and os.environ.get("N8N_WEBHOOK_URL", "").strip()
    with gr.Blocks(title="Trends Scraper") as demo:
        gr.Markdown(
            "## Trends Scraper\n"
            "Production path: **Google Trends**.\n\n"
            "The UI keeps **X** and **NewsAPI** buttons available for later testing, "
            "but the documented production path is Google only."
        )
        if not has_webhook:
            gr.Markdown(
                "Warning: **N8N_WEBHOOK_URL** is not set. Add it in **Space -> Settings -> Repository secrets** to send results to n8n."
            )
        with gr.Row():
            btn_google = gr.Button("Run Google Trends")
            btn_x = gr.Button("Run X Trends")
            btn_newsapi = gr.Button("Run NewsAPI Trends")
        out = gr.Textbox(
            label="Log",
            lines=20,
            max_lines=30,
            interactive=False,
        )
        btn_google.click(fn=lambda: run_scraper("run_google_trends.py"), outputs=out)
        btn_x.click(fn=lambda: run_scraper("run_x_trends.py"), outputs=out)
        btn_newsapi.click(fn=lambda: run_scraper("run_newsapi_trends.py"), outputs=out)
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)


if __name__ == "__main__":
    main()
