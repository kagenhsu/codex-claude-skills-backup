#!/usr/bin/env python3
"""Local quota watcher for Claude Code / Codex handoff reminders.

This script is intentionally small and local-first:
- Claude Code can read cctokmon statusline output directly.
- Codex can read a generic JSON status file exported by another watcher.
- When thresholds are crossed, the script writes a fixed-format handoff summary.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_PROVIDER_CANDIDATES: dict[str, list[tuple[str, str]]] = {
    "claude": [
        ("claude_statusline", "~/.claude/cctokmon-state.json"),
        ("claude_statusline", "~/.claude/stats-cache.json"),
    ],
    "codex": [
        ("generic", "~/.codex/quota-status.json"),
    ],
}


@dataclass
class ProviderStatus:
    name: str
    usage_percent: float | None
    reset_at: str
    status: str
    source_path: str
    detail: str = ""


@dataclass
class RuntimeSnapshot:
    workspace_root: Path
    thresholds: dict[str, Any]
    state_file: Path
    handoff_file: Path
    statuses: list[ProviderStatus]
    levels: dict[str, str]
    current_state: dict[str, Any]
    previous_state: dict[str, Any]


def notify_user(title: str, message: str) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.Popen(
                [
                    "osascript",
                    "-e",
                    f'display notification "{message}" with title "{title}"',
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        if sys.platform.startswith("win"):
            script = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                f'[System.Windows.Forms.MessageBox]::Show("{message}", "{title}") | Out-Null'
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
    except Exception:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quota guard for Codex / Claude Code")
    parser.add_argument(
        "--config",
        default="quota_guard.example.json",
        help="Path to config JSON. Default: quota_guard.example.json",
    )
    parser.add_argument("--once", action="store_true", help="Run one check and exit")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expand(path_str: str, base: Path) -> Path:
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def parse_claude_statusline(path: Path) -> ProviderStatus:
    data = load_json(path)
    rate_limits = data.get("rate_limits") or {}
    five_hour = rate_limits.get("five_hour") or {}
    seven_day = rate_limits.get("seven_day") or {}
    percentages = [
        value
        for value in (
            five_hour.get("used_percentage"),
            seven_day.get("used_percentage"),
        )
        if isinstance(value, (int, float))
    ]
    usage = max(percentages) if percentages else None
    resets = [
        value
        for value in (
            five_hour.get("resets_at"),
            seven_day.get("resets_at"),
        )
        if value is not None
    ]
    reset_at = str(min(resets)) if resets else "unknown"
    detail = []
    if isinstance(five_hour.get("used_percentage"), (int, float)):
        detail.append(f"5h={five_hour['used_percentage']:.0f}%")
    if isinstance(seven_day.get("used_percentage"), (int, float)):
        detail.append(f"7d={seven_day['used_percentage']:.0f}%")
    return ProviderStatus(
        name="claude",
        usage_percent=usage,
        reset_at=reset_at,
        status="ok" if usage is not None else "partial",
        source_path=str(path),
        detail=" ".join(detail) or "已接上 Claude quota 來源",
    )


def parse_generic(path: Path, provider_name: str) -> ProviderStatus:
    data = load_json(path)
    usage = data.get("usage_percent")
    if isinstance(usage, str):
        try:
            usage = float(usage)
        except ValueError:
            usage = None
    if not isinstance(usage, (int, float)):
        usage = None
    return ProviderStatus(
        name=provider_name,
        usage_percent=float(usage) if usage is not None else None,
        reset_at=str(data.get("reset_at", "unknown")),
        status=str(data.get("status", "partial")),
        source_path=str(path),
        detail=str(data.get("detail", "")) or "已接上自訂 quota 來源",
    )


def detect_provider_source(
    name: str, provider_cfg: dict[str, Any], base: Path
) -> tuple[Path | None, str, str]:
    raw_path = str(provider_cfg.get("path", "auto"))
    raw_format = str(provider_cfg.get("format", "auto"))
    if raw_path != "auto":
        path = expand(raw_path, base)
        return path, raw_format if raw_format != "auto" else "generic", ""

    for fmt, candidate in DEFAULT_PROVIDER_CANDIDATES.get(name, []):
        path = expand(candidate, base)
        if path.exists():
            return path, fmt, f"自動偵測到 {path.name}"

    if name == "claude":
        settings_path = expand("~/.claude/settings.json", base)
        if settings_path.exists():
            return (
                settings_path,
                "unavailable",
                "已找到 Claude 設定，但尚未接上 quota 狀態檔；建議接 cctokmon 類輸出",
            )

    if name == "codex":
        global_state_path = expand("~/.codex/.codex-global-state.json", base)
        if global_state_path.exists():
            return (
                global_state_path,
                "unavailable",
                "已找到 Codex 全域狀態檔，但目前沒有穩定 quota 欄位可直接讀取",
            )

    return None, "missing", "尚未找到可用的 quota 狀態來源"


def read_provider(name: str, provider_cfg: dict[str, Any], base: Path) -> ProviderStatus:
    path, fmt, note = detect_provider_source(name, provider_cfg, base)
    if path is None:
        return ProviderStatus(name, None, "unknown", "missing", "not-found", note)
    if fmt == "missing":
        return ProviderStatus(name, None, "unknown", "missing", str(path), note)
    if fmt == "unavailable":
        return ProviderStatus(name, None, "unknown", "needs-setup", str(path), note)
    if not path.exists():
        return ProviderStatus(name, None, "unknown", "missing", str(path), note)
    if fmt == "claude_statusline":
        status = parse_claude_statusline(path)
    else:
        status = parse_generic(path, name)
    if note:
        status.detail = f"{note}；{status.detail}".strip("；")
    return status


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_json(path)


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def classify_level(usage: float | None, thresholds: dict[str, Any]) -> str:
    if usage is None:
        return "unknown"
    if usage >= thresholds["critical"]:
        return "critical"
    if usage >= thresholds["handoff"]:
        return "handoff"
    if usage >= thresholds["warn"]:
        return "warn"
    return "ok"


def run_git_status(workspace_root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=workspace_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ["git status unavailable"]
    return output.splitlines() if output else ["工作目錄乾淨"]


def read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def build_handoff(workspace_root: Path, statuses: list[ProviderStatus]) -> str:
    dual_state = read_optional(workspace_root / "DUAL-AI-STATE.md")
    next_task = read_optional(workspace_root / "NEXT-AI-TASK.md")
    git_status = run_git_status(workspace_root)
    provider_lines = []
    for item in statuses:
        usage = "unknown" if item.usage_percent is None else f"{item.usage_percent:.0f}%"
        suffix = f" detail={item.detail}" if item.detail else ""
        provider_lines.append(
            f"- {item.name}: usage={usage} reset={item.reset_at} status={item.status}{suffix} source={item.source_path}"
        )

    return "\n".join(
        [
            "- 目前做到哪裡",
            dual_state or "尚未找到 DUAL-AI-STATE.md，請人工補一句目前階段。",
            "- 已完成",
            "已完成限制時間檢查，並整理目前 provider 狀態。",
            "- 未完成",
            "\n".join(git_status),
            "- 下一步",
            "先停止大改，確認是否要換手、存檔或等 reset。",
            "- 下次開工提示詞",
            "請先讀取目前工作目錄、DUAL-AI-STATE.md、NEXT-AI-TASK.md 與 git status，"
            "用最小範圍接續，不要重做已完成部分。",
            "- 風險",
            "\n".join(provider_lines),
            next_task or "尚未找到 NEXT-AI-TASK.md。",
        ]
    )


def load_runtime_snapshot(config_path: Path) -> RuntimeSnapshot:
    config = load_json(config_path)
    base = config_path.parent.resolve()
    workspace_root = expand(config.get("workspace_root", "."), base)
    thresholds = config["thresholds"]
    output_cfg = config["output"]
    state_file = expand(output_cfg["state_file"], workspace_root)
    handoff_file = expand(output_cfg["handoff_file"], workspace_root)

    statuses = [
        read_provider(name, provider_cfg, base)
        for name, provider_cfg in config["providers"].items()
    ]
    levels = {item.name: classify_level(item.usage_percent, thresholds) for item in statuses}
    current = {
        item.name: {
            "usage_percent": item.usage_percent,
            "level": levels[item.name],
            "reset_at": item.reset_at,
            "status": item.status,
        }
        for item in statuses
    }

    previous = load_state(state_file)
    return RuntimeSnapshot(
        workspace_root=workspace_root,
        thresholds=thresholds,
        state_file=state_file,
        handoff_file=handoff_file,
        statuses=statuses,
        levels=levels,
        current_state=current,
        previous_state=previous,
    )


def write_handoff(snapshot: RuntimeSnapshot) -> str:
    handoff = build_handoff(snapshot.workspace_root, snapshot.statuses)
    snapshot.handoff_file.write_text(handoff + "\n", encoding="utf-8")
    return handoff


def overall_level(levels: dict[str, str]) -> str:
    order = ["unknown", "ok", "warn", "handoff", "critical"]
    max_index = 0
    for level in levels.values():
        if level in order:
            max_index = max(max_index, order.index(level))
    return order[max_index]


def build_alert_message(snapshot: RuntimeSnapshot) -> str:
    parts = []
    for item in snapshot.statuses:
        level = snapshot.levels[item.name]
        if level not in {"warn", "handoff", "critical"}:
            continue
        usage = "unknown" if item.usage_percent is None else f"{item.usage_percent:.0f}%"
        parts.append(f"{item.name}={usage} ({level})")
    return "；".join(parts) or "限制接近上限，請先整理進度。"


def check_once(config_path: Path) -> int:
    snapshot = load_runtime_snapshot(config_path)
    previous_overall = overall_level(
        {name: item.get("level", "unknown") for name, item in snapshot.previous_state.items()}
    )
    current_overall = overall_level(snapshot.levels)
    should_write_handoff = any(
        snapshot.levels[item.name] in {"handoff", "critical"}
        and snapshot.previous_state.get(item.name, {}).get("level") != snapshot.levels[item.name]
        for item in snapshot.statuses
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] quota-guard")
    for item in snapshot.statuses:
        usage = "unknown" if item.usage_percent is None else f"{item.usage_percent:.0f}%"
        print(
            f"  {item.name}: usage={usage} level={snapshot.levels[item.name]} "
            f"reset={item.reset_at} status={item.status}"
        )

    if should_write_handoff:
        write_handoff(snapshot)
        print(f"  wrote handoff: {snapshot.handoff_file}")

    if current_overall != previous_overall and current_overall in {"warn", "handoff", "critical"}:
        notify_user("Quota Guard", build_alert_message(snapshot))

    save_state(snapshot.state_file, snapshot.current_state)
    return 0


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    if args.once:
        return check_once(config_path)

    config = load_json(config_path)
    poll_seconds = int(config.get("poll_seconds", 60))
    while True:
        check_once(config_path)
        time.sleep(poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
