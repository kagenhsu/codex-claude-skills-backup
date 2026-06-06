# Daily Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a beginner-friendly `日常提示詞` page to the static console.

**Architecture:** Keep the first version static inside `scripts/build.py`, matching the existing `homeHtml()` pattern. Rebuild `index.html` from the generator and avoid changing YAML schemas.

**Tech Stack:** Python static HTML generator, vanilla HTML/CSS/JavaScript, local `index.html`.

---

### Task 1: Add Page Entry And Intro

**Files:**
- Modify: `scripts/build.py`

- [ ] **Step 1: Add header tab**

Add a `日常提示詞` tab after `首頁 / 快速開始`:

```html
<button class="tab" data-tab="daily">日常提示詞</button>
```

- [ ] **Step 2: Add page intro**

Add `PAGE_INTROS.daily` with title, lead, purpose, first action, and suitable scenario text.

- [ ] **Step 3: Add homepage jump**

Add one homepage button:

```html
<button class="copy-btn" type="button" data-home-tab="daily">我要日常提示詞</button>
```

### Task 2: Add Daily Prompt Cards

**Files:**
- Modify: `scripts/build.py`

- [ ] **Step 1: Add static data**

Create `DAILY_PROMPT_SECTIONS` in the inline script with four sections:

```js
const DAILY_PROMPT_SECTIONS = [
  {title:"開發系統", cards:[...]},
  {title:"找資料 / 做比對", cards:[...]},
  {title:"整理資料", cards:[...]},
  {title:"整理電腦檔案", cards:[...]}
];
```

- [ ] **Step 2: Add rendering helpers**

Create `dailyPromptCard(card)` and `dailyHtml()`.

- [ ] **Step 3: Ensure file safety prompts**

The `整理電腦檔案` prompts must include:

```text
不要刪除、不要搬移、不要改名。請先列出整理計畫與受影響檔案，等我確認後再產生下一步指令。
```

### Task 3: Wire Render And Styles

**Files:**
- Modify: `scripts/build.py`
- Generate: `index.html`

- [ ] **Step 1: Add CSS**

Add daily page classes for hero, section, card, and safety note.

- [ ] **Step 2: Add render branch**

Add:

```js
if(tab==="daily"){countLine.textContent="";content.innerHTML=dailyHtml();return}
```

- [ ] **Step 3: Rebuild**

Run:

```bash
python3 scripts/build.py
```

Expected output:

```text
OK: .../index.html built with 45 skills / 40 prompts / 3 combos
```

### Task 4: Verify

**Files:**
- Read: `index.html`

- [ ] **Step 1: Check generated content**

Run:

```bash
rg -n "日常提示詞|整理電腦檔案|不要刪除|data-tab=\"daily\"" index.html scripts/build.py
```

- [ ] **Step 2: Check inline JS syntax**

Extract the inline script and run:

```bash
node --check /tmp/codex-console-inline.js
```

- [ ] **Step 3: Confirm no schema count changed**

Confirm build output still reports `45 skills / 40 prompts / 3 combos`.
