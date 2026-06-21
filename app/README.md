# RAG Knowledge App Frontend

This directory contains the primary web UI for the RAG knowledge assistant.

The frontend is built with:

- Next.js
- shadcn/ui and Radix UI
- Tailwind CSS
- lucide-react icons

The RAG core still runs in Python. The frontend talks to the Python FastAPI service and must not access SQLite, Chroma, chat models, or embedding models directly.

## Prerequisites

Start the Python API from the project root:

```powershell
uv run rag-api
```

The default API address is:

```text
http://127.0.0.1:8000
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
http://localhost:8000
```

To use a different API address, create `app/.env.local`:

```text
NEXT_PUBLIC_RAG_API_BASE_URL=http://127.0.0.1:8000
```

## Checks

```powershell
npm run typecheck
npm run lint
npm run build
```

## UI Structure

- Left workspace sidebar: document management, new conversation, conversation history, settings.
- Main chat area: centered message stream and bottom input.
- Document manager: batch upload, automatic parsing and indexing, duplicate hints, delete, reindex.
- Settings: model configuration, retrieval parameters, embedding rate limits, language switch, future account placeholder.
