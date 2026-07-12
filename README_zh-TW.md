<h1 align="center">web-perf-audit</h1>

<p align="center">
  <a href="README.md">English</a>&nbsp;·&nbsp;
  <a href="README_zh-CN.md">简体中文</a>&nbsp;·&nbsp;
  📖 <b>繁體中文</b>&nbsp;·&nbsp;
  <a href="README_ja.md">日本語</a>&nbsp;·&nbsp;
  <a href="README_ko.md">한국어</a>&nbsp;·&nbsp;
  <a href="README_es.md">Español</a>&nbsp;·&nbsp;
  <a href="README_tr.md">Türkçe</a>&nbsp;·&nbsp;
  <a href="README_ru.md">Русский</a>
</p>

<p align="center">
  <strong>不只跑分 — 直接給你可直接執行的優化方案。</strong><br>
  Multi-Agent Web Performance Audit Pipeline — SCAN → ANALYZE → SCORE → REPORT.<br>
  Not another Lighthouse wrapper. A complete audit-to-fix workflow with CWV impact estimates.<br>
  Works with <strong>Claude Code, Cursor, VSCode Copilot,</strong> and any CI pipeline.
</p>

<p align="center">
  <img src="docs/pipeline.png" alt="web-perf-audit pipeline: SCAN → ANALYZE → SCORE → REPORT" width="800">
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/logo-dark.svg">
    <img alt="web-perf-audit" src="docs/logo.svg" width="520">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/EVEDensity/web-perf-audit/stargazers">
    <img src="https://img.shields.io/github/stars/EVEDensity/web-perf-audit?style=for-the-badge&logo=github&labelColor=1e293b&color=f5c842" alt="Stars">
  </a>
  <a href="https://github.com/EVEDensity/web-perf-audit/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/LICENSE-MIT-3b82f6?style=for-the-badge&logo=open-source-initiative&logoColor=white&labelColor=1e293b" alt="License">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/PYTHON-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=1e293b" alt="Python">
  </a>
  <a href="https://nodejs.org/">
    <img src="https://img.shields.io/badge/NODE.JS-18+-339933?style=for-the-badge&logo=nodedotjs&logoColor=white&labelColor=1e293b" alt="Node.js">
  </a>
  <a href="https://claude.ai/code">
    <img src="https://img.shields.io/badge/CLAUDE_CODE-skill-d97706?style=for-the-badge&logo=anthropic&logoColor=white&labelColor=1e293b" alt="Claude Code">
  </a>
  <br>
  <a href="https://github.com/EVEDensity/web-perf-audit/actions">
    <img src="https://img.shields.io/badge/BUILD-passing-22c55e?style=for-the-badge&logo=githubactions&logoColor=white&labelColor=1e293b" alt="Build">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/IDE-Cursor_|_Copilot_|_VSCode-8b5cf6?style=for-the-badge&logo=visualstudiocode&logoColor=white&labelColor=1e293b" alt="IDE">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/STANDARD-web.dev-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white&labelColor=1e293b" alt="web.dev">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/PLATFORM-win_|_mac_|_linux-6b7280?style=for-the-badge&logo=linux&logoColor=white&labelColor=1e293b" alt="Platform">
  </a>
</p>

<p align="center">
  <code>npx web-perf-audit --url https://example.com --audience dev</code>
</p>

---

## 為什麼需要 web-perf-audit

你跑了 Lighthouse。LCP 4.2s，得分 62。你盯著螢幕。然後呢？

市面上的工具都在告訴你「哪裡不好」。沒有一個告訴你「改哪一行、怎麼改、為什麼會見效」。web-perf-audit 填補了這個空缺——

- **SCAN**：Lighthouse + Puppeteer 採集原始 CWV 資料
- **ANALYZE**：5 個 Agent 並行掃描（關鍵路徑、資源預載入、圖片、字型、JS 冗餘）
- **SCORE**：按 CWV 影響面加權打分，P0/P1/P2 優先級排序
- **REPORT**：生成附帶複製貼上程式碼的修復方案，每條建議都鏈回 web.dev 原理

> *"目標不是 Lighthouse 100 分——是真實使用者的頁面飛快載入、互動即時回應。"*

---

## ✨ 核心能力

| 能力 | 說明 |
|------|------|
| 🎯 **web.dev 標準對齊** | 所有檢測規則基於 [web.dev/learn/performance](https://web.dev/learn/performance)。LCP ≤2.5s、INP ≤200ms、CLS ≤0.1，p75 分位。 |
| 🤖 **多 Agent 並行審計** | 5 個專職 Agent：工程掃描 → 資源解析 → 指標打分 → 變更預測 → 修復方案生成。各司其職，並行執行。 |
| 🔧 **確定性 + 實測混合** | 靜態檢測（缺 `defer`、`font-display` 錯誤、無 `srcset`）每次結果一致；執行時指標（LCP、TBT）透過 Lighthouse 實際瀏覽器測量。 |
| 📊 **離線視覺化面板** | Chart.js 互動式儀表板。評分圓環、CWV 指標卡、分類長條圖、優先級問題清單。審計完成後無需聯網。 |
| 🔁 **Git 感知增量審計** | SHA256 指紋快取，頁面無變化則跳過全流程。`perf-diff` 對比兩個分支的審計結果，合併前發現效能回歸。 |
| 🧩 **跨平台 & 多 IDE 適配** | macOS / Linux / Windows 全平台支援。Claude Code 原生 Skill，Cursor rules，VSCode Copilot 指令。GitHub Actions 一行整合。 |

---

## 🏗 架構

### 多 Agent 審計流水線

```
使用者觸發 /perf analyze <URL>
         │
         ├─ Stage 1: SCAN
         │   ├─ 工程掃描 Agent (框架檢測、建構產物發現、.webperfignore 過濾)
         │   └─ Lighthouse + Puppeteer (LCP/CLS/INP/TBT/FCP 原始資料)
         │
         ├─ Stage 2: ANALYZE (5 Agent 並行)
         │   ├─ 關鍵路徑 Agent (渲染阻塞、請求鏈深度、DOM 大小)
         │   ├─ Resource Hints Agent (preload/prefetch/preconnect 品質)
         │   ├─ 圖片審計 Agent (格式/sizes/懶載入/LCP 候選圖片)
         │   ├─ 字型審計 Agent (font-display/woff2/子集化/預載入)
         │   └─ JS 審計 Agent (Coverage 資料、長任務、第三方腳本)
         │
         ├─ Stage 3: SCORE
         │   └─ 指標打分 Agent (CWV 影響面加權 × 嚴重度係數 → P0/P1/P2)
         │
         └─ Stage 4: REPORT
             └─ 優化方案 Agent (匹配修復模板、生成 before/after 程式碼)
                    ↓
             audit-report.json / report.md / dashboard.html
```

### 分層設計

| 層 | 職責 | 技術棧 |
|----|------|--------|
| **觸發層** | CLI / CI / IDE 呼叫入口 | Claude Code Skill、GitHub Actions、Cursor rules |
| **採集層** | 原始資料 + 專案結構發現 | Lighthouse CLI、Puppeteer、PageSpeed Insights API |
| **分析層** | 5 維度靜態 + 執行時分析 | Python 3.8+ (HTMLParser)、Node.js (Puppeteer) |
| **打分引擎** | CWV 加權優先級計算 | Python 評分引擎 (7 分類 × 嚴重度乘數) |
| **輸出層** | 報告渲染 + 修復模板 | Python (Markdown/JSON)、Chart.js (儀表板) |
| **增量層** | 指紋快取 + 跨分支對比 | SHA256 指紋、JSON 結構對比 |

---

## 🚀 快速開始

```bash
# 1. 克隆倉庫
git clone https://github.com/EVEDensity/web-perf-audit.git && cd web-perf-audit

# 2. 安裝依賴
npm install -g lighthouse && npm install

# 3. 執行審計
python scripts/fetch_metrics.py "https://example.com" --output-dir .web-perf
# ... (5 個分析器並行執行) ...
python scripts/score_and_report.py "https://example.com" --output-dir .web-perf --format all

# 4. 開啟儀表板
open .web-perf/dashboard.html   # macOS
start .web-perf/dashboard.html  # Windows
```

### Claude Code 一鍵安裝

```
/plugin install web-perf-audit@EVEDensity/web-perf-audit
/perf analyze https://example.com
```

---

## 📦 安裝指南

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.sh | bash
```

### Windows PowerShell

```powershell
iwr -Uri https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.ps1 -OutFile install.ps1; ./install.ps1
```

### 前置依賴

| 依賴 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.8 | 所有分析 + 打分腳本 |
| Node.js | ≥ 18 | Lighthouse CLI + Puppeteer |
| Lighthouse | latest | CWV 指標採集 |
| Puppeteer | ^22.0.0 | JS Coverage + Long Task API |

---

## 📖 CLI 命令參考

| 命令 | 說明 | 示例 |
|------|------|------|
| `/perf analyze` | 全流程審計 | `python scripts/fetch_metrics.py <URL> --output-dir .web-perf` |
| `/perf dashboard` | 開啟視覺化面板 | `open .web-perf/dashboard.html` |
| `/perf diff` | Git 變更效能對比 | `python scripts/diff_report.py before.json after.json` |
| `/perf resource` | 靜態資源批量審計 | `python scripts/audit_images.py <URL> -o images.json` |
| `/perf explain` | 單維度深度分析 | `python scripts/analyze_critical_path.py metrics.json` |
| `/perf chat` | 對話式效能諮詢 | Claude Code 原生對話 |

---

## 💼 實戰案例

### 本地專案審計

```bash
npm run dev &
python scripts/fetch_metrics.py "http://localhost:5173" --output-dir .web-perf
python scripts/score_and_report.py "http://localhost:5173" --output-dir .web-perf --format all
```

### CI 效能門禁

```yaml
- name: Performance Gate
  run: |
    python scripts/score_and_report.py "$STAGING_URL" --output-dir .web-perf --format json
    SCORE=$(python -c "import json; print(json.load(open('.web-perf/audit-report.json'))['overallScore']['overallScore'])")
    if [ "$SCORE" -lt 70 ]; then exit 1; fi
```

### 接入 AgentHub

web-perf-audit 是 [AgentHub](https://github.com/EVEDensity/AgentHub) 的一等公民插件，開箱即用。

---

## ❓ 常見問題

<details>
<summary><strong>和直接跑 Lighthouse 有什麼區別？</strong></summary>

Lighthouse 給分數和審計列表。我們在此基礎上額外做了 5 個維度的深度分析（Hints 品質評分、@font-face 解析、JS Coverage 實測、第三方歸因、DOM 深度），按 CWV 影響面排序優先級，生成可複製的修復程式碼，支援增量對比，每個建議都鏈回 web.dev 原理文件。
</details>

<details>
<summary><strong>每次審計要多久？</strong></summary>

典型頁面 30-90 秒。Lighthouse 15-40s（取決於頁面複雜度），5 個並行分析器 10-30s，打分秒級完成。
</details>

<details>
<summary><strong>支援 SPA 嗎？</strong></summary>

是的。Puppeteer 端等待 `networkidle2` 後才採集 Coverage 資料，動態載入的 chunk 不會漏。建議 SPA 用 `--strategy desktop`。
</details>

<details>
<summary><strong>內網站點能用嗎？</strong></summary>

可以。`localhost` 和內部 IP 均支援，自簽憑證加 `--extra-lighthouse-flags "--chrome-flags='--ignore-certificate-errors'"`。
</details>

<details>
<summary><strong>團隊怎麼共享審計結果？</strong></summary>

儀表板 HTML 是純靜態檔案，丟到任何靜態託管即可。或是上傳 CI artifact，隊員下載本地開啟。
</details>

---

## 🤝 參與貢獻

- **新增審計規則**：在 `references/` 添加 md，遵循「問題→檢測→修復→收益」模板
- **新增 Agent**：在 `scripts/` 創建腳本（Python/Node.js），輸出 JSON，註冊到 `score_and_report.py`
- **儀表板改進**：編輯 `templates/dashboard.html`，用示例 JSON 測試
- **Bug 回饋**：提 Issue 時附上 `audit-report.json` 和測試 URL

### 關聯倉庫

| 專案 | 說明 |
|------|------|
| [AgentHub](https://github.com/EVEDensity/AgentHub) | 多 Agent 編排平台 — web-perf-audit 是官方插件 |
| [MineWorld](https://github.com/EVEDensity/MineWorld) | WebGL 體素引擎 — 效能優化經驗的本工具來源 |

### 推薦 Topics

`web-performance` `core-web-vitals` `lighthouse` `performance-audit` `web-vitals` `claude-code` `devtools` `pagespeed-insights` `webperf` `performance-budget` `ci-cd` `frontend-engineering`

---

## 📄 授權

MIT © 2026 [EVEDensity](https://github.com/EVEDensity)

<p align="center">
  基於 <a href="https://web.dev/learn/performance">web.dev/learn/performance</a> — Google Chrome 官方 Web 效能課程。<br>
  流水線架構靈感來自 <a href="https://github.com/Egonex-AI/Understand-Anything">Understand-Anything</a>。<br>
  屬於 <a href="https://github.com/EVEDensity/AgentHub">AgentHub</a> 生態。
</p>

---

<p align="center">
  <sub>
    <a href="README.md">English</a> ·
    <a href="README_zh-CN.md">简体中文</a> ·
    📖 繁體中文 ·
    <a href="README_ja.md">日本語</a> ·
    <a href="README_ko.md">한국어</a> ·
    <a href="README_es.md">Español</a> ·
    <a href="README_tr.md">Türkçe</a> ·
    <a href="README_ru.md">Русский</a>
  </sub>
</p>
