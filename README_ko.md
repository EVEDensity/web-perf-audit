<h1 align="center">web-perf-audit</h1>

<p align="center">
  <a href="README.md">English</a>&nbsp;·&nbsp;
  <a href="README_zh-CN.md">简体中文</a>&nbsp;·&nbsp;
  <a href="README_zh-TW.md">繁體中文</a>&nbsp;·&nbsp;
  <a href="README_ja.md">日本語</a>&nbsp;·&nbsp;
  📖 <b>한국어</b>&nbsp;·&nbsp;
  <a href="README_es.md">Español</a>&nbsp;·&nbsp;
  <a href="README_tr.md">Türkçe</a>&nbsp;·&nbsp;
  <a href="README_ru.md">Русский</a>
</p>

<p align="center">
  <strong>점수만 내는 게 아닙니다 — 실행 가능한 최적화 방안을 직접 전달합니다.</strong><br>
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

## web-perf-audit이 필요한 이유

Lighthouse를 실행했습니다. LCP 4.2초, 점수 62점. 화면만 바라보고 있습니다. 이제 뭘 해야 하죠?

시중의 도구들은 "무엇이 잘못되었는지"만 알려줍니다. "어떤 줄을, 어떻게 고쳐야 하고, 왜 그것이 효과가 있는지"를 알려주는 도구는 없습니다. web-perf-audit이 그 간극을 메웁니다——

- **SCAN**: Lighthouse + Puppeteer로 원시 CWV 데이터 수집
- **ANALYZE**: 5개 에이전트가 병렬 분석 (크리티컬 패스, 리소스 힌트, 이미지, 폰트, JS 중복)
- **SCORE**: CWV 영향도 기준 가중치 채점, P0/P1/P2 우선순위 정렬
- **REPORT**: 복사 가능한 수정 코드가 포함된 리포트, 모든 제안이 web.dev 원리 문서로 연결

> *"목표는 Lighthouse 100점이 아닙니다 — 실제 사용자에게 페이지가 빠르게 로드되고 즉시 반응하는 것입니다."*

---

## ✨ 핵심 기능

| 기능 | 설명 |
|------|------|
| 🎯 **web.dev 표준 정렬** | 모든 감지 규칙은 [web.dev/learn/performance](https://web.dev/learn/performance) 기반. LCP ≤2.5s, INP ≤200ms, CLS ≤0.1, p75 백분위수. |
| 🤖 **멀티 에이전트 병렬 감사** | 5개 전담 에이전트: 프로젝트 스캔 → 리소스 분석 → 지표 스코어링 → 변경 예측 → 최적화 방안 생성. 각자 역할 수행, 병렬 실행. |
| 🔧 **결정론적 + 실측 하이브리드** | 정적 체크(`defer` 누락, `font-display` 오류, `srcset` 없음)는 항상 동일 결과. 런타임 지표(LCP, TBT)는 Lighthouse로 실제 브라우저 측정. |
| 📊 **오프라인 대시보드** | Chart.js 인터랙티브 대시보드. 점수 링, CWV 지표 카드, 카테고리 바 차트, 우선순위 이슈 목록. 감사 후 오프라인에서도 작동. |
| 🔁 **Git 인식 증분 감사** | SHA256 핑거프린트 캐시. 페이지 변경 없으면 전체 파이프라인 건너뜀. `perf-diff`로 브랜치 간 성능 회귀 감지. |
| 🧩 **크로스 플랫폼 & 멀티 IDE** | macOS / Linux / Windows 지원. Claude Code 네이티브 스킬, Cursor 규칙, VSCode Copilot 명령. GitHub Actions 한 줄 통합. |

---

## 🏗 아키텍처

### 멀티 에이전트 감사 파이프라인

```
사용자 실행 /perf analyze <URL>
         │
         ├─ Stage 1: SCAN
         │   ├─ 프로젝트 스캔 에이전트 (프레임워크 감지, 빌드 산출물 발견, .webperfignore 필터)
         │   └─ Lighthouse + Puppeteer (LCP/CLS/INP/TBT/FCP 원시 데이터)
         │
         ├─ Stage 2: ANALYZE (5 에이전트 병렬)
         │   ├─ 크리티컬 패스 에이전트 (렌더링 차단, 요청 체인 깊이, DOM 크기)
         │   ├─ Resource Hints 에이전트 (preload/prefetch/preconnect 품질)
         │   ├─ 이미지 감사 에이전트 (포맷/sizes/지연 로딩/LCP 후보 이미지)
         │   ├─ 폰트 감사 에이전트 (font-display/woff2/서브세팅/프리로드)
         │   └─ JS 감사 에이전트 (Coverage 데이터, Long Task, 서드파티 스크립트)
         │
         ├─ Stage 3: SCORE
         │   └─ 지표 스코어링 에이전트 (CWV 영향도 가중치 × 심각도 계수 → P0/P1/P2)
         │
         └─ Stage 4: REPORT
             └─ 최적화 방안 에이전트 (수정 템플릿 매칭, before/after 코드 생성)
                    ↓
             audit-report.json / report.md / dashboard.html
```

### 레이어 설계

| 레이어 | 역할 | 기술 |
|--------|------|------|
| **트리거** | CLI / CI / IDE 호출 | Claude Code 스킬, GitHub Actions, Cursor 규칙 |
| **수집** | 원시 데이터 + 프로젝트 구조 | Lighthouse CLI, Puppeteer, PageSpeed Insights API |
| **분석** | 5차원 정적 + 런타임 분석 | Python 3.8+ (HTMLParser), Node.js (Puppeteer) |
| **스코어링** | CWV 가중 우선순위 계산 | Python 스코어링 엔진 (7개 카테고리 × 심각도 승수) |
| **출력** | 리포트 렌더링 + 수정 템플릿 | Python (Markdown/JSON), Chart.js (대시보드) |
| **차이** | 핑거프린트 캐시 + 브랜치 간 비교 | SHA256 핑거프린트, JSON 구조 차이 |

---

## 🚀 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/EVEDensity/web-perf-audit.git && cd web-perf-audit

# 2. 의존성 설치
npm install -g lighthouse && npm install

# 3. 감사 실행
python scripts/fetch_metrics.py "https://example.com" --output-dir .web-perf
# ... (5개 분석기 병렬 실행) ...
python scripts/score_and_report.py "https://example.com" --output-dir .web-perf --format all

# 4. 대시보드 열기
open .web-perf/dashboard.html   # macOS
start .web-perf/dashboard.html  # Windows
```

### Claude Code 원클릭 설치

```
/plugin install web-perf-audit@EVEDensity/web-perf-audit
/perf analyze https://example.com
```

---

## 📦 설치

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.sh | bash
```

### Windows PowerShell

```powershell
iwr -Uri https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.ps1 -OutFile install.ps1; ./install.ps1
```

### 사전 요구사항

| 의존성 | 버전 | 용도 |
|--------|------|------|
| Python | ≥ 3.8 | 모든 분석 + 스코어링 스크립트 |
| Node.js | ≥ 18 | Lighthouse CLI + Puppeteer |
| Lighthouse | latest | CWV 지표 수집 |
| Puppeteer | ^22.0.0 | JS Coverage + Long Task API |

---

## 📖 CLI 명령어 참조

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/perf analyze` | 전체 감사 | `python scripts/fetch_metrics.py <URL> --output-dir .web-perf` |
| `/perf dashboard` | 대시보드 열기 | `open .web-perf/dashboard.html` |
| `/perf diff` | Git 변경 성능 비교 | `python scripts/diff_report.py before.json after.json` |
| `/perf resource` | 정적 리소스 일괄 감사 | `python scripts/audit_images.py <URL> -o images.json` |
| `/perf explain` | 단일 차원 심층 분석 | `python scripts/analyze_critical_path.py metrics.json` |
| `/perf chat` | 대화형 성능 컨설팅 | Claude Code 네이티브 대화 |

---

## 💼 실전 활용 사례

### 로컬 프로젝트 감사

```bash
npm run dev &
python scripts/fetch_metrics.py "http://localhost:5173" --output-dir .web-perf
python scripts/score_and_report.py "http://localhost:5173" --output-dir .web-perf --format all
```

### CI 성능 게이트

```yaml
- name: Performance Gate
  run: |
    python scripts/score_and_report.py "$STAGING_URL" --output-dir .web-perf --format json
    SCORE=$(python -c "import json; print(json.load(open('.web-perf/audit-report.json'))['overallScore']['overallScore'])")
    if [ "$SCORE" -lt 70 ]; then exit 1; fi
```

---

## ❓ 자주 묻는 질문

<details>
<summary><strong>Lighthouse를 직접 실행하는 것과 무엇이 다른가요?</strong></summary>

Lighthouse는 점수와 감사 목록만 제공합니다. 우리는 여기에 더해 5가지 차원의 심층 분석(Hints 품질 점수, @font-face 파싱, JS Coverage 실측, 서드파티 귀속, DOM 깊이)을 수행하고, CWV 영향도 기준 우선순위를 매기며, 복사 가능한 수정 코드를 생성하고, 증분 차이 비교를 지원하며, 모든 제안이 web.dev 원리 문서로 연결됩니다.
</details>

<details>
<summary><strong>감사에 얼마나 시간이 걸리나요?</strong></summary>

일반적인 페이지 기준 30~90초. Lighthouse 15~40초(페이지 복잡도에 따라 다름), 5개 병렬 분석기 10~30초, 스코어링은 1초 미만.
</details>

<details>
<summary><strong>SPA를 지원하나요?</strong></summary>

네. Puppeteer는 `networkidle2`를 기다린 후 Coverage 데이터를 수집하므로 동적으로 로드된 청크도 캡처됩니다. SPA에는 `--strategy desktop`을 권장합니다.
</details>

---

## 📄 라이선스

MIT © 2026 [EVEDensity](https://github.com/EVEDensity)

<p align="center">
  <a href="https://web.dev/learn/performance">web.dev/learn/performance</a> — Google Chrome 공식 Web 성능 과정 기반.<br>
  파이프라인 아키텍처는 <a href="https://github.com/Egonex-AI/Understand-Anything">Understand-Anything</a>에서 영감을 받았습니다.<br>
  <a href="https://github.com/EVEDensity/AgentHub">AgentHub</a> 에코시스템의 일부.
</p>

---

<p align="center">
  <sub>
    <a href="README.md">English</a> ·
    <a href="README_zh-CN.md">简体中文</a> ·
    <a href="README_zh-TW.md">繁體中文</a> ·
    <a href="README_ja.md">日本語</a> ·
    📖 한국어 ·
    <a href="README_es.md">Español</a> ·
    <a href="README_tr.md">Türkçe</a> ·
    <a href="README_ru.md">Русский</a>
  </sub>
</p>
