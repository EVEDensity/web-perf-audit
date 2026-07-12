<h1 align="center">web-perf-audit</h1>

<p align="center">
  <a href="README.md">English</a>&nbsp;·&nbsp;
  <a href="README_zh-CN.md">简体中文</a>&nbsp;·&nbsp;
  <a href="README_zh-TW.md">繁體中文</a>&nbsp;·&nbsp;
  📖 <b>日本語</b>&nbsp;·&nbsp;
  <a href="README_ko.md">한국어</a>&nbsp;·&nbsp;
  <a href="README_es.md">Español</a>&nbsp;·&nbsp;
  <a href="README_tr.md">Türkçe</a>&nbsp;·&nbsp;
  <a href="README_ru.md">Русский</a>
</p>

<p align="center">
  <strong>スコアだけじゃない — 実行可能な最適化案を手渡します。</strong><br>
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

## web-perf-audit が必要な理由

Lighthouse を実行しました。LCP 4.2s、スコア 62。画面を見つめています。次は？

世の中のツールは「何が悪いか」を教えてくれます。しかし「どの行を、どう修正し、なぜそれが効くのか」を教えてくれるものはありません。web-perf-audit はそのギャップを埋めます——

- **SCAN**：Lighthouse + Puppeteer で生の CWV データを収集
- **ANALYZE**：5 つのエージェントが並行して分析（クリティカルパス、リソースヒント、画像、フォント、JS 冗長性）
- **SCORE**：CWV への影響度で重み付け採点、P0/P1/P2 で優先順位付け
- **REPORT**：コピペ可能な修正コード付きレポート、全提案が web.dev の原理にリンク

> *"目標は Lighthouse 100 点ではありません — 実際のユーザーにとってページが高速に読み込まれ、即座に応答することです。"*

---

## ✨ 主要機能

| 機能 | 説明 |
|------|------|
| 🎯 **web.dev 標準準拠** | 全検出ルールは [web.dev/learn/performance](https://web.dev/learn/performance) に基づく。LCP ≤2.5s、INP ≤200ms、CLS ≤0.1、p75 パーセンタイル。 |
| 🤖 **マルチエージェント並行監査** | 5 つの専任エージェント：プロジェクトスキャン → リソース解析 → 指標スコアリング → 変更予測 → 最適化案生成。各エージェントが並行実行。 |
| 🔧 **決定論的 + 実測ハイブリッド** | 静的チェック（`defer` 欠落、`font-display` 誤り、`srcset` なし）は常に同じ結果。実行時指標（LCP、TBT）は Lighthouse による実際のブラウザ計測。 |
| 📊 **オフラインダッシュボード** | Chart.js インタラクティブダッシュボード。スコアリング、CWV 指標カード、カテゴリ別棒グラフ、優先度付き問題リスト。監査後はオフラインで完結。 |
| 🔁 **Git 対応インクリメンタル監査** | SHA256 フィンガープリントキャッシュ。ページに変更がなければ全工程をスキップ。`perf-diff` でブランチ間のパフォーマンス回帰を検出。 |
| 🧩 **クロスプラットフォーム & マルチ IDE** | macOS / Linux / Windows 対応。Claude Code ネイティブスキル、Cursor ルール、VSCode Copilot 指示。GitHub Actions ワンライン統合。 |

---

## 🏗 アーキテクチャ

### マルチエージェント監査パイプライン

```
ユーザーが /perf analyze <URL> を実行
         │
         ├─ Stage 1: SCAN
         │   ├─ プロジェクトスキャンエージェント (フレームワーク検出、ビルド成果物発見、.webperfignore フィルタ)
         │   └─ Lighthouse + Puppeteer (LCP/CLS/INP/TBT/FCP 生データ)
         │
         ├─ Stage 2: ANALYZE (5 エージェント並行)
         │   ├─ クリティカルパスエージェント (レンダリングブロック、リクエストチェーン深度、DOM サイズ)
         │   ├─ Resource Hints エージェント (preload/prefetch/preconnect 品質)
         │   ├─ 画像監査エージェント (フォーマット/sizes/遅延読み込み/LCP 候補画像)
         │   ├─ フォント監査エージェント (font-display/woff2/サブセット化/プリロード)
         │   └─ JS 監査エージェント (Coverage データ、Long Task、サードパーティスクリプト)
         │
         ├─ Stage 3: SCORE
         │   └─ 指標スコアリングエージェント (CWV 影響度加重 × 重大度係数 → P0/P1/P2)
         │
         └─ Stage 4: REPORT
             └─ 最適化案エージェント (修正テンプレート照合、before/after コード生成)
                    ↓
             audit-report.json / report.md / dashboard.html
```

### レイヤー設計

| レイヤー | 役割 | 技術 |
|----------|------|------|
| **トリガー** | CLI / CI / IDE 呼び出し | Claude Code スキル、GitHub Actions、Cursor ルール |
| **収集** | 生データ + プロジェクト構造 | Lighthouse CLI、Puppeteer、PageSpeed Insights API |
| **分析** | 5 次元の静的 + 実行時分析 | Python 3.8+ (HTMLParser)、Node.js (Puppeteer) |
| **スコアリング** | CWV 加重優先度計算 | Python スコアリングエンジン (7 カテゴリ × 重大度乗数) |
| **出力** | レポートレンダリング + 修正テンプレート | Python (Markdown/JSON)、Chart.js (ダッシュボード) |
| **差分** | フィンガープリントキャッシュ + ブランチ間比較 | SHA256 フィンガープリント、JSON 構造差分 |

---

## 🚀 クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/EVEDensity/web-perf-audit.git && cd web-perf-audit

# 2. 依存関係をインストール
npm install -g lighthouse && npm install

# 3. 監査を実行
python scripts/fetch_metrics.py "https://example.com" --output-dir .web-perf
# ... (5 つのアナライザーを並行実行) ...
python scripts/score_and_report.py "https://example.com" --output-dir .web-perf --format all

# 4. ダッシュボードを開く
open .web-perf/dashboard.html   # macOS
start .web-perf/dashboard.html  # Windows
```

### Claude Code ワンクリックインストール

```
/plugin install web-perf-audit@EVEDensity/web-perf-audit
/perf analyze https://example.com
```

---

## 📦 インストール

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.sh | bash
```

### Windows PowerShell

```powershell
iwr -Uri https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.ps1 -OutFile install.ps1; ./install.ps1
```

### 前提条件

| 依存関係 | バージョン | 用途 |
|----------|-----------|------|
| Python | ≥ 3.8 | 全分析・スコアリングスクリプト |
| Node.js | ≥ 18 | Lighthouse CLI + Puppeteer |
| Lighthouse | latest | CWV 指標収集 |
| Puppeteer | ^22.0.0 | JS Coverage + Long Task API |

---

## 📖 CLI コマンドリファレンス

| コマンド | 説明 | 例 |
|----------|------|-----|
| `/perf analyze` | 全工程監査 | `python scripts/fetch_metrics.py <URL> --output-dir .web-perf` |
| `/perf dashboard` | ダッシュボードを開く | `open .web-perf/dashboard.html` |
| `/perf diff` | Git 変更のパフォーマンス比較 | `python scripts/diff_report.py before.json after.json` |
| `/perf resource` | 静的リソース一括監査 | `python scripts/audit_images.py <URL> -o images.json` |
| `/perf explain` | 単一次元の詳細分析 | `python scripts/analyze_critical_path.py metrics.json` |
| `/perf chat` | 対話型パフォーマンス相談 | Claude Code ネイティブ対話 |

---

## 💼 実践ユースケース

### ローカルプロジェクト監査

```bash
npm run dev &
python scripts/fetch_metrics.py "http://localhost:5173" --output-dir .web-perf
python scripts/score_and_report.py "http://localhost:5173" --output-dir .web-perf --format all
```

### CI パフォーマンスゲート

```yaml
- name: Performance Gate
  run: |
    python scripts/score_and_report.py "$STAGING_URL" --output-dir .web-perf --format json
    SCORE=$(python -c "import json; print(json.load(open('.web-perf/audit-report.json'))['overallScore']['overallScore'])")
    if [ "$SCORE" -lt 70 ]; then exit 1; fi
```

---

## ❓ よくある質問

<details>
<summary><strong>Lighthouse を直接実行するのと何が違いますか？</strong></summary>

Lighthouse はスコアと監査リストを提供します。我々はそれに加えて 5 次元の深層分析（Hints 品質スコア、@font-face 解析、JS Coverage 実測、サードパーティ帰属、DOM 深度）を行い、CWV 影響度で優先順位付けし、コピペ可能な修正コードを生成し、インクリメンタル差分比較をサポートし、全提案が web.dev の原理ドキュメントにリンクされています。
</details>

<details>
<summary><strong>監査にはどのくらい時間がかかりますか？</strong></summary>

一般的なページで 30〜90 秒。Lighthouse 15〜40 秒（ページの複雑さに依存）、5 つの並行アナライザー 10〜30 秒、スコアリングは 1 秒未満。
</details>

<details>
<summary><strong>SPA に対応していますか？</strong></summary>

はい。Puppeteer は `networkidle2` を待ってから Coverage データを収集するため、動的ロードされたチャンクも捕捉されます。SPA では `--strategy desktop` を推奨します。
</details>

---

## 📄 ライセンス

MIT © 2026 [EVEDensity](https://github.com/EVEDensity)

<p align="center">
  <a href="https://web.dev/learn/performance">web.dev/learn/performance</a>（Google Chrome 公式 Web パフォーマンスコース）に基づく。<br>
  パイプラインアーキテクチャは <a href="https://github.com/Egonex-AI/Understand-Anything">Understand-Anything</a> に着想。<br>
  <a href="https://github.com/EVEDensity/AgentHub">AgentHub</a> エコシステムの一部。
</p>

---

<p align="center">
  <sub>
    <a href="README.md">English</a> ·
    <a href="README_zh-CN.md">简体中文</a> ·
    <a href="README_zh-TW.md">繁體中文</a> ·
    📖 日本語 ·
    <a href="README_ko.md">한국어</a> ·
    <a href="README_es.md">Español</a> ·
    <a href="README_tr.md">Türkçe</a> ·
    <a href="README_ru.md">Русский</a>
  </sub>
</p>
