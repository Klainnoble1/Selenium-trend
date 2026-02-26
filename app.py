"""
Gradio app for Hugging Face Space: run the trends scraper from the UI.
Set N8N_WEBHOOK_URL in Space Secrets to send results to n8n.
"""

import os
import subprocess
import sys

import gradio as gr

from dotenv import load_dotenv

load_dotenv()


def run_scraper():
    """Run run_scraper.py and return combined stdout + stderr."""
    env = os.environ.copy()
    env["HEADLESS"] = "true"
    try:
        result = subprocess.run(
            [sys.executable, "run_scraper.py"],
            capture_output=True,
            text=True,
            timeout=600,
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
        return "Scraper timed out after 10 minutes. Try again or reduce countries."
    except Exception as e:
        return f"Error: {e}"


def main():
    has_webhook = "N8N_WEBHOOK_URL" in os.environ and os.environ.get("N8N_WEBHOOK_URL", "").strip()
    with gr.Blocks(title="Google Trends Scraper") as demo:
        gr.Markdown(
            "## Google Trends Scraper (4h real-time)\n"
            "Scrapes **US, UK, Canada, Germany, Switzerland**, fetches article content per trend, "
            "saves `trends_output.json` and sends to n8n if **N8N_WEBHOOK_URL** is set in Space Secrets."
        )
        if not has_webhook:
            gr.Markdown(
                "⚠️ **N8N_WEBHOOK_URL** is not set. Add it in **Space → Settings → Repository secrets** to send results to n8n."
            )
        btn = gr.Button("Run trends scraper")
        out = gr.Textbox(
            label="Log",
            lines=20,
            max_lines=30,
            interactive=False,
        )
        btn.click(fn=run_scraper, outputs=out)
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)


if __name__ == "__main__":
    main()
