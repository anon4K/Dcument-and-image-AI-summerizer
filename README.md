# DocQA — Document & Image Analyzer

Upload documents or images and get AI-generated summaries or descriptions, 
streamed live, with a history log and PDF export.

## Features
- Multi-file upload (PDF, DOCX, TXT, images) with drag-and-drop
- Live streaming AI responses via Server-Sent Events
- Automatic retry on transient AI provider errors
- Query history with latency tracking
- Client-side PDF export of results

## Tech stack
- Django (async views, ASGI via uvicorn)
- Google Gemini API (multimodal: text + image understanding)
- Vanilla JS frontend (SSE streaming, no framework)
- SQLite (dev) — swappable for Postgres in production

## Architecture
- Browser (upload.html): uploads files via fetch()
- qa/views.py  →  analyze() ← the main endpoint, async Django view
- qa/extract.py             ← pulls text out of PDF/DOCX/TXT files
- qa/llm.py                 ← talks to Gemini's API
- qa/models.py → QueryLog   ← saves each result to the database

## Running locally
\`\`\`bash
git clone ..., 
cd docqa, 
python -m venv venv, 
venv\Scripts\activate, 
pip install -r requirements.txt, 
# add GEMINI_API_KEY to .env, 
python manage.py migrate, 
uvicorn config.asgi:application --reload
\`\`\`

## What I'd improve next
- A Concurrent file processing which is currently sequential
- Real token/cost tracking from Gemini's usage metadata
- Postgres + pgvector for semantic search over past uploads
- Parse basic markdown before rendering to PDF. In simpler words, format gemini texts and render to jspdf.
