<h1 align="center">web-perf-audit</h1>

<p align="center">
  <a href="README.md">English</a>&nbsp;·&nbsp;
  📖 <b>简体中文</b>&nbsp;·&nbsp;
  <a href="README_zh-TW.md">繁體中文</a>&nbsp;·&nbsp;
  <a href="README_ja.md">日本語</a>&nbsp;·&nbsp;
  <a href="README_ko.md">한국어</a>&nbsp;·&nbsp;
  <a href="README_es.md">Español</a>&nbsp;·&nbsp;
  <a href="README_tr.md">Türkçe</a>&nbsp;·&nbsp;
  <a href="README_ru.md">Русский</a>
</p>

<p align="center">
  <strong>不止是跑分 — 直接把可执行的优化方案交到你手里。</strong><br>
  Multi-Agent Web Performance Audit Pipeline — SCAN → ANALYZE → SCORE → REPORT.<br>
  Not another Lighthouse wrapper. A complete audit-to-fix workflow with CWV impact estimates.<br>
  Works with <strong>Claude Code, Cursor, VSCode Copilot,</strong> and any CI pipeline.
</p>

<p align="center">
  <img src="docs/pipeline.png" alt="web-perf-audit pipeline: SCAN → ANALYZE → SCORE → REPORT" width="800">
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



---

## 为什么需要 web-perf-audit

你跑了 Lighthouse。LCP 4.2s，得分 62。你盯着屏幕。然后呢？

市面上的工具都在告诉你「哪里不好」。没有一个告诉你「改哪一行、怎么改、为什么会奏效」。web-perf-audit 填补了这个缺口——

- **SCAN**：Lighthouse + Puppeteer 采集原始 CWV 数据
- **ANALYZE**：5 个 Agent 并行扫描（关键路径、资源预加载、图片、字体、JS 冗余）
- **SCORE**：按 CWV 影响面加权打分，P0/P1/P2 优先级排序
- **REPORT**：生成带复制粘贴代码的修复方案，每条建议都链回 web.dev 原理

> *"目标不是 Lighthouse 100 分——是真实用户的页面飞快加载、交互即时响应。"*

---

## ✨ 核心能力

| 能力 | 说明 |
|------|------|
| 🎯 **web.dev 标准对齐** | 所有检测规则基于 [web.dev/learn/performance](https://web.dev/learn/performance)。LCP ≤2.5s、INP ≤200ms、CLS ≤0.1，p75 分位。 |
| 🤖 **多 Agent 并行审计** | 5 个专职 Agent：工程扫描 → 资源解析 → 指标打分 → 变更预测 → 修复方案生成。各司其职，并行执行。 |
| 🔧 **确定性 + 实测混合** | 静态检测（缺 `defer`、`font-display` 错误、无 `srcset`）每次结果一致；运行时指标（LCP、TBT）通过 Lighthouse 实际浏览器测量。 |
| 📊 **离线可视化面板** | Chart.js 交互式仪表盘。评分圆环、CWV 指标卡、分类柱状图、优先级问题列表。审计完成后无需联网。 |
| 🔁 **Git 感知增量审计** | SHA256 指纹缓存，页面无变化则跳过全流程。`perf-diff` 对比两个分支的审计结果，合并前发现性能回归。 |
| 🧩 **跨平台 & 多 IDE 适配** | macOS / Linux / Windows 全平台支持。Claude Code 原生 Skill，Cursor rules，VSCode Copilot 指令。GitHub Actions 一行集成。 |

---

## 🏗 架构

### 多 Agent 审计流水线

```
用户触发 /perf analyze <URL>
         │
         ├─ Stage 1: SCAN
         │   ├─ 工程扫描 Agent (框架检测、产物发现、.webperfignore 过滤)
         │   └─ Lighthouse + Puppeteer (LCP/CLS/INP/TBT/FCP 原始数据)
         │
         ├─ Stage 2: ANALYZE (5 Agent 并行)
         │   ├─ 关键路径 Agent (渲染阻塞、请求链深度、DOM 大小)
         │   ├─ Resource Hints Agent (preload/prefetch/preconnect 质量)
         │   ├─ 图片审计 Agent (格式/sizes/懒加载/LCP 候选图片)
         │   ├─ 字体审计 Agent (font-display/woff2/子集化/预加载)
         │   └─ JS 审计 Agent (Coverage 数据、长任务、第三方脚本)
         │
         ├─ Stage 3: SCORE
         │   └─ 指标打分 Agent (CWV 影响面加权 × 严重度系数 → P0/P1/P2)
         │
         └─ Stage 4: REPORT
             └─ 优化方案 Agent (匹配修复模板、生成 before/after 代码)
                    ↓
             audit-report.json / report.md / dashboard.html
```

### 分层设计

| 层 | 职责 | 技术栈 |
|----|------|--------|
| **触发层** | CLI / CI / IDE 调用入口 | Claude Code Skill、GitHub Actions、Cursor rules |
| **采集层** | 原始数据 + 项目结构发现 | Lighthouse CLI、Puppeteer、PageSpeed Insights API |
| **分析层** | 5 维度静态 + 运行时分析 | Python 3.8+ (HTMLParser)、Node.js (Puppeteer) |
| **打分引擎** | CWV 加权优先级计算 | Python 评分引擎 (7 分类 × 严重度乘数) |
| **输出层** | 报告渲染 + 修复模板 | Python (Markdown/JSON)、Chart.js (仪表盘) |
| **增量层** | 指纹缓存 + 跨分支对比 | SHA256 指纹、JSON 结构对比 |

---

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/EVEDensity/web-perf-audit.git && cd web-perf-audit

# 2. 安装依赖
npm install -g lighthouse && npm install

# 3. 运行审计
python scripts/fetch_metrics.py "https://example.com" --output-dir .web-perf
# ... (5 个分析器并行运行) ...
python scripts/score_and_report.py "https://example.com" --output-dir .web-perf --format all

# 4. 打开仪表盘
open .web-perf/dashboard.html   # macOS
start .web-perf/dashboard.html  # Windows
```

### Claude Code 一键安装

```
/plugin install web-perf-audit@EVEDensity/web-perf-audit
/perf analyze https://example.com
```

---

## 📦 安装指南

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.sh | bash
```

### Windows PowerShell

```powershell
iwr -Uri https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.ps1 -OutFile install.ps1; ./install.ps1
```

### 前置依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.8 | 所有分析 + 打分脚本 |
| Node.js | ≥ 18 | Lighthouse CLI + Puppeteer |
| Lighthouse | latest | CWV 指标采集 |
| Puppeteer | ^22.0.0 | JS Coverage + Long Task API |

---

## 📖 CLI 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `/perf analyze` | 全流程审计 | `python scripts/fetch_metrics.py <URL> --output-dir .web-perf` |
| `/perf dashboard` | 打开可视化面板 | `open .web-perf/dashboard.html` |
| `/perf diff` | Git 变更性能对比 | `python scripts/diff_report.py before.json after.json` |
| `/perf resource` | 静态资源批量审计 | `python scripts/audit_images.py <URL> -o images.json` |
| `/perf explain` | 单维度深度分析 | `python scripts/analyze_critical_path.py metrics.json` |
| `/perf chat` | 对话式性能咨询 | Claude Code 原生对话 |

---

## 💼 实战案例

### 本地项目审计

```bash
npm run dev &
python scripts/fetch_metrics.py "http://localhost:5173" --output-dir .web-perf
# ... 并行分析 ...
python scripts/score_and_report.py "http://localhost:5173" --output-dir .web-perf --format all
```

### CI 性能门禁

```yaml
- name: Performance Gate
  run: |
    python scripts/score_and_report.py "$STAGING_URL" --output-dir .web-perf --format json
    SCORE=$(python -c "import json; print(json.load(open('.web-perf/audit-report.json'))['overallScore']['overallScore'])")
    if [ "$SCORE" -lt 70 ]; then exit 1; fi
```

### 接入 AgentHub

web-perf-audit 是 [AgentHub](https://github.com/EVEDensity/AgentHub) 的一等公民插件，开箱即用。

---

## ❓ 常见问题

<details>
<summary><strong>和直接跑 Lighthouse 有什么区别？</strong></summary>

Lighthouse 给分数和审计列表。我们在此基础上额外做了 5 个维度的深度分析（Hints 质量评分、`@font-face` 解析、JS Coverage 实测、第三方归因、DOM 深度），按 CWV 影响面排序优先级，生成可复制的修复代码，支持增量对比，每个建议都链回 web.dev 原理文档。
</details>

<details>
<summary><strong>每次审计要多久？</strong></summary>

典型页面 30-90 秒。Lighthouse 15-40s（取决于页面复杂度），5 个并行分析器 10-30s，打分秒级完成。
</details>

<details>
<summary><strong>支持 SPA 吗？</strong></summary>

是的。Puppeteer 端等待 `networkidle2` 后才采集 Coverage 数据，动态加载的 chunk 不会漏。建议 SPA 用 `--strategy desktop`。
</details>

<details>
<summary><strong>内网站点能用吗？</strong></summary>

可以。`localhost` 和内部 IP 均支持，自签证书加 `--extra-lighthouse-flags "--chrome-flags='--ignore-certificate-errors'"`。
</details>

<details>
<summary><strong>团队怎么共享审计结果？</strong></summary>

仪表盘 HTML 是纯静态文件，丢到任何静态托管即可。或是上传 CI artifact，队员下载本地打开。
</details>

---

## 🤝 参与贡献

- **新增审计规则**：在 `references/` 添加 md，遵循「问题→检测→修复→收益」模板
- **新增 Agent**：在 `scripts/` 创建脚本（Python/Node.js），输出 JSON，注册到 `score_and_report.py`
- **仪表盘改进**：编辑 `templates/dashboard.html`，用示例 JSON 测试
- **Bug 反馈**：提 Issue 时附上 `audit-report.json` 和测试 URL

### 关联仓库

| 项目 | 说明 |
|------|------|
| [AgentHub](https://github.com/EVEDensity/AgentHub) | 多 Agent 编排平台 — web-perf-audit 是官方插件 |
| [MineWorld](https://github.com/EVEDensity/MineWorld) | WebGL 体素引擎 — 性能优化经验的本工具来源 |

### 推荐 Topics

`web-performance` `core-web-vitals` `lighthouse` `performance-audit` `web-vitals` `claude-code` `devtools` `pagespeed-insights` `webperf` `performance-budget` `ci-cd` `frontend-engineering`

---

## 📄 许可证

MIT © 2026 [EVEDensity](https://github.com/EVEDensity)

<p align="center">
  基于 <a href="https://web.dev/learn/performance">web.dev/learn/performance</a> — Google Chrome 官方 Web 性能课程。<br>
  流水线架构灵感来自 <a href="https://github.com/Egonex-AI/Understand-Anything">Understand-Anything</a>。<br>
  属于 <a href="https://github.com/EVEDensity/AgentHub">AgentHub</a> 生态。
</p>

---

<p align="center">
  <sub>
    <a href="README.md">English</a> ·
    📖 简体中文 ·
    <a href="README_zh-TW.md">繁體中文</a> ·
    <a href="README_ja.md">日本語</a> ·
    <a href="README_ko.md">한국어</a> ·
    <a href="README_es.md">Español</a> ·
    <a href="README_tr.md">Türkçe</a> ·
    <a href="README_ru.md">Русский</a>
  </sub>
</p>
