#!/usr/bin/env python3
"""
Run the trends scraper as a long-running worker.

Environment:
  RUN_ONCE=true        Run a single scrape and exit.
  SCRAPE_INTERVAL_MINUTES=360
                       Delay between runs when looping.
  HEADLESS=true        Use headless browser mode.
"""

import os
import subprocess
import sys
import time
from datetime import datetime, timezone


def run_scraper_once() -> int:
    env = os.environ.copy()
    env.setdefault("HEADLESS", "true")

    print(f"[{timestamp()}] Starting scraper run...", flush=True)
    result = subprocess.run(
        [sys.executable, "run_scraper.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
    )
    print(
        f"[{timestamp()}] Scraper finished with exit code {result.returncode}",
        flush=True,
    )
    return result.returncode


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    run_once = os.environ.get("RUN_ONCE", "false").lower() == "true"
    interval_minutes = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "360"))

    if run_once:
        raise SystemExit(run_scraper_once())

    while True:
        run_scraper_once()
        sleep_seconds = max(interval_minutes, 1) * 60
        print(
            f"[{timestamp()}] Sleeping for {interval_minutes} minutes before next run.",
            flush=True,
        )
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
