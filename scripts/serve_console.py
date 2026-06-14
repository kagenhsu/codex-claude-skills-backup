#!/usr/bin/env python3
"""Serve the local console over HTTP and optionally open it in a browser."""

from __future__ import annotations

import argparse
import contextlib
import http.server
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def pick_port(host: str, start: int, tries: int) -> int:
    for port in range(start, start + tries):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"找不到可用連接埠（從 {start} 起試了 {tries} 個）。")


class QuietConsoleHandler(http.server.SimpleHTTPRequestHandler):
    def copyfile(self, source, outputfile) -> None:
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            pass


def open_browser_url(url: str) -> bool:
    methods: list[list[str]] = []
    if sys.platform == "darwin":
        methods.append(["open", url])
    elif os.name == "nt":
        methods.append(["cmd", "/c", "start", "", url])
    else:
        methods.append(["xdg-open", url])

    for cmd in methods:
        try:
            subprocess.Popen(cmd)
            return True
        except OSError:
            continue

    try:
        return webbrowser.open(url)
    except webbrowser.Error:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the Codex console locally.")
    parser.add_argument("--root", default=".", help="Console root directory")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Preferred port")
    parser.add_argument("--tries", type=int, default=20, help="How many ports to try")
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the console URL in the default browser",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    index_path = root / "index.html"
    if not index_path.exists():
        print(f"找不到 index.html：{index_path}", file=sys.stderr)
        return 1

    try:
        port = pick_port(args.host, args.port, args.tries)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    handler = lambda *handler_args, **handler_kwargs: QuietConsoleHandler(
        *handler_args,
        directory=str(root),
        **handler_kwargs,
    )
    server = http.server.ThreadingHTTPServer((args.host, port), handler)
    url = f"http://{args.host}:{port}/index.html"

    print("本地控制台已啟動。")
    print(f"請打開：{url}")
    print("按 Ctrl+C 可停止伺服器。")

    if args.open_browser:
        # Give the OS a brief moment to see the listening socket before opening the tab.
        time.sleep(0.15)
        opened = open_browser_url(url)
        if opened:
            print("已嘗試自動打開瀏覽器。")
        else:
            print("無法自動打開瀏覽器，請手動複製上面的網址。")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止本地控制台。")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
