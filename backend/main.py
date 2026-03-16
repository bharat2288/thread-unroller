"""
Thread Unroller API.

FastAPI backend for extracting Twitter/X threads into various formats.
"""

import re
import sys
import asyncio

# Fix for Playwright on Windows - must use WindowsSelectorEventLoopPolicy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from config import COOKIE_FILE, CORS_ORIGINS, ARCHIVE_DIR
from models import (
    UnrollRequest,
    UnrollResponse,
    HealthResponse,
    ArchiveRequest,
    ArchiveResponse,
)
from extractor import extract_thread, load_cookies
from formatters import thread_to_markdown, thread_to_json, thread_to_html, format_thread
from media_downloader import download_thread_media, extract_media_urls_from_thread


import os
_debug = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")
app = FastAPI(
    title="Thread Unroller",
    description="Extract Twitter/X threads into Markdown, JSON, or HTML with media",
    version="1.1.0",
    docs_url="/docs" if _debug else None,
    redoc_url="/redoc" if _debug else None,
    openapi_url="/openapi.json" if _debug else None,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check service health and cookie status.

    Returns information about whether cookies are loaded and valid.
    """
    cookies = load_cookies()

    return HealthResponse(
        status="healthy",
        cookies_loaded=len(cookies) > 0,
        cookie_count=len(cookies),
        cookie_file_exists=COOKIE_FILE.exists(),
    )


@app.post("/unroll", response_model=UnrollResponse)
async def unroll_thread(request: UnrollRequest):
    """
    Extract and format a Twitter/X thread.

    Takes a thread URL and returns the thread content in the requested format.
    Extraction uses Playwright with cookie-based authentication.

    This endpoint may take 10-30 seconds depending on thread length.
    """
    try:
        # Extract thread data
        thread_data = await extract_thread(
            url=request.url,
            timing_mode='normal',
        )

        # Format output
        formatted = format_thread(
            thread=thread_data,
            format=request.format,
            include_media=request.include_media,
        )

        return UnrollResponse(
            success=True,
            thread_data=thread_data,
            formatted_output=formatted,
            format=request.format,
            error=None,
            error_code=None,
        )

    except ValidationError as e:
        return UnrollResponse(
            success=False,
            thread_data=None,
            formatted_output=None,
            format=request.format,
            error=str(e),
            error_code="INVALID_URL",
        )

    except Exception as e:
        error_msg = str(e)

        # Determine error code from exception message
        if "RATE_LIMITED" in error_msg:
            error_code = "RATE_LIMITED"
            error_msg = "Twitter has rate-limited this request. Try again in a few minutes."
        elif "EXTRACTION_FAILED" in error_msg:
            error_code = "EXTRACTION_FAILED"
        elif "timeout" in error_msg.lower():
            error_code = "TIMEOUT"
            error_msg = "Request timed out. The thread may be too long or Twitter is slow."
        else:
            error_code = "UNKNOWN"

        return UnrollResponse(
            success=False,
            thread_data=None,
            formatted_output=None,
            format=request.format,
            error=error_msg,
            error_code=error_code,
        )


def sanitize_folder_name(name: str) -> str:
    """Remove invalid characters from folder name."""
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')


@app.post("/archive", response_model=ArchiveResponse)
async def save_to_archive(request: ArchiveRequest):
    """
    Save thread to archive with media.

    Creates a folder with:
    - thread.md (Markdown for LLM input)
    - thread.html (viewable with local media)
    - thread.json (structured data)
    - media/ (downloaded images and videos)

    Can accept either a URL (will extract) or pre-extracted thread_data.
    """
    try:
        # Get thread data - either extract fresh or use provided
        if request.thread_data:
            thread_data = request.thread_data
        elif request.url:
            thread_data = await extract_thread(url=request.url, timing_mode='normal')
        else:
            return ArchiveResponse(
                success=False,
                error="Must provide either 'url' or 'thread_data'",
            )

        # Create archive folder: archive/handle_date_tweetid/
        date_part = thread_data.date or "unknown"
        tweet_id = thread_data.tweet_id or "unknown"
        folder_name = sanitize_folder_name(f"{thread_data.handle}_{date_part}_{tweet_id}")
        archive_folder = ARCHIVE_DIR / folder_name
        archive_folder.mkdir(parents=True, exist_ok=True)

        files_created = []

        # Extract media URLs from thread
        media_urls = extract_media_urls_from_thread(thread_data.model_dump())

        # Download media files
        media_mapping = {}
        media_downloaded = 0
        media_failed = 0

        if media_urls:
            media_mapping = await download_thread_media(media_urls, archive_folder)
            media_downloaded = len(media_mapping)
            media_failed = len(media_urls) - media_downloaded

        # Create base filename: handle_date (e.g., "travis_kling_2024-03-05")
        base_filename = f"{thread_data.handle}_{date_part}"

        # Generate and save Markdown
        md_content = thread_to_markdown(thread_data, include_media=True)
        md_filename = f"{base_filename}.md"
        md_path = archive_folder / md_filename
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        files_created.append(md_filename)

        # Generate and save JSON
        json_content = thread_to_json(thread_data)
        json_filename = f"{base_filename}.json"
        json_path = archive_folder / json_filename
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        files_created.append(json_filename)

        # Generate and save HTML with local media paths
        html_content = thread_to_html(thread_data, media_mapping=media_mapping)
        html_filename = f"{base_filename}.html"
        html_path = archive_folder / html_filename
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        files_created.append(html_filename)

        # Add media folder to list if any media was downloaded
        if media_downloaded > 0:
            files_created.append(f"media/ ({media_downloaded} files)")

        return ArchiveResponse(
            success=True,
            archive_path=str(archive_folder),
            files_created=files_created,
            media_downloaded=media_downloaded,
            media_failed=media_failed,
        )

    except Exception as e:
        return ArchiveResponse(
            success=False,
            error=str(e),
        )


# For running directly with: python -m backend.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
