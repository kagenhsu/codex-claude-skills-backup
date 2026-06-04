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

data_json = json.dumps({"skills": skills, "prompts": prompts}, ensure_ascii=False).replace("</", "<\\/")


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
  .empty{color:var(--muted); text-align:center; padding:36px 0;}
  footer{text-align:center; color:var(--muted); font-size:.75rem; padding:20px;}
  @media (max-width:760px){main,header{padding-left:14px; padding-right:14px;} .grid,.intro-grid,.workflow-guide{grid-template-columns:1fr;} .section-head{display:block;} }
</style>
</head>
<body>
<header><div class="head-inner"><h1>Skill 助手控制台 <span class="sub">Codex / Claude Code / Claude Desktop 導覽版</span></h1><div class="tabs"><button class="tab active" data-tab="backup">換電腦／同步</button><button class="tab" data-tab="skills">Skills</button><button class="tab" data-tab="prompts">提示詞庫</button><button class="tab" data-tab="workflow">三方 AI 工作流</button><button class="tab" data-tab="guide">AI 角色導覽</button><button class="tab" data-tab="sop">安檢 SOP</button></div></div></header>
<main><div class="search"><span class="icon">搜</span><input id="searchBox" type="text" placeholder="搜尋 skill、提示詞、觸發句，例如：git、翻譯、審查、三 AI"></div><div id="pageIntro" class="page-intro"></div><div id="chips" class="chips"></div><div id="countLine" class="count"></div><div id="content"></div></main>
<footer>資料來源：data/skills.yaml + data/prompts.yaml；修改後執行 python scripts/build.py 重建</footer>
<script>
const DATA = __DATA_JSON__;
const WORKFLOW_HTML = __WORKFLOW_HTML__;
const GUIDE_HTML = __GUIDE_HTML__;
let tab = "backup", cat = "全部", q = "", flowMode = "dualai";
const FLOW_META = {
  dualai:{label:"三方 AI 協作",title:"三方 AI 工作流提示詞",lead:"適合重要系統修改：Codex 是主力工程師，負責規劃、分段實作、測試與修正；Claude Code（VS Code）是審查員，負責架構審查、風險檢查與複審；Claude Desktop 是顧問／文字助理，負責需求、文件與提示詞。"},
  solo:{label:"單一 AI 使用",title:"單一 AI 使用提示詞",lead:"同事只有單一 AI 時，也能用這些提示詞讓 AI 先釐清、再分段執行、最後提醒是否需要審查。"},
  common:{label:"通用",title:"通用提示詞",lead:"日常可直接複製使用的提示詞，例如 Skill 安檢、交接、摘要與一般 AI 工作輔助。"}
};
const STAGE_META = {
  dualai:{entry:["入口","啟動或接續三方 AI 工作流"],"1":["第 1 階段：Codex","規劃、拆任務、建立狀態檔"],"2":["第 2 階段：Codex","分段實作、build、驗證"],"3":["第 3 階段：Claude Code（VS Code）","審查 diff、架構與風險"],"4":["第 4 階段：Codex","逐條修正、重新驗證"],"5":["第 5 階段：Claude Code（VS Code）","複審並確認可收尾"],handoff:["轉交","把目前狀態交給下一方"],status:["狀態檔","讀寫 DUAL-AI-STATE.md"]},
  solo:{entry:["入口","只用一個 AI 時先用這張說明工作方式"],"1":["第 1 步","釐清任務與目標"],"2":["第 2 步","提出方案、先不修改"],"3":["第 3 步","分段執行並自我檢查"],"4":["第 4 步","收尾、整理驗證與 commit 建議"]}
};
const FLOW_ORDER = {dualai:["entry","1","2","3","4","5","handoff","status"],solo:["entry","1","2","3","4"]};
const PAGE_INTROS = {
  backup:{title:"換電腦／同步",lead:"這頁只在換電腦、重裝工具，或要把已整理好的 skills 同步到另一台機器時使用。平常找功能請看 Skills；要複製工作指令請看提示詞庫。",purpose:"把這個專案保存的 skills 備份包，安裝到 Codex 或 Claude Code 可讀的位置。",first:"如果不是換電腦或重裝，通常不用按這頁的還原指令。",when:"換電腦、重裝工具、同步 Mac mini 或 VS Code Claude Code 時使用。"},
  skills:{title:"Skills",lead:"查看每個 skill 的用途、風險與觸發句，直接複製給 AI 使用。",purpose:"快速判斷要叫哪個 AI skill。",first:"搜尋關鍵字，再複製觸發句。",when:"不確定某個任務該用哪個 skill 時。"},
  prompts:{title:"提示詞庫",lead:"常用提示詞集中管理，適合你直接複製給 Codex、Claude Code（VS Code）或 Claude Desktop。",purpose:"快速啟動工作流程。",first:"先選三方 AI、單一 AI 或通用分類，再複製。",when:"要交辦任務、請 AI 審查、整理交接或產出文件時。"},
  workflow:{title:"三方 AI 工作流",lead:"說明 Codex、Claude Code（VS Code）、Claude Desktop 的協作流程：Codex 做主力工程，Claude Code 做審查複審，Claude Desktop 做需求與文字輔助。",purpose:"讓三方各做各的，避免同時亂改或角色混淆。",first:"先讀 DUAL-AI-STATE.md，再接續目前階段。",when:"做網站、系統、腳本、多裝置同步或 git 存檔時。"},
  guide:{title:"AI 角色導覽",lead:"這頁幫新手判斷 Codex、Claude Code（VS Code）、Claude Desktop 各自適合做什麼。",purpose:"快速判斷誰負責規劃、實作、審查、文件或提示詞。",first:"先看角色表，再到提示詞庫複製對應模板。",when:"不確定要叫哪個 AI 處理，或同事只有單一 AI 可用時。"},
  sop:{title:"安檢 SOP",lead:"安裝或使用外部 skill 前，先檢查是否有高風險指令與敏感權限。",purpose:"降低誤裝危險 skill 的風險。",first:"先複製安檢提示詞給 AI。",when:"安裝陌生 skill、看到 danger 或會操作帳號/API 時。"}
};
const riskCls = {"低":"low","中":"mid","高":"high"};
const esc = s => (s ?? "").toString().replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
function copyText(text, btn){const done=()=>{btn.textContent="已複製";btn.classList.add("done");setTimeout(()=>{btn.textContent="複製";btn.classList.remove("done");},1400)};if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done).catch(fallback)}else fallback();function fallback(){const ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);ta.select();document.execCommand("copy");document.body.removeChild(ta);done()}}
document.addEventListener("click",e=>{const b=e.target.closest("[data-copy]");if(b)copyText(decodeURIComponent(b.dataset.copy),b)});
function match(obj,fields){if(!q)return true;const hay=fields.map(f=>Array.isArray(obj[f])?obj[f].join(" "):(obj[f]||"")).join(" ").toLowerCase();return hay.includes(q.toLowerCase())}
function cats(){if(tab==="skills")return["全部",...new Set(DATA.skills.map(s=>s.category))];return[]}
function renderIntro(){const info=PAGE_INTROS[tab];document.getElementById("pageIntro").innerHTML=`<h2>${esc(info.title)}</h2><div class="lead">${esc(info.lead)}</div><div class="intro-grid"><div class="intro-item"><div class="intro-label">用途</div><div class="intro-text">${esc(info.purpose)}</div></div><div class="intro-item"><div class="intro-label">先做</div><div class="intro-text">${esc(info.first)}</div></div><div class="intro-item"><div class="intro-label">適合情境</div><div class="intro-text">${esc(info.when)}</div></div></div>`}
function skillCard(s){const triggers=(s.triggers||[]).map(t=>`<div class="trigger"><code>${esc(t)}</code><button class="copy-btn" data-copy="${encodeURIComponent(t)}">複製</button></div>`).join("");return`<div class="card"><h3>${esc(s.name)} <span class="badge ${riskCls[s.risk]||"low"}">${esc(s.risk)}風險</span> <span class="cat-tag">${esc(s.category)}</span></h3><div class="summary">${esc(s.summary)}</div>${s.notes?`<div class="notes">${esc(s.notes)}</div>`:""}${triggers}</div>`}
function stageLabel(p){if(!p.flow||!p.stage)return"通用";const meta=STAGE_META[p.flow]?.[p.stage];return meta?meta[0]:p.stage}
function promptCard(p){return`<div class="card"><h3>${esc(p.title)} <span class="stage-tag">${esc(stageLabel(p))}</span> <span class="cat-tag">${esc(p.category)}</span></h3><div class="usage">${esc(p.usage)}</div><pre class="prompt-body">${esc(p.prompt)}</pre><button class="copy-btn" data-copy="${encodeURIComponent(p.prompt)}">複製</button></div>`}
function workflowGuide(){if(flowMode==="dualai")return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">Codex</div><div class="guide-text">主力工程師：規劃、分段實作、測試、修正。</div></div><div class="guide-item"><div class="guide-label">Claude Code（VS Code）</div><div class="guide-text">審查員：看 diff、抓風險、提出 P0/P1/P2 問題。</div></div><div class="guide-item"><div class="guide-label">Claude Desktop</div><div class="guide-text">顧問／文字助理：整理需求、提示詞、主管版說明。</div></div></div>`;if(flowMode==="solo")return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">先規劃</div><div class="guide-text">讓單一 AI 先讀文件並列出做法。</div></div><div class="guide-item"><div class="guide-label">再實作</div><div class="guide-text">只做最小必要修改，避免一次改太大。</div></div><div class="guide-item"><div class="guide-label">要自檢</div><div class="guide-text">請 AI 用審查角度檢查結果。</div></div></div>`;return`<div class="workflow-guide"><div class="guide-item"><div class="guide-label">專案啟動</div><div class="guide-text">AGENTS、PRD、交接摘要與規劃模板。</div></div><div class="guide-item"><div class="guide-label">工程常用</div><div class="guide-text">Git、API、部署與資料庫模板。</div></div><div class="guide-item"><div class="guide-label">Skill 管理</div><div class="guide-text">新增 skill、資安檢查與提示詞收錄。</div></div></div>`}
function flowButtons(){return`<div class="flow-switch">${Object.entries(FLOW_META).map(([key,m])=>`<button class="flow-btn ${flowMode===key?"active":""}" data-flow="${key}">${m.label}</button>`).join("")}</div>`}
function renderPromptFlow(){const meta=FLOW_META[flowMode];const visible=DATA.prompts.filter(p=>(p.flow||"common")===flowMode&&match(p,["title","usage","category","prompt","flow","stage"]));let html=`<div class="page-intro"><h2>${esc(meta.title)}</h2><div class="lead">${esc(meta.lead)}</div>${workflowGuide()}</div>${flowButtons()}`;if(flowMode==="common"){const groups=[...new Set(visible.map(p=>p.category))];html+=groups.map(group=>{const items=visible.filter(p=>p.category===group);return`<section class="flow-section"><div class="section-head"><h2>${esc(group)}</h2><span class="hint">${items.length} 則</span></div><div class="grid">${items.map(promptCard).join("")}</div></section>`}).join("")}else{html+=FLOW_ORDER[flowMode].map(stage=>{const items=visible.filter(p=>String(p.stage||"")===stage);if(!items.length)return"";const[label,hint]=STAGE_META[flowMode][stage]||[stage,""];return`<section class="flow-section"><div class="section-head"><h2>${esc(label)}</h2><span class="hint">${esc(hint)}，${items.length} 則</span></div><div class="grid">${items.map(promptCard).join("")}</div></section>`}).join("")}return html||`<div class="empty">找不到符合條件的提示詞。</div>`}
function cmdRow(label,cmd){return`<div class="trigger"><div style="flex:1"><div class="usage">${esc(label)}</div><code>${esc(cmd)}</code></div><button class="copy-btn" data-copy="${encodeURIComponent(cmd)}">複製</button></div>`}
function backupHtml(){return`<div class="sop"><div class="card"><h2>這頁是做什麼</h2><div class="summary">簡單說：這頁不是日常功能頁，而是「搬家工具」。當你換電腦、重裝 Codex / Claude Code，或要把同一套 skills 放到另一台機器時才用。</div><ul><li><b>codex-skills-backup.tar.gz</b>：已整理好的 skills 備份包</li><li><b>restore-skills.sh</b>：把備份包安裝到 Codex / Claude Code 的 skills 目錄</li><li><b>平常找功能</b>：請切到 Skills 或提示詞庫，不用執行這裡的指令</li></ul></div><div class="card"><h2>同步到新環境的指令</h2>${cmdRow("只有換電腦／重裝時才執行","./restore-skills.sh")}</div></div>`}
const SOP_HTML=`<div class="sop"><div class="card"><h2>Skill 安裝前安檢</h2><ol><li>確認來源 repo 是否可信。</li><li>檢查是否讀取 API key、SSH key 或執行危險 shell 指令。</li><li>檢查是否要求 AI 忽略原本規則或外傳資料。</li></ol></div><div class="card"><h2>安檢提示詞</h2><pre class="prompt-body" id="sopPrompt"></pre><button class="copy-btn" id="sopCopy">複製</button></div></div>`;
function render(){const chips=document.getElementById("chips"),content=document.getElementById("content"),countLine=document.getElementById("countLine");renderIntro();chips.innerHTML=cats().map(c=>`<button class="chip ${c===cat?"active":""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");chips.querySelectorAll(".chip").forEach(ch=>ch.onclick=()=>{cat=ch.dataset.cat;render()});if(tab==="backup"){countLine.textContent="";content.innerHTML=backupHtml();return}if(tab==="workflow"){countLine.textContent="";content.innerHTML=WORKFLOW_HTML;return}if(tab==="guide"){countLine.textContent="";content.innerHTML=GUIDE_HTML;return}if(tab==="sop"){countLine.textContent="";content.innerHTML=SOP_HTML;const sp=DATA.prompts.find(p=>p.category==="安全檢查"||p.title.includes("安裝前資安檢查"));if(sp){document.getElementById("sopPrompt").textContent=sp.prompt;document.getElementById("sopCopy").dataset.copy=encodeURIComponent(sp.prompt)}return}if(tab==="skills"){const items=DATA.skills.filter(s=>(cat==="全部"||s.category===cat)&&match(s,["name","summary","category","triggers","notes"]));countLine.textContent=`共 ${items.length} 個 skill`;content.innerHTML=items.length?`<div class="grid">${items.map(skillCard).join("")}</div>`:`<div class="empty">找不到符合條件的 skill。</div>`;return}if(tab==="prompts"){const count=DATA.prompts.filter(p=>(p.flow||"common")===flowMode&&match(p,["title","usage","category","prompt","flow","stage"])).length;countLine.textContent=`目前顯示 ${count} 則提示詞，總共 ${DATA.prompts.length} 則`;content.innerHTML=renderPromptFlow();content.querySelectorAll(".flow-btn").forEach(btn=>btn.onclick=()=>{flowMode=btn.dataset.flow;render()})}}
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));t.classList.add("active");tab=t.dataset.tab;cat="全部";render()});document.getElementById("searchBox").addEventListener("input",e=>{q=e.target.value.trim();render()});render();
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
print(f"OK: {out} built with {len(skills)} skills / {len(prompts)} prompts")
