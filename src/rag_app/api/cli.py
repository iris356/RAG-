"""Command line entrypoint for the FastAPI server."""

from __future__ import annotations

import uvicorn


def main() -> int:
    """Run the HTTP API for the RAG application."""

    uvicorn.run(
        "rag_app.api.main:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
