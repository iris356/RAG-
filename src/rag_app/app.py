"""Minimal Streamlit entrypoint for the RAG knowledge app."""

from __future__ import annotations

import streamlit as st

from rag_app.core.config import get_settings
from rag_app.core.logging import configure_logging
from rag_app.core.paths import ensure_data_directories


def main() -> None:
    """Render the initial application shell."""

    settings = get_settings()
    configure_logging(settings.log_level)
    directories = ensure_data_directories(settings.data_dir)

    st.set_page_config(page_title=settings.app_name, page_icon=":books:", layout="wide")
    st.title(settings.app_name)
    st.caption("Python + LangChain RAG knowledge base foundation")

    st.subheader("Data directories")
    st.write(f"Data root: `{directories.root}`")

    st.table(
        [
            {"Name": "Raw files", "Path": str(directories.raw)},
            {"Name": "Chroma", "Path": str(directories.chroma)},
            {"Name": "SQLite", "Path": str(directories.sqlite)},
            {"Name": "Temporary files", "Path": str(directories.tmp)},
        ]
    )

    st.subheader("Module status")
    st.success("Module 01: Project foundation is ready.")
    st.info("Next module: model configuration.")


if __name__ == "__main__":
    main()
