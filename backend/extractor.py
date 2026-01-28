"""
Thread extraction interface.

Calls the standalone extract_worker.py script in a subprocess
to avoid Windows asyncio compatibility issues with Playwright.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from config import COOKIE_FILE, DEFAULT_TIMEOUT_MS
from models import Tweet, ThreadData


# Path to the extraction worker script
WORKER_SCRIPT = Path(__file__).parent / "extract_worker.py"


def load_cookies(cookie_file: Path = None) -> List[Dict]:
    """
    Load cookies from JSON file (for health check).
    """
    cookie_file = cookie_file or COOKIE_FILE

    if not cookie_file.exists():
        return []

    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        return [c for c in cookies if isinstance(c, dict) and c.get('name') and c.get('value')]
    except Exception:
        return []


async def extract_thread(
    url: str,
    timing_mode: str = 'normal',
    timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> ThreadData:
    """
    Extract a Twitter thread from the given URL.

    Runs the extraction in a subprocess to avoid Windows asyncio issues.
    """
    # Get the Python executable from the virtual environment
    # Try local venv first, then Google Drive venv
    venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        # Try Google Drive venv
        gdrive_venv = Path(r"C:\Users\bhara\dev\thread-unroller\backend\venv\Scripts\python.exe")
        if gdrive_venv.exists():
            venv_python = gdrive_venv
        else:
            # Fall back to system Python
            venv_python = sys.executable

    # Run extraction in subprocess (blocking call in executor)
    # Use longer timeout - extraction can take 30+ seconds
    timeout_seconds = max(120, timeout_ms // 1000 + 60)

    def run_subprocess():
        result = subprocess.run(
            [str(venv_python), str(WORKER_SCRIPT), url, timing_mode],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(WORKER_SCRIPT.parent),
        )
        return result

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_subprocess)

    # Parse output
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        print(f"DEBUG subprocess stderr: {stderr}")
        print(f"DEBUG subprocess stdout: {stdout}")

        # Try to parse JSON error from stdout
        try:
            data = json.loads(stdout)
            if "error" in data:
                raise Exception(f"{data['error']}: {data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            pass

        raise Exception(f"EXTRACTION_FAILED: Worker process failed: {stderr or stdout}")

    # Always log stderr for debugging (contains scroll progress info)
    if result.stderr:
        print(f"DEBUG subprocess stderr:\n{result.stderr}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse JSON: {result.stdout[:500]}")
        raise Exception(f"EXTRACTION_FAILED: Invalid JSON from worker: {e}")

    # Check for error response
    if "error" in data and not data.get("success"):
        raise Exception(f"{data['error']}: {data.get('message', 'Unknown error')}")

    # Convert to ThreadData model
    tweets = [
        Tweet(
            index=t["index"],
            text=t["text"],
            timestamp=t.get("timestamp"),
            media_urls=t.get("media_urls", [])
        )
        for t in data.get("tweets", [])
    ]

    return ThreadData(
        author=data.get("author", "Unknown"),
        handle=data.get("handle", "unknown"),
        date=data.get("date"),
        tweet_count=data.get("tweet_count", len(tweets)),
        tweets=tweets,
        thread_url=data.get("thread_url", url),
        tweet_id=data.get("tweet_id")
    )
