"""
Pydantic models for Thread Unroller API.

Defines request/response schemas for the /unroll endpoint.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse


class UnrollRequest(BaseModel):
    """Request body for /unroll endpoint."""

    url: str = Field(..., description="Twitter/X thread URL")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description="Output format for preview (markdown or json)"
    )
    include_media: bool = Field(
        default=True,
        description="Include media URLs in output"
    )

    @field_validator('url')
    @classmethod
    def validate_twitter_url(cls, v: str) -> str:
        """Ensure URL is a valid Twitter/X status URL."""
        v = v.strip()

        # Must have a scheme
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v

        parsed = urlparse(v)

        # Check domain
        valid_domains = {'x.com', 'twitter.com', 'mobile.twitter.com'}
        domain = parsed.netloc.lower().replace('www.', '')
        if domain not in valid_domains:
            raise ValueError(f"URL must be from twitter.com or x.com, got: {domain}")

        # Check for /status/ in path (indicates a tweet)
        if '/status/' not in parsed.path:
            raise ValueError("URL must be a tweet URL (should contain /status/)")

        return v


class Tweet(BaseModel):
    """A single tweet in a thread."""

    index: int = Field(..., description="Position in thread (1-indexed)")
    text: str = Field(..., description="Tweet text content")
    timestamp: Optional[str] = Field(None, description="ISO timestamp if available")
    media_urls: List[str] = Field(default_factory=list, description="URLs of images/videos")


class ThreadData(BaseModel):
    """Structured data for an extracted thread."""

    author: str = Field(..., description="Display name of thread author")
    handle: str = Field(..., description="@handle of thread author")
    date: Optional[str] = Field(None, description="Date of first tweet (YYYY-MM-DD)")
    tweet_count: int = Field(..., description="Number of tweets in thread")
    tweets: List[Tweet] = Field(..., description="List of tweets in order")
    thread_url: str = Field(..., description="Original URL")
    tweet_id: Optional[str] = Field(None, description="ID of first tweet")


class UnrollResponse(BaseModel):
    """Response from /unroll endpoint."""

    success: bool = Field(..., description="Whether extraction succeeded")
    thread_data: Optional[ThreadData] = Field(None, description="Extracted thread data")
    formatted_output: Optional[str] = Field(None, description="Formatted thread content")
    format: str = Field(..., description="Format used for output")
    error: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(
        None,
        description="Error code: RATE_LIMITED, INVALID_URL, AUTH_FAILED, EXTRACTION_FAILED"
    )


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str = Field(..., description="Service status")
    cookies_loaded: bool = Field(..., description="Whether cookies were loaded")
    cookie_count: int = Field(..., description="Number of cookies loaded")
    cookie_file_exists: bool = Field(..., description="Whether cookie file exists")


class ArchiveRequest(BaseModel):
    """
    Request to save thread to archive with media.

    Can either provide a URL (will extract fresh) or existing thread_data.
    """
    url: Optional[str] = Field(None, description="Thread URL to extract and archive")
    thread_data: Optional[ThreadData] = Field(None, description="Pre-extracted thread data")

    @field_validator('url')
    @classmethod
    def validate_twitter_url(cls, v: Optional[str]) -> Optional[str]:
        """Ensure URL is a valid Twitter/X status URL if provided."""
        if v is None:
            return v

        v = v.strip()

        # Must have a scheme
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v

        parsed = urlparse(v)

        # Check domain
        valid_domains = {'x.com', 'twitter.com', 'mobile.twitter.com'}
        domain = parsed.netloc.lower().replace('www.', '')
        if domain not in valid_domains:
            raise ValueError(f"URL must be from twitter.com or x.com, got: {domain}")

        # Check for /status/ in path (indicates a tweet)
        if '/status/' not in parsed.path:
            raise ValueError("URL must be a tweet URL (should contain /status/)")

        return v


class ArchiveResponse(BaseModel):
    """Response from /archive endpoint."""

    success: bool
    archive_path: Optional[str] = Field(None, description="Path to archive folder")
    files_created: List[str] = Field(default_factory=list, description="List of created files")
    media_downloaded: int = Field(0, description="Number of media files downloaded")
    media_failed: int = Field(0, description="Number of media downloads that failed")
    error: Optional[str] = None
