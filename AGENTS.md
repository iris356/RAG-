# Repository Guidelines

## Project Structure & Module Organization

This repository contains a local RAG knowledge base app built around Python, LangChain, FastAPI, Chroma, and SQLite. Core backend code lives in `src/rag_app/`, with focused packages for `api/`, `core/`, `documents/`, `vectors/`, `qa/`, `conversations/`, and `models/`. Tests live in `tests/` and mirror the backend modules. Runtime data directories are under `data/` and should keep only safe placeholders such as `.gitkeep` in Git. Project planning and module summaries live in `docs/`; use `docs/rag-plan.md` as the source of truth for implementation order. The production frontend is in `app/` using Next.js, shadcn/ui, and Tailwind CSS.

## Build, Test, and Development Commands

- `uv sync`: install Python dependencies.
- `uv run rag-api`: start the FastAPI backend at `http://127.0.0.1:8000`.
- `python -m compileall src tests`: perform a quick Python syntax check.
- `uv run --no-sync pytest`: run the backend test suite.
- `cd app && npm install`: install frontend dependencies.
- `cd app && npm run dev`: start the frontend at `http://127.0.0.1:3000`.
- `cd app && npm run typecheck && npm run lint && npm run build`: validate frontend changes.

## Coding Style & Naming Conventions

Use Python 3.11+ with 4-space indentation, type hints where they clarify behavior, and module names in `snake_case`. Keep FastAPI routes thin and place business logic in service modules. React components use TypeScript, functional components, and file names that match existing conventions such as `rag-workspace.tsx`. Do not change the core stack without explaining the reason, impact, and alternatives first.

## Testing Guidelines

Use `pytest` for backend tests. Name files `test_*.py` and keep tests close to the module behavior they verify. For frontend work, run type checking, linting, and a production build. Add or update tests for document ingestion, vector storage, model configuration, API behavior, and RAG answer flows when those areas change.

## Commit & Pull Request Guidelines

Follow the existing conventional commit style, for example `feat: add model configuration module`, `fix: handle document deletion cleanup`, or `docs: refresh workspace usage guides`. Before committing, run relevant checks and inspect `git status` to ensure only task-related files are included. Pull requests should describe the change, list validation performed, link related issues, and include screenshots for visible frontend updates.

## Agent-Specific Instructions

Before development tasks, read `docs/rag-plan.md` and relevant module summaries in `docs/`. Complete work in small, verifiable steps. When finishing a planned module, add a summary document in `docs/`, commit locally, and push to GitHub. Never force-push without explicit user confirmation.
