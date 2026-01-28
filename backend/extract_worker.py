"""
Standalone Playwright extraction worker.

This script runs in a separate process to avoid Windows asyncio
compatibility issues with uvicorn's event loop.

Usage: python extract_worker.py <url> [timing_mode]
Output: JSON to stdout
"""

import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, Page, ElementHandle

# Configuration (duplicated to avoid import issues in subprocess)
COOKIE_FILE = Path(r"C:\Users\bhara\dev\twitter-cookies.json")

TWITTER_DOMAINS = ["twitter.com", "x.com", "mobile.twitter.com", "mobile.x.com"]

TWEET_SELECTOR_CANDIDATES = [
    'article[data-testid="tweet"]',
    'article[role="article"]',
    '[data-testid="cellInnerDiv"] article',
]

BROWSER_VIEWPORT = {"width": 1280, "height": 4000}  # Tall viewport to load more tweets
DEFAULT_TIMEOUT_MS = 120000  # 2 minutes for slow pages/long threads

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

TIMING_CONFIGS = {
    'fast': {
        'wait_until': 'domcontentloaded',
        'initial_wait': 2000,
        'selector_timeout': 5000,
        'post_selector_wait': 500,
        'scroll_wait': 200,
        'fallback_wait': 3000,
    },
    'normal': {
        'wait_until': 'networkidle',
        'initial_wait': 4000,
        'selector_timeout': 8000,
        'post_selector_wait': 1500,
        'scroll_wait': 300,
        'fallback_wait': 4000,
    },
    'slow': {
        'wait_until': 'networkidle',
        'initial_wait': 6000,
        'selector_timeout': 12000,
        'post_selector_wait': 2500,
        'scroll_wait': 500,
        'fallback_wait': 6000,
    },
}


def get_timing(mode: str) -> dict:
    return TIMING_CONFIGS.get(mode, TIMING_CONFIGS['normal'])


def load_cookies(cookie_file: Path = None) -> List[Dict]:
    """Load cookies from JSON file and convert to Playwright format."""
    cookie_file = cookie_file or COOKIE_FILE

    if not cookie_file.exists():
        return []

    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)

        playwright_cookies = []
        for cookie in cookies:
            if not isinstance(cookie, dict):
                continue

            playwright_cookie = {
                'name': cookie.get('name'),
                'value': cookie.get('value'),
                'domain': cookie.get('domain', '.x.com'),
                'path': cookie.get('path', '/'),
            }

            if 'secure' in cookie:
                playwright_cookie['secure'] = bool(cookie.get('secure', False))
            if 'httpOnly' in cookie:
                playwright_cookie['httpOnly'] = bool(cookie.get('httpOnly', False))
            if 'sameSite' in cookie and cookie.get('sameSite'):
                same_site = str(cookie['sameSite']).capitalize()
                if same_site in ['Strict', 'Lax', 'None']:
                    playwright_cookie['sameSite'] = same_site

            if playwright_cookie['name'] and playwright_cookie['value']:
                playwright_cookies.append(playwright_cookie)

        return playwright_cookies

    except Exception as e:
        print(f"Error loading cookies: {e}", file=sys.stderr)
        return []


def parse_tweet_id(url: str) -> Optional[str]:
    """Extract tweet ID from URL."""
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else None


def extract_handle_from_url(url: str) -> str:
    """Extract @handle from Twitter URL."""
    try:
        parts = urlparse(url).path.strip("/").split("/")
        if parts and parts[0] not in {"i", "status"}:
            return parts[0]
    except Exception:
        pass
    return "unknown"


def extract_timestamp(page: Page) -> Optional[str]:
    """Extract tweet timestamp from time element."""
    try:
        page.wait_for_timeout(500)
        time_elements = page.query_selector_all('time[datetime]')

        for time_elem in time_elements:
            datetime_str = time_elem.get_attribute('datetime')
            if datetime_str:
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
    except Exception:
        pass
    return None


def expand_tweet_text(tweet_element: ElementHandle, page: Page) -> None:
    """Click 'Show more' button if present to expand truncated tweet text."""
    try:
        # Look for "Show more" button within the tweet
        show_more_selectors = [
            '[data-testid="tweet-text-show-more-link"]',
            'button[data-testid="tweet-text-show-more-link"]',
            'span:has-text("Show more")',
        ]

        for selector in show_more_selectors:
            show_more = tweet_element.query_selector(selector)
            if show_more:
                show_more.click()
                page.wait_for_timeout(300)  # Wait for expansion
                print(f"DEBUG: Clicked 'Show more' to expand tweet", file=sys.stderr)
                break
    except Exception as e:
        # Show more button not found or click failed - continue with truncated text
        pass


def extract_tweet_text(tweet_element: ElementHandle, page: Page = None) -> str:
    """Extract text content from a tweet element, expanding if truncated."""
    try:
        # First try to expand truncated text if page context available
        if page:
            expand_tweet_text(tweet_element, page)

        text_elem = tweet_element.query_selector('[data-testid="tweetText"]')
        if text_elem:
            return text_elem.inner_text()
    except Exception:
        pass
    return ""


def extract_media_urls(tweet_element: ElementHandle) -> List[str]:
    """Extract image and video URLs from a tweet element."""
    urls = []

    try:
        image_selectors = [
            'img[src*="pbs.twimg.com/media"]',
            'img[src*="ton.twitter.com"]',
        ]

        for selector in image_selectors:
            images = tweet_element.query_selector_all(selector)
            for img in images:
                src = img.get_attribute('src')
                if src:
                    clean_src = src.split('?')[0]
                    if clean_src not in urls:
                        full_src = clean_src + "?format=jpg&name=large"
                        urls.append(full_src)

        video_thumbs = tweet_element.query_selector_all('[data-testid="videoPlayer"] img')
        for thumb in video_thumbs:
            src = thumb.get_attribute('src')
            if src and 'pbs.twimg.com' in src:
                urls.append(src)

    except Exception:
        pass

    return urls


def get_author_handle(tweet_element: ElementHandle) -> Optional[str]:
    """Extract the @handle from a tweet element."""
    try:
        handle_elem = tweet_element.query_selector('[data-testid="User-Name"] a[href^="/"]')
        if handle_elem:
            href = handle_elem.get_attribute('href')
            if href:
                return href.strip('/').split('/')[0].lower()
    except Exception:
        pass
    return None


def get_author_display_name(tweet_element: ElementHandle) -> str:
    """Extract display name from a tweet element."""
    try:
        name_container = tweet_element.query_selector('[data-testid="User-Name"]')
        if name_container:
            name_link = name_container.query_selector('a span')
            if name_link:
                return name_link.inner_text()
    except Exception:
        pass
    return "Unknown"


def extract_thread(url: str, timing_mode: str = 'normal') -> dict:
    """
    Extract a Twitter thread from the given URL.

    Returns a dict with thread data or error information.
    """
    timing = get_timing(timing_mode)
    thread_author_handle = extract_handle_from_url(url).lower()
    tweet_id = parse_tweet_id(url)

    with sync_playwright() as p:
        user_agent = random.choice(USER_AGENTS)
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            viewport=BROWSER_VIEWPORT,
            user_agent=user_agent
        )

        cookies = load_cookies()
        if cookies:
            context.add_cookies(cookies)

        page = context.new_page()

        try:
            # Navigate to thread
            page.goto(url, wait_until=timing['wait_until'], timeout=DEFAULT_TIMEOUT_MS)
            page.wait_for_timeout(timing['initial_wait'])

            # Wait for tweets to load with retry
            tweet_selector = TWEET_SELECTOR_CANDIDATES[0]
            tweets_found = False
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    page.wait_for_selector(tweet_selector, timeout=timing['selector_timeout'])
                    page.wait_for_timeout(timing['post_selector_wait'])
                    tweet_elements = page.query_selector_all(tweet_selector)
                    if len(tweet_elements) > 0:
                        tweets_found = True
                        print(f"DEBUG: Found tweets on attempt {attempt + 1}", file=sys.stderr)
                        break
                except Exception:
                    pass

                # Retry: wait and try again
                if attempt < max_retries - 1:
                    print(f"DEBUG: Attempt {attempt + 1} failed, retrying...", file=sys.stderr)
                    page.wait_for_timeout(timing['fallback_wait'])

            # Check for failures if no tweets found after all retries
            if not tweets_found:
                content = page.content()
                title = page.title()
                print(f"DEBUG: Page title: {title}", file=sys.stderr)
                print(f"DEBUG: Content length: {len(content)}", file=sys.stderr)

                if "Something went wrong" in content:
                    return {"error": "RATE_LIMITED", "message": "Twitter has rate-limited this request"}
                elif "Log in" in content and "Sign up" in content:
                    return {"error": "AUTH_FAILED", "message": "Cookies not working - Twitter asking for login"}
                else:
                    return {"error": "EXTRACTION_FAILED", "message": f"No tweets found. Page title: {title}"}

            # Get timestamp from first tweet
            thread_date = extract_timestamp(page)

            # Click any "Show this thread" or thread continuation links
            thread_expand_selectors = [
                'a[href*="/status/"][aria-label*="Show"]',
                'div[role="link"]:has-text("Show this thread")',
                'span:has-text("Show this thread")',
                '[data-testid="tweet"] a:has-text("Show more replies")',
            ]
            for selector in thread_expand_selectors:
                try:
                    expand_links = page.query_selector_all(selector)
                    for link in expand_links[:5]:  # Limit to avoid clicking too many
                        link.click()
                        page.wait_for_timeout(1000)
                        print(f"DEBUG: Clicked thread expansion link", file=sys.stderr)
                except Exception:
                    pass

            # Collect all tweets with scrolling to load more
            # Strategy: scroll slowly through the page, extracting tweets as we go
            # Twitter virtualizes the DOM, so we must extract before scrolling away
            tweets = []
            author_display_name = None
            seen_texts = set()
            max_scroll_attempts = 30  # Allow more scrolls for long threads
            no_new_tweets_count = 0
            max_no_new = 5  # Be more patient - sometimes tweets take time to load
            last_scroll_position = 0

            for scroll_attempt in range(max_scroll_attempts):
                # Get current scroll position
                current_scroll = page.evaluate("window.scrollY")

                tweet_elements = page.query_selector_all(tweet_selector)
                print(f"DEBUG: Scroll {scroll_attempt + 1}: Found {len(tweet_elements)} elements at scroll pos {current_scroll}", file=sys.stderr)

                new_tweets_this_scroll = 0

                for tweet_elem in tweet_elements:
                    try:
                        tweet_handle = get_author_handle(tweet_elem)

                        if tweet_handle and tweet_handle == thread_author_handle:
                            if author_display_name is None:
                                author_display_name = get_author_display_name(tweet_elem)

                            # Extract text without clicking "Show more" to avoid DOM disruption
                            # Note: Some tweets may be truncated due to Twitter's virtualization
                            text = extract_tweet_text(tweet_elem, None)

                            if text and text not in seen_texts:
                                seen_texts.add(text)
                                media_urls = extract_media_urls(tweet_elem)

                                tweets.append({
                                    "index": len(tweets) + 1,
                                    "text": text,
                                    "timestamp": None,
                                    "media_urls": media_urls
                                })
                                new_tweets_this_scroll += 1
                                print(f"DEBUG: Extracted tweet {len(tweets)}: {text[:50]}...", file=sys.stderr)

                        if len(tweets) >= 50:
                            break
                    except Exception as e:
                        # Element may have been detached from DOM
                        continue

                if len(tweets) >= 50:
                    print(f"DEBUG: Reached max tweet limit (50)", file=sys.stderr)
                    break

                # Check if we found new tweets this scroll
                if new_tweets_this_scroll == 0:
                    no_new_tweets_count += 1
                    print(f"DEBUG: No new tweets found (attempt {no_new_tweets_count}/{max_no_new})", file=sys.stderr)
                    if no_new_tweets_count >= max_no_new:
                        print(f"DEBUG: Stopping - no new tweets after {max_no_new} scrolls", file=sys.stderr)
                        break
                else:
                    no_new_tweets_count = 0  # Reset counter if we found new tweets

                # Scroll down by a smaller amount to catch all tweets (half viewport)
                page.evaluate("window.scrollBy(0, window.innerHeight * 0.6)")
                page.wait_for_timeout(timing['scroll_wait'] + 800)  # Extra wait for lazy loading

                # Check if we've reached the bottom
                new_scroll = page.evaluate("window.scrollY")
                if new_scroll == last_scroll_position and scroll_attempt > 5:
                    print(f"DEBUG: Reached bottom of page", file=sys.stderr)
                    # One more attempt after reaching bottom
                    no_new_tweets_count = max(no_new_tweets_count, max_no_new - 1)
                last_scroll_position = new_scroll

            print(f"DEBUG: Total tweets extracted: {len(tweets)}", file=sys.stderr)

            if not tweets:
                return {"error": "EXTRACTION_FAILED", "message": "No tweets found from thread author"}

            return {
                "success": True,
                "author": author_display_name or thread_author_handle,
                "handle": thread_author_handle,
                "date": thread_date,
                "tweet_count": len(tweets),
                "tweets": tweets,
                "thread_url": url,
                "tweet_id": tweet_id
            }

        finally:
            context.close()
            browser.close()


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "INVALID_ARGS", "message": "Usage: python extract_worker.py <url> [timing_mode]"}))
        sys.exit(1)

    url = sys.argv[1]
    timing_mode = sys.argv[2] if len(sys.argv) > 2 else 'normal'

    try:
        result = extract_thread(url, timing_mode)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": "EXCEPTION", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
