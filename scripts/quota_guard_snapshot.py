#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
CLAUDE_STATE = Path.home() / ".claude" / "cctokmon-state.json"
CLAUDE_CACHE = Path.home() / ".claude" / "cctokmon-cache.json"
CLAUDE_LOG_FILES = [
    Path.home() / "Library" / "Logs" / "Claude" / "claude.ai-web.log",
    Path.home() / "Library" / "Logs" / "Claude" / "claude.ai-web1.log",
]
CODEX_QUOTA_FILE = Path.home() / ".codex" / "quota-status.json"
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
CLAUDE_DEFAULT_CONTEXT_TOKENS = 200_000
APPLICATIONS_DIR = Path("/Applications")


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def save_json(path: Path, payload):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        return True
    except Exception:
        return False


def remaining_percent_from_used(used):
    if used is None:
        return None
    try:
        return max(0, min(100, 100 - float(used)))
    except Exception:
        return None


def remaining_text_from_timestamp(timestamp):
    if timestamp in (None, ""):
        return "尚未接上"
    try:
        target = int(timestamp)
    except Exception:
        return "尚未接上"
    try:
        now_local = datetime.now().astimezone()
        target_local = datetime.fromtimestamp(target).astimezone()
        delta_seconds = int((target_local - now_local).total_seconds())
        if delta_seconds <= 0:
            return "已重置"
        # 一律顯示「現實的幾點幾分重置」，依日期距離切標籤：
        #   今天 → 「今天 HH:MM 重置」
        #   明天 → 「明天 HH:MM 重置」
        #   更遠 → 「M/D HH:MM 重置」
        day_diff = (target_local.date() - now_local.date()).days
        hhmm = target_local.strftime("%H:%M")
        if day_diff <= 0:
            return f"今天 {hhmm} 重置"
        if day_diff == 1:
            return f"明天 {hhmm} 重置"
        return f"{target_local.month}/{target_local.day} {hhmm} 重置"
    except Exception:
        pass
    # 兜底：時區或 strftime 失敗時，退回純倒數格式
    now = int(datetime.now(timezone.utc).timestamp())
    seconds = max(0, target - now)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days > 0:
        return f"{days}天 {hours}小時"
    if hours > 0:
        return f"{hours}小時 {minutes}分"
    return f"{minutes}分鐘"


def is_future_timestamp(timestamp):
    if timestamp in (None, ""):
        return False
    try:
        target = int(timestamp)
    except Exception:
        return False
    now = int(datetime.now(timezone.utc).timestamp())
    return target > now


def unresolved_window(title, text="尚未接上"):
    return {
        "title": title,
        "remaining_percent": None,
        "remaining_text": text,
        "alert_stage": "unavailable",
    }


def alert_stage_from_remaining_percent(percent):
    if percent is None:
        return "unavailable"
    try:
        value = float(percent)
    except Exception:
        return "unavailable"
    if value <= 10:
        return "reserve"
    if value <= 30:
        return "handoff"
    if value <= 45:
        return "prepare"
    return "normal"


def codex_installed():
    return shutil.which("codex") is not None or (APPLICATIONS_DIR / "Codex.app").exists() or CODEX_QUOTA_FILE.exists()


def claude_installed():
    return (
        shutil.which("claude") is not None
        or (APPLICATIONS_DIR / "Claude.app").exists()
        or CLAUDE_SETTINGS.exists()
        or CLAUDE_STATE.exists()
        or CLAUDE_CACHE.exists()
    )


def read_codex_rate_limits():
    try:
        process = subprocess.Popen(
            ["codex", "app-server", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return None

    try:
        requests = [
            {
                "id": "0",
                "method": "initialize",
                "params": {"clientInfo": {"name": "quota-guard", "version": "0.1.0"}},
            },
            {"id": "1", "method": "account/rateLimits/read", "params": None},
        ]
        for item in requests:
            process.stdin.write(json.dumps(item, ensure_ascii=False) + "\n")
        process.stdin.flush()

        result = None
        for _ in range(12):
            line = process.stdout.readline()
            if not line:
                break
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if payload.get("id") == "1" and "result" in payload:
                result = payload["result"]
                break
        return result
    finally:
        try:
            process.terminate()
            process.wait(timeout=1)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


def codex_provider():
    result = read_codex_rate_limits()
    if result:
        snapshot = (result.get("rateLimitsByLimitId") or {}).get("codex") or result.get("rateLimits") or {}
        primary = snapshot.get("primary") or {}
        secondary = snapshot.get("secondary") or {}
        return {
            "name": "Codex",
            "source": "codex-app-server",
            "windows": [
                {
                    "title": "本輪",
                    "remaining_percent": remaining_percent_from_used(primary.get("usedPercent")),
                    "remaining_text": remaining_text_from_timestamp(primary.get("resetsAt")),
                    "alert_stage": alert_stage_from_remaining_percent(
                        remaining_percent_from_used(primary.get("usedPercent"))
                    ),
                },
                {
                    "title": "本週",
                    "remaining_percent": remaining_percent_from_used(secondary.get("usedPercent")),
                    "remaining_text": remaining_text_from_timestamp(secondary.get("resetsAt")),
                    "alert_stage": alert_stage_from_remaining_percent(
                        remaining_percent_from_used(secondary.get("usedPercent"))
                    ),
                },
            ],
        }

    data = load_json(CODEX_QUOTA_FILE)
    if not data:
        return {
            "name": "Codex",
            "source": "unavailable",
            "windows": [
                unresolved_window("本輪", "尚未接上"),
                unresolved_window("本週", "尚未接上"),
            ],
        }

    return {
        "name": "Codex",
        "source": "quota-status-json",
        "windows": [
            {
                "title": "本輪",
                "remaining_percent": remaining_percent_from_used(data.get("session_usage_percent") or data.get("usage_percent")),
                "remaining_text": remaining_text_from_timestamp(data.get("session_reset_at") or data.get("reset_at")),
                "alert_stage": alert_stage_from_remaining_percent(
                    remaining_percent_from_used(data.get("session_usage_percent") or data.get("usage_percent"))
                ),
            },
            {
                "title": "本週",
                "remaining_percent": remaining_percent_from_used(data.get("weekly_usage_percent") or data.get("week_usage_percent")),
                "remaining_text": remaining_text_from_timestamp(data.get("weekly_reset_at") or data.get("week_reset_at")),
                "alert_stage": alert_stage_from_remaining_percent(
                    remaining_percent_from_used(data.get("weekly_usage_percent") or data.get("week_usage_percent"))
                ),
            },
        ],
    }


def claude_bridge_configured():
    settings = load_json(CLAUDE_SETTINGS)
    if not isinstance(settings, dict):
        return False
    bridge_path = str(ROOT / "scripts" / "claude_quota_statusline.sh")
    wrapper_path = str(Path.home() / ".claude" / "cctokmon-bridge.sh")
    accepted = (bridge_path, wrapper_path, "claude_quota_statusline.sh", "cctokmon-bridge.sh")
    configured = settings.get("statusLine")
    cmd_str = None
    if isinstance(configured, str):
        cmd_str = configured
    elif isinstance(configured, dict) and configured.get("type") == "command":
        cmd_str = configured.get("command") or ""
    return bool(cmd_str) and any(token in cmd_str for token in accepted)


def extract_json_object(line):
    start = line.find("{")
    if start < 0:
        return None
    try:
        return json.loads(line[start:])
    except Exception:
        return None


def read_claude_rate_limit_log():
    for path in CLAUDE_LOG_FILES:
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except Exception:
            continue

        for line in reversed(lines):
            if '"type":"rate_limit_error"' not in line and '"type":"exceeded_limit"' not in line:
                continue
            payload = extract_json_object(line)
            if not isinstance(payload, dict):
                continue
            message = payload.get("message")
            if not isinstance(message, str) or '"windows"' not in message:
                continue
            try:
                detail = json.loads(message)
            except Exception:
                continue
            windows = detail.get("windows") or {}
            five_hour = windows.get("5h") or {}
            seven_day = windows.get("7d") or {}
            if not five_hour and not seven_day:
                continue
            return {
                "five_hour": five_hour,
                "seven_day": seven_day,
            }
    return None


def remaining_percent_from_utilization(window):
    if not isinstance(window, dict):
        return None
    utilization = window.get("utilization")
    if utilization is None:
        return None
    try:
        return max(0, min(100, 100 - (float(utilization) * 100)))
    except Exception:
        return None


def unresolved_claude_window(title):
    if title == "本輪":
        return unresolved_window(title, "Claude Code 平時不主動報告 5 小時配額，下次撞到限制後會自動補上")
    return unresolved_window(title, "Claude Code 平時不主動報告 7 天配額，下次撞到限制後會自動補上")


def context_window_proxy(state):
    cw = (state or {}).get("context_window") or {}
    used = cw.get("used_percentage")
    if used is None:
        used_tokens = cw.get("used_tokens")
        total_tokens = cw.get("total_tokens")
        if isinstance(used_tokens, (int, float)) and isinstance(total_tokens, (int, float)) and total_tokens:
            used = (float(used_tokens) / float(total_tokens)) * 100
    if used is None:
        return None
    try:
        used_value = float(used)
    except Exception:
        return None
    remaining = max(0.0, min(100.0, 100.0 - used_value))
    return {
        "title": "目前對話 context",
        "remaining_percent": remaining,
        "remaining_text": f"已用 {round(used_value, 1)}%（statusline 即時值）",
        "alert_stage": alert_stage_from_remaining_percent(remaining),
    }


def latest_session_usage_proxy():
    if not CLAUDE_PROJECTS_DIR.exists():
        return None
    candidates = []
    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl in project_dir.glob("*.jsonl"):
            try:
                candidates.append((jsonl.stat().st_mtime, jsonl))
            except OSError:
                continue
    if not candidates:
        return None
    candidates.sort(reverse=True)

    for _, jsonl in candidates:
        try:
            lines = jsonl.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            msg = obj.get("message") or {}
            if msg.get("role") != "assistant":
                continue
            usage = msg.get("usage") or {}
            try:
                used_tokens = (
                    int(usage.get("input_tokens") or 0)
                    + int(usage.get("cache_creation_input_tokens") or 0)
                    + int(usage.get("cache_read_input_tokens") or 0)
                )
            except Exception:
                continue
            if used_tokens <= 0:
                continue
            used_percent = (used_tokens / float(CLAUDE_DEFAULT_CONTEXT_TOKENS)) * 100
            used_percent = max(0.0, min(100.0, used_percent))
            remaining = 100.0 - used_percent
            return {
                "title": "目前對話 context",
                "remaining_percent": remaining,
                "remaining_text": f"已用 {round(used_percent, 1)}%（{used_tokens:,} / {CLAUDE_DEFAULT_CONTEXT_TOKENS:,} tokens，來源：session log）",
                "alert_stage": alert_stage_from_remaining_percent(remaining),
            }
    return None


def claude_window_from_fallback(title, window):
    timestamp = (window or {}).get("resets_at")
    if not is_future_timestamp(timestamp):
        return unresolved_claude_window(title)
    return {
        "title": title,
        "remaining_percent": remaining_percent_from_utilization(window),
        "remaining_text": remaining_text_from_timestamp(timestamp),
        "alert_stage": alert_stage_from_remaining_percent(remaining_percent_from_utilization(window)),
    }


def claude_windows_from_rate_limits(five_hour, seven_day):
    return [
        {
            "title": "本輪",
            "remaining_percent": remaining_percent_from_used(five_hour.get("used_percentage")),
            "remaining_text": remaining_text_from_timestamp(
                iso_to_timestamp(five_hour.get("resets_at"))
            ),
            "alert_stage": alert_stage_from_remaining_percent(
                remaining_percent_from_used(five_hour.get("used_percentage"))
            ),
        },
        {
            "title": "本週",
            "remaining_percent": remaining_percent_from_used(seven_day.get("used_percentage")),
            "remaining_text": remaining_text_from_timestamp(
                iso_to_timestamp(seven_day.get("resets_at"))
            ),
            "alert_stage": alert_stage_from_remaining_percent(
                remaining_percent_from_used(seven_day.get("used_percentage"))
            ),
        },
    ]


def cacheable_claude_windows(windows):
    for window in windows:
        if window.get("remaining_percent") is not None and window.get("remaining_text") not in ("尚未接上", ""):
            return True
    return False


def write_claude_cache(windows, source):
    payload = {
        "source": source,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "windows": windows,
    }
    save_json(CLAUDE_CACHE, payload)


def read_claude_cache():
    data = load_json(CLAUDE_CACHE)
    if not isinstance(data, dict):
        return None
    windows = data.get("windows")
    if not isinstance(windows, list):
        return None
    valid = []
    for item in windows:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or "限制"
        percent = item.get("remaining_percent")
        text = item.get("remaining_text") or "尚未接上"
        if percent is None and "真實" in text:
            continue
        valid.append(
            {
                "title": title,
                "remaining_percent": percent,
                "remaining_text": f"{text}（最近一次有效資料）",
                "alert_stage": alert_stage_from_remaining_percent(percent),
            }
        )
    if not valid:
        return None
    return {
        "source": data.get("source") or "cache",
        "cached_at": data.get("cached_at"),
        "windows": valid,
    }


def claude_provider():
    data = load_json(CLAUDE_STATE)
    proxy = context_window_proxy(data) if isinstance(data, dict) else None
    if proxy is None:
        proxy = latest_session_usage_proxy()

    if isinstance(data, dict):
        rate_limits = data.get("rate_limits") or {}
        five_hour = rate_limits.get("five_hour") or {}
        seven_day = rate_limits.get("seven_day") or {}
        if five_hour or seven_day:
            windows = claude_windows_from_rate_limits(five_hour, seven_day)
            if cacheable_claude_windows(windows):
                write_claude_cache(windows, "cctokmon-state")
            return {
                "name": "Claude Code",
                "source": "cctokmon-state",
                "windows": windows,
            }

    fallback = read_claude_rate_limit_log()
    if fallback and (
        is_future_timestamp((fallback.get("five_hour") or {}).get("resets_at"))
        or is_future_timestamp((fallback.get("seven_day") or {}).get("resets_at"))
    ):
        windows = [
            claude_window_from_fallback("本輪", fallback.get("five_hour")),
            claude_window_from_fallback("本週", fallback.get("seven_day")),
        ]
        if cacheable_claude_windows(windows):
            write_claude_cache(windows, "claude-rate-limit-log")
        return {
            "name": "Claude Code",
            "source": "claude-rate-limit-log",
            "windows": windows,
        }

    configured = claude_bridge_configured()
    cached = read_claude_cache()
    if cached:
        return {
            "name": "Claude Code",
            "source": "cache",
            "windows": list(cached["windows"]),
        }

    if proxy:
        # statusline 已成功觸發但平台不主動回報 5h/7d 配額，
        # 至少把 context window 用量顯示出來，讓使用者看得到「真實數據」。
        return {
            "name": "Claude Code",
            "source": "context-proxy",
            "windows": [
                unresolved_claude_window("本輪"),
                unresolved_claude_window("本週"),
                proxy,
            ],
        }

    return {
        "name": "Claude Code",
        "source": "waiting" if configured else "unavailable",
        "windows": [
            unresolved_claude_window("本輪") if configured else unresolved_window("本輪", "尚未接上"),
            unresolved_claude_window("本週") if configured else unresolved_window("本週", "尚未接上"),
        ],
    }


def iso_to_timestamp(value):
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return int(datetime.fromisoformat(value).timestamp())
    except Exception:
        return None


def main():
    providers = []
    if claude_installed():
        providers.append(claude_provider())
    if codex_installed():
        providers.append(codex_provider())
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "providers": providers,
    }
    json.dump(payload, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
