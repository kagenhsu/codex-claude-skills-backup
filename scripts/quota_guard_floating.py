#!/usr/bin/env python3
"""跨平台的桌面浮動小視窗（配額守門員）。

主要目的是給 Windows 用 — macOS 已經有 quota_guard_floating.swift，
原生 NSPanel 比 Tkinter 漂亮，所以 Mac 預設仍走 swift。

本檔案直接呼叫 quota_guard_snapshot.py，吃同一份 JSON，
顯示規則與 swift 版對齊：
  alert_stage: prepare → 黃 / handoff → 橘 / reserve → 紅 /
               unavailable → 灰 / 其他（normal）→ 綠
  本輪 / 本週 兩條 progress bar，旁邊掛重置時間文字。
  「複製交接提示詞」按鈕，提示詞文字與 swift 版完全一致。

設計選擇：
  - 用 Tkinter 是因為 Windows 內建 Python 標準 + 不需要額外裝套件。
  - 不做 mini 模式（swift 版有）。Windows 使用者多半用滑鼠拖到角落即可。
  - 不做自動 resize；用一個固定夠寬的視窗 + 內容靠左對齊。
  - 一律 always-on-top，但允許使用者拖移。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_SCRIPT = ROOT / "scripts" / "quota_guard_snapshot.py"
REFRESH_INTERVAL_MS = 30_000  # 30 秒刷一次，跟 swift 版一致

ALERT_COLOR = {
    "prepare": "#F4C430",       # 黃
    "handoff": "#FF8C42",       # 橘
    "reserve": "#E63946",       # 紅
    "unavailable": "#8E8E93",   # 灰
}
DEFAULT_COLOR = "#34C759"       # 綠（normal）

BACKGROUND = "#1E1E22"
CARD_BG = "#2A2A30"
TEXT_PRIMARY = "#F2F2F7"
TEXT_SECONDARY = "#A1A1A6"


def python_bin() -> str:
    return sys.executable or "python3"


def fetch_snapshot() -> dict:
    """呼叫 quota_guard_snapshot.py，拿回 providers/windows 結構。"""
    try:
        popen_kwargs: dict = {
            "capture_output": True,
            "text": True,
            "timeout": 15,
            "cwd": str(ROOT),
        }
        if sys.platform == "win32":
            # python.exe 是主控台子系統執行檔；從沒有主控台的 pythonw GUI 行程呼叫時，
            # Windows 預設會跳出一個黑色主控台視窗再馬上關掉（每 30 秒刷新就閃一次）。
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            [python_bin(), str(SNAPSHOT_SCRIPT)],
            **popen_kwargs,
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip() or "snapshot 失敗", "providers": []}
        return json.loads(result.stdout)
    except FileNotFoundError:
        return {"error": f"找不到 snapshot 腳本：{SNAPSHOT_SCRIPT}", "providers": []}
    except subprocess.TimeoutExpired:
        return {"error": "snapshot 逾時，10 秒內沒結果。", "providers": []}
    except Exception as exc:  # noqa: BLE001 — 顯示用，需要 catch-all
        return {"error": f"snapshot 例外：{exc}", "providers": []}


def unavailable_detail_text(text: str, percent) -> str:
    """跟 swift 版的 unavailableDetailText 行為一致。"""
    if percent is not None:
        return text
    trimmed = (text or "").strip()
    if not trimmed or trimmed == "尚未接上":
        return "等待下次可用時間"
    if trimmed.startswith("等待 Claude 回傳"):
        return trimmed
    if trimmed == "等待下一次互動":
        return "等下次互動後更新可用時間"
    suffix = "（最近一次有效資料）"
    if trimmed.endswith(suffix):
        base = trimmed[: -len(suffix)]
        return f"可於 {base} 後再次使用{suffix}"
    return f"可於 {trimmed} 後再次使用"


def percent_label(percent) -> str:
    if percent is None:
        return "限制休息中"
    try:
        return f"{int(round(float(percent)))}%"
    except (TypeError, ValueError):
        return "—"


def color_for_stage(stage: str) -> str:
    return ALERT_COLOR.get(stage, DEFAULT_COLOR)


def final_handoff_needed(providers: list[dict]) -> bool:
    for p in providers:
        for w in p.get("windows", []) or []:
            if w.get("alert_stage") == "reserve":
                return True
    return False


def next_ai_name(providers: list[dict]) -> str:
    candidates = []
    for p in providers:
        windows = p.get("windows") or []
        if not windows:
            continue
        first = windows[0]
        percent = first.get("remaining_percent")
        if percent is None:
            continue
        try:
            candidates.append((p.get("name", "下一棒 AI"), float(percent)))
        except (TypeError, ValueError):
            continue
    if not candidates:
        return "下一棒 AI"
    candidates.sort(key=lambda item: item[1], reverse=True)
    return candidates[0][0]


def build_handoff_prompt(providers: list[dict]) -> str:
    """提示詞與 swift 版 handoffPrompt() 對齊，方便兩邊複製出來的東西完全相同。"""
    next_ai = next_ai_name(providers)

    status_lines: list[str] = []
    for p in providers:
        name = p.get("name", "未知")
        parts: list[str] = []
        for w in p.get("windows", []) or []:
            title = w.get("title", "")
            text = unavailable_detail_text(w.get("remaining_text", ""), w.get("remaining_percent"))
            parts.append(f"{title} {percent_label(w.get('remaining_percent'))} / {text}")
        status_lines.append(f"- {name}：{'、'.join(parts)}")
    status_block = "\n".join(status_lines)

    if final_handoff_needed(providers):
        return (
            f"⚠️ 最終交接模式 — 上一棒 AI 即將撞限制，立即切換給{next_ai}。\n\n"
            "第一件事（這一棒必做，不能跳過）：\n"
            "執行 skill `/handoff-now`（Claude Code）或同等動作（Codex 請讀 "
            "skills/handoff-now/templates/handoff-now.md 當範本），把當前對話進度寫到專案根目錄 "
            "`.handoff-now.md`。寫完之後再做下面的事。\n\n"
            "目前配額狀態：\n"
            f"{status_block}\n\n"
            "然後請直接輸出交接摘要，格式固定：\n"
            "- 目前做到哪裡\n"
            "- 已完成\n"
            "- 未完成\n"
            "- 下一步\n"
            "- 下次開工提示詞\n"
            "- 風險\n\n"
            "要求：\n"
            "1. 全程使用繁體中文。\n"
            "2. 先寫 `.handoff-now.md`，再回答其他事。\n"
            "3. 這一棒以收尾、保存脈絡、交棒為優先，不再開新功能或新大任務。\n"
            "4. 若需要修改，只做最小必要收尾。\n"
        )

    return (
        f"請切換給{next_ai}繼續動作。先不要重做，先把目前進度整理成可直接接手的交接摘要。\n\n"
        "目前配額狀態：\n"
        f"{status_block}\n\n"
        "交接摘要格式固定：\n"
        "- 目前做到哪裡\n"
        "- 已完成\n"
        "- 未完成\n"
        "- 下一步\n"
        "- 下次開工提示詞\n"
        "- 風險\n\n"
        "要求：\n"
        "1. 全程使用繁體中文。\n"
        "2. 先讀目前專案相關檔案與最新改動，再填上面 6 項。\n"
        "3. 如果上一個 AI 正在限制休息中，這一棒直接接手繼續做。\n"
        "4. 下一步只列最小必要動作，不要再開新大任務。\n"
    )


class WindowRow:
    """單條 progress bar 的視覺與資料更新。"""

    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg=CARD_BG)
        self.title_label = tk.Label(self.frame, text="", bg=CARD_BG, fg=TEXT_PRIMARY,
                                     font=("Microsoft JhengHei UI", 11, "bold"), anchor="w")
        self.title_label.pack(fill="x", padx=12, pady=(8, 2))

        self.bar_bg = tk.Frame(self.frame, bg="#3A3A40", height=10)
        self.bar_bg.pack(fill="x", padx=12)
        self.bar_fill = tk.Frame(self.bar_bg, bg=DEFAULT_COLOR, height=10)
        self.bar_fill.place(relx=0, rely=0, relwidth=0, relheight=1)

        self.detail_label = tk.Label(self.frame, text="", bg=CARD_BG, fg=TEXT_SECONDARY,
                                      font=("Microsoft JhengHei UI", 10), anchor="w", justify="left")
        self.detail_label.pack(fill="x", padx=12, pady=(2, 8))

    def update(self, window_data: dict) -> None:
        title = window_data.get("title", "")
        stage = window_data.get("alert_stage", "unavailable")
        percent = window_data.get("remaining_percent")
        text = unavailable_detail_text(window_data.get("remaining_text", ""), percent)

        self.title_label.configure(text=title)
        color = color_for_stage(stage)
        self.bar_fill.configure(bg=color)

        ratio = 0.0
        if percent is not None:
            try:
                ratio = max(0.0, min(1.0, float(percent) / 100.0))
            except (TypeError, ValueError):
                ratio = 0.0
        self.bar_fill.place_configure(relwidth=ratio)

        detail = f"{percent_label(percent)}  {text}"
        self.detail_label.configure(text=detail)


class ProviderCard:
    """單一 provider（Claude Code / Codex）的卡片區塊。"""

    def __init__(self, parent: tk.Widget, name: str) -> None:
        self.container = tk.Frame(parent, bg=CARD_BG, highlightthickness=0)
        self.container.pack(fill="x", pady=(0, 10))

        self.name_label = tk.Label(self.container, text=name, bg=CARD_BG, fg=TEXT_PRIMARY,
                                    font=("Microsoft JhengHei UI", 13, "bold"), anchor="w")
        self.name_label.pack(fill="x", padx=12, pady=(8, 0))

        self.rows: list[WindowRow] = []
        self.name = name

    def update(self, provider_data: dict) -> None:
        windows = provider_data.get("windows") or []
        # 建好需要的 row（懶建）
        while len(self.rows) < len(windows):
            row = WindowRow(self.container)
            row.frame.pack(fill="x", padx=4)
            self.rows.append(row)
        # 隱藏多餘的 row（資料變少時）
        for idx, row in enumerate(self.rows):
            if idx < len(windows):
                row.frame.pack(fill="x", padx=4)
                row.update(windows[idx])
            else:
                row.frame.pack_forget()


class FloatingApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("配額守門員")
        self.root.configure(bg=BACKGROUND)
        self.root.geometry("420x420+80+80")
        # Windows / Linux 都支援；macOS Tk 8.5 也支援，但 mac 我們走 swift 版。
        self.root.attributes("-topmost", True)
        self.root.minsize(360, 320)

        self.providers_state: list[dict] = []
        self.auto_copied_final = False

        header = tk.Frame(self.root, bg=BACKGROUND)
        header.pack(fill="x", padx=16, pady=(14, 6))

        tk.Label(header, text="Codex Pro × Claude Code", bg=BACKGROUND, fg=TEXT_PRIMARY,
                 font=("Microsoft JhengHei UI", 14, "bold")).pack(side="left")
        self.updated_label = tk.Label(header, text="尚未更新", bg=BACKGROUND, fg=TEXT_SECONDARY,
                                       font=("Microsoft JhengHei UI", 10))
        self.updated_label.pack(side="right")

        body = tk.Frame(self.root, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=16, pady=4)
        self.body = body

        self.cards: dict[str, ProviderCard] = {}

        footer = tk.Frame(self.root, bg=BACKGROUND)
        footer.pack(fill="x", padx=16, pady=(6, 14))

        self.handoff_button = ttk.Button(footer, text="複製切換提示詞", command=self.copy_handoff)
        self.handoff_button.pack(side="right")

        self.refresh_button = ttk.Button(footer, text="立即重新整理", command=self.refresh_now)
        self.refresh_button.pack(side="right", padx=(0, 8))

        # 第一次 render：放空殼提示
        self._set_updated("讀取中…")
        self.root.after(50, self.refresh_now)

    # ---- update flow -----------------------------------------------------

    def refresh_now(self) -> None:
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self) -> None:
        snapshot = fetch_snapshot()
        self.root.after(0, self._apply_snapshot, snapshot)

    def _apply_snapshot(self, snapshot: dict) -> None:
        providers = snapshot.get("providers") or []
        error = snapshot.get("error")
        self.providers_state = providers

        # 卡片：依 provider 名稱對應 / 新增 / 移除
        seen: set[str] = set()
        for p in providers:
            name = p.get("name", "未知")
            seen.add(name)
            card = self.cards.get(name)
            if card is None:
                card = ProviderCard(self.body, name)
                self.cards[name] = card
            card.update(p)
        # 移除 snapshot 沒再出現的卡片
        for name in list(self.cards.keys()):
            if name not in seen:
                self.cards[name].container.destroy()
                del self.cards[name]

        # footer 按鈕文字 / 自動複製最終交接提示詞
        final = final_handoff_needed(providers)
        self.handoff_button.configure(text="複製最終交接提示詞" if final else "複製切換提示詞")
        if final and not self.auto_copied_final:
            self._copy_to_clipboard(build_handoff_prompt(providers))
            self.auto_copied_final = True
            self._set_updated("已自動複製最終交接提示詞")
            self.root.after(1800, lambda: self._set_updated(self._time_string()))
        if not final:
            self.auto_copied_final = False

        if error:
            self._set_updated(f"讀取失敗：{error[:40]}")
        elif not final:
            self._set_updated(self._time_string())

        # 排程下一次
        self.root.after(REFRESH_INTERVAL_MS, self.refresh_now)

    # ---- helpers ---------------------------------------------------------

    def copy_handoff(self) -> None:
        prompt = build_handoff_prompt(self.providers_state)
        self._copy_to_clipboard(prompt)
        final = final_handoff_needed(self.providers_state)
        msg = "已複製最終交接提示詞" if final else "已複製切換提示詞"
        self._set_updated(msg)
        self.root.after(1600, lambda: self._set_updated(self._time_string()))

    def _copy_to_clipboard(self, text: str) -> None:
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            # Tk 本身需要還在跑才能保留 clipboard；on Windows update() 後就 OK。
            self.root.update_idletasks()
        except tk.TclError:
            pass

    def _set_updated(self, text: str) -> None:
        prefix = "更新 " if ":" in text and "讀取" not in text and "複製" not in text else ""
        self.updated_label.configure(text=f"{prefix}{text}")

    def _time_string(self) -> str:
        return time.strftime("%H:%M:%S")

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    if not SNAPSHOT_SCRIPT.exists():
        sys.stderr.write(f"找不到 snapshot 腳本：{SNAPSHOT_SCRIPT}\n")
        return 1
    # Windows 雙擊 pythonw 時不會看到 stderr，但 Tk root 會 show 錯誤訊息。
    try:
        app = FloatingApp()
    except tk.TclError as exc:
        sys.stderr.write(f"Tkinter 初始化失敗：{exc}\n")
        sys.stderr.write("Windows 請執行：python -m tkinter，看是否能跳出測試視窗。\n")
        return 2
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
