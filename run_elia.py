# ============================================================
#  File: run_elia.py
#  Project: SEVEN / Elia bridge
#  Description: Convenience entry point for launching Elia with SEVEN routing.
#  Author(s): Team SEVEN
#  Date: 2025-11-18
# ============================================================
"""Launch the Elia TUI configured to use the SEVEN routing backend."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ELIA_APP_DIR = REPO_ROOT / "apps" / "elia"


def _bootstrap_paths() -> None:
    """Ensure both the Elia app and SEVEN package are importable."""
    for path in (ELIA_APP_DIR, REPO_ROOT):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _ensure_database_exists() -> None:
    """Create the database if it doesn't exist."""
    from elia_chat.database.database import create_database, sqlite_file_name
    # Import models to ensure they're registered with SQLModel metadata
    import elia_chat.database.models  # noqa: F401

    if not sqlite_file_name.exists():
        print(f"Creating database at {sqlite_file_name}")
        asyncio.run(create_database())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Elia chat UI.")
    parser.add_argument(
        "-p",
        "--prompt",
        default="",
        help="Optional prompt to pre-populate when Elia opens.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _bootstrap_paths()
    _ensure_database_exists()

    from elia_chat.app import Elia
    from elia_chat.config import LaunchConfig

    config = LaunchConfig.get_current()
    app = Elia(config=config, startup_prompt=args.prompt)
    app.run()


if __name__ == "__main__":
    main()
