# RAG Knowledge App Frontend

This directory contains the primary web UI for the RAG knowledge assistant.

The frontend is built with:

- Next.js
- shadcn/ui and Radix UI
- Tailwind CSS
- lucide-react icons

The RAG core still runs in Python. The frontend talks to the Python FastAPI service and must not access SQLite, Chroma, chat models, or embedding models directly.

## Current UI

- RAGFlow-style overview dashboard with warm orange palette, left navigation, top search, metric cards, QA test panel, recent imports, activity, and trend panels.
- Document manager with batch upload, automatic parsing/indexing, duplicate hints, desktop table, and responsive layout.
- Conversation test view with session list, message stream, and composer.
- Document manager with batch upload, automatic parsing/indexing, duplicate hints, desktop table, and mobile cards.
- Settings page for chat model, embedding model, retrieval parameters, embedding rate limits, presets, tests, and language switch.
- Responsive mobile navigation verified with Playwright.

## Prerequisites

Start the Python API from the project root:

```powershell
uv run rag-api
```

The default API address is:

```text
http://127.0.0.1:8000
```

You can check the API with:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health
```

## Install

From this directory:

```powershell
npm install
```

## Run

```powershell
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

By default, the frontend calls:

```text
http://127.0.0.1:8000
```

To use a different API address, create `app/.env.local`:

```text
NEXT_PUBLIC_RAG_API_BASE_URL=http://127.0.0.1:8000
```

## Production Smoke Test

```powershell
npm run build
npm run start -- --hostname 127.0.0.1 --port 3001
```

Open:

```text
http://127.0.0.1:3001
```

The FastAPI CORS configuration allows the common local ports `3000` and `3001`.

## Checks

```powershell
npm run typecheck
npm run lint
npm run build
```

## UI Structure

- Left workspace sidebar: overview, document management, retrieval/conversation testing, settings, status, and recent conversations.
- Overview: metric cards, smart Q&A test, retrieved snippets, generated answer, recent import tasks, activities, and visual trend panels.
- Document manager: batch upload, automatic parsing and indexing, duplicate hints, delete, reindex.
- Conversation test: session list, message stream, delete, new conversation, and question composer.
- Settings: model configuration, retrieval parameters, embedding rate limits, language switch, future account placeholder.

## Troubleshooting

If the API fails with `Errno 10048`, port `8000` is already in use:

```powershell
netstat -ano | Select-String ':8000'
```

After confirming the PID is the old API process:

```powershell
Stop-Process -Id <PID> -Force
```

If the frontend opens but data does not load, verify `NEXT_PUBLIC_RAG_API_BASE_URL` and confirm `/api/health` returns `200`.
