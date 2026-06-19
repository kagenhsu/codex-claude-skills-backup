#!/usr/bin/env python3
"""Serve the local console over HTTP and optionally open it in a browser."""

from __future__ import annotations

import argparse
import contextlib
import http.server
import json
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
    quota_guardian_launcher: Path | None = None
    root_dir_name: str | None = None

    def copyfile(self, source, outputfile) -> None:
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _normalized_path(self) -> str:
        path = self.path
        root_name = self.root_dir_name
        if root_name and path.startswith(f"/{root_name}/"):
            path = path[len(root_name) + 1 :]
            if not path.startswith("/"):
                path = "/" + path
        return path

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if length <= 0:
            return None
        try:
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _copy_to_clipboard(self, text: str) -> None:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
            return
        if os.name == "nt":
            subprocess.run(["cmd", "/c", "clip"], input=text, text=True, check=True)
            return
        raise RuntimeError("clipboard_unsupported")

    def _activate_first_available_app(self, candidates: list[str]) -> str:
        errors: list[str] = []
        if sys.platform == "darwin":
            for app_name in candidates:
                try:
                    subprocess.run(["open", "-a", app_name], check=True)
                    return app_name
                except Exception as exc:
                    errors.append(f"{app_name}: {exc}")
            raise RuntimeError("; ".join(errors) or "open_failed")

        raise RuntimeError("activate_unsupported")

    def do_POST(self) -> None:
        path = self._normalized_path()
        if path == "/api/wake-ai":
            payload = self._read_json_body()
            if not isinstance(payload, dict):
                self._send_json(400, {"ok": False, "error": "bad_json"})
                return
            target = payload.get("target")
            prompt = payload.get("prompt")
            if target not in {"codex", "claude"} or not isinstance(prompt, str) or not prompt.strip():
                self._send_json(400, {"ok": False, "error": "bad_payload"})
                return

            candidates = ["Codex"] if target == "codex" else ["Claude", "Visual Studio Code"]
            try:
                self._copy_to_clipboard(prompt)
                opened_app = self._activate_first_available_app(candidates)
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})
                return

            self._send_json(200, {"ok": True, "openedApp": opened_app, "copied": True})
            return

        if path != "/api/open-quota-guardian":
            self._send_json(404, {"ok": False, "error": "not_found"})
            return

        launcher = self.quota_guardian_launcher
        if launcher is None or not launcher.exists():
            self._send_json(404, {"ok": False, "error": "launcher_missing"})
            return

        try:
            subprocess.Popen(
                ["/bin/bash", str(launcher)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(launcher.parent),
            )
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})
            return

        self._send_json(200, {"ok": True})

    def do_GET(self) -> None:
        self.path = self._normalized_path()
        super().do_GET()

    def do_HEAD(self) -> None:
        self.path = self._normalized_path()
        super().do_HEAD()


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
    quota_guardian_launcher = root / "開啟配額守門員.command"
    if not index_path.exists():
        print(f"找不到 index.html：{index_path}", file=sys.stderr)
        return 1

    try:
        port = pick_port(args.host, args.port, args.tries)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    handler_class = QuietConsoleHandler
    handler_class.quota_guardian_launcher = quota_guardian_launcher
    handler_class.root_dir_name = root.name
    handler = lambda *handler_args, **handler_kwargs: handler_class(
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
