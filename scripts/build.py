#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the offline Skill console from YAML data."""

import html as html_mod
import json
import re
from base64 import b64encode
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
skills = yaml.safe_load((ROOT / "data" / "skills.yaml").read_text(encoding="utf-8")) or []
prompts = yaml.safe_load((ROOT / "data" / "prompts.yaml").read_text(encoding="utf-8")) or []
combos = yaml.safe_load((ROOT / "data" / "combos.yaml").read_text(encoding="utf-8")) or []


def validate_combos() -> None:
    prompt_titles = [item.get("title") for item in prompts if item.get("title")]
    prompt_title_set = set(prompt_titles)
    duplicate_titles = sorted({title for title in prompt_titles if prompt_titles.count(title) > 1})
    missing_refs: list[str] = []

    for combo in combos:
        combo_title = combo.get("title", "未命名組合包")
        for step in combo.get("steps") or []:
            prompt_title = step.get("prompt_title")
            if not prompt_title:
                missing_refs.append(f"{combo_title}: 有 step 缺少 prompt_title")
            elif prompt_title not in prompt_title_set:
                missing_refs.append(f"{combo_title}: 找不到 prompt_title「{prompt_title}」")

    if duplicate_titles or missing_refs:
        lines = ["combos 引用檢查失敗："]
        if duplicate_titles:
            lines.append("重複的 prompt title：")
            lines.extend(f"- {title}" for title in duplicate_titles)
        if missing_refs:
            lines.append("缺少或錯誤的 combos 引用：")
            lines.extend(f"- {item}" for item in missing_refs)
        raise SystemExit("\n".join(lines))


validate_combos()

data_json = json.dumps({"skills": skills, "prompts": prompts, "combos": combos}, ensure_ascii=False).replace("</", "<\\/")


def asset_data_url(*parts: str) -> str:
    path = ROOT.joinpath(*parts)
    suffix = path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".gif": "image/gif",
    }.get(suffix, "application/octet-stream")
    encoded = b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


install_guide_assets_json = json.dumps(
    {
        "codexPluginsOverview": asset_data_url("assets", "install-guide", "codex-plugins-overview.png"),
        "codexPluginsExtra": asset_data_url("assets", "install-guide", "codex-plugins-extra.png"),
        "vscodeInstalled1": asset_data_url("assets", "install-guide", "vscode-installed-1.png"),
        "vscodeInstalled2": asset_data_url("assets", "install-guide", "vscode-installed-2.png"),
        "iconDocuments": asset_data_url("assets", "install-guide", "icon-documents.png"),
        "iconSpreadsheets": asset_data_url("assets", "install-guide", "icon-spreadsheets.png"),
        "iconPresentations": asset_data_url("assets", "install-guide", "icon-presentations.png"),
        "iconBrowser": asset_data_url("assets", "install-guide", "icon-browser.png"),
        "iconGithub": asset_data_url("assets", "install-guide", "icon-github.png"),
        "iconFigma": asset_data_url("assets", "install-guide", "icon-figma.png"),
        "iconSupabase": asset_data_url("assets", "install-guide", "icon-supabase.png"),
        "iconCanva": asset_data_url("assets", "install-guide", "icon-canva.png"),
    },
    ensure_ascii=False,
).replace("</", "<\\/")


def markdown_to_cards(path: Path, fallback_title: str, fallback_text: str) -> str:
    if not path.exists():
        return (
            '<div class="sop"><div class="card"><h2>'
            + html_mod.escape(fallback_title)
            + '</h2><div class="summary">'
            + html_mod.escape(fallback_text)
            + "</div></div></div>"
        )

    lines_out: list[str] = []
    in_list = False
    in_table = False
    table_row_count = 0

    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if "|" in raw and raw.startswith("|") and raw.endswith("|"):
            cells = [html_mod.escape(cell.strip()) for cell in raw.strip("|").split("|")]
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            if in_list:
                lines_out.append("</ul>")
                in_list = False
            if not in_table:
                lines_out.append("<table><tbody>")
                in_table = True
                table_row_count = 0
            tag = "th" if table_row_count == 0 else "td"
            row = "".join(f"<{tag}>{cell}</{tag}>" for cell in cells)
            lines_out.append(f"<tr>{row}</tr>")
            table_row_count += 1
            continue

        if in_table:
            lines_out.append("</tbody></table>")
            in_table = False

        text = html_mod.escape(raw)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

        if text.startswith("- ") or text.startswith("* "):
            if not in_list:
                lines_out.append("<ul>")
                in_list = True
            lines_out.append("<li>" + text[2:] + "</li>")
            continue

        if in_list:
            lines_out.append("</ul>")
            in_list = False

        if text.startswith("&gt; "):
            lines_out.append('<div class="summary"><i>' + text[5:] + "</i></div>")
        elif text.startswith("### "):
            lines_out.append("<h3>" + text[4:] + "</h3>")
        elif text.startswith("## "):
            lines_out.append('</div><div class="card"><h2>' + text[3:] + "</h2>")
        elif text.startswith("# "):
            lines_out.append("<h2>" + text[2:] + "</h2>")
        elif text:
            lines_out.append('<div class="summary">' + text + "</div>")

    if in_table:
        lines_out.append("</tbody></table>")
    if in_list:
        lines_out.append("</ul>")
    return '<div class="sop"><div class="card">' + "\n".join(lines_out) + "</div></div>"


workflow_json = json.dumps(
    markdown_to_cards(ROOT / "docs" / "dual-ai-workflow.md", "二刀流工作流", "尚未設定。"),
    ensure_ascii=False,
).replace("</", "<\\/")
guide_json = json.dumps(
    markdown_to_cards(ROOT / "docs" / "ai-role-guide.md", "AI 角色導覽", "尚未設定。"),
    ensure_ascii=False,
).replace("</", "<\\/")
state_path = ROOT / "DUAL-AI-STATE.md"
next_path = ROOT / "NEXT-AI-TASK.md"
agents_path = ROOT / "AGENTS.md"
prd_path = ROOT / "PRD.md"
plan_path = ROOT / "專案規劃表.md"
state_html = json.dumps(
    {
        "raw": state_path.read_text(encoding="utf-8") if state_path.exists() else "",
        "html": markdown_to_cards(state_path, "DUAL-AI-STATE", "尚未設定。"),
    },
    ensure_ascii=False,
).replace("</", "<\\/")
agents_html = json.dumps(
    {
        "raw": agents_path.read_text(encoding="utf-8") if agents_path.exists() else "",
        "html": markdown_to_cards(agents_path, "AGENTS", "尚未設定。"),
    },
    ensure_ascii=False,
).replace("</", "<\\/")
prd_html = json.dumps(
    {
        "raw": prd_path.read_text(encoding="utf-8") if prd_path.exists() else "",
        "html": markdown_to_cards(prd_path, "PRD", "尚未設定。"),
    },
    ensure_ascii=False,
).replace("</", "<\\/")
next_html = json.dumps(
    {
        "raw": next_path.read_text(encoding="utf-8") if next_path.exists() else "",
        "html": markdown_to_cards(next_path, "NEXT-AI-TASK", "尚未設定。"),
    },
    ensure_ascii=False,
).replace("</", "<\\/")
plan_html = json.dumps(
    {
        "raw": plan_path.read_text(encoding="utf-8") if plan_path.exists() else "",
        "html": markdown_to_cards(plan_path, "專案規劃表", "尚未設定。"),
    },
    ensure_ascii=False,
).replace("</", "<\\/")
project_path_json = json.dumps(str(ROOT), ensure_ascii=False).replace("</", "<\\/")
project_url_json = json.dumps(ROOT.as_uri() + "/", ensure_ascii=False).replace("</", "<\\/")


def quota_guardian_status() -> dict:
    launcher = ROOT / "開啟配額守門員.command"
    swift_file = ROOT / "scripts" / "quota_guard_floating.swift"
    snapshot_file = ROOT / "scripts" / "quota_guard_snapshot.py"
    claude_bridge = ROOT / "scripts" / "claude_quota_statusline.sh"
    bridge_installer = ROOT / "scripts" / "install_claude_quota_bridge.py"
    automation_file = Path.home() / ".codex" / "automations" / "codex-pro-claude-code" / "automation.toml"
    claude_settings = Path.home() / ".claude" / "settings.json"
    claude_state = Path.home() / ".claude" / "cctokmon-state.json"
    claude_cache = Path.home() / ".claude" / "cctokmon-cache.json"

    files_ready = all(path.exists() for path in [launcher, swift_file, snapshot_file, claude_bridge, bridge_installer])
    automation_ready = automation_file.exists()
    statusline_ready = False
    bridge_wrapper = Path.home() / ".claude" / "cctokmon-bridge.sh"
    accepted_bridge_paths = (str(claude_bridge), str(bridge_wrapper), claude_bridge.name, bridge_wrapper.name)
    if claude_settings.exists():
        try:
            settings_obj = json.loads(claude_settings.read_text(encoding="utf-8"))
            configured = settings_obj.get("statusLine")
            cmd_str = None
            if isinstance(configured, str):
                cmd_str = configured
            elif isinstance(configured, dict) and configured.get("type") == "command":
                cmd_str = configured.get("command") or ""
            statusline_ready = bool(cmd_str) and any(p in cmd_str for p in accepted_bridge_paths)
        except Exception:
            statusline_ready = False

    installed = files_ready and (automation_ready or statusline_ready)
    claude_live_ready = False
    if claude_state.exists():
        try:
            state_obj = json.loads(claude_state.read_text(encoding="utf-8"))
            if isinstance(state_obj, dict):
                rl = state_obj.get("rate_limits") or {}
                claude_live_ready = bool(rl.get("five_hour") or rl.get("seven_day"))
        except Exception:
            claude_live_ready = False
    claude_cache_ready = claude_cache.exists()
    bridge_pinged = claude_state.exists()
    claude_projects_dir = Path.home() / ".claude" / "projects"
    session_log_ready = False
    if claude_projects_dir.exists():
        try:
            for project_dir in claude_projects_dir.iterdir():
                if project_dir.is_dir() and any(project_dir.glob("*.jsonl")):
                    session_log_ready = True
                    break
        except Exception:
            session_log_ready = False
    if claude_live_ready:
        claude_status_text = "Claude Code 已接上真實 5 小時 / 7 天配額資料。"
    elif claude_cache_ready:
        claude_status_text = "Claude Code 目前顯示最近一次有效 quota 資料；即時資料尚未重新輸出。"
    elif session_log_ready:
        claude_status_text = "已從 session log 取得真實 context 用量（含本對話 token 進度）；5 小時 / 7 天配額平台不主動輸出，下次撞到 429 限制時才會自動補上。"
    elif bridge_pinged:
        claude_status_text = "Claude Code statusline 橋接已成功觸發；但 Claude Code 平時不會主動回傳 5 小時 / 7 天配額，下次撞到 429 限制時才會自動補上實際數字。"
    elif statusline_ready:
        claude_status_text = "Claude Code 橋接已裝好，但 statusline 還沒被觸發；請在 Claude Code 送出一則訊息後，1 分鐘內回來查看。"
    else:
        claude_status_text = "Claude Code quota 橋接尚未完成。"
    install_prompt = "\n".join(
        [
            "請幫我在目前這台電腦把「Codex Pro × Claude Code 配額守門員」安裝好，並直接完成可用版本。",
            "",
            "專案路徑：",
            str(ROOT),
            "",
            "安裝目標：",
            "1. 建立或補齊配額守門員需要的啟動檔、快照腳本、浮動窗程式。",
            "2. 讓首頁控制台可以啟動這個功能。",
            "3. 接上 Codex 與 Claude Code 的 quota / reset 資料來源。",
            "4. Claude Code 若需要 statusline 橋接，請直接幫我安裝到這台電腦。",
            "5. 安裝完成後，請驗證我按下啟動檔就能看到浮動視窗。",
            "",
            "限制：",
            "- 全程使用繁體中文。",
            "- 先檢查目前缺少哪些檔案與設定，再直接補齊，不要只做方案討論。",
            "- 不要刪除既有資料。",
            "- 完成後請回報：改了哪些檔案、怎麼驗證、現在如何開啟。",
        ]
    )
    return {
        "installed": installed,
        "filesReady": files_ready,
        "automationReady": automation_ready,
        "statuslineReady": statusline_ready,
        "claudeLiveReady": claude_live_ready,
        "claudeCacheReady": claude_cache_ready,
        "claudeStatusText": claude_status_text,
        "claudeWakePrompt": "請先直接回覆一句短訊息，並讓目前這個 Claude Code 工作階段刷新 statusline 與最新 quota / reset 資料。如果配額欄位可用，請正常輸出即可。",
        "codexWakePrompt": "請切換給 Codex 接手目前工作。先不要重做，先讀目前專案檔案與最新改動，然後直接進入收尾模式：整理進度、補最小必要修改、避免再開新大任務、必要時產生交接摘要。",
        "launcherName": launcher.name,
        "installPrompt": install_prompt,
    }


quota_guardian_status_json = json.dumps(quota_guardian_status(), ensure_ascii=False).replace("</", "<\\/")

def collect_console_paths(root: Path):
    # 跳過：.git（內檔太多會讓 HTML 肥大；用標記路徑代替）、node_modules、暫存、編譯產物
    skip_dirs = {".git", "node_modules", ".codex-tmp", "__pycache__", ".DS_Store"}
    paths = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        parts = rel.parts
        if any(part in skip_dirs for part in parts):
            continue
        if p.is_file():
            paths.append(root.name + "/" + str(rel).replace("\\", "/"))
    # 若有 .git/ 資料夾（代表已 git init），補一個標記路徑供前端偵測「2.3 初始化 Git」
    if (root / ".git").is_dir():
        paths.append(root.name + "/.git/HEAD")
    paths.sort()
    return paths

console_file_paths_json = json.dumps(collect_console_paths(ROOT), ensure_ascii=False).replace("</", "<\\/")

BACKUP_PROMPTS = {
    "backupUnified": """請協助我把這台電腦上的 Codex / Claude Code 個人化設定、skills、提示詞與資料，一次自動備份到我自己的 GitHub 私人倉庫。請自動判斷我的作業系統（macOS 或 Windows），使用對應的指令語法，整個流程請一次自動完成。

請依下列順序執行：

1) 偵測作業系統
   - macOS / Linux：使用 zsh / bash，路徑用 ~/，同步用 rsync。
   - Windows：使用 PowerShell，路徑用 $env:USERPROFILE，同步用 robocopy。

2) 安裝必要工具（沒有就裝；裝完用 --version 驗證）
   - macOS：用 Homebrew 安裝 git、gh。沒裝 Homebrew 就先帶我裝 Homebrew。
   - Windows：用 winget 安裝 Git.Git、GitHub.cli。沒裝 winget 就帶我從 Microsoft Store 取得 App Installer。

3) 登入 GitHub（如果沒帳號 → 帶我註冊）
   - 跑 `gh auth status`。
   - 沒登入：開瀏覽器到 https://github.com/signup 帶我建立帳號（已有就跳過），再跑 `gh auth login`，選 GitHub.com → HTTPS → Login with a web browser，照畫面完成驗證。
   - 登入完成後，記住我的 GitHub 帳號名稱供後續步驟使用。

4) 準備備份倉庫
   - 預設倉庫名：my-codex-claude-backup，預設為 **Private（私有）**，避免個人提示詞、設定外流。
   - 先 `gh repo view <我的帳號>/my-codex-claude-backup` 檢查是否存在。
   - 不存在就 `gh repo create <我的帳號>/my-codex-claude-backup --private --description "Codex / Claude Code 個人備份"`。

5) 蒐集要備份的資料夾
   - Codex 設定：macOS `~/.codex/` / Windows `$env:USERPROFILE\\.codex\\`
   - Claude Code 設定：macOS `~/.claude/` / Windows `$env:USERPROFILE\\.claude\\`
   - 控制台客製化資料（若存在）：包含這個專案 / codex-claude-skills-backup 內的 data/、skills/
   - **排除清單**（必須做到，避免外洩）：
     .credentials.json、*.log、*.tmp、projects/、todos/、shell-snapshots/、statsig/、__pycache__、node_modules

6) 建立 / 更新本機備份工作目錄
   - macOS：`~/Documents/codex-claude-backup-work/`
   - Windows：`$env:USERPROFILE\\Documents\\codex-claude-backup-work\\`
   - 第一次：`gh repo clone <我的帳號>/my-codex-claude-backup <備份工作目錄>`；之後改成 `git -C <備份工作目錄> pull`。
   - macOS：用 `rsync -a --delete --exclude` 把資料同步到工作目錄下的 `backup/`，保留相對結構。
   - Windows：用 `robocopy /MIR /XD ... /XF ...` 做相同效果。

7) 自動產出 RESTORE.md
   - 紀錄：備份時間、來源電腦名稱、原始絕對路徑對照表、排除了哪些檔案、還原時要還回的位置。

8) 提交與推送
   - `git -C <備份工作目錄> add -A`
   - commit message 用繁體中文：`backup: 同步 <YYYY-MM-DD HH:MM> 的 Codex / Claude 設定`
   - `git push`

9) 回報結果
   - 倉庫 HTTPS 網址（之後還原會用到）
   - 備份了哪些資料夾、各自佔多少容量
   - 是否成功、有沒有跳過的檔案、敏感檔案是否確實排除
   - 下次想還原時，到新電腦複製控制台「從 GitHub 還原」的提示詞即可

安全要求：每一步驟前先用一句話告訴我你要做什麼，並把實際指令逐行顯示出來；遇到不確定或要覆蓋的事先停下來問我，不要強行繼續。""",

    "restoreUnified": """請協助我把 GitHub 上的 Codex / Claude Code 個人備份還原到「這台電腦」。請自動判斷作業系統（macOS 或 Windows），使用對應指令，整個流程一次自動完成。

請依下列順序執行：

1) 確認備份倉庫
   - 預設嘗試我自己的私人 repo：<我的 GitHub 帳號>/my-codex-claude-backup。
   - 如果還不知道我的帳號，請問我 GitHub 使用者名稱或完整 repo 網址。

2) 偵測作業系統
   - macOS / Linux：用 zsh / bash、~/、rsync。
   - Windows：用 PowerShell、$env:USERPROFILE、robocopy。

3) 安裝必要工具（沒有就裝；裝完用 --version 驗證）
   - macOS：Homebrew → git、gh。沒 brew 就先帶我裝 Homebrew。
   - Windows：winget → Git.Git、GitHub.cli。

4) 登入 GitHub
   - 跑 `gh auth status`；沒登入就 `gh auth login`（GitHub.com → HTTPS → Login with a web browser）。

5) 取回備份倉庫
   - clone 到：
     macOS：`~/Documents/codex-claude-backup-work/`
     Windows：`$env:USERPROFILE\\Documents\\codex-claude-backup-work\\`
   - 如果該資料夾已存在，改跑 `git -C <路徑> pull` 取得最新版本。
   - 確認裡面有 `backup/` 與 `RESTORE.md`，把 RESTORE.md 顯示給我看，確認這是要還原的版本。

6) 預演還原（先不覆蓋）
   - 列出將要還原的檔案數、目標路徑，並指出哪些既有檔案會被覆蓋。
   - 如果本機已有 `.codex` 或 `.claude`，先做一份時間戳備份：
     macOS：`~/.codex.bak-<YYYYMMDD-HHMM>/`、`~/.claude.bak-<YYYYMMDD-HHMM>/`
     Windows：`$env:USERPROFILE\\.codex.bak-<yyyyMMdd-HHmm>\\`、`$env:USERPROFILE\\.claude.bak-<yyyyMMdd-HHmm>\\`
   - 把預演結果顯示給我，等我確認「可以還原」再進下一步。

7) 正式還原
   - 把 `backup/` 下的內容還回原始路徑：
     `backup/.codex/` → `~/.codex/`（或 Windows 對應路徑）
     `backup/.claude/` → `~/.claude/`（同上）
     控制台客製化資料 → 依 `RESTORE.md` 還回對應位置。
   - macOS 用 `rsync -a`；Windows 用 `robocopy /E`。
   - **絕對不要**還回 .credentials.json、*.log 等敏感／暫存檔（備份內應該本來就沒有，但再確認一次）。

8) 後置處理
   - macOS：對 ~/.claude、~/.codex 跑 `chmod -R u+rwX`，必要時用 `xattr -dr com.apple.quarantine` 解除隔離。
   - Windows：確認資料夾權限正常，必要時 `icacls` 修正。

9) 回報結果
   - 還原了哪些資料夾與檔案數
   - 哪些既有檔案被先打包備份、備份到哪
   - 我下一步該做什麼（例如重新開 Codex / Claude Code 測試）
   - 如果有失敗或衝突，列出來讓我決定

安全要求：每一步驟前先用一句話說明你要做什麼，並把實際指令逐行顯示出來；覆蓋既有檔案前一定要先做時間戳備份；遇到不確定的事先停下來問我，不要強行繼續。""",

    "backupMac": """請幫我在這台 macOS 電腦把 Codex / Claude Code 個人化設定、skills、提示詞，一次自動備份到我自己的 GitHub 私人倉庫。整個流程請一次自動完成。

步驟：
1) 用 Homebrew 安裝 git、gh（沒裝 brew 先帶我裝 Homebrew）。
2) 跑 `gh auth status`；沒登入就開 https://github.com/signup 帶我註冊（已有就跳過），再 `gh auth login` 用瀏覽器完成驗證。
3) 預設倉庫 `my-codex-claude-backup`（私有）。不存在就 `gh repo create <我的帳號>/my-codex-claude-backup --private --description "Codex / Claude Code 個人備份"`。
4) 把這些路徑同步到 `~/Documents/codex-claude-backup-work/backup/`（第一次先 `gh repo clone` 拉空 repo 下來；之後 `git -C <路徑> pull`）：
   - `~/.codex/`
   - `~/.claude/`（排除 projects/、todos/、shell-snapshots/、statsig/、.credentials.json、*.log、*.tmp）
   - 控制台客製化的 `data/`、`skills/`（若存在）
   - 用 `rsync -a --delete --exclude` 同步。
5) 自動寫一份 `RESTORE.md` 記錄這份備份的來源路徑與時間。
6) `git add -A` → `git commit -m "backup: 同步 <YYYY-MM-DD HH:MM> 的 Codex / Claude 設定"` → `git push`。
7) 回報：倉庫網址、備份了什麼、容量、是否成功、有沒有跳過的檔案，並提醒我下次到新電腦用「從 GitHub 還原」的提示詞還原即可。

每一步驟前先說明你要做什麼，並顯示指令；遇到不確定的事先停下來問我。""",

    "backupWin": """請幫我在這台 Windows 電腦（用 PowerShell）把 Codex / Claude Code 個人化設定、skills、提示詞，一次自動備份到我自己的 GitHub 私人倉庫。整個流程請一次自動完成。

步驟：
1) 用 winget 安裝 `Git.Git` 與 `GitHub.cli`，安裝後重新打開 PowerShell。
2) 跑 `gh auth status`；沒登入就開 https://github.com/signup 帶我註冊（已有就跳過），再 `gh auth login` 用瀏覽器完成驗證。
3) 預設倉庫 `my-codex-claude-backup`（私有）。不存在就 `gh repo create <我的帳號>/my-codex-claude-backup --private --description "Codex / Claude Code 個人備份"`。
4) 把這些路徑同步到 `$env:USERPROFILE\\Documents\\codex-claude-backup-work\\backup\\`（第一次先 `gh repo clone` 拉空 repo 下來；之後 `git -C <路徑> pull`）：
   - `$env:USERPROFILE\\.codex\\`
   - `$env:USERPROFILE\\.claude\\`（用 robocopy 排除 projects、todos、shell-snapshots、statsig、.credentials.json、*.log、*.tmp）
   - 控制台客製化的 `data\\`、`skills\\`（若存在）
   - 同步用 `robocopy <來源> <目的> /MIR /XD projects todos shell-snapshots statsig /XF .credentials.json *.log *.tmp`。
5) 自動寫一份 `RESTORE.md` 記錄這份備份的來源路徑與時間。
6) `git add -A` → `git commit -m "backup: 同步 <yyyy-MM-dd HH:mm> 的 Codex / Claude 設定"` → `git push`。
7) 回報：倉庫網址、備份了什麼、容量、是否成功、有沒有跳過的檔案，並提醒我下次到新電腦用「從 GitHub 還原」的提示詞還原即可。

每一步驟前先說明你要做什麼，並顯示指令；遇到不確定的事先停下來問我。""",

    "restoreMac": """請幫我在這台 macOS 電腦把我 GitHub 上的 Codex / Claude Code 備份還原回來。

步驟：
1) 用 Homebrew 裝 git、gh（沒 brew 先帶我裝 Homebrew）。
2) 跑 `gh auth status`；沒登入就 `gh auth login` 用瀏覽器完成驗證。
3) 預設 repo `<我的帳號>/my-codex-claude-backup`，不知道帳號就問我。
4) clone 到 `~/Documents/codex-claude-backup-work/`（已存在就 `git pull`），把 RESTORE.md 顯示給我確認。
5) 預演還原：列出會覆蓋哪些檔案；如果 `~/.codex`、`~/.claude` 已存在，先打包成 `~/.codex.bak-<時間戳>/`、`~/.claude.bak-<時間戳>/` 備份，等我確認再下一步。
6) 用 `rsync -a` 把 `backup/.codex/` → `~/.codex/`，`backup/.claude/` → `~/.claude/`，控制台客製化資料依 RESTORE.md 還回對應位置。
7) `chmod -R u+rwX ~/.codex ~/.claude`，必要時 `xattr -dr com.apple.quarantine`。
8) 回報：還原了什麼、檔案數、既有檔案備份到哪，提醒我重新開 Codex / Claude Code 測試。

安全要求：每一步驟前先說明你要做什麼，並顯示指令；覆蓋前一定要先做時間戳備份；遇到不確定的事先停下來問我。""",

    "restoreWin": """請幫我在這台 Windows 電腦（用 PowerShell）把我 GitHub 上的 Codex / Claude Code 備份還原回來。

步驟：
1) 用 winget 裝 `Git.Git` 與 `GitHub.cli`，安裝後重開 PowerShell。
2) 跑 `gh auth status`；沒登入就 `gh auth login` 用瀏覽器完成驗證。
3) 預設 repo `<我的帳號>/my-codex-claude-backup`，不知道帳號就問我。
4) clone 到 `$env:USERPROFILE\\Documents\\codex-claude-backup-work\\`（已存在就 `git pull`），把 RESTORE.md 顯示給我確認。
5) 預演還原：列出會覆蓋哪些檔案；如果 `$env:USERPROFILE\\.codex\\`、`$env:USERPROFILE\\.claude\\` 已存在，先複製成 `.codex.bak-<時間戳>\\`、`.claude.bak-<時間戳>\\` 備份，等我確認再下一步。
6) 用 `robocopy <來源> <目的> /E` 把 `backup\\.codex\\` → `$env:USERPROFILE\\.codex\\`，`backup\\.claude\\` → `$env:USERPROFILE\\.claude\\`，控制台客製化資料依 RESTORE.md 還回對應位置。
7) 必要時用 `icacls` 修正資料夾權限。
8) 回報：還原了什麼、檔案數、既有檔案備份到哪，提醒我重新開 Codex / Claude Code 測試。

安全要求：每一步驟前先說明你要做什麼，並顯示指令；覆蓋前一定要先做時間戳備份；遇到不確定的事先停下來問我。""",
}

backup_prompts_json = json.dumps(BACKUP_PROMPTS, ensure_ascii=False).replace("</", "<\\/")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>新手 AI 外掛控制台｜Codex Pro × Claude Code 入門系統</title>
<style>
  :root{--bg:#f4f6fb; --panel:#eef1f8; --card:#ffffff; --border:#d9e0ef; --text:#1f2937; --muted:#657085; --accent:#3b6fe0; --accent-soft:#e8eefc; --green:#168a55; --amber:#a66a00; --red:#c23b3b; --shadow:0 1px 3px rgba(30,40,80,.07);}
  *{box-sizing:border-box; margin:0; padding:0;}
  body{background:var(--bg); color:var(--text); font-family:"PingFang TC","Microsoft JhengHei","Noto Sans TC",sans-serif; line-height:1.55;}
  header{position:sticky; top:0; z-index:50; background:rgba(244,246,251,.92); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px); padding:12px 24px 0; border-bottom:1px solid var(--border); box-shadow:0 4px 16px rgba(30,40,80,.05);}
  .head-inner{max-width:1120px; margin:0 auto;}
  h1{font-size:1.05rem; display:flex; align-items:center; gap:10px; margin-bottom:8px;}
  h1 .sub{font-size:.78rem; color:var(--muted); font-weight:normal;}
  .tabs{display:flex; gap:8px; flex-wrap:wrap;}
  .tab{padding:8px 14px; border-radius:10px 10px 0 0; background:transparent; border:none; color:var(--muted); font-size:.92rem; cursor:pointer; border-bottom:2px solid transparent;}
  .tab.active{color:var(--text); border-bottom-color:var(--accent); background:var(--panel);}
  main{max-width:1120px; margin:0 auto; padding:14px 24px 60px;}
  .search{margin:0 0 12px; position:relative;}
  .search input{width:100%; padding:11px 16px 11px 40px; border-radius:10px; border:1px solid var(--border); background:var(--card); color:var(--text); font-size:.96rem; outline:none;}
  .search input:focus{border-color:var(--accent); box-shadow:0 0 0 3px rgba(59,111,224,.12);}
  .search .icon{position:absolute; left:14px; top:50%; transform:translateY(-50%); color:var(--muted);}
  .page-intro{background:var(--card); border:1px solid var(--border); border-radius:10px; padding:16px; margin-bottom:14px; box-shadow:var(--shadow);}
  .launch-tip{background:linear-gradient(135deg,#fff7e8,#eef4ff); border:1px solid #e6d3a3; border-radius:10px; padding:12px 14px; margin-bottom:14px; box-shadow:var(--shadow);}
  .launch-tip b{display:block; margin-bottom:4px;}
  .home-hero{background:linear-gradient(135deg,#f7fbff,#eef2ff 58%,#fff8ec); border:1px solid var(--border); border-radius:16px; padding:18px; margin-bottom:16px; box-shadow:var(--shadow);}
  .home-hero h2{font-size:1.35rem; margin-bottom:8px;}
  .home-hero p{font-size:.94rem; color:var(--text); margin-bottom:12px;}
  .home-actions{display:flex; gap:10px; flex-wrap:wrap; margin-top:12px;}
  .home-actions .copy-btn{width:auto; flex:1 1 150px; padding:8px 10px; font-size:.84rem;}
  .home-kpis{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:14px;}
  .home-kpi{background:rgba(255,255,255,.82); border:1px solid var(--border); border-radius:12px; padding:12px;}
  .home-kpi b{display:block; font-size:1rem; margin-bottom:4px;}
  .guardian-kpis{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:12px;}
  .home-steps{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-bottom:16px;}
  .home-step{background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; box-shadow:var(--shadow);}
  .home-step .num{display:inline-flex; width:28px; height:28px; align-items:center; justify-content:center; border-radius:999px; background:var(--accent); color:#fff; font-weight:700; margin-bottom:8px;}
  .home-step h3{font-size:1rem; margin-bottom:6px;}
  .home-split{display:grid; grid-template-columns:1.15fr .85fr; gap:14px; align-items:stretch;}
  .home-stack{display:flex; flex-direction:column; gap:14px;}
  .home-panel{background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; box-shadow:var(--shadow);}
  .home-panel h3{font-size:1rem; margin-bottom:8px;}
  .home-panel-actions{display:grid; grid-template-columns:repeat(auto-fit,minmax(142px,1fr)); gap:8px; margin-top:12px;}
  .home-panel-actions .copy-btn{font-size:.78rem; padding:8px 10px;}
  .guardian-actions{grid-template-columns:minmax(0,208px); justify-content:center;}
  .guardian-actions .guardian-launch-btn{width:208px; justify-self:center;}
  .home-panel-actions .primary-copy{grid-column:1/-1; width:min(320px,100%); justify-self:center; background:linear-gradient(135deg,#1f4fbf,#3b6fe0); box-shadow:0 8px 18px rgba(59,111,224,.22); font-weight:700;}
  .home-panel-actions .primary-copy:hover{background:linear-gradient(135deg,#183f9b,#2f5cc4);}
  .home-copy-hint{margin-top:12px; background:#fff7d6; border:1px solid #ead48b; color:#6f5208; border-radius:8px; padding:8px 10px; font-size:.84rem; font-weight:600;}
  .role-grid{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px;}
  .role-card{background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:12px;}
  .role-card h4{font-size:.96rem; margin-bottom:6px;}
  .mini-list{display:flex; flex-direction:column; gap:8px;}
  .mini-item{background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:10px 12px;}
  .mini-item b{display:block; font-size:.88rem; margin-bottom:3px;}
  .page-intro h2{font-size:1.12rem; margin-bottom:6px;}
  .lead{font-size:.92rem; color:var(--text); margin-bottom:10px;}
  .intro-grid,.workflow-guide{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px;}
  .intro-item,.guide-item{background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:10px 12px;}
  .intro-label,.guide-label{font-size:.92rem; font-weight:800; color:#2a3b5f; margin-bottom:6px; line-height:1.35;}
  .intro-text,.guide-text{font-size:.84rem; color:var(--text);}
  .chips,.flow-switch{display:flex; gap:8px; flex-wrap:wrap; margin:12px 0 14px;}
  .chip,.flow-btn{padding:6px 13px; border-radius:999px; border:1px solid var(--border); background:var(--card); color:var(--muted); font-size:.84rem; cursor:pointer;}
  .chip.active,.flow-btn.active{background:var(--accent); border-color:var(--accent); color:#fff;}
  .count{color:var(--muted); font-size:.83rem; margin-bottom:10px;}
  .grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:14px;}
  .card{background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px; display:flex; flex-direction:column; gap:8px; box-shadow:var(--shadow);}
  .card h3{font-size:.98rem; display:flex; align-items:center; gap:8px; flex-wrap:wrap;}
  .badge,.cat-tag,.stage-tag{font-size:.7rem; padding:2px 8px; border-radius:999px; font-weight:600;}
  .badge.low{background:rgba(31,157,99,.12); color:var(--green);}
  .badge.mid{background:rgba(185,127,16,.12); color:var(--amber);}
  .badge.high{background:rgba(208,69,69,.12); color:var(--red);}
  .cat-tag{color:var(--muted); border:1px solid var(--border); font-weight:500;}
  .stage-tag{background:var(--accent-soft); color:#244fae;}
  .summary{font-size:.87rem; color:var(--text);}
  .notes{font-size:.8rem; color:var(--amber);}
  .usage{font-size:.8rem; color:var(--muted);}
  .trigger{display:flex; align-items:center; gap:8px; background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:8px 10px;}
  .trigger code{flex:1; font-size:.8rem; color:#2c4a9e; font-family:inherit; word-break:break-all;}
  .copy-btn{width:100%; border:none; border-radius:8px; background:var(--accent); color:#fff; padding:7px 12px; font-size:.82rem; cursor:pointer; transition:background .15s; text-decoration:none; text-align:center;}
  .trigger .copy-btn{width:auto; flex-shrink:0;}
  .copy-btn:hover{background:#2f5cc4;}
  .copy-btn.done{background:var(--green);}
  pre.prompt-body{background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:10px 12px; font-size:.8rem; color:#33405e; white-space:pre-wrap; font-family:inherit; max-height:170px; overflow:auto;}
  .flow-section{margin-top:18px;}
  .section-head{display:flex; align-items:baseline; justify-content:space-between; gap:12px; margin:0 0 10px; padding-bottom:6px; border-bottom:1px solid var(--border);}
  .section-head h2{font-size:1rem;}
  .section-head .hint{font-size:.8rem; color:var(--muted);}
  .sop{max-width:780px; display:flex; flex-direction:column; gap:16px;}
  .progress-sop,.wide-sop{max-width:none; width:100%;}
  .wide-sop>.card{width:100%; box-sizing:border-box;}
  .sop .card{gap:10px;}
  .sop h2{font-size:1.06rem;}
  .sop h3{font-size:.94rem; margin-top:6px;}
  .sop ol,.sop ul{padding-left:1.4em; font-size:.9rem;}
  .sop li{margin:4px 0;}
  .sop table{width:100%; border-collapse:collapse; font-size:.88rem; border:1px solid var(--border); border-radius:8px; overflow:hidden;}
  .sop th,.sop td{border:1px solid var(--border); padding:8px 10px; vertical-align:top; text-align:left;}
  .sop th{background:var(--panel); font-weight:700;}
  .sop code{background:var(--panel); border:1px solid var(--border); border-radius:6px; padding:1px 5px;}
  .form-grid{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px;}
  .field{display:flex; flex-direction:column; gap:5px;}
  .field.full{grid-column:1/-1;}
  .field label{font-size:.78rem; color:var(--muted);}
  .field .help{font-size:.74rem; color:var(--muted);}
  .field input,.field select,.field textarea{width:100%; border:1px solid var(--border); border-radius:8px; background:#fff; color:var(--text); padding:9px 10px; font:inherit; font-size:.88rem;}
  .field input.needs-input{border-color:var(--accent); box-shadow:0 0 0 3px rgba(47,111,237,.12);}
  .field textarea{min-height:120px; resize:vertical;}
  .capture-switch{display:flex; gap:8px; flex-wrap:wrap;}
  .capture-btn{padding:7px 13px; border-radius:999px; border:1px solid var(--border); background:var(--card); color:var(--muted); cursor:pointer;}
  .capture-btn.active{background:var(--accent); border-color:var(--accent); color:#fff;}
  .capture-link{display:grid; grid-template-columns:1fr auto 1fr auto; align-items:center; gap:12px; background:linear-gradient(90deg,rgba(47,111,237,.12),rgba(46,164,79,.10)); border:1px dashed rgba(47,111,237,.45); border-radius:14px; padding:12px;}
  .capture-step{display:flex; align-items:flex-start; gap:9px;}
  .capture-step span{display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:999px; background:var(--accent); color:#fff; font-weight:700; font-size:.78rem; flex-shrink:0;}
  .capture-step b{display:block; font-size:.9rem; margin-bottom:2px;}
  .capture-step small{display:block; color:var(--muted); font-size:.76rem; line-height:1.35;}
  .capture-arrow{color:var(--accent); font-weight:800; font-size:1.1rem;}
  .capture-status{justify-self:end; background:#fff; border:1px solid var(--border); color:var(--muted); border-radius:999px; padding:6px 10px; font-size:.78rem; white-space:nowrap;}
  .checkline{display:flex; align-items:flex-start; gap:8px; font-size:.85rem; color:var(--text);}
  .checkline input{margin-top:3px;}
  .warning{font-size:.8rem; color:var(--amber); background:rgba(185,127,16,.09); border:1px solid rgba(185,127,16,.2); border-radius:8px; padding:8px 10px;}
  .copy-btn:disabled{background:#aab4c8; cursor:not-allowed;}
  .state-board{margin-bottom:16px;}
  .state-board textarea{width:100%; min-height:130px; border:1px solid var(--border); border-radius:8px; padding:10px 12px; font:inherit; font-size:.86rem; resize:vertical;}
  .state-summary{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:10px;}
  .state-item{background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:10px;}
  .state-item.full{grid-column:1/-1;}
  .state-label{font-size:.74rem; color:var(--muted); margin-bottom:3px;}
  .state-value{font-size:.85rem; white-space:pre-wrap;}
  .state-stage-active{outline:2px solid var(--accent); background:var(--accent-soft);}
  .combo-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; margin-bottom:16px;}
  .combo-card{background:var(--card); border:1px solid var(--border); border-radius:10px; padding:12px; display:flex; flex-direction:column; gap:8px; box-shadow:var(--shadow);}
  .combo-steps{font-size:.78rem; color:var(--muted); padding-left:1.2em;}
  .daily-hero{background:linear-gradient(135deg,#fff8e8,#eaf4ff 58%,#eef8ef); border:1px solid rgba(185,127,16,.22); border-radius:18px; padding:20px; box-shadow:var(--shadow);}
  .daily-hero h2{font-size:1.55rem; margin-bottom:8px;}
  .daily-hero p{color:var(--muted); max-width:820px; line-height:1.75;}
  .daily-principles{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:14px;}
  .daily-principle{background:rgba(255,255,255,.72); border:1px solid rgba(47,111,237,.15); border-radius:14px; padding:12px;}
  .daily-section{margin-top:16px;}
  .daily-section-head{display:flex; justify-content:space-between; align-items:flex-end; gap:12px; margin-bottom:10px;}
  .daily-section-head h3{font-size:1.1rem;}
  .daily-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px;}
  .daily-card{background:var(--card); border:1px solid var(--border); border-radius:14px; padding:14px; box-shadow:var(--shadow); display:flex; flex-direction:column; gap:10px;}
  .daily-card h4{font-size:1rem;}
  .daily-card-actions{display:grid; gap:8px; margin-top:auto;}
  .copy-btn.secondary-btn{background:#eef2ff; color:#24438f;}
  .copy-btn.secondary-btn:hover{background:#dde7ff;}
  .daily-safety{background:rgba(46,164,79,.1); border:1px solid rgba(46,164,79,.22); border-radius:12px; padding:10px; color:#17612d; font-size:.84rem; line-height:1.6;}
  .daily-modal{position:fixed; inset:0; z-index:60; display:flex; align-items:center; justify-content:center; padding:18px;}
  .daily-modal-backdrop{position:absolute; inset:0; background:rgba(15,23,42,.45);}
  .daily-modal-card{position:relative; width:min(760px,100%); max-height:min(88vh,920px); overflow:auto; background:#fff; border-radius:18px; border:1px solid rgba(148,163,184,.35); box-shadow:0 28px 80px rgba(15,23,42,.24); padding:18px;}
  .daily-modal-head{display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:12px;}
  .daily-modal-close{border:none; background:#eef2f7; color:#334155; border-radius:999px; padding:8px 12px; cursor:pointer; font-size:.82rem;}
  .daily-modal-step{font-size:.78rem; color:var(--muted);}
  .daily-modal-title{font-size:1.1rem; margin-top:4px;}
  .daily-modal-body{display:grid; gap:12px;}
  .daily-modal-question{border:1px solid var(--border); border-radius:14px; padding:14px; background:#fcfdff;}
  .daily-modal-question h4{font-size:1rem; margin-bottom:6px;}
  .daily-choice-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; margin-top:10px;}
  .daily-choice-btn{border:1px solid #cbd5e1; background:#fff; color:#1e293b; border-radius:10px; padding:10px 12px; text-align:left; cursor:pointer; font-size:.84rem; line-height:1.45;}
  .daily-choice-btn.active{border-color:#2f6fed; background:#edf4ff; color:#1d4ed8;}
  .daily-modal-input,.daily-modal-textarea{width:100%; border:1px solid #cbd5e1; border-radius:10px; padding:10px 12px; font:inherit; margin-top:10px; background:#fff;}
  .daily-modal-textarea{min-height:120px; resize:vertical;}
  .daily-modal-preview{background:#f8fafc; border:1px solid #dbe3ef; border-radius:14px; padding:14px;}
  .daily-modal-actions{display:flex; flex-wrap:wrap; gap:8px; justify-content:space-between; margin-top:4px;}
  .daily-modal-actions .group{display:flex; flex-wrap:wrap; gap:8px;}
  .online-banner{background:linear-gradient(135deg,#eaf3ff,#f3e8ff); border:1px solid #c7d5ee; border-radius:10px; padding:12px 14px; margin-bottom:14px; box-shadow:var(--shadow); display:flex; gap:12px; align-items:flex-start; flex-wrap:wrap;}
  .online-banner b{display:block; margin-bottom:4px;}
  .online-banner .grow{flex:1; min-width:240px;}
  .online-banner a{color:var(--accent); text-decoration:none; border-bottom:1px solid currentColor;}
  .online-banner button{border:none; border-radius:8px; background:var(--accent); color:#fff; padding:8px 14px; font-size:.86rem; cursor:pointer; white-space:nowrap;}
  .online-banner button:hover{background:#2f5cc4;}
  .install-hero{background:linear-gradient(135deg,#f7fbff,#eaf2ff 62%,#fff8ec); border-color:#c6d6ef;}
  .install-hero h2{font-size:1.28rem;}
  .install-hero .privacy-note{background:rgba(255,255,255,.75); border:1px solid rgba(59,111,224,.22); border-radius:10px; padding:10px 12px; color:#214069; font-size:.86rem;}
  .install-grid{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px;}
  .install-card{background:var(--card); border:1px solid var(--border); border-radius:14px; padding:14px; box-shadow:var(--shadow); display:flex; flex-direction:column; gap:10px;}
  .install-card.featured{border-color:#b9cbee; background:linear-gradient(180deg,#ffffff,#f4f8ff);}
  .install-card h3{font-size:1rem;}
  .install-card .install-subtitle{font-size:.82rem; color:var(--muted);}
  .automation-builder{display:grid; grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr); gap:14px; align-items:start;}
  .automation-panel{display:flex; flex-direction:column; gap:12px;}
  .automation-preview{position:sticky; top:86px;}
  .automation-badges{display:flex; gap:8px; flex-wrap:wrap;}
  .automation-badge{font-size:.74rem; padding:3px 9px; border-radius:999px; background:var(--accent-soft); color:#244fae; border:1px solid rgba(59,111,224,.16);}
  .automation-tip{background:#fff7d6; border:1px solid #ead48b; color:#6f5208; border-radius:10px; padding:10px 12px; font-size:.84rem; line-height:1.55;}
  .automation-records{display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px;}
  .automation-record{background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; box-shadow:var(--shadow); display:flex; flex-direction:column; gap:10px;}
  .automation-record-head{display:flex; align-items:flex-start; justify-content:space-between; gap:10px;}
  .automation-record-title{font-size:1rem; font-weight:800; color:#243a63;}
  .automation-meta{display:flex; flex-wrap:wrap; gap:6px;}
  .automation-meta span{font-size:.74rem; padding:2px 8px; border-radius:999px; border:1px solid var(--border); color:var(--muted); background:var(--panel);}
  .automation-kv{display:grid; gap:8px;}
  .automation-kv-item{background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:10px;}
  .automation-kv-item b{display:block; font-size:.78rem; color:#2a3b5f; margin-bottom:4px;}
  .automation-kv-item .summary{font-size:.82rem;}
  .automation-record-actions{display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:8px;}
  .automation-empty{background:linear-gradient(135deg,#f9fbff,#f3f7ff); border:1px dashed #bfd0f2; border-radius:12px; padding:18px; color:var(--muted); text-align:center;}
  .automation-counter{font-size:.8rem; color:var(--muted);}
  .install-steps{counter-reset:step; display:flex; flex-direction:column; gap:7px; margin-top:2px;}
  .install-step{display:flex; gap:8px; align-items:flex-start; font-size:.82rem; color:var(--text);}
  .install-step span{display:inline-flex; align-items:center; justify-content:center; width:20px; height:20px; border-radius:999px; background:var(--accent-soft); color:#244fae; font-weight:700; font-size:.72rem; flex-shrink:0;}
  .install-result-grid{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px;}
  .install-result{background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:12px;}
  .install-result b{display:block; margin-bottom:4px;}
  .tutorial-btn{background:#edf2ff; color:#244fae; border:1px solid #c8d7fb;}
  .tutorial-btn:hover,.tutorial-btn.active{background:var(--accent); color:#fff; border-color:var(--accent);}
  .install-tutorial-card{background:linear-gradient(180deg,#ffffff,#f8fbff); border:1px solid #bfd0f2;}
  .install-tutorial-head{display:flex; justify-content:space-between; align-items:flex-start; gap:14px; flex-wrap:wrap;}
  .install-tutorial-badge{display:inline-flex; align-items:center; gap:6px; padding:5px 10px; border-radius:999px; background:#edf2ff; color:#244fae; font-size:.78rem; font-weight:700;}
  .install-tutorial-grid{display:grid; grid-template-columns:1.15fr .85fr; gap:12px;}
  .install-tutorial-grid.full{grid-template-columns:1fr;}
  .install-tutorial-steps{display:flex; flex-direction:column; gap:10px;}
  .install-tutorial-step{display:flex; gap:10px; padding:10px 12px; background:var(--panel); border:1px solid var(--border); border-radius:10px;}
  .install-tutorial-step span{display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:999px; background:var(--accent); color:#fff; font-size:.78rem; font-weight:700; flex-shrink:0;}
  .install-article{margin-top:12px; display:flex; flex-direction:column; gap:14px;}
  .install-article-section{background:linear-gradient(180deg,#ffffff,#f7faff); border:1px solid #cbd9f5; border-radius:14px; padding:14px;}
  .install-article-section h3{font-size:1rem; margin-bottom:8px;}
  .install-article-section ol{padding-left:1.2em; display:flex; flex-direction:column; gap:8px; color:var(--text);}
  .install-article-section li{line-height:1.7;}
  .install-article-section p{font-size:.86rem; color:var(--text); line-height:1.7;}
  .install-article-note{margin-top:10px; padding:10px 12px; border-radius:10px; background:#edf4ff; border:1px solid #cddcf9; color:#24406d; font-size:.82rem; line-height:1.6;}
  .plugin-mini-section{margin-top:12px; padding:12px; background:linear-gradient(180deg,#f8fbff,#eef4ff); border:1px solid #cbd9f5; border-radius:12px;}
  .plugin-mini-section h3{font-size:.95rem; margin-bottom:4px;}
  .plugin-mini-grid{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:10px;}
  .plugin-mini-card{display:flex; gap:10px; align-items:flex-start; padding:10px; background:rgba(255,255,255,.92); border:1px solid #d8e2f6; border-radius:12px; box-shadow:0 6px 18px rgba(54,88,160,.06);}
  .plugin-mini-icon{display:inline-flex; align-items:center; justify-content:center; width:42px; height:42px; border-radius:12px; font-size:1.2rem; font-weight:700; color:#173b86; background:linear-gradient(180deg,#ffffff,#e7efff); border:1px solid #c7d5f3; flex-shrink:0;}
  .plugin-mini-icon img{width:100%; height:100%; object-fit:contain; border-radius:12px; display:block;}
  .plugin-mini-copy{display:flex; flex-direction:column; gap:3px; min-width:0;}
  .plugin-mini-title{font-size:.86rem; font-weight:700; color:var(--text);}
  .plugin-mini-desc{font-size:.77rem; color:var(--muted); line-height:1.5;}
  .install-manual{margin-top:12px; display:flex; flex-direction:column; gap:12px;}
  .manual-figure{background:linear-gradient(180deg,#ffffff,#f7faff); border:1px solid #cbd9f5; border-radius:14px; padding:12px; box-shadow:0 8px 22px rgba(54,88,160,.06);}
  .manual-figure img{display:block; width:100%; height:auto; border-radius:12px; border:1px solid #dbe3f2; background:#fff;}
  .manual-figure b{display:block; margin-bottom:8px; font-size:.92rem;}
  .manual-caption{margin-top:8px; font-size:.79rem; color:var(--muted); line-height:1.6;}
  .manual-merged{display:flex; flex-direction:column; gap:10px; border-radius:12px; overflow:hidden; background:#fff;}
  .manual-merged img{display:block; width:100%; height:auto; border:1px solid #dbe3f2; border-radius:12px; background:#fff;}
  .install-tutorial-shot{display:flex; flex-direction:column; gap:10px;}
  .shot-frame{background:linear-gradient(160deg,#eff4ff,#ffffff 70%); border:1px solid #cbd9f5; border-radius:14px; padding:14px; min-height:150px; box-shadow:inset 0 1px 0 rgba(255,255,255,.7);}
  .shot-window{border:1px solid #c9d5ee; border-radius:12px; overflow:hidden; background:#fff;}
  .shot-toolbar{display:flex; align-items:center; gap:6px; padding:8px 10px; background:#f2f5fb; border-bottom:1px solid #dbe3f2;}
  .shot-dot{width:8px; height:8px; border-radius:999px; background:#98abcf;}
  .shot-body{padding:12px; display:flex; flex-direction:column; gap:8px;}
  .shot-line{height:10px; border-radius:999px; background:linear-gradient(90deg,#dbe6fb,#eef3ff);}
  .shot-line.short{width:56%;}
  .shot-line.mid{width:74%;}
  .shot-pill-row{display:flex; gap:8px; flex-wrap:wrap;}
  .shot-pill{padding:5px 8px; border-radius:999px; background:#edf2ff; color:#244fae; font-size:.74rem; font-weight:700;}
  .shot-caption{font-size:.79rem; color:var(--muted);}
  .advanced-section{margin-top:4px; border-top:1px dashed var(--border); padding-top:14px;}
  .advanced-grid{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px;}
  .builder-actions{display:flex; gap:10px; flex-wrap:wrap; margin-top:12px;}
  .builder-preview-card{height:100%; min-height:0; display:grid; grid-template-rows:auto 1fr auto; gap:10px;}
  .builder-preview-card pre.prompt-body{max-height:800px; min-height:0; height:100%; overflow:auto;}
  .builder-preview{min-height:0;}
  .builder-status{background:#fff7d6; border:1px solid #ead48b; color:#6f5208; border-radius:8px; padding:8px 10px; font-size:.84rem; margin-top:10px;}
  .doc-accordion{display:flex; flex-direction:column; gap:12px;}
  .doc-fold{background:var(--card); border:1px solid var(--border); border-radius:12px; box-shadow:var(--shadow); overflow:hidden;}
  .doc-fold[open]{border-color:#bfd0f2;}
  .doc-fold summary{list-style:none; cursor:pointer; display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding:14px 16px; background:linear-gradient(180deg,#ffffff,#f7faff);}
  .doc-fold summary::-webkit-details-marker{display:none;}
  .doc-fold summary:hover{background:linear-gradient(180deg,#f8fbff,#eef4ff);}
  .doc-fold-title{display:flex; flex-direction:column; gap:4px;}
  .doc-fold-title b{font-size:1rem;}
  .doc-fold-arrow{color:var(--accent); font-size:1.1rem; line-height:1; flex-shrink:0; padding-top:2px;}
  .doc-fold[open] .doc-fold-arrow{transform:rotate(90deg);}
  .doc-fold-body{padding:0 14px 14px;}
  .doc-fold-body .sop{max-width:none;}
  .skill-capture-fold{margin-top:12px;}
  .lifecycle-features{margin-top:8px; padding-left:1.1em; color:var(--muted); font-size:.78rem; line-height:1.5;}
  .lifecycle-features li{margin:3px 0;}
  .plan-progress-banner{background:linear-gradient(135deg,#eef7ee 0%,#e8efff 100%);border:1px solid #c6e5c9;border-radius:10px;padding:14px 16px;margin:12px 0;}
  .plan-progress-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;}
  .plan-progress-cell{min-width:0;}
  .plan-prog-label{font-size:.75rem;color:#4b5563;margin-bottom:4px;letter-spacing:.02em;}
  .plan-prog-value{font-size:.92rem;font-weight:600;color:#166534;word-break:break-word;line-height:1.4;}
  .plan-prog-next{color:#92400e;}
  .plan-prog-pct{font-weight:500;color:#4b5563;font-size:.85rem;}
  .plan-prog-bar{height:8px;background:#e5e7eb;border-radius:99px;overflow:hidden;margin-top:10px;}
  .plan-prog-bar > span{display:block;height:100%;background:linear-gradient(90deg,#2f63da,#16a34a);transition:width .4s ease;}
  .plan-prog-hint{font-size:.74rem;color:var(--muted);margin-top:6px;}
  .plan-list{display:flex;flex-direction:column;gap:8px;margin-top:6px;}
  .plan-stage{background:var(--panel);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
  .plan-stage[open]{border-color:#2f63da;box-shadow:0 2px 6px rgba(47,99,218,.08);}
  .plan-stage.status-done{border-color:#c6e5c9;}
  .plan-stage.status-current{border-color:#f3d68b;}
  .plan-stage > summary{list-style:none;cursor:pointer;padding:12px 14px;display:flex;align-items:center;gap:10px;background:#f5f7fa;user-select:none;}
  .plan-stage > summary::-webkit-details-marker{display:none;}
  .plan-stage[open] > summary{background:#eef2f8;border-bottom:1px solid var(--border);}
  .plan-stage-badge{font-size:.72rem;padding:2px 9px;border-radius:99px;font-weight:600;flex-shrink:0;}
  .badge-done{background:#dcf2dd;color:#166534;}
  .badge-current{background:#fef3c7;color:#92400e;}
  .badge-todo{background:#e5e7eb;color:#4b5563;}
  .badge-partial{background:#fef3c7;color:#92400e;}
  .badge-ref{background:#e0e7ff;color:#3730a3;}
  .plan-stage-title{flex:1;font-weight:600;color:#2a3b5f;font-size:.92rem;line-height:1.4;}
  .plan-stage-count{font-size:.8rem;color:#4b5563;font-variant-numeric:tabular-nums;font-family:"SF Mono",Menlo,monospace;}
  .plan-stage-caret{color:var(--accent);font-size:.9rem;transition:transform .2s;}
  .plan-stage[open] .plan-stage-caret{transform:rotate(90deg);}
  .plan-stage-body{padding:12px 16px 16px;}
  .plan-stage-desc{font-size:.84rem;color:#4b5563;margin-bottom:8px;line-height:1.55;}
  .plan-step-list{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:4px;}
  .plan-step{display:flex;align-items:flex-start;gap:8px;padding:7px 10px;border-radius:6px;font-size:.84rem;line-height:1.5;border:1px solid transparent;}
  .plan-step.done{background:#eef7ee;color:#166534;}
  .plan-step.done .plan-step-text{text-decoration:line-through;text-decoration-color:rgba(22,101,52,.3);}
  .plan-step.current{background:#fffaf0;border-color:#f3d68b;color:#7c2d12;font-weight:500;}
  .plan-step.todo{background:#fafbfc;color:#4b5563;}
  .plan-step.note{color:var(--muted);font-size:.8rem;}
  .plan-step-mark{min-width:18px;text-align:center;font-weight:700;flex-shrink:0;}
  .plan-step-id{font-family:"SF Mono",Menlo,monospace;font-size:.72rem;background:#fff;border:1px solid var(--border);border-radius:4px;padding:1px 6px;margin-right:2px;flex-shrink:0;color:#4b5563;}
  .plan-step.current .plan-step-id{background:#fef3c7;border-color:#f3d68b;color:#92400e;}
  .plan-step.done .plan-step-id{background:#dcf2dd;border-color:#c6e5c9;color:#166534;}
  .plan-step-text{flex:1;word-break:break-word;}
  @media (max-width:760px){.plan-progress-row{grid-template-columns:1fr;}}
  .empty{color:var(--muted); text-align:center; padding:36px 0;}
  footer{text-align:center; color:var(--muted); font-size:.75rem; padding:20px;}
  @media (max-width:760px){main,header{padding-left:14px; padding-right:14px;} .grid,.intro-grid,.workflow-guide,.state-summary,.form-grid,.capture-link,.home-kpis,.guardian-kpis,.home-steps,.home-split,.role-grid,.daily-principles,.install-grid,.install-result-grid,.advanced-grid,.automation-builder,.automation-records{grid-template-columns:1fr;} .guardian-actions{grid-template-columns:1fr;} .guardian-actions .guardian-launch-btn{width:min(208px,100%);} .capture-arrow{transform:rotate(90deg); justify-self:center;} .capture-status{justify-self:start;} .section-head,.daily-section-head{display:block;} .automation-preview{position:static;} }
</style>
</head>
<body>
<header><div class="head-inner"><h1>新手 AI 外掛控制台 <span class="sub">Codex Pro × Claude Code 入門系統</span></h1><div class="tabs"><button class="tab active" data-tab="guide">新手快速開始</button><button class="tab" data-tab="installGuide">安裝與外掛</button><button class="tab" data-tab="customSkill">個人化設定</button><button class="tab" data-tab="automation">自動化設定</button><button class="tab" data-tab="daily">日常提示詞</button><button class="tab" data-tab="progress">專案開發（雙刀／單刀）</button><button class="tab" data-tab="prompts">提示詞庫</button><button class="tab" data-tab="skills">外掛 / Skill庫</button><button class="tab" data-tab="backup">備份 / 還原</button></div></div></header>
<main><div id="onlineBanner"></div><div id="launchTip"></div><div id="pageIntro" class="page-intro"></div><div id="searchSlot"></div><div class="search"><span class="icon">搜</span><input id="searchBox" type="text" placeholder="搜尋 skill、提示詞、觸發句、角色、分工、導覽，例如：git、翻譯、審查、二刀流"></div><div id="chips" class="chips"></div><div id="countLine" class="count"></div><div id="content"></div></main>
<footer>資料來源：data/skills.yaml + data/prompts.yaml + data/combos.yaml；修改後執行 python3 scripts/build.py 重建</footer>
<script>
const DATA = __DATA_JSON__;
const INSTALL_GUIDE_ASSETS = __INSTALL_GUIDE_ASSETS__;
const WORKFLOW_HTML = __WORKFLOW_HTML__;
const GUIDE_HTML = __GUIDE_HTML__;
// STATE_HTML / NEXT_HTML 為 {raw, html}：raw 餵 parseWorkflowState，html 顯示完整檔案視圖。命名沿用使用者指定。
const STATE_HTML = __STATE_HTML__;
const NEXT_HTML = __NEXT_HTML__;
const AGENTS_HTML = __AGENTS_HTML__;
const PRD_HTML = __PRD_HTML__;
const PLAN_HTML = __PLAN_HTML__;
const CONSOLE_FILE_PATHS = __CONSOLE_FILE_PATHS__;
const PROJECT_PATH = __PROJECT_PATH__;
const PROJECT_URL = __PROJECT_URL__;
const BACKUP_PROMPTS = __BACKUP_PROMPTS_JSON__;
const QUOTA_GUARDIAN_STATUS = __QUOTA_GUARDIAN_STATUS_JSON__;
const TAB_STORAGE_KEY="skill-console-active-tab";
const VALID_TABS=["guide","installGuide","customSkill","automation","daily","progress","prompts","skills","backup"];
function restoreTab(){const stored=localStorage.getItem(TAB_STORAGE_KEY)||"";return VALID_TABS.includes(stored)?stored:"guide"}
let tab = restoreTab(), cat = "全部", q = "", flowMode = "dualai", dailyMode = "全部", captureMode = "prompt", progressMode = "status", selectedProject = null, progressPickerMessage = "", progressNextPromptOpen = false, installGuideTopic = "codex", progressFlow = "dual";
let dailyWizardState = {cardId:"", step:0, answers:{}};
let promptWizardState = {promptKey:"", step:0, answers:{}};
const FLOW_META = {
  dualai:{label:"二刀流協作",title:"二刀流工作流提示詞",lead:"適合重要系統修改：Claude Code（VS Code）是主力工程師，負責規劃、分段實作、測試與修正；Codex 負責審查、修改建議、複審，最後也由 Codex 做存檔收尾（因為 Codex 在終端機顯示『哪裡要改』對新手最直觀）。"},
  solo:{label:"單一 AI 使用",title:"單一 AI 使用提示詞",lead:"同事只有單一 AI 時，也能用這些提示詞讓 AI 先釐清、再分段執行、最後提醒是否需要審查。"},
  common:{label:"通用",title:"通用提示詞",lead:"日常可直接複製使用的提示詞，例如 Skill 安檢、交接、摘要與一般 AI 工作輔助。"}
};
const STAGE_META = {
  dualai:{entry:["入口","啟動或接續二刀流工作流"],"1":["第 1 階段：Claude Code（VS Code）","規劃、拆任務、建立狀態檔"],"2":["第 2 階段：Claude Code（VS Code）","分段實作、build、驗證"],"3":["第 3 階段：Codex","審查＋修改建議，檢查 diff、架構與風險"],"4":["第 4 階段：Claude Code（VS Code）","修正＋開發，逐條處理並重新驗證"],"5":["第 5 階段：Codex","複審＋修改，確認可收尾或補問題"],handoff:["轉交","把目前狀態交給下一方"],status:["狀態檔","讀寫 DUAL-AI-STATE.md"],"context-compact":["上下文壓縮","壓縮後輸出可接續摘要"],archive:["存檔收尾","Codex 在第 5 階段通過後驗證、更新狀態檔與交還 push 決定權"]},
  solo:{entry:["入口","只用一個 AI 時先用這張說明工作方式"],"1":["第 1 步","釐清任務與目標"],"2":["第 2 步","提出方案、先不修改"],"3":["第 3 步","分段執行並自我檢查"],"4":["第 4 步","收尾、整理驗證與 commit 建議"]}
};
const FLOW_ORDER = {dualai:["entry","1","2","3","4","5","handoff","status","context-compact","archive"],solo:["entry","1","2","3","4"]};
const DAILY_COMMON_QUESTIONS = [
  {id:"goal_mode",label:"你這次主要想做什麼？",type:"choice",options:["先整理想法","直接產生可複製提示詞","先規劃再做","先比對 / 分析","我不確定，請幫我判斷"]},
  {id:"input_mode",label:"你手上的資料大概是哪一種？",type:"choice",options:["只有一個模糊想法","一段文字 / 筆記","網址 / 文章 / 文件","錯誤訊息 / 問題描述","已有完整需求","其他"]},
  {id:"audience_mode",label:"這段提示詞主要要幫誰使用？",type:"choice",options:["我自己","主管 / 老闆","客戶 / 外部對象","工程師 / 設計師 / 同事","一般大眾 / 粉絲","我不確定"]},
  {id:"reply_mode",label:"你希望 AI 怎麼回？",type:"choice",options:["最短可執行版","條列重點版","先問我再做","一步一步教學版","專業完整版本"]},
  {id:"risk_mode",label:"你希望 AI 先怎麼處理風險？",type:"choice",options:["先講風險，不直接動手","可以直接先產出草稿","先做最小版本","不確定，請 AI 自己判斷"]},
  {id:"extra_notes",label:"還有沒有要補充的情境或限制？",type:"textarea",placeholder:"選填，例如：先不要改檔、不要出現太多術語、要用繁體中文。"}
];
const DAILY_PROMPT_SECTIONS = [
  {title:"開發系統",hint:"寫程式、修 bug、讀專案時先用這區。",cards:[
    {title:"雙 AI 討論新專案方向",when:"只有一個模糊想法，想先聊成可規劃的新專案或新系統時。",prompt:`我有一個新專案或新系統想法，請先陪我討論與規劃，不要直接寫程式、不要直接改檔案。

初步想法：
【在這裡貼上你的想法，可以很模糊】

請採用「雙 AI 角色討論」方式協助我：
1. Claude Code（VS Code）角色：主力工程師，負責把想法拆成系統、功能、資料、流程與可執行任務。
2. Codex 角色：審查員／挑戰者，負責追問需求盲點、技術風險、邊界情況、成本與維護問題；最後也由 Codex 做存檔收尾。
3. 使用者角色：最終決策者，你要用簡單問題引導我做選擇，不要一次問太多。

互動流程：
1. 先用 5 句話重述你理解的想法。
2. 分別用 Claude Code 視角與 Codex 視角，各提出最重要的觀察。
3. 先問我最多 5 個關鍵問題，問題要好回答，必要時提供選項。
4. 根據我的回答，整理出：目標使用者、核心痛點、第一版功能、暫時不做的事、風險。
5. 最後產出一份新手看得懂的專案規劃草案。
6. 如果適合進入二刀流開發，最後再給我兩段可複製提示詞：
   - 給 Claude Code（VS Code）的「建立 AGENTS.md / PRD.md 並規劃第一版」提示詞。
   - 給 Codex 的「審查專案規劃」提示詞。

限制：
- 不要假裝已經知道我的需求；不清楚就問。
- 不要一開始就建檔或寫程式。
- 不要把第一版做太大，請優先找最小可行版本。
- 如果我只有一個 AI，也請你先在同一個回答中模擬 Claude Code 與 Codex 兩種視角。`},
    {title:"請先讀懂這個專案",when:"接手舊專案，或第一次打開一個專案時。",prompt:`請先讀懂這個專案，但先不要修改任何檔案。

請依序幫我做：
1. 先讀 README、AGENTS、PRD、目錄結構與重要設定檔。
2. 用新手能懂的方式說明這個專案是做什麼。
3. 列出最重要的資料夾與檔案，各自負責什麼。
4. 判斷如果我要開始開發，第一步應該看哪裡。
5. 如果資訊不足，請列出你還需要我補充什麼。

限制：
- 先不要修改任何檔案。
- 先不要執行破壞性指令。
- 不確定的地方請明講，不要自己猜。`},
    {title:"幫我規劃一個功能",when:"想新增功能，但還不知道怎麼拆任務時。",prompt:`我想新增一個功能，請你先幫我規劃，不要直接改檔案。

功能想法：
【在這裡貼上你的功能想法】

請幫我：
1. 先用新手能懂的話重述我的需求。
2. 如果需求不清楚，先問最多 3 個必要問題。
3. 拆成可以一步一步完成的小任務。
4. 說明會影響哪些檔案或模組。
5. 列出可能風險與驗證方式。

等我確認規劃後，再進入實作。`},
    {title:"幫我修 bug",when:"畫面壞掉、功能不動、指令報錯時。",prompt:`我遇到一個 bug，請你用穩健方式幫我處理。

問題描述：
【貼上錯誤訊息、畫面狀況、重現步驟】

請依序處理：
1. 先整理你理解到的問題。
2. 找出最可能的原因，並說明判斷依據。
3. 先提出最小修正方案。
4. 經我同意後再修改檔案。
5. 修完後請執行可行的驗證，並回報結果。

限制：
- 不要一次大改。
- 不要順手重構無關程式。
- 如果需要危險指令，先停下來問我。`}
  ]},
  {title:"找資料 / 做比對",hint:"查文件、比工具、整理外部資訊時用這區。",cards:[
    {title:"幫我找相關資料並整理",when:"想理解工具、文件、範例或做資料蒐集時。",prompt:`請幫我找相關資料並整理成新手看得懂的摘要。

我要了解的主題：
【貼上主題或問題】

請幫我：
1. 先列出查找方向與關鍵字。
2. 整理重點、限制、適用情境。
3. 如果有來源，請標示來源名稱或連結。
4. 把不確定或可能過時的資訊標出來。
5. 最後給我一段「我現在該怎麼做」的建議。

限制：
- 不要把推測說成事實。
- 找不到可靠來源時要明講。`},
    {title:"幫我比較幾個方案",when:"要選技術、工具、流程或做決策前。",prompt:`請幫我比較下面幾個方案，並用新手能懂的方式整理。

我要比較的方案：
【方案 A】
【方案 B】
【方案 C，可留空】

請用表格列出：
1. 適合情境。
2. 優點。
3. 缺點。
4. 成本或學習門檻。
5. 風險。
6. 你的建議。

最後請補一句：如果我是新手，應該先選哪個，以及為什麼。
請記得：你可以給建議，但最後決定權留給我。`}
  ]},
  {title:"整理資料",hint:"整理筆記、會議、文章、雜亂文字時用這區。",cards:[
    {title:"整理錄音逐字稿成會議記錄",when:"拿到會議錄音、逐字稿或口述內容，要整理成會議記錄、風險、待辦、工程師版規劃或主管摘要時使用。",prompt:`使用 meeting-audio-project-assistant 協助我處理下面這份錄音或逐字稿。

請先不要直接整理，先用「風險型專案助理」角度確認：
1. 敏感等級：公開 / 內部 / 客戶 / 個資
2. 輸出用途：個人版 / 工程師版 / 主管版 / 三者都要
3. 是否已有逐字稿，還是只有錄音檔
4. 是否需要說話者標記
5. 是否允許使用雲端 API；若含客戶或個資，預設不允許

確認後請依序輸出：
1. 結論 / 建議
2. 3 到 5 個風險點
3. 需要確認的問題
4. 會議重點摘要
5. 決議與待辦事項
6. 未確認問題
7. 下一步最小行動

如果我要工程師版，請再補：
- 需求背景
- 使用者目標
- 功能需求
- 資料需求
- 開發任務
- 驗收條件

如果我要主管版，請再補：
- 一句話結論
- 目前狀態
- 影響
- 需要主管決策的事項

逐字稿或錄音內容如下：
【貼上逐字稿，或描述錄音檔路徑與會議背景】`},
    {title:"幫我整理這段資料",when:"貼上一大段文字、筆記、會議紀錄後使用。",prompt:`請幫我整理下面這段資料，讓它變得清楚、好讀、可執行。

資料內容：
【貼上資料】

請輸出：
1. 一段短摘要。
2. 重點條列。
3. 待辦事項。
4. 重要決定。
5. 還不清楚、需要補問的地方。

限制：
- 不要自行補不存在的資訊。
- 如果原文有矛盾，請標出來。`},
    {title:"幫我把資料整理成表格",when:"想把雜亂文字變成欄位、表格或清單時。",prompt:`請幫我把下面資料整理成表格。

資料內容：
【貼上資料】

請先建議適合的欄位，然後輸出表格。

要求：
1. 保留原始意思。
2. 不要自行補不存在的資料。
3. 缺資料的欄位請填「待補」。
4. 如果資料太亂，請先列出你會怎麼分類。`}
  ]},
  {title:"整理電腦檔案",hint:"風險最高，只先規劃，不直接動你的檔案。",safety:"這區所有提示詞都要求 AI 先列計畫，不刪除、不搬移、不改名，等你確認後才進下一步。",cards:[
    {title:"先幫我規劃資料夾分類",when:"資料夾很亂，但你還不想讓 AI 動檔案。",prompt:`請先幫我規劃資料夾分類，但不要直接修改任何檔案。

資料夾或檔案清單：
【貼上資料夾路徑或檔案清單】

請幫我：
1. 只根據資料夾名稱與檔名分析。
2. 建議分類規則。
3. 建議要建立哪些資料夾。
4. 列出哪些檔案可能放在哪一類。
5. 標出你不確定的檔案，讓我自己判斷。

安全限制：
- 不要刪除任何檔案。
- 不要搬移任何檔案。
- 不要改任何檔名。
- 請先列出整理計畫與受影響檔案。
- 等我確認後，再產生下一步指令。`},
    {title:"幫我產生安全整理計畫",when:"準備整理大量檔案前，先做 dry-run 計畫。",prompt:`請幫我產生一份安全的電腦檔案整理計畫，但現在只做 dry-run，不要真的動檔案。

目標資料夾：
【貼上資料夾路徑或檔案清單】

我希望整理成：
【例如：依專案、日期、檔案類型、用途分類】

請輸出：
1. 建議分類結構。
2. 受影響檔案清單。
3. 每個檔案建議搬到哪裡。
4. 可能重複或不確定的檔案。
5. 執行前備份建議。
6. 需要我確認的問題。

安全限制：
- 不要刪除、不要搬移、不要改名。
- 請先列出整理計畫與受影響檔案，等我確認後再產生下一步指令。
- 如果你需要執行任何指令，必須先問我。`}
  ]},
  {title:"生成圖片提示詞",hint:"要用 Codex / 圖像 skill 產生圖片前，先把主題、風格、比例與限制講清楚。",cards:[
    {title:"生成海報 / 傳單提示詞",when:"要做活動宣傳、招生、促銷、展覽、課程或品牌曝光的海報與傳單時。",questions:[
      {id:"promo_purpose",label:"宣傳用途",type:"choice",options:["活動宣傳","課程 / 招生","產品促銷","服務介紹","品牌形象","其他"]},
      {id:"promo_format",label:"輸出形式",type:"choice",options:["海報","傳單","海報 + 傳單同時要"]},
      {id:"promo_style",label:"視覺風格",type:"choice",options:["專業商務","文青質感","科技未來感","活潑吸睛","高級精品感","可愛親和","其他"]},
      {id:"promo_audience",label:"目標受眾",type:"choice",options:["一般消費者","學生","家長","上班族","老闆 / 主管","特定社群"]},
      {id:"promo_ratio",label:"圖片比例 / 尺寸",type:"choice",options:["A4 傳單直式","4:5 社群宣傳海報","1:1 方形","9:16 直式看板","16:9 橫式","我不確定，請你建議"]},
      {id:"promo_text_zone",label:"是否需要保留文字區",type:"choice",options:["需要大標題區","需要標題 + 內文區","幾乎不要文字，只留視覺","我不確定，請你建議"]},
      {id:"promo_brand",label:"品牌素材狀況",type:"choice",options:["有品牌色 / Logo / 指定元素","有參考圖或現成文案","沒有，請你自由提案"]}
    ],prompt:`請先不要直接生成海報或傳單圖片，先用「選擇題」逐題問我，幫我把需求問清楚後，再整理成可直接生圖的提示詞。

請依序用選擇題問我，每次 1 題：
1. 宣傳用途
- A. 活動宣傳
- B. 課程 / 招生
- C. 產品促銷
- D. 服務介紹
- E. 品牌形象
- F. 其他（讓我補充）
2. 輸出形式
- A. 海報
- B. 傳單
- C. 海報 + 傳單同時要
3. 視覺風格
- A. 專業商務
- B. 文青質感
- C. 科技未來感
- D. 活潑吸睛
- E. 高級精品感
- F. 可愛親和
- G. 其他（讓我補充）
4. 目標受眾
- A. 一般消費者
- B. 學生
- C. 家長
- D. 上班族
- E. 老闆 / 主管
- F. 特定社群（讓我補充）
5. 圖片比例 / 尺寸
- A. A4 傳單直式
- B. 4:5 社群宣傳海報
- C. 1:1 方形
- D. 9:16 直式看板
- E. 16:9 橫式
- F. 我不確定，請你建議
6. 是否需要保留文字區
- A. 需要大標題區
- B. 需要標題 + 內文區
- C. 幾乎不要文字，只留視覺
- D. 我不確定，請你建議
7. 是否有品牌限制
- A. 有品牌色 / Logo / 指定元素
- B. 有參考圖或現成文案
- C. 沒有，請你自由提案

當我回答完後，請輸出：
1. 結論 / 建議
2. 3 到 5 個風險點
3. 還需要我補充的資訊
4. 3 個海報 / 傳單圖片生成版本
- 版本 A：穩健清楚版
- 版本 B：更吸睛宣傳版
- 版本 C：更有設計感版
5. 每個版本都附上：
- 中文提示詞
- 英文提示詞
- 建議比例
- 構圖說明
- 負面提示詞
6. 如果圖片內需要精準文字，請明確提醒我改用後製加字，不要把大量中文字直接交給生圖模型。`}
    ,{title:"生成社群貼文圖片提示詞",when:"要做 Facebook、Instagram、Threads、LinkedIn、小紅書或一般社群圖卡時。",questions:[
      {id:"social_purpose",label:"社群用途",type:"choice",options:["活動預告","產品 / 服務宣傳","品牌曝光","新功能 / 新消息公告","知識型圖卡","導流到網站 / 報名頁","其他"]},
      {id:"social_platform",label:"平台",type:"choice",options:["Instagram","Facebook","Threads","LinkedIn","小紅書","多平台共用"]},
      {id:"social_style",label:"視覺風格",type:"choice",options:["專業乾淨","活潑吸睛","高級質感","科技感","溫暖生活感","強烈促銷感","其他"]},
      {id:"social_format",label:"圖片形式",type:"choice",options:["單張貼文圖","方形圖卡","直式封面圖","輪播第一張主視覺","限時動態封面"]},
      {id:"social_audience",label:"目標對象",type:"choice",options:["新客戶","舊客戶","粉絲","主管 / B2B 對象","特定族群"]},
      {id:"social_copy_zone",label:"是否需要留白放文案",type:"choice",options:["要明顯標題區","要 CTA / 按鈕視覺區","只要主視覺，不放太多字","我不確定，請你建議"]},
      {id:"social_brand",label:"品牌素材狀況",type:"choice",options:["已有品牌色","已有 Logo / 產品照","已有文案","都沒有，請你先提方向"]}
    ],prompt:`請先不要直接生成社群圖片，先用「選擇題」逐題問我，確認宣傳目的與風格後，再整理成可直接生圖的提示詞。

請依序用選擇題問我，每次 1 題：
1. 社群用途
- A. 活動預告
- B. 產品 / 服務宣傳
- C. 品牌曝光
- D. 新功能 / 新消息公告
- E. 知識型圖卡
- F. 導流到網站 / 報名頁
- G. 其他（讓我補充）
2. 平台
- A. Instagram
- B. Facebook
- C. Threads
- D. LinkedIn
- E. 小紅書
- F. 多平台共用
3. 視覺風格
- A. 專業乾淨
- B. 活潑吸睛
- C. 高級質感
- D. 科技感
- E. 溫暖生活感
- F. 強烈促銷感
- G. 其他（讓我補充）
4. 圖片形式
- A. 單張貼文圖
- B. 方形圖卡
- C. 直式封面圖
- D. 輪播第一張主視覺
- E. 限時動態封面
5. 目標對象
- A. 新客戶
- B. 舊客戶
- C. 粉絲
- D. 主管 / B2B 對象
- E. 特定族群（讓我補充）
6. 是否需要留白放文案
- A. 要明顯標題區
- B. 要 CTA / 按鈕視覺區
- C. 只要主視覺，不放太多字
- D. 我不確定，請你建議
7. 品牌素材狀況
- A. 已有品牌色
- B. 已有 Logo / 產品照
- C. 已有文案
- D. 都沒有，請你先提方向

當我回答完後，請輸出：
1. 結論 / 建議
2. 3 到 5 個風險點
3. 還需要我補充的資訊
4. 3 個社群貼文圖片生成版本
- 版本 A：穩健通用版
- 版本 B：更吸睛互動版
- 版本 C：更有品牌感版
5. 每個版本都附上：
- 中文提示詞
- 英文提示詞
- 建議平台比例
- 畫面構圖說明
- 負面提示詞
6. 額外補一段：
- 這張圖適合搭配的貼文語氣
- 建議 CTA 類型
- 如果要精準放中文字，應該後製處理哪些文字區塊。`}
    ,{title:"幫我把想法整理成圖片提示詞",when:"你只有模糊想法，想先變成可拿去生圖的 prompt。",prompt:`請幫我把下面的想法整理成高品質圖片生成提示詞。

圖片想法：
【貼上你想生成的圖片內容，例如文章封面、產品圖、插畫、社群圖卡】

請先不要直接生成圖片，先幫我整理：
1. 圖片用途：例如文章封面、簡報圖、社群貼文、產品示意圖。
2. 主體：畫面中最重要的人、物、場景或概念。
3. 風格：寫實、插畫、電影感、資訊圖、極簡、科技感等。
4. 構圖：主體位置、背景、視角、光線、是否需要留白。
5. 比例：16:9、1:1、9:16、4:3 或其他。
6. 需要避免的內容：不要出現錯字、不要塞太多文字、不要像廉價素材圖。

最後請輸出 3 個版本：
- 版本 A：穩健清楚版
- 版本 B：更有設計感版
- 版本 C：更大膽創意版

每個版本都請附：
1. 中文提示詞
2. 英文提示詞
3. 建議比例
4. 適合用在哪裡`},
    {title:"生成文章封面圖提示詞",when:"寫文章、報告、企劃或簡報，需要一張封面圖時。",prompt:`請幫我產生一組可直接用於 AI 圖像生成的文章封面提示詞。

文章或主題：
【貼上文章標題、摘要或核心觀點】

目標讀者：
【例如主管、一般大眾、工程師、客戶、學生】

我希望的氣氛：
【例如專業、溫暖、科技感、冷靜、震撼、可愛、未來感】

請輸出：
1. 封面視覺概念：用 3-5 句話說明畫面長什麼樣。
2. 圖片生成提示詞：繁體中文一版、英文一版。
3. 構圖要求：主體、背景、留白、光線、視角。
4. 文字處理：如果需要標題，請建議後製加字；不要要求 AI 在圖中直接產生大量文字。
5. 比例建議：16:9、1:1、9:16 各適合什麼情境。
6. 負面提示詞：列出不要出現的元素，例如低解析、過度複雜、錯字、扭曲手指、廉價素材感。`}
  ]},
  {title:"生成影片提示詞",hint:"要替 Codex 準備短影音、展示影片或腳本分鏡時，先把鏡頭、節奏、旁白與畫面限制講清楚。",cards:[
    {title:"幫我把想法整理成 Codex 影片生成提示詞",when:"想用 Codex 生成影片，但還不知道怎麼描述鏡頭與畫面。",prompt:`請幫我把下面的想法整理成適合 Codex 使用的高品質影片生成提示詞。

影片想法：
【貼上你想做的影片內容，例如產品展示、短影音、品牌形象、教學片段】

請先不要直接生成影片，先幫我整理：
1. 影片用途：社群短影音、產品展示、活動開場、教學、簡報背景。
2. 影片長度：建議 5 秒、10 秒、15 秒或 30 秒。
3. 畫面主體：人物、產品、場景或抽象概念。
4. 鏡頭運動：推進、拉遠、環繞、平移、手持感、定鏡。
5. 節奏與情緒：冷靜、快速、震撼、溫暖、專業、科技感。
6. 畫面比例：16:9、9:16、1:1。
7. 不要出現的問題：字幕亂碼、人物變形、品牌文字錯誤、鏡頭太晃、過度特效。

最後請輸出 3 個版本：
- 版本 A：穩健清楚版
- 版本 B：更有電影感版
- 版本 C：適合社群短影音版

每個版本都請附：
1. 中文影片提示詞
2. 英文影片提示詞
3. 分鏡或鏡頭描述
4. 建議比例與秒數
5. 負面提示詞`},
    {title:"生成短影音分鏡提示詞",when:"要把一個主題做成 15-30 秒短片或廣告腳本時。",prompt:`請幫我把下面主題整理成 AI 影片生成用的短影音分鏡提示詞。

主題：
【貼上產品、服務、文章主題或活動內容】

目標觀眾：
【例如主管、一般消費者、社群粉絲、客戶、學生】

影片目的：
【例如吸引注意、介紹功能、展示成果、說服購買、教學】

請輸出：
1. 一句影片核心概念。
2. 15 秒版本分鏡：3-5 個鏡頭，每個鏡頭包含畫面、鏡頭運動、情緒、秒數。
3. 30 秒版本分鏡：5-8 個鏡頭，每個鏡頭包含畫面、鏡頭運動、情緒、秒數。
4. 可直接貼給影片生成模型的中文 prompt。
5. 可直接貼給影片生成模型的英文 prompt。
6. 旁白草稿：如果不適合旁白，也請說明原因。
7. 負面提示詞：避免錯字、怪異人物、過度轉場、畫面不連續、品牌標誌錯誤。

限制：
- 不要把畫面塞滿文字。
- 如果需要精準文字或 Logo，請建議後製加入，不要要求 AI 直接生成精準中文字。`}
  ]},
  {title:"生成簡報 / 互動式網頁簡報",hint:"要請 Codex 幫你整理簡報或做可操作的網頁簡報時，先把受眾、結構、頁數與互動需求講清楚。",cards:[
    {title:"幫我整理成簡報生成提示詞",when:"腦中有內容方向，但還不知道怎麼交代 AI 產出簡報架構與每頁重點時。",prompt:`請幫我把下面的想法整理成適合 Codex 使用的簡報生成提示詞。

簡報主題：
【貼上主題，例如產品提案、專案進度、教學內容、內部報告】

已知素材：
【貼上重點資料、數字、文章、會議結論，沒有可留空】

請先不要直接做簡報檔，先幫我整理：
1. 簡報目的：提案、說服、匯報、教學、招商、Demo。
2. 目標觀眾：主管、客戶、同事、學生、投資人。
3. 預計頁數：5 頁、8 頁、10 頁、15 頁。
4. 內容結構：封面、問題、解法、證據、案例、結論、下一步。
5. 視覺方向：專業、科技感、簡潔、高級、活潑、品牌化。
6. 是否需要圖表、流程圖、時間線、對照表。
7. 不要出現的問題：字太多、空話、頁面太滿、風格不一致、沒有重點。

最後請輸出：
1. 一段可直接貼給 Codex 的簡報生成提示詞
2. 建議的簡報大綱
3. 每頁標題與 3-5 個重點
4. 建議視覺風格與版型
5. 如果要做成正式簡報檔，還缺哪些資料`},
    {title:"幫我整理成互動式網頁簡報提示詞",when:"要把簡報做成可點擊、可滾動、可展示動畫的網頁簡報時。",prompt:`請幫我把下面的想法整理成適合 Codex 使用的互動式網頁簡報提示詞。

主題：
【貼上主題】

使用情境：
【例如登台簡報、業務展示、產品 Demo、展場播放、作品集】

請先幫我整理：
1. 簡報目標：介紹、說服、展示成果、帶看功能、導流。
2. 頁面形式：單頁滾動、分頁切換、全螢幕投影片、故事型敘事。
3. 互動需求：按鈕切換、步進動畫、圖表互動、影片嵌入、前後頁切換。
4. 內容段落：開場、痛點、方案、亮點、案例、CTA。
5. 視覺方向：品牌色、字體氣質、背景風格、動態節奏。
6. 裝置需求：桌機簡報、手機可看、投影幕展示。
7. 限制條件：不要太花、不要卡頓、不要依賴太多外部服務。

最後請輸出：
1. 一段可直接貼給 Codex 的互動式網頁簡報生成提示詞
2. 頁面 / 投影片結構
3. 每一段的互動與動畫建議
4. 技術注意事項
5. 如果要開始做，建議先準備的素材清單`},
  ]},
  {title:"生成網站",hint:"要請 Codex 幫你做網站時，先把網站目的、頁面、風格、內容來源與功能範圍講清楚。",cards:[
    {title:"幫我整理成網站生成提示詞",when:"想做一個官網、產品頁、作品集或活動頁，但還不知道怎麼開需求。",prompt:`請幫我把下面的想法整理成適合 Codex 使用的網站生成提示詞。

網站想法：
【貼上你想做的網站內容】

請先不要直接開始寫程式，先幫我整理：
1. 網站類型：品牌官網、產品介紹頁、活動頁、作品集、部落格、內部工具。
2. 目標使用者：客戶、一般訪客、主管、學生、社群粉絲。
3. 主要目標：蒐集名單、展示資訊、導購、預約、下載、建立信任。
4. 需要頁面：首頁、關於、服務、案例、FAQ、聯絡、登入等。
5. 視覺風格：專業、極簡、科技感、溫暖、年輕、大膽。
6. 內容來源：我已經有文案、只有草稿、需要 AI 先補文案。
7. 功能需求：表單、搜尋、篩選、動畫、部落格、CMS、會員、串 API。
8. 限制條件：手機優先、載入速度、SEO、不要太難維護。

最後請輸出：
1. 一段可直接貼給 Codex 的網站生成提示詞
2. 建議網站架構與頁面清單
3. 首頁區塊規劃
4. 視覺與內容建議
5. 開發前還需要補的資訊`},
    {title:"幫我整理成網站改版提示詞",when:"已有舊網站，想請 Codex 協助重做結構、視覺或內容時。",prompt:`請幫我把下面的網站改版需求整理成適合 Codex 使用的提示詞。

現有網站：
【貼上網址或描述現況】

改版目標：
【例如更專業、轉換率更高、手機版更好、改成新品牌風格】

目前問題：
【例如資訊太亂、太醜、太慢、不好操作、沒有重點】

請先幫我整理：
1. 保留什麼：品牌元素、既有文案、功能、SEO 結構。
2. 要重做什麼：首頁、導覽、文案、視覺、資訊架構、互動。
3. 使用者最重要的任務是什麼。
4. 哪些頁面優先改。
5. 適合的新版風格方向。
6. 技術或維護限制。
7. 風險提醒：資料遺失、SEO 掉落、內容搬移、相容性問題。

最後請輸出：
1. 一段可直接貼給 Codex 的網站改版提示詞
2. 改版重點清單
3. 優先順序建議
4. 新舊差異整理方式
5. 開始前應先確認的事項`},
  ]},
  {title:"大型系統 / 系統遷移",hint:"開發複雜系統、或把現有桌面 / Excel 系統改成網頁版時，先從這區開始規劃。",cards:[
    {title:"分析現有系統，規劃網頁版",when:"手邊有一套桌面程式或舊系統，想把它搬到網頁上，但不知道從哪裡下手。",prompt:`我手邊有一套現有的【桌面程式 / Windows 系統 / Excel 工作流程 / 其他系統】，想把它搬到網頁上。請先幫我分析與規劃，不要直接寫程式。

現有系統描述：
【說明這套系統是做什麼的、有哪些主要功能、誰在用、目前怎麼用】

請依序幫我：
1. 整理這套系統的核心功能清單（5–10 項，用白話描述）。
2. 判斷哪些功能「完全可以搬到網頁」、哪些「需要調整」、哪些「暫時不搬」。
3. 說明網頁版與桌面版的主要差異（登入方式、資料儲存、多人同時用等）。
4. 建議技術方向（例如：純網頁、需要後端 API、需要資料庫），用新手聽得懂的話說明。
5. 建議第一版網頁版應該先做哪 3 項核心功能。
6. 列出遷移風險：舊資料、使用者習慣、功能缺口。

限制：
- 先不要寫程式，先幫我搞清楚「要做什麼」再談「怎麼做」。
- 如果描述不夠清楚，請問我最多 3 個問題。
- 給我新手看得懂的建議，不要一開始就丟一堆技術名詞。`},
    {title:"大型系統分階段規劃",when:"要開發的系統太大，一次做完不現實，需要切成幾個可執行的階段。",prompt:`我要開發一個比較大的系統，一次做完太難，想分成幾個階段。請先幫我規劃分階段策略，不要直接寫程式。

系統目標：
【說明這個系統要解決什麼問題、主要功能有哪些、誰會用】

使用情境：
【例如：公司內部用、對外客戶用、幾個人用、需不需要多人同時使用】

請幫我：
1. 整理功能清單，依「一定要有」「應該有」「有更好」三類分類。
2. 建議分成幾個開發階段，每個階段的目標與完成條件。
3. 第一階段（MVP）：最小可以給人用的版本，具體包含哪些功能。
4. 各階段依賴關係：哪些功能要先做才能做後面的。
5. 每個階段的預估難度（新手 / 中等 / 困難）與大概時間。
6. 第一步：現在最應該先做什麼。

限制：
- 先不要寫程式，先規劃。
- 第一階段請盡量小，兩週內能動的版本才算。
- 如果需求不清楚，請先問我最多 3 個問題。`},
    {title:"把人工流程 / Excel 自動化成系統",when:"現在用人工或 Excel 處理一個流程，想把它自動化或做成網頁系統。",prompt:`我現在有一個用人工或 Excel 處理的流程，想把它自動化或做成系統。請先幫我盤點與規劃，不要直接寫程式。

目前流程描述：
【說明現在怎麼做：誰負責、用什麼工具、每次要花多久、有哪些步驟】

痛點：
【最讓你頭大的步驟、最容易出錯的地方、最浪費時間的環節】

請幫我：
1. 用條列方式整理目前的作業流程。
2. 標出哪些步驟「可以直接自動化」、哪些「要人判斷才能做」。
3. 建議自動化後的新流程（改前 vs 改後對比）。
4. 說明要做到這個效果，大概需要什麼技術（用新手聽得懂的話）。
5. 估算自動化後每週可省多少時間，可以用來跟主管說明價值。
6. 建議第一步：最小範圍的自動化先做什麼，兩週內能動的版本。

限制：
- 先不要寫程式。
- 請先問我最多 3 個必要問題（如果描述不夠清楚）。
- 最後請給我一段可以講給主管聽的說明方式。`},
    {title:"盤點現有資料庫結構",when:"接手一套舊系統，想先搞清楚資料庫裡有哪些資料表、每張表是做什麼用的，再決定怎麼動它。",prompt:`我接手了一套系統，想先把資料庫結構摸清楚再動手。請幫我規劃如何盤點，並提供對應的查詢語法。

資料庫類型：【MySQL / PostgreSQL / MS SQL Server / SQLite / 其他】

請幫我：
1. 提供可以列出「這個資料庫所有資料表名稱」的 SQL 語法。
2. 提供可以查看「某張資料表的所有欄位、資料型別、是否允許空值、預設值」的語法。
3. 提供可以查看「有哪些外鍵關聯（foreign key）」的語法，讓我知道哪些表是互相連動的。
4. 提供可以一次抓出「每張資料表大概有幾筆資料」的語法。
5. 說明我拿到這些資訊後，要怎麼整理成一份讓新人也看得懂的資料表清單。

限制：
- 我不一定熟 SQL，請在每段語法後面加一行說明「這段在做什麼」。
- 如果不同資料庫語法有差異，請分開列出。
- 最後建議我用什麼工具（GUI 或命令列）來執行這些語法最方便。`},
    {title:"分析資料表關聯，準備遷移",when:"要把舊資料庫的資料搬到新系統，需要先搞清楚資料表之間怎麼串在一起，避免搬的時候順序錯誤或漏掉關聯。",prompt:`我要把舊系統的資料庫遷移到新系統，需要先理清資料表的關聯與搬移順序。

資料庫類型：【MySQL / PostgreSQL / MS SQL Server / SQLite / 其他】

現有資料表（如果已知道）：
【貼上 SHOW TABLES 或 \\dt 的輸出，或直接描述你知道的表名；不知道就填「還不清楚」】

請幫我：
1. 提供語法，列出所有外鍵關係（從哪張表的哪個欄位指向哪張表的哪個欄位）。
2. 根據外鍵依賴，幫我排出「資料應該照這個順序遷移」的清單（先搬哪張、再搬哪張）。
3. 指出遷移時最常踩的坑：外鍵約束失敗、資料型別不符、NULL 值問題、自增 ID 衝突等。
4. 建議遷移前的備份方式，以及如何驗證遷移後資料是否完整。
5. 如果有些資料在舊系統是「邏輯刪除」（軟刪除），說明遷移時要特別注意什麼。

限制：
- 請給可以直接貼到資料庫工具執行的 SQL。
- 如果我貼出的資訊不夠，請告訴我還需要補充什麼。
- 步驟說明用新手看得懂的白話文。`},
    {title:"幫我選資料庫 + 設定連線",when:"要開始一個新專案或接手舊系統，不確定該用哪種資料庫、或不知道怎麼在程式裡連上資料庫。",prompt:`我需要在專案裡選擇並連接資料庫，請幫我選型並給出連線設定範例。

專案情況：
- 程式語言 / 框架：【Python / Node.js / PHP / Java / C# / 其他】
- 預計用途：【例如：網頁後端 API、桌面應用、數據分析腳本、小型工具】
- 資料量規模：【幾百筆 / 幾萬筆 / 幾百萬筆以上】
- 需不需要多人同時讀寫：【是 / 否 / 不確定】
- 已有的資料庫（如果有）：【MySQL / PostgreSQL / MS SQL Server / SQLite / MongoDB / 其他 / 還沒有】

請幫我：
1. 根據我的情況推薦最適合的資料庫，說明理由（用白話比較 2–3 個選項）。
2. 提供在我的語言 / 框架裡安裝資料庫套件的指令。
3. 提供一份最小可執行的連線範例程式碼（包含：連線字串格式、如何測試連線是否成功）。
4. 說明連線字串裡每個參數的意思（host、port、dbname、user、password 等）。
5. 告訴我連線資訊應該放在哪裡（.env 檔？config 檔？），不應該直接寫在程式碼裡。
6. 列出最常見的連線失敗原因與排查步驟。

限制：
- 給我可以直接複製貼上執行的程式碼。
- 不要只貼官方文件連結，請直接給範例。`},
    {title:"對資料庫做新增、修改、刪除、搜尋",when:"已經連上資料庫了，想知道怎麼用程式對資料庫做基本的 CRUD 操作（建立、讀取、更新、刪除）。",prompt:`我已經連上資料庫，想學會用程式對資料庫做基本操作（CRUD）。

環境資訊：
- 程式語言 / 框架：【Python / Node.js / PHP / Java / C# / 其他】
- 資料庫：【MySQL / PostgreSQL / MS SQL Server / SQLite / 其他】
- 是否使用 ORM：【是，用 【ORM 名稱】 / 否，直接寫 SQL / 不確定什麼是 ORM】

資料表（如果已知道）：
【貼上資料表名稱與主要欄位，例如：users 表有 id、name、email、created_at】

請分別示範：
1. **新增（INSERT）**：新增一筆資料的完整範例，包含如何帶入變數。
2. **查詢（SELECT）**：
   - 查全部資料
   - 依條件搜尋（例如：找特定 email、找某個日期之後的資料）
   - 只取部分欄位
   - 排序 + 分頁（LIMIT / OFFSET）
3. **修改（UPDATE）**：依 ID 更新特定欄位的範例。
4. **刪除（DELETE）**：依條件刪除資料，並說明軟刪除（加 deleted_at 欄位）與硬刪除的差異。
5. **防 SQL Injection**：說明為什麼不能用字串拼接，並示範正確的參數化查詢寫法。

限制：
- 每個操作給一段完整可執行的程式碼，不要只貼片段。
- 如果 ORM 與原生 SQL 寫法差很多，請兩種都示範。
- 最後提醒我哪些操作執行前要特別小心（例如：沒有 WHERE 條件的 DELETE）。`}
  ]}
];
const PROJECT_STAGES = [
  ["v1.0","控制台初版","Skill 目錄、提示詞庫、搜尋與安檢流程。"],
  ["v1.1","快速看板與組合包","二刀流中控快速看板與常用流程一包複製。"],
  ["v1.2","Backlog 修正","修正 state board、中文階段解析與 combos 檢查。"],
  ["v1.3","桌面入口","macOS / Windows 桌面捷徑與安裝流程整理。"],
  ["v1.4","維護收尾","移除多餘參數、補維護註解與忽略檔規則。"],
  ["v1.5","上下文壓縮","新增壓縮接續規則、提示詞卡與 skill 同步。"],
  ["v1.6","固定交棒檔","新增 NEXT-AI-TASK.md，讓下一棒 AI 能接續。"],
  ["v1.7","二刀流中控收尾","提示詞定位、狀態解析與 backlog 標記補齊。"],
  ["v1.8","新手入口與開發進度","新增開發進度 tab，整理目前狀態與下一步。"],
  ["v1.9","二刀流命名","統一控制台名稱為二刀流開發助手控制台。"],
  ["v2.0","日常提示詞","新增新手版日常提示詞與 GitHub Pages demo banner。"],
  ["v2.1","分工提示與專案討論","新增新手分工說明入口與雙 AI 新專案討論提示詞。"]
];
const PAGE_INTROS = {
  installGuide:{title:"安裝與外掛",lead:"這頁專門介紹怎麼安裝 Codex、Claude Code、常用外掛 / skills，最後再教你怎麼和這個控制台網站一起使用。",purpose:"把工具安裝、登入、加插件、接上控制台的流程一次講清楚。",first:"先決定你要用桌面版、IDE extension 還是 CLI；建議新手先裝 Codex app，再裝 Claude Code。",when:"第一次使用這套控制台，或要教同事、家人、團隊成員從零安裝時。"},
  backup:{title:"備份 / 還原",lead:"這頁只做兩件事：把你電腦上的 Codex / Claude Code 設定一次備份到自己的 GitHub，或是從 GitHub 把它還原回任何一台電腦（Mac 或 Windows 都自動判斷）。整個流程靠一段提示詞跑完，沒 GitHub 帳號或倉庫也會自動帶你建立。",purpose:"用提示詞替你完成本機 → GitHub 的備份，以及 GitHub → 本機（Mac／Windows）的還原。",first:"先點「複製 備份提示詞」，把它貼給 Codex 或 Claude Code（VS Code），它會自己處理 GitHub 帳號與倉庫。",when:"想把目前設定備份起來、換電腦、重灌系統、給家人或團隊複製同一份環境時。"},
  skills:{title:"外掛 / Skill庫",lead:"查看每個外掛、skill 的用途、風險與觸發句，直接複製給 AI 使用。",purpose:"快速判斷現在要叫哪個外掛或 AI skill。",first:"搜尋關鍵字，再複製觸發句。",when:"不確定某個任務該用哪個外掛或 skill 時。"},
  prompts:{title:"提示詞庫",lead:"常用提示詞集中管理，適合你直接複製給 Codex 或 Claude Code（VS Code）。",purpose:"快速啟動工作流程。",first:"先選二刀流、單一 AI 或通用分類，再複製。",when:"要交辦任務、請 AI 審查、整理交接或產出文件時。"},
  capture:{title:"收錄新內容",lead:"看到好用提示詞或 skill 時，先填表產生交辦提示詞與 YAML 片段，再交給 Codex 寫入、重建、驗證與 commit。",purpose:"安全收錄新內容，不需要你手寫 YAML。",first:"先選提示詞或 Skill；新手請複製「給 Codex 的完整交辦提示詞」。",when:"看到新 skill、實用提示詞，或想把工作流模板收入控制台時。"},
  control:{title:"二刀流中控",lead:"v1 是靜態教學頁，不讀取 DUAL-AI-STATE.md；按鈕只會跳到提示詞庫並複製對應提示詞。",purpose:"讓每個階段知道要找誰、做什麼、複製哪張提示詞。",first:"先看目前要進哪一階段，再按卡片按鈕複製對應提示詞。",when:"要從規劃、實作、審查、修正、複審到存檔收尾一路接續時。"},
  progress:{title:"專案開發（雙刀／單刀）",lead:"這頁把目前專案做到哪裡、下一步要做什麼一次整理出來。預設是雙刀流（Claude Code＋Codex）；雙刀流跑不動時，可在下方切換成單刀（Codex 專用），照樣把專案推下去。",purpose:"不用翻文件也能快速知道現在進度、是否有卡點，以及下一步該做什麼。",first:"先看目前階段與下一步；如果有未解決問題，先處理警示區。",when:"接續開發、換 AI 接手、雙刀流臨時跑不動需要單刀續開，或想確認這個專案現在是不是可以往下一步走時。"},
  daily:{title:"日常提示詞",lead:"不知道怎麼開口時，先從這裡複製。這頁把開發、查資料、整理資料、整理電腦檔案、生成圖片、生成影片、生成簡報與生成網站整理成新手可直接使用的提示詞。",purpose:"把日常最常用的 AI 交辦方式整理成安全、直接可複製的新手版。",first:"先選你現在想做什麼，再複製對應卡片。整理電腦檔案時，只先規劃，不直接動檔。",when:"開發系統、找資料比對、整理文字資料、分類電腦檔案、產生圖片 prompt、產生影片 prompt、整理簡報需求或規劃網站需求時。"},
  customSkill:{title:"個人化設定",lead:"用選單自動組出「個人化專屬 skill」提示詞。使用者先選職業、用途、AI 風格、安裝目標，再複製整段給 Codex。",purpose:"把你的工作痛點、陪練方式與封裝安裝流程，變成可重複使用的專屬 AI 工作 skill。",first:"進頁面後會跳出選單；先選好欄位，再按「更新提示詞」或直接複製。",when:"想讓 AI 先理解你的職務與業務，再替你做挑刺陪練，最後封裝成可安裝 skill 時。"},
  automation:{title:"自動化設定",lead:"把常用的 AI 自動化流程入口集中在這一頁，先看流程說明，再決定要不要跳到專案開發頁接續。",purpose:"整理自動化流程、工作交接與專案接續的主要入口。",first:"先看你現在需要的是流程說明、提示詞收錄，還是直接接續專案。",when:"想把 AI 工作流程做成固定步驟、接續專案、或整理自動化操作入口時。"},
  guide:{title:"新手快速開始",lead:"這一頁改成新手版入口，專門幫你用最簡單的方式認識這套外掛系統，知道先裝什麼、先開什麼、接著怎麼用。",purpose:"讓第一次接觸的人不用先懂很多指令，也能照著控制台把工具、外掛與提示詞順順接起來。",first:"先看下方的新手 3 步驟，再按你現在需要的入口進去。",when:"第一次使用這套控制台、要教新手上手，或想快速整理自己目前該從哪裡開始時。"}
};
const riskCls = {"低":"low","中":"mid","高":"high"};
const esc = s => (s ?? "").toString().replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
function copyText(text, btn){const original=btn.dataset.copyLabel||btn.textContent;btn.dataset.copyLabel=original;const done=()=>{btn.textContent="已複製";btn.classList.add("done");setTimeout(()=>{btn.textContent=original;btn.classList.remove("done");},1400)};if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done).catch(fallback)}else fallback();function fallback(){const ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);ta.select();document.execCommand("copy");document.body.removeChild(ta);done()}}
document.addEventListener("click",e=>{const b=e.target.closest("[data-copy]");if(b)copyText(decodeURIComponent(b.dataset.copy),b)});
function match(obj,fields){if(!q)return true;const hay=fields.map(f=>Array.isArray(obj[f])?obj[f].join(" "):(obj[f]||"")).join(" ").toLowerCase();return hay.includes(q.toLowerCase())}
function cats(){if(tab==="skills")return["全部",...new Set(DATA.skills.map(s=>s.category))];if(tab==="prompts")return["全部",...new Set(DATA.prompts.filter(p=>(p.flow||"common")===flowMode).map(p=>p.category).filter(Boolean))];return[]}
function renderLaunchTip(){const tip=document.getElementById("launchTip");if(!tip)return;const isFile=location.protocol==="file:";if(!isFile){tip.innerHTML="";return}tip.innerHTML=`<div class="launch-tip"><b>目前是直接用書籤／檔案打開控制台</b><div class="summary">這種開法只會打開 <code>index.html</code>，不會先執行「更新並開啟控制台.command」或 <code>python3 scripts/build.py</code>。如果你希望每次都先更新再開頁面，請改用桌面的 <code>二刀流開發助手控制台.command</code>，或在這個專案資料夾裡雙擊 <code>更新並開啟控制台.command</code>。</div></div>`}
function renderOnlineBanner(){const el=document.getElementById("onlineBanner");if(!el)return;const isOnline=/\.github\.io$/i.test(location.hostname);if(!isOnline){el.innerHTML="";return}el.innerHTML=`<div class="online-banner"><div class="grow"><b>這是公開展示版，已改成新手也能上手的 AI 外掛系統</b><div class="summary">這裡可以直接看介面、複製提示詞、理解安裝流程與外掛怎麼搭配使用。頁面裡的範例進度、AGENTS、PRD 主要是示意用途，幫助第一次接觸的人先看懂整套工作方式。</div><div class="summary" style="margin-top:6px">這是要給第一次安裝使用者用的提示詞複製自動安裝功能。你先下載到自己電腦，再複製提示詞交給 Codex 或 Claude Code，自動安裝完整版系統。安裝完成後，控制台主資料夾預設會在 <code>~/Documents/CodexClaudeSkillsConsole</code>（macOS）或 <code>我的文件\\CodexClaudeSkillsConsole</code>（Windows），之後你可以直接改裡面的 <code>data/prompts.yaml</code>、<code>data/skills.yaml</code> 來客製自己的流程。</div></div><button type="button" data-tab-jump="installGuide">下載到自己電腦</button></div>`;el.querySelector("[data-tab-jump]")?.addEventListener("click",()=>setTab("installGuide"))}
function renderIntro(){const promptExtra=tab==="prompts"?promptLibraryCaptureBlock():"";const skillExtra=tab==="skills"?skillLibraryCaptureBlock():"";const info=PAGE_INTROS[tab];const extra=skillExtra||promptExtra;document.getElementById("pageIntro").innerHTML=`<h2>${esc(info.title)}</h2><div class="lead">${esc(info.lead)}</div><div class="intro-grid"><div class="intro-item"><div class="intro-label">用途</div><div class="intro-text">${esc(info.purpose)}</div></div><div class="intro-item"><div class="intro-label">先做</div><div class="intro-text">${esc(info.first)}</div></div><div class="intro-item"><div class="intro-label">適合情境</div><div class="intro-text">${esc(info.when)}</div></div></div>${extra}`;if(tab==="skills"||tab==="prompts")bindCapture()}
function homePrompt(title,fallback){return DATA.prompts.find(p=>p.title===title)?.prompt||fallback}
function promptInfoByTitle(title,fallback=""){const found=DATA.prompts.find(p=>p.title===title);return{prompt:found?found.prompt:fallback,targetPrompt:found?promptKey(found):"",found:!!found}}
function homeHtml(){const guardianInstalled=!!QUOTA_GUARDIAN_STATUS.installed;const guardianStatusText=guardianInstalled?"這台電腦已偵測到配額守門員可用，可直接開啟。":"這台電腦尚未完成配額守門員安裝；先複製安裝提示詞，交給任一個 AI 幫你裝起來。";const claudeQuotaText=QUOTA_GUARDIAN_STATUS.claudeStatusText||"";const claudeNeedsWake=QUOTA_GUARDIAN_STATUS.statuslineReady&&!QUOTA_GUARDIAN_STATUS.claudeLiveReady;const wakeClaudeButton=claudeNeedsWake?`<button class="copy-btn" type="button" data-wake-ai="claude" data-wake-prompt="${encodeURIComponent(QUOTA_GUARDIAN_STATUS.claudeWakePrompt)}">喚醒 Claude Code</button>`:"";const wakeHint=claudeNeedsWake?`<div class="summary" style="margin-top:6px">若 Claude 還沒刷新即時配額，下面會出現喚醒按鈕，按下後會先幫你複製提示詞並切到 Claude Code。</div>`:"";const guardianAction=guardianInstalled?`<button class="copy-btn tutorial-btn guardian-launch-btn" type="button" data-open-quota-guardian="1">開啟配額守門員</button>`:`<button class="copy-btn" type="button" data-copy="${encodeURIComponent(QUOTA_GUARDIAN_STATUS.installPrompt)}">安裝配額守門員提示詞</button>`;const guardianCards=guardianInstalled?`<div class="guardian-kpis"><div class="home-kpi"><b>開啟後會做什麼</b><div class="summary">直接叫出桌面浮動視窗，開始顯示 Codex / Claude Code 的本輪與本週限制資訊。</div></div><div class="home-kpi"><b>Claude 目前狀態</b><div class="summary">${claudeQuotaText}</div></div></div>`:`<div class="guardian-kpis"><div class="home-kpi"><b>安裝後會有什麼</b><div class="summary">AI 會幫你補齊啟動檔、浮動窗、配額監看與自動提醒設定，之後就能直接從這頁開啟。</div></div><div class="home-kpi"><b>這個提示詞怎麼用</b><div class="summary">按一下複製後，貼給任一個 AI，它會依目前這台電腦的狀態直接幫你裝起來。</div></div></div>`;return`<div class="wide-sop"><div class="home-hero"><h2>把 AI 外掛系統整理成新手也能直接上手的控制台</h2><p>這一頁不講太多技術名詞，先幫你把工具安裝、外掛開啟、提示詞使用和接續專案的入口整理好。你只要照順序點進去，就能比較安心地開始使用。</p><div class="summary" style="margin-top:10px">如果你是第一次接觸 AI 開發，我會比較推薦先從 <b>Codex Pro</b> 版本開始慢慢摸熟。先習慣怎麼和 AI 對話、怎麼下任務、怎麼看它回覆的規劃與修改建議，之後你才會越來越懂 AI agent 到底可以幫你做到哪裡。</div><div class="summary" style="margin-top:10px">這套控制台也是我累積大約五年的 AI 使用經驗，一邊實作、一邊整理，慢慢寫出來的外掛系統。目的不是讓你一次學會全部，而是讓新手也能先用起來，再慢慢理解每個工具在幫什麼。</div><div class="home-actions" style="margin-top:14px"><button class="copy-btn" type="button" data-home-tab="installGuide">先看安裝教學</button><button class="copy-btn" type="button" data-home-tab="skills">我想找外掛 / Skill</button><button class="copy-btn" type="button" data-home-tab="prompts">我要複製提示詞</button><button class="copy-btn" type="button" data-home-tab="progress">我正在接續專案</button></div><div class="home-kpis"><div class="home-kpi"><b>新手先做什麼</b><div class="summary">先把 Codex 或 Claude Code 裝好，再把常用外掛打開。</div></div><div class="home-kpi"><b>這套系統在幫什麼</b><div class="summary">幫你把安裝、外掛、提示詞與工作流程整理成看得懂的步驟。</div></div><div class="home-kpi"><b>使用原則</b><div class="summary">先用會用到的，不用第一天就把全部功能研究完。</div></div></div></div><div class="home-panel" style="margin:16px 0"><h3>我們開發的配額守門員</h3><div class="summary">這個功能會固定幫你看 Codex 和 Claude Code 現在還剩多少可用額度，並在快碰到限制前先提醒你不要再往下開大任務。</div><div class="summary" style="margin-top:8px">你按下開啟後，桌面會跳出浮動小視窗，直接顯示兩個 AI 的本輪與本週狀態；如果其中一個顯示限制休息中，就代表它現在不能繼續用，會同時標出下次可再使用的時間。</div><div class="summary" style="margin-top:8px">提醒規則現在是：本輪和本週都用同一套分級。剩 45% 先提醒開始整理進度；剩 30% 到 10% 時，改成提醒你準備交接摘要、停止再開新任務，優先收尾；低於或等於 10% 時就直接自動準備下一位 AI 的最終交接提示詞。</div><div class="summary" style="margin-top:8px"><b>目前狀態：</b>${guardianStatusText}</div><div class="summary" style="margin-top:6px"><b>Claude 配額：</b>${claudeQuotaText}</div>${wakeHint}<div class="home-panel-actions guardian-actions" style="margin-top:12px">${guardianAction}${wakeClaudeButton}</div>${guardianCards}</div><div class="home-panel" style="margin:16px 0"><h3>新手最簡單的使用順序</h3><div class="summary">第 1 步先看「安裝教學」把桌面版與常用外掛準備好 → 第 2 步到「提示詞庫」或「Skill庫」找現在要用的內容 → 第 3 步真的進入工作時，再用「開發進度」接續專案。</div><div class="summary" style="margin-top:8px">如果你現在只是想先試試看怎麼和 AI 開口，可以先跳到「日常提示詞」。</div></div><div class="home-steps"><div class="home-step"><span class="num">1</span><h3>先把工具和外掛準備好</h3><div class="summary">到安裝教學看你要用 Codex 還是 Claude Code，照著步驟下載、登入，然後把需要的官方外掛或 VS Code 模組開起來。</div></div><div class="home-step"><span class="num">2</span><h3>再找現在要用的內容</h3><div class="summary">想直接交辦事情，就去提示詞庫；想找可搭配的功能，就去 Skill 庫。你不用全部看完，只找目前會用到的就好。</div></div><div class="home-step"><span class="num">3</span><h3>最後再接實際工作</h3><div class="summary">當你要真的接續專案、查目前做到哪裡、交給下一個 AI 或自己繼續做時，再進開發進度頁就可以。</div></div></div><div class="home-stack"><div class="home-panel"><h3>這套系統幫你精簡了什麼</h3><div class="mini-list"><div class="mini-item"><b>安裝更簡單</b><div class="summary">把下載入口、登入順序、外掛開啟方式集中在同一頁，不用自己東找西找。</div></div><div class="mini-item"><b>外掛更好懂</b><div class="summary">先從最常用、名字最好懂的外掛開始，不再一開始就塞滿一大堆工具。</div></div><div class="mini-item"><b>提示詞可直接複製</b><div class="summary">不知道怎麼下指令時，直接複製控制台裡整理好的提示詞交給 AI。</div></div><div class="mini-item"><b>專案可接續</b><div class="summary">真的進入工作後，再用開發進度看現在做到哪裡，減少中途斷線。</div></div></div></div><div class="home-panel"><h3>每一頁在做什麼</h3><div class="mini-list"><div class="mini-item"><b>安裝教學</b><div class="summary">教你怎麼下載、登入、開外掛，適合第一次接觸的人。</div></div><div class="mini-item"><b>日常提示詞</b><div class="summary">整理最常用的 AI 問法，讓你不知道怎麼開口時可以直接複製。</div></div><div class="mini-item"><b>提示詞庫</b><div class="summary">把比較完整的工作提示詞整理在一起，適合拿來正式交辦任務。</div></div><div class="mini-item"><b>Skill 庫</b><div class="summary">看有哪些外掛、技能或工作模組可以搭配使用，知道它們各自幫什麼。</div></div><div class="mini-item"><b>開發進度</b><div class="summary">你已經有正在做的專案時，用來接手、交接與確認目前做到哪裡。</div></div><div class="mini-item"><b>備份 / 還原</b><div class="summary">用提示詞把目前設定一鍵備份到自己的 GitHub，再用另一段提示詞還原到任何一台 Mac 或 Windows。</div></div></div></div></div></div>`}
async function openQuotaGuardian(btn){const original=btn.textContent;btn.disabled=true;btn.textContent="開啟中...";try{const res=await fetch("/api/open-quota-guardian",{method:"POST"});if(!res.ok)throw new Error(`HTTP ${res.status}`);const data=await res.json();if(!data.ok)throw new Error(data.error||"open_failed");btn.textContent="已開啟";setTimeout(()=>{btn.textContent=original;btn.disabled=false;},1600)}catch(err){btn.textContent="開啟失敗";setTimeout(()=>{btn.textContent=original;btn.disabled=false;},2200)}}
async function wakeAI(btn){const original=btn.textContent;const prompt=decodeURIComponent(btn.dataset.wakePrompt||"");const target=btn.dataset.wakeAi||"";btn.disabled=true;btn.textContent="啟動中...";try{const res=await fetch("/api/wake-ai",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target,prompt})});if(!res.ok)throw new Error(`HTTP ${res.status}`);const data=await res.json();if(!data.ok)throw new Error(data.error||"wake_failed");btn.textContent="已切換";setTimeout(()=>{btn.textContent=original;btn.disabled=false;},1600)}catch(err){copyText(prompt,btn);btn.textContent="已複製";setTimeout(()=>{btn.textContent=original;btn.disabled=false;},1600)}}
function bindHome(){document.querySelectorAll("[data-home-tab]").forEach(btn=>btn.onclick=()=>setTab(btn.dataset.homeTab));document.querySelectorAll("[data-open-quota-guardian]").forEach(btn=>btn.onclick=()=>openQuotaGuardian(btn));document.querySelectorAll("[data-wake-ai]").forEach(btn=>btn.onclick=()=>wakeAI(btn))}
function dailyCardId(sectionIndex,cardIndex){return`${sectionIndex}-${cardIndex}`}
function dailyFindCard(cardId){for(let sectionIndex=0;sectionIndex<DAILY_PROMPT_SECTIONS.length;sectionIndex+=1){const section=DAILY_PROMPT_SECTIONS[sectionIndex];for(let cardIndex=0;cardIndex<(section.cards||[]).length;cardIndex+=1){const card=section.cards[cardIndex];if(dailyCardId(sectionIndex,cardIndex)===cardId)return{section,sectionIndex,card,cardIndex}}}return null}
function dailyQuestionList(card){return[...(card.questions||[]),...DAILY_COMMON_QUESTIONS]}
function dailyAnswerEntry(questionId){return dailyWizardState.answers?.[questionId]||{choice:"",text:""}}
function dailyAnswerLabel(question){const answer=dailyAnswerEntry(question.id);if(question.type==="choice"){if(answer.choice&&answer.text.trim())return`${answer.choice} / 補充：${answer.text.trim()}`;return answer.choice||answer.text.trim()||"未填寫"}return answer.text.trim()||"未填寫"}
function builtPromptMissingBlock(questions,answerLabelFn){const missingQuestions=questions.filter(question=>answerLabelFn(question)==="未填寫");return missingQuestions.length?`\n\n目前仍未填寫的欄位：\n${missingQuestions.map(question=>`- ${question.label}`).join("\n")}\n\n處理規則：\n1. 先不要跳過這些欄位。\n2. 請先逐題追問我，直到這些欄位可以補齊。\n3. 問完後，請把我補充的答案填回原始提示詞與對應欄位。\n4. 如果這張提示詞的任務是建立或更新專案資料夾、AGENTS.md、PRD.md、README.md 或其他 .md 檔，請在內容確認後，把補齊後的資訊一併寫入對應檔案。`:"\n\n目前欄位已足夠，若還有模糊處，再用最少問題補問後直接執行。"}
function dailyChoiceButton(question,option){const active=dailyAnswerEntry(question.id).choice===option?" active":"";return`<button class="daily-choice-btn${active}" type="button" data-daily-choice="${esc(question.id)}" data-choice-value="${esc(option)}">${esc(option)}</button>`}
function dailyQuestionHtml(question){const answer=dailyAnswerEntry(question.id);const inputTag=question.type==="textarea"?"textarea":"input";const inputClass=question.type==="textarea"?"daily-modal-textarea":"daily-modal-input";const inputAttrs=question.type==="textarea"?`placeholder="${esc(question.placeholder||"可留空，之後再補")}"`:`type="text" value="${esc(answer.text)}" placeholder="${esc(question.placeholder||"可留空，之後再補")}"`;const inputBody=question.type==="textarea"?`<textarea class="${inputClass}" data-daily-text="${esc(question.id)}" placeholder="${esc(question.placeholder||"可留空，之後再補")}">${esc(answer.text)}</textarea>`:`<input class="${inputClass}" data-daily-text="${esc(question.id)}" ${inputAttrs}>`;return`<div class="daily-modal-question"><div class="daily-modal-step">逐題整理需求</div><h4>${esc(question.label)}</h4>${question.type==="choice"?`<div class="daily-choice-grid">${(question.options||[]).map(option=>dailyChoiceButton(question,option)).join("")}</div>`:""}${inputBody}</div>`}
function dailyBuiltPrompt(card){const questions=dailyQuestionList(card);const questionLines=questions.map(question=>`- ${question.label}：${dailyAnswerLabel(question)}`).join("\n");const missingBlock=builtPromptMissingBlock(questions,dailyAnswerLabel);return`請先根據下面這些回答整理需求，不要直接忽略空白欄位。若資訊不足，先用最少問題補問，再執行後面的原始提示詞。${missingBlock}\n\n卡片：${card.title}\n適用情境：${card.when}\n\n使用者回答：\n${questionLines}\n\n原始提示詞：\n${card.prompt}`}
function dailyWizardHtml(){if(!dailyWizardState.cardId)return"";const meta=dailyFindCard(dailyWizardState.cardId);if(!meta)return"";const {card}=meta;const questions=dailyQuestionList(card);const previewStep=questions.length;const step=Math.min(dailyWizardState.step,previewStep);if(step>=previewStep){const prompt=dailyBuiltPrompt(card);return`<div class="daily-modal" id="dailyWizard"><div class="daily-modal-backdrop" data-daily-close="1"></div><div class="daily-modal-card"><div class="daily-modal-head"><div><div class="daily-modal-step">完成自動生成提示詞</div><div class="daily-modal-title">${esc(card.title)}</div><div class="summary">${esc(card.when)}</div></div><button class="daily-modal-close" type="button" data-daily-close="1">關閉</button></div><div class="daily-modal-body"><div class="daily-modal-preview"><div class="summary"><b>這就是要交給 AI 的最終提示詞</b></div><pre class="prompt-body" id="dailyWizardPrompt">${esc(prompt)}</pre></div><div class="daily-modal-actions"><div class="group"><button class="copy-btn secondary-btn" type="button" data-daily-back="1">回上一題</button></div><div class="group"><button class="copy-btn" type="button" id="dailyWizardCopy" data-copy="${encodeURIComponent(prompt)}">複製自動生成提示詞</button></div></div></div></div></div>`}const question=questions[step];return`<div class="daily-modal" id="dailyWizard"><div class="daily-modal-backdrop" data-daily-close="1"></div><div class="daily-modal-card"><div class="daily-modal-head"><div><div class="daily-modal-step">第 ${step+1} 題 / 共 ${questions.length} 題</div><div class="daily-modal-title">${esc(card.title)}</div><div class="summary">${esc(card.when)}</div></div><button class="daily-modal-close" type="button" data-daily-close="1">關閉</button></div><div class="daily-modal-body">${dailyQuestionHtml(question)}<div class="daily-modal-actions"><div class="group">${step>0?`<button class="copy-btn secondary-btn" type="button" data-daily-back="1">上一題</button>`:""}<button class="copy-btn secondary-btn" type="button" data-daily-close="1">先關閉</button></div><div class="group"><button class="copy-btn" type="button" data-daily-next="1">${step===questions.length-1?"完成並自動生成提示詞":"下一題"}</button></div></div></div></div></div>`}
function dailyPromptCard(card,sectionIndex,cardIndex){const cardId=dailyCardId(sectionIndex,cardIndex);return`<div class="daily-card"><h4>${esc(card.title)}</h4><div class="usage">${esc(card.when)}</div><pre class="prompt-body">${esc(card.prompt)}</pre><div class="daily-card-actions"><button class="copy-btn" type="button" data-daily-open="${esc(cardId)}">開始互動式自動生成提示詞</button></div></div>`}
function dailyModeButtons(){const modes=["全部",...DAILY_PROMPT_SECTIONS.map(section=>section.title)];return`<div class="flow-switch">${modes.map(mode=>`<button class="flow-btn ${dailyMode===mode?"active":""}" onclick="dailyMode='${esc(mode)}';render()">${esc(mode)}</button>`).join("")}</div>`}
function dailyHtml(){const sections=DAILY_PROMPT_SECTIONS.map((section,sectionIndex)=>({...section,__sectionIndex:sectionIndex})).filter(section=>dailyMode==="全部"||section.title===dailyMode);return`<div class="wide-sop"><div class="daily-hero"><h2>日常工作不知道怎麼問，就先從這裡開始</h2><p>這頁改成互動式自動生成提示詞。你先點卡片，系統會用小視窗一題一題讓你選擇或補充需求，最後再自動組成可直接貼給 Codex 或 Claude Code 的提示詞。</p><div class="daily-principles"><div class="daily-principle"><b>先講目的</b><div class="summary">告訴 AI 你想完成什麼，不只是丟一堆資料。</div></div><div class="daily-principle"><b>先看再做</b><div class="summary">要求 AI 先分析、先規劃，確認後再修改。</div></div><div class="daily-principle"><b>重要檔案先保護</b><div class="summary">涉及電腦檔案時，先備份、先列計畫，不直接動檔。</div></div></div></div>${dailyModeButtons()}${sections.map(section=>`<section class="daily-section"><div class="daily-section-head"><div><h3>${esc(section.title)}</h3><div class="summary">${esc(section.hint)}</div></div>${section.safety?`<div class="daily-safety">${esc(section.safety)}</div>`:""}</div><div class="daily-grid">${section.cards.map((card,cardIndex)=>dailyPromptCard(card,section.__sectionIndex,cardIndex)).join("")}</div></section>`).join("")}${dailyWizardHtml()}</div>`}
function bindDaily(){document.querySelectorAll("[data-daily-mode]").forEach(btn=>btn.onclick=()=>{dailyMode=btn.dataset.dailyMode;render()});document.querySelectorAll("[data-daily-open]").forEach(btn=>btn.onclick=()=>{dailyWizardState={cardId:btn.dataset.dailyOpen||"",step:0,answers:{}};render()});document.querySelectorAll("[data-daily-close]").forEach(btn=>btn.onclick=()=>{dailyWizardState={cardId:"",step:0,answers:{}};render()});document.querySelectorAll("[data-daily-choice]").forEach(btn=>btn.onclick=()=>{const id=btn.dataset.dailyChoice||"";const prev=dailyAnswerEntry(id);dailyWizardState.answers[id]={...prev,choice:btn.dataset.choiceValue||""};render()});document.querySelectorAll("[data-daily-text]").forEach(el=>el.oninput=()=>{const id=el.dataset.dailyText||"";const prev=dailyAnswerEntry(id);dailyWizardState.answers[id]={...prev,text:el.value||""}});document.querySelectorAll("[data-daily-back]").forEach(btn=>btn.onclick=()=>{dailyWizardState.step=Math.max(0,dailyWizardState.step-1);render()});document.querySelectorAll("[data-daily-next]").forEach(btn=>btn.onclick=()=>{const meta=dailyFindCard(dailyWizardState.cardId);if(!meta)return;const total=dailyQuestionList(meta.card).length;dailyWizardState.step=Math.min(total,dailyWizardState.step+1);render()})}
const PROMPT_WIZARD_QUESTIONS=[{id:"goal",label:"你這次最想讓 AI 幫你做什麼？",type:"choice",options:["先幫我釐清需求","先幫我規劃步驟","直接幫我產出內容","先幫我檢查風險或問題"],placeholder:"可補充這次真正要完成的目標"},{id:"materials",label:"你現在手上有什麼資料？",type:"choice",options:["我已經有完整資料","我只有部分資料","我只有一個模糊想法","我要 AI 先告訴我還缺什麼"],placeholder:"可補充檔案、網址、背景或限制"},{id:"style",label:"你希望 AI 先怎麼做？",type:"choice",options:["先問我關鍵問題","先看內容再規劃","先列風險再動手","直接做初版給我看"],placeholder:"可補充你偏好的互動方式"},{id:"limits",label:"這次有沒有不能碰的限制？",type:"choice",options:["先不要直接改檔","先不要安裝或部署","先不要刪東西","沒有，先做初版"],placeholder:"可補充任何風險、限制或驗收標準"}];
function promptFindByKey(key){return DATA.prompts.find(p=>promptKey(p)===key)||null}
function promptPlaceholderStructuredLabel(beforeText){const equalsLabel=beforeText.match(/(?:^|[，。、；;：:]\s*)([^【：:=\n]+?)\s*=\s*$/);if(equalsLabel?.[1])return equalsLabel[1].trim();const colonLabel=beforeText.match(/(?:^|[，。、；;]\s*)([^【：:\n=]+?)\s*[：:]\s*$/);if(colonLabel?.[1])return colonLabel[1].trim();return""}
function promptPlaceholderLabel(beforeText,rawValue,lineIndex,matchIndex){const structuredLabel=promptPlaceholderStructuredLabel(beforeText);if(structuredLabel)return structuredLabel.replace(/^[\s\-*•]+/,"").replace(/^\d+[.)、]\s*/,"").trim();return rawValue||`欄位${lineIndex+1}-${matchIndex+1}`}
function promptPlaceholderOptions(rawValue,hasStructuredLabel){if(!hasStructuredLabel||!/\s\/\s/.test(rawValue))return[];const parts=rawValue.split("/").map(option=>option.trim()).filter(Boolean);if(parts.length<2||parts.length>8)return[];return parts.every(option=>option.length<=16)?parts:[]}
function promptPlaceholderQuestions(promptItem){const seen=new Set();return(promptItem.prompt||"").split("\n").flatMap((line,lineIndex)=>Array.from(line.matchAll(/【([^】]*)】/g)).map((match,matchIndex)=>{const rawToken=match[0];const rawValue=(match[1]||"").trim();const beforeText=line.slice(0,match.index||0);const structuredLabel=promptPlaceholderStructuredLabel(beforeText);const fieldLabel=promptPlaceholderLabel(beforeText,rawValue,lineIndex,matchIndex);const dedupeKey=`${fieldLabel}::${rawToken}::${lineIndex}::${matchIndex}`;if(seen.has(dedupeKey))return null;seen.add(dedupeKey);const options=promptPlaceholderOptions(rawValue,!!structuredLabel);return{id:`placeholder_${lineIndex}_${matchIndex}`,label:fieldLabel,type:"text",placeholder:fieldLabel?`請輸入 ${fieldLabel}`:`請補充此欄位`,options,rawToken,lineIndex,matchIndex}}).filter(Boolean))}
function promptWizardQuestions(promptItem){return[...PROMPT_WIZARD_QUESTIONS,...promptPlaceholderQuestions(promptItem)]}
function promptWizardAnswerEntry(questionId){return promptWizardState.answers?.[questionId]||{choice:"",text:""}}
function promptWizardAnswerLabel(question){const answer=promptWizardAnswerEntry(question.id);if(answer.choice&&answer.text.trim())return`${answer.choice} / 補充：${answer.text.trim()}`;return answer.choice||answer.text.trim()||"未填寫"}
function promptWizardMissingQuestions(promptItem){return promptWizardQuestions(promptItem).filter(question=>promptWizardAnswerLabel(question)==="未填寫")}
function promptWizardChoiceButton(question,option){const active=promptWizardAnswerEntry(question.id).choice===option?" active":"";return`<button class="daily-choice-btn${active}" type="button" data-prompt-choice="${esc(question.id)}" data-choice-value="${esc(option)}">${esc(option)}</button>`}
function promptWizardQuestionHtml(question){const answer=promptWizardAnswerEntry(question.id);const choiceGrid=question.options?.length?`<div class="daily-choice-grid">${question.options.map(option=>promptWizardChoiceButton(question,option)).join("")}</div>`:"";return`<div class="daily-modal-question"><div class="daily-modal-step">逐題選擇需求</div><h4>${esc(question.label)}</h4>${choiceGrid}<input class="daily-modal-input" data-prompt-text="${esc(question.id)}" type="text" value="${esc(answer.text)}" placeholder="${esc(question.placeholder||"可留空，之後再補")}"></div>`}
function promptWizardFilledPrompt(promptItem){const lines=(promptItem.prompt||"").split("\n");const placeholderGroups=new Map();promptPlaceholderQuestions(promptItem).forEach(question=>{if(typeof question.lineIndex!=="number"||typeof question.matchIndex!=="number")return;const key=String(question.lineIndex);const existing=placeholderGroups.get(key)||[];existing.push(question);placeholderGroups.set(key,existing)});placeholderGroups.forEach((questions,key)=>{const lineIndex=Number(key);const line=lines[lineIndex]||"";const matches=Array.from(line.matchAll(/【([^】]*)】/g));if(!matches.length)return;const replacements=new Map();questions.forEach(question=>{const answer=promptWizardAnswerEntry(question.id);const value=(answer.text||"").trim()||answer.choice||"";if(value)replacements.set(question.matchIndex,value)});if(!replacements.size)return;let rebuilt="";let cursor=0;matches.forEach((match,idx)=>{const start=match.index||0;const token=match[0];rebuilt+=line.slice(cursor,start);rebuilt+=replacements.has(idx)?replacements.get(idx):token;cursor=start+token.length});rebuilt+=line.slice(cursor);lines[lineIndex]=rebuilt});return lines.join("\n")}
function promptWizardBuiltPrompt(promptItem){const questions=promptWizardQuestions(promptItem);const questionLines=questions.map(question=>`- ${question.label}：${promptWizardAnswerLabel(question)}`).join("\n");const missingBlock=builtPromptMissingBlock(questions,promptWizardAnswerLabel);return`請先根據下面這些回答理解我的需求，不要直接忽略空白欄位。若資訊不足，先用最少問題補問，再執行後面的原始提示詞。${missingBlock}\n\n提示詞標題：${promptItem.title}\n用途：${promptItem.usage||"未填寫"}\n分類：${promptItem.category||"未分類"}\n\n使用者回答：\n${questionLines}\n\n原始提示詞：\n${promptWizardFilledPrompt(promptItem)}`}
function promptWizardHtml(){if(!promptWizardState.promptKey)return"";const promptItem=promptFindByKey(promptWizardState.promptKey);if(!promptItem)return"";const questions=promptWizardQuestions(promptItem);const previewStep=questions.length;const step=Math.min(promptWizardState.step,previewStep);if(step>=previewStep){const prompt=promptWizardBuiltPrompt(promptItem);return`<div class="daily-modal" id="promptWizard"><div class="daily-modal-backdrop" data-prompt-close="1"></div><div class="daily-modal-card"><div class="daily-modal-head"><div><div class="daily-modal-step">完成自動生成提示詞</div><div class="daily-modal-title">${esc(promptItem.title)}</div><div class="summary">${esc(promptItem.usage||"這張提示詞卡片")}</div></div><button class="daily-modal-close" type="button" data-prompt-close="1">關閉</button></div><div class="daily-modal-body"><div class="daily-modal-preview"><div class="summary"><b>這就是要交給 AI 的最終提示詞</b></div><pre class="prompt-body" id="promptWizardPrompt">${esc(prompt)}</pre></div><div class="daily-modal-actions"><div class="group"><button class="copy-btn secondary-btn" type="button" data-prompt-back="1">回上一題</button></div><div class="group"><button class="copy-btn" type="button" id="promptWizardCopy" data-copy="${encodeURIComponent(prompt)}">複製自動生成提示詞</button></div></div></div></div></div>`}const question=questions[step];return`<div class="daily-modal" id="promptWizard"><div class="daily-modal-backdrop" data-prompt-close="1"></div><div class="daily-modal-card"><div class="daily-modal-head"><div><div class="daily-modal-step">第 ${step+1} 題 / 共 ${questions.length} 題</div><div class="daily-modal-title">${esc(promptItem.title)}</div><div class="summary">${esc(promptItem.usage||"這張提示詞卡片")}</div></div><button class="daily-modal-close" type="button" data-prompt-close="1">關閉</button></div><div class="daily-modal-body">${promptWizardQuestionHtml(question)}<div class="daily-modal-actions"><div class="group">${step>0?`<button class="copy-btn secondary-btn" type="button" data-prompt-back="1">上一題</button>`:""}<button class="copy-btn secondary-btn" type="button" data-prompt-close="1">先關閉</button></div><div class="group"><button class="copy-btn" type="button" data-prompt-next="1">${step===questions.length-1?"完成並自動生成提示詞":"下一題"}</button></div></div></div></div></div>`}
function bindPromptLibrary(){document.querySelectorAll("[data-prompt-open]").forEach(btn=>btn.onclick=()=>{promptWizardState={promptKey:btn.dataset.promptOpen||"",step:0,answers:{}};render()});document.querySelectorAll("[data-prompt-close]").forEach(btn=>btn.onclick=()=>{promptWizardState={promptKey:"",step:0,answers:{}};render()});document.querySelectorAll("[data-prompt-choice]").forEach(btn=>btn.onclick=()=>{const id=btn.dataset.promptChoice||"";const prev=promptWizardAnswerEntry(id);promptWizardState.answers[id]={...prev,choice:btn.dataset.choiceValue||""};render()});document.querySelectorAll("[data-prompt-text]").forEach(el=>el.oninput=()=>{const id=el.dataset.promptText||"";const prev=promptWizardAnswerEntry(id);promptWizardState.answers[id]={...prev,text:el.value||""}});document.querySelectorAll("[data-prompt-back]").forEach(btn=>btn.onclick=()=>{promptWizardState.step=Math.max(0,promptWizardState.step-1);render()});document.querySelectorAll("[data-prompt-next]").forEach(btn=>btn.onclick=()=>{const promptItem=promptFindByKey(promptWizardState.promptKey);if(!promptItem)return;const total=promptWizardQuestions(promptItem).length;promptWizardState.step=Math.min(total,promptWizardState.step+1);render()})}
function skillCard(s){const triggers=(s.triggers||[]).map(t=>`<div class="trigger"><code>${esc(t)}</code><button class="copy-btn" data-copy="${encodeURIComponent(t)}">複製</button></div>`).join("");return`<div class="card"><h3>${esc(s.name)} <span class="badge ${riskCls[s.risk]||"low"}">${esc(s.risk)}風險</span> <span class="cat-tag">${esc(s.category)}</span></h3><div class="summary">${esc(s.summary)}</div>${s.notes?`<div class="notes">${esc(s.notes)}</div>`:""}${triggers}</div>`}
function stageLabel(p){if(!p.flow||!p.stage)return"通用";const meta=STAGE_META[p.flow]?.[p.stage];return meta?meta[0]:p.stage}
function promptKey(p){return `${p.flow||"common"}::${p.stage||""}::${p.title}`}
function promptCard(p){return`<div class="card" data-prompt-key="${esc(promptKey(p))}"><h3>${esc(p.title)} <span class="stage-tag">${esc(stageLabel(p))}</span> <span class="cat-tag">${esc(p.category)}</span></h3><div class="usage">${esc(p.usage)}</div><pre class="prompt-body">${esc(p.prompt)}</pre><button class="copy-btn" type="button" data-prompt-open="${esc(promptKey(p))}">開始互動式自動生成提示詞</button></div>`}
function comboPrompt(combo){const lines=[`以下是「${combo.title}」。`,combo.usage||"", ""];const missing=[];(combo.steps||[]).forEach((step,idx)=>{const prompt=DATA.prompts.find(p=>p.title===step.prompt_title);if(!prompt){missing.push(step.prompt_title);return}if(step.custom_intro)lines.push(step.custom_intro,"");lines.push(`--- Prompt ${idx+1}：${prompt.title} ---`,prompt.prompt,"")});if(missing.length)lines.unshift(`提醒：找不到以下提示詞，已略過：${missing.join("、")}`,"");return lines.join("\n").trim()}
function comboCard(combo){const missing=(combo.steps||[]).filter(step=>!DATA.prompts.some(p=>p.title===step.prompt_title)).map(step=>step.prompt_title);const steps=(combo.steps||[]).map(step=>`<li>${esc(step.prompt_title)}</li>`).join("");const text=comboPrompt(combo);return`<div class="combo-card"><h3>${esc(combo.title)} <span class="cat-tag">${esc(combo.category||"組合包")}</span></h3><div class="usage">${esc(combo.usage||"")}</div>${missing.length?`<div class="warning">缺少提示詞：${esc(missing.join("、"))}</div>`:""}<ol class="combo-steps">${steps}</ol><button class="copy-btn" data-copy="${encodeURIComponent(text)}">複製整包（${(combo.steps||[]).length} 張）</button></div>`}
function combosHtml(){const combos=DATA.combos||[];if(!combos.length)return"";return`<section class="flow-section"><div class="section-head"><h2>常用組合包</h2><span class="hint">一鍵複製常用流程</span></div><div class="combo-grid">${combos.map(comboCard).join("")}</div></section>`}
function workflowGuide(){if(flowMode==="dualai")return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">Codex</div><div class="guide-text">主力工程師：規劃、分段實作、測試、修正與延伸開發。</div></div><div class="guide-item"><div class="guide-label">Claude Code（VS Code）</div><div class="guide-text">審查員：看 diff、抓風險、提出 P0/P1/P2 問題與修改建議。</div></div></div>`;if(flowMode==="solo")return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">先規劃</div><div class="guide-text">讓單一 AI 先讀文件並列出做法。</div></div><div class="guide-item"><div class="guide-label">再實作</div><div class="guide-text">只做最小必要修改，避免一次改太大。</div></div><div class="guide-item"><div class="guide-label">要自檢</div><div class="guide-text">請 AI 用審查角度檢查結果。</div></div></div>`;return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">專案啟動</div><div class="guide-text">AGENTS、PRD、交接摘要與規劃模板。</div></div><div class="guide-item"><div class="guide-label">工程常用</div><div class="guide-text">Git、API、部署與資料庫模板。</div></div><div class="guide-item"><div class="guide-label">Skill 管理</div><div class="guide-text">新增 skill、資安檢查與提示詞收錄。</div></div></div>`}
function flowButtons(){return`<div class="flow-switch">${Object.entries(FLOW_META).map(([key,m])=>`<button class="flow-btn ${flowMode===key?"active":""}" data-flow="${key}">${m.label}</button>`).join("")}</div>`}
function promptLibraryCaptureBlock(){return`<details class="doc-fold skill-capture-fold"><summary><div class="doc-fold-title"><b>把新提示詞收進提示詞庫</b><span>新手版：貼上內容 → 複製提示詞 → 交給 Codex 幫你整理、收錄、重建。</span></div><span class="doc-fold-arrow">›</span></summary><div class="doc-fold-body"><div class="workflow-guide" style="margin:12px 0 14px"><div class="guide-item"><div class="guide-label">用途</div><div class="guide-text">看到好用提示詞時，不用自己整理 YAML，先用這裡產生交辦內容。</div></div><div class="guide-item"><div class="guide-label">先做</div><div class="guide-text">把標題、用途和提示詞原文補進去，其他格式交給 Codex 幫你收。</div></div><div class="guide-item"><div class="guide-label">結果</div><div class="guide-text">複製提示詞後，Codex 會把內容收進提示詞庫並重建頁面。</div></div></div>${captureHtml("prompt",false)}</div></details>`}
function renderPromptFlow(){const visible=DATA.prompts.filter(p=>(p.flow||"common")==="common"&&(cat==="全部"||p.category===cat)&&match(p,["title","usage","category","prompt","flow","stage"]));if(!visible.length)return`<div class="empty">找不到符合條件的提示詞。</div>${promptWizardHtml()}`;if(cat==="全部"){const groups=[...new Set(visible.map(p=>p.category))];return`${groups.map(group=>{const items=visible.filter(p=>p.category===group);return`<section class="flow-section"><div class="section-head"><h2>${esc(group)}</h2><span class="hint">${items.length} 則</span></div><div class="grid">${items.map(promptCard).join("")}</div></section>`}).join("")}${promptWizardHtml()}`}return`<div class="grid">${visible.map(promptCard).join("")}</div>${promptWizardHtml()}`}
function skillLibraryCaptureBlock(){return`<details class="doc-fold skill-capture-fold"><summary><div class="doc-fold-title"><b>把新 Skill 收進 Skill庫</b><span>新手版：貼上網址 → 複製提示詞 → 交給 Codex 幫你安檢、安裝、收錄。</span></div><span class="doc-fold-arrow">›</span></summary><div class="doc-fold-body"><div class="workflow-guide" style="margin:12px 0 14px"><div class="guide-item"><div class="guide-label">用途</div><div class="guide-text">看到新 Skill 時，不用自己整理格式，先用這裡產生交辦提示詞。</div></div><div class="guide-item"><div class="guide-label">先做</div><div class="guide-text">只要貼 GitHub URL 或本機資料夾路徑，其他欄位交給 Codex 幫你處理。</div></div><div class="guide-item"><div class="guide-label">結果</div><div class="guide-text">複製提示詞後，Codex 會先跑安檢；安全才安裝並收進 Skill庫。</div></div></div>${captureHtml("skill",false)}</div></details>`}
function renderSkillLibrary(){const items=DATA.skills.filter(s=>(cat==="全部"||s.category===cat)&&match(s,["name","summary","category","triggers","notes"]));return items.length?`<div class="grid">${items.map(skillCard).join("")}</div>`:`<div class="empty">找不到符合條件的 skill。</div>`}
function cmdRow(label,cmd){return`<div class="trigger"><div style="flex:1"><div class="usage">${esc(label)}</div><code>${esc(cmd)}</code></div><button class="copy-btn" data-copy="${encodeURIComponent(cmd)}">複製指令</button></div>`}
function installSteps(system){return`<div class="install-steps"><div class="install-step"><span>1</span><div>打開 ${esc(system)}</div></div><div class="install-step"><span>2</span><div>貼上剛剛複製的指令</div></div><div class="install-step"><span>3</span><div>按 Enter，等待安裝完成</div></div></div>`}
function installGuideTopicButton(topic,label){return`<button class="copy-btn tutorial-btn ${installGuideTopic===topic?"active":""}" type="button" data-install-guide-topic="${topic}">${label}</button>`}
function installGuideShot(title,pills,caption){return`<div class="shot-frame"><div class="shot-window"><div class="shot-toolbar"><span class="shot-dot"></span><span class="shot-dot"></span><span class="shot-dot"></span></div><div class="shot-body"><div class="summary"><b>${esc(title)}</b></div><div class="shot-line"></div><div class="shot-line mid"></div><div class="shot-pill-row">${pills.map(p=>`<span class="shot-pill">${esc(p)}</span>`).join("")}</div><div class="shot-line short"></div></div></div><div class="shot-caption">${esc(caption)}</div></div>`}
function installPromptCard(label,prompt){return`<button class="copy-btn" type="button" data-copy="${encodeURIComponent(prompt)}">${label}</button>`}
function installWakeCard(label,target,prompt){return`<button class="copy-btn tutorial-btn" type="button" data-wake-ai="${esc(target)}" data-wake-prompt="${encodeURIComponent(prompt)}">${label}</button>`}
function installPluginMiniGrid(items,title,summary){return`<div class="plugin-mini-section"><h3>${esc(title)}</h3><div class="summary">${esc(summary)}</div><div class="plugin-mini-grid">${items.map(item=>`<div class="plugin-mini-card"><div class="plugin-mini-icon">${item.iconSrc?`<img src="${esc(item.iconSrc)}" alt="${esc(item.title)}">`:esc(item.icon)}</div><div class="plugin-mini-copy"><div class="plugin-mini-title">${esc(item.title)}</div><div class="plugin-mini-desc">${esc(item.desc)}</div></div></div>`).join("")}</div></div>`}
function installGuideFigure(src,title,caption){return`<div class="manual-figure"><b>${esc(title)}</b><img src="${esc(src)}" alt="${esc(title)}"><div class="manual-caption">${esc(caption)}</div></div>`}
function installGuideMergedFigure(src1,src2,_cropTop,title,caption){return`<div class="manual-figure"><b>${esc(title)}</b><div class="manual-merged"><img src="${esc(src1)}" alt="${esc(title)}"><img src="${esc(src2)}" alt="${esc(title)}"></div><div class="manual-caption">${esc(caption)}</div></div>`}
function installGuideArticle(sections){return`<div class="install-article">${sections.map(section=>`<section class="install-article-section"><h3>${esc(section.title)}</h3>${section.body||""}${section.note?`<div class="install-article-note">${esc(section.note)}</div>`:""}</section>`).join("")}</div>`}
function installGuideTutorialHtml(){
  const codexPluginCards = [
    {icon:"D",iconSrc:INSTALL_GUIDE_ASSETS.iconDocuments,title:"Documents／文件",desc:"建立與編輯文件內容。"},
    {icon:"S",iconSrc:INSTALL_GUIDE_ASSETS.iconSpreadsheets,title:"Spreadsheets／試算表",desc:"整理資料表、欄位與數字。"},
    {icon:"P",iconSrc:INSTALL_GUIDE_ASSETS.iconPresentations,title:"Presentations／簡報",desc:"建立與修改投影片。"},
    {icon:"B",iconSrc:INSTALL_GUIDE_ASSETS.iconBrowser,title:"Browser／瀏覽器",desc:"控制內建瀏覽器檢查網站與畫面。"},
    {icon:"GH",iconSrc:INSTALL_GUIDE_ASSETS.iconGithub,title:"GitHub／程式碼庫",desc:"查看 repo、issue、PR 與 CI 狀態。"},
    {icon:"F",iconSrc:INSTALL_GUIDE_ASSETS.iconFigma,title:"Figma／設計稿",desc:"把設計稿和前端實作接起來。"},
    {icon:"DB",iconSrc:INSTALL_GUIDE_ASSETS.iconSupabase,title:"Supabase／資料庫",desc:"管理資料表、查詢資料與後端設定。"},
    {icon:"C",iconSrc:INSTALL_GUIDE_ASSETS.iconCanva,title:"Canva／設計工具",desc:"做設計圖、社群圖與視覺素材。"}
  ];
  const codexArticle = installGuideArticle([
    {
      title:"第一次使用 Codex，要先做這四件事",
      body:`<p>如果你是第一次使用 Codex，可以先照這個順序做，不用急著研究太多功能。先把 Codex 下載好、登入好，接著到 app 裡把常用的官方內建外掛程式打開，這樣後面使用起來會比較順。</p><ol><li>先下載 Codex app：按上面的 macOS 或 Windows 按鈕，先把最新版裝到電腦裡。</li><li>打開 Codex 並登入：用你的 ChatGPT 帳號登入，先進到 Codex 的主畫面。</li><li>到 app 裡打開官方內建外掛：進入後，到左側選單或設定裡找到 <b>Plugins</b>，這裡就是管理官方內建外掛程式的地方。</li><li>看到想用的外掛後，把右邊的開關打開：開關打開，就表示這個官方內建外掛已經裝好，可以直接使用。</li></ol>${installGuideFigure(INSTALL_GUIDE_ASSETS.codexPluginsOverview,"Codex Plugins 真實介面","這張就是你提供的真實畫面。第一次使用的人只要先找到 Plugins 頁面，再把想用的外掛右邊開關打開就可以了。")}`,
      note:"你可以把這一段理解成先把工作環境準備好，不是要你一開始就把所有工具都研究完。"
    },
    {
      title:"其他外掛程式什麼時候再開？",
      body:`<p>當你後面開始做設計、接 GitHub、查資料庫，或要做網站相關工作時，再回來把對應的外掛程式打開就可以了。像 Canva、Figma、GitHub、Hostinger、Supabase 這些，都比較適合等你真的用到時再補。</p>${installGuideFigure(INSTALL_GUIDE_ASSETS.codexPluginsExtra,"更多常見官方外掛","這一張補的是第二批比較常見的官方外掛。你不用第一天全部打開，等真的需要時再回來開就好。")}`,
      note:"最簡單的原則就是：現在會用到的先開，暫時用不到的先不要動。"
    },
    {
      title:"建議一起裝的必備 skill：LangGPT",
      body:`<p>如果你後面會自己做 prompt、設計職業型 skill，或想把工作流程整理成可重複使用的 AI 模板，建議把 <b>LangGPT</b> 一起裝起來。它的強項是把需求整理成固定結構，例如 Role、Profile、Goal、Skills、Rules、Workflow，讓 AI 比較容易穩定產出可重用的 skill。</p><p>這顆 skill 很適合搭配你現在這套控制台的「個人化設定」頁面一起使用，尤其是你要根據職業、行業別、痛點去生成 skill 時，效果會更完整。</p>`,
      note:"LangGPT 已經安裝到 Codex 與 Claude Code，系統裡的「外掛 / Skill庫」也看得到這顆 skill。"
    }
  ]);
  const claudeArticle = installGuideArticle([
    {
      title:"第一次使用 Claude Code，可以先照這個順序做",
      body:`<p>如果你想把 Claude Code 裝進 VS Code 使用，可以先照這個順序準備。先下載 Claude 桌面版，再下載 VS Code，最後到 VS Code 裡安裝 Claude Code extension，這樣之後做審查、補改和複審會比較順。</p><ol><li>先下載 Claude：按上面的 macOS 或 Windows 按鈕，進官方最新版下載入口。</li><li>再下載 VS Code：如果這台電腦還沒有 VS Code，就依系統下載對應版本。</li><li>打開 VS Code 並安裝 Claude Code extension：進到 Extensions，搜尋 <b>Claude Code</b>，安裝後登入，就可以開始使用。</li></ol>`,
      note:"這一段是桌面下載導向，不是在這裡直接做 CLI 安裝。"
    },
    {
      title:"Claude Code 比較適合什麼情境？",
      body:`<p>如果你習慣在 VS Code 裡工作，Claude Code 適合在編輯器側邊直接和專案一起做主力開發（規劃、實作、修正）。它很適合搭配 Codex 分工：Claude Code 偏向主力開發，Codex 偏向審查、複審與存檔收尾（Codex 終端機介面對新手最容易看出「哪裡要改」）。</p><p>簡單理解就是：你如果大多時間都待在 VS Code，想要在同一個編輯器裡直接和 AI 一起寫程式、改檔，這一套會比較順手。</p>`,
      note:"先把工具裝好、能正常登入使用就可以，不用一開始研究太多進階設定。"
    },
    {
      title:"建議一起安裝的 VS Code 模組",
      body:`<p>如果你準備把 Claude Code 放進 VS Code 一起使用，建議可以把常見會配合開發流程的模組一起裝好。這樣之後在同一個編輯器裡做開發、審查、除錯、遠端連線和版本管理會比較順。</p><p><b>建議優先安裝：</b>Claude Code for VS Code、Chinese (Traditional) Language Pack for Visual Studio Code、GitHub Pull Requests、PowerShell。</p><p><b>如果你會做 Python 開發：</b>Pylance、Python、Python Debugger、Python Environments。</p><p><b>如果你會用 Docker 或容器：</b>Dev Containers、Container Tools、Docker。</p><p><b>如果你常連遠端主機：</b>Remote Explorer、Remote - SSH、Remote - SSH: Editing Configuration Files。</p><p><b>其他常用補充：</b>vscode-pdf，方便直接在 VS Code 裡看 PDF。</p>${installGuideMergedFigure(INSTALL_GUIDE_ASSETS.vscodeInstalled1,INSTALL_GUIDE_ASSETS.vscodeInstalled2,520,"建議可搭配安裝的 VS Code 模組","這裡把你的模組畫面改成上下接續顯示，方便第一次設定的人直接照著名字去找、去安裝。")}<p>後面實際開發時，Claude Code 也可以依照你當下的需求，提醒你還缺哪些適合的模組；有些情況下，它也可以直接協助你把需要的模組安裝起來。</p>`,
      note:"最簡單的做法是：先裝 Claude Code、中文語系、GitHub、你會用到的語言工具，再依工作內容補 Docker 或遠端 SSH。"
    }
  ]);
  const topics = {
    codex: {
      badge: "Codex 安裝教學",
      title: "先把 Codex 裝好，再進工作區與 Plugins",
      lead: "這一段教第一次使用的人怎麼下載 Codex、登入、選專案資料夾，然後到 app 內把官方內建外掛程式打開。",
      steps: [],
      extras: codexArticle,
      shots: []
    },
    claude: {
      badge: "Claude Code 教學",
      title: "Claude 先下載，再補 VS Code 與 Claude Code extension",
      lead: "這一段改成桌面下載導向，不再先秀 CLI 指令。適合想在 VS Code 裡做審查、補改與複審的人。",
      steps: [],
      extras: claudeArticle,
      shots: []
    },
    system: {
      badge: "我們系統教學",
      title: "把我們的控制台與 skills 裝到自己的電腦",
      lead: "這一段改成提示詞導向。把提示詞複製給 Codex 或 Claude Code（VS Code），請它自動幫你下載、放到正確位置並回報安裝結果。",
      steps: [
        ["選要複製的提示詞","要整套控制台就複製完整版安裝提示詞；只想把系統裡整理好的 skills 全部裝進 Codex / Claude Code，就複製全部 skills 安裝提示詞。"],
        ["貼給 Codex 或 Claude Code","把提示詞貼給 Codex，或貼給 VS Code 裡的 Claude Code，讓它接手處理下載、檢查與安裝。"],
        ["完成後回來控制台接流程","安裝完成後，再回到這套控制台接著找提示詞、看 Skill庫、做開發進度交接。"]
      ],
      shots: [
        installGuideShot("用提示詞自動安裝",["Codex","Claude Code","自動處理"],"不是自己手動點一堆檔案，而是把提示詞交給 AI 幫你安裝。"),
        installGuideShot("安裝完成後的控制台",["提示詞庫","Skill庫","開發進度"],"完成安裝後，回到這套控制台就能直接接續日常工作流程。")
      ]
    }
  };
  const current = topics[installGuideTopic] || topics.codex;
  return `<div class="card install-tutorial-card"><div class="install-tutorial-head"><div><div class="install-tutorial-badge">${esc(current.badge)}</div><h2>${esc(current.title)}</h2><div class="summary">${esc(current.lead)}</div></div></div><div class="install-tutorial-grid ${current.shots.length?"":"full"}"><div>${current.steps.length?`<div class="install-tutorial-steps">${current.steps.map((step,idx)=>`<div class="install-tutorial-step"><span>${idx+1}</span><div><b>${esc(step[0])}</b><div class="summary">${esc(step[1])}</div></div></div>`).join("")}</div>`:""}${current.extras||""}</div>${current.shots.length?`<div class="install-tutorial-shot">${current.shots.join("")}</div>`:""}</div></div>`
}
function installGuideHtml(){const unifiedPrompt=`請幫我在目前這台電腦安裝這套完整版控制台系統，並自動判斷是 macOS 還是 Windows。\n\n要求：\n1. 自動判斷作業系統後，優先使用官方 install.sh 或 install.ps1。\n2. 把控制台與 skills 放到正確位置。\n3. 安裝完成後，白話告訴我控制台主資料夾在哪裡，方便我後續自己客製。\n4. 回報你下載了哪些檔案、放到哪裡、安裝是否成功。\n5. 如果遇到權限、Gatekeeper 或 PowerShell 執行政策問題，先告訴我再處理。\n\n安裝來源：\n- https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.sh\n- https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.ps1\n- https://github.com/kagenhsu/codex-claude-skills-backup/raw/main/codex-skills-backup.tar.gz\n\n安裝後請特別告訴我：\n- macOS 控制台主資料夾預設在 ~/Documents/CodexClaudeSkillsConsole\n- Windows 控制台主資料夾預設在 我的文件\\CodexClaudeSkillsConsole\n- 之後如果要客製系統，優先看 data/prompts.yaml、data/skills.yaml、index.html、scripts/serve_console.py`;const allSkillsPrompt=`請幫我在目前這台電腦安裝這個系統裡整理好的全部 skills，並自動判斷是 macOS 還是 Windows。\n\n要求：\n1. 先回報風險：會寫入哪些資料夾、是否可能和既有同名 skills 衝突、是否需要我先關閉 Codex 或 Claude Code。\n2. 下載最新版 skills 備份包：\n- https://github.com/kagenhsu/codex-claude-skills-backup/raw/main/codex-skills-backup.tar.gz\n3. 解壓後，把裡面的 skills 安裝到這兩個位置；沒有資料夾就建立，有同名目錄先提醒我再決定是否覆蓋：\n- ~/.codex/skills/\n- ~/.claude/skills/\n4. 只安裝 skills，不要順手改我的個人 prompts、專案檔案、git 設定或其他系統設定。\n5. 安裝完成後，列出實際安裝了哪些 skills、各自放到哪裡，以及哪些因為同名衝突而跳過。\n6. 最後提醒我要重新打開 Codex 或 Claude Code，讓新 skills 生效。\n7. 不要自動 commit、push，或刪除我原本的 skill。\n\n如果你判斷這台電腦已經完整下載整個 repo，也可以改用 repo 內現成的安裝方式處理，但前提仍然是：只安裝全部 skills，不要把其他不相關內容一起改掉。`;return`<div class="sop wide-sop"><div class="card install-hero"><h2>Codex / Claude Code 安裝與設定完整教學</h2><div class="summary">這頁專門給第一次接觸的人看。先把工具裝好、登入好、常用外掛 / skills 放好，再回到控制台照流程使用，會比直接亂裝穩很多。</div><div class="privacy-note">這一頁是教學頁，不會直接替你安裝任何東西。外部連結會帶你去官方文件；本控制台主要負責整理流程、提示詞與操作順序。</div></div><div class="install-grid"><div class="install-card featured"><h3>1. 安裝 Codex</h3><div class="install-subtitle">建議新手先從桌面版開始，再決定要不要補 IDE extension</div><div class="install-steps"><div class="install-step"><span>1</span><div>到官方頁下載 Codex app，安裝後打開。</div></div><div class="install-step"><span>2</span><div>用 ChatGPT 帳號登入，或依需求改用 OpenAI API key。</div></div><div class="install-step"><span>3</span><div>選一個專案資料夾，確認是本機模式，再開始第一個任務。</div></div></div><div class="summary">如果你主要在 VS Code、Cursor 或 Windsurf 工作，也可以再安裝 Codex extension，讓它直接出現在編輯器側欄。</div><div class="summary" style="margin-top:6px">如果你是 Intel Mac，請改用官方安裝頁選 Intel 版本。</div><div class="home-panel-actions"><a class="copy-btn" href="https://persistent.oaistatic.com/codex-app-prod/Codex.dmg" target="_blank" rel="noreferrer">下載最新 macOS 版</a><a class="copy-btn" href="https://get.microsoft.com/installer/download/9PLM9XGG6VKS?cid=website_cta_psi" target="_blank" rel="noreferrer">下載最新 Windows 版</a><button class="copy-btn tutorial-btn" type="button" data-install-guide-topic="codex">查看教學</button></div></div><div class="install-card featured"><h3>2. 安裝 Claude Code</h3><div class="install-subtitle">如果你習慣用 VS Code 審查、補改與複審，這一套很適合當第二支 AI</div><div class="summary">這裡改成直接走官方最新版下載入口：先裝 Claude，再補 VS Code，就能照這個控制台的分工流程使用。</div><div class="home-panel-actions"><a class="copy-btn" href="https://claude.com/download" target="_blank" rel="noreferrer">下載最新 macOS 版</a><a class="copy-btn" href="https://claude.ai/api/desktop/win32/x64/exe/latest/redirect" target="_blank" rel="noreferrer">下載最新 Windows 版</a></div><div class="home-panel-actions"><a class="copy-btn tutorial-btn" href="https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal" target="_blank" rel="noreferrer">下載 VS Code macOS 版</a><a class="copy-btn tutorial-btn" href="https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user" target="_blank" rel="noreferrer">下載 VS Code Windows 版</a></div><div class="home-panel-actions"><button class="copy-btn tutorial-btn" type="button" data-install-guide-topic="claude">查看教學</button></div><div class="summary">VS Code 裝好後，再照官方教學登入 Claude Code extension 即可。</div></div><div class="install-card"><h3>3. 安裝外掛 / skills</h3><div class="install-subtitle">工具裝好後，再補你真的會用到的能力，不要一開始全部裝滿</div><div class="summary"><b>我們的系統：</b>這是要給第一次安裝使用者用的提示詞複製功能。你不用自己手動整理檔案，直接複製對應提示詞，再交給 Codex 或 Claude Code（VS Code）幫你處理。</div><div class="summary"><b>控制台資料夾位置：</b>macOS 預設在 <code>~/Documents/CodexClaudeSkillsConsole</code>；Windows 預設在 <code>我的文件\\CodexClaudeSkillsConsole</code>。之後你可以直接改裡面的 <code>data/prompts.yaml</code>、<code>data/skills.yaml</code> 來客製自己的系統。</div><div class="summary"><b>適合情境：</b>第一次裝這套系統、換電腦重裝，或只想先把這個系統裡整理好的全部 skills 裝進自己的 Codex / Claude Code。</div><div class="summary">下面只留兩個入口：一個是整套控制台完整版安裝；另一個是只安裝這個系統裡面整理好的全部 skills。</div><div class="home-panel-actions">${installPromptCard("複製完整版安裝提示詞",unifiedPrompt)}${installPromptCard("複製系統內全部 skills 安裝提示詞",allSkillsPrompt)}</div></div></div>${installGuideTutorialHtml()}</div>`}
function bindInstallGuide(){document.querySelectorAll("[data-install-guide-topic]").forEach(btn=>btn.onclick=()=>{installGuideTopic=btn.dataset.installGuideTopic||"codex";render();setTimeout(()=>document.querySelector(".install-tutorial-card")?.scrollIntoView({behavior:"smooth",block:"start"}),80)});document.querySelectorAll("[data-wake-ai]").forEach(btn=>btn.onclick=()=>wakeAI(btn))}
function backupHtml(){
const winCmd=`powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.ps1 | iex"`;
const macCmd="curl -fsSL https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.sh | bash";
const restoreCmd="./restore-skills.sh";
const backupUrl="https://github.com/kagenhsu/codex-claude-skills-backup/raw/main/codex-skills-backup.tar.gz";
const P=BACKUP_PROMPTS;
return`<div class="sop wide-sop"><div class="card install-hero"><h2>備份 / 還原 — 一段提示詞跑完</h2><div class="summary">這頁只做兩件事：把這台電腦的 Codex / Claude Code 設定備份到你自己的 GitHub，或從 GitHub 還原到任何一台 Mac / Windows。複製下面的提示詞貼給 Codex 或 Claude Code（VS Code），AI 會自動偵測作業系統、安裝必要工具、處理 GitHub 登入與倉庫建立，然後完成備份或還原。<b>沒有 GitHub 帳號或倉庫也會自動帶你建立</b>，不用先去網站操作。</div><div class="privacy-note">這個網頁本身不會碰你的檔案；按下「複製」只是把提示詞放到剪貼簿。你貼給本機 AI 之後，AI 才會真正在你的電腦上跑指令，每一步前都會先告訴你要做什麼。</div></div><div class="install-grid"><div class="install-card featured"><h3>① 備份到 GitHub（自動偵測 Mac / Windows）</h3><div class="install-subtitle">複製後貼給 Codex 或 Claude Code。沒 GitHub 帳號 / 倉庫都會自動建立。</div>${installPromptCard("複製『備份到 GitHub』提示詞",P.backupUnified)}<div class="summary" style="margin-top:10px">提示詞會做：(1) 自動裝 git／gh，(2) 沒登入就帶你跑 <code>gh auth login</code>，(3) 沒倉庫就用 <code>gh repo create</code> 建立 <b>私有</b> repo <code>my-codex-claude-backup</code>，(4) 把 <code>~/.codex</code>、<code>~/.claude</code> 與控制台客製化資料同步進去，(5) 自動產出 <code>RESTORE.md</code>，(6) 用繁體中文 commit 後 push。</div><div class="summary" style="margin-top:6px">想要單一系統版本（不偵測），可以用下面這兩個：</div><div class="home-panel-actions">${installPromptCard("複製 macOS 版備份提示詞",P.backupMac)}${installPromptCard("複製 Windows 版備份提示詞",P.backupWin)}</div></div><div class="install-card featured"><h3>② 從 GitHub 還原到這台電腦（Mac / Windows 都行）</h3><div class="install-subtitle">複製後貼給 Codex 或 Claude Code。會在覆蓋前先做時間戳備份。</div>${installPromptCard("複製『從 GitHub 還原』提示詞",P.restoreUnified)}<div class="summary" style="margin-top:10px">提示詞會做：(1) 自動裝 git／gh，(2) 跑 <code>gh auth login</code>，(3) 從 <code>my-codex-claude-backup</code> clone 下來，(4) 把現有 <code>~/.codex</code>、<code>~/.claude</code> 先做時間戳備份（避免直接被覆蓋），(5) 預演要還原什麼給你看，等你確認後再覆蓋，(6) 還原完回報結果與下一步。</div><div class="summary" style="margin-top:6px">需要單一系統版本時：</div><div class="home-panel-actions">${installPromptCard("複製 macOS 版還原提示詞",P.restoreMac)}${installPromptCard("複製 Windows 版還原提示詞",P.restoreWin)}</div></div></div><div class="card"><h2>還沒有 GitHub 帳號或倉庫怎麼辦？</h2><div class="summary">不用先去網站開帳號，「備份到 GitHub」提示詞已經把這些步驟內建進去：</div><ul><li>會先檢查 <code>gh auth status</code>。如果沒登入，會幫你開 <a href="https://github.com/signup" target="_blank" rel="noopener">https://github.com/signup</a>，逐步教你建立帳號。</li><li>建立完帳號後跑 <code>gh auth login</code>，選 <b>GitHub.com → HTTPS → Login with a web browser</b>，瀏覽器會自動開驗證頁。</li><li>還沒倉庫時，會用 <code>gh repo create my-codex-claude-backup --private</code> 直接幫你建立 <b>私人倉庫</b>，不用自己進網站操作。</li><li>整個過程沒帳號、沒倉庫、沒 CLI 都可以從零開始；每一步前 AI 會說明，並等你確認重要動作。</li></ul></div><div class="card"><h2>會備份什麼？不會備份什麼？</h2><div class="install-result-grid"><div class="install-result"><b>會備份</b><div class="summary"><code>~/.codex/</code>、<code>~/.claude/</code> 內的設定、commands、skills，以及這個控制台的 <code>data/</code>、<code>skills/</code>。</div></div><div class="install-result"><b>不會備份</b><div class="summary">登入憑證（<code>.credentials.json</code>）、log、tmp、<code>shell-snapshots/</code>、<code>todos/</code>、<code>projects/</code>、<code>statsig/</code>、<code>node_modules</code>、<code>__pycache__</code> 等暫存或敏感資料。</div></div><div class="install-result"><b>還原時的保護</b><div class="summary">遇到既有 <code>~/.codex</code>、<code>~/.claude</code> 會先打包成 <code>.codex.bak-時間戳</code>、<code>.claude.bak-時間戳</code> 保留下來，再做還原，避免你舊環境直接被覆蓋。</div></div></div></div><div class="advanced-section"><div class="section-head"><h2>進階：用作者的安裝腳本（不是新手主流路線）</h2><span class="hint">只想用作者整理好的 skills 包，不想透過 AI 自動處理 GitHub 備份</span></div><div class="advanced-grid"><div class="card"><h2>Windows / macOS 一鍵安裝指令</h2>${cmdRow("Windows（PowerShell）",winCmd)}${cmdRow("macOS（Terminal）",macCmd)}<div class="summary">這是作者原本的一鍵安裝腳本，會把控制台與作者整理的 skills 裝到固定位置，<b>但不會替你做 GitHub 備份</b>。如果你想要「我電腦的設定備份到我自己的 GitHub」，請改用上面的備份提示詞。</div></div><div class="card"><h2>離線備份包 / 離線還原</h2><a class="copy-btn" href="${backupUrl}" target="_blank" rel="noopener">下載作者整理的備份包</a>${cmdRow("macOS 離線還原 skills",restoreCmd)}<div class="summary">這個是「作者整理好的 skills 包」，不是你個人的備份。要備份／還原自己的內容請用上面的提示詞。</div></div></div></div></div>`;
}
function wideHtml(html){return html.replace('<div class="sop">','<div class="sop wide-sop">')}
const CONTROL_STAGES=[
  {stage:"1",role:"Claude Code（VS Code）",purpose:"規劃與拆任務",plain:"先把需求變成可做的清單，避免一開始就亂改檔。"},
  {stage:"2",role:"Claude Code（VS Code）",purpose:"分段實作與驗證",plain:"一段一段做，每段 build、檢查、commit。"},
  {stage:"3",role:"Codex",purpose:"審查＋修改建議",plain:"請 Codex 用審查員角度抓 P0/P1/P2 問題，並附修改建議；終端機介面直接標出哪裡要改。"},
  {stage:"4",role:"Claude Code（VS Code）",purpose:"修正＋開發",plain:"把審查意見搬回 Claude Code，逐條處理、補開發並重新驗證。"},
  {stage:"5",role:"Codex",purpose:"複審＋補修改",plain:"修完後再請 Codex 確認沒有殘留問題，必要時補最後修改建議。"},
  {stage:"archive",role:"Codex",purpose:"存檔收尾",plain:"複審通過後由 Codex 做最後驗證、更新狀態檔、commit，push 決定權交回使用者。",query:"存檔收尾",fallback:"請依 dual-ai-workflow 第 5 階段通過後的收尾流程，重新驗證、更新 DUAL-AI-STATE.md、建立本地 commit，並把是否 push origin/main 的決定權交回使用者。"}
];
function controlPromptInfo(item){let found=null;if(item.stage==="archive")found=DATA.prompts.find(p=>(p.flow||"common")==="dualai"&&(String(p.stage||"")==="archive"||p.title.includes("存檔收尾")));else found=DATA.prompts.find(p=>(p.flow||"common")==="dualai"&&String(p.stage||"")===item.stage);return{prompt:found?found.prompt:item.fallback,targetStage:found?String(found.stage||item.stage):item.stage,targetPrompt:found?promptKey(found):"",found:!!found}}
function stateDraft(){return localStorage.getItem("workflow-state-draft")||""}
// 必須與 DUAL-AI-STATE.md section 名稱保持同步
const STATE_SECTIONS=["任務名稱","目前階段","已完成事項","下一步","未解決問題","最後更新時間"];
const PROJECT_STATE_DETAIL_SECTIONS=["任務名稱","目前階段","狀態","已完成事項","驗證結果","本輪 P2","下一步","未解決問題","最後更新時間"];
const NEXT_TASK_SECTIONS=["任務名稱","目前階段","上一棒 AI","下一棒 AI","交棒目的","最後更新","必讀檔案","本輪已完成","驗證要求","凍結期規則","P2-V22（給未來使用週後評估，不主動修）","下一棒要做","注意事項"];
const STATE_SECTION_PATTERN=STATE_SECTIONS.map(item=>item.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")).join("|");
function sectionAfter(text,label){if(!STATE_SECTIONS.includes(label))return"";const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");const match=text.match(new RegExp(`(?:^|\\n)${escaped}：?\\s*([\\s\\S]*?)(?=\\n(?:${STATE_SECTION_PATTERN})：?|$)`));return match?match[1].trim():""}
function labelledValue(text,label){const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");const match=(text||"").match(new RegExp(`(?:^|\\n)${escaped}：?\\s*(.*)`));return match?match[1].trim():""}
function sectionFromLabels(text,label,labels){if(!(text||"").trim())return"";if(!labels.includes(label))return labelledValue(text,label);const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");const pattern=labels.map(item=>item.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")).join("|");const match=text.match(new RegExp(`(?:^|\\n)${escaped}：?\\s*([\\s\\S]*?)(?=\\n(?:${pattern})：?|$)`));return match?match[1].trim():""}
function parseNextTask(text){return{text:text||"",task:labelledValue(text,"任務名稱")||"尚未設定。",current:labelledValue(text,"目前階段")||"尚未設定。",previous:labelledValue(text,"上一棒 AI")||"尚未設定。",nextOwner:labelledValue(text,"下一棒 AI")||"尚未設定。",handoff:labelledValue(text,"交棒目的")||"尚未設定。",updated:labelledValue(text,"最後更新")||"尚未設定。",required:sectionFromLabels(text,"必讀檔案",NEXT_TASK_SECTIONS)||"尚未設定。",done:sectionFromLabels(text,"本輪已完成",NEXT_TASK_SECTIONS)||"尚未設定。",verify:sectionFromLabels(text,"驗證要求",NEXT_TASK_SECTIONS)||"尚未設定。",nextSteps:sectionFromLabels(text,"下一棒要做",NEXT_TASK_SECTIONS)||"尚未設定。",notes:sectionFromLabels(text,"注意事項",NEXT_TASK_SECTIONS)||"尚未設定。"}}
function parseStageNumber(value){const map={一:"1",二:"2",三:"3",四:"4",五:"5"};return map[value]||value||""}
function parseWorkflowState(text){if(!text.trim())return{ok:false,message:"無法解析，請確認貼上的是 DUAL-AI-STATE.md 全文。"};const current=(text.match(/目前階段：?\s*(.*)/)||[])[1]?.trim()||"";const next=sectionAfter(text,"下一步");const unresolved=sectionAfter(text,"未解決問題");const updated=(text.match(/最後更新時間：?\s*(.*)/)||[])[1]?.trim()||"";const done=sectionAfter(text,"已完成事項").split(/\n/).map(s=>s.trim()).filter(Boolean).slice(-3).join("\n");const stageMatch=current.match(/第\s*([1-5一二三四五])\s*階段/);const stage=current.includes("已完成")?"5":parseStageNumber(stageMatch?stageMatch[1]:"");const ok=!!(current||next||unresolved||updated||done);return{ok,current:current||"尚未判斷",done:done||"尚未解析",next:next||"尚未解析",unresolved:unresolved||"無",updated:updated||"尚未解析",stage,message:ok?"":"無法解析，請確認貼上的是 DUAL-AI-STATE.md 全文。"}}
function parseProjectStageDetails(src){const workflow=parseWorkflowState(src.state.raw||"");const nextTask=parseNextTask(src.next.raw||"");const task=sectionFromLabels(src.state.raw||"","任務名稱",PROJECT_STATE_DETAIL_SECTIONS)||nextTask.task||src.name||"尚未設定。";const status=sectionFromLabels(src.state.raw||"","狀態",PROJECT_STATE_DETAIL_SECTIONS)||"尚未設定。";const verify=sectionFromLabels(src.state.raw||"","驗證結果",PROJECT_STATE_DETAIL_SECTIONS)||nextTask.verify||"尚未設定。";const current=sectionFromLabels(src.state.raw||"","目前階段",PROJECT_STATE_DETAIL_SECTIONS)||nextTask.current||"尚未設定。";const done=sectionFromLabels(src.state.raw||"","已完成事項",PROJECT_STATE_DETAIL_SECTIONS)||nextTask.done||"尚未設定。";const next=sectionFromLabels(src.state.raw||"","下一步",PROJECT_STATE_DETAIL_SECTIONS)||nextTask.nextSteps||"尚未設定。";const unresolved=sectionFromLabels(src.state.raw||"","未解決問題",PROJECT_STATE_DETAIL_SECTIONS)||"尚未設定。";const updated=sectionFromLabels(src.state.raw||"","最後更新時間",PROJECT_STATE_DETAIL_SECTIONS)||nextTask.updated||"尚未設定。";return{workflow,nextTask,task,status,verify,current,done,next,unresolved,updated}}
function stateSummaryHtml(parsed){return parsed.ok?`<div class="state-summary"><div class="state-item"><div class="state-label">目前階段</div><div class="state-value">${esc(parsed.current)}</div></div><div class="state-item"><div class="state-label">最後更新時間</div><div class="state-value">${esc(parsed.updated)}</div></div><div class="state-item full"><div class="state-label">上一步做了什麼</div><div class="state-value">${esc(parsed.done)}</div></div><div class="state-item full"><div class="state-label">下一步</div><div class="state-value">${esc(parsed.next)}</div></div><div class="state-item full"><div class="state-label">未解決問題</div><div class="state-value">${esc(parsed.unresolved)}</div></div></div>`:`<div class="warning">${esc(parsed.message)}</div>`}
function mdSection(text,label){const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");const match=text.match(new RegExp(`(?:^|\\n)## ${escaped}\\s*\\n([\\s\\S]*?)(?=\\n## |$)`));return match?match[1].trim():"尚未設定。"}
function simpleMarkdownHtml(raw,fallbackTitle){if(!raw.trim())return`<div class="sop"><div class="card"><h2>${esc(fallbackTitle)}</h2><div class="summary">尚未設定。</div></div></div>`;return`<pre class="prompt-body">${esc(raw)}</pre>`}
function prdFeatures(raw){const section=mdSection(raw,"4. 功能清單");if(!section||section==="尚未設定。")return[];return section.split(/\n/).map(line=>line.trim()).filter(line=>/^\d+\./.test(line)).map(line=>line.replace(/^\d+\.\s*/,""))}
function progressSource(){return selectedProject||{name:"目前控制台資料夾",path:PROJECT_PATH,state:STATE_HTML,next:NEXT_HTML,agents:AGENTS_HTML,prd:PRD_HTML,plan:PLAN_HTML,filePaths:CONSOLE_FILE_PATHS,projectType:"console"}}
function progressMissingFiles(src){return [["DUAL-AI-STATE.md",src.state.raw],["NEXT-AI-TASK.md",src.next.raw],["AGENTS.md",src.agents.raw],["PRD.md",src.prd.raw]].filter(([,raw])=>!raw.trim()).map(([name])=>name)}
function progressSetupPrompt(src,missing){return`請幫我檢查這個專案資料夾，並補齊開發進度控制台需要的 markdown 檔案。\n\n專案資料夾：${src.path||src.name}\n缺少檔案：${missing.join("、")}\n\n請建立或補齊：\n- DUAL-AI-STATE.md：記錄任務名稱、目前階段、已完成事項、下一步、未解決問題、最後更新時間。\n- NEXT-AI-TASK.md：記錄上一棒 AI、下一棒 AI、交棒目的、必讀檔案、已完成、下一棒要做、驗證要求。\n- AGENTS.md：記錄專案名稱、專案簡介、開發協作規範與檔案結構。\n- PRD.md：記錄專案背景、目標、痛點、功能清單、不做的事與驗收標準。\n\n請先讀現有檔案與 git 狀態，再用繁體中文補檔；不要刪除既有內容。`}
function progressFileCheckHtml(src){const missing=progressMissingFiles(src);if(!missing.length)return`<div class="card"><h2>必備檔案檢查</h2><div class="summary">✅ 已找到 DUAL-AI-STATE.md、NEXT-AI-TASK.md、AGENTS.md、PRD.md，下方資料卡可以正常顯示。</div></div>`;const prompt=progressSetupPrompt(src,missing);return`<div class="warning"><div><b>缺少必要 .md 檔案：</b>${esc(missing.join("、"))}</div><div class="summary" style="margin-top:6px">這個專案可能是新專案，或還沒建立交接文件。請先把下方提示詞交給 AI 補齊檔案，補完後重新選擇資料夾。</div><button class="copy-btn" style="margin-top:8px" data-copy="${encodeURIComponent(prompt)}">複製給 AI 補檔提示詞</button></div>`}
function progressPickerHtml(src){const helper=progressPickerMessage?`<div class="summary" style="margin-top:8px;color:var(--amber)">${esc(progressPickerMessage)}</div>`:`<div class="summary" style="margin-top:8px">如果按了「選擇專案資料夾」沒有跳出視窗，通常是瀏覽器不支援資料夾選取；這時會自動改走備援方式，或在這裡顯示原因。</div>`;return`<div class="warning"><div>請選擇要查看的專案資料夾；系統會自動檢查 DUAL-AI-STATE.md / NEXT-AI-TASK.md / AGENTS.md / PRD.md 是否存在。</div><div class="trigger" style="margin-top:8px"><code>${esc(src.path||src.name)}</code><button class="copy-btn" type="button" data-progress-pick>選擇專案資料夾</button><button class="copy-btn" type="button" data-copy="${encodeURIComponent(src.path||src.name)}">複製目前名稱</button><input id="projectFolderInput" type="file" webkitdirectory directory multiple style="display:none"></div>${helper}</div>`}
function progressFlowSwitchHtml(){const isDual=progressFlow==="dual";return`<div class="card"><div class="section-head"><h2>切換開發模式：雙刀 / 單刀</h2><span class="hint">當雙刀流跑不動時，可隨時切到單刀（Codex 專用）繼續開發</span></div><div class="flow-switch" style="margin-top:8px"><button class="flow-btn ${isDual?"active":""}" data-progress-flow="dual" type="button">專案開發（雙刀）</button><button class="flow-btn ${!isDual?"active":""}" data-progress-flow="solo" type="button">專案開發（單刀）</button></div><div class="summary" style="margin-top:10px">${isDual?"<b>目前是雙刀模式</b>：Claude Code（VS Code）負責規劃與實作，Codex（終端機）負責審查、複審與收尾。適合重要修改、核心邏輯與正式版交付。":"<b>目前是單刀模式（Codex 專用）</b>：當雙刀流暫時跑不動（只剩一個 AI、Claude Code 卡住、額度用完、想用最簡流程）時，就用 Codex 一個 AI 走完「規劃 → 分段實作 → 自審 → 收尾」，繼續把專案推進。"}</div><div class="summary" style="margin-top:6px;color:#5b6478">切換後，頁面上的提示詞、開發階段、收尾步驟會全部換成對應模式版本；上方的分頁名稱也會跟著變成「專案開發（雙刀）」或「專案開發（單刀）」。</div></div>`}
function progressIntroSeenKey(){return `progress-intro-seen-${progressFlow}`}
function progressIntroShouldOpen(){if(localStorage.getItem(progressIntroSeenKey())==="seen")return false;localStorage.setItem(progressIntroSeenKey(),"seen");return true}
function progressDualSoloIntroHtml(){
  const openAttr=progressIntroShouldOpen()?" open":"";
  if(progressFlow==="solo"){
    return`<div class="card"><details class="doc-fold" data-progress-intro="solo"${openAttr}><summary><div class="doc-fold-title"><b>🗡️ 單刀模式（Codex 專用）：一個 AI 也能把專案推下去</b><div class="summary">只用 Codex 一個 AI 走完「規劃 → 分段實作 → 自審 → 收尾」。適合雙刀流跑不動、只有一個 AI 可用，或這次只是小修小改時。點標題可收合。</div></div><span class="doc-fold-arrow">›</span></summary><div class="doc-fold-body"><h3 style="margin:14px 0 8px;font-size:.95rem">為什麼這頁專為 Codex 設計？</h3><div class="workflow-guide"><div class="guide-item"><div class="guide-label">🔍 Codex（終端機 AI agent）</div><div class="guide-text">能直接讀檔、改檔、跑指令、做驗證；介面會把「哪裡要改」標得很清楚，對新手最好上手。單刀模式時，它要同時兼任規劃者、開發者、審查員與收尾者。</div></div><div class="guide-item"><div class="guide-label">💡 為什麼不直接用 Claude Code？</div><div class="guide-text">Claude Code（VS Code）若已卡住、額度用完，或你還沒設定好，先用 Codex 把專案先推一段路也沒問題。等雙刀流恢復再切回來。</div></div></div><h3 style="margin:16px 0 8px;font-size:.95rem">單刀模式四段強制流程（給 Codex）</h3><div class="summary">不要讓 Codex 一開口就動手。一定要走「先規劃 → 再實作 → 自審 → 收尾」這四段。</div><div class="workflow-guide" style="margin-top:8px"><div class="guide-item"><div class="guide-label">① Codex 釐清任務</div><div class="guide-text">先讀 AGENTS.md / PRD.md / 專案規劃表.md / DUAL-AI-STATE.md，列出方案 → 你確認後才動手。</div></div><div class="guide-item"><div class="guide-label">② Codex 分段實作</div><div class="guide-text">一次改一小段，每段都跑驗證、回報差異，不要一次改太多難回溯。</div></div><div class="guide-item"><div class="guide-label">③ Codex 自審</div><div class="guide-text">請 Codex 切換成「審查員」視角，列出 P0／P1／P2 風險，自己抓自己的問題。</div></div><div class="guide-item"><div class="guide-label">④ Codex 收尾</div><div class="guide-text">更新 DUAL-AI-STATE.md、建立本地 commit；是否 push 完全由你決定。</div></div></div><h3 style="margin:16px 0 8px;font-size:.95rem">什麼時候用單刀模式</h3><div class="workflow-guide"><div class="guide-item"><div class="guide-label">雙刀流跑不動時</div><div class="guide-text">Claude Code 額度用完、登入有問題、VS Code 還沒裝好、或是某個 agent 一直卡住。</div></div><div class="guide-item"><div class="guide-label">只有 Codex 可以用時</div><div class="guide-text">這台機器只裝了 Codex；或這個專案只想用一個 AI 帳號處理。</div></div><div class="guide-item"><div class="guide-label">小修小改</div><div class="guide-text">小段文案、配色、加註解、修錯字、純資料維護（改 yaml）。</div></div></div><h3 style="margin:16px 0 8px;font-size:.95rem">單刀模式三條紀律</h3><ul class="lifecycle-features" style="font-size:.85rem"><li><b>不准跳過規劃</b>：Codex 必須先讀檔、提案，等你確認才能動手。</li><li><b>每段結束都更新 <code>DUAL-AI-STATE.md</code></b>，雙刀流恢復時下一棒接得回來。</li><li><b>重要動作要你明確同意</b>：push、刪檔、改設定、改受保護函式，Codex 不能自己決定。</li></ul></div></details></div>`;
  }
  return`<div class="card"><details class="doc-fold" data-progress-intro="dual"${openAttr}><summary><div class="doc-fold-title"><b>🗡️ Claude Code × Codex：怎麼搭配開發專案</b><div class="summary">兩個 AI 各有專長，搭配使用比單獨用更穩定。下面用最白話的方式說它們的分工，以及什麼時候用「雙刀流」、什麼時候用「單刀流」。點標題可收合。</div></div><span class="doc-fold-arrow">›</span></summary><div class="doc-fold-body"><h3 style="margin:14px 0 8px;font-size:.95rem">兩個 AI 各自的角色</h3><div class="workflow-guide"><div class="guide-item"><div class="guide-label">⚒️ Claude Code（VS Code，主力工程師）</div><div class="guide-text">VS Code 內的 AI agent，能直接讀檔、寫程式、跑指令、做驗證。負責規劃任務、實際改檔、跑 build／測試、整理交接摘要。</div></div><div class="guide-item"><div class="guide-label">🔍 Codex（審查員＋收尾）</div><div class="guide-text">在終端機跑的 AI agent，介面對新手最直觀地標出「哪裡要改」。接到 Claude Code 的 diff 後，標出 P0／P1／P2 風險與修改建議；複審通過後也由 Codex 做最終驗證、commit 與存檔收尾。</div></div></div><h3 style="margin:16px 0 8px;font-size:.95rem">雙刀流：兩個 AI 接力（適合重要修改）</h3><div class="summary">同時間只有一個 AI 動手，每一棒做完都整理交接內容給下一棒。順序如下：</div><div class="workflow-guide" style="margin-top:8px"><div class="guide-item"><div class="guide-label">① Claude Code 規劃</div><div class="guide-text">讀檔、拆任務、提方案 → 你確認再進下一棒。</div></div><div class="guide-item"><div class="guide-label">② Claude Code 實作</div><div class="guide-text">分段改檔、跑 build、做驗證 → 整理交接摘要。</div></div><div class="guide-item"><div class="guide-label">③ Codex 審查</div><div class="guide-text">看 diff、抓 P0／P1／P2 風險與修改建議（終端機介面直接標出哪裡要改）。</div></div><div class="guide-item"><div class="guide-label">④ Claude Code 修正</div><div class="guide-text">逐條處理審查意見、重新驗證。</div></div><div class="guide-item"><div class="guide-label">⑤ Codex 複審</div><div class="guide-text">確認上一輪問題真的解掉。</div></div><div class="guide-item"><div class="guide-label">⑥ Codex 收尾</div><div class="guide-text">最終驗證、更新 DUAL-AI-STATE.md、本地 commit；是否 push 由你決定。</div></div></div><h3 style="margin:16px 0 8px;font-size:.95rem">單刀流：一個 AI 走完（適合小修小改）</h3><div class="summary">只有一個 AI 也要強制走「先規劃 → 再實作 → 最後自審」三段，不要讓它一開口就動手。如果你想專為 Codex 跑單刀流，請點上方「專案開發（單刀）」切換模式。</div><div class="workflow-guide" style="margin-top:8px"><div class="guide-item"><div class="guide-label">① 釐清任務</div><div class="guide-text">AI 先讀檔、提出做法 → 你確認方案再動手。</div></div><div class="guide-item"><div class="guide-label">② 分段執行</div><div class="guide-text">一次改一小段，做完報告，避免一次改太大難回溯。</div></div><div class="guide-item"><div class="guide-label">③ 自審</div><div class="guide-text">請 AI 用「審查員」的視角檢查自己的改動，列出風險。</div></div></div><h3 style="margin:16px 0 8px;font-size:.95rem">什麼時候用哪一種</h3><div class="workflow-guide"><div class="guide-item"><div class="guide-label">用雙刀流</div><div class="guide-text">動到核心邏輯、資料庫、外部 API、安全相關、刪檔重構，或使用者看得到的主功能。</div></div><div class="guide-item"><div class="guide-label">用單刀流</div><div class="guide-text">雙刀流跑不動、小段文案、配色、加註解、修錯字、純資料維護（改 yaml），或只有一個 AI 帳號可用時。</div></div></div><h3 style="margin:16px 0 8px;font-size:.95rem">三條共用紀律</h3><ul class="lifecycle-features" style="font-size:.85rem"><li><b>一次只有一個 AI 動手</b>，另一個暫停，避免互相覆蓋。</li><li><b>每棒結束都要更新 <code>DUAL-AI-STATE.md</code></b>，下一棒（或下次自己接手）才能無痛上手。</li><li><b>重要動作要使用者明確同意</b>：push、刪檔、改設定、改受保護函式，AI 不自己決定。</li></ul></div></details></div>`;
}
function progressModeButtons(){const modes=[["startup","第 0 步：先把開工前的 6 個東西建起來","先建立文件、規劃表、忽略規則與下一階段提示詞，後面不管是單一 AI 還是雙 AI 開發都比較不會走歪。"],["status","第 1 步：先看目前狀態","先確認這個專案現在卡在哪裡、上一棒做了什麼、下一步是什麼。"],["project","第 2 步：看專案敘述","先看這個專案到底要做什麼、目標是什麼、有哪些功能。"],["docs","第 3 步：讀規則文件","打開 AGENTS / PRD / 狀態檔，確認細節、規則與交接內容。"],["stages","第 4 步：看開發階段","照專案規劃表確認現在做到哪個功能階段，下一段要做什麼。"],["acceptance","第 5 步：驗收、上傳備份、上架到哪裡去","最後確認驗收有沒有完成，再決定這版是只上傳 GitHub 備份，還是正式上架到要部署的地方。"]];return`${progressFlowSwitchHtml()}${progressDualSoloIntroHtml()}<div class="card" style="margin-top:12px"><h2>新手從零開始，請照這個順序看</h2><div class="summary">如果你是第一次接這個專案，不要急著改檔。先做第 0 步把開工前的東西建起來，再照下面第 1 到第 5 步往下看，這樣比較不會漏掉關鍵資訊。</div><div class="workflow-guide">${modes.map(([key,label,desc])=>`<div class="guide-item"><div class="guide-label">${esc(label)}</div><div class="guide-text">${esc(desc)}</div><button class="flow-btn ${progressMode===key?"active":""}" data-progress-mode="${key}" style="margin-top:8px">${esc(label)}</button></div>`).join("")}</div></div>`}
function progressStartupHtml(){const setupItems=[{title:"建立 AGENTS.md 頂層規則文件",label:"1. 建立 AGENTS.md",button:"建立 AGENTS.md",desc:"先把專案規則、協作方式與檔案結構講清楚，後面 AI 才不會各做各的。",fallback:"請在專案根目錄只建立一個頂層規則文件 AGENTS.md，把我們的協作規範寫進去。之後每次回答都要用我聽得懂的話解釋，不要亂刪文件。專案名稱：【】專案簡介：【】"},{title:"梳理需求並產出 PRD",label:"2. 建立 PRD.md",button:"建立 PRD.md",desc:"需求還沒落成文件前，先整理目標、痛點、功能清單與驗收標準。",fallback:"先和我討論、梳理需求，確認後再建立 PRD.md 檔案，至少包含：專案背景、專案目標、專案痛點、功能清單、不做的事。我們先討論，先不要寫程式。"},{title:"建立專案規劃表（從零到開發結束）",label:"3. 建立 專案規劃表.md",button:"建立 專案規劃表.md",desc:"把整個系統從第 0 步到驗收上架拆成階段，讓新手知道現在做到哪裡。",fallback:"請幫我建立一份「專案規劃表.md」，用繁體中文把這個專案從第 0 步準備、需求整理、環境架設、基礎系統、功能開發、驗收、上架，依序拆成可理解的階段。每個階段都要寫出：這一階段要做什麼、會產出什麼、完成後怎麼判斷可以進下一步。"},{title:"建立 .gitignore + 種子 DUAL-AI-STATE",label:"4. 建立 .gitignore",button:"建立 .gitignore",desc:"正式開發前先補版控忽略規則與初始進度檔，之後接手比較不會亂。",fallback:"請先不要開始寫功能，先幫我做新專案開工前的基礎準備。檢查專案根目錄後，建立或補齊 .gitignore，並建立一份種子 DUAL-AI-STATE.md，先填好任務名稱、目前階段、已完成事項、下一步、未解決問題、最後更新時間。"},{title:"確認技術棧 / 資料庫 / 上架目標",label:"5. 先確認技術棧 / 資料庫 / 上架目標",button:"先確認技術棧 / 資料庫 / 上架目標",desc:"先讓 AI 讀檔判斷這個專案用了哪些程式語言、框架、資料庫，最後準備部署到哪裡。",fallback:"請先不要直接改程式，先幫我確認這個專案使用哪些程式語言、框架、資料庫，以及最後要上架到哪裡。"},{title:"建立兩個 AI 的交流.md 提示詞",label:"6. 建立兩個 AI 的交流.md 提示詞",button:"展開兩個 AI 的交流.md 提示詞資訊卡",desc:"按下按鈕後，下面會展開雙刀流與一刀流的接棒提示詞資訊卡，讓 Codex 跟 Claude Code 每個階段完成後，都能自動產生交給下一位 AI 繼續動作的提示詞。",fallback:"請依照目前專案已經建立好的 AGENTS.md、PRD.md、專案規劃表.md、DUAL-AI-STATE.md，幫我建立一份「兩個 AI 的交流.md」用的接棒提示詞規格。我要讓 Codex 跟 Claude Code 在每個階段完成後，都能自動產生交給下一位 AI 的提示詞，內容至少要包含：目前做到哪裡、這一棒改了什麼、哪些檔案受影響、驗證結果、剩下的風險、下一位 AI 要先做什麼。請同時產出雙刀流與單刀流版本。",toggle:true}];const dualaiInfo=promptInfoByTitle("① 第一階段：Claude Code 規劃","請先讀取專案結構與相關文件，不要直接修改。先提出方案，再等我確認。");const soloInfo=promptInfoByTitle("單一 AI 也能用控制台","我現在只使用一個 AI，但想用這套二刀流開發助手控制台輔助工作。請先幫我釐清任務目標，提出方案，再分段執行。");const nextPromptCard=progressNextPromptOpen?(progressFlow==="solo"?`<div class="card" style="margin-top:12px"><div class="section-head"><h2>下一層提示詞資訊卡（單刀 / Codex 專用）</h2><span class="hint">雙刀流暫時跑不動時，只要這一張就能讓 Codex 接著開發</span></div><div class="workflow-guide"><div class="guide-item"><div class="guide-label">Codex 單刀開工提示詞</div><div class="guide-text">直接交給 Codex：先讀文件、列方案、等你確認，再分段實作、自審、收尾。一張就走完四段流程。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(soloInfo.prompt)}">複製 Codex 單刀開工提示詞</button></div></div></div>`:`<div class="card" style="margin-top:12px"><div class="section-head"><h2>下一層提示詞資訊卡</h2><span class="hint">依你接下來要怎麼做，選擇雙刀流或一刀流</span></div><div class="workflow-guide"><div class="guide-item"><div class="guide-label">雙刀流提示詞資訊卡</div><div class="guide-text">適合重要系統修改。先交給 Claude Code 規劃，再依序走 Claude Code 實作、Codex 審查與後續接棒流程，最後由 Codex 存檔收尾。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(dualaiInfo.prompt)}">複製雙刀流開工提示詞</button></div><div class="guide-item"><div class="guide-label">一刀流提示詞資訊卡</div><div class="guide-text">如果你現在只有一個 AI，就先用這張提示詞，讓它先釐清任務、提出方案，再分段執行。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(soloInfo.prompt)}">複製一刀流開工提示詞</button></div></div></div>`):"";return`<div class="card"><div class="section-head"><h2>第 0 步：先把開工前的東西建起來</h2><span class="hint">先把基礎文件與提示詞準備好，後面才不會越做越亂</span></div><div class="summary">這一區只顯示第 0 步要先準備的內容，不是正式開發流程。先把這些提示詞用起來，再進到第 1 階段之後的開發、審查、修正與收尾。${progressFlow==="solo"?"<br><b>目前是單刀（Codex）模式</b>：基礎文件還是要先準備好，後面才把開發、審查、收尾全部交給 Codex 一個 AI 處理。":""}</div><div class="workflow-guide">${setupItems.map(item=>{const info=promptInfoByTitle(item.title,item.fallback);const action=item.toggle?`<button class="copy-btn" type="button" style="margin-top:8px" data-progress-next-prompts-toggle>${esc(progressNextPromptOpen?"收合下一階段提示詞資訊卡":item.button)}</button>`:`<button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(info.prompt)}">${esc(item.button)}</button>`;return`<div class="guide-item"><div class="guide-label">${esc(item.label)}</div><div class="guide-text">${esc(item.desc)}</div>${action}</div>`}).join("")}</div></div>${nextPromptCard}`}
function progressStageFlowSoloHtml(){const soloItems=[{label:"第 1 階段：Codex 釐清任務（讀檔＋提案）",desc:"先讓 Codex 讀 AGENTS.md、PRD.md、專案規劃表.md、DUAL-AI-STATE.md。只提案，不改檔；你確認方案後再進下一階段。",fallback:"請以 Codex 單刀模式開工。先讀 AGENTS.md、PRD.md、專案規劃表.md、DUAL-AI-STATE.md，整理：(1) 目前任務目標、(2) 受影響檔案、(3) 建議方案與分段步驟、(4) 風險與替代方案。本階段只提案，等我確認再動手。"},{label:"第 2 階段：Codex 分段實作（一次一小段）",desc:"方案確認後，由 Codex 一次改一小段，每段改完都跑驗證、回報差異，不要一次改太多難回溯。",fallback:"現在由 Codex 進入單刀分段實作階段。請依照已確認的方案，分段修改檔案。每段都需要：(1) 說明本段改了什麼、為何要改；(2) 真正執行 build／測試／lint；(3) 回報差異與驗證結果；(4) 如果遇到不確定的地方先停下來問我。"},{label:"第 3 階段：Codex 自審（切成審查員視角）",desc:"請 Codex 換上「審查員」帽子，自己抓自己的問題，列出 P0／P1／P2 風險與修改建議。",fallback:"請 Codex 切換成「審查員」視角，對自己這一輪的所有改動做單刀自審：(1) 列出 P0／P1／P2 風險與修改建議；(2) 標出沒驗證到的盲點；(3) 點出有沒有違反 AGENTS.md 或受保護函式規範；(4) 給出是否可以收尾的明確結論。"},{label:"第 4 階段：Codex 收尾（更新狀態檔＋本地 commit）",desc:"自審通過後，由 Codex 做最終驗證、更新 DUAL-AI-STATE.md、本地 commit；是否 push 完全由你決定。",fallback:"請 Codex 以單刀模式收尾：(1) 跑最終驗證；(2) 更新 DUAL-AI-STATE.md（任務、目前階段、已完成、下一步、未解決問題、最後更新時間）；(3) 建立本地 commit，commit message 用繁體中文；(4) 不要 push，把是否 push origin/main 的決定權交回給我。"},{label:"切回雙刀的時機提示",desc:"當 Claude Code 恢復可用、或這段改動影響核心邏輯／資料庫／外部 API 時，請主動建議切回雙刀流。",fallback:"請 Codex 在每一階段結束時主動評估：是否該切回雙刀流？評估標準：(1) Claude Code 是否恢復可用；(2) 接下來的改動是否會動到核心邏輯、資料庫、外部 API、安全相關或受保護函式。如果應該切回雙刀，請寫一段交接摘要，方便 Claude Code 從 DUAL-AI-STATE.md 直接接手。"}];const githubInfo=promptInfoByTitle("首次上傳 GitHub：繁體中文專案敘述","請協助我準備這個專案首次上傳 GitHub 的繁體中文說明與存檔流程。");const downloadInfo=promptInfoByTitle("跨地點 / 跨系統接續","請協助我做跨地點 / 跨系統接續存檔與交接，本輪不要自動 push，除非我明確確認。");return`<div class="card"><div class="section-head"><h2>單刀模式四段流程（Codex 專用）</h2><span class="hint">雙刀流跑不動時，照這四段交給 Codex 就能繼續推進專案</span></div><div class="summary">這一頁是「單刀（Codex）模式」的開發階段資訊卡。提示詞已經改成 Codex 一個 AI 走完全部流程的版本，每張卡都對應一段交辦提示詞，按按鈕即可複製。</div><div class="workflow-guide">${soloItems.map(item=>`<div class="guide-item"><div class="guide-label">${esc(item.label)}</div><div class="guide-text">${esc(item.desc)}</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(item.fallback)}">複製 ${esc(item.label)} 提示詞</button></div>`).join("")}</div><div class="section-head" style="margin-top:12px"><h2>GitHub 備份提示詞</h2><span class="hint">單刀模式照樣可以上傳備份／下載接續</span></div><div class="summary">單刀模式收尾後，一樣可以把目前版本上傳到 GitHub 備份；如果換電腦或環境，再從 GitHub 下載回來接續開發。</div><div class="workflow-guide" style="margin-top:8px"><div class="guide-item"><div class="guide-label">上傳 GitHub 備份提示詞</div><div class="guide-text">把單刀模式做出的這一版整理後上傳 GitHub，方便存檔、備份與下次接手。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(githubInfo.prompt)}">上傳 GitHub 備份提示詞</button></div><div class="guide-item"><div class="guide-label">下載 GitHub 備份提示詞</div><div class="guide-text">在另一台電腦或另一個環境，把 GitHub 備份下載回來，由 Codex 單刀繼續開發。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(downloadInfo.prompt)}">下載 GitHub 備份提示詞</button></div></div></div>`}
function progressStageFlowHtml(){if(progressFlow==="solo")return progressStageFlowSoloHtml();const flowItems=[{title:"① 第一階段：Claude Code 規劃",label:"第 1 階段：Claude Code 規劃",desc:"先交給 Claude Code（VS Code）讀檔、拆任務、提出方案，不要一開始就直接改。",fallback:"請先讀取專案結構與相關文件，不要直接修改。先提出方案，再等我確認。"},{title:"② 第二階段：Claude Code 分段實作",label:"第 2 階段：Claude Code 實作",desc:"方案確認後，交給 Claude Code 分段開發、build、驗證，再整理交棒內容。",fallback:"現在由 Claude Code（VS Code）負責分段實作，其他 AI 暫停動作。請依照已確認的方案，在真實專案中分段修改。修改完成後請回報修改檔案、驗證結果與交給下一棒的提示詞。"},{title:"③ 第三階段：Codex 審查＋修改建議",label:"第 3 階段：Codex 審查＋修改建議",desc:"把 Claude Code 的交接摘要、diff 與驗證結果貼給 Codex 做審查，並附修改建議。Codex 終端機介面會直觀地標出「哪裡要改」，對新手最好讀。",fallback:"現在由 Codex 負責審查，其他 AI 暫停動作。請審查這次改動、diff 與驗證結果，列出 P0/P1/P2 風險與修改建議。"},{title:"④ 第四階段：Claude Code 修正＋開發",label:"第 4 階段：Claude Code 修正＋開發",desc:"把審查意見貼回 Claude Code，逐條處理、補開發、重新驗證。",fallback:"現在由 Claude Code（VS Code）負責修正，其他 AI 暫停動作。請逐條判斷審查意見，處理必要修正並重新驗證。"},{title:"⑤ 第五階段：Codex 複審＋確認",label:"第 5 階段：Codex 複審＋確認",desc:"修正後再交給 Codex 複審，確認前一輪問題真的有解掉。",fallback:"現在由 Codex 負責複審，其他 AI 暫停動作。請再次檢查修正後的結果，確認前一輪問題是否已處理。",kind:"review"},{title:"給 Codex 的存檔收尾提示詞（模板）",label:"第 6 階段：Codex 存檔收尾",button:"第 6 階段：Codex 存檔收尾",desc:"複審通過後，由 Codex 做最終驗證、本地 commit，並由使用者決定是否 push（Codex 介面讓你逐筆看見要改／要 commit 的內容）。",fallback:"請執行最終驗證、更新 DUAL-AI-STATE.md、建立本地 commit，並把是否 push origin/main 的決定權交回使用者。",kind:"archive"}];const githubInfo=promptInfoByTitle("首次上傳 GitHub：繁體中文專案敘述","請協助我準備這個專案首次上傳 GitHub 的繁體中文說明與存檔流程。");const downloadInfo=promptInfoByTitle("跨地點 / 跨系統接續","請協助我做跨地點 / 跨系統接續存檔與交接，本輪不要自動 push，除非我明確確認。");return`<div class="card"><div class="section-head"><h2>開發階段提示詞資訊卡</h2><span class="hint">按按鈕就能複製對應提示詞，交給另一個 AI 接棒</span></div><div class="summary">這一區是正式開發後的交接流程。每一張卡都對應一棒提示詞，適合拿去交給另一個 AI 做開發、審查、修正、驗收與存檔。</div><div class="workflow-guide">${flowItems.map(item=>{const info=promptInfoByTitle(item.title,item.fallback);const buttonLabel=item.button||item.label;return`<div class="guide-item"><div class="guide-label">${esc(item.label)}</div><div class="guide-text">${esc(item.desc)}</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(info.prompt)}">${esc(buttonLabel)}</button></div>`}).join("")}</div><div class="section-head" style="margin-top:12px"><h2>GitHub 備份提示詞</h2><span class="hint">先上傳備份，需要時再下載回來接續</span></div><div class="summary">這裡分成兩個動作：先把目前版本上傳到 GitHub 備份；之後如果換電腦或換工作環境，再從 GitHub 下載回來接續。</div><div class="workflow-guide" style="margin-top:8px"><div class="guide-item"><div class="guide-label">上傳 GitHub 備份提示詞</div><div class="guide-text">這一段只處理把目前版本整理後上傳到 GitHub，方便存檔、備份與團隊接手。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(githubInfo.prompt)}">上傳 GitHub 備份提示詞</button></div><div class="guide-item"><div class="guide-label">下載 GitHub 備份提示詞</div><div class="guide-text">這一段只處理從 GitHub 把備份下載回來，在另一台電腦或另一個環境接續開發。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(downloadInfo.prompt)}">下載 GitHub 備份提示詞</button></div></div></div>`}
function progressDocPreview(raw,fallback){if(!(raw||"").trim())return fallback;return raw.split(/\n+/).map(line=>line.trim()).filter(Boolean).slice(0,2).join(" ").slice(0,140)}
function progressDocAccordion(title,label,raw,htmlText,open=false){const preview=progressDocPreview(raw,`${label} 尚未設定。`);return`<details class="doc-fold"${open?" open":""}><summary><div class="doc-fold-title"><b>${esc(title)}</b><div class="summary">${esc(preview)}</div></div><span class="doc-fold-arrow">›</span></summary><div class="doc-fold-body">${htmlText}</div></details>`}
function progressLifecycleStepKey(details,featureCount){if((details.status||"").includes("已完成")||(details.current||"").includes("已完成"))return"release";if(details.workflow.stage==="1")return"planning";if(details.workflow.stage==="2")return"architecture";if(details.workflow.stage==="3")return"basic-system";if(details.workflow.stage==="4"&&featureCount>0)return"feature-1";if(details.workflow.stage==="5")return"acceptance";if((details.task||"").includes("尚未設定"))return"planning";return"foundation"}
function progressLifecycleHtml(details,src){const features=prdFeatures(src.prd.raw);const activeKey=progressLifecycleStepKey(details,features.length);const stageFeatureList=(items)=>items.length?`<ul class="lifecycle-features">${items.map(item=>`<li>${esc(item)}</li>`).join("")}</ul>`:"";const featureStages=features.map((item,index)=>[`feature-${index+1}`,`功能階段 ${index+1}`,"依專案規劃把單一功能模組完整做出來，做完再進下一個功能。",[item]]);const steps=[["planning","第 0 階段：專案規劃","先把需求方向、使用者痛點、第一版目標與不做的事講清楚。",["確認專案背景、目標、痛點與不做的事","把整體需求整理成可開發的 PRD"]],["foundation","第 1 階段：建立基礎文件","先建立專案規則與需求文件，讓後面每一步都有依據。",["建立 AGENTS.md","建立 PRD.md","建立 .gitignore 與種子 DUAL-AI-STATE.md"]],["architecture","第 2 階段：建開發環境與系統架構","把開發環境、資料夾結構、主要模組與資料流先搭好。",["建立開發環境與必要套件","規劃資料夾結構與模組邊界","決定資料流、路由、資料庫或 API 架構"]],["basic-system","第 3 階段：先做出基本系統","先把整個系統骨架做出來，至少能看出完整頁面與核心入口。",["登入功能","使用者管理","網頁介面規劃","整個框架頁面完成"]],...featureStages,["acceptance","最後階段：驗收","把所有功能串起來檢查，確認真的能用。",["整體功能驗收","修最後的阻擋問題","確認驗收標準都有達成"]],["release","上架階段","完成收尾、部署或上架，並把狀態檔更新乾淨。",["更新 DUAL-AI-STATE.md / NEXT-AI-TASK.md","建立本地 commit","部署 / 上架 / 是否 push 交回使用者決定"]]];return`<div class="workflow-guide">${steps.map(([key,label,text,items])=>`<div class="guide-item${activeKey===key?" state-stage-active":""}"><div class="guide-label">${esc(label)}</div><div class="guide-text">${esc(text)}</div>${stageFeatureList(items)}</div>`).join("")}</div>`}
function progressStageMapHtml(parsed,src){const details=parseProjectStageDetails(src);const roleMap={1:"Claude Code（VS Code）",2:"Claude Code（VS Code）",3:"Codex",4:"Claude Code（VS Code）",5:"Codex"};const role=details.workflow.stage?roleMap[details.workflow.stage]||"尚未判斷":"尚未判斷";const subline=src.projectType!=="console"?"這裡顯示的是你目前選到的專案狀態，不再混入控制台自己的版本歷史。":"這裡只顯示目前真正做到哪一階段，不再顯示控制台自己的版本地圖。";return`<div class="card"><h2>目前開發階段</h2><div class="summary">${esc(subline)}</div><div class="state-summary"><div class="state-item full"><div class="state-label">任務名稱</div><div class="state-value">${esc(details.task)}</div></div><div class="state-item"><div class="state-label">目前階段</div><div class="state-value">${esc(details.current)}</div></div><div class="state-item"><div class="state-label">目前負責 AI</div><div class="state-value">${esc(role)}</div></div><div class="state-item full"><div class="state-label">目前狀態</div><div class="state-value">${esc(details.status||"尚未設定。")}</div></div><div class="state-item full"><div class="state-label">交棒目的</div><div class="state-value">${esc(details.nextTask.handoff||"尚未設定。")}</div></div><div class="state-item"><div class="state-label">下一棒 AI</div><div class="state-value">${esc(details.nextTask.nextOwner||"尚未設定。")}</div></div><div class="state-item"><div class="state-label">最後更新</div><div class="state-value">${esc(details.updated)}</div></div></div></div>`}
function progressStatusHtml(parsed,src){const details=parseProjectStageDetails(src);if(!parsed.ok||!src.state.raw.trim()||!details.current||details.current==="尚未設定。"||!details.task||details.task==="尚未設定。")return"";return progressStageMapHtml(parsed,src)}
function progressProjectHtml(src){const projectIntro=(src.agents.raw.match(/專案簡介：\s*(.*)/)||[])[1]?.trim()||"尚未設定。";const goal=mdSection(src.prd.raw,"2. 專案目標");const pains=mdSection(src.prd.raw,"3. 專案痛點").split(/\n/).map(line=>line.trim()).filter(line=>line.startsWith("|")&& !line.includes("---")).slice(1,5).map(line=>line.split("|")[2]?.trim()).filter(Boolean);const features=prdFeatures(src.prd.raw).slice(0,4);return`<div class="card"><h2>整個專案系統簡介</h2><div class="summary">${esc(projectIntro)}</div><div class="summary">${esc(goal)}</div><div class="state-summary" style="margin-top:6px"><div class="state-item full"><div class="state-label">這個系統主要在解決什麼？</div><div class="state-value">${esc(pains.join("、")||"尚未設定。")}</div></div><div class="state-item full"><div class="state-label">核心能力</div><div class="state-value">${esc(features.join("、")||"尚未設定。")}</div></div></div></div>`}
function parseProjectPlanStages(raw){
  if(!(raw||"").trim())return[];
  const text=raw.replace(/\r\n/g,"\n");
  const parts=text.split(/\n(?=##\s+)/);
  const stages=[];
  for(const part of parts){
    const m=part.match(/^##\s+(.+?)\n([\s\S]*)$/);
    if(!m)continue;
    const title=m[1].trim();
    const body=m[2].trim();
    const bodyLines=body.split(/\n/).map(l=>l.trim());
    const descLines=[];
    const bullets=[];
    let inBullets=false;
    for(const line of bodyLines){
      if(!line)continue;
      if(/^###?\s/.test(line))continue;
      if(/^[-*]\s/.test(line)){
        inBullets=true;
        let txt=line.replace(/^[-*]\s+/,"").replace(/^\*\*(.+?)\*\*[:：]?\s*/,"$1：").trim();
        const idMatch=txt.match(/^(\d+\.\d+)[\s:：]/);
        const id=idMatch?idMatch[1]:null;
        if(id)txt=txt.slice(idMatch[0].length).trim();
        bullets.push({id:id,text:txt});
      }else if(!inBullets&&descLines.length<2){
        descLines.push(line);
      }
    }
    const desc=descLines.join(" ").slice(0,200);
    const stageMatch=title.match(/第\s*(\d+)\s*階段/);
    const stageNum=stageMatch?parseInt(stageMatch[1],10):null;
    stages.push({title:title,desc:desc,bullets:bullets,stageNum:stageNum});
  }
  return stages;
}
const PLAN_DETECTION_RULES={
  "1.1":[/\/PRD( \d+)?\.md$/i],
  "1.2":[/\/PRD( \d+)?\.md$/i],
  "1.3":[/\/PRD( \d+)?\.md$/i],
  "1.4":[/\/PRD( \d+)?\.md$/i],
  "1.5":[/\/PRD( \d+)?\.md$/i],
  "1.6":[/\/AGENTS\.md$/i],
  "1.8":[/\/PRD( \d+)?\.md$/i],
  "2.2":[/\/(data|scripts|docs|skills)\/[^/]+$/i],
  "2.3":[/\/\.git\//i,/\/\.gitkeep$/i],
  "2.4":[/\/\.gitignore$/i],
  "2.6":[/\/index\.html$/i],
  "2.7":[/\/scripts\/build\.py$/i],
  "3.3":[/\/data\/skills\.yaml$/i],
  "3.4":[/\/data\/skills\.yaml$/i],
  "3.5":[/\/data\/skills\.yaml$/i],
  "3.6":[/\/data\/skills\.yaml$/i],
  "3.7":[/\/data\/prompts\.yaml$/i],
  "3.8":[/\/scripts\/build\.py$/i],
  "3.9":[/\/index\.html$/i],
  "3.10":[/\/index\.html$/i],
  "4.14":[/\/docs\/skill-console-plan\.md$/i],
  "4.15":[/\/docs\/(v1-1-plan|v1-2-backlog)\.md$/i],
  "5.9":[/\/docs\/(v1-1-plan|v1-2-backlog)\.md$/i],
  "6.1":[/\/README( \d+)?\.md$/i],
  "6.2":[/\/README( \d+)?\.md$/i],
  "6.3":[/\/codex-skills-backup\.tar\.gz$/i],
  "6.4":[/\/install( \d+)?\.sh$/i],
  "6.5":[/\/install( \d+)?\.ps1$/i],
  "6.6":[/\/restore-skills\.sh$/i],
  "6.8":[/\/CHANGELOG\.md$/i]
};
function detectPlanDone(filePaths){
  const paths=(filePaths||[]).map(p=>"/"+p);
  const done=new Set();
  for(const id of Object.keys(PLAN_DETECTION_RULES)){
    const rules=PLAN_DETECTION_RULES[id];
    for(const re of rules){
      if(paths.some(p=>re.test(p))){done.add(id);break;}
    }
  }
  return done;
}
function progressPlanStagesHtml(src){
  const plan=src.plan||{raw:"",html:""};
  const stages=parseProjectPlanStages(plan.raw);
  const planPrompt="請幫我建立一份「專案規劃表.md」，用繁體中文把這個專案從第 0 步準備、需求整理、環境架設、基礎系統、功能開發、驗收、上架，依序拆成可理解的階段。每個階段都要寫出：這一階段要做什麼、會產出什麼、完成後怎麼判斷可以進下一步。";
  if(!stages.length){
    return`<div class="card" style="margin-top:12px"><div class="section-head"><h2>本專案的全部開發階段</h2><span class="hint">尚未找到 專案規劃表.md</span></div><div class="summary">沒有在這個專案找到 <code>專案規劃表.md</code>。複製下方提示詞讓 AI 幫你建立這份規劃表；建好後重新選擇資料夾，這裡就會自動顯示所有開發階段的資訊卡。</div><div class="workflow-guide" style="margin-top:8px"><div class="guide-item"><div class="guide-label">建立 專案規劃表.md</div><div class="guide-text">交給 AI 依照專案背景、痛點與功能清單，拆出第 0 階段到驗收、上架的完整階段。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(planPrompt)}">複製「請 AI 寫專案規劃表」提示詞</button></div></div></div>`;
  }
  const done=detectPlanDone(src.filePaths);
  const stageStats=stages.map(s=>{
    const tracked=s.bullets.filter(b=>b.id);
    const doneCount=tracked.filter(b=>done.has(b.id)).length;
    const total=tracked.length;
    const isDone=total>0&&doneCount===total;
    const isUntouched=total>0&&doneCount===0;
    return{doneCount:doneCount,total:total,isDone:isDone,isUntouched:isUntouched};
  });
  let currentStageIdx=stageStats.findIndex(st=>st.total>0&&!st.isDone);
  if(currentStageIdx<0)currentStageIdx=stages.length-1;
  let currentBulletStage=-1,currentBulletIdx=-1;
  for(let i=0;i<stages.length&&currentBulletStage<0;i++){
    for(let j=0;j<stages[i].bullets.length;j++){
      const b=stages[i].bullets[j];
      if(b.id&&!done.has(b.id)){currentBulletStage=i;currentBulletIdx=j;break;}
    }
  }
  const totalSteps=stageStats.reduce((s,st)=>s+st.total,0);
  const doneSteps=stageStats.reduce((s,st)=>s+st.doneCount,0);
  const progressPct=totalSteps?Math.round(doneSteps/totalSteps*100):0;
  let nextStepLabel="全部完成 🎉";
  if(currentBulletStage>=0){
    const b=stages[currentBulletStage].bullets[currentBulletIdx];
    nextStepLabel=`${b.id}：${b.text.slice(0,50)}${b.text.length>50?"…":""}`;
  }
  const currentTitle=stages[currentStageIdx]?stages[currentStageIdx].title:"—";
  const banner=`<div class="plan-progress-banner"><div class="plan-progress-row"><div class="plan-progress-cell"><div class="plan-prog-label">目前開發階段</div><div class="plan-prog-value">${esc(currentTitle)}</div></div><div class="plan-progress-cell"><div class="plan-prog-label">下一個小步驟</div><div class="plan-prog-value plan-prog-next">${esc(nextStepLabel)}</div></div><div class="plan-progress-cell"><div class="plan-prog-label">總進度</div><div class="plan-prog-value">${doneSteps} / ${totalSteps}　<span class="plan-prog-pct">(${progressPct}%)</span></div></div></div><div class="plan-prog-bar"><span style="width:${progressPct}%"></span></div><div class="plan-prog-hint">系統會依專案資料夾裡實際存在的關鍵檔案，自動判斷每個小步驟是否完成。</div></div>`;
  const sourceLabel=(src.path||src.name||"目前專案")+"/專案規劃表.md";
  const stagesHtml=stages.map((s,i)=>{
    const st=stageStats[i];
    let status,statusClass;
    if(st.total===0){status="參考";statusClass="ref";}
    else if(st.isDone){status="✓ 已完成";statusClass="done";}
    else if(i===currentStageIdx){status="⏳ 進行中";statusClass="current";}
    else if(st.isUntouched){status="⭕ 尚未開始";statusClass="todo";}
    else{status="⏳ 部分完成";statusClass="partial";}
    const open=(i===currentStageIdx)?" open":"";
    const countText=st.total>0?`${st.doneCount} / ${st.total}`:"";
    const stepsHtml=s.bullets.map((b,j)=>{
      const isStepDone=b.id&&done.has(b.id);
      const isCurrentStep=(i===currentBulletStage&&j===currentBulletIdx);
      let cls="plan-step";
      if(isStepDone)cls+=" done";
      else if(isCurrentStep)cls+=" current";
      else if(b.id)cls+=" todo";
      else cls+=" note";
      const mark=isStepDone?"✓":(isCurrentStep?"➤":(b.id?"○":"·"));
      const idTag=b.id?`<span class="plan-step-id">${b.id}</span>`:"";
      return`<li class="${cls}"><span class="plan-step-mark">${mark}</span>${idTag}<span class="plan-step-text">${esc(b.text)}</span></li>`;
    }).join("");
    const descHtml=s.desc?`<div class="plan-stage-desc">${esc(s.desc)}</div>`:"";
    return`<details class="plan-stage status-${statusClass}"${open}><summary><span class="plan-stage-badge badge-${statusClass}">${status}</span><span class="plan-stage-title">${esc(s.title)}</span>${countText?`<span class="plan-stage-count">${countText}</span>`:""}<span class="plan-stage-caret">▸</span></summary><div class="plan-stage-body">${descHtml}<ul class="plan-step-list">${stepsHtml}</ul></div></details>`;
  }).join("");
  return`<div class="card" style="margin-top:12px"><div class="section-head"><h2>本專案的全部開發階段</h2><span class="hint">來自 ${esc(sourceLabel)}</span></div><div class="summary">這張卡會依專案資料夾內實際存在的關鍵檔案自動判斷進度，告訴你目前做到哪一個階段、哪一個小步驟。點任一階段標題可展開／收合內容。</div>${banner}<div class="plan-list">${stagesHtml}</div></div>`;
}
function progressStagesHtml(src){return progressStageFlowHtml()+progressPlanStagesHtml(src)}
function progressAcceptanceHtml(src){const listHtml=items=>items.length?`<ul class="lifecycle-features">${items.map(item=>`<li>${esc(item)}</li>`).join("")}</ul>`:`<div class="summary">尚未設定。</div>`;const acceptanceInfo=promptInfoByTitle("驗收專案功能是否可交付","請幫我做這個專案版本的驗收檢查，先不要直接改程式。");const githubInfo=promptInfoByTitle("首次上傳 GitHub：繁體中文專案敘述","請協助我準備這個專案首次上傳 GitHub 的繁體中文說明與存檔流程。");const deployInfo=promptInfoByTitle("部署讓別人也能訪問（含 Docker）","我要讓這個專案在本地設備或雲端伺服器上，讓拿到網址的人都能訪問。");return`<div class="card"><h2>驗收與上傳資訊卡</h2><div class="summary">這裡是最後收尾區。先確認這一版能不能交付，再決定要不要本地 commit、上傳 GitHub 做開發中備份，或正式部署上線給別人使用。</div><div class="workflow-guide" style="margin-top:12px"><div class="guide-item"><div class="guide-label">1. 驗收</div><div class="guide-text">先驗收，確認功能正常、沒有阻擋問題，這一版真的可以交付。</div>${listHtml(["先確認核心流程是否可用","確認沒有 P0 / P1 阻擋問題","確認這一版是否已達到交付標準"])}</div><div class="guide-item"><div class="guide-label">2. 備份上傳</div><div class="guide-text">如果這一版只是先存開發中的版本，就整理說明後上傳 GitHub 做備份與接續。</div>${listHtml(["GitHub：偏向版本備份與多人接續","適合自己或團隊之後再接著開發","上傳前先把這一版的說明整理好"])}</div><div class="guide-item"><div class="guide-label">3. 正式上架</div><div class="guide-text">如果這一版要給別人直接打開網址使用，就要確認最後準備上架到哪裡，並安排正式部署。</div>${listHtml(["先確認最後要部署到哪個平台或主機","正式上架：偏向讓外部使用者實際訪問","上架前先完成驗收，再安排部署"])}</div></div><div class="workflow-guide" style="margin-top:12px"><div class="guide-item"><div class="guide-label">驗收提示詞</div><div class="guide-text">先檢查這個版本是否真的可交付，還缺哪些驗收資訊。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(acceptanceInfo.prompt)}">複製驗收提示詞</button></div><div class="guide-item"><div class="guide-label">上傳 GitHub 提示詞</div><div class="guide-text">把這個版本整理成繁體中文說明，再上傳 GitHub 當作開發中的備份。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(githubInfo.prompt)}">複製上傳 GitHub 提示詞</button></div><div class="guide-item"><div class="guide-label">正式上架提示詞</div><div class="guide-text">如果要讓別人真的打開網址使用，就用這張提示詞安排正式部署。</div><button class="copy-btn" type="button" style="margin-top:8px" data-copy="${encodeURIComponent(deployInfo.prompt)}">複製正式上架提示詞</button></div></div></div>`}
function progressDocsHtml(src){return`<div class="card"><h2>專案文件伸縮資訊卡</h2><div class="summary">這裡把 <code>AGENTS.md</code>、<code>PRD.md</code>、<code>DUAL-AI-STATE.md</code>、<code>NEXT-AI-TASK.md</code> 都改成可展開／收合的資訊卡，先看摘要，需要時再打開全文。</div><div class="doc-accordion">${progressDocAccordion("AGENTS.md","AGENTS",src.agents.raw,src.agents.html,true)}${progressDocAccordion("PRD.md","PRD",src.prd.raw,src.prd.html)}${progressDocAccordion("DUAL-AI-STATE.md","DUAL-AI-STATE",src.state.raw,src.state.html)}${progressDocAccordion("NEXT-AI-TASK.md","NEXT-AI-TASK",src.next.raw,src.next.html)}</div></div>`}
function progressHtml(){const src=progressSource();const parsed=parseWorkflowState(src.state.raw);const body={startup:progressStartupHtml(),status:progressStatusHtml(parsed,src),project:progressProjectHtml(src),stages:progressStagesHtml(src),docs:progressDocsHtml(src),acceptance:progressAcceptanceHtml(src)}[progressMode]||progressStatusHtml(parsed,src);return`<div class="sop progress-sop">${progressPickerHtml(src)}${progressFileCheckHtml(src)}${progressModeButtons()}${body}</div>`}
async function filesFromDirectoryHandle(handle,prefix=""){const files=[];for await (const entry of handle.values()){const nextPrefix=prefix?`${prefix}/${entry.name}`:entry.name;if(entry.kind==="file"){const file=await entry.getFile();try{Object.defineProperty(file,"webkitRelativePath",{configurable:true,value:nextPrefix})}catch{}files.push(file)}else if(entry.kind==="directory"){files.push(...await filesFromDirectoryHandle(entry,nextPrefix))}}return files}
async function loadProjectFolder(files,rootName=""){const list=[...files];if(!list.length){progressPickerMessage="沒有讀到任何檔案；請確認你選的是資料夾，而且瀏覽器允許讀取。";render();return}const root=rootName||(list[0]?.webkitRelativePath||"").split("/")[0]||"使用者選擇的專案";const find=name=>list.find(file=>file.name===name||file.webkitRelativePath.endsWith(`/${name}`));const read=async name=>{const file=find(name);return file?await file.text():""};const state=await read("DUAL-AI-STATE.md"),next=await read("NEXT-AI-TASK.md"),agents=await read("AGENTS.md"),prd=await read("PRD.md"),plan=await read("專案規劃表.md");const filePaths=list.map(f=>f.webkitRelativePath||f.name);selectedProject={name:root,path:root,state:{raw:state,html:simpleMarkdownHtml(state,"DUAL-AI-STATE")},next:{raw:next,html:simpleMarkdownHtml(next,"NEXT-AI-TASK")},agents:{raw:agents,html:simpleMarkdownHtml(agents,"AGENTS")},prd:{raw:prd,html:simpleMarkdownHtml(prd,"PRD")},plan:{raw:plan,html:simpleMarkdownHtml(plan,"專案規劃表")},filePaths:filePaths,projectType:"picked"};progressPickerMessage=`已載入資料夾：${root}`;progressMode="status";render()}
async function pickProjectFolder(){const picker=document.getElementById("projectFolderInput");if(window.showDirectoryPicker){try{const handle=await window.showDirectoryPicker();const files=await filesFromDirectoryHandle(handle);await loadProjectFolder(files,handle.name);return}catch(err){if(err?.name==="AbortError")return;if(!picker){progressPickerMessage=`資料夾選取失敗：${err?.message||"目前瀏覽器不支援。"}`;render();return}}}if(!picker){progressPickerMessage="找不到備援的資料夾選取元件，請重新整理頁面再試。";render();return}picker.value="";try{picker.click()}catch(err){progressPickerMessage=`這個瀏覽器沒有成功打開資料夾選取視窗：${err?.message||"可能不支援 file:// 下的資料夾存取。"}`;render()}}
function bindProgress(){document.querySelectorAll("[data-progress-mode]").forEach(btn=>btn.onclick=()=>{progressMode=btn.dataset.progressMode;render()});document.querySelectorAll("[data-progress-flow]").forEach(btn=>btn.onclick=()=>{progressFlow=btn.dataset.progressFlow;render()});const picker=document.getElementById("projectFolderInput");const pickBtn=document.querySelector("[data-progress-pick]");if(pickBtn)pickBtn.onclick=()=>pickProjectFolder();if(picker)picker.onchange=e=>loadProjectFolder(e.target.files);document.querySelectorAll("[data-progress-startup-copy]").forEach(btn=>btn.onclick=()=>copyText(decodeURIComponent(btn.dataset.progressStartupCopy),btn));document.querySelectorAll("[data-progress-next-prompts-toggle]").forEach(btn=>btn.onclick=()=>{progressNextPromptOpen=!progressNextPromptOpen;render()});document.querySelectorAll("[data-progress-intro]").forEach(el=>el.ontoggle=()=>{if(el.open)localStorage.setItem(progressIntroSeenKey(),"seen")})}
function stateBoardHtml(){const draft=stateDraft();const parsed=parseWorkflowState(draft);return`<div class="card state-board"><h2>DUAL-AI-STATE 快速看板</h2><div class="summary">把狀態檔全文貼在這裡，控制台只在瀏覽器本機解析與暫存，不上傳、不寫回檔案。</div><textarea id="workflowStateInput" placeholder="貼上 DUAL-AI-STATE.md 全文">${esc(draft)}</textarea><div id="workflowStateResult">${stateSummaryHtml(parsed)}</div></div>`}
function updateControlActive(stage){document.querySelectorAll("[data-control-card-stage]").forEach(card=>card.classList.toggle("state-stage-active",!!stage&&card.dataset.controlCardStage===stage))}
function controlHtml(){const parsed=parseWorkflowState(stateDraft());return`${stateBoardHtml()}<div class="grid">${CONTROL_STAGES.map(item=>{const meta=STAGE_META.dualai[item.stage]||[item.stage,item.purpose];const info=controlPromptInfo(item);const prompt=info.prompt||`請進入 dual-ai-workflow ${meta[0]}，依目前專案實際狀態接續。`;const active=parsed.stage&&item.stage===parsed.stage?" state-stage-active":"";return`<div class="card${active}" data-control-card-stage="${esc(item.stage)}"><h3>${esc(meta[0])} <span class="cat-tag">${esc(item.role)}</span></h3><div class="usage">${esc(item.purpose)}</div><div class="summary">${esc(item.plain)}</div><div class="usage">prompt 已複製到剪貼簿，提示詞庫已切到二刀流協作，請對照階段瀏覽。</div><button class="copy-btn" data-control-stage="${esc(info.targetStage)}" data-control-prompt="${esc(info.targetPrompt)}" data-control-copy="${encodeURIComponent(prompt)}">跳到提示詞庫並複製 prompt</button></div>`}).join("")}</div>`}
function bindControl(){document.querySelectorAll("[data-control-stage]").forEach(btn=>btn.onclick=()=>{copyText(decodeURIComponent(btn.dataset.controlCopy),btn);const targetStage=btn.dataset.controlStage;const targetPrompt=btn.dataset.controlPrompt;setTimeout(()=>{flowMode="dualai";q="";document.getElementById("searchBox").value="";setTab("prompts");setTimeout(()=>{const target=targetPrompt?[...document.querySelectorAll("[data-prompt-key]")].find(card=>card.dataset.promptKey===targetPrompt):null;(target||document.querySelector(`[data-stage="${targetStage}"]`))?.scrollIntoView({behavior:"smooth",block:"start"})},80)},260)})}
function bindStateBoard(){const input=document.getElementById("workflowStateInput");const result=document.getElementById("workflowStateResult");if(input&&result)input.oninput=()=>{localStorage.setItem("workflow-state-draft",input.value);const parsed=parseWorkflowState(input.value);result.innerHTML=stateSummaryHtml(parsed);updateControlActive(parsed.stage)}}
const PROMPT_CATEGORIES=["專案啟動","開發過程","版本控制","整合串接","上線部署","二刀流協作","Skill 管理","安全檢查","二刀流工作流","單一 AI 精簡","其他"];
const PROMPT_CAPTURE_METHODS=["從網頁提取提示詞","從痛點產生提示詞"];
const PROMPT_CAPTURE_TARGETS=["提示詞庫","日常提示詞","開發進度"];
function storageKey(){return captureMode==="skill"?"capture-draft-skill":"capture-draft-prompt"}
function readDraft(){try{return JSON.parse(localStorage.getItem(storageKey())||"{}")}catch{return{}}}
function writeDraft(data){localStorage.setItem(storageKey(),JSON.stringify(data))}
function formVal(id){return document.getElementById(id)?.value||""}
function formChecked(id){return !!document.getElementById(id)?.checked}
function detailStateKey(name){return `capture-detail-${captureMode}-${name}`}
function detailOpen(name){return localStorage.getItem(detailStateKey(name))==="open"}
function setDetailOpen(name,open){localStorage.setItem(detailStateKey(name),open?"open":"closed")}
function yamlScalar(value){return (value||"").replace(/\\/g,"\\\\").replace(/"/g,'\\"')}
function yamlBlock(value,indent="  "){const lines=(value||"").split(/\r?\n/);return lines.map(line=>indent+line).join("\n")}
function optionsHtml(list,active){return list.map(item=>`<option value="${esc(item)}" ${item===active?"selected":""}>${esc(item)}</option>`).join("")}
function promptCategories(){return PROMPT_CATEGORIES}
function skillCategories(){return [...new Set(DATA.skills.map(s=>s.category)),"其他"]}
function promptDraft(){const data=readDraft();return{method:data.method||"從網頁提取提示詞",target:data.target||"提示詞庫",title:data.title||"",usage:data.usage||"",sourceUrl:data.sourceUrl||"",pain:data.pain||"",idea:data.idea||"",category:data.category||"專案啟動",categoryOther:data.categoryOther||"",flow:data.flow||"common",stage:data.stage||"",prompt:data.prompt||""}}
function skillDraft(){const data=readDraft();return{source:data.source||""}}
function captureData(){if(captureMode==="skill")return{source:formVal("skillSource")};return{method:formVal("promptMethod")||"從網頁提取提示詞",target:formVal("promptTarget")||"提示詞庫",title:formVal("promptTitle"),usage:formVal("promptUsage"),sourceUrl:formVal("promptSourceUrl"),pain:formVal("promptPain"),idea:formVal("promptIdea"),category:formVal("promptCategory")==="其他"?formVal("promptCategoryOther"):formVal("promptCategory"),categoryOther:formVal("promptCategoryOther"),flow:formVal("promptFlow")||"common",stage:formVal("promptStage"),prompt:formVal("promptText")}}
function promptYaml(d){return`- title: ${d.title||"【標題】"}\n  category: ${d.category||"專案啟動"}\n  usage: ${d.usage||"【用途】"}\n  flow: ${d.flow||"common"}\n  stage: '${yamlScalar(d.stage||"")}'\n  prompt: |-\n${yamlBlock(d.prompt||"【提示詞內容】","    ")}`}
function skillYaml(d){return`# Skill 模式不需要手寫 YAML。\n# source 會從上方 Skill 網址欄自動帶入；Codex 先跑安檢，安全後再整理 data/skills.yaml 欄位。\nsource: ${d.source||"【上方 Skill 網址欄尚未填寫】"}`}
function skillCapturePrompt(d){const source=d.source||"【上方 Skill 網址欄尚未填寫】";return`請幫我安裝並收錄這個 Skill，但必須先跑安檢，安全才可以安裝。\n\nSkill 來源（已由上方 Skill 網址欄自動帶入）：${source}\n\n請依序處理：\n1. 先使用本專案「安檢流程」檢查來源、腳本、權限、憑證讀取、外部下載、提示詞注入與可追溯性。\n2. 若風險為「不要裝」或有高風險不確定項，請停止，不要安裝，並用小白能懂的話說明原因。\n3. 若風險可接受，才安裝到 Codex 與 Claude Code 兩邊可讀的位置：\n   - ~/.codex/skills/\n   - ~/.claude/skills/\n4. 讀取 skill 內容後，自動整理中文摘要、分類、風險等級、觸發句與注意事項，寫入 data/skills.yaml。\n5. 執行 python3 scripts/build.py 重建 index.html。\n6. 驗證 index.html 搜尋得到新 Skill 卡片，並確認 Codex / Claude Code 安裝位置都有該 skill。\n7. 更新 codex-skills-backup.tar.gz。\n8. 回報：安檢結論、安裝位置、收錄到 data/skills.yaml 的內容、驗證結果、是否還有風險。\n9. 不要自動 commit 或 push，等使用者決定。\n10. 更新系統的skill庫、提示詞庫或是日常提示詞都新增進去`}
function promptCaptureTargetInfo(target){return{target,storageHint:target==="提示詞庫"?"寫入 data/prompts.yaml，讓提示詞庫能搜尋到。":target==="日常提示詞"?"更新日常提示詞區塊，讓新手能直接複製使用。":"更新開發進度頁相關提示詞入口，讓接手專案時找得到。"}}
function promptMethodMeta(method){return(method||"從網頁提取提示詞")==="從網頁提取提示詞"?{label:"從網頁提取提示詞",summaryTitle:"收錄預覽",summaryHint:"下面這段只是給你確認 AI 會怎麼分類與收錄。",promptTitle:"推薦複製：一次完成網頁提取＋分類收錄",promptHelp:"你只要複製一次下面這段，AI 就會先從網址抓出提示詞，再直接整理並收進你指定的位置。",cta:"複製一次完成提示詞"}:{label:"從痛點產生提示詞",summaryTitle:"收錄預覽",summaryHint:"下面這段只是給你確認 AI 會怎麼分類與收錄。",promptTitle:"推薦複製：一次完成痛點生成＋分類收錄",promptHelp:"你只要複製一次下面這段，AI 就會先根據你的痛點設計提示詞，再直接整理並收進你指定的位置。",cta:"複製一次完成提示詞"}}
function promptSummary(d){const targetInfo=promptCaptureTargetInfo(d.target||"提示詞庫");const isUrlMode=(d.method||"從網頁提取提示詞")==="從網頁提取提示詞";const sourceBlock=isUrlMode?`來源網址：${d.sourceUrl||"尚未填寫"}\n提取任務：先從這個網址抓出網頁裡明確出現的提示詞文字，再整理分類後收進系統。`:`你的痛點：${d.pain||"尚未填寫"}\n你的想法：${d.idea||"未填寫"}\n生成任務：先根據痛點與想法產生新提示詞，再整理分類後收進系統。`;return`目前表單輸入預覽\n\n收錄方式：${d.method||"從網頁提取提示詞"}\n寫入系統：${targetInfo.target}\n寫入說明：${targetInfo.storageHint}\n標題：${d.title||"尚未填寫，之後可讓 AI 自動命名"}\n用途：${d.usage||"尚未填寫，可交給 AI 補寫"}\n${sourceBlock}\n補充分類：${d.category||"專案啟動"}\n適用流程：${d.flow||"common"}\n階段：${d.stage||"未填寫"}\n\n已整理好的提示詞原文：\n${d.prompt||"尚未填寫"}\n\n提醒：這張卡會跟著你上面欄位即時更新。`}
function codexCapturePrompt(d){if(captureMode==="skill")return skillCapturePrompt(d);const targetInfo=promptCaptureTargetInfo(d.target||"提示詞庫");const extraction=(d.method||"從網頁提取提示詞")==="從網頁提取提示詞"?`來源網址：${d.sourceUrl||"【尚未填寫】"}\n\n請先打開這個網址，提取網頁裡明確出現的「提示詞文字」或可直接複製使用的提示內容。\n不要只摘要網頁主題，也不要只寫你的理解；要先把網頁裡真正可用的提示詞內容抽出來。\n提取完成後，再依內容幫我判斷要收進提示詞庫、日常提示詞或開發進度的哪一類。\n如果網頁裡沒有明確提示詞、內容太零碎，或看起來不適合直接收錄，請停止並回報原因。`:`使用者痛點：${d.pain||"【尚未填寫】"}\n使用者想法：${d.idea||"【可留空】"}\n\n請根據上面的痛點與想法，先幫我設計一段新手也能直接複製使用的提示詞。`;
return`請幫我把一筆新提示詞收錄進系統，但先幫我整理內容，不要直接亂寫。\n\n這是我目前在表單裡輸入的內容，請以這些內容為準：\n- 收錄方式：${d.method||"從網頁提取提示詞"}\n- 寫入系統：${targetInfo.target}\n- 建議標題：${d.title||"尚未填寫，可由 AI 自動命名"}\n- 建議用途：${d.usage||"尚未填寫，可由 AI 根據內容補寫"}\n- 來源網址：${d.sourceUrl||"尚未填寫"}\n- 補充分類：${d.category||"專案啟動"}\n- 流程：${d.flow||"common"}\n- 階段：${d.stage||"未填寫"}\n- 已整理好的提示詞原文：${d.prompt||"尚未填寫"}\n\n來源說明：\n${extraction}\n\n請依序處理：\n1. 先檢查內容是否適合收錄，若有不清楚、過度空泛或風險高的地方，先停下來說明。\n2. 幫我整理成最終可收錄版本；如果標題或用途沒填，請根據內容一起補寫。\n3. 如果原文不足，請補成完整可用提示詞。\n4. 依「寫入系統」決定更新位置：${targetInfo.storageHint}\n5. 如果是提示詞庫，請同步整理成 data/prompts.yaml 可接受的格式。\n6. 執行 python3 scripts/build.py 重建 index.html。\n7. 驗證更新後的頁面能在對應區塊找到新內容。\n8. 回報：最後寫入哪裡、整理後的提示詞全文、驗證結果、是否還有風險。\n9. 不要自動 commit 或 push，等使用者決定。`}
function captureMissing(d){if(captureMode==="skill")return[!d.source&&"Skill 網址或路徑"].filter(Boolean);const missing=[];if((d.method||"從網頁提取提示詞")==="從網頁提取提示詞"){if(!d.sourceUrl)missing.push("來源網址")}else{if(!d.pain)missing.push("痛點")}if(!d.target)missing.push("寫入系統");return missing}
function captureLinkHtml(d,mode){const missing=captureMissing(d);const status=missing.length?(mode==="skill"?"請先填上方 Skill 網址欄":`還差：${missing.join("、")}`):mode==="skill"?"已連到上方 Skill 網址，可複製提示詞":"已可複製整理＋收錄提示詞";const first=mode==="skill"?["貼上 Skill 網址","只要貼 GitHub URL 或本機資料夾路徑。"]:[(d.method||"從網頁提取提示詞")==="從網頁提取提示詞"?"貼上網址":"講出痛點", (d.method||"從網頁提取提示詞")==="從網頁提取提示詞"?"讓 AI 先從網頁抓出提示詞內容。":"讓 AI 先根據你的需求生出提示詞。"];const second=mode==="skill"?["下方自動產生","提示詞會讀取上方網址，要求 AI 先安檢，安全後才安裝。"]:["自動整理並收錄",`會依你選的「${esc(d.target||"提示詞庫")}」更新到對應系統。`];return`<div class="capture-link" id="captureLink"><div class="capture-step"><span>1</span><div><b>${esc(first[0])}</b><small>${esc(first[1])}</small></div></div><div class="capture-arrow">→</div><div class="capture-step"><span>2</span><div><b>${esc(second[0])}</b><small>${esc(second[1])}</small></div></div><div class="capture-status">${esc(status)}</div></div>`}
function captureHtml(mode=captureMode,showSwitch=true){captureMode=mode;const d=mode==="skill"?skillDraft():promptDraft();const categoryList=mode==="skill"?skillCategories():promptCategories();const category=d.categoryOther?"其他":d.category;const otherStyle=category==="其他"?"":"display:none";const yaml=mode==="skill"?skillYaml(d):promptSummary(d);const codex=codexCapturePrompt(d);const methodMeta=mode==="prompt"?promptMethodMeta(d.method):null;const headerTitle=mode==="skill"?"把新 Skill 收進 Skill庫":"把新提示詞收進系統";const headerSummary=mode==="skill"?"貼上 Skill 網址或資料夾路徑，下方會自動產生安檢＋安裝提示詞；安全後再交給 Codex 寫入 Skill庫與安裝位置。":"分成兩種做法：貼網址讓 AI 抽出網頁裡的提示詞，或直接講你的痛點讓 AI 幫你生提示詞；最後再收進提示詞庫、日常提示詞或開發進度。";const resultTitle=mode==="skill"?"推薦複製：一次完成安檢＋安裝＋收錄":methodMeta.promptTitle;const resultHelp=mode==="skill"?"你只要複製一次下面這段，AI 就會先跑安檢；安全後再安裝到 Codex 與 Claude Code，並同步收錄 Skill庫相關資料。":methodMeta.promptHelp;const previewTitle=mode==="skill"?"安裝預覽":"收錄預覽";const previewHelp=mode==="skill"?"下面這段只是給你確認 AI 會怎麼安檢、安裝與收錄，不需要再另外複製第二次。":"這段只是給你確認 AI 會怎麼分類與收錄，不需要再另外複製第二次。";const mainBtn=mode==="skill"?"複製一次完成提示詞":methodMeta.cta;return`<div class="sop wide-sop" id="captureWorkspace" data-show-switch="${showSwitch?"1":"0"}"><div class="card"><h2>${headerTitle}</h2>${showSwitch?`<div class="capture-switch"><button class="capture-btn ${mode==="prompt"?"active":""}" data-capture-mode="prompt">提示詞</button><button class="capture-btn ${mode==="skill"?"active":""}" data-capture-mode="skill">Skill</button></div>`:""}<div class="summary">${headerSummary}</div></div><div class="card"><h2>${mode==="skill"?"Skill 收錄表單":"提示詞收錄表單"}</h2>${mode==="skill"?skillForm(d):promptForm(d,categoryList,category,otherStyle)}</div>${captureLinkHtml(d,mode)}<div class="card"><div class="section-head"><h2>${resultTitle}</h2><span class="hint">${esc(mode==="skill"?"安檢＋安裝＋收錄":"提取 / 生成 ＋ 分類收錄")}</span></div><div class="summary">${resultHelp}</div><pre class="prompt-body" id="captureCodex">${esc(codex)}</pre><div class="summary" style="margin-top:10px"><b>${previewTitle}</b></div><div class="summary" style="margin-top:6px">${previewHelp}</div><pre class="prompt-body" id="captureYaml">${esc(yaml)}</pre><div class="home-panel-actions" style="margin-top:10px"><button class="copy-btn" id="captureCodexBtn" data-copy="${encodeURIComponent(codex)}">${mainBtn}</button></div></div></div>`}
function promptForm(d,cats,category,otherStyle){const isUrlMode=(d.method||"從網頁提取提示詞")==="從網頁提取提示詞";const targetInfo=promptCaptureTargetInfo(d.target||"提示詞庫");const targetExplain=d.target==="提示詞庫"?"適合正式收錄成可搜尋卡片。":d.target==="日常提示詞"?"適合新手直接複製、每天反覆使用。":"適合放進接手專案、交接、下一步提示的流程裡。";return`<div class="workflow-guide" style="margin-bottom:14px"><div class="guide-item"><div class="guide-label">方法 1</div><div class="guide-text">在網頁看到好用提示詞時，只貼網址，讓 Codex 或 Claude Code 先幫你抽內容。</div></div><div class="guide-item"><div class="guide-label">方法 2</div><div class="guide-text">如果是你自己想研發的新提示詞，就只講痛點和想法，讓 AI 幫你先產生。</div></div><div class="guide-item"><div class="guide-label">收去哪裡</div><div class="guide-text">可直接指定收進提示詞庫、日常提示詞或開發進度，後面由 AI 幫你更新對應系統。</div></div></div><div class="card" style="padding:14px; margin-bottom:14px"><b>現在會收進：${esc(d.target||"提示詞庫")}</b><div class="summary" style="margin-top:6px">${esc(targetExplain)}</div><div class="summary" style="margin-top:6px">${esc(targetInfo.storageHint)}</div></div><div class="form-grid"><div class="field"><label>收錄方式</label><select id="promptMethod" data-capture-input>${optionsHtml(PROMPT_CAPTURE_METHODS,d.method)}</select><div class="help">選你現在是哪一種來源。</div></div><div class="field"><label>寫入系統</label><select id="promptTarget" data-capture-input>${optionsHtml(PROMPT_CAPTURE_TARGETS,d.target)}</select><div class="help">決定最後要收進哪一頁系統。</div></div><div class="field"><label>標題</label><input id="promptTitle" data-capture-input value="${esc(d.title)}" placeholder="可留空，讓 AI 幫你命名"><div class="help">如果已經想好名稱可以先填，沒有也沒關係。</div></div><div class="field"><label>用途</label><input id="promptUsage" data-capture-input value="${esc(d.usage)}" placeholder="可留空，讓 AI 幫你補寫這段提示詞的用途"><div class="help">這欄可以不填，後面會請 AI 根據內容自動補用途。</div></div>${isUrlMode?`<div class="field full"><label>來源網址</label><input id="promptSourceUrl" data-capture-input value="${esc(d.sourceUrl)}" placeholder="貼上有提示詞的網頁網址"><div class="help">只要貼網址，AI 會先從網頁裡找可收錄的提示詞。</div></div>`:`<div class="field full"><label>你的痛點</label><textarea id="promptPain" data-capture-input placeholder="例如：我每次交辦 AI 做市場比對時，問題都問得太散，回來的內容很亂。">${esc(d.pain)}</textarea><div class="help">直接講你現在卡住的地方。</div></div><div class="field full"><label>你的想法</label><textarea id="promptIdea" data-capture-input placeholder="例如：我希望它先幫我列比對表，再補差異與建議。">${esc(d.idea)}</textarea><div class="help">有想法就補，沒有可留空。</div></div>`}<details class="doc-fold" data-capture-detail="prompt-advanced" style="margin-top:4px"${detailOpen("prompt-advanced")?" open":""}><summary><div class="doc-fold-title"><b>進階補充欄位</b><div class="summary">大多數情況可不填，只有你想微調收錄方式時再展開。</div></div><span class="doc-fold-arrow">›</span></summary><div class="doc-fold-body"><div class="form-grid"><div class="field"><label>補充分類</label><select id="promptCategory" data-capture-input>${optionsHtml(cats,category)}</select><input id="promptCategoryOther" data-capture-input style="${otherStyle}" value="${esc(d.categoryOther)}" placeholder="輸入其他分類"><div class="help">這是給 AI 的整理提示，不想選也可先用預設。</div></div><div class="field"><label>適用流程</label><select id="promptFlow" data-capture-input>${optionsHtml(["common","dualai","solo"],d.flow)}</select><div class="help">不確定就選 common。</div></div><div class="field"><label>階段</label><input id="promptStage" data-capture-input value="${esc(d.stage)}" placeholder="entry / 1 / 2 / 3 / 4 / 5 / archive"><div class="help">如果和開發階段有關，再補這欄。</div></div><div class="field full"><label>已整理好的提示詞原文（選填）</label><textarea id="promptText" data-capture-input placeholder="如果你手上已經有完整提示詞，可以直接貼這裡。">${esc(d.prompt)}</textarea><div class="help">有現成原文才需要貼，沒有就交給 AI 整理。</div></div></div></div></details></div>`}
function skillForm(d){return`<div class="form-grid"><div class="field full"><label>Skill 網址或資料夾路徑</label><input id="skillSource" data-capture-input class="${d.source?"":"needs-input"}" value="${esc(d.source)}" placeholder="貼上 GitHub URL 或本機資料夾路徑"><div class="help">這裡就是下方提示詞會讀取的 Skill 來源；貼上後會自動帶入安檢＋安裝提示詞。</div></div></div>`}
function rerenderCaptureWorkspace(){const root=document.getElementById("captureWorkspace");if(!root){render();return}const showSwitch=root.dataset.showSwitch==="1";const activeId=document.activeElement?.id||"";const start=document.activeElement&&typeof document.activeElement.selectionStart==="number"?document.activeElement.selectionStart:null;const end=document.activeElement&&typeof document.activeElement.selectionEnd==="number"?document.activeElement.selectionEnd:null;root.outerHTML=captureHtml(captureMode,showSwitch);bindCapture();if(activeId){const next=document.getElementById(activeId);if(next){next.focus();try{if(start!==null&&end!==null&&typeof next.setSelectionRange==="function")next.setSelectionRange(start,end)}catch{}}}}
function updateCaptureOutputs(){const data=captureData();const yaml=captureMode==="skill"?skillYaml(data):promptSummary(data);const codex=codexCapturePrompt(data);const yamlPre=document.getElementById("captureYaml"),codexPre=document.getElementById("captureCodex"),link=document.getElementById("captureLink"),skillSource=document.getElementById("skillSource"),codexBtn=document.getElementById("captureCodexBtn");if(yamlPre)yamlPre.textContent=yaml;if(codexPre)codexPre.textContent=codex;if(link)link.outerHTML=captureLinkHtml(data,captureMode);if(skillSource)skillSource.classList.toggle("needs-input",captureMode==="skill"&&!data.source);if(codexBtn)codexBtn.dataset.copy=encodeURIComponent(codex)}
function bindCapture(){document.querySelectorAll("[data-capture-mode]").forEach(btn=>btn.onclick=()=>{captureMode=btn.dataset.captureMode;render()});document.querySelectorAll("[data-capture-detail]").forEach(el=>el.ontoggle=()=>setDetailOpen(el.dataset.captureDetail,el.open));document.querySelectorAll("[data-capture-input]").forEach(el=>el.oninput=el.onchange=()=>{const data=captureData();writeDraft(data);if(["promptMethod","promptTarget","promptCategory"].includes(el.id))rerenderCaptureWorkspace();else updateCaptureOutputs()})}
const CUSTOM_SKILL_DEFAULTS={role:"AI 系統開發與管理者",industry:"",scenario:"工作決策陪練與挑刺",style:"直接、務實、先挑風險",target:"Codex 跟 Claude Code 這兩個專用",skillName:"",level:"先給結論，再補背景",pain:"我需要一個懂我職務、業務痛點與工作習慣的 AI 陪練，能先追問、再挑刺、最後把流程封裝成可重複使用的 skill。",extra:"請用繁體中文。不要無腦誇。需求不清楚時先問關鍵問題。涉及安裝或改檔時先說風險。"};
const CUSTOM_SKILL_FIELDS=["customRole","customIndustry","customScenario","customStyle","customTarget","customSkillName","customLevel","customPain","customExtra"];
const AUTOMATION_DEFAULTS={name:"",problem:"",pain:"",trigger:"",goal:"",output:"",type:"工作交接 / 接續專案",target:"Codex + Claude Code",frequency:"每 10 分鐘檢查一次；5 小時 / 本輪與本週剩 45% 先進第一階段提醒，30%~10% 時進正式換手提醒，10% 以下進強制收尾模式",notes:"請用繁體中文。先問不清楚的地方，再設計自動化。若 5 小時 / 本輪或本週剩 45% 以下，先提醒整理進度；若剩 30%~10%，要主動提醒產生交接摘要、停止再開新大任務；若低於 10%，要明確提醒只做必要收尾。"};
const AUTOMATION_TYPES=["工作交接 / 接續專案","整理資料 / 摘要輸出","收錄提示詞 / Skill","審查 / 驗收 / 回報","自訂"];
const AUTOMATION_TARGETS=["Codex + Claude Code","只給 Codex","只給 Claude Code"];
const AUTOMATION_FIELDS=["automationName","automationProblem","automationPain","automationTrigger","automationGoal","automationOutput","automationType","automationTarget","automationFrequency","automationNotes"];
function customSkillData(){const stored=JSON.parse(localStorage.getItem("custom-skill-builder")||"{}");return{...CUSTOM_SKILL_DEFAULTS,...stored}}
function customSkillRead(){const data={role:formVal("customRole"),industry:formVal("customIndustry"),scenario:formVal("customScenario"),style:formVal("customStyle"),target:formVal("customTarget"),skillName:formVal("customSkillName"),level:formVal("customLevel"),pain:formVal("customPain"),extra:formVal("customExtra")};localStorage.setItem("custom-skill-builder",JSON.stringify(data));return data}
function automationData(){const stored=JSON.parse(localStorage.getItem("automation-builder-draft")||"{}");return{...AUTOMATION_DEFAULTS,...stored}}
function automationRead(){const data={name:formVal("automationName"),problem:formVal("automationProblem"),pain:formVal("automationPain"),trigger:formVal("automationTrigger"),goal:formVal("automationGoal"),output:formVal("automationOutput"),type:formVal("automationType")||AUTOMATION_DEFAULTS.type,target:formVal("automationTarget")||AUTOMATION_DEFAULTS.target,frequency:formVal("automationFrequency")||AUTOMATION_DEFAULTS.frequency,notes:formVal("automationNotes")};localStorage.setItem("automation-builder-draft",JSON.stringify(data));return data}
function automationRecords(){try{return JSON.parse(localStorage.getItem("automation-records")||"[]")}catch{return[]}}
function saveAutomationRecords(items){localStorage.setItem("automation-records",JSON.stringify(items))}
function automationFormOpen(){const stored=localStorage.getItem("automation-form-open");return stored===null?true:stored==="open"}
function automationPromptText(d){const name=d.name?.trim()||"請根據問題與痛點自動命名";return[`我要建立一套可重複使用的 AI 自動化流程，讓 Codex 與 / 或 Claude Code 之後可以依照固定提示詞幫我執行。`,"",`自動化基本資料：`,`- 自動化名稱：${name}`,`- 自動化類型：${d.type}`,`- 建置目標：${d.target}`,`- 要解決的問題：${d.problem||"請先追問我，釐清目前問題。"}`,`- 目前痛點：${d.pain||"請先追問我，釐清真實痛點。"}`,`- 觸發自動化的提示詞：${d.trigger||"【請在這裡填入平常會講給 AI 的觸發句】"}`,`- 希望達成的結果：${d.goal||"【請補上想要的最終結果】"}`,`- 預期輸出 / 動作：${d.output||"【請補上輸出格式、要產生的檔案、回報方式】"}`,`- 使用頻率：${d.frequency}`,`- 其他限制：${d.notes||"請用繁體中文，需求不清楚時先問。"}`
,"","請依序處理：","1. 先用最多 5 個問題補齊缺的資訊；如果已經足夠，就直接進下一步。","2. 根據上面的問題、痛點與觸發句，設計一套「可重複使用的自動化流程規格」。","3. 請把流程拆成：觸發條件、輸入資料、執行步驟、輸出結果、例外處理、安全界線。","4. 產出一段給 Codex 用的自動化建置提示詞。","5. 如果目標包含 Claude Code，也另外產出一段給 Claude Code 用的自動化建置提示詞。","6. 幫我整理一份可顯示在管理頁的自動化卡片資料，至少包含：名稱、用途、痛點、觸發提示詞、預期輸出、風險提醒。","7. 如果這套流程適合封裝成 skill、固定模板或管理 SOP，也請提出建議。","8. 不要直接刪檔或批量改檔；若要寫檔或安裝，先列出計畫與風險，等我確認。"
,"","輸出格式請固定為：","A. 自動化摘要","B. 需要確認的問題","C. 流程規格","D. 給 Codex 的建置提示詞","E. 給 Claude Code 的建置提示詞（如果需要）","F. 管理頁顯示卡片資料","G. 風險與注意事項"].join("\n")}
function automationRecordCard(item,index){const target=item.target||AUTOMATION_DEFAULTS.target;const type=item.type||AUTOMATION_DEFAULTS.type;const prompt=item.prompt||automationPromptText(item);const created=item.createdAt||"";return`<div class="automation-record"><div class="automation-record-head"><div><div class="automation-record-title">${esc(item.name||"未命名自動化")}</div><div class="automation-meta"><span>${esc(type)}</span><span>${esc(target)}</span><span>${esc(item.frequency||AUTOMATION_DEFAULTS.frequency)}</span></div></div><div class="automation-counter">#${index+1}</div></div><div class="automation-kv"><div class="automation-kv-item"><b>要解決的問題</b><div class="summary">${esc(item.problem||"未填寫")}</div></div><div class="automation-kv-item"><b>目前痛點</b><div class="summary">${esc(item.pain||"未填寫")}</div></div><div class="automation-kv-item"><b>觸發提示詞</b><pre class="prompt-body">${esc(item.trigger||"未填寫")}</pre></div><div class="automation-kv-item"><b>預期輸出 / 動作</b><div class="summary">${esc(item.output||"未填寫")}</div></div>${created?`<div class="automation-kv-item"><b>建立時間</b><div class="summary">${esc(created)}</div></div>`:""}</div><div class="automation-record-actions"><button class="copy-btn" type="button" data-copy="${encodeURIComponent(prompt)}">複製建置提示詞</button><button class="copy-btn tutorial-btn" type="button" data-automation-load="${index}">載入回表單</button><button class="copy-btn tutorial-btn" type="button" data-automation-delete="${index}">刪除這筆</button></div></div>`}
function automationRecordsHtml(){const items=automationRecords();if(!items.length)return`<div class="automation-empty">還沒有建立任何自動化。先在上方填入問題、痛點與觸發提示詞，存檔後這裡就會列出你已設定的自動化動作。</div>`;return`<div class="automation-records">${items.map(automationRecordCard).join("")}</div>`}
function customSkillInstallInstruction(d){if(d.target==="Codex + Claude Code 都安裝（缺一也繼續）")return["安裝到 Codex 與 Claude Code 兩邊可讀的位置。","如果其中一個軟體沒有安裝、路徑不存在，或該環境暫時不能寫入，另一邊仍要繼續完成，不要整體中止。","除了安裝 SKILL.md，也要額外產出可直接貼到 Codex 與 Claude Code 的個人化提示詞 / 自定義指令版本，方便我手動放到兩邊 AI 的個人設定裡。"].join(" ");if(d.target==="先只產生 SKILL.md，不安裝")return"這一輪只產生 SKILL.md、安裝計畫與個人化提示詞，不要實際安裝。";return`依「${d.target}」處理，並同步產出可直接貼上的個人化提示詞版本。`}
function customSkillPromptText(d){const skillName=d.skillName?.trim()||"請根據我的角色、用途與痛點自動命名";return[`我想建立一個自己的個人化專屬 skill，請用 Codex 跟 Claude Code 這兩個專用流程協助我完成。`,"",`我的基本設定：`,`- 我的職業 / 身分：${d.role}`,`- 我的行業別：${d.industry||"尚未填寫，請先追問我所屬產業或服務類型"}`,`- 主要用途：${d.scenario}`,`- 期待 AI 互動風格：${d.style}`,`- 回答深度：${d.level}`,`- Skill 名稱：${skillName}`,`- 安裝目標：${d.target}`,`- 目前痛點：${d.pain||"請先追問我，協助我釐清。"}`,`- 其他要求：${d.extra||"請用繁體中文，需求不清楚時先問。"}`,"","第一段：徹底理解我","現在你的首要身份是一個提問者。","請你問我所有你需要的問題，直到你真正理解：","1. 我的職務與日常工作情境","2. 我的行業別與所屬產業特性","3. 我的業務核心訴求","4. 我的真實痛點","5. 我最常卡住的決策點","6. 我希望 AI 在工作中扮演的角色","","請一次最多問 5 個問題。問題要具體、好回答；必要時提供選項。","不要急著產出 skill。你要先問到能和我一起梳理出清晰路徑。","","第二段：做我的陪練與挑刺者","根據你對我的了解，接下來做我的陪練。","不管我提出什麼想法，不管我拋出什麼計劃，禁止無腦誇。","你的唯一任務是挑刺，請直白指出 3 到 5 個：","1. 我沒想到的風險點","2. 我忽略的關鍵問題","3. 可能導致失敗的假設","4. 需要先驗證的地方","5. 更務實的下一步","","輸出格式請固定為：","結論 / 建議","3 到 5 個風險點","我應該先回答或確認的問題","下一步最小行動","","第三段：封裝成 skill","當你已經懂我的痛點、職務人設、行業背景與工作方式後，請幫我封裝成一個 skill。","請產出完整 skill 資料夾設計，至少包含：",`1. skill 名稱：${skillName}`,"2. SKILL.md 完整內容","3. 觸發規則：什麼情境下 AI 必須使用這個 skill","4. AI 回答規則：語氣、格式、禁止事項、風險提醒方式","5. 範例觸發句：至少 5 句","6. 安裝前風險檢查：是否會讀寫檔案、是否需要網路、是否接觸敏感資料","7. 另外產出個人化提示詞 / 自定義指令版本：至少一份給 Codex、一份給 Claude Code","",`SKILL.md 要適合 ${d.target}，並且用繁體中文說明清楚。`,"","第四段：安裝與驗證","請在封裝完成後，先停止並列出安裝計畫與風險。","如果我確認要安裝，才進行安裝。","","安裝要求：","1. 不要刪除任何既有文件或資料夾。","2. 不要使用批量刪除指令。","3. 安裝前先檢查目標路徑是否存在。",`4. ${customSkillInstallInstruction(d)}`,"5. 安裝後驗證該 skill 的 SKILL.md 存在。","6. 回報安裝位置、檔案清單、如何觸發、如何測試。","7. 回報兩份個人化提示詞 / 自定義指令內容：一份給 Codex，一份給 Claude Code。","","請先從第一段開始，不要跳到第三段，也不要直接寫檔。"].join("\n")}
function portableSkillName(d){return(d.skillName||"").trim()||"開發決策陪練與挑刺官"}
function portableSkillSlug(name){return name.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g,"-").replace(/^-+|-+$/g,"")||"personal-work-coach"}
function portableSkillSummary(d){return[d.role,d.industry?`${d.industry}情境`:"",d.scenario].filter(Boolean).join(" / ")}
function portableSkillArtifacts(d){const skillName=portableSkillName(d);const slug=portableSkillSlug(skillName);const scenario=d.scenario||"工作決策陪練與挑刺";const style=d.style||"顧問式追問、先釐清再行動";const level=d.level||"只給最短可執行版本";const industry=d.industry||"請先追問使用者所屬產業或服務類型";const pain=d.pain||"請先追問使用者目前最真實的工作痛點";const extra=d.extra||"請用繁體中文。需求不清楚時先問。涉及改檔或安裝時先說風險。";const summary=portableSkillSummary(d);const skillMd=`---\nname: ${skillName}\ndescription: 先追問釐清需求，再挑刺風險與錯誤假設，最後收斂成最短可執行下一步。適合 ${scenario}。\n---\n\n# ${skillName}\n\n## 使用者背景\n- 職業 / 身分：${d.role}\n- 行業別：${industry}\n- 主要用途：${scenario}\n- 互動風格：${style}\n- 回答深度：${level}\n- 真實痛點：${pain}\n\n## 核心任務\n1. 先問清楚，不要急著做\n2. 先用白話解釋現在在解什麼問題\n3. 直白指出風險、漏洞、錯誤假設\n4. 收斂成最小可執行下一步\n5. 在一個功能能跑通後，提醒是否先做版本備份\n\n## 何時必須啟用\n- 使用者丟出模糊想法，需要先判斷值不值得做\n- 使用者丟出計畫、spec、prompt、skill 草稿，要你挑刺\n- 使用者卡在不知道先做哪一步\n- 使用者需要你把技術問題翻成白話\n- 使用者需要先做出可見畫面或可執行原型，再逐步細修\n- 使用者擔心系統改完後重開、換環境、部署後會壞\n\n## 工作規則\n1. 第一題預設先問：你這次真正要解的問題是什麼\n2. 若需求、目標、成功條件不清楚，先追問，單次最多 5 題\n3. 回答一律使用繁體中文\n4. 不要無腦誇\n5. 若涉及改檔、安裝、部署、重要設定，先講風險再動手\n6. 先用白話解釋這次改動在解什麼問題，再講怎麼做\n7. 回答只給最短可執行版本\n8. 如果資訊不足，不要亂猜，要先指出缺什麼\n\n## 固定輸出格式\n### 結論 / 建議\n- 這次在解什麼問題\n- 現在最值得先做哪一步\n\n### 3 到 5 個風險點\n- 沒想到的風險點\n- 忽略的關鍵問題\n- 可能導致失敗的假設\n- 需要先驗證的地方\n- 更務實的下一步\n\n### 我應該先回答或確認的問題\n列出最影響決策的 1 到 3 題。\n\n### 下一步最小行動\n只給當下最小、最務實、最容易驗證的一步。\n\n## 額外要求\n${extra}\n`;const agentsMd=`# 個人化規則：${skillName}\n\n## 角色\n你是我的${skillName}。\n先釐清，再行動。不要無腦誇。\n\n## 我的工作背景\n- ${summary}\n- 主要用途：${scenario}\n- 真實痛點：${pain}\n\n## 互動原則\n1. 第一優先先問：這次真正要解的問題是什麼\n2. 需求不清楚時，最多一次問 5 題\n3. 先用白話說明這次在解什麼問題，再給建議\n4. 回答只給最短可執行版本\n5. 一個功能能跑通後，提醒是否先做版本備份\n6. 若系統重開後打不開，優先判斷是否為啟動、路徑、服務、權限、設定或環境差異問題\n7. 涉及改檔、安裝、部署、重要設定時，先說風險\n\n## 固定輸出\n- 結論 / 建議\n- 3 到 5 個風險點\n- 我應該先回答或確認的問題\n- 下一步最小行動\n\n## 禁止\n- 無腦誇\n- 沒問清楚就直接做\n- 長篇空話\n- 高風險改動前不提醒風險\n`;const claudeMd=`# 個人化規則：${skillName}\n\n你先做討論與釐清，不要急著做結論。\n你的任務是先追問、再挑刺、再收斂成最小下一步。\n\n## 使用者背景\n- 職業 / 身分：${d.role}\n- 行業別：${industry}\n- 主要用途：${scenario}\n- 痛點：${pain}\n\n## 必做\n1. 第一題先問：這次真正要解的問題是什麼\n2. 需求不清楚時，最多一次問 5 題\n3. 先白話解釋，再給建議\n4. 若涉及改檔、安裝、部署、重要設定，先提醒風險\n5. 回答維持最短可執行版本\n6. 一個功能能跑通後，提醒是否要先做版本備份\n\n## 固定輸出\n- 結論 / 建議\n- 3 到 5 個風險點\n- 我應該先回答或確認的問題\n- 下一步最小行動\n\n## 禁止\n- 無腦誇\n- 沒問清楚就下結論\n- 長篇理論堆砌\n- 把不確定的事講成確定\n`;const codexPrompt=`你是我的「${skillName}」。\n\n我的背景：\n- 我是 ${d.role}\n- 我的行業別：${industry}\n- 我的主要用途：${scenario}\n- 我的痛點：${pain}\n- 我偏好：${style}\n- 回答深度：${level}\n\n你在 Codex 的角色：\n- 負責查修、修改落地、細部畫面調整\n- 在可執行原型或畫面出來後，協助往下細修\n- 小階段完成後，提醒是否適合備份、上傳、上架\n- 若系統重開或換環境後出問題，先做問題分類再排查\n\n你的規則：\n1. 需求不清楚時，先問關鍵問題，最多一次 5 題\n2. 不要無腦誇\n3. 涉及改檔、安裝、部署、重要設定前，先說風險\n4. 先用白話說明這次在解什麼問題，再講怎麼做\n5. 不要給長篇理論，只給最短可執行版本\n6. 若一個功能已跑通，主動提醒我可考慮先做版本備份\n7. 若資訊不足，不要亂猜，先指出缺什麼資訊\n\n固定輸出格式：\n- 結論 / 建議\n- 3 到 5 個風險點\n- 我應該先回答或確認的問題\n- 下一步最小行動\n`;const claudePrompt=`你是我的「${skillName}」。\n\n我的背景：\n- 我是 ${d.role}\n- 我的行業別：${industry}\n- 我的主要用途：${scenario}\n- 我的痛點：${pain}\n- 我偏好：${style}\n- 回答深度：${level}\n\n你在 Claude Code 的角色：\n- 先討論、先追問、先幫我釐清真正問題\n- 開始開發前，先把目標、限制、成功條件收斂\n- 每做到一小階段，就回頭複查方向、風險、驗證方式是否成立\n- 不要急著產出方案，先幫我縮小問題\n\n你的規則：\n1. 第一優先先問：我這次真正要解的問題是什麼\n2. 若需求還模糊，先追問，不要直接跳解法\n3. 不要無腦誇，只做陪練、挑刺、收斂\n4. 先用新手也懂的方式解釋目前在做什麼\n5. 每次回覆盡量短，但要能直接執行\n6. 若涉及改檔、安裝、部署，先提醒風險\n7. 若發現方向可能錯，直說，不要包裝\n\n固定輸出格式：\n- 結論 / 建議\n- 3 到 5 個風險點\n- 我應該先回答或確認的問題\n- 下一步最小行動\n`;function installPrompt(target){const targetText=target==="codex"?"Codex":"Claude Code";const globalName=target==="codex"?"AGENTS.md":"CLAUDE.md";const globalContent=target==="codex"?agentsMd:claudeMd;const globalPath=target==="codex"?"~/.codex/AGENTS.md":"~/.claude/CLAUDE.md";const skillPath=target==="codex"?`~/.codex/skills/${slug}/SKILL.md`:`~/.claude/skills/${slug}/SKILL.md`;const promptContent=target==="codex"?codexPrompt:claudePrompt;return`請幫我在這台電腦安裝一份可攜式個人化 skill 到 ${targetText}。\n\n要求：\n1. 先檢查目標路徑是否存在；不存在就建立，但不要刪除任何既有資料夾。\n2. 安裝前先回報風險：是否會寫檔、是否會覆蓋、是否涉及全域規則。\n3. 建立 skill 目錄並寫入 SKILL.md。\n4. 同步產出一份 ${globalName} 全域規則檔；若既有檔案存在，不要直接覆蓋，先備份或合併。\n5. 回報安裝位置、檔案清單、如何觸發、如何測試。\n6. 不要自動 commit 或 push。\n\n目標檔案：\n- ${skillPath}\n- ${globalPath}\n\nSKILL.md 內容如下：\n\`\`\`md\n${skillMd}\n\`\`\`\n\n${globalName} 內容如下：\n\`\`\`md\n${globalContent}\n\`\`\`\n\n給 ${targetText} 的個人化提示詞如下：\n\`\`\`md\n${promptContent}\n\`\`\`\n`}const installBothPrompt=`請幫我在這台電腦安裝一份可攜式個人化 skill 到 Codex 與 Claude Code，缺一也繼續。\n\n要求：\n1. 先檢查這台電腦是否已有 Codex 與 Claude Code 可用路徑。\n2. 安裝前先回報風險：哪些檔案會被寫入、哪些路徑不存在、哪些地方可能和既有全域規則衝突。\n3. Codex 與 Claude Code 兩邊都要各自建立 skill 目錄與 SKILL.md。\n4. 另外產出兩份全域規則檔：Codex 用 AGENTS.md，Claude Code 用 CLAUDE.md；若既有檔案存在，不要直接覆蓋，先備份或合併。\n5. 最後回報：成功安裝到哪裡、哪一邊因缺少路徑而跳過、如何觸發、如何測試。\n6. 不要刪除任何既有文件，不要自動 commit 或 push。\n\n以下是要安裝的內容。\n\n=== SKILL.md ===\n\`\`\`md\n${skillMd}\n\`\`\`\n\n=== Codex AGENTS.md ===\n\`\`\`md\n${agentsMd}\n\`\`\`\n\n=== Claude Code CLAUDE.md ===\n\`\`\`md\n${claudeMd}\n\`\`\`\n\n=== 給 Codex 的個人化提示詞 ===\n\`\`\`md\n${codexPrompt}\n\`\`\`\n\n=== 給 Claude Code 的個人化提示詞 ===\n\`\`\`md\n${claudePrompt}\n\`\`\`\n`;return{skillName,slug,skillMd,agentsMd,claudeMd,codexPrompt,claudePrompt,installCodexPrompt:installPrompt("codex"),installClaudePrompt:installPrompt("claude"),installBothPrompt}}
function customSkillBundleSection(title,summary,body,copyLabel){return`<div class="guide-item"><div class="guide-label">${esc(title)}</div><div class="guide-text">${esc(summary)}</div><pre class="prompt-body builder-preview" style="margin-top:8px">${esc(body)}</pre><div class="home-panel-actions" style="margin-top:8px"><button class="copy-btn" type="button" data-copy="${encodeURIComponent(body)}">${esc(copyLabel)}</button></div></div>`}
function customSkillBundleHtml(artifacts){return`<div class="card"><div class="section-head"><h2>雙刀流個人化設定包</h2><span class="hint">把 5 份內容合成一張資訊卡</span></div><div class="summary">這不是單一檔案，而是一組給雙刀流工作一起用的設定包。用途是把你的個人化 skill、本機全域規則，以及兩個 AI 的專屬提示詞一次整理好。</div><div class="summary" style="margin-top:8px"><b>如果你要長期用 Codex + Claude Code 雙刀流，這 5 份建議一起設定。</b> 這樣 Codex 負責查修、落地、細修時，和 Claude Code 負責追問、挑刺、複查時，會吃到同一套人設與規則，不容易兩邊講法不同。</div><div class="workflow-guide" style="margin-top:12px"><div class="guide-item"><div class="guide-label">這個動作會做什麼</div><div class="guide-text">先產出可攜式 <code>SKILL.md</code>、全域規則檔、Codex 提示詞、Claude Code 提示詞。後面你可以只複製內容，也可以交給下方的自動安裝動作，讓 AI 幫你落地到本機。</div></div><div class="guide-item"><div class="guide-label">會形成什麼功能</div><div class="guide-text">1. 你每次開新任務時，AI 會先問清楚再動手。2. Codex 與 Claude Code 會各自遵守相同的人設與風險規則。3. 你在不同電腦、不同專案之間，也比較容易維持一致的工作方式。</div></div><div class="guide-item"><div class="guide-label">什麼情況一定要設</div><div class="guide-text">如果你只是偶爾單次使用，可以只複製提示詞；但如果你要把這套流程變成長期雙刀流工作模式，建議這 5 份一起設，否則很容易出現一邊會追問、另一邊直接亂做的情況。</div></div>${customSkillBundleSection("1. SKILL.md","這是核心 skill 本體。它定義你的角色、人設、觸發情境、固定輸出格式。",""+artifacts.skillMd,"複製 skill.md 建置提示詞")}${customSkillBundleSection("2. AGENTS.md","這是給 Codex 端用的全域規則檔，讓它進專案時先照你的工作習慣行動。",""+artifacts.agentsMd,"複製 agents.md 建置提示詞")}${customSkillBundleSection("3. CLAUDE.md","這是給 Claude Code 端用的全域規則檔，讓它先追問、先挑刺、先複查。",""+artifacts.claudeMd,"複製 claude.md 建置提示詞")}${customSkillBundleSection("4. 給 Codex 的個人化提示詞","這是你臨時不想安裝、只想快速貼給 Codex 開工時用的版本。",""+artifacts.codexPrompt,"複製 Codex 提示詞")}${customSkillBundleSection("5. 給 Claude Code 的個人化提示詞","這是你臨時不想安裝、只想快速貼給 Claude Code 討論或複查時用的版本。",""+artifacts.claudePrompt,"複製 Claude 提示詞")}</div></div>`}
function customSkillInstallHtml(artifacts){return`<div class="card"><div class="section-head"><h2>自動安裝動作</h2><span class="hint">改成提示詞自動下載與安裝</span></div><div class="summary">這一區不再提供下載檔案。按下按鈕後，會先把對應安裝提示詞放到剪貼簿，再嘗試切到指定 AI，讓它接手幫你安裝。</div><div class="workflow-guide" style="margin-top:12px"><div class="guide-item"><div class="guide-label">安裝到 Codex</div><div class="guide-text">會建立 <code>~/.codex/skills/${esc(artifacts.slug)}/SKILL.md</code>，並處理 Codex 側的全域規則與提示詞。</div><div class="home-panel-actions" style="margin-top:8px">${installWakeCard("交給 Codex 自動安裝","codex",artifacts.installCodexPrompt)}${installPromptCard("只複製 Codex 安裝提示詞",artifacts.installCodexPrompt)}</div></div><div class="guide-item"><div class="guide-label">安裝到 Claude Code</div><div class="guide-text">會建立 <code>~/.claude/skills/${esc(artifacts.slug)}/SKILL.md</code>，並處理 Claude Code 側的全域規則與提示詞。</div><div class="home-panel-actions" style="margin-top:8px">${installWakeCard("交給 Claude Code 自動安裝","claude",artifacts.installClaudePrompt)}${installPromptCard("只複製 Claude 安裝提示詞",artifacts.installClaudePrompt)}</div></div><div class="guide-item"><div class="guide-label">雙邊一起裝</div><div class="guide-text">適合你要把同一份個人化 skill 同步到這台電腦的兩個 AI 環境。</div><div class="home-panel-actions" style="margin-top:8px">${installWakeCard("交給 Codex 做雙邊安裝","codex",artifacts.installBothPrompt)}${installPromptCard("只複製雙邊安裝提示詞",artifacts.installBothPrompt)}</div></div></div></div>`}
function customSkillHtml(){const d=customSkillData();const artifacts=portableSkillArtifacts(d);return`<div class="sop wide-sop"><div class="card"><h2>自製專屬 Skill 產生器</h2><div class="summary">直接在這裡選欄位，右側會即時產生可攜式 skill 內容、兩份 AI 提示詞，以及「交給 AI 自動安裝」的提示詞。</div><div class="summary" style="margin-top:8px">建議先搭配 <b>LangGPT</b> 一起使用。它已安裝到系統裡，能幫你把職業、行業別、用途與痛點整理成更穩定的結構化 skill。</div></div><div class="home-split"><div class="card"><h2>選單設定</h2><div class="form-grid"><div class="field"><label>你的職業 / 身分</label><select id="customRole" data-custom-skill-input>${optionsHtml(["AI 系統開發與管理者","資訊主管 / IT 管理者","行政人員","業務人員","工務人員","會計人員","人事人員","採購 / 採發人員","總務 / 事務人員","行銷企劃 / 品牌經營者","資料整合 / 報表分析人員","專案經理 / 專案助理","客服 / 營運人員","設計 / 美編人員","工程師 / 軟體開發人員","門市 / 店長 / 現場管理","創業者 / 老闆","自訂"],d.role)}</select></div><div class="field"><label>行業別</label><input id="customIndustry" data-custom-skill-input value="${esc(d.industry)}" placeholder="例如：營造業、餐飲業、貿易業、電商、製造業、顧問服務"><div class="summary" style="margin-top:6px">這個欄位很重要，特別是選到創業者、老闆、業務或行政時，補上行業別後，AI 產生的 skill 會更貼近你的實際工作。</div></div><div class="field"><label>主要用途</label><select id="customScenario" data-custom-skill-input>${optionsHtml(["工作決策陪練與挑刺","AI 系統規劃與專案推進","提示詞工程與 SOP 建立","資料查詢、整合與報告產出","跨角色溝通與主管簡報"],d.scenario)}</select></div><div class="field"><label>AI 互動風格</label><select id="customStyle" data-custom-skill-input>${optionsHtml(["直接、務實、先挑風險","新手教學、一步一步帶我做","主管視角、重點摘要與決策建議","顧問式追問、先釐清再行動"],d.style)}</select></div><div class="field"><label>安裝目標</label><select id="customTarget" data-custom-skill-input>${optionsHtml(["Codex 跟 Claude Code 這兩個專用","Claude Code 專用","Codex + Claude Code 都安裝（缺一也繼續）","先只產生 SKILL.md，不安裝"],d.target)}</select></div><div class="field"><label>Skill 名稱</label><input id="customSkillName" data-custom-skill-input value="${esc(d.skillName)}" placeholder="可留白，讓 AI 自動命名"><div class="summary" style="margin-top:6px">這個欄位可以不填。留白時，會交給 AI 依照你的角色、用途與痛點自動幫你取名字。</div></div><div class="field"><label>回答深度</label><select id="customLevel" data-custom-skill-input>${optionsHtml(["先給結論，再補背景","完整深入分析","只給最短可執行版本"],d.level)}</select></div><div class="field full"><label>你目前最想解決的痛點</label><textarea id="customPain" data-custom-skill-input>${esc(d.pain)}</textarea><div class="help">可以在這裡繼續補充情境、限制、範例或你已經試過的方法。</div></div><div class="field full"><label>其他要求</label><textarea id="customExtra" data-custom-skill-input>${esc(d.extra)}</textarea><div class="help">可以在這裡補充口吻、格式、安裝偏好、禁用事項或任何額外要求。</div></div></div><div class="builder-actions"><button class="copy-btn" type="button" id="customSkillReset">清空重選</button></div></div><div class="card builder-preview-card"><h2>交辦版長提示詞</h2><pre class="prompt-body builder-preview" id="customSkillPrompt">${esc(customSkillPromptText(d))}</pre><div class="home-panel-actions"><button class="copy-btn" type="button" id="customSkillCopy">複製交辦提示詞</button></div></div></div><div class="automation-preview" style="margin-top:16px; display:grid; gap:12px;">${customSkillBundleHtml(artifacts)}${customSkillInstallHtml(artifacts)}</div></div>`}
function automationHtml(){const d=automationData();const records=automationRecords();const prompt=automationPromptText(d);const formOpen=automationFormOpen();return`<div class="sop wide-sop"><div class="card"><h2>建立 Codex / Claude Code 自動化</h2><div class="summary">先把你現在的問題、痛點與平常會講給 AI 的觸發提示詞寫進來。右側會即時生成一段「自動化建置提示詞」，你可以直接交給 Codex 或 Claude Code 幫你把流程建起來。</div><div class="automation-badges"><span class="automation-badge">先寫問題與痛點</span><span class="automation-badge">再產生建置提示詞</span><span class="automation-badge">最後把已設定自動化留在這頁管理</span></div></div><div class="automation-builder"><div class="automation-panel"><details class="doc-fold"${formOpen?" open":""} id="automationFormFold"><summary><div class="doc-fold-title"><b>自動化需求表單</b><div class="summary">這裡可以收合。要新增或修改自動化時再展開填寫。</div></div><span class="doc-fold-arrow">›</span></summary><div class="doc-fold-body"><div class="card" style="border:none; box-shadow:none; padding:14px 0 0;"><div class="form-grid"><div class="field"><label>自動化名稱</label><input id="automationName" data-automation-input value="${esc(d.name)}" placeholder="例如：專案交接自動化 / 每日摘要整理 / 提示詞收錄助手"></div><div class="field"><label>建置目標</label><select id="automationTarget" data-automation-input>${optionsHtml(AUTOMATION_TARGETS,d.target)}</select></div><div class="field"><label>自動化類型</label><select id="automationType" data-automation-input>${optionsHtml(AUTOMATION_TYPES,d.type)}</select></div><div class="field"><label>使用頻率</label><input id="automationFrequency" data-automation-input value="${esc(d.frequency)}" placeholder="例如：每天一次 / 每次接手專案時 / 有新提示詞時"></div><div class="field full"><label>要解決的問題</label><textarea id="automationProblem" data-automation-input placeholder="直接寫你現在最想解決的問題。">${esc(d.problem)}</textarea><div class="help">這一欄偏向客觀問題，例如：交接資訊很散、每次都要重講一次背景。</div></div><div class="field full"><label>目前痛點</label><textarea id="automationPain" data-automation-input placeholder="寫真實痛點，例如：每次交給不同 AI 都要重新整理規格，常常漏掉關鍵上下文。">${esc(d.pain)}</textarea><div class="help">這一欄偏向真實不方便的地方，後面會直接寫進建置提示詞。</div></div><div class="field full"><label>觸發自動化的提示詞</label><textarea id="automationTrigger" data-automation-input placeholder="如果你已經知道要怎麼觸發，就直接寫；如果你不會寫，也可以先留白，交給 AI 反問你：什麼情境下要啟動、你通常會怎麼開口、希望它先做什麼。">${esc(d.trigger)}</textarea><div class="help">不會寫也沒關係。AI 可以先追問你「要怎麼樣觸發這個動作」，再幫你整理成正式提示詞；之後這段會顯示在下方管理卡片。</div></div><div class="field full"><label>希望達成的結果</label><textarea id="automationGoal" data-automation-input placeholder="例如：自動整理成固定格式的交接摘要，包含目前階段、風險、待辦、下一步。">${esc(d.goal)}</textarea></div><div class="field full"><label>預期輸出 / 動作</label><textarea id="automationOutput" data-automation-input placeholder="例如：回傳摘要、產生 markdown、更新固定狀態欄位、列出下一步提示詞。">${esc(d.output)}</textarea></div><div class="field full"><label>其他限制或要求</label><textarea id="automationNotes" data-automation-input placeholder="例如：一定先問不清楚的地方；不能直接刪檔；要用繁體中文。">${esc(d.notes)}</textarea></div></div><div class="automation-tip">這一頁的已建立自動化清單目前先存在瀏覽器本機 <code>localStorage</code>。也就是說，同一台電腦同一個瀏覽器會記得；若要正式收進 repo，下一步可以再把你確認好的自動化整理成 YAML 或管理檔。</div><div class="home-panel-actions"><button class="copy-btn primary-copy" type="button" id="automationCopy" data-copy="${encodeURIComponent(prompt)}">複製自動化建置提示詞</button><button class="copy-btn tutorial-btn" type="button" id="automationSave">存成這頁的自動化卡片</button><button class="copy-btn tutorial-btn" type="button" id="automationReset">清空表單</button></div></div></div></details></div><div class="automation-panel automation-preview"><div class="card"><h2>給 Codex / Claude Code 的建置提示詞</h2><div class="summary">先複製這段，再貼給 Codex 或 Claude Code。它會先理解問題與痛點，再幫你設計、建置與管理這個自動化流程。</div><pre class="prompt-body builder-preview" id="automationPrompt">${esc(prompt)}</pre><div class="home-panel-actions"><button class="copy-btn" type="button" data-copy="${encodeURIComponent(prompt)}">複製這段提示詞</button><button class="copy-btn tutorial-btn" type="button" data-automation-tab="progress">我要直接接續專案</button></div></div><div class="card"><h2>你會在這頁看到什麼</h2><div class="mini-list"><div class="mini-item"><b>已設定哪些自動化</b><div class="summary">每一張卡片都會留下自動化名稱、用途、痛點與建置目標。</div></div><div class="mini-item"><b>要怎麼觸發</b><div class="summary">卡片內會直接顯示觸發提示詞，之後不用再猜這個自動化要怎麼叫出來。</div></div><div class="mini-item"><b>要產生什麼結果</b><div class="summary">每張卡片都會留預期輸出，方便你回頭檢查這個自動化是不是設對了。</div></div></div><a class="copy-btn" href="docs/ai-workflow-control-center-design.md" target="_blank" rel="noreferrer">看流程說明</a></div></div></div><div class="card"><div class="section-head"><h2>已建立的自動化</h2><span class="hint">${records.length} 筆</span></div><div class="summary">下方會列出你已經設定過哪些自動化動作，以及它們各自對應的觸發提示詞。</div>${automationRecordsHtml()}</div>`}
function updateCustomSkill(){customSkillRead();const contentEl=document.getElementById("content");if(contentEl){contentEl.innerHTML=customSkillHtml();bindCustomSkill()}}
function bindCustomSkill(){document.querySelectorAll("[data-custom-skill-input]").forEach(el=>el.oninput=el.onchange=updateCustomSkill);document.querySelectorAll("[data-wake-ai]").forEach(btn=>btn.onclick=()=>wakeAI(btn));const copy=document.getElementById("customSkillCopy");if(copy)copy.onclick=()=>copyText(document.getElementById("customSkillPrompt")?.textContent||"",copy);const reset=document.getElementById("customSkillReset");if(reset)reset.onclick=()=>{localStorage.removeItem("custom-skill-builder");const contentEl=document.getElementById("content");if(contentEl){contentEl.innerHTML=customSkillHtml();bindCustomSkill()}}}
function updateAutomation(){const d=automationRead();const out=document.getElementById("automationPrompt");const copy=document.getElementById("automationCopy");const prompt=automationPromptText(d);if(out)out.textContent=prompt;if(copy)copy.dataset.copy=encodeURIComponent(prompt)}
function bindAutomation(){updateAutomation();const fold=document.getElementById("automationFormFold");if(fold)fold.ontoggle=()=>localStorage.setItem("automation-form-open",fold.open?"open":"closed");document.querySelectorAll("[data-automation-input]").forEach(el=>el.oninput=el.onchange=updateAutomation);document.querySelectorAll("[data-automation-tab]").forEach(btn=>btn.onclick=()=>setTab(btn.dataset.automationTab));document.querySelectorAll("[data-automation-load]").forEach(btn=>btn.onclick=()=>{const item=automationRecords()[Number(btn.dataset.automationLoad)];if(!item)return;localStorage.setItem("automation-builder-draft",JSON.stringify({...AUTOMATION_DEFAULTS,...item}));localStorage.setItem("automation-form-open","open");const contentEl=document.getElementById("content");contentEl.innerHTML=automationHtml();bindAutomation()});document.querySelectorAll("[data-automation-delete]").forEach(btn=>btn.onclick=()=>{const index=Number(btn.dataset.automationDelete);const items=automationRecords();items.splice(index,1);saveAutomationRecords(items);const contentEl=document.getElementById("content");contentEl.innerHTML=automationHtml();bindAutomation()});const save=document.getElementById("automationSave");if(save)save.onclick=()=>{const d=automationRead();const items=automationRecords();const record={...d,prompt:automationPromptText(d),createdAt:new Date().toLocaleString("zh-TW",{hour12:false})};items.unshift(record);saveAutomationRecords(items);const contentEl=document.getElementById("content");contentEl.innerHTML=automationHtml();bindAutomation()};const reset=document.getElementById("automationReset");if(reset)reset.onclick=()=>{localStorage.removeItem("automation-builder-draft");localStorage.setItem("automation-form-open","open");const contentEl=document.getElementById("content");contentEl.innerHTML=automationHtml();bindAutomation()};const copy=document.getElementById("automationCopy");if(copy)copy.onclick=()=>copyText(document.getElementById("automationPrompt")?.textContent||"",copy)}
function render(){const chips=document.getElementById("chips"),content=document.getElementById("content"),countLine=document.getElementById("countLine"),search=document.querySelector(".search"),searchSlot=document.getElementById("searchSlot");if(tab==="prompts")flowMode="common";const progressTabBtn=document.querySelector('[data-tab="progress"]');if(progressTabBtn)progressTabBtn.textContent=progressFlow==="solo"?"專案開發（單刀）":"專案開發（雙刀）";renderOnlineBanner();renderLaunchTip();renderIntro();const showSearch=tab==="skills"||tab==="prompts";if(search){if(showSearch&&searchSlot){search.style.display="flex";searchSlot.appendChild(search)}else{search.style.display="none"}}chips.innerHTML=cats().map(c=>`<button class="chip ${c===cat?"active":""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");chips.querySelectorAll(".chip").forEach(ch=>ch.onclick=()=>{cat=ch.dataset.cat;if(tab==="prompts"&&cat!=="全部")flowMode="common";render()});if(tab==="backup"){countLine.textContent="";content.innerHTML=backupHtml();return}if(tab==="installGuide"){countLine.textContent="";content.innerHTML=installGuideHtml();bindInstallGuide();return}if(tab==="guide"){countLine.textContent="";content.innerHTML=homeHtml();bindHome();return}if(tab==="daily"){countLine.textContent="";content.innerHTML=dailyHtml();bindDaily();return}if(tab==="customSkill"){countLine.textContent="";content.innerHTML=customSkillHtml();bindCustomSkill();return}if(tab==="automation"){countLine.textContent="";content.innerHTML=automationHtml();bindAutomation();return}if(tab==="progress"){countLine.textContent="";content.innerHTML=progressHtml();bindProgress();return}if(tab==="skills"){const items=DATA.skills.filter(s=>(cat==="全部"||s.category===cat)&&match(s,["name","summary","category","triggers","notes"]));countLine.textContent=`共 ${items.length} 個 skill`;content.innerHTML=renderSkillLibrary();bindCapture();return}if(tab==="prompts"){const commonPrompts=DATA.prompts.filter(p=>(p.flow||"common")==="common");const count=commonPrompts.filter(p=>(cat==="全部"||p.category===cat)&&match(p,["title","usage","category","prompt","flow","stage"])).length;countLine.textContent=`目前顯示 ${count} 則提示詞，總共 ${commonPrompts.length} 則`;content.innerHTML=renderPromptFlow();bindCapture();bindPromptLibrary()}}
function setTab(next){document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));document.querySelector(`[data-tab="${next}"]`)?.classList.add("active");tab=next;localStorage.setItem(TAB_STORAGE_KEY,tab);cat="全部";render()}
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>setTab(t.dataset.tab));document.getElementById("searchBox").addEventListener("input",e=>{q=e.target.value.trim();render()});render();
</script>
</body>
</html>
'''

out = ROOT / "index.html"
html_out = (
    TEMPLATE.replace("__DATA_JSON__", data_json)
    .replace("__INSTALL_GUIDE_ASSETS__", install_guide_assets_json)
    .replace("__WORKFLOW_HTML__", workflow_json)
    .replace("__GUIDE_HTML__", guide_json)
    .replace("__STATE_HTML__", state_html)
    .replace("__NEXT_HTML__", next_html)
    .replace("__AGENTS_HTML__", agents_html)
    .replace("__PRD_HTML__", prd_html)
    .replace("__PLAN_HTML__", plan_html)
    .replace("__CONSOLE_FILE_PATHS__", console_file_paths_json)
    .replace("__PROJECT_PATH__", project_path_json)
    .replace("__PROJECT_URL__", project_url_json)
    .replace("__QUOTA_GUARDIAN_STATUS_JSON__", quota_guardian_status_json)
    .replace("__BACKUP_PROMPTS_JSON__", backup_prompts_json)
)
out.write_text(html_out, encoding="utf-8")
print(f"OK: {out} built with {len(skills)} skills / {len(prompts)} prompts / {len(combos)} combos")
