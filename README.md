# Thread Unroller

A local-first tool to extract and format Twitter/X threads into portable, shareable formats. No API keys needed — uses cookie-based browser automation (Playwright) to access threads as an authenticated user.

Built for researchers, writers, and anyone who wants to save threads without paying for yet another SaaS subscription.

## Features

- **Thread Extraction**: Paste a thread URL, get structured content back
- **Multiple Formats**: Export as Markdown (for notes/LLMs) or JSON (for data processing)
- **Save to Archive**: Download complete threads with all media (images, videos) for offline access
- **Local Web UI**: Simple interface to preview, copy, and download

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Twitter/X account (for cookie-based auth)

### Installation

```bash
git clone https://github.com/yourusername/thread-unroller.git
cd thread-unroller

# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
playwright install chromium

# Frontend
cd ../frontend
npm install
```

### Cookie Setup

This tool uses your browser cookies for authentication (no API keys).

1. Log into Twitter/X in your browser
2. Export cookies using a browser extension (e.g., "Cookie-Editor")
3. Save as `twitter-cookies.json` outside the project directory
4. Update the path in `backend/config.py` if needed

### Running

```bash
# Terminal 1: Start backend
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

Open http://localhost:5174 in your browser.

## Architecture

```
Browser (React + Vite)     →  FastAPI Backend  →  Playwright Extractor
localhost:5174                localhost:8000       (cookie-based auth)
                                    ↓
                              Format Converters
                              (MD, JSON, HTML)
                                    ↓
                              Media Downloader
                              (for archive mode)
```

**Key files:**
- `backend/main.py` — API endpoints
- `backend/extractor.py` — Thread extraction logic
- `backend/formatters.py` — Output format converters
- `frontend/src/App.tsx` — Main UI

## Limitations

- Single thread at a time (no batch processing yet)
- Cookies expire — refresh periodically
- Quote tweets and embedded threads not expanded (v1)
- Local tool only — not a hosted service

## License

MIT
