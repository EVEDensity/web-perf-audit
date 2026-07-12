<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/node-18+-green.svg" alt="Node.js 18+">
  <img src="https://img.shields.io/badge/skill-claude--code-orange.svg" alt="Claude Code Skill">
  <img src="https://img.shields.io/badge/knowledge-web.dev-4285F4.svg" alt="Knowledge: web.dev">
</p>

<h1 align="center">Web Performance Audit</h1>

<p align="center">
  <strong>Fixes that ship > advice that sits in a dashboard.</strong><br>
  Turn any URL into a prioritized, code-level performance optimization plan.<br>
  Multi-stage pipeline: SCAN → ANALYZE → SCORE → REPORT.<br>
  Works with <strong>Claude Code</strong> and any CI pipeline.
</p>

---

## Why web-perf-audit

Lighthouse tells you **what's wrong**. web-perf-audit tells you **exactly what to change and why it matters**.

Every issue in the report comes with:
- A severity rating weighted against Core Web Vitals impact (not discovery order)
- A copy-pasteable code fix
- A backlink to the web.dev principle explaining *why* that fix works
- An estimated LCP/CLS/INP/TBT improvement in milliseconds

> *"The goal isn't a 100/100 Lighthouse score — it's a page that loads fast and responds instantly for real users."*

---

## Architecture

### Monorepo Structure

```
web-perf-audit/
├── SKILL.md                          # Claude Code skill entry point
├── README.md                         # ← you are here
├── package.json                      # Node dependencies (Puppeteer)
├── .webperfignore                    # Exclude third-party noise from audit
│
├── references/                       # 8 web.dev knowledge modules (markdown)
│   ├── critical-path.md              #   Critical Rendering Path
│   ├── html-loading.md               #   HTML parsing & resource ordering
│   ├── resource-hints.md             #   preload / prefetch / preconnect
│   ├── image-performance.md          #   modern formats, srcset, lazy loading
│   ├── video-performance.md          #   encoding, poster, GIF→MP4
│   ├── font-performance.md           #   font-display, subsetting, preload
│   ├── js-performance.md             #   code splitting, workers, long tasks
│   └── predictive-loading.md         #   prefetch, prerender, SW precaching
│
├── scripts/                          # 8 executable audit scripts
│   ├── fetch_metrics.py              #   Stage 1 — Lighthouse / PSI data
│   ├── analyze_critical_path.py      #   Stage 2 — render-blocking analysis
│   ├── check_resource_hints.py       #   Stage 2 — hints audit
│   ├── audit_images.py               #   Stage 2 — image audit
│   ├── audit_fonts.py                #   Stage 2 — font audit
│   ├── audit_js_bundles.js           #   Stage 2 — JS coverage + long tasks
│   ├── score_and_report.py           #   Stage 3+4 — scoring + report gen
│   └── diff_report.py                #   CI/PR — compare two audits
│
├── templates/
│   └── dashboard.html                # Chart.js interactive dashboard
│
└── .web-perf/                        # Generated (gitignored)
    ├── audit-report.json             #   Structured data for CI/programmatic use
    ├── report.md                     #   Human-readable P0→P1→P2 report
    ├── dashboard.html                #   Visual dashboard (from template)
    └── fingerprint.txt               #   Incremental-analysis cache
```

### Tech Stack

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| **Data Collection** | Lighthouse CLI, PageSpeed Insights API | Raw CWV metrics (LCP/CLS/INP/TBT/FCP) |
| **Static Analysis** | Python 3.8+ (stdlib + BeautifulSoup) | HTML parsing, DOM scanning, @font-face extraction, resource hint validation |
| **Runtime Profiling** | Puppeteer (Chrome headless) | JS Coverage API, Long Task observer, third-party attribution |
| **Scoring Engine** | Python | Weighted multi-dimensional scoring (25% metrics + 20% CRP + 20% JS + 15% images + 10% hints + 5% fonts + 5% 3P) |
| **Report Generation** | Python + Chart.js | JSON (structured) + Markdown (human) + HTML (dashboard) |
| **Knowledge Base** | Markdown (8 modules) | web.dev-aligned references; every issue backlinks to a principle |

---

## Core Design: Deterministic Checks + Lighthouse Hybrid

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| **Deterministic** | Python scripts | Parse HTML/CSS for missing `defer`, missing `srcset`, wrong `font-display`, absent `width`/`height`, malformed preloads. Same page → same result every run. |
| **Measurement** | Lighthouse / Puppeteer | Capture real browser metrics: LCP, CLS, TBT, JS Coverage, Long Tasks. Numbers that reflect actual user experience. |

> This split means the structural audit is **reproducible** (you can run it in CI and get the same issue list), while the metrics layer captures **real-world variability** (network conditions, device emulation).

---

## Multi-Stage Pipeline

The `/web-perf-audit` skill orchestrates 4 stages across 8 scripts:

```
SCAN (1 script)
  │  fetch_metrics.py ── Lighthouse → metrics.json
  │
  ├─ ANALYZE (5 scripts — run in parallel)
  │  ├─ analyze_critical_path.py   → critical-path.json
  │  ├─ check_resource_hints.py    → resource-hints.json
  │  ├─ audit_images.py            → images.json
  │  ├─ audit_fonts.py             → fonts.json
  │  └─ audit_js_bundles.js        → js-bundles.json
  │
  ├─ SCORE (1 script)
  │  └─ score_and_report.py ── weighted scoring → P0/P1/P2 priority
  │
  └─ REPORT (same script)
     ├─ audit-report.json   ← programmatic consumption
     ├─ report.md           ← human-readable
     └─ dashboard.html      ← visual dashboard
```

### Agent Script Map

| Script | Language | Input | Output | Runs |
|--------|----------|-------|--------|------|
| `fetch_metrics.py` | Python | URL | `metrics.json` | Stage 1 — must run first |
| `analyze_critical_path.py` | Python | `metrics.json` | `critical-path.json` | Stage 2 — parallel |
| `check_resource_hints.py` | Python | URL | `resource-hints.json` | Stage 2 — parallel |
| `audit_images.py` | Python | URL | `images.json` | Stage 2 — parallel |
| `audit_fonts.py` | Python | URL | `fonts.json` | Stage 2 — parallel |
| `audit_js_bundles.js` | Node.js | URL | `js-bundles.json` | Stage 2 — parallel |
| `score_and_report.py` | Python | all above | `audit-report.json`, `report.md`, `dashboard.html` | Stage 3+4 |
| `diff_report.py` | Python | 2× `audit-report.json` | `diff-report.json` | CI/PR only |

### Incremental Analysis

- **Fingerprint cache**: SHA256 hash of CWV values + resource summary written to `fingerprint.txt`
- **Second run**: if fingerprint matches → skip full pipeline, report "no changes"
- **Diff mode**: `diff_report.py before.json after.json` → score delta, resolved/new issue types, per-metric trend

---

## Scoring & Prioritization

### Weight Distribution

| Category | Weight | Primary CWV | Rationale |
|----------|:------:|------------|-----------|
| **Metrics** (Lighthouse Score) | 25% | All | Baseline measurement |
| **Critical Path** | 20% | LCP, FCP | Blocking resources directly delay first paint |
| **JS Bundles** | 20% | TBT, INP | Unused JS + long tasks block interactivity |
| **Images** | 15% | LCP, CLS | LCP is usually an image; missing dimensions cause layout shift |
| **Resource Hints** | 10% | LCP, FCP | Preload/preconnect can save 300ms-2s |
| **Fonts** | 5% | LCP, CLS | FOIT/FOUT affects perceived speed + layout stability |
| **Third Party** | 5% | TBT | Third-party JS often dominates main thread |

### Priority Tiers

Issues are **never** sorted by discovery order. Each issue gets a priority score: `impact_weight × severity_multiplier`.

| Tier | Threshold | Meaning |
|------|----------|---------|
| **P0 — Critical** | Score ≥ 20 | Fix immediately; high CWV impact |
| **P1 — High** | Score 10–19 | Fix this sprint; measurable improvement |
| **P2 — Moderate** | Score < 10 | Nice-to-have; smaller or indirect impact |

---

## Output Format

### `.web-perf/audit-report.json`

```jsonc
{
  "url": "https://example.com",
  "timestamp": "2026-07-12T10:30:00Z",
  "overallScore": { "overallScore": 72, "grade": "B" },
  "metrics": {
    "lcp": { "value": 3200, "rating": "needs-improvement" },
    "cls": { "value": 0.08, "rating": "good" }
  },
  "allIssues": [
    {
      "priority": "P0",
      "priorityScore": 27,
      "severity": "critical",
      "type": "render-blocking",
      "description": "3 render-blocking stylesheets delay LCP by 1200ms",
      "fix": "<link rel=\"preload\" href=\"styles.css\" as=\"style\" onload=\"this.rel='stylesheet'\">",
      "ref": "references/critical-path.md"
    }
  ],
  "comparison": {
    "previousScore": 68,
    "change": 4,
    "direction": "improved"
  }
}
```

### `.web-perf/report.md`

Human-readable, organized by P0 → P1 → P2. Each issue includes:

```
### P0 — Critical

**1. [render-blocking]** 🔴

> 3 render-blocking stylesheets delay LCP by 1200ms

- **Affects:** LCP (primary), FCP (secondary)
- **Wasted time:** 1200ms

**🔧 Fix:**
```html
<link rel="preload" href="styles.css" as="style" onload="this.rel='stylesheet'">
```

📚 See: `references/critical-path.md`
```

### Dashboard

Interactive HTML dashboard with Chart.js:
- Score ring (color-coded by grade A-F)
- CWV metric cards (LCP / CLS / INP / TBT / FCP)
- Category breakdown bar chart
- Priority-ordered issue list with P0/P1/P2 badges
- vs-previous-audit comparison panel (if available)

---

## Quick Start

### Prerequisites

```bash
# Node.js (for Lighthouse + Puppeteer)
npm install -g lighthouse
npm install puppeteer

# Python (3.8+)
python --version  # ≥ 3.8
```

### One-URL Audit

```bash
cd web-perf-audit
URL="https://example.com"

# Stage 1: Collect metrics
python scripts/fetch_metrics.py "$URL" --output-dir .web-perf

# Stage 2: Run 5 analysis scripts in parallel
python scripts/analyze_critical_path.py .web-perf/metrics.json -o .web-perf/critical-path.json &
python scripts/check_resource_hints.py "$URL" -o .web-perf/resource-hints.json &
python scripts/audit_images.py "$URL" -o .web-perf/images.json &
python scripts/audit_fonts.py "$URL" -o .web-perf/fonts.json &
node scripts/audit_js_bundles.js "$URL" --output .web-perf/js-bundles.json &
wait

# Stage 3+4: Score and generate reports
python scripts/score_and_report.py "$URL" --output-dir .web-perf --format all
```

### CI Integration (GitHub Actions Example)

```yaml
name: Performance Diff
on: [pull_request]

jobs:
  perf-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need base ref for diff

      - name: Audit base branch
        run: |
          git checkout ${{ github.base_ref }}
          python scripts/fetch_metrics.py "$STAGING_URL" --output-dir .web-perf/before

      - name: Audit PR branch
        run: |
          git checkout ${{ github.head_ref }}
          python scripts/fetch_metrics.py "$STAGING_URL" --output-dir .web-perf/after

      - name: Generate diff report
        run: |
          python scripts/diff_report.py \
            .web-perf/before/audit-report.json \
            .web-perf/after/audit-report.json \
            --format both \
            -o .web-perf/diff-report.md

      - name: Comment PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('.web-perf/diff-report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

### Using .webperfignore

Create a `.webperfignore` file to exclude third-party resources you can't control:

```
google-analytics.com
googletagmanager.com
facebook.net
doubleclick.net
hotjar.com
cdnjs.cloudflare.com
```

---

## Reference Knowledge Base

Each file in `references/` follows a consistent structure:

| Section | Content |
|---------|---------|
| **Problem** | Observable symptoms + affected CWV metrics |
| **Detection** | Lighthouse audit IDs, DevTools steps, script commands |
| **Fix** | Copy-pasteable code (before/after) |
| **Expected Benefit** | Millisecond/score improvement per optimization |

| File | Covers | Key Lighthouse Audits |
|------|--------|----------------------|
| `critical-path.md` | Render-blocking CSS/JS, request chains, DOM size | `render-blocking-resources`, `critical-request-chains`, `dom-size` |
| `html-loading.md` | Script attributes, `<head>` ordering, parser behavior | — |
| `resource-hints.md` | preload, prefetch, preconnect, dns-prefetch | `uses-rel-preconnect`, `uses-rel-preload` |
| `image-performance.md` | WebP/AVIF, srcset, lazy loading, LCP images | `modern-image-formats`, `uses-responsive-images`, `offscreen-images` |
| `video-performance.md` | Encoding, poster, preload, GIF→MP4 | `efficient-animated-content` |
| `font-performance.md` | font-display, subsetting, preload, system fonts | `font-display` |
| `js-performance.md` | Code splitting, Workers, Coverage, third-party | `unused-javascript`, `legacy-javascript`, `duplicated-javascript` |
| `predictive-loading.md` | prefetch, prerender, SW precache, Quicklink | — |

---

## Design Philosophy

### 1. Audits that ship fixes

Every issue comes with a concrete, copy-pasteable code change. No ambiguous "consider optimizing" — either `<script defer>` or `<link rel="preload">` or `loading="lazy"`.

### 2. Priority by impact, not discovery

Issues are scored against their Core Web Vitals impact surface (LCP 40% / CLS 20% / TBT-INP 30% / Other 10%), then sorted P0→P1→P2. The first issue you see is the one that will move the needle most.

### 3. Deterministic where possible, measured where necessary

HTML structure doesn't change between runs — so static checks (missing `defer`, wrong `font-display`, absent `srcset`) produce the same result every time. Metrics (LCP, TBT) come from Lighthouse because they depend on real network/device conditions.

### 4. Every recommendation traces to a principle

No black-box advice. Every issue's `ref` field points to a specific `references/*.md` file that explains the *why* — rooted in web.dev's Learn Performance curriculum.

### 5. JSON-first, human-readable second

The canonical output is `audit-report.json`. Markdown and HTML are rendered views of the same data. This means you can pipe the JSON into Slack, Datadog, Grafana, or your own dashboard without parsing prose.

---

## Platform Support

| Platform | Integration | Status |
|----------|-----------|--------|
| **Claude Code** | Native skill (`SKILL.md`) | ✅ Primary |
| **GitHub Actions** | CI diff pipeline | ✅ Supported |
| **GitLab CI** | CI diff pipeline | ✅ Supported |
| **Jenkins / CircleCI** | Shell scripts | ✅ Compatible |
| **Vercel / Netlify** | Deploy hook + audit | ✅ Compatible |
| **Custom Dashboard** | `audit-report.json` | ✅ JSON API |

---

## FAQ

### How is this different from running Lighthouse?

Lighthouse gives you a score and a list of audits. web-perf-audit:
- Runs Lighthouse as its *first stage* to capture metrics
- Then runs **5 additional analysis passes** that Lighthouse doesn't do (resource hint quality scoring, font subsetting analysis, real JS Coverage via Puppeteer, @font-face rule parsing)
- **Scores and prioritizes** all findings against CWV impact
- Produces **structured JSON** for CI, not just a web UI
- Supports **incremental diff** between two audits for PR gating
- Every fix backlinks to a **web.dev knowledge module**

### Do I need a PageSpeed Insights API key?

No. The default path uses local Lighthouse CLI (free, no key required). PSI is optional and adds CrUX field data (real-user metrics from Chrome).

### Can I run this against localhost?

Yes. Lighthouse supports `http://localhost:*` URLs. For self-signed certificates, pass `--extra-lighthouse-flags --chrome-flags="--ignore-certificate-errors"`.

### How long does a full audit take?

Roughly 30-90 seconds depending on page complexity (Lighthouse takes 15-40s, parallel analysis scripts take 10-30s, scoring is instant).

### What about SPA / JS-heavy apps?

The Puppeteer-based `audit_js_bundles.js` waits for `networkidle2` before collecting Coverage data, so it captures dynamically loaded chunks. For fully client-rendered apps, also run Lighthouse with `--preset=desktop` if that matches your user base.

---

## Contributing

This skill follows the [Claude Code Skill specification](https://docs.claude.codes/skills). Contributions are welcome:

1. **New reference module** — add a `.md` file to `references/` following the problem→detect→fix→benefit template
2. **New audit script** — add to `scripts/`, wire into `score_and_report.py`'s scoring engine
3. **Dashboard improvements** — edit `templates/dashboard.html`
4. **Bug fixes** — open an issue or PR

---

## License

MIT © 2026

---

<p align="center">
  Built with web.dev's <a href="https://web.dev/learn/performance">Learn Performance</a> curriculum as the knowledge foundation.<br>
  Pipeline architecture inspired by <a href="https://github.com/Egonex-AI/Understand-Anything">Understand-Anything</a>.
</p>
