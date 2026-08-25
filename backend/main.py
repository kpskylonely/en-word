from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

import uvicorn

from backend.app import create_app
from backend.config import ensure_user_db, static_dir
from backend.paths import is_frozen, resource_root

DEFAULT_PORT = 8765


def run_server(port: int, assets: Path | None) -> None:
    app = create_app(static_dir=assets)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


def main() -> None:
    parser = argparse.ArgumentParser(description="EnWord desktop app")
    parser.add_argument("--dev", action="store_true", help="API only, no desktop window")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    root = resource_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    if is_frozen():
        ensure_user_db()

    assets = static_dir()
    if args.dev:
        run_server(args.port, assets=None)
        return

    if assets is None:
        print("dist/ not found. Run: npm run build", file=sys.stderr)
        sys.exit(1)

    server = threading.Thread(
        target=run_server,
        args=(args.port, assets),
        daemon=True,
    )
    server.start()
    time.sleep(0.5)

    import webview

    from backend.desktop_api import DesktopApi

    desktop_api = DesktopApi()
    use_transparent = sys.platform in ("darwin", "linux")

    window = webview.create_window(
        "离线背单词",
        f"http://127.0.0.1:{args.port}",
        width=960,
        height=680,
        min_size=(800, 560),
        js_api=desktop_api,
        transparent=use_transparent,
        background_color="#01000000" if use_transparent else "#FFF5F7FA",
    )
    desktop_api.bind_window(window)
    webview.start()


if __name__ == "__main__":
    main()
