"""Command line helpers for launching the Streamlit app."""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run the Streamlit application."""

    app_path = Path(__file__).resolve().with_name("app.py")
    src_path = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(src_path)
        if not existing_pythonpath
        else f"{src_path}{os.pathsep}{existing_pythonpath}"
    )
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    command = [sys.executable, "-m", "streamlit", "run", str(app_path), *sys.argv[1:]]
    return subprocess.call(command, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
