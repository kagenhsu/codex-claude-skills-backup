#!/usr/bin/env python3
"""Minimal desktop app for Codex / Claude Code quota reminders."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from quota_guard import (
    RuntimeSnapshot,
    load_runtime_snapshot,
    notify_user,
    overall_level,
    save_state,
    write_handoff,
)


LEVEL_LABELS = {
    "ok": "安全",
    "warn": "快休息",
    "handoff": "該換手",
    "critical": "立刻換手",
    "unknown": "資料不足",
}

LEVEL_COLORS = {
    "ok": "#168a55",
    "warn": "#a66a00",
    "handoff": "#c26a00",
    "critical": "#c23b3b",
    "unknown": "#657085",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Desktop quota guard app")
    parser.add_argument(
        "--config",
        default="quota_guard.example.json",
        help="Path to config JSON. Default: quota_guard.example.json",
    )
    return parser.parse_args()


class QuotaGuardApp:
    def __init__(self, root: tk.Tk, config_path: Path) -> None:
        self.root = root
        self.config_path = config_path
        self.snapshot: RuntimeSnapshot | None = None
        self.last_overall_level: str | None = None

        self.root.title("Quota Guard")
        self.root.geometry("680x420")
        self.root.minsize(640, 360)

        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)

        header = ttk.Frame(frame)
        header.pack(fill="x", pady=(0, 12))

        title = ttk.Label(header, text="Codex / Claude Code 配額守門員", font=("Arial", 16, "bold"))
        title.pack(side="left")

        self.status_badge = tk.Label(
            header,
            text="讀取中",
            fg="white",
            bg=LEVEL_COLORS["unknown"],
            padx=12,
            pady=6,
        )
        self.status_badge.pack(side="right")

        self.providers_frame = ttk.Frame(frame)
        self.providers_frame.pack(fill="x", pady=(0, 12))

        self.provider_cards: dict[str, dict[str, tk.Widget]] = {}

        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=(0, 12))
        ttk.Button(actions, text="立即重新整理", command=self.refresh).pack(side="left")
        ttk.Button(actions, text="產生交接摘要", command=self.generate_handoff).pack(side="left", padx=8)
        ttk.Button(actions, text="打開交接檔", command=self.open_handoff).pack(side="left")
        ttk.Button(actions, text="打開設定檔", command=self.open_config).pack(side="left", padx=8)

        self.summary = tk.Text(frame, height=12, wrap="word")
        self.summary.pack(fill="both", expand=True)
        self.summary.configure(state="disabled")

        self.refresh()

    def render_provider_card(self, provider_name: str) -> dict[str, tk.Widget]:
        card = ttk.LabelFrame(self.providers_frame, text=provider_name.upper(), padding=12)
        card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        usage = ttk.Label(card, text="使用率：讀取中", font=("Arial", 12, "bold"))
        usage.pack(anchor="w", pady=(0, 6))
        reset = ttk.Label(card, text="Reset：讀取中")
        reset.pack(anchor="w", pady=(0, 4))
        detail = ttk.Label(card, text="來源：", foreground="#657085")
        detail.pack(anchor="w", pady=(0, 4))
        source = ttk.Label(card, text="檔案：", foreground="#657085")
        source.pack(anchor="w", pady=(0, 4))
        level = ttk.Label(card, text="狀態：讀取中")
        level.pack(anchor="w")

        return {"usage": usage, "reset": reset, "detail": detail, "source": source, "level": level}

    def notify_level_change(self, overall: str) -> None:
        if overall == self.last_overall_level:
            return
        self.last_overall_level = overall
        if overall in {"handoff", "critical"}:
            notify_user("Quota Guard", "限制接近上限，請先整理進度並準備換手。")
            messagebox.showwarning("Quota Guard", "限制接近上限，請先整理進度並準備換手。")
        elif overall == "warn":
            notify_user("Quota Guard", "使用量已偏高，建議先不要開新大任務。")
            messagebox.showinfo("Quota Guard", "使用量已偏高，建議先不要開新大任務。")

    def refresh(self) -> None:
        try:
            self.snapshot = load_runtime_snapshot(self.config_path)
        except Exception as exc:
            messagebox.showerror("Quota Guard", f"讀取設定或狀態失敗：\n{exc}")
            return

        snapshot = self.snapshot
        overall = overall_level(snapshot.levels)
        self.status_badge.configure(text=LEVEL_LABELS[overall], bg=LEVEL_COLORS[overall])

        for item in snapshot.statuses:
            card = self.provider_cards.get(item.name)
            if not card:
                card = self.render_provider_card(item.name)
                self.provider_cards[item.name] = card
            usage = "unknown" if item.usage_percent is None else f"{item.usage_percent:.0f}%"
            card["usage"].configure(text=f"使用率：{usage}")
            card["reset"].configure(text=f"Reset：{item.reset_at}")
            detail_text = item.detail or "無補充說明"
            card["detail"].configure(text=f"來源說明：{detail_text}")
            card["source"].configure(text=f"檔案：{item.source_path}")
            card["level"].configure(text=f"狀態：{LEVEL_LABELS[snapshot.levels[item.name]]}")

        lines = [
            f"目前總體狀態：{LEVEL_LABELS[overall]}",
            "",
            "提醒規則：",
            f"- {snapshot.thresholds['warn']}%：快休息",
            f"- {snapshot.thresholds['handoff']}%：該換手",
            f"- {snapshot.thresholds['critical']}%：立刻換手",
            "",
            "說明：",
            "- 這個 app 只負責提醒與輸出交接摘要，不會自動 commit / push。",
            "- 會先自動找本機可用來源，找不到就直接顯示尚未接上。",
            "- Claude 建議接 cctokmon statusline 類資料來源。",
            "- Codex 目前以自訂 JSON 狀態檔為主；若只有全域設定檔，先顯示資料不足，不亂報數字。",
            "- macOS 會用系統通知；Windows 會用視窗提示。",
        ]
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", "\n".join(lines))
        self.summary.configure(state="disabled")

        self.notify_level_change(overall)
        self.root.after(60000, self.refresh)

    def generate_handoff(self) -> None:
        if not self.snapshot:
            return
        write_handoff(self.snapshot)
        save_state(self.snapshot.state_file, self.snapshot.current_state)
        messagebox.showinfo("Quota Guard", f"已產生交接摘要：\n{self.snapshot.handoff_file}")

    def open_handoff(self) -> None:
        if not self.snapshot:
            return
        path = self.snapshot.handoff_file
        if not path.exists():
            self.generate_handoff()
        self._open_path(path)

    def open_config(self) -> None:
        self._open_path(self.config_path)

    def _open_path(self, path: Path) -> None:
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            elif sys.platform.startswith("win"):
                subprocess.Popen(["cmd", "/c", "start", "", str(path)], shell=True)
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Quota Guard", f"無法打開檔案：\n{exc}")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    root = tk.Tk()
    app = QuotaGuardApp(root, config_path)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
