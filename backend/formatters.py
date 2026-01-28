"""
Output formatters for thread data.

Converts ThreadData into Markdown, JSON, or HTML formats.
"""

import json
from typing import Dict, Optional
from models import ThreadData


def thread_to_markdown(thread: ThreadData, include_media: bool = True) -> str:
    """
    Format thread as Markdown.

    Output format:
    # Thread by @handle

    **Author:** Display Name (@handle)
    **Date:** 2024-01-15 | **Tweets:** 12

    ---

    ## 1/12

    Tweet text here...

    ![Image](media_url)

    ---
    """
    lines = []

    # Header
    lines.append(f"# Thread by @{thread.handle}")
    lines.append("")

    # Metadata
    meta_parts = [f"**Author:** {thread.author} (@{thread.handle})"]
    if thread.date:
        meta_parts.append(f"**Date:** {thread.date}")
    meta_parts.append(f"**Tweets:** {thread.tweet_count}")
    lines.append(" | ".join(meta_parts))
    lines.append("")
    lines.append("---")
    lines.append("")

    # Each tweet
    for tweet in thread.tweets:
        # Tweet header with position
        lines.append(f"## {tweet.index}/{thread.tweet_count}")
        lines.append("")

        # Tweet text
        lines.append(tweet.text)
        lines.append("")

        # Media (if included)
        if include_media and tweet.media_urls:
            for i, url in enumerate(tweet.media_urls, 1):
                lines.append(f"![Image {i}]({url})")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Footer with source
    lines.append(f"*Source: [{thread.thread_url}]({thread.thread_url})*")

    return "\n".join(lines)


def thread_to_json(thread: ThreadData) -> str:
    """
    Format thread as JSON.

    Returns pretty-printed JSON string of the ThreadData.
    """
    # Convert to dict, handling nested models
    data = {
        "author": thread.author,
        "handle": thread.handle,
        "date": thread.date,
        "tweet_count": thread.tweet_count,
        "thread_url": thread.thread_url,
        "tweet_id": thread.tweet_id,
        "tweets": [
            {
                "index": t.index,
                "text": t.text,
                "timestamp": t.timestamp,
                "media_urls": t.media_urls
            }
            for t in thread.tweets
        ]
    }

    return json.dumps(data, indent=2, ensure_ascii=False)


def thread_to_html(
    thread: ThreadData,
    media_mapping: Optional[Dict[str, str]] = None,
) -> str:
    """
    Format thread as HTML with embedded media.

    Args:
        thread: ThreadData to format
        media_mapping: Optional dict mapping original URLs to local paths.
                       If provided, uses local paths; otherwise uses original URLs.

    Output: Standalone HTML file viewable in browser, printable to PDF.
    """
    # Use local paths if mapping provided, otherwise original URLs
    def get_media_src(url: str) -> str:
        if media_mapping and url in media_mapping:
            return media_mapping[url]
        return url

    # Escape HTML special characters in text
    def escape_html(text: str) -> str:
        return (
            text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace('\n', '<br>\n')
        )

    # Build tweet HTML
    tweets_html = []
    for tweet in thread.tweets:
        media_html = ""
        if tweet.media_urls:
            media_items = []
            for url in tweet.media_urls:
                src = get_media_src(url)
                # Check if video (mp4, webm, mov)
                if any(src.lower().endswith(ext) for ext in ('.mp4', '.webm', '.mov')):
                    media_items.append(
                        f'<video controls class="tweet-media">'
                        f'<source src="{src}" type="video/mp4">'
                        f'Your browser does not support video.'
                        f'</video>'
                    )
                else:
                    media_items.append(
                        f'<img src="{src}" alt="Tweet media" class="tweet-media" loading="lazy">'
                    )
            media_html = '<div class="tweet-media-container">' + '\n'.join(media_items) + '</div>'

        tweet_html = f'''
        <article class="tweet">
            <header class="tweet-header">
                <span class="tweet-index">{tweet.index}/{thread.tweet_count}</span>
                {f'<time class="tweet-time">{tweet.timestamp}</time>' if tweet.timestamp else ''}
            </header>
            <div class="tweet-text">{escape_html(tweet.text)}</div>
            {media_html}
        </article>
        '''
        tweets_html.append(tweet_html)

    # Full HTML document
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thread by @{thread.handle}</title>
    <style>
        :root {{
            --bg-primary: #0c0f0d;
            --bg-secondary: #151a16;
            --text-primary: #e8e6e3;
            --text-secondary: #a0a0a0;
            --accent: #a67c52;
            --border: #2a2f2c;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
            max-width: 700px;
            margin: 0 auto;
        }}

        header.thread-header {{
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }}

        h1 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .thread-meta {{
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}

        .thread-meta span {{
            margin-right: 1rem;
        }}

        .tweet {{
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }}

        .tweet-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            font-size: 0.875rem;
        }}

        .tweet-index {{
            color: var(--accent);
            font-weight: 600;
        }}

        .tweet-time {{
            color: var(--text-secondary);
        }}

        .tweet-text {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .tweet-media-container {{
            margin-top: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .tweet-media {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}

        video.tweet-media {{
            width: 100%;
        }}

        footer.thread-footer {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}

        footer a {{
            color: var(--accent);
            text-decoration: none;
        }}

        footer a:hover {{
            text-decoration: underline;
        }}

        /* Print styles */
        @media print {{
            body {{
                background: white;
                color: black;
                padding: 1rem;
            }}

            .tweet {{
                background: #f5f5f5;
                break-inside: avoid;
            }}

            .tweet-index {{
                color: #666;
            }}
        }}
    </style>
</head>
<body>
    <header class="thread-header">
        <h1>Thread by @{thread.handle}</h1>
        <div class="thread-meta">
            <span><strong>{thread.author}</strong></span>
            {f'<span>{thread.date}</span>' if thread.date else ''}
            <span>{thread.tweet_count} tweets</span>
        </div>
    </header>

    <main>
        {''.join(tweets_html)}
    </main>

    <footer class="thread-footer">
        <p>Source: <a href="{thread.thread_url}" target="_blank">{thread.thread_url}</a></p>
    </footer>
</body>
</html>
'''
    return html


def format_thread(
    thread: ThreadData,
    format: str,
    include_media: bool = True,
    media_mapping: Optional[Dict[str, str]] = None,
) -> str:
    """
    Format thread using the specified format.

    Args:
        thread: ThreadData to format
        format: One of "markdown", "json", "html"
        include_media: Whether to include media URLs (not used for JSON)
        media_mapping: For HTML, optional mapping of original URLs to local paths

    Returns:
        Formatted string
    """
    if format == "json":
        return thread_to_json(thread)
    elif format == "html":
        return thread_to_html(thread, media_mapping)
    else:
        # Default to markdown
        return thread_to_markdown(thread, include_media)


def get_file_extension(format: str) -> str:
    """Get appropriate file extension for format."""
    extensions = {
        "markdown": "md",
        "json": "json",
        "html": "html",
    }
    return extensions.get(format, "md")
