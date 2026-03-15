"""
Configuration settings for Thread Unroller.

Paths, timing configs, and other settings.
"""

from pathlib import Path
from typing import Dict, Any

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
ARCHIVE_DIR = PROJECT_ROOT / "archive"

# Cookie file location (from Twitter Screenshots project)
COOKIE_FILE = Path(r"C:\Users\bhara\dev\twitter-cookies.json")

# Twitter/X domains we recognize
TWITTER_DOMAINS = {"x.com", "twitter.com", "mobile.twitter.com"}

# Tweet element selectors (from reference script)
# These may need updating if Twitter changes their DOM structure
TWEET_SELECTOR_CANDIDATES = [
    'article[data-testid="tweet"]',
    'div[data-testid="tweet"]',  # fallback
]

# Timing configurations for Playwright waits
# "normal" is faster but may miss content on slow connections
# "slow" is more reliable but takes longer
TIMING_CONFIG: Dict[str, Dict[str, Any]] = {
    'normal': {
        'wait_until': 'domcontentloaded',
        'initial_wait': 3000,          # ms after page load
        'selector_timeout': 5000,      # ms to wait for tweet element
        'post_selector_wait': 500,     # ms after finding selector
        'fallback_wait': 2000,         # ms if selector not found
        'scroll_wait': 300,            # ms after scrolling to element
        'capture_settle': 500,         # ms before extracting content
    },
    'slow': {
        'wait_until': 'domcontentloaded',
        'initial_wait': 6000,
        'selector_timeout': 12000,
        'post_selector_wait': 1500,
        'fallback_wait': 4000,
        'scroll_wait': 800,
        'capture_settle': 1500,
    }
}

# Default timing mode
DEFAULT_TIMING_MODE = 'normal'

# Browser settings
BROWSER_VIEWPORT = {"width": 1280, "height": 2000}
DEFAULT_TIMEOUT_MS = 30000

# User agents for rotation (helps avoid detection)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# API settings
API_HOST = "127.0.0.1"
API_PORT = 8000
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite dev server (legacy)
    "http://127.0.0.1:5173",
    "http://localhost:5174",  # Thread Unroller Frontend (new port)
    "http://127.0.0.1:5174",
]


def get_timing(mode: str = None) -> Dict[str, Any]:
    """Get timing configuration for specified mode."""
    mode = mode or DEFAULT_TIMING_MODE
    return TIMING_CONFIG.get(mode, TIMING_CONFIG['normal'])
