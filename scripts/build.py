#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the offline Skill console from YAML data."""

import html as html_mod
import json
import re
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
project_path_json = json.dumps(str(ROOT), ensure_ascii=False).replace("</", "<\\/")
project_url_json = json.dumps(ROOT.as_uri() + "/", ensure_ascii=False).replace("</", "<\\/")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>二刀流開發助手控制台｜Codex × Claude Code 開發系統</title>
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
  .home-kpis{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:14px;}
  .home-kpi{background:rgba(255,255,255,.82); border:1px solid var(--border); border-radius:12px; padding:12px;}
  .home-kpi b{display:block; font-size:1rem; margin-bottom:4px;}
  .home-steps{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-bottom:16px;}
  .home-step{background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; box-shadow:var(--shadow);}
  .home-step .num{display:inline-flex; width:28px; height:28px; align-items:center; justify-content:center; border-radius:999px; background:var(--accent); color:#fff; font-weight:700; margin-bottom:8px;}
  .home-step h3{font-size:1rem; margin-bottom:6px;}
  .home-split{display:grid; grid-template-columns:1.15fr .85fr; gap:14px;}
  .home-panel{background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; box-shadow:var(--shadow);}
  .home-panel h3{font-size:1rem; margin-bottom:8px;}
  .home-panel-actions{display:grid; grid-template-columns:repeat(auto-fit,minmax(142px,1fr)); gap:8px; margin-top:12px;}
  .home-panel-actions .copy-btn{font-size:.78rem; padding:8px 10px;}
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
  .intro-label,.guide-label{font-size:.74rem; color:var(--muted); margin-bottom:3px;}
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
  .daily-safety{background:rgba(46,164,79,.1); border:1px solid rgba(46,164,79,.22); border-radius:12px; padding:10px; color:#17612d; font-size:.84rem; line-height:1.6;}
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
  .install-steps{counter-reset:step; display:flex; flex-direction:column; gap:7px; margin-top:2px;}
  .install-step{display:flex; gap:8px; align-items:flex-start; font-size:.82rem; color:var(--text);}
  .install-step span{display:inline-flex; align-items:center; justify-content:center; width:20px; height:20px; border-radius:999px; background:var(--accent-soft); color:#244fae; font-weight:700; font-size:.72rem; flex-shrink:0;}
  .install-result-grid{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px;}
  .install-result{background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:12px;}
  .install-result b{display:block; margin-bottom:4px;}
  .advanced-section{margin-top:4px; border-top:1px dashed var(--border); padding-top:14px;}
  .advanced-grid{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px;}
  .builder-actions{display:flex; gap:10px; flex-wrap:wrap; margin-top:12px;}
  .builder-preview{min-height:430px; max-height:70vh;}
  .builder-status{background:#fff7d6; border:1px solid #ead48b; color:#6f5208; border-radius:8px; padding:8px 10px; font-size:.84rem; margin-top:10px;}
  .empty{color:var(--muted); text-align:center; padding:36px 0;}
  footer{text-align:center; color:var(--muted); font-size:.75rem; padding:20px;}
  @media (max-width:760px){main,header{padding-left:14px; padding-right:14px;} .grid,.intro-grid,.workflow-guide,.state-summary,.form-grid,.capture-link,.home-kpis,.home-steps,.home-split,.role-grid,.daily-principles,.install-grid,.install-result-grid,.advanced-grid{grid-template-columns:1fr;} .capture-arrow{transform:rotate(90deg); justify-self:center;} .capture-status{justify-self:start;} .section-head,.daily-section-head{display:block;} }
</style>
</head>
<body>
<header><div class="head-inner"><h1>二刀流開發助手控制台 <span class="sub">Codex × Claude Code 開發系統</span></h1><div class="tabs"><button class="tab active" data-tab="guide">首頁 / 快速開始</button><button class="tab" data-tab="daily">日常提示詞</button><button class="tab" data-tab="customSkill">自製 Skill</button><button class="tab" data-tab="progress">開發進度</button><button class="tab" data-tab="control">二刀流中控</button><button class="tab" data-tab="prompts">提示詞庫</button><button class="tab" data-tab="skills">Skills</button><button class="tab" data-tab="capture">收錄新內容</button><button class="tab" data-tab="backup">換電腦／同步</button></div></div></header>
<main><div id="onlineBanner"></div><div id="launchTip"></div><div class="search"><span class="icon">搜</span><input id="searchBox" type="text" placeholder="搜尋 skill、提示詞、觸發句、角色、分工、導覽，例如：git、翻譯、審查、二刀流"></div><div id="pageIntro" class="page-intro"></div><div id="chips" class="chips"></div><div id="countLine" class="count"></div><div id="content"></div></main>
<footer>資料來源：data/skills.yaml + data/prompts.yaml + data/combos.yaml；修改後執行 python3 scripts/build.py 重建</footer>
<script>
const DATA = __DATA_JSON__;
const WORKFLOW_HTML = __WORKFLOW_HTML__;
const GUIDE_HTML = __GUIDE_HTML__;
// STATE_HTML / NEXT_HTML 為 {raw, html}：raw 餵 parseWorkflowState，html 顯示完整檔案視圖。命名沿用使用者指定。
const STATE_HTML = __STATE_HTML__;
const NEXT_HTML = __NEXT_HTML__;
const AGENTS_HTML = __AGENTS_HTML__;
const PRD_HTML = __PRD_HTML__;
const PROJECT_PATH = __PROJECT_PATH__;
const PROJECT_URL = __PROJECT_URL__;
let tab = "guide", cat = "全部", q = "", flowMode = "dualai", dailyMode = "全部", captureMode = "prompt", progressMode = "status", selectedProject = null, progressPickerMessage = "";
const FLOW_META = {
  dualai:{label:"二刀流協作",title:"二刀流工作流提示詞",lead:"適合重要系統修改：Codex 是主力工程師，負責規劃、分段實作、測試與修正；Claude Code（VS Code）是審查員，負責架構審查、風險檢查與複審。"},
  solo:{label:"單一 AI 使用",title:"單一 AI 使用提示詞",lead:"同事只有單一 AI 時，也能用這些提示詞讓 AI 先釐清、再分段執行、最後提醒是否需要審查。"},
  common:{label:"通用",title:"通用提示詞",lead:"日常可直接複製使用的提示詞，例如 Skill 安檢、交接、摘要與一般 AI 工作輔助。"}
};
const STAGE_META = {
  dualai:{entry:["入口","啟動或接續二刀流工作流"],"1":["第 1 階段：Codex","規劃、拆任務、建立狀態檔"],"2":["第 2 階段：Codex","分段實作、build、驗證"],"3":["第 3 階段：Claude Code（VS Code）","審查 diff、架構與風險"],"4":["第 4 階段：Codex","逐條修正、重新驗證"],"5":["第 5 階段：Claude Code（VS Code）","複審並確認可收尾"],handoff:["轉交","把目前狀態交給下一方"],status:["狀態檔","讀寫 DUAL-AI-STATE.md"],"context-compact":["上下文壓縮","壓縮後輸出可接續摘要"],archive:["存檔收尾","第 5 階段通過後驗證、更新狀態檔與交還 push 決定權"]},
  solo:{entry:["入口","只用一個 AI 時先用這張說明工作方式"],"1":["第 1 步","釐清任務與目標"],"2":["第 2 步","提出方案、先不修改"],"3":["第 3 步","分段執行並自我檢查"],"4":["第 4 步","收尾、整理驗證與 commit 建議"]}
};
const FLOW_ORDER = {dualai:["entry","1","2","3","4","5","handoff","status","context-compact","archive"],solo:["entry","1","2","3","4"]};
const DAILY_PROMPT_SECTIONS = [
  {title:"開發系統",hint:"寫程式、修 bug、讀專案時先用這區。",cards:[
    {title:"雙 AI 討論新專案方向",when:"只有一個模糊想法，想先聊成可規劃的新專案或新系統時。",prompt:`我有一個新專案或新系統想法，請先陪我討論與規劃，不要直接寫程式、不要直接改檔案。

初步想法：
【在這裡貼上你的想法，可以很模糊】

請採用「雙 AI 角色討論」方式協助我：
1. Codex 角色：主力工程師，負責把想法拆成系統、功能、資料、流程與可執行任務。
2. Claude Code（VS Code）角色：審查員／挑戰者，負責追問需求盲點、技術風險、邊界情況、成本與維護問題。
3. 使用者角色：最終決策者，你要用簡單問題引導我做選擇，不要一次問太多。

互動流程：
1. 先用 5 句話重述你理解的想法。
2. 分別用 Codex 視角與 Claude Code 視角，各提出最重要的觀察。
3. 先問我最多 5 個關鍵問題，問題要好回答，必要時提供選項。
4. 根據我的回答，整理出：目標使用者、核心痛點、第一版功能、暫時不做的事、風險。
5. 最後產出一份新手看得懂的專案規劃草案。
6. 如果適合進入二刀流開發，最後再給我兩段可複製提示詞：
   - 給 Codex 的「建立 AGENTS.md / PRD.md 並規劃第一版」提示詞。
   - 給 Claude Code（VS Code）的「審查專案規劃」提示詞。

限制：
- 不要假裝已經知道我的需求；不清楚就問。
- 不要一開始就建檔或寫程式。
- 不要把第一版做太大，請優先找最小可行版本。
- 如果我只有一個 AI，也請你先在同一個回答中模擬 Codex 與 Claude Code 兩種視角。`},
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
    {title:"幫我把想法整理成圖片提示詞",when:"你只有模糊想法，想先變成可拿去生圖的 prompt。",prompt:`請幫我把下面的想法整理成高品質圖片生成提示詞。

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
  {title:"生成影片提示詞",hint:"要做短影音、展示影片或腳本分鏡時，先把鏡頭、節奏、旁白與畫面限制講清楚。",cards:[
    {title:"幫我把想法整理成影片生成提示詞",when:"想用 AI 生成影片，但還不知道怎麼描述鏡頭與畫面。",prompt:`請幫我把下面的想法整理成高品質影片生成提示詞。

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
  backup:{title:"換電腦／同步",lead:"這頁是新手安裝、下載備份包、換電腦同步與建立自己版本的入口。線上 demo 不能直接操作你的電腦；請依你的系統複製指令後，到 PowerShell 或 Terminal 執行。",purpose:"把二刀流控制台與整理好的 skills 安裝到 Codex / Claude Code 可讀的位置，或下載備份包留存。",first:"先選 Windows 或 macOS 安裝指令；按下複製後，照卡片上的 3 個小步驟貼到終端機執行。",when:"第一次安裝、換電腦、重裝工具、下載備份包，或想把自己客製化版本同步到其他機器時。"},
  skills:{title:"Skills",lead:"查看每個 skill 的用途、風險與觸發句，直接複製給 AI 使用。",purpose:"快速判斷要叫哪個 AI skill。",first:"搜尋關鍵字，再複製觸發句。",when:"不確定某個任務該用哪個 skill 時。"},
  prompts:{title:"提示詞庫",lead:"常用提示詞集中管理，適合你直接複製給 Codex 或 Claude Code（VS Code）。",purpose:"快速啟動工作流程。",first:"先選二刀流、單一 AI 或通用分類，再複製。",when:"要交辦任務、請 AI 審查、整理交接或產出文件時。"},
  capture:{title:"收錄新內容",lead:"看到好用提示詞或 skill 時，先填表產生交辦提示詞與 YAML 片段，再交給 Codex 寫入、重建、驗證與 commit。",purpose:"安全收錄新內容，不需要你手寫 YAML。",first:"先選提示詞或 Skill；新手請複製「給 Codex 的完整交辦提示詞」。",when:"看到新 skill、實用提示詞，或想把工作流模板收入控制台時。"},
  control:{title:"二刀流中控",lead:"v1 是靜態教學頁，不讀取 DUAL-AI-STATE.md；按鈕只會跳到提示詞庫並複製對應提示詞。",purpose:"讓每個階段知道要找誰、做什麼、複製哪張提示詞。",first:"先看目前要進哪一階段，再按卡片按鈕複製對應提示詞。",when:"要從規劃、實作、審查、修正、複審到存檔收尾一路接續時。"},
  progress:{title:"開發進度",lead:"這頁把目前專案做到哪裡、下一步要做什麼一次整理出來。",purpose:"不用翻文件也能快速知道現在進度、是否有卡點，以及下一步該做什麼。",first:"先看目前階段與下一步；如果有未解決問題，先處理警示區。",when:"接續開發、換 AI 接手、或想確認這個專案現在是不是可以往下一步走時。"},
  daily:{title:"日常提示詞",lead:"不知道怎麼開口時，先從這裡複製。這頁把開發、查資料、整理資料、整理電腦檔案、生成圖片與生成影片整理成新手可直接使用的提示詞。",purpose:"把日常最常用的 AI 交辦方式整理成安全、直接可複製的新手版。",first:"先選你現在想做什麼，再複製對應卡片。整理電腦檔案時，只先規劃，不直接動檔。",when:"開發系統、找資料比對、整理文字資料、分類電腦檔案、產生圖片 prompt 或產生影片 prompt 時。"},
  customSkill:{title:"自製 Skill",lead:"用選單自動組出「個人化專屬 skill」提示詞。使用者先選職業、用途、AI 風格、安裝目標，再複製整段給 Codex。",purpose:"把你的工作痛點、陪練方式與封裝安裝流程，變成可重複使用的專屬 AI 工作 skill。",first:"進頁面後會跳出選單；先選好欄位，再按「更新提示詞」或直接複製。",when:"想讓 AI 先理解你的職務與業務，再替你做挑刺陪練，最後封裝成可安裝 skill 時。"},
  guide:{title:"首頁 / 快速開始",lead:"這裡先用最簡單的方式說明這套輔助系統在做什麼、怎麼分工、第一步該按哪裡。",purpose:"讓新手一進來就知道 Codex 做什麼、Claude Code 做什麼，以及怎麼開始。",first:"先看下方 3 步驟；如果你正在接續專案，直接去「開發進度」。",when:"第一次打開控制台，或想快速教同事這套系統怎麼用時。"}
};
const riskCls = {"低":"low","中":"mid","高":"high"};
const esc = s => (s ?? "").toString().replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
function copyText(text, btn){const original=btn.dataset.copyLabel||btn.textContent;btn.dataset.copyLabel=original;const done=()=>{btn.textContent="已複製";btn.classList.add("done");setTimeout(()=>{btn.textContent=original;btn.classList.remove("done");},1400)};if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done).catch(fallback)}else fallback();function fallback(){const ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);ta.select();document.execCommand("copy");document.body.removeChild(ta);done()}}
document.addEventListener("click",e=>{const b=e.target.closest("[data-copy]");if(b)copyText(decodeURIComponent(b.dataset.copy),b)});
function match(obj,fields){if(!q)return true;const hay=fields.map(f=>Array.isArray(obj[f])?obj[f].join(" "):(obj[f]||"")).join(" ").toLowerCase();return hay.includes(q.toLowerCase())}
function cats(){if(tab==="skills")return["全部",...new Set(DATA.skills.map(s=>s.category))];if(tab==="prompts")return["全部",...new Set(DATA.prompts.filter(p=>(p.flow||"common")===flowMode).map(p=>p.category).filter(Boolean))];return[]}
function renderLaunchTip(){const tip=document.getElementById("launchTip");if(!tip)return;const isFile=location.protocol==="file:";if(!isFile){tip.innerHTML="";return}tip.innerHTML=`<div class="launch-tip"><b>目前是直接用書籤／檔案打開控制台</b><div class="summary">這種開法只會打開 <code>index.html</code>，不會先執行「更新並開啟控制台.command」或 <code>python3 scripts/build.py</code>。如果你希望每次都先更新再開頁面，請改用桌面的 <code>二刀流開發助手控制台.command</code>，或在這個專案資料夾裡雙擊 <code>更新並開啟控制台.command</code>。</div></div>`}
function renderOnlineBanner(){const el=document.getElementById("onlineBanner");if(!el)return;const isOnline=/\.github\.io$/i.test(location.hostname);if(!isOnline){el.innerHTML="";return}el.innerHTML=`<div class="online-banner"><div class="grow"><b>這是線上試用版（demo）</b><div class="summary">頁面內顯示的開發進度、AGENTS、PRD 是這套控制台自己的範例；要查自己專案請按「開發進度」→ 選資料夾。日常提示詞 / Skills / 提示詞庫可以直接用。</div><div class="summary" style="margin-top:6px">想在自己電腦用，請按右邊「下載安裝」看一行指令；或到 <a href="https://github.com/kagenhsu/codex-claude-skills-backup" target="_blank" rel="noopener">GitHub repo</a> 看原始碼。</div></div><button type="button" data-tab-jump="backup">下載安裝</button></div>`;el.querySelector("[data-tab-jump]")?.addEventListener("click",()=>setTab("backup"))}
function renderIntro(){const info=PAGE_INTROS[tab];document.getElementById("pageIntro").innerHTML=`<h2>${esc(info.title)}</h2><div class="lead">${esc(info.lead)}</div><div class="intro-grid"><div class="intro-item"><div class="intro-label">用途</div><div class="intro-text">${esc(info.purpose)}</div></div><div class="intro-item"><div class="intro-label">先做</div><div class="intro-text">${esc(info.first)}</div></div><div class="intro-item"><div class="intro-label">適合情境</div><div class="intro-text">${esc(info.when)}</div></div></div>`}
function homePrompt(title,fallback){return DATA.prompts.find(p=>p.title===title)?.prompt||fallback}
function homeHtml(){const rolePrompt=homePrompt("二刀流分工細節說明","請用小白能懂的方式，說明 Codex 和 Claude Code（VS Code）的分工細節。");const codexPrompt=homePrompt("① 第一階段：Codex 規劃","請先讀取專案結構與相關文件，不要直接修改。先提出方案，再等我確認。");const reviewPrompt=homePrompt("③ 第三階段：Claude Code（VS Code）審查","請審查這次改動、diff 與驗證結果，列出 P0/P1/P2 風險。");const soloPrompt=homePrompt("單一 AI 也能用控制台","我現在只使用一個 AI，但想用這套二刀流開發助手控制台輔助工作。請先幫我釐清任務目標，提出方案，再分段執行。");return`<div class="wide-sop"><div class="home-hero"><h2>這是一套讓 Codex 和 Claude Code 分工合作的開發輔助系統</h2><p>簡單說：Codex 負責規劃、實作、修正；Claude Code（VS Code）負責審查與複審。你不用記全部流程，只要知道現在是新專案、接續專案，還是要找提示詞即可。</p><div class="home-actions"><button class="copy-btn" type="button" data-home-tab="daily">我要日常提示詞</button><button class="copy-btn" type="button" data-home-tab="progress">我正在接續專案</button><button class="copy-btn" type="button" data-home-tab="prompts">我要複製提示詞</button><button class="copy-btn" type="button" data-home-tab="skills">我要找 Skill</button></div><div class="home-kpis"><div class="home-kpi"><b>先看哪裡</b><div class="summary">有現成專案就先開「開發進度」，只是日常交辦就開「日常提示詞」。</div></div><div class="home-kpi"><b>核心分工</b><div class="summary">Codex 做事，Claude Code 抓問題，你做最後決定。</div></div><div class="home-kpi"><b>新手原則</b><div class="summary">先照流程走，不用一開始就理解全部頁籤。</div></div></div></div><div class="home-steps"><div class="home-step"><span class="num">1</span><h3>先確認你是哪一種情況</h3><div class="summary">日常交辦：先去日常提示詞。新專案：先去提示詞庫找 AGENTS / PRD。舊專案：先去開發進度選資料夾。只想找工具：直接去 Skills。</div></div><div class="home-step"><span class="num">2</span><h3>照二刀流分工做</h3><div class="summary">Codex 先規劃與實作，Claude Code 再審查。不要兩邊同時亂改，這樣最穩。</div></div><div class="home-step"><span class="num">3</span><h3>每一棒都留交接檔</h3><div class="summary">這套系統主要靠 <code>DUAL-AI-STATE.md</code>、<code>NEXT-AI-TASK.md</code>、<code>AGENTS.md</code>、<code>PRD.md</code> 接續，不要只靠聊天記憶。</div></div></div><div class="home-split"><div class="home-panel"><h3>二刀流最簡單分工</h3><div class="role-grid"><div class="role-card"><h4>Codex</h4><div class="summary">主力工程師。適合規劃、拆任務、分段實作、跑測試、修正問題。</div></div><div class="role-card"><h4>Claude Code（VS Code）</h4><div class="summary">審查員。適合看 diff、抓風險、提 P0/P1/P2、做複審。</div></div><div class="role-card"><h4>你</h4><div class="summary">最後決策者。看結論、決定要不要繼續、要不要 commit / push。</div></div><div class="role-card"><h4>單一 AI 也能用</h4><div class="summary">如果手邊只有一個 AI，就改走提示詞庫裡的「單一 AI 使用」流程。</div></div></div><div class="home-copy-hint">第一次使用請先按「新手先按：複製分工細節說明」，貼給 AI 了解兩邊怎麼配合。</div><div class="home-panel-actions"><button class="copy-btn primary-copy" data-copy="${encodeURIComponent(rolePrompt)}">新手先按：複製分工細節說明</button><button class="copy-btn" data-copy="${encodeURIComponent(codexPrompt)}">複製 Codex 開工提示詞</button><button class="copy-btn" data-copy="${encodeURIComponent(reviewPrompt)}">複製 Claude 審查提示詞</button><button class="copy-btn" data-copy="${encodeURIComponent(soloPrompt)}">複製單一 AI 提示詞</button></div></div><div class="home-panel"><h3>最常用的三個入口</h3><div class="mini-list"><div class="mini-item"><b>日常提示詞</b><div class="summary">不知道怎麼開口時用。開發、查資料、整理文字、整理電腦檔案都有新手版提示詞。</div></div><div class="mini-item"><b>開發進度</b><div class="summary">接續現有專案時用。選資料夾後看目前階段、下一步、缺哪些檔案。</div></div><div class="mini-item"><b>提示詞庫</b><div class="summary">不知道怎麼開工時用。裡面有新專案啟動、審查、交接、收尾提示詞。</div></div><div class="mini-item"><b>二刀流中控</b><div class="summary">已經知道自己在第幾階段時用。直接跳到對應提示詞。</div></div></div></div></div><div class="home-panel" style="margin-top:14px"><h3>二刀流完整流程</h3><div class="summary">第 1 階段 Codex 規劃 → 第 2 階段 Codex 實作 → 第 3 階段 Claude Code 審查 → 第 4 階段 Codex 修正 → 第 5 階段 Claude Code 複審 → Codex 存檔收尾。</div><div class="summary" style="margin-top:8px">如果你已經知道自己在哪一階段，直接去「二刀流中控」會比讀長篇說明更快。</div></div></div>`}
function bindHome(){const actions=document.querySelector(".home-actions");if(actions&&!actions.querySelector('[data-home-tab="customSkill"]'))actions.querySelector('[data-home-tab="daily"]')?.insertAdjacentHTML("afterend",'<button class="copy-btn" type="button" data-home-tab="customSkill">我要自製 Skill</button>');const steps=document.querySelector(".home-steps");if(steps&&!document.querySelector(".skill-explain-panel"))steps.insertAdjacentHTML("afterend",`<div class="home-panel skill-explain-panel" style="margin-bottom:16px"><h3>新手先懂：Skill 是什麼？</h3><div class="workflow-guide"><div class="guide-item"><div class="guide-label">一句話</div><div class="guide-text">Skill 就像寫給 AI 的「專用工作說明書」。遇到特定任務時，AI 會照這份說明書做事。</div></div><div class="guide-item"><div class="guide-label">它解決什麼</div><div class="guide-text">不用每次重新交代規則。例如翻譯、查錯、審查、整理文件，都可以先做成固定流程。</div></div><div class="guide-item"><div class="guide-label">自製 Skill</div><div class="guide-text">就是把你的職務、痛點、語氣、禁忌和工作流程，封裝成你的個人 AI 工作模式。</div></div></div><div class="summary" style="margin-top:10px">簡單比喻：普通提示詞是「這次請你怎麼做」；Skill 是「以後遇到這類事情，都照這套方法做」。</div></div>`);document.querySelectorAll("[data-home-tab]").forEach(btn=>btn.onclick=()=>setTab(btn.dataset.homeTab))}
function dailyPromptCard(card){return`<div class="daily-card"><h4>${esc(card.title)}</h4><div class="usage">${esc(card.when)}</div><pre class="prompt-body">${esc(card.prompt)}</pre><button class="copy-btn" data-copy="${encodeURIComponent(card.prompt)}">複製這段提示詞</button></div>`}
function dailyModeButtons(){const modes=["全部",...DAILY_PROMPT_SECTIONS.map(section=>section.title)];return`<div class="flow-switch">${modes.map(mode=>`<button class="flow-btn ${dailyMode===mode?"active":""}" onclick="dailyMode='${esc(mode)}';render()">${esc(mode)}</button>`).join("")}</div>`}
function dailyHtml(){const sections=DAILY_PROMPT_SECTIONS.filter(section=>dailyMode==="全部"||section.title===dailyMode);return`<div class="wide-sop"><div class="daily-hero"><h2>日常工作不知道怎麼問，就先從這裡複製</h2><p>這頁是新手版提示詞，不用先懂二刀流或專案文件。你只要選「現在想做什麼」，複製卡片給 Codex 或 Claude Code，就能開始請 AI 幫忙。</p><div class="daily-principles"><div class="daily-principle"><b>先講目的</b><div class="summary">告訴 AI 你想完成什麼，不只是丟一堆資料。</div></div><div class="daily-principle"><b>先看再做</b><div class="summary">要求 AI 先分析、先規劃，確認後再修改。</div></div><div class="daily-principle"><b>重要檔案先保護</b><div class="summary">涉及電腦檔案時，先備份、先列計畫，不直接動檔。</div></div></div></div>${dailyModeButtons()}${sections.map(section=>`<section class="daily-section"><div class="daily-section-head"><div><h3>${esc(section.title)}</h3><div class="summary">${esc(section.hint)}</div></div>${section.safety?`<div class="daily-safety">${esc(section.safety)}</div>`:""}</div><div class="daily-grid">${section.cards.map(dailyPromptCard).join("")}</div></section>`).join("")}</div>`}
function bindDaily(){document.querySelectorAll("[data-daily-mode]").forEach(btn=>btn.onclick=()=>{dailyMode=btn.dataset.dailyMode;render()})}
function skillCard(s){const triggers=(s.triggers||[]).map(t=>`<div class="trigger"><code>${esc(t)}</code><button class="copy-btn" data-copy="${encodeURIComponent(t)}">複製</button></div>`).join("");return`<div class="card"><h3>${esc(s.name)} <span class="badge ${riskCls[s.risk]||"low"}">${esc(s.risk)}風險</span> <span class="cat-tag">${esc(s.category)}</span></h3><div class="summary">${esc(s.summary)}</div>${s.notes?`<div class="notes">${esc(s.notes)}</div>`:""}${triggers}</div>`}
function stageLabel(p){if(!p.flow||!p.stage)return"通用";const meta=STAGE_META[p.flow]?.[p.stage];return meta?meta[0]:p.stage}
function promptKey(p){return `${p.flow||"common"}::${p.stage||""}::${p.title}`}
function promptCard(p){return`<div class="card" data-prompt-key="${esc(promptKey(p))}"><h3>${esc(p.title)} <span class="stage-tag">${esc(stageLabel(p))}</span> <span class="cat-tag">${esc(p.category)}</span></h3><div class="usage">${esc(p.usage)}</div><pre class="prompt-body">${esc(p.prompt)}</pre><button class="copy-btn" data-copy="${encodeURIComponent(p.prompt)}">複製</button></div>`}
function comboPrompt(combo){const lines=[`以下是「${combo.title}」。`,combo.usage||"", ""];const missing=[];(combo.steps||[]).forEach((step,idx)=>{const prompt=DATA.prompts.find(p=>p.title===step.prompt_title);if(!prompt){missing.push(step.prompt_title);return}if(step.custom_intro)lines.push(step.custom_intro,"");lines.push(`--- Prompt ${idx+1}：${prompt.title} ---`,prompt.prompt,"")});if(missing.length)lines.unshift(`提醒：找不到以下提示詞，已略過：${missing.join("、")}`,"");return lines.join("\n").trim()}
function comboCard(combo){const missing=(combo.steps||[]).filter(step=>!DATA.prompts.some(p=>p.title===step.prompt_title)).map(step=>step.prompt_title);const steps=(combo.steps||[]).map(step=>`<li>${esc(step.prompt_title)}</li>`).join("");const text=comboPrompt(combo);return`<div class="combo-card"><h3>${esc(combo.title)} <span class="cat-tag">${esc(combo.category||"組合包")}</span></h3><div class="usage">${esc(combo.usage||"")}</div>${missing.length?`<div class="warning">缺少提示詞：${esc(missing.join("、"))}</div>`:""}<ol class="combo-steps">${steps}</ol><button class="copy-btn" data-copy="${encodeURIComponent(text)}">複製整包（${(combo.steps||[]).length} 張）</button></div>`}
function combosHtml(){const combos=DATA.combos||[];if(!combos.length)return"";return`<section class="flow-section"><div class="section-head"><h2>常用組合包</h2><span class="hint">一鍵複製常用流程</span></div><div class="combo-grid">${combos.map(comboCard).join("")}</div></section>`}
function workflowGuide(){if(flowMode==="dualai")return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">Codex</div><div class="guide-text">主力工程師：規劃、分段實作、測試、修正。</div></div><div class="guide-item"><div class="guide-label">Claude Code（VS Code）</div><div class="guide-text">審查員：看 diff、抓風險、提出 P0/P1/P2 問題。</div></div></div>`;if(flowMode==="solo")return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">先規劃</div><div class="guide-text">讓單一 AI 先讀文件並列出做法。</div></div><div class="guide-item"><div class="guide-label">再實作</div><div class="guide-text">只做最小必要修改，避免一次改太大。</div></div><div class="guide-item"><div class="guide-label">要自檢</div><div class="guide-text">請 AI 用審查角度檢查結果。</div></div></div>`;return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">專案啟動</div><div class="guide-text">AGENTS、PRD、交接摘要與規劃模板。</div></div><div class="guide-item"><div class="guide-label">工程常用</div><div class="guide-text">Git、API、部署與資料庫模板。</div></div><div class="guide-item"><div class="guide-label">Skill 管理</div><div class="guide-text">新增 skill、資安檢查與提示詞收錄。</div></div></div>`}
function flowButtons(){return`<div class="flow-switch">${Object.entries(FLOW_META).map(([key,m])=>`<button class="flow-btn ${flowMode===key?"active":""}" data-flow="${key}">${m.label}</button>`).join("")}</div>`}
function renderPromptFlow(){const meta=FLOW_META[flowMode];const visible=DATA.prompts.filter(p=>(p.flow||"common")===flowMode&&(cat==="全部"||p.category===cat)&&match(p,["title","usage","category","prompt","flow","stage"]));let html=`<div class="page-intro"><h2>${esc(meta.title)}</h2><div class="lead">${esc(meta.lead)}</div>${workflowGuide()}</div>${flowButtons()}`;if(cat==="全部"&&!q)html+=combosHtml();if(flowMode==="common"){const groups=[...new Set(visible.map(p=>p.category))];html+=groups.map(group=>{const items=visible.filter(p=>p.category===group);return`<section class="flow-section"><div class="section-head"><h2>${esc(group)}</h2><span class="hint">${items.length} 則</span></div><div class="grid">${items.map(promptCard).join("")}</div></section>`}).join("")}else{html+=FLOW_ORDER[flowMode].map(stage=>{const items=visible.filter(p=>String(p.stage||"")===stage);if(!items.length)return"";const[label,hint]=STAGE_META[flowMode][stage]||[stage,""];return`<section class="flow-section" data-stage="${esc(stage)}"><div class="section-head"><h2>${esc(label)}</h2><span class="hint">${esc(hint)}，${items.length} 則</span></div><div class="grid">${items.map(promptCard).join("")}</div></section>`}).join("")}return html||`<div class="empty">找不到符合條件的提示詞。</div>`}
function cmdRow(label,cmd){return`<div class="trigger"><div style="flex:1"><div class="usage">${esc(label)}</div><code>${esc(cmd)}</code></div><button class="copy-btn" data-copy="${encodeURIComponent(cmd)}">複製指令</button></div>`}
function installSteps(system){return`<div class="install-steps"><div class="install-step"><span>1</span><div>打開 ${esc(system)}</div></div><div class="install-step"><span>2</span><div>貼上剛剛複製的指令</div></div><div class="install-step"><span>3</span><div>按 Enter，等待安裝完成</div></div></div>`}
function backupHtml(){const winCmd=`powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.ps1 | iex"`;const macCmd="curl -fsSL https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.sh | bash";const restoreCmd="./restore-skills.sh";const backupUrl="https://github.com/kagenhsu/codex-claude-skills-backup/raw/main/codex-skills-backup.tar.gz";return`<div class="sop wide-sop"><div class="card install-hero"><h2>把二刀流控制台裝到自己的電腦</h2><div class="summary">線上 demo 可以先試用提示詞與介面；如果你想在自己的電腦使用 skills、本機控制台和桌面捷徑，請選下面的 Windows 或 macOS 安裝指令。</div><div class="privacy-note">這個網頁不會讀取你的電腦資料，也不會送任何東西到伺服器；所有按鈕都只是把指令複製到剪貼簿，或開啟下載連結。</div></div><div class="install-grid"><div class="install-card featured"><h3>Windows 安裝指令</h3><div class="install-subtitle">複製後貼到 PowerShell 執行</div><button class="copy-btn" data-copy="${encodeURIComponent(winCmd)}">複製指令</button>${installSteps("PowerShell")}<pre class="prompt-body">${esc(winCmd)}</pre></div><div class="install-card featured"><h3>macOS 安裝指令</h3><div class="install-subtitle">複製後貼到 Terminal 執行</div><button class="copy-btn" data-copy="${encodeURIComponent(macCmd)}">複製指令</button>${installSteps("Terminal")}<pre class="prompt-body">${esc(macCmd)}</pre></div><div class="install-card"><h3>下載 skills 備份包</h3><div class="install-subtitle">適用情境：網路慢、想先看備份包內容，或公司網路擋 raw.githubusercontent.com。</div><a class="copy-btn" href="${backupUrl}" target="_blank" rel="noopener">下載備份包</a><div class="summary">下載的是 <code>codex-skills-backup.tar.gz</code>，裡面是整理好的 skills，不會自動安裝。</div></div></div><div class="card"><h2>安裝完成後，你會得到什麼？</h2><div class="install-result-grid"><div class="install-result"><b>skills 放到正確位置</b><div class="summary">安裝腳本會把 skills 放到 Codex / Claude Code 讀得到的位置。</div></div><div class="install-result"><b>桌面控制台入口</b><div class="summary">桌面會出現「二刀流開發助手控制台」捷徑或 <code>.command</code>。</div></div><div class="install-result"><b>本機可用工作台</b><div class="summary">之後可用本機控制台複製提示詞、看 skills、跑二刀流流程。</div></div></div></div><div class="card"><h2>注意事項</h2><ul><li>線上 demo 不能直接替你備份本機檔案，也不能自動讀取你的 skills。</li><li>安裝前想先看完整說明，可以回 GitHub repo 的 README。</li><li>macOS 第一次雙擊桌面 <code>.command</code> 若出現「無法識別開發者」，請在 Finder 對檔案按右鍵選「打開」。</li><li>如果安裝失敗或看不懂錯誤訊息，可以到 GitHub Issues 留言。</li></ul></div><div class="advanced-section"><div class="section-head"><h2>進階區：不是新手第一步該按</h2><span class="hint">已下載整包 repo 或已客製化的人再看</span></div><div class="advanced-grid"><div class="card"><h2>給已下載整個 repo 的人</h2><div class="summary">如果你已經把整個專案下載到電腦，macOS 換機或重裝時可以在專案資料夾執行：</div>${cmdRow("macOS 離線還原 skills",restoreCmd)}</div><div class="card"><h2>已安裝後，想擁有自己的版本？</h2><div class="summary">如果你已經改過 <code>data/prompts.yaml</code>、<code>data/skills.yaml</code>，想跨機器同步或團隊共用，可以把整個資料夾 push 到你自己的 GitHub。</div><ol><li>在 GitHub 開一個空 repo，例如 <code>my-codex-console</code>。</li><li>在這個資料夾跑：</li></ol>${cmdRow("加入自己的遠端，不要覆蓋 origin","git remote add mine <你的 repo 網址>")} ${cmdRow("推到自己的 repo","git push -u mine main")}<ol start="3"><li>之後換機器時：</li></ol>${cmdRow("從自己的 repo 取回","git clone <你的 repo 網址>")} ${cmdRow("重新產生控制台","python3 scripts/build.py")}<div class="warning">重要：請用 <code>git remote add mine</code>，不要用 <code>git remote set-url origin</code>。後者會把作者原 repo 的來源改掉，之後想更新會比較容易迷路。</div></div></div></div></div>`}
function wideHtml(html){return html.replace('<div class="sop">','<div class="sop wide-sop">')}
const CONTROL_STAGES=[
  {stage:"1",role:"Codex",purpose:"規劃與拆任務",plain:"先把需求變成可做的清單，避免一開始就亂改檔。"},
  {stage:"2",role:"Codex",purpose:"分段實作與驗證",plain:"一段一段做，每段 build、檢查、commit。"},
  {stage:"3",role:"Claude Code（VS Code）",purpose:"審查 diff 與風險",plain:"請另一個 AI 用審查員角度抓 P0/P1/P2 問題。"},
  {stage:"4",role:"Codex",purpose:"逐條修正審查意見",plain:"把審查意見搬回 Codex，逐條處理並重新驗證。"},
  {stage:"5",role:"Claude Code（VS Code）",purpose:"複審與通過確認",plain:"修完後再請審查員確認沒有殘留問題。"},
  {stage:"archive",role:"Codex",purpose:"存檔收尾",plain:"複審通過後做最後驗證、更新狀態檔、commit，push 決定權交回使用者。",query:"存檔收尾",fallback:"請依 dual-ai-workflow 第 5 階段通過後的收尾流程，重新驗證、更新 DUAL-AI-STATE.md、建立本地 commit，並把是否 push origin/main 的決定權交回使用者。"}
];
function controlPromptInfo(item){let found=null;if(item.stage==="archive")found=DATA.prompts.find(p=>(p.flow||"common")==="dualai"&&(String(p.stage||"")==="archive"||p.title.includes("存檔收尾")));else found=DATA.prompts.find(p=>(p.flow||"common")==="dualai"&&String(p.stage||"")===item.stage);return{prompt:found?found.prompt:item.fallback,targetStage:found?String(found.stage||item.stage):item.stage,targetPrompt:found?promptKey(found):"",found:!!found}}
function stateDraft(){return localStorage.getItem("workflow-state-draft")||""}
// 必須與 DUAL-AI-STATE.md section 名稱保持同步
const STATE_SECTIONS=["任務名稱","目前階段","已完成事項","下一步","未解決問題","最後更新時間"];
const STATE_SECTION_PATTERN=STATE_SECTIONS.map(item=>item.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")).join("|");
function sectionAfter(text,label){if(!STATE_SECTIONS.includes(label))return"";const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");const match=text.match(new RegExp(`(?:^|\\n)${escaped}：?\\s*([\\s\\S]*?)(?=\\n(?:${STATE_SECTION_PATTERN})：?|$)`));return match?match[1].trim():""}
function parseStageNumber(value){const map={一:"1",二:"2",三:"3",四:"4",五:"5"};return map[value]||value||""}
function parseWorkflowState(text){if(!text.trim())return{ok:false,message:"無法解析，請確認貼上的是 DUAL-AI-STATE.md 全文。"};const current=(text.match(/目前階段：?\s*(.*)/)||[])[1]?.trim()||"";const next=sectionAfter(text,"下一步");const unresolved=sectionAfter(text,"未解決問題");const updated=(text.match(/最後更新時間：?\s*(.*)/)||[])[1]?.trim()||"";const done=sectionAfter(text,"已完成事項").split(/\n/).map(s=>s.trim()).filter(Boolean).slice(-3).join("\n");const stageMatch=current.match(/第\s*([1-5一二三四五])\s*階段/);const stage=current.includes("已完成")?"5":parseStageNumber(stageMatch?stageMatch[1]:"");const ok=!!(current||next||unresolved||updated||done);return{ok,current:current||"尚未判斷",done:done||"尚未解析",next:next||"尚未解析",unresolved:unresolved||"無",updated:updated||"尚未解析",stage,message:ok?"":"無法解析，請確認貼上的是 DUAL-AI-STATE.md 全文。"}}
function stateSummaryHtml(parsed){return parsed.ok?`<div class="state-summary"><div class="state-item"><div class="state-label">目前階段</div><div class="state-value">${esc(parsed.current)}</div></div><div class="state-item"><div class="state-label">最後更新時間</div><div class="state-value">${esc(parsed.updated)}</div></div><div class="state-item full"><div class="state-label">上一步做了什麼</div><div class="state-value">${esc(parsed.done)}</div></div><div class="state-item full"><div class="state-label">下一步</div><div class="state-value">${esc(parsed.next)}</div></div><div class="state-item full"><div class="state-label">未解決問題</div><div class="state-value">${esc(parsed.unresolved)}</div></div></div>`:`<div class="warning">${esc(parsed.message)}</div>`}
function mdSection(text,label){const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");const match=text.match(new RegExp(`(?:^|\\n)## ${escaped}\\s*\\n([\\s\\S]*?)(?=\\n## |$)`));return match?match[1].trim():"尚未設定。"}
function simpleMarkdownHtml(raw,fallbackTitle){if(!raw.trim())return`<div class="sop"><div class="card"><h2>${esc(fallbackTitle)}</h2><div class="summary">尚未設定。</div></div></div>`;return`<pre class="prompt-body">${esc(raw)}</pre>`}
function progressSource(){return selectedProject||{name:"目前控制台資料夾",path:PROJECT_PATH,state:STATE_HTML,next:NEXT_HTML,agents:AGENTS_HTML,prd:PRD_HTML,projectType:"console"}}
function progressMissingFiles(src){return [["DUAL-AI-STATE.md",src.state.raw],["NEXT-AI-TASK.md",src.next.raw],["AGENTS.md",src.agents.raw],["PRD.md",src.prd.raw]].filter(([,raw])=>!raw.trim()).map(([name])=>name)}
function progressSetupPrompt(src,missing){return`請幫我檢查這個專案資料夾，並補齊開發進度控制台需要的 markdown 檔案。\n\n專案資料夾：${src.path||src.name}\n缺少檔案：${missing.join("、")}\n\n請建立或補齊：\n- DUAL-AI-STATE.md：記錄任務名稱、目前階段、已完成事項、下一步、未解決問題、最後更新時間。\n- NEXT-AI-TASK.md：記錄上一棒 AI、下一棒 AI、交棒目的、必讀檔案、已完成、下一棒要做、驗證要求。\n- AGENTS.md：記錄專案名稱、專案簡介、開發協作規範與檔案結構。\n- PRD.md：記錄專案背景、目標、痛點、功能清單、不做的事與驗收標準。\n\n請先讀現有檔案與 git 狀態，再用繁體中文補檔；不要刪除既有內容。`}
function progressFileCheckHtml(src){const missing=progressMissingFiles(src);if(!missing.length)return`<div class="card"><h2>必備檔案檢查</h2><div class="summary">✅ 已找到 DUAL-AI-STATE.md、NEXT-AI-TASK.md、AGENTS.md、PRD.md，下方資料卡可以正常顯示。</div></div>`;const prompt=progressSetupPrompt(src,missing);return`<div class="warning"><div><b>缺少必要 .md 檔案：</b>${esc(missing.join("、"))}</div><div class="summary" style="margin-top:6px">這個專案可能是新專案，或還沒建立交接文件。請先把下方提示詞交給 AI 補齊檔案，補完後重新選擇資料夾。</div><button class="copy-btn" style="margin-top:8px" data-copy="${encodeURIComponent(prompt)}">複製給 AI 補檔提示詞</button></div>`}
function progressPickerHtml(src){const helper=progressPickerMessage?`<div class="summary" style="margin-top:8px;color:var(--amber)">${esc(progressPickerMessage)}</div>`:`<div class="summary" style="margin-top:8px">如果按了「選擇專案資料夾」沒有跳出視窗，通常是瀏覽器不支援資料夾選取；這時會自動改走備援方式，或在這裡顯示原因。</div>`;return`<div class="warning"><div>請選擇要查看的專案資料夾；系統會自動檢查 DUAL-AI-STATE.md / NEXT-AI-TASK.md / AGENTS.md / PRD.md 是否存在。</div><div class="trigger" style="margin-top:8px"><code>${esc(src.path||src.name)}</code><button class="copy-btn" type="button" data-progress-pick>選擇專案資料夾</button><button class="copy-btn" type="button" data-copy="${encodeURIComponent(src.path||src.name)}">複製目前名稱</button><input id="projectFolderInput" type="file" webkitdirectory directory multiple style="display:none"></div>${helper}</div>`}
function progressModeButtons(){const modes=[["status","目前狀態"],["project","專案敘述"],["stages","開發階段"],["docs","AGENTS / PRD"]];return`<div class="card"><h2>切換檢視</h2><div class="summary">這裡先確認你看的專案資料夾，再切換查看狀態、專案描述、開發階段或規則文件。</div><div class="flow-switch">${modes.map(([key,label])=>`<button class="flow-btn ${progressMode===key?"active":""}" data-progress-mode="${key}">${label}</button>`).join("")}</div></div>`}
function progressStageMapHtml(parsed,src){if(src.projectType!=="console")return`<div class="card"><h2>目前查看的是其他專案</h2><div class="summary">你現在選的是 <code>${esc(src.path||src.name)}</code>，這裡不再顯示本控制台自己的 v1.0～v1.9 版本地圖，避免誤以為那是該專案的版本。</div><div class="summary">這個頁面只能根據該專案根目錄的 <code>DUAL-AI-STATE.md</code>、<code>NEXT-AI-TASK.md</code>、<code>AGENTS.md</code>、<code>PRD.md</code> 顯示資訊；如果這些檔案不存在，下面就只會看到缺檔提示。</div></div>`;const currentVersion=(parsed.current.match(/v\d+\.\d+/)||[])[0]||"";return`<div class="card"><h2>控制台版本地圖</h2><div class="summary">這裡顯示整個控制台從 v1.0 到目前版本的開發階段；目前版本會用藍框標出來。</div><div class="workflow-guide">${PROJECT_STAGES.map(([version,title,desc])=>{const active=currentVersion===version?" state-stage-active":"";return`<div class="guide-item${active}"><div class="guide-label">${esc(version)}｜${esc(title)}</div><div class="guide-text">${esc(desc)}</div></div>`}).join("")}</div></div>`}
function progressStatusHtml(parsed,src){const summary=parsed.ok?`<div class="state-summary"><div class="state-item full"><div class="state-label">目前查看資料夾</div><div class="state-value">${esc(src.path||src.name)}</div></div><div class="state-item full"><div class="state-label">目前階段</div><div class="state-value">${esc(parsed.current)}</div></div><div class="state-item full"><div class="state-label">上一步做了什麼</div><div class="state-value">${esc(parsed.done)}</div></div><div class="state-item full"><div class="state-label">下一步</div><div class="state-value">${esc(parsed.next)}</div></div><div class="state-item full"><div class="state-label">未解決問題</div><div class="state-value">${esc(parsed.unresolved)}</div></div></div>`:`<div class="state-summary"><div class="state-item full"><div class="state-label">目前查看資料夾</div><div class="state-value">${esc(src.path||src.name)}</div></div></div>${stateSummaryHtml(parsed)}`;return`${progressStageMapHtml(parsed,src)}${summary}`}
function progressProjectHtml(src){const projectName=(src.agents.raw.match(/專案名稱：\s*(.*)/)||[])[1]?.trim()||src.name||"尚未設定。";const projectIntro=(src.agents.raw.match(/專案簡介：\s*(.*)/)||[])[1]?.trim()||"尚未設定。";const goal=mdSection(src.prd.raw,"2. 專案目標");const scope=mdSection(src.prd.raw,"4. 功能清單");return`<div class="state-summary"><div class="state-item full"><div class="state-label">資料夾</div><div class="state-value">${esc(src.path||src.name)}</div></div><div class="state-item full"><div class="state-label">專案名稱</div><div class="state-value">${esc(projectName)}</div></div><div class="state-item full"><div class="state-label">專案敘述</div><div class="state-value">${esc(projectIntro)}</div></div><div class="state-item full"><div class="state-label">專案目標</div><div class="state-value">${esc(goal)}</div></div><div class="state-item full"><div class="state-label">功能清單</div><div class="state-value">${esc(scope)}</div></div></div>`}
function progressStagesHtml(src){return`<div class="card"><h2>二刀流開發階段</h2><div class="workflow-guide">${FLOW_ORDER.dualai.filter(stage=>["1","2","3","4","5"].includes(stage)).map(stage=>{const meta=STAGE_META.dualai[stage];return`<div class="guide-item"><div class="guide-label">${esc(meta[0])}</div><div class="guide-text">${esc(meta[1])}</div></div>`}).join("")}</div></div><div class="card"><h2>本專案 / 網站開發階段</h2><div class="summary">${esc(mdSection(src.prd.raw,"1. 專案背景"))}</div><div class="summary">${esc(mdSection(src.prd.raw,"2. 專案目標"))}</div><div class="summary">${esc(mdSection(src.prd.raw,"6. 驗收標準"))}</div></div>`}
function progressDocsHtml(src){return`<div class="card"><h2>AGENTS.md</h2>${src.agents.html}</div><div class="card"><h2>PRD.md</h2>${src.prd.html}</div>`}
function progressHtml(){const src=progressSource();const parsed=parseWorkflowState(src.state.raw);const body={status:progressStatusHtml(parsed,src),project:progressProjectHtml(src),stages:progressStagesHtml(src),docs:progressDocsHtml(src)}[progressMode]||progressStatusHtml(parsed,src);return`<div class="sop progress-sop">${progressPickerHtml(src)}${progressFileCheckHtml(src)}${progressModeButtons()}${body}</div>`}
async function filesFromDirectoryHandle(handle,prefix=""){const files=[];for await (const entry of handle.values()){const nextPrefix=prefix?`${prefix}/${entry.name}`:entry.name;if(entry.kind==="file"){const file=await entry.getFile();try{Object.defineProperty(file,"webkitRelativePath",{configurable:true,value:nextPrefix})}catch{}files.push(file)}else if(entry.kind==="directory"){files.push(...await filesFromDirectoryHandle(entry,nextPrefix))}}return files}
async function loadProjectFolder(files,rootName=""){const list=[...files];if(!list.length){progressPickerMessage="沒有讀到任何檔案；請確認你選的是資料夾，而且瀏覽器允許讀取。";render();return}const root=rootName||(list[0]?.webkitRelativePath||"").split("/")[0]||"使用者選擇的專案";const find=name=>list.find(file=>file.name===name||file.webkitRelativePath.endsWith(`/${name}`));const read=async name=>{const file=find(name);return file?await file.text():""};const state=await read("DUAL-AI-STATE.md"),next=await read("NEXT-AI-TASK.md"),agents=await read("AGENTS.md"),prd=await read("PRD.md");selectedProject={name:root,path:root,state:{raw:state,html:simpleMarkdownHtml(state,"DUAL-AI-STATE")},next:{raw:next,html:simpleMarkdownHtml(next,"NEXT-AI-TASK")},agents:{raw:agents,html:simpleMarkdownHtml(agents,"AGENTS")},prd:{raw:prd,html:simpleMarkdownHtml(prd,"PRD")},projectType:"picked"};progressPickerMessage=`已載入資料夾：${root}`;progressMode="status";render()}
async function pickProjectFolder(){const picker=document.getElementById("projectFolderInput");if(window.showDirectoryPicker){try{const handle=await window.showDirectoryPicker();const files=await filesFromDirectoryHandle(handle);await loadProjectFolder(files,handle.name);return}catch(err){if(err?.name==="AbortError")return;if(!picker){progressPickerMessage=`資料夾選取失敗：${err?.message||"目前瀏覽器不支援。"}`;render();return}}}if(!picker){progressPickerMessage="找不到備援的資料夾選取元件，請重新整理頁面再試。";render();return}picker.value="";try{picker.click()}catch(err){progressPickerMessage=`這個瀏覽器沒有成功打開資料夾選取視窗：${err?.message||"可能不支援 file:// 下的資料夾存取。"}`;render()}}
function bindProgress(){document.querySelectorAll("[data-progress-mode]").forEach(btn=>btn.onclick=()=>{progressMode=btn.dataset.progressMode;render()});const picker=document.getElementById("projectFolderInput");const pickBtn=document.querySelector("[data-progress-pick]");if(pickBtn)pickBtn.onclick=()=>pickProjectFolder();if(picker)picker.onchange=e=>loadProjectFolder(e.target.files)}
function stateBoardHtml(){const draft=stateDraft();const parsed=parseWorkflowState(draft);return`<div class="card state-board"><h2>DUAL-AI-STATE 快速看板</h2><div class="summary">把狀態檔全文貼在這裡，控制台只在瀏覽器本機解析與暫存，不上傳、不寫回檔案。</div><textarea id="workflowStateInput" placeholder="貼上 DUAL-AI-STATE.md 全文">${esc(draft)}</textarea><div id="workflowStateResult">${stateSummaryHtml(parsed)}</div></div>`}
function updateControlActive(stage){document.querySelectorAll("[data-control-card-stage]").forEach(card=>card.classList.toggle("state-stage-active",!!stage&&card.dataset.controlCardStage===stage))}
function controlHtml(){const parsed=parseWorkflowState(stateDraft());return`${stateBoardHtml()}<div class="grid">${CONTROL_STAGES.map(item=>{const meta=STAGE_META.dualai[item.stage]||[item.stage,item.purpose];const info=controlPromptInfo(item);const prompt=info.prompt||`請進入 dual-ai-workflow ${meta[0]}，依目前專案實際狀態接續。`;const active=parsed.stage&&item.stage===parsed.stage?" state-stage-active":"";return`<div class="card${active}" data-control-card-stage="${esc(item.stage)}"><h3>${esc(meta[0])} <span class="cat-tag">${esc(item.role)}</span></h3><div class="usage">${esc(item.purpose)}</div><div class="summary">${esc(item.plain)}</div><div class="usage">prompt 已複製到剪貼簿，提示詞庫已切到二刀流協作，請對照階段瀏覽。</div><button class="copy-btn" data-control-stage="${esc(info.targetStage)}" data-control-prompt="${esc(info.targetPrompt)}" data-control-copy="${encodeURIComponent(prompt)}">跳到提示詞庫並複製 prompt</button></div>`}).join("")}</div>`}
function bindControl(){document.querySelectorAll("[data-control-stage]").forEach(btn=>btn.onclick=()=>{copyText(decodeURIComponent(btn.dataset.controlCopy),btn);const targetStage=btn.dataset.controlStage;const targetPrompt=btn.dataset.controlPrompt;setTimeout(()=>{flowMode="dualai";q="";document.getElementById("searchBox").value="";setTab("prompts");setTimeout(()=>{const target=targetPrompt?[...document.querySelectorAll("[data-prompt-key]")].find(card=>card.dataset.promptKey===targetPrompt):null;(target||document.querySelector(`[data-stage="${targetStage}"]`))?.scrollIntoView({behavior:"smooth",block:"start"})},80)},260)})}
function bindStateBoard(){const input=document.getElementById("workflowStateInput");const result=document.getElementById("workflowStateResult");if(input&&result)input.oninput=()=>{localStorage.setItem("workflow-state-draft",input.value);const parsed=parseWorkflowState(input.value);result.innerHTML=stateSummaryHtml(parsed);updateControlActive(parsed.stage)}}
const PROMPT_CATEGORIES=["專案啟動","開發過程","版本控制","整合串接","上線部署","二刀流協作","Skill 管理","安全檢查","二刀流工作流","單一 AI 精簡","其他"];
function storageKey(){return captureMode==="skill"?"capture-draft-skill":"capture-draft-prompt"}
function readDraft(){try{return JSON.parse(localStorage.getItem(storageKey())||"{}")}catch{return{}}}
function writeDraft(data){localStorage.setItem(storageKey(),JSON.stringify(data))}
function formVal(id){return document.getElementById(id)?.value||""}
function formChecked(id){return !!document.getElementById(id)?.checked}
function yamlScalar(value){return (value||"").replace(/\\/g,"\\\\").replace(/"/g,'\\"')}
function yamlBlock(value,indent="  "){const lines=(value||"").split(/\r?\n/);return lines.map(line=>indent+line).join("\n")}
function optionsHtml(list,active){return list.map(item=>`<option value="${esc(item)}" ${item===active?"selected":""}>${esc(item)}</option>`).join("")}
function promptCategories(){return PROMPT_CATEGORIES}
function skillCategories(){return [...new Set(DATA.skills.map(s=>s.category)),"其他"]}
function promptDraft(){const data=readDraft();return{title:data.title||"",category:data.category||"專案啟動",categoryOther:data.categoryOther||"",usage:data.usage||"",flow:data.flow||"common",stage:data.stage||"",prompt:data.prompt||""}}
function skillDraft(){const data=readDraft();return{source:data.source||""}}
function captureData(){if(captureMode==="skill")return{source:formVal("skillSource")};return{title:formVal("promptTitle"),category:formVal("promptCategory")==="其他"?formVal("promptCategoryOther"):formVal("promptCategory"),categoryOther:formVal("promptCategoryOther"),usage:formVal("promptUsage"),flow:formVal("promptFlow")||"common",stage:formVal("promptStage"),prompt:formVal("promptText")}}
function promptYaml(d){return`- title: ${d.title||"【標題】"}\n  category: ${d.category||"專案啟動"}\n  usage: ${d.usage||"【用途】"}\n  flow: ${d.flow||"common"}\n  stage: '${yamlScalar(d.stage||"")}'\n  prompt: |-\n${yamlBlock(d.prompt||"【提示詞內容】","    ")}`}
function skillYaml(d){return`# Skill 模式不需要手寫 YAML。\n# source 會從上方 Skill 網址欄自動帶入；Codex 先跑安檢，安全後再整理 data/skills.yaml 欄位。\nsource: ${d.source||"【上方 Skill 網址欄尚未填寫】"}`}
function skillCapturePrompt(d){const source=d.source||"【上方 Skill 網址欄尚未填寫】";return`請幫我安裝並收錄這個 Skill，但必須先跑安檢，安全才可以安裝。\n\nSkill 來源（已由上方 Skill 網址欄自動帶入）：${source}\n\n請依序處理：\n1. 先使用本專案「安檢流程」檢查來源、腳本、權限、憑證讀取、外部下載、提示詞注入與可追溯性。\n2. 若風險為「不要裝」或有高風險不確定項，請停止，不要安裝，並用小白能懂的話說明原因。\n3. 若風險可接受，才安裝到 Codex 與 Claude Code 兩邊可讀的位置：\n   - ~/.codex/skills/\n   - ~/.claude/skills/\n4. 讀取 skill 內容後，自動整理中文摘要、分類、風險等級、觸發句與注意事項，寫入 data/skills.yaml。\n5. 執行 python3 scripts/build.py 重建 index.html。\n6. 驗證 index.html 搜尋得到新 Skill 卡片，並確認 Codex / Claude Code 安裝位置都有該 skill。\n7. 更新 codex-skills-backup.tar.gz。\n8. 回報：安檢結論、安裝位置、收錄到 data/skills.yaml 的內容、驗證結果、是否還有風險。\n9. 不要自動 commit 或 push，等使用者決定。`}
function codexCapturePrompt(d){if(captureMode==="skill")return skillCapturePrompt(d);const target="data/prompts.yaml";const yaml=promptYaml(d);return`請把下面這筆新內容收錄進控制台。\n\n要求：\n1. 先檢查內容格式與風險。\n2. 寫入 ${target}。\n3. 執行 python3 scripts/build.py 重建 index.html。\n4. 驗證 index.html 搜尋得到新卡片。\n5. 建立本地 git commit，commit message 使用繁體中文。\n6. 不要 push origin/main，等使用者決定。\n\n建議 YAML 片段如下：\n\n${yaml}`}
function captureMissing(d){return captureMode==="skill"?[!d.source&&"Skill 網址或路徑"].filter(Boolean):[!d.title&&"標題",!d.usage&&"用途",!d.prompt&&"提示詞原文"].filter(Boolean)}
function captureLinkHtml(d,disabled){const missing=captureMissing(d);const status=missing.length?(captureMode==="skill"?"請先填上方 Skill 網址欄":`還差：${missing.join("、")}`):captureMode==="skill"?"已連到上方 Skill 網址，可複製提示詞":"已可複製交辦提示詞";const first=captureMode==="skill"?["貼上 Skill 網址","只要貼 GitHub URL 或本機資料夾路徑。"]:["填上方表單","標題、分類、用途與原文會即時存成草稿。"];const second=captureMode==="skill"?["下方自動產生","提示詞會讀取上方網址，要求 AI 先安檢，安全後才安裝。"]:["下方自動產生","交辦提示詞與 YAML 片段會跟表單同步更新。"];return`<div class="capture-link" id="captureLink"><div class="capture-step"><span>1</span><div><b>${esc(first[0])}</b><small>${esc(first[1])}</small></div></div><div class="capture-arrow">→</div><div class="capture-step"><span>2</span><div><b>${esc(second[0])}</b><small>${esc(second[1])}</small></div></div><div class="capture-status">${esc(status)}</div></div>`}
function captureHtml(){const d=captureMode==="skill"?skillDraft():promptDraft();const categoryList=captureMode==="skill"?skillCategories():promptCategories();const category=d.categoryOther?"其他":d.category;const otherStyle=category==="其他"?"":"display:none";const yaml=captureMode==="skill"?skillYaml(d):promptYaml(d);const codex=codexCapturePrompt(d);const disabled=false;const codexTitle=captureMode==="skill"?"推薦複製：給 Codex 的安檢＋安裝提示詞":"推薦複製：給 Codex 的完整交辦提示詞";const codexHelp=captureMode==="skill"?"這張卡由上方網址即時產生；複製給 Codex 後，AI 會先跑安檢，安全才安裝到 Codex 與 Claude Code。":"這張卡由上方表單即時產生；填完表單後，直接複製這段交給 Codex 收錄、重建與驗證。";const yamlHelp=captureMode==="skill"?"Skill 模式不需要你手寫 YAML；AI 安檢並讀取 skill 後，會自動整理欄位再寫入 data/skills.yaml。":"這張卡同樣由上方表單即時產生；懂 YAML 時可檢查這段，不懂也沒關係，複製上一張卡即可。";return`<div class="sop wide-sop"><div class="card"><div class="capture-switch"><button class="capture-btn ${captureMode==="prompt"?"active":""}" data-capture-mode="prompt">提示詞</button><button class="capture-btn ${captureMode==="skill"?"active":""}" data-capture-mode="skill">Skill</button></div><div class="summary">${captureMode==="skill"?"貼上 Skill 網址或資料夾路徑，下方會自動產生安檢＋安裝提示詞；安全後才會裝進 Codex 與 Claude Code。":"不知道怎麼填也沒關係，先貼原文。新手建議複製「給 Codex 的完整交辦提示詞」，讓 Codex 幫你寫入、重建、驗證與 commit。"}</div></div><div class="card"><h2>${captureMode==="skill"?"Skill 收錄表單":"提示詞收錄表單"}</h2>${captureMode==="skill"?skillForm(d):promptForm(d,categoryList,category,otherStyle)}</div>${captureLinkHtml(d,disabled)}<div class="card"><h2>${codexTitle}</h2><div class="summary">${codexHelp}</div><pre class="prompt-body" id="captureCodex">${esc(codex)}</pre><button class="copy-btn" data-copy="${encodeURIComponent(codex)}">複製交辦提示詞</button></div><div class="card"><h2>進階檢查：${captureMode==="skill"?"安裝摘要":"YAML 片段"}</h2><div class="summary">${yamlHelp}</div><pre class="prompt-body" id="captureYaml">${esc(yaml)}</pre><button class="copy-btn" data-copy="${encodeURIComponent(yaml)}">複製${captureMode==="skill"?"摘要":" YAML"}</button></div></div>`}
function promptForm(d,cats,category,otherStyle){return`<div class="form-grid"><div class="field"><label>標題</label><input id="promptTitle" data-capture-input value="${esc(d.title)}"><div class="help">這張卡片在控制台上顯示的名字。</div></div><div class="field"><label>分類</label><select id="promptCategory" data-capture-input>${optionsHtml(cats,category)}</select><input id="promptCategoryOther" data-capture-input style="${otherStyle}" value="${esc(d.categoryOther)}" placeholder="輸入其他分類"><div class="help">分類是之後搜尋和整理用的。</div></div><div class="field"><label>用途</label><input id="promptUsage" data-capture-input value="${esc(d.usage)}"><div class="help">什麼時候會用到它。</div></div><div class="field"><label>適用流程</label><select id="promptFlow" data-capture-input>${optionsHtml(["common","dualai","solo"],d.flow)}</select><div class="help">不確定就選 common。</div></div><div class="field"><label>階段</label><input id="promptStage" data-capture-input value="${esc(d.stage)}" placeholder="entry / 1 / 2 / 3 / 4 / 5 / archive"><div class="help">沒有階段就留空。</div></div><div class="field full"><label>提示詞原文</label><textarea id="promptText" data-capture-input>${esc(d.prompt)}</textarea><div class="help">貼上你想收錄的完整提示詞。</div></div></div>`}
function skillForm(d){return`<div class="form-grid"><div class="field full"><label>Skill 網址或資料夾路徑</label><input id="skillSource" data-capture-input class="${d.source?"":"needs-input"}" value="${esc(d.source)}" placeholder="貼上 GitHub URL 或本機資料夾路徑"><div class="help">這裡就是下方提示詞會讀取的 Skill 來源；貼上後會自動帶入安檢＋安裝提示詞。</div></div></div>`}
function updateCaptureOutputs(){const data=captureData();const yaml=captureMode==="skill"?skillYaml(data):promptYaml(data);const codex=codexCapturePrompt(data);const disabled=false;const yamlPre=document.getElementById("captureYaml"),codexPre=document.getElementById("captureCodex"),link=document.getElementById("captureLink"),skillSource=document.getElementById("skillSource");if(yamlPre)yamlPre.textContent=yaml;if(codexPre)codexPre.textContent=codex;if(link)link.outerHTML=captureLinkHtml(data,disabled);if(skillSource)skillSource.classList.toggle("needs-input",captureMode==="skill"&&!data.source);const buttons=document.querySelectorAll(".card .copy-btn");if(buttons.length>1){buttons[buttons.length-2].dataset.copy=encodeURIComponent(codex);buttons[buttons.length-1].dataset.copy=encodeURIComponent(yaml)}}
function bindCapture(){document.querySelectorAll("[data-capture-mode]").forEach(btn=>btn.onclick=()=>{captureMode=btn.dataset.captureMode;render()});document.querySelectorAll("[data-capture-input]").forEach(el=>el.oninput=el.onchange=()=>{const data=captureData();writeDraft(data);if(["promptCategory"].includes(el.id))render();else updateCaptureOutputs()})}
const CUSTOM_SKILL_DEFAULTS={role:"AI 系統開發與管理者",scenario:"工作決策陪練與挑刺",style:"直接、務實、先挑風險",target:"Codex 專用",skillName:"personal-work-coach",level:"先給結論，再補背景",pain:"我需要一個懂我職務、業務痛點與工作習慣的 AI 陪練，能先追問、再挑刺、最後把流程封裝成可重複使用的 skill。",extra:"請用繁體中文。不要無腦誇。需求不清楚時先問關鍵問題。涉及安裝或改檔時先說風險。"};
const CUSTOM_SKILL_FIELDS=["customRole","customScenario","customStyle","customTarget","customSkillName","customLevel","customPain","customExtra"];
function customSkillData(){const stored=JSON.parse(localStorage.getItem("custom-skill-builder")||"{}");return{...CUSTOM_SKILL_DEFAULTS,...stored}}
function customSkillRead(){const data={role:formVal("customRole"),scenario:formVal("customScenario"),style:formVal("customStyle"),target:formVal("customTarget"),skillName:formVal("customSkillName"),level:formVal("customLevel"),pain:formVal("customPain"),extra:formVal("customExtra")};localStorage.setItem("custom-skill-builder",JSON.stringify(data));return data}
function customSkillPromptText(d){return[`我想建立一個自己的個人化專屬 skill，請用 Codex 專用流程協助我完成。`,"",`我的基本設定：`,`- 我的職業 / 身分：${d.role}`,`- 主要用途：${d.scenario}`,`- 期待 AI 互動風格：${d.style}`,`- 回答深度：${d.level}`,`- Skill 名稱：${d.skillName}`,`- 安裝目標：${d.target}`,`- 目前痛點：${d.pain||"請先追問我，協助我釐清。"}`,`- 其他要求：${d.extra||"請用繁體中文，需求不清楚時先問。"}`,"","第一段：徹底理解我","現在你的首要身份是一個提問者。","請你問我所有你需要的問題，直到你真正理解：","1. 我的職務與日常工作情境","2. 我的業務核心訴求","3. 我的真實痛點","4. 我最常卡住的決策點","5. 我希望 AI 在工作中扮演的角色","","請一次最多問 5 個問題。問題要具體、好回答；必要時提供選項。","不要急著產出 skill。你要先問到能和我一起梳理出清晰路徑。","","第二段：做我的陪練與挑刺者","根據你對我的了解，接下來做我的陪練。","不管我提出什麼想法，不管我拋出什麼計劃，禁止無腦誇。","你的唯一任務是挑刺，請直白指出 3 到 5 個：","1. 我沒想到的風險點","2. 我忽略的關鍵問題","3. 可能導致失敗的假設","4. 需要先驗證的地方","5. 更務實的下一步","","輸出格式請固定為：","結論 / 建議","3 到 5 個風險點","我應該先回答或確認的問題","下一步最小行動","","第三段：封裝成 skill","當你已經懂我的痛點、職務人設與工作方式後，請幫我封裝成一個 skill。","請產出完整 skill 資料夾設計，至少包含：",`1. skill 名稱：${d.skillName}`,"2. SKILL.md 完整內容","3. 觸發規則：什麼情境下 AI 必須使用這個 skill","4. AI 回答規則：語氣、格式、禁止事項、風險提醒方式","5. 範例觸發句：至少 5 句","6. 安裝前風險檢查：是否會讀寫檔案、是否需要網路、是否接觸敏感資料","",`SKILL.md 要適合 ${d.target}，並且用繁體中文說明清楚。`,"","第四段：安裝與驗證","請在封裝完成後，先停止並列出安裝計畫與風險。","如果我確認要安裝，才進行安裝。","","安裝要求：","1. 不要刪除任何既有文件或資料夾。","2. 不要使用批量刪除指令。","3. 安裝前先檢查目標路徑是否存在。",`4. ${d.target==="Codex + Claude Code 都安裝"?"安裝到 Codex 與 Claude Code 兩邊可讀的位置。":`依「${d.target}」處理。`}`,"5. 安裝後驗證該 skill 的 SKILL.md 存在。","6. 回報安裝位置、檔案清單、如何觸發、如何測試。","","請先從第一段開始，不要跳到第三段，也不要直接寫檔。"].join("\n")}
function customSkillHtml(){const d=customSkillData();return`<div class="sop wide-sop"><div class="card"><h2>自製專屬 Skill 產生器</h2><div class="summary">直接在這裡選欄位，右側會即時產生可複製給 Codex 的完整提示詞。這不是安裝動作，只是先產生交辦內容。</div></div><div class="home-split"><div class="card"><h2>選單設定</h2><div class="form-grid"><div class="field"><label>你的職業 / 身分</label><select id="customRole" data-custom-skill-input>${optionsHtml(["AI 系統開發與管理者","資訊主管 / IT 管理者","行銷企劃 / 品牌經營者","資料整合 / 報表分析人員","創業者 / 老闆","自訂"],d.role)}</select></div><div class="field"><label>主要用途</label><select id="customScenario" data-custom-skill-input>${optionsHtml(["工作決策陪練與挑刺","AI 系統規劃與專案推進","提示詞工程與 SOP 建立","資料查詢、整合與報告產出","跨角色溝通與主管簡報"],d.scenario)}</select></div><div class="field"><label>AI 互動風格</label><select id="customStyle" data-custom-skill-input>${optionsHtml(["直接、務實、先挑風險","新手教學、一步一步帶我做","主管視角、重點摘要與決策建議","顧問式追問、先釐清再行動"],d.style)}</select></div><div class="field"><label>安裝目標</label><select id="customTarget" data-custom-skill-input>${optionsHtml(["Codex 專用","Claude Code 專用","Codex + Claude Code 都安裝","先只產生 SKILL.md，不安裝"],d.target)}</select></div><div class="field"><label>Skill 名稱</label><input id="customSkillName" data-custom-skill-input value="${esc(d.skillName)}" placeholder="personal-work-coach"></div><div class="field"><label>回答深度</label><select id="customLevel" data-custom-skill-input>${optionsHtml(["先給結論，再補背景","完整深入分析","只給最短可執行版本"],d.level)}</select></div><div class="field full"><label>你目前最想解決的痛點</label><textarea id="customPain" data-custom-skill-input>${esc(d.pain)}</textarea></div><div class="field full"><label>其他要求</label><textarea id="customExtra" data-custom-skill-input>${esc(d.extra)}</textarea></div></div><div class="builder-actions"><button class="copy-btn" type="button" id="customSkillReset">清空重選</button></div></div><div class="card"><h2>可複製提示詞</h2><pre class="prompt-body builder-preview" id="customSkillPrompt"></pre><button class="copy-btn" type="button" id="customSkillCopy">複製提示詞</button></div></div></div>`}
function updateCustomSkill(){const d=customSkillRead();const out=document.getElementById("customSkillPrompt");if(out)out.textContent=customSkillPromptText(d)}
function bindCustomSkill(){updateCustomSkill();document.querySelectorAll("[data-custom-skill-input]").forEach(el=>el.oninput=el.onchange=updateCustomSkill);const copy=document.getElementById("customSkillCopy");if(copy)copy.onclick=()=>copyText(document.getElementById("customSkillPrompt")?.textContent||"",copy);const reset=document.getElementById("customSkillReset");if(reset)reset.onclick=()=>{localStorage.removeItem("custom-skill-builder");const contentEl=document.getElementById("content");contentEl.innerHTML=customSkillHtml();bindCustomSkill()}}
function render(){const chips=document.getElementById("chips"),content=document.getElementById("content"),countLine=document.getElementById("countLine");renderOnlineBanner();renderLaunchTip();renderIntro();chips.innerHTML=cats().map(c=>`<button class="chip ${c===cat?"active":""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");chips.querySelectorAll(".chip").forEach(ch=>ch.onclick=()=>{cat=ch.dataset.cat;if(tab==="prompts"&&cat!=="全部")flowMode="common";render()});if(tab==="backup"){countLine.textContent="";content.innerHTML=backupHtml();return}if(tab==="guide"){countLine.textContent="";content.innerHTML=homeHtml();bindHome();return}if(tab==="daily"){countLine.textContent="";content.innerHTML=dailyHtml();return}if(tab==="customSkill"){countLine.textContent="";content.innerHTML=customSkillHtml();bindCustomSkill();return}if(tab==="progress"){countLine.textContent="";content.innerHTML=progressHtml();bindProgress();return}if(tab==="capture"){countLine.textContent="";content.innerHTML=captureHtml();bindCapture();return}if(tab==="control"){countLine.textContent="";content.innerHTML=controlHtml();bindControl();bindStateBoard();return}if(tab==="skills"){const items=DATA.skills.filter(s=>(cat==="全部"||s.category===cat)&&match(s,["name","summary","category","triggers","notes"]));countLine.textContent=`共 ${items.length} 個 skill`;content.innerHTML=items.length?`<div class="grid">${items.map(skillCard).join("")}</div>`:`<div class="empty">找不到符合條件的 skill。</div>`;return}if(tab==="prompts"){const count=DATA.prompts.filter(p=>(p.flow||"common")===flowMode&&(cat==="全部"||p.category===cat)&&match(p,["title","usage","category","prompt","flow","stage"])).length;countLine.textContent=`目前顯示 ${count} 則提示詞，總共 ${DATA.prompts.length} 則`;content.innerHTML=renderPromptFlow();content.querySelectorAll(".flow-btn").forEach(btn=>btn.onclick=()=>{flowMode=btn.dataset.flow;cat="全部";render()})}}
function setTab(next){document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));document.querySelector(`[data-tab="${next}"]`)?.classList.add("active");tab=next;cat="全部";render()}
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>setTab(t.dataset.tab));document.getElementById("searchBox").addEventListener("input",e=>{q=e.target.value.trim();render()});render();
</script>
</body>
</html>
'''

out = ROOT / "index.html"
html_out = (
    TEMPLATE.replace("__DATA_JSON__", data_json)
    .replace("__WORKFLOW_HTML__", workflow_json)
    .replace("__GUIDE_HTML__", guide_json)
    .replace("__STATE_HTML__", state_html)
    .replace("__NEXT_HTML__", next_html)
    .replace("__AGENTS_HTML__", agents_html)
    .replace("__PRD_HTML__", prd_html)
    .replace("__PROJECT_PATH__", project_path_json)
    .replace("__PROJECT_URL__", project_url_json)
)
out.write_text(html_out, encoding="utf-8")
print(f"OK: {out} built with {len(skills)} skills / {len(prompts)} prompts / {len(combos)} combos")
