"""
Media downloader for Thread Unroller.

Downloads images and videos from extracted threads using HTTP requests.
Runs after extraction completes — decoupled for reliability.
"""

import re
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, unquote

from config import COOKIE_FILE


# Default headers to mimic browser requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,video/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://x.com/",
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
DOWNLOAD_TIMEOUT_SECONDS = 60


def get_file_extension_from_url(url: str) -> str:
    """
    Extract file extension from URL.

    Handles Twitter's media URLs which often have format params like ?format=jpg
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)

    # Check query params for format (Twitter style: ?format=jpg&name=large)
    if parsed.query:
        params = dict(p.split('=') for p in parsed.query.split('&') if '=' in p)
        if 'format' in params:
            return params['format'].lower()

    # Fall back to path extension
    if '.' in path:
        ext = path.rsplit('.', 1)[-1].lower()
        # Clean up any query remnants
        ext = ext.split('?')[0].split('&')[0]
        if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'mov'):
            return ext

    # Default to jpg for images (most common on Twitter)
    return 'jpg'


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename."""
    # Replace invalid chars with underscore
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')


def generate_media_filename(url: str, index: int, tweet_index: int) -> str:
    """
    Generate a descriptive filename for a media file.

    Format: tweet{tweet_index}_media{index}.{ext}
    Example: tweet03_media01.jpg
    """
    ext = get_file_extension_from_url(url)
    return f"tweet{tweet_index:02d}_media{index:02d}.{ext}"


async def download_single_file(
    session: aiohttp.ClientSession,
    url: str,
    save_path: Path,
    retries: int = MAX_RETRIES
) -> Tuple[bool, Optional[str]]:
    """
    Download a single file with retry logic.

    Returns:
        (success, error_message)
    """
    last_error = None

    for attempt in range(retries):
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS),
                headers=DEFAULT_HEADERS
            ) as response:
                if response.status == 200:
                    content = await response.read()

                    # Ensure parent directory exists
                    save_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write file
                    with open(save_path, 'wb') as f:
                        f.write(content)

                    return (True, None)

                elif response.status == 404:
                    # Don't retry 404s
                    return (False, f"File not found (404): {url}")

                elif response.status == 403:
                    # Don't retry 403s - likely auth issue
                    return (False, f"Access denied (403): {url}")

                else:
                    last_error = f"HTTP {response.status}"

        except asyncio.TimeoutError:
            last_error = "Download timed out"

        except aiohttp.ClientError as e:
            last_error = str(e)

        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"

        # Wait before retry (except on last attempt)
        if attempt < retries - 1:
            await asyncio.sleep(RETRY_DELAY_SECONDS)

    return (False, f"Failed after {retries} attempts: {last_error}")


async def download_thread_media(
    media_urls: List[Dict[str, any]],
    archive_folder: Path,
) -> Dict[str, str]:
    """
    Download all media from a thread.

    Args:
        media_urls: List of dicts with 'url', 'tweet_index', 'media_index' keys
        archive_folder: Path to archive/[thread-name]/ folder

    Returns:
        Mapping of {original_url: local_relative_path} for successful downloads.
        Failed downloads are logged but don't stop other downloads.
    """
    media_folder = archive_folder / "media"
    media_folder.mkdir(parents=True, exist_ok=True)

    url_to_local: Dict[str, str] = {}
    failed_downloads: List[Tuple[str, str]] = []

    async with aiohttp.ClientSession() as session:
        # Download files concurrently but with some limit to avoid overwhelming
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent downloads

        async def download_with_semaphore(media_info: Dict) -> None:
            async with semaphore:
                url = media_info['url']
                tweet_idx = media_info['tweet_index']
                media_idx = media_info['media_index']

                filename = generate_media_filename(url, media_idx, tweet_idx)
                save_path = media_folder / filename

                success, error = await download_single_file(session, url, save_path)

                if success:
                    # Store relative path (relative to archive folder)
                    url_to_local[url] = f"media/{filename}"
                else:
                    failed_downloads.append((url, error))

        # Create tasks for all downloads
        tasks = [download_with_semaphore(m) for m in media_urls]
        await asyncio.gather(*tasks)

    # Log failures (could be enhanced to return these to caller)
    if failed_downloads:
        print(f"[media_downloader] {len(failed_downloads)} downloads failed:")
        for url, error in failed_downloads:
            print(f"  - {url}: {error}")

    return url_to_local


def extract_media_urls_from_thread(thread_data: dict) -> List[Dict]:
    """
    Extract all media URLs from thread data with their indices.

    Args:
        thread_data: ThreadData as dict (or ThreadData model)

    Returns:
        List of {url, tweet_index, media_index} dicts
    """
    media_list = []

    # Handle both dict and Pydantic model
    tweets = thread_data.get('tweets', []) if isinstance(thread_data, dict) else thread_data.tweets

    for tweet in tweets:
        # Handle both dict and Pydantic model
        tweet_index = tweet.get('index', 0) if isinstance(tweet, dict) else tweet.index
        media_urls = tweet.get('media_urls', []) if isinstance(tweet, dict) else tweet.media_urls

        for i, url in enumerate(media_urls, 1):
            media_list.append({
                'url': url,
                'tweet_index': tweet_index,
                'media_index': i,
            })

    return media_list
