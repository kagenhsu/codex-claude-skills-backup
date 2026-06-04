#!/usr/bin/env python3
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
    markdown_to_cards(ROOT / "docs" / "dual-ai-workflow.md", "三 AI 工作流", "尚未設定。"),
    ensure_ascii=False,
).replace("</", "<\\/")
guide_json = json.dumps(
    markdown_to_cards(ROOT / "docs" / "ai-role-guide.md", "AI 角色導覽", "尚未設定。"),
    ensure_ascii=False,
).replace("</", "<\\/")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Skill 助手控制台｜Codex / Claude Code / Claude Desktop</title>
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
  .copy-btn{width:100%; border:none; border-radius:8px; background:var(--accent); color:#fff; padding:7px 12px; font-size:.82rem; cursor:pointer; transition:background .15s;}
  .trigger .copy-btn{width:auto; flex-shrink:0;}
  .copy-btn:hover{background:#2f5cc4;}
  .copy-btn.done{background:var(--green);}
  pre.prompt-body{background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:10px 12px; font-size:.8rem; color:#33405e; white-space:pre-wrap; font-family:inherit; max-height:170px; overflow:auto;}
  .flow-section{margin-top:18px;}
  .section-head{display:flex; align-items:baseline; justify-content:space-between; gap:12px; margin:0 0 10px; padding-bottom:6px; border-bottom:1px solid var(--border);}
  .section-head h2{font-size:1rem;}
  .section-head .hint{font-size:.8rem; color:var(--muted);}
  .sop{max-width:780px; display:flex; flex-direction:column; gap:16px;}
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
  .field textarea{min-height:120px; resize:vertical;}
  .capture-switch{display:flex; gap:8px; flex-wrap:wrap;}
  .capture-btn{padding:7px 13px; border-radius:999px; border:1px solid var(--border); background:var(--card); color:var(--muted); cursor:pointer;}
  .capture-btn.active{background:var(--accent); border-color:var(--accent); color:#fff;}
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
  .empty{color:var(--muted); text-align:center; padding:36px 0;}
  footer{text-align:center; color:var(--muted); font-size:.75rem; padding:20px;}
  @media (max-width:760px){main,header{padding-left:14px; padding-right:14px;} .grid,.intro-grid,.workflow-guide,.state-summary{grid-template-columns:1fr;} .section-head{display:block;} }
</style>
</head>
<body>
<header><div class="head-inner"><h1>Skill 助手控制台 <span class="sub">Codex / Claude Code / Claude Desktop 導覽版</span></h1><div class="tabs"><button class="tab active" data-tab="guide">AI 角色導覽</button><button class="tab" data-tab="skills">Skills</button><button class="tab" data-tab="prompts">提示詞庫</button><button class="tab" data-tab="capture">收錄新內容</button><button class="tab" data-tab="control">三方中控</button><button class="tab" data-tab="workflow">三方 AI 工作流</button><button class="tab" data-tab="sop">安檢 SOP</button><button class="tab" data-tab="backup">換電腦／同步</button></div></div></header>
<main><div class="search"><span class="icon">搜</span><input id="searchBox" type="text" placeholder="搜尋 skill、提示詞、觸發句、角色、分工、導覽，例如：git、翻譯、審查、三 AI"></div><div id="pageIntro" class="page-intro"></div><div id="chips" class="chips"></div><div id="countLine" class="count"></div><div id="content"></div></main>
<footer>資料來源：data/skills.yaml + data/prompts.yaml + data/combos.yaml；修改後執行 python3 scripts/build.py 重建</footer>
<script>
const DATA = __DATA_JSON__;
const WORKFLOW_HTML = __WORKFLOW_HTML__;
const GUIDE_HTML = __GUIDE_HTML__;
let tab = "guide", cat = "全部", q = "", flowMode = "dualai", captureMode = "prompt";
const FLOW_META = {
  dualai:{label:"三方 AI 協作",title:"三方 AI 工作流提示詞",lead:"適合重要系統修改：Codex 是主力工程師，負責規劃、分段實作、測試與修正；Claude Code（VS Code）是審查員，負責架構審查、風險檢查與複審；Claude Desktop 是顧問／文字助理，負責需求、文件與提示詞。"},
  solo:{label:"單一 AI 使用",title:"單一 AI 使用提示詞",lead:"同事只有單一 AI 時，也能用這些提示詞讓 AI 先釐清、再分段執行、最後提醒是否需要審查。"},
  common:{label:"通用",title:"通用提示詞",lead:"日常可直接複製使用的提示詞，例如 Skill 安檢、交接、摘要與一般 AI 工作輔助。"}
};
const STAGE_META = {
  dualai:{entry:["入口","啟動或接續三方 AI 工作流"],"1":["第 1 階段：Codex","規劃、拆任務、建立狀態檔"],"2":["第 2 階段：Codex","分段實作、build、驗證"],"3":["第 3 階段：Claude Code（VS Code）","審查 diff、架構與風險"],"4":["第 4 階段：Codex","逐條修正、重新驗證"],"5":["第 5 階段：Claude Code（VS Code）","複審並確認可收尾"],handoff:["轉交","把目前狀態交給下一方"],status:["狀態檔","讀寫 DUAL-AI-STATE.md"],archive:["存檔收尾","第 5 階段通過後驗證、更新狀態檔與交還 push 決定權"],"desktop-summary":["主管版摘要","請 Claude Desktop 整理給人看的進度摘要"]},
  solo:{entry:["入口","只用一個 AI 時先用這張說明工作方式"],"1":["第 1 步","釐清任務與目標"],"2":["第 2 步","提出方案、先不修改"],"3":["第 3 步","分段執行並自我檢查"],"4":["第 4 步","收尾、整理驗證與 commit 建議"]}
};
const FLOW_ORDER = {dualai:["entry","1","2","3","4","5","handoff","status"],solo:["entry","1","2","3","4"]};
const PAGE_INTROS = {
  backup:{title:"換電腦／同步",lead:"這頁只在換電腦、重裝工具，或要把已整理好的 skills 同步到另一台機器時使用。平常找功能請看 Skills；要複製工作指令請看提示詞庫。",purpose:"把這個專案保存的 skills 備份包，安裝到 Codex 或 Claude Code 可讀的位置。",first:"如果不是換電腦或重裝，通常不用按這頁的還原指令。",when:"換電腦、重裝工具、同步 Mac mini 或 VS Code Claude Code 時使用。"},
  skills:{title:"Skills",lead:"查看每個 skill 的用途、風險與觸發句，直接複製給 AI 使用。",purpose:"快速判斷要叫哪個 AI skill。",first:"搜尋關鍵字，再複製觸發句。",when:"不確定某個任務該用哪個 skill 時。"},
  prompts:{title:"提示詞庫",lead:"常用提示詞集中管理，適合你直接複製給 Codex、Claude Code（VS Code）或 Claude Desktop。",purpose:"快速啟動工作流程。",first:"先選三方 AI、單一 AI 或通用分類，再複製。",when:"要交辦任務、請 AI 審查、整理交接或產出文件時。"},
  capture:{title:"收錄新內容",lead:"看到好用提示詞或 skill 時，先填表產生交辦提示詞與 YAML 片段，再交給 Codex 寫入、重建、驗證與 commit。",purpose:"安全收錄新內容，不需要你手寫 YAML。",first:"先選提示詞或 Skill；新手請複製「給 Codex 的完整交辦提示詞」。",when:"看到新 skill、實用提示詞，或想把工作流模板收入控制台時。"},
  control:{title:"三方中控",lead:"v1 是靜態教學頁，不讀取 DUAL-AI-STATE.md；按鈕只會跳到提示詞庫並複製對應提示詞。",purpose:"讓每個階段知道要找誰、做什麼、複製哪張提示詞。",first:"先看目前要進哪一階段，再按卡片按鈕複製對應提示詞。",when:"要從規劃、實作、審查、修正、複審到存檔收尾一路接續時。"},
  workflow:{title:"三方 AI 工作流",lead:"說明 Codex、Claude Code（VS Code）、Claude Desktop 的協作流程：Codex 做主力工程，Claude Code 做審查複審，Claude Desktop 做需求與文字輔助。",purpose:"讓三方各做各的，避免同時亂改或角色混淆。",first:"先讀 DUAL-AI-STATE.md，再接續目前階段。",when:"做網站、系統、腳本、多裝置同步或 git 存檔時。"},
  guide:{title:"AI 角色導覽",lead:"這頁幫新手判斷 Codex、Claude Code（VS Code）、Claude Desktop 各自適合做什麼。",purpose:"快速判斷誰負責規劃、實作、審查、文件或提示詞。",first:"先看角色表，再到提示詞庫複製對應模板。",when:"不確定要叫哪個 AI 處理，或同事只有單一 AI 可用時。"},
  sop:{title:"安檢 SOP",lead:"安裝或使用外部 skill 前，先檢查是否有高風險指令與敏感權限。",purpose:"降低誤裝危險 skill 的風險。",first:"先複製安檢提示詞給 AI。",when:"安裝陌生 skill、看到 danger 或會操作帳號/API 時。"}
};
const riskCls = {"低":"low","中":"mid","高":"high"};
const esc = s => (s ?? "").toString().replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
function copyText(text, btn){const done=()=>{btn.textContent="已複製";btn.classList.add("done");setTimeout(()=>{btn.textContent="複製";btn.classList.remove("done");},1400)};if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done).catch(fallback)}else fallback();function fallback(){const ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);ta.select();document.execCommand("copy");document.body.removeChild(ta);done()}}
document.addEventListener("click",e=>{const b=e.target.closest("[data-copy]");if(b)copyText(decodeURIComponent(b.dataset.copy),b)});
function match(obj,fields){if(!q)return true;const hay=fields.map(f=>Array.isArray(obj[f])?obj[f].join(" "):(obj[f]||"")).join(" ").toLowerCase();return hay.includes(q.toLowerCase())}
function cats(){if(tab==="skills")return["全部",...new Set(DATA.skills.map(s=>s.category))];if(tab==="prompts")return["全部","專案啟動"];return[]}
function renderIntro(){const info=PAGE_INTROS[tab];document.getElementById("pageIntro").innerHTML=`<h2>${esc(info.title)}</h2><div class="lead">${esc(info.lead)}</div><div class="intro-grid"><div class="intro-item"><div class="intro-label">用途</div><div class="intro-text">${esc(info.purpose)}</div></div><div class="intro-item"><div class="intro-label">先做</div><div class="intro-text">${esc(info.first)}</div></div><div class="intro-item"><div class="intro-label">適合情境</div><div class="intro-text">${esc(info.when)}</div></div></div>`}
function skillCard(s){const triggers=(s.triggers||[]).map(t=>`<div class="trigger"><code>${esc(t)}</code><button class="copy-btn" data-copy="${encodeURIComponent(t)}">複製</button></div>`).join("");return`<div class="card"><h3>${esc(s.name)} <span class="badge ${riskCls[s.risk]||"low"}">${esc(s.risk)}風險</span> <span class="cat-tag">${esc(s.category)}</span></h3><div class="summary">${esc(s.summary)}</div>${s.notes?`<div class="notes">${esc(s.notes)}</div>`:""}${triggers}</div>`}
function stageLabel(p){if(!p.flow||!p.stage)return"通用";const meta=STAGE_META[p.flow]?.[p.stage];return meta?meta[0]:p.stage}
function promptCard(p){return`<div class="card"><h3>${esc(p.title)} <span class="stage-tag">${esc(stageLabel(p))}</span> <span class="cat-tag">${esc(p.category)}</span></h3><div class="usage">${esc(p.usage)}</div><pre class="prompt-body">${esc(p.prompt)}</pre><button class="copy-btn" data-copy="${encodeURIComponent(p.prompt)}">複製</button></div>`}
function comboPrompt(combo){const lines=[`以下是「${combo.title}」。`,combo.usage||"", ""];const missing=[];(combo.steps||[]).forEach((step,idx)=>{const prompt=DATA.prompts.find(p=>p.title===step.prompt_title);if(!prompt){missing.push(step.prompt_title);return}if(step.custom_intro)lines.push(step.custom_intro,"");lines.push(`--- Prompt ${idx+1}：${prompt.title} ---`,prompt.prompt,"")});if(missing.length)lines.unshift(`提醒：找不到以下提示詞，已略過：${missing.join("、")}`,"");return lines.join("\n").trim()}
function comboCard(combo){const missing=(combo.steps||[]).filter(step=>!DATA.prompts.some(p=>p.title===step.prompt_title)).map(step=>step.prompt_title);const steps=(combo.steps||[]).map(step=>`<li>${esc(step.prompt_title)}</li>`).join("");const text=comboPrompt(combo);return`<div class="combo-card"><h3>${esc(combo.title)} <span class="cat-tag">${esc(combo.category||"組合包")}</span></h3><div class="usage">${esc(combo.usage||"")}</div>${missing.length?`<div class="warning">缺少提示詞：${esc(missing.join("、"))}</div>`:""}<ol class="combo-steps">${steps}</ol><button class="copy-btn" data-copy="${encodeURIComponent(text)}">複製整包（${(combo.steps||[]).length} 張）</button></div>`}
function combosHtml(){const combos=DATA.combos||[];if(!combos.length)return"";return`<section class="flow-section"><div class="section-head"><h2>常用組合包</h2><span class="hint">一鍵複製常用流程</span></div><div class="combo-grid">${combos.map(comboCard).join("")}</div></section>`}
function workflowGuide(){if(flowMode==="dualai")return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">Codex</div><div class="guide-text">主力工程師：規劃、分段實作、測試、修正。</div></div><div class="guide-item"><div class="guide-label">Claude Code（VS Code）</div><div class="guide-text">審查員：看 diff、抓風險、提出 P0/P1/P2 問題。</div></div><div class="guide-item"><div class="guide-label">Claude Desktop</div><div class="guide-text">顧問／文字助理：整理需求、提示詞、主管版說明。</div></div></div>`;if(flowMode==="solo")return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">先規劃</div><div class="guide-text">讓單一 AI 先讀文件並列出做法。</div></div><div class="guide-item"><div class="guide-label">再實作</div><div class="guide-text">只做最小必要修改，避免一次改太大。</div></div><div class="guide-item"><div class="guide-label">要自檢</div><div class="guide-text">請 AI 用審查角度檢查結果。</div></div></div>`;return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">專案啟動</div><div class="guide-text">AGENTS、PRD、交接摘要與規劃模板。</div></div><div class="guide-item"><div class="guide-label">工程常用</div><div class="guide-text">Git、API、部署與資料庫模板。</div></div><div class="guide-item"><div class="guide-label">Skill 管理</div><div class="guide-text">新增 skill、資安檢查與提示詞收錄。</div></div></div>`}
function flowButtons(){return`<div class="flow-switch">${Object.entries(FLOW_META).map(([key,m])=>`<button class="flow-btn ${flowMode===key?"active":""}" data-flow="${key}">${m.label}</button>`).join("")}</div>`}
function renderPromptFlow(){const meta=FLOW_META[flowMode];const visible=DATA.prompts.filter(p=>(p.flow||"common")===flowMode&&(cat==="全部"||p.category===cat)&&match(p,["title","usage","category","prompt","flow","stage"]));let html=`<div class="page-intro"><h2>${esc(meta.title)}</h2><div class="lead">${esc(meta.lead)}</div>${workflowGuide()}</div>${flowButtons()}`;if(cat==="全部"&&!q)html+=combosHtml();if(flowMode==="common"){const groups=[...new Set(visible.map(p=>p.category))];html+=groups.map(group=>{const items=visible.filter(p=>p.category===group);return`<section class="flow-section"><div class="section-head"><h2>${esc(group)}</h2><span class="hint">${items.length} 則</span></div><div class="grid">${items.map(promptCard).join("")}</div></section>`}).join("")}else{html+=FLOW_ORDER[flowMode].map(stage=>{const items=visible.filter(p=>String(p.stage||"")===stage);if(!items.length)return"";const[label,hint]=STAGE_META[flowMode][stage]||[stage,""];return`<section class="flow-section"><div class="section-head"><h2>${esc(label)}</h2><span class="hint">${esc(hint)}，${items.length} 則</span></div><div class="grid">${items.map(promptCard).join("")}</div></section>`}).join("")}return html||`<div class="empty">找不到符合條件的提示詞。</div>`}
function cmdRow(label,cmd){return`<div class="trigger"><div style="flex:1"><div class="usage">${esc(label)}</div><code>${esc(cmd)}</code></div><button class="copy-btn" data-copy="${encodeURIComponent(cmd)}">複製</button></div>`}
function backupHtml(){return`<div class="sop"><div class="card"><h2>這頁是做什麼</h2><div class="summary">簡單說：這頁不是日常功能頁，而是「搬家工具」。當你換電腦、重裝 Codex / Claude Code，或要把同一套 skills 放到另一台機器時才用。</div><ul><li><b>codex-skills-backup.tar.gz</b>：已整理好的 skills 備份包</li><li><b>restore-skills.sh</b>：把備份包安裝到 Codex / Claude Code 的 skills 目錄</li><li><b>平常找功能</b>：請切到 Skills 或提示詞庫，不用執行這裡的指令</li></ul></div><div class="card"><h2>同步到新環境的指令</h2>${cmdRow("只有換電腦／重裝時才執行","./restore-skills.sh")}</div></div>`}
const CONTROL_STAGES=[
  {stage:"1",role:"Codex",purpose:"規劃與拆任務",plain:"先把需求變成可做的清單，避免一開始就亂改檔。"},
  {stage:"2",role:"Codex",purpose:"分段實作與驗證",plain:"一段一段做，每段 build、檢查、commit。"},
  {stage:"3",role:"Claude Code（VS Code）",purpose:"審查 diff 與風險",plain:"請另一個 AI 用審查員角度抓 P0/P1/P2 問題。"},
  {stage:"4",role:"Codex",purpose:"逐條修正審查意見",plain:"把審查意見搬回 Codex，逐條處理並重新驗證。"},
  {stage:"5",role:"Claude Code（VS Code）",purpose:"複審與通過確認",plain:"修完後再請審查員確認沒有殘留問題。"},
  {stage:"archive",role:"Codex",purpose:"存檔收尾",plain:"複審通過後做最後驗證、更新狀態檔、commit，push 決定權交回使用者。",query:"存檔收尾",fallback:"請依 dual-ai-workflow 第 5 階段通過後的收尾流程，重新驗證、更新 DUAL-AI-STATE.md、建立本地 commit，並把是否 push origin/main 的決定權交回使用者。"},
  {stage:"desktop-summary",role:"Claude Desktop",purpose:"主管版摘要",plain:"把目前進度整理成非工程同事也看得懂的摘要。",query:"Claude Desktop 主管 摘要",fallback:"請整理這個專案目前進度的主管版摘要：用繁體中文列出已完成、正在做、下一步、風險與需要使用者決定的事項。"}
];
function controlPrompt(item){if(item.stage==="archive"){const p=DATA.prompts.find(p=>String(p.stage||"")==="archive"||p.title.includes("存檔收尾"));if(p)return p.prompt}if(item.stage==="desktop-summary"){const p=DATA.prompts.find(p=>String(p.stage||"")==="desktop-summary"||p.title.includes("主管版"));if(p)return p.prompt}const found=DATA.prompts.find(p=>(p.flow||"common")==="dualai"&&String(p.stage||"")===item.stage);return found?found.prompt:item.fallback}
function stateDraft(){return localStorage.getItem("workflow-state-draft")||""}
function sectionAfter(text,label){const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");const match=text.match(new RegExp(`${escaped}：?\\s*([\\s\\S]*?)(?=\\n[^\\n：]{2,20}：|$)`));return match?match[1].trim():""}
function parseWorkflowState(text){if(!text.trim())return{ok:false,message:"無法解析，請確認貼上的是 DUAL-AI-STATE.md 全文。"};const current=(text.match(/目前階段：?\s*(.*)/)||[])[1]?.trim()||"";const next=sectionAfter(text,"下一步");const unresolved=sectionAfter(text,"未解決問題");const updated=(text.match(/最後更新時間：?\s*(.*)/)||[])[1]?.trim()||"";const done=sectionAfter(text,"已完成事項").split(/\n/).map(s=>s.trim()).filter(Boolean).slice(-3).join("\n");const stageMatch=current.match(/第\s*([1-5])\s*階段/);const stage=current.includes("已完成")?"5":(stageMatch?stageMatch[1]:"");const ok=!!(current||next||unresolved||updated||done);return{ok,current:current||"尚未判斷",done:done||"尚未解析",next:next||"尚未解析",unresolved:unresolved||"無",updated:updated||"尚未解析",stage,message:ok?"":"無法解析，請確認貼上的是 DUAL-AI-STATE.md 全文。"}}
function stateBoardHtml(){const draft=stateDraft();const parsed=parseWorkflowState(draft);return`<div class="card state-board"><h2>DUAL-AI-STATE 快速看板</h2><div class="summary">把狀態檔全文貼在這裡，控制台只在瀏覽器本機解析與暫存，不上傳、不寫回檔案。</div><textarea id="workflowStateInput" placeholder="貼上 DUAL-AI-STATE.md 全文">${esc(draft)}</textarea>${parsed.ok?`<div class="state-summary"><div class="state-item"><div class="state-label">目前階段</div><div class="state-value">${esc(parsed.current)}</div></div><div class="state-item"><div class="state-label">最後更新時間</div><div class="state-value">${esc(parsed.updated)}</div></div><div class="state-item full"><div class="state-label">上一步做了什麼</div><div class="state-value">${esc(parsed.done)}</div></div><div class="state-item full"><div class="state-label">下一步</div><div class="state-value">${esc(parsed.next)}</div></div><div class="state-item full"><div class="state-label">未解決問題</div><div class="state-value">${esc(parsed.unresolved)}</div></div></div>`:`<div class="warning">${esc(parsed.message)}</div>`}</div>`}
function controlHtml(){const parsed=parseWorkflowState(stateDraft());return`${stateBoardHtml()}<div class="grid">${CONTROL_STAGES.map(item=>{const meta=STAGE_META.dualai[item.stage]||[item.stage,item.purpose];const prompt=controlPrompt(item)||`請進入 dual-ai-workflow ${meta[0]}，依目前專案實際狀態接續。`;const active=parsed.stage&&item.stage===parsed.stage?" state-stage-active":"";return`<div class="card${active}"><h3>${esc(meta[0])} <span class="cat-tag">${esc(item.role)}</span></h3><div class="usage">${esc(item.purpose)}</div><div class="summary">${esc(item.plain)}</div><button class="copy-btn" data-control-stage="${esc(item.stage)}" data-control-query="${esc(item.query||meta[0])}" data-control-copy="${encodeURIComponent(prompt)}">跳到提示詞庫並複製 prompt</button></div>`}).join("")}</div>`}
function bindControl(){document.querySelectorAll("[data-control-stage]").forEach(btn=>btn.onclick=()=>{copyText(decodeURIComponent(btn.dataset.controlCopy),btn);setTimeout(()=>{flowMode="dualai";q=btn.dataset.controlQuery;document.getElementById("searchBox").value=q;setTab("prompts")},260)})}
function bindStateBoard(){const input=document.getElementById("workflowStateInput");if(input)input.oninput=()=>{localStorage.setItem("workflow-state-draft",input.value);render()}}
const PROMPT_CATEGORIES=["專案啟動","開發過程","版本控制","整合串接","上線部署","三方 AI 協作","Skill 管理","安全檢查","三方 AI 工作流","單AI精簡","其他"];
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
function skillDraft(){const data=readDraft();return{name:data.name||"",source:data.source||"",category:data.category||"Skill 管理",categoryOther:data.categoryOther||"",risk:data.risk||"中",summary:data.summary||"",triggers:data.triggers||"",notes:data.notes||"",checked:!!data.checked}}
function captureData(){if(captureMode==="skill")return{name:formVal("skillName"),source:formVal("skillSource"),category:formVal("skillCategory")==="其他"?formVal("skillCategoryOther"):formVal("skillCategory"),categoryOther:formVal("skillCategoryOther"),risk:formVal("skillRisk")||"中",summary:formVal("skillSummary"),triggers:formVal("skillTriggers"),notes:formVal("skillNotes"),checked:formChecked("skillChecked")};return{title:formVal("promptTitle"),category:formVal("promptCategory")==="其他"?formVal("promptCategoryOther"):formVal("promptCategory"),categoryOther:formVal("promptCategoryOther"),usage:formVal("promptUsage"),flow:formVal("promptFlow")||"common",stage:formVal("promptStage"),prompt:formVal("promptText")}}
function promptYaml(d){return`- title: ${d.title||"【標題】"}\n  category: ${d.category||"專案啟動"}\n  usage: ${d.usage||"【用途】"}\n  flow: ${d.flow||"common"}\n  stage: '${yamlScalar(d.stage||"")}'\n  prompt: |-\n${yamlBlock(d.prompt||"【提示詞內容】","    ")}`}
function skillYaml(d){const triggers=(d.triggers||"【觸發句】").split(/\r?\n/).filter(Boolean).map(t=>`  - ${t}`).join("\n");return`- name: ${d.name||"【skill-name】"}\n  category: ${d.category||"Skill 管理"}\n  risk: ${d.risk||"中"}\n  summary: ${d.summary||"【用途摘要】"}\n  triggers:\n${triggers}\n  notes: ${d.notes||"來源："+(d.source||"【來源】")}`}
function codexCapturePrompt(d){const target=captureMode==="skill"?"data/skills.yaml":"data/prompts.yaml";const yaml=captureMode==="skill"?skillYaml(d):promptYaml(d);return`請把下面這筆新內容收錄進控制台。\n\n要求：\n1. 先檢查內容格式與風險。\n2. 寫入 ${target}。\n3. 執行 python3 scripts/build.py 重建 index.html。\n4. 驗證 index.html 搜尋得到新卡片。\n5. 建立本地 git commit，commit message 使用繁體中文。\n6. 不要 push origin/main，等使用者決定。\n\n${captureMode==="skill"?"我已確認先跑過「Skill 安裝前資安檢查」提示詞。\n\n":""}建議 YAML 片段如下：\n\n${yaml}`}
function captureHtml(){const d=captureMode==="skill"?skillDraft():promptDraft();const categoryList=captureMode==="skill"?skillCategories():promptCategories();const category=d.categoryOther?"其他":d.category;const otherStyle=category==="其他"?"":"display:none";const yaml=captureMode==="skill"?skillYaml(d):promptYaml(d);const codex=codexCapturePrompt(d);const disabled=captureMode==="skill"&&!d.checked;return`<div class="sop"><div class="card"><div class="capture-switch"><button class="capture-btn ${captureMode==="prompt"?"active":""}" data-capture-mode="prompt">提示詞</button><button class="capture-btn ${captureMode==="skill"?"active":""}" data-capture-mode="skill">Skill</button></div><div class="summary">不知道怎麼填也沒關係，先貼原文。新手建議複製「給 Codex 的完整交辦提示詞」，讓 Codex 幫你寫入、重建、驗證與 commit。</div></div><div class="card"><h2>${captureMode==="skill"?"Skill 收錄表單":"提示詞收錄表單"}</h2>${captureMode==="skill"?skillForm(d,categoryList,category,otherStyle):promptForm(d,categoryList,category,otherStyle)}</div><div class="card"><h2>推薦複製：給 Codex 的完整交辦提示詞</h2>${disabled?`<div class="warning">請先勾選「我已對 skill 跑過 Skill 安裝前資安檢查」才可複製交辦提示詞。</div>`:""}<pre class="prompt-body" id="captureCodex">${esc(codex)}</pre><button class="copy-btn" ${disabled?"disabled":""} data-copy="${encodeURIComponent(codex)}">複製交辦提示詞</button></div><div class="card"><h2>進階檢查：YAML 片段</h2><div class="summary">這是給懂格式的人檢查用；不懂 YAML 也沒關係，複製上一段給 Codex 即可。</div>${disabled?`<div class="warning">尚未安檢，不建議收錄或安裝。</div>`:""}<pre class="prompt-body" id="captureYaml">${esc(yaml)}</pre><button class="copy-btn" data-copy="${encodeURIComponent(yaml)}">複製 YAML</button></div></div>`}
function promptForm(d,cats,category,otherStyle){return`<div class="form-grid"><div class="field"><label>標題</label><input id="promptTitle" data-capture-input value="${esc(d.title)}"><div class="help">這張卡片在控制台上顯示的名字。</div></div><div class="field"><label>分類</label><select id="promptCategory" data-capture-input>${optionsHtml(cats,category)}</select><input id="promptCategoryOther" data-capture-input style="${otherStyle}" value="${esc(d.categoryOther)}" placeholder="輸入其他分類"><div class="help">分類是之後搜尋和整理用的。</div></div><div class="field"><label>用途</label><input id="promptUsage" data-capture-input value="${esc(d.usage)}"><div class="help">什麼時候會用到它。</div></div><div class="field"><label>適用流程</label><select id="promptFlow" data-capture-input>${optionsHtml(["common","dualai","solo"],d.flow)}</select><div class="help">不確定就選 common。</div></div><div class="field"><label>階段</label><input id="promptStage" data-capture-input value="${esc(d.stage)}" placeholder="entry / 1 / 2 / 3 / 4 / 5 / archive"><div class="help">沒有階段就留空。</div></div><div class="field full"><label>提示詞原文</label><textarea id="promptText" data-capture-input>${esc(d.prompt)}</textarea><div class="help">貼上你想收錄的完整提示詞。</div></div></div>`}
function skillForm(d,cats,category,otherStyle){return`<div class="form-grid"><div class="field full"><label class="checkline"><input type="checkbox" id="skillChecked" data-capture-input ${d.checked?"checked":""}>我已對 skill 跑過「Skill 安裝前資安檢查」提示詞。</label><div class="help">陌生來源一定先安檢；未勾選時不會啟用 Codex 交辦提示詞。</div></div><div class="field"><label>Skill 名稱</label><input id="skillName" data-capture-input value="${esc(d.name)}"></div><div class="field"><label>來源</label><input id="skillSource" data-capture-input value="${esc(d.source)}" placeholder="GitHub URL 或資料夾路徑"></div><div class="field"><label>分類</label><select id="skillCategory" data-capture-input>${optionsHtml(cats,category)}</select><input id="skillCategoryOther" data-capture-input style="${otherStyle}" value="${esc(d.categoryOther)}" placeholder="輸入其他分類"></div><div class="field"><label>風險等級</label><select id="skillRisk" data-capture-input>${optionsHtml(["低","中","高"],d.risk)}</select><div class="help">預設中；確認安全後再改低。</div></div><div class="field full"><label>用途摘要</label><textarea id="skillSummary" data-capture-input>${esc(d.summary)}</textarea></div><div class="field full"><label>觸發句</label><textarea id="skillTriggers" data-capture-input placeholder="每行一句觸發句">${esc(d.triggers)}</textarea></div><div class="field full"><label>注意事項</label><textarea id="skillNotes" data-capture-input>${esc(d.notes)}</textarea></div></div>`}
function updateCaptureOutputs(){const data=captureData();const yaml=captureMode==="skill"?skillYaml(data):promptYaml(data);const codex=codexCapturePrompt(data);const yamlPre=document.getElementById("captureYaml"),codexPre=document.getElementById("captureCodex");if(yamlPre)yamlPre.textContent=yaml;if(codexPre)codexPre.textContent=codex;const buttons=document.querySelectorAll(".card .copy-btn");if(buttons.length>1){buttons[buttons.length-2].dataset.copy=encodeURIComponent(codex);buttons[buttons.length-1].dataset.copy=encodeURIComponent(yaml)}}
function bindCapture(){document.querySelectorAll("[data-capture-mode]").forEach(btn=>btn.onclick=()=>{captureMode=btn.dataset.captureMode;render()});document.querySelectorAll("[data-capture-input]").forEach(el=>el.oninput=el.onchange=()=>{const data=captureData();writeDraft(data);if(["skillChecked","skillCategory","promptCategory"].includes(el.id))render();else updateCaptureOutputs()})}
const SOP_HTML=`<div class="sop"><div class="card"><h2>Skill 安裝前安檢</h2><ol><li>確認來源 repo 是否可信。</li><li>檢查是否讀取 API key、SSH key 或執行危險 shell 指令。</li><li>檢查是否要求 AI 忽略原本規則或外傳資料。</li></ol></div><div class="card"><h2>安檢提示詞</h2><pre class="prompt-body" id="sopPrompt"></pre><button class="copy-btn" id="sopCopy">複製</button></div></div>`;
function render(){const chips=document.getElementById("chips"),content=document.getElementById("content"),countLine=document.getElementById("countLine");renderIntro();chips.innerHTML=cats().map(c=>`<button class="chip ${c===cat?"active":""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");chips.querySelectorAll(".chip").forEach(ch=>ch.onclick=()=>{cat=ch.dataset.cat;if(tab==="prompts"&&cat!=="全部")flowMode="common";render()});if(tab==="backup"){countLine.textContent="";content.innerHTML=backupHtml();return}if(tab==="workflow"){countLine.textContent="";content.innerHTML=WORKFLOW_HTML;return}if(tab==="guide"){countLine.textContent="";content.innerHTML=GUIDE_HTML;return}if(tab==="capture"){countLine.textContent="";content.innerHTML=captureHtml();bindCapture();return}if(tab==="control"){countLine.textContent="";content.innerHTML=controlHtml();bindControl();bindStateBoard();return}if(tab==="sop"){countLine.textContent="";content.innerHTML=SOP_HTML;const sp=DATA.prompts.find(p=>p.category==="安全檢查"||p.title.includes("安裝前資安檢查"));if(sp){document.getElementById("sopPrompt").textContent=sp.prompt;document.getElementById("sopCopy").dataset.copy=encodeURIComponent(sp.prompt)}return}if(tab==="skills"){const items=DATA.skills.filter(s=>(cat==="全部"||s.category===cat)&&match(s,["name","summary","category","triggers","notes"]));countLine.textContent=`共 ${items.length} 個 skill`;content.innerHTML=items.length?`<div class="grid">${items.map(skillCard).join("")}</div>`:`<div class="empty">找不到符合條件的 skill。</div>`;return}if(tab==="prompts"){const count=DATA.prompts.filter(p=>(p.flow||"common")===flowMode&&(cat==="全部"||p.category===cat)&&match(p,["title","usage","category","prompt","flow","stage"])).length;countLine.textContent=`目前顯示 ${count} 則提示詞，總共 ${DATA.prompts.length} 則`;content.innerHTML=renderPromptFlow();content.querySelectorAll(".flow-btn").forEach(btn=>btn.onclick=()=>{flowMode=btn.dataset.flow;cat="全部";render()})}}
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
)
out.write_text(html_out, encoding="utf-8")
print(f"OK: {out} built with {len(skills)} skills / {len(prompts)} prompts / {len(combos)} combos")
